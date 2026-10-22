"""Registro dos backbones candidatos.

Cada entrada declara o tamanho de entrada, a conversão a partir da saída de
preparar_imagem (float32 em [0, 1]), a faixa que o backbone espera, a origem
dos pesos e como seus blocos são reconhecidos para o fine-tuning. Para incluir
um backbone novo basta acrescentar uma entrada em REGISTRO.

Fine-tuning tem o mesmo significado para todos: descongelar os N últimos blocos
da base. O stem nunca é descongelado, as camadas finais, topo convolucional,
acompanham o último bloco e as BatchNormalization permanecem congeladas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import re

import keras

# Média e desvio-padrão do ImageNet usados pelo pré-processador do preset KerasHub
MEDIA_IMAGENET = (0.485, 0.456, 0.406)
DESVIO_IMAGENET = (0.229, 0.224, 0.225)
PRESET_LITE0 = "efficientnet_lite0_ra_imagenet"


@dataclass(frozen=True)
class Backbone:
    nome: str
    tamanho_entrada: int
    construtor: Callable[[int, bool], keras.Model]
    escala: float | tuple[float, ...]
    deslocamento: float | tuple[float, ...]
    faixa_esperada: str
    fonte: str
    padrao_bloco: str
    suporta_fine_tuning: bool = True
    congelar_inicialmente: bool = True

    def camada_conversao(self) -> keras.layers.Layer:
        """Leva [0, 1] para a faixa esperada: x * escala + deslocamento."""
        return keras.layers.Rescaling(self.escala, self.deslocamento, name="conversao_entrada")

    def construir_base(self, pesos_pre_treinados: bool = True) -> keras.Model:
        return self.construtor(self.tamanho_entrada, pesos_pre_treinados)

    def blocos(self, base: keras.Model) -> list[list[keras.layers.Layer]]:
        """Agrupa as camadas da base em blocos, na ordem; o stem fica de fora."""
        padrao = re.compile(self.padrao_bloco)
        grupos: list[list[keras.layers.Layer]] = []
        atual = None
        for camada in base.layers:
            encontrado = padrao.match(camada.name)
            if encontrado and encontrado.group(1) != atual:
                atual = encontrado.group(1)
                grupos.append([])
            if grupos:
                grupos[-1].append(camada)
        if not grupos:
            raise ValueError(f"nenhum bloco reconhecido em {self.nome} com '{self.padrao_bloco}'")
        return grupos


def _aplicacao(classe: str, **kwargs) -> Callable[[int, bool], keras.Model]:
    def construir(tamanho: int, pesos_pre_treinados: bool) -> keras.Model:
        return getattr(keras.applications, classe)(
            input_shape=(tamanho, tamanho, 3),
            include_top=False,
            weights="imagenet" if pesos_pre_treinados else None,
            **kwargs,
        )
    return construir


def _lite0(tamanho: int, pesos_pre_treinados: bool) -> keras.Model:
    import keras_hub  # dependência só desta entrada

    return keras_hub.models.Backbone.from_preset(PRESET_LITE0, load_weights=pesos_pre_treinados)


def _cnn_baseline(tamanho: int, pesos_pre_treinados: bool) -> keras.Model:
    """CNN pequena, sem pré-treino, baseada no tutorial de classificação de imagens."""
    entrada = keras.Input((tamanho, tamanho, 3))
    x = keras.layers.Conv2D(16, 3, padding="same", activation="relu", name="block1_conv")(entrada)
    x = keras.layers.MaxPooling2D(name="block1_pool")(x)
    x = keras.layers.Conv2D(32, 3, padding="same", activation="relu", name="block2_conv")(x)
    x = keras.layers.MaxPooling2D(name="block2_pool")(x)
    x = keras.layers.Conv2D(64, 3, padding="same", activation="relu", name="block3_conv")(x)
    x = keras.layers.MaxPooling2D(name="block3_pool")(x)
    return keras.Model(entrada, x, name="cnn_baseline_base")


_PADRAO_MOBILENET_V3 = r"^(expanded_conv(?:_\d+)?)_"
_PADRAO_MOBILENET_V2 = r"^(expanded_conv|block_\d+)_"
_PADRAO_EFFICIENTNET = r"^(block\d+[a-z])_"
_FAIXA_0_255 = "[0, 255]; Rescaling e normalização ficam dentro do modelo Keras"

REGISTRO: dict[str, Backbone] = {
    entrada.nome: entrada
    for entrada in (
        Backbone(
            nome="cnn_baseline",
            tamanho_entrada=224,
            construtor=_cnn_baseline,
            escala=1.0,
            deslocamento=0.0,
            faixa_esperada="[0, 1], sem conversão adicional",
            fonte="CNN simples treinada do zero, sem pesos pré-treinados",
            padrao_bloco=r"^(block\d+)_",
            suporta_fine_tuning=False,
            congelar_inicialmente=False,
        ),
        Backbone(
            nome="mobilenet_v3_small",
            tamanho_entrada=224,
            construtor=_aplicacao("MobileNetV3Small"),
            escala=255.0,
            deslocamento=0.0,
            faixa_esperada=_FAIXA_0_255 + " (include_preprocessing=True)",
            fonte="keras.applications.MobileNetV3Small, pesos ImageNet-1k",
            padrao_bloco=_PADRAO_MOBILENET_V3,
        ),
        Backbone(
            nome="mobilenet_v3_large",
            tamanho_entrada=224,
            construtor=_aplicacao("MobileNetV3Large"),
            escala=255.0,
            deslocamento=0.0,
            faixa_esperada=_FAIXA_0_255 + " (include_preprocessing=True)",
            fonte="keras.applications.MobileNetV3Large (alpha=1.0), pesos ImageNet-1k",
            padrao_bloco=_PADRAO_MOBILENET_V3,
        ),
        Backbone(
            nome="mobilenet_v3_large_075",
            tamanho_entrada=224,
            construtor=_aplicacao("MobileNetV3Large", alpha=0.75),
            escala=255.0,
            deslocamento=0.0,
            faixa_esperada=_FAIXA_0_255 + " (include_preprocessing=True)",
            fonte="keras.applications.MobileNetV3Large (alpha=0.75), pesos ImageNet-1k",
            padrao_bloco=_PADRAO_MOBILENET_V3,
        ),
        Backbone(
            nome="mobilenet_v2",
            tamanho_entrada=224,
            construtor=_aplicacao("MobileNetV2"),
            escala=2.0,
            deslocamento=-1.0,
            faixa_esperada="[-1, 1], equivalente a mobilenet_v2.preprocess_input",
            fonte="keras.applications.MobileNetV2 (alpha=1.0), pesos ImageNet-1k",
            padrao_bloco=_PADRAO_MOBILENET_V2,
        ),
        Backbone(
            nome="efficientnet_b0",
            tamanho_entrada=224,
            construtor=_aplicacao("EfficientNetB0"),
            escala=255.0,
            deslocamento=0.0,
            faixa_esperada=_FAIXA_0_255,
            fonte="keras.applications.EfficientNetB0, pesos ImageNet-1k",
            padrao_bloco=_PADRAO_EFFICIENTNET,
        ),
        Backbone(
            nome="efficientnet_lite0",
            tamanho_entrada=224,
            construtor=_lite0,
            escala=tuple(1.0 / d for d in DESVIO_IMAGENET),
            deslocamento=tuple(-m / d for m, d in zip(MEDIA_IMAGENET, DESVIO_IMAGENET)),
            faixa_esperada=(
                "(x - média ImageNet) / desvio ImageNet, por canal; é o que faz o "
                "EfficientNetImageConverter do preset sobre [0, 255]"
            ),
            fonte=(
                f"KerasHub, preset {PRESET_LITE0}: pesos do timm efficientnet_lite0.ra_in1k "
                "(ImageNet-1k, receita RandAugment), não o checkpoint original do Google"
            ),
            padrao_bloco=_PADRAO_EFFICIENTNET,
        ),
    )
}
# EfficientNet-Lite2 fica fora: o Keras 3/KerasHub não tem preset nem conversor
# para essa variante (verificado na T5.1 com keras-hub 0.32.0).


def obter(nome: str) -> Backbone:
    if nome not in REGISTRO:
        raise ValueError(f"backbone '{nome}' não registrado; opções: {', '.join(REGISTRO)}")
    return REGISTRO[nome]
