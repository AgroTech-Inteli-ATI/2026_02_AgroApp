"""Pipeline de treinamento modular.

Um único protocolo para todos os backbones candidatos, controlado pela config:

    python -m src.treinamento_t5_1 --config assets/data/treino_T5_1/config_base.json \
        --raiz-imagens <pasta com dataset/, Milho/ e Soja/> [--saida runs]

Segue o guia de transfer learning do TensorFlow/Keras: a base pré-treinada é
congelada e chamada com training=False, uma cabeça nova é treinada e, se a
config pedir, os últimos blocos da base são descongelados e treinados com taxa
de aprendizado menor. A validação é avaliada a cada época com as métricas fixas
de src/avaliacao.py; o teste não é carregado.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import argparse
import csv
import importlib.metadata
import json
import platform
import subprocess

import numpy as np
import keras
import PIL
import tensorflow as tf

from src import backbones
from src.avaliacao import calcular_metricas
from src.config_treino import MONITORES, carregar_config, validar_config
from src.dados_treino import (
    INDICE_PADRAO,
    PESOS_PADRAO,
    SequenciaImagens,
    carregar_class_weight,
    carregar_indice,
    nomes_classes,
    preparar_particao,
)

RAIZ = Path(__file__).resolve().parents[1]
SAIDA_PADRAO = RAIZ / "runs"
ESQUEMA_METRICAS = "metricas_validacao_T5_1_v1"
OTIMIZADORES = {
    "adam": keras.optimizers.Adam,
    "adamw": keras.optimizers.AdamW,
    "sgd": keras.optimizers.SGD,
    "rmsprop": keras.optimizers.RMSprop,
}


def configurar_sementes(semente: int, deterministico: bool) -> None:
    keras.utils.set_random_seed(semente)
    if deterministico:
        tf.config.experimental.enable_op_determinism()


def construir_modelo(
    backbone: backbones.Backbone, quantidade_classes: int, dropout: float, pesos_pre_treinados: bool = True
) -> tuple[keras.Model, keras.Model]:
    """Input [0, 1] → conversão → base → GAP → Dropout → Dense."""
    base = backbone.construir_base(pesos_pre_treinados)
    base.trainable = not backbone.congelar_inicialmente
    tamanho = backbone.tamanho_entrada
    entrada = keras.Input((tamanho, tamanho, 3), name="imagem")
    x = backbone.camada_conversao()(entrada)
    x = base(x, training=False)
    x = keras.layers.GlobalAveragePooling2D(name="pooling")(x)
    x = keras.layers.Dropout(dropout, name="dropout")(x)
    saida = keras.layers.Dense(quantidade_classes, activation="softmax", name="classificacao")(x)
    return keras.Model(entrada, saida, name=f"t5_1_{backbone.nome}"), base


def descongelar_blocos(base: keras.Model, backbone: backbones.Backbone, quantidade: int) -> int:
    """Descongela os `quantidade` últimos blocos, mantendo BatchNorm congelado. Retorna o total de blocos."""
    if not backbone.suporta_fine_tuning:
        raise ValueError(f"o backbone '{backbone.nome}' não suporta fine-tuning; use fine_tuning.ativo=false")
    blocos = backbone.blocos(base)
    if not 1 <= quantidade <= len(blocos):
        raise ValueError(
            f"fine_tuning.blocos_descongelados={quantidade} fora de 1..{len(blocos)} para '{backbone.nome}'"
        )
    selecionadas = {id(camada) for bloco in blocos[-quantidade:] for camada in bloco}
    base.trainable = True
    for camada in base.layers:
        camada.trainable = id(camada) in selecionadas and not isinstance(
            camada, keras.layers.BatchNormalization
        )
    return len(blocos)


def contar_parametros(pesos: list) -> int:
    return int(sum(np.prod(peso.shape) for peso in pesos))


class SincronizarEpoca(keras.callbacks.Callback):
    """Informa à sequência de treino a época corrente (embaralhamento e augmentation)."""

    def __init__(self, sequencia: SequenciaImagens):
        super().__init__()
        self.sequencia = sequencia

    def on_epoch_begin(self, epoch, logs=None):
        self.sequencia.definir_epoca(epoch)


class AvaliacaoValidacao(keras.callbacks.Callback):
    """Calcula val_loss e val_f1_macro com src/avaliacao.py ao fim de cada época."""

    def __init__(self, sequencia: SequenciaImagens, quantidade_classes: int):
        super().__init__()
        self.sequencia = sequencia
        self.quantidade_classes = quantidade_classes

    def on_epoch_end(self, epoch, logs=None):
        probabilidades = self.model.predict(self.sequencia, verbose=0)
        rotulos = self.sequencia.rotulos
        corretas = np.clip(probabilidades[np.arange(len(rotulos)), rotulos], 1e-7, 1.0)
        metricas = calcular_metricas(rotulos, probabilidades.argmax(axis=1), self.quantidade_classes)
        logs["val_loss"] = float(-np.mean(np.log(corretas)))
        logs["val_f1_macro"] = metricas["f1_macro"]


class MelhoresPesos(keras.callbacks.Callback):
    """Guarda os pesos da melhor época segundo o monitor, ao longo de todas as fases."""

    def __init__(self, monitor: str):
        super().__init__()
        self.monitor = monitor
        self.maior_melhor = MONITORES[monitor] == "max"
        self.melhor_valor = None
        self.melhor_epoca = None
        self.pesos = None

    def on_epoch_end(self, epoch, logs=None):
        valor = logs[self.monitor]
        if self.melhor_valor is None or (valor > self.melhor_valor if self.maior_melhor else valor < self.melhor_valor):
            self.melhor_valor = float(valor)
            self.melhor_epoca = epoch + 1
            self.pesos = self.model.get_weights()


def _executar_fase(
    modelo: keras.Model,
    config: dict,
    taxa: float,
    epoca_inicial: int,
    epocas: int,
    treino: SequenciaImagens,
    callbacks_comuns: list,
    class_weight: dict[int, float] | None,
    verbose: int,
) -> keras.callbacks.History:
    otimizador = OTIMIZADORES[config["otimizador"]["nome"]](learning_rate=taxa)
    modelo.compile(optimizer=otimizador, loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    parada = keras.callbacks.EarlyStopping(
        monitor=config["parada"]["monitor"],
        mode=MONITORES[config["parada"]["monitor"]],
        patience=config["parada"]["paciencia"],
        restore_best_weights=False,  # a restauração é feita por MelhoresPesos, entre fases
    )
    return modelo.fit(
        treino,
        epochs=epoca_inicial + epocas,
        initial_epoch=epoca_inicial,
        class_weight=class_weight,
        callbacks=[*callbacks_comuns, parada],
        verbose=verbose,
    )


def _sha256(caminho: Path) -> str:
    return sha256(Path(caminho).read_bytes()).hexdigest()


def _git(*argumentos: str) -> str | None:
    try:
        return subprocess.run(
            ["git", *argumentos], cwd=RAIZ, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _versao(pacote: str) -> str | None:
    try:
        return importlib.metadata.version(pacote)
    except importlib.metadata.PackageNotFoundError:
        return None


def _ambiente(caminho_indice: Path, caminho_pesos: Path, caminho_config: Path | None) -> dict:
    status = _git("status", "--porcelain")
    return {
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "keras_hub": _versao("keras-hub"),
        "numpy": np.__version__,
        "pillow": PIL.__version__,
        "dispositivos": [d.name for d in tf.config.list_physical_devices()],
        "git_commit": _git("rev-parse", "HEAD"),
        "git_alteracoes_locais": bool(status) if status is not None else None,
        "sha256": {
            "indice_pipeline": _sha256(caminho_indice),
            "pesos_classes": _sha256(caminho_pesos),
            "config": _sha256(caminho_config) if caminho_config else None,
        },
    }


def _pasta_rodada(saida: Path, backbone: str, semente: int) -> Path:
    base = f"{datetime.now():%Y%m%d-%H%M%S}_{backbone}_s{semente}"
    pasta = saida / base
    sufixo = 1
    while pasta.exists():
        sufixo += 1
        pasta = saida / f"{base}_{sufixo}"
    pasta.mkdir(parents=True)
    return pasta


def treinar(
    config: dict,
    raiz_imagens: Path,
    saida: Path = SAIDA_PADRAO,
    caminho_indice: Path = INDICE_PADRAO,
    caminho_pesos: Path = PESOS_PADRAO,
    caminho_config: Path | None = None,
    pesos_pre_treinados: bool = True,
    verbose: int = 2,
) -> Path:
    """Treina, avalia na validação e grava a rodada. Retorna a pasta da rodada."""
    validar_config(config, tuple(backbones.REGISTRO))
    backbone = backbones.obter(config["backbone"])
    configurar_sementes(config["semente"], config["deterministico"])

    indice = carregar_indice(caminho_indice)
    nomes = nomes_classes(indice)
    quantidade_classes = len(nomes)
    class_weight = (
        carregar_class_weight(caminho_pesos, quantidade_classes) if config["balanceamento"]["class_weight"] else None
    )
    tamanho = backbone.tamanho_entrada
    imagens_treino, rotulos_treino, sementes = preparar_particao(indice, "treino", raiz_imagens, tamanho)
    imagens_val, rotulos_val, _ = preparar_particao(indice, "validacao", raiz_imagens, tamanho)
    treino = SequenciaImagens(
        imagens_treino, rotulos_treino, "treino", config["batch"], config["semente"],
        sementes, aumentar=config["augmentation"]["ativo"],
    )
    validacao = SequenciaImagens(imagens_val, rotulos_val, "validacao", config["batch"])

    modelo, base = construir_modelo(backbone, quantidade_classes, config["cabeca"]["dropout"], pesos_pre_treinados)
    melhores = MelhoresPesos(config["parada"]["monitor"])
    callbacks_comuns = [SincronizarEpoca(treino), AvaliacaoValidacao(validacao, quantidade_classes), melhores]
    restaurar = config["parada"]["restaurar_melhores_pesos"]

    treinaveis_cabeca = contar_parametros(modelo.trainable_weights)
    historico = _executar_fase(
        modelo, config, config["otimizador"]["taxa_aprendizado"], 0, config["epocas_max"],
        treino, callbacks_comuns, class_weight, verbose,
    )
    linhas_historico = [("cabeca", historico)]
    epocas_cabeca = len(historico.epoch)
    epocas_ft = 0
    treinaveis_ft = None
    blocos_total = None

    if config["fine_tuning"]["ativo"]:
        if restaurar:
            modelo.set_weights(melhores.pesos)
        blocos_total = descongelar_blocos(base, backbone, config["fine_tuning"]["blocos_descongelados"])
        treinaveis_ft = contar_parametros(modelo.trainable_weights)
        historico_ft = _executar_fase(
            modelo, config, config["fine_tuning"]["taxa_aprendizado"], epocas_cabeca,
            config["fine_tuning"]["epocas_max"], treino, callbacks_comuns, class_weight, verbose,
        )
        linhas_historico.append(("fine_tuning", historico_ft))
        epocas_ft = len(historico_ft.epoch)

    if restaurar:
        modelo.set_weights(melhores.pesos)

    previstos = modelo.predict(validacao, verbose=0).argmax(axis=1)
    pasta = _pasta_rodada(Path(saida), backbone.nome, config["semente"])
    (pasta / "config_usada.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (pasta / "ambiente.json").write_text(
        json.dumps(_ambiente(caminho_indice, caminho_pesos, caminho_config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _gravar_historico(pasta / "historico.csv", linhas_historico)
    metricas = {
        "esquema": ESQUEMA_METRICAS,
        "backbone": backbone.nome,
        "fonte_pesos": backbone.fonte if pesos_pre_treinados else "sem pesos pré-treinados",
        "tamanho_entrada": tamanho,
        "faixa_entrada_backbone": backbone.faixa_esperada,
        "semente": config["semente"],
        "monitor": config["parada"]["monitor"],
        "pesos_finais": "melhor época" if restaurar else "última época",
        "melhor_epoca": melhores.melhor_epoca,
        "melhor_valor_monitor": melhores.melhor_valor,
        "epocas_executadas": {"cabeca": epocas_cabeca, "fine_tuning": epocas_ft},
        "fine_tuning": {
            "ativo": config["fine_tuning"]["ativo"],
            "blocos_descongelados": config["fine_tuning"]["blocos_descongelados"] if config["fine_tuning"]["ativo"] else 0,
            "blocos_na_base": blocos_total if blocos_total is not None else len(backbone.blocos(base)),
        },
        "parametros": {
            "total": int(modelo.count_params()),
            "base": int(base.count_params()),
            "treinaveis_cabeca": treinaveis_cabeca,
            "treinaveis_fine_tuning": treinaveis_ft,
        },
        "imagens": {"treino": int(len(rotulos_treino)), "validacao": int(len(rotulos_val))},
        "validacao": calcular_metricas(rotulos_val, previstos, quantidade_classes, nomes),
    }
    (pasta / "metricas_validacao.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    modelo.save(pasta / "melhor_modelo.keras")
    return pasta


def _gravar_historico(caminho: Path, fases: list[tuple[str, keras.callbacks.History]]) -> None:
    linhas = []
    for fase, historico in fases:
        for posicao, epoca in enumerate(historico.epoch):
            linha = {"fase": fase, "epoca": epoca + 1}
            linha.update({chave: float(valores[posicao]) for chave, valores in historico.history.items()})
            linhas.append(linha)
    campos = list(dict.fromkeys(chave for linha in linhas for chave in linha))
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Treinamento modular T5.1")
    parser.add_argument("--config", type=Path, required=True, help="JSON no formato de assets/data/treino_T5_1/config_base.json")
    parser.add_argument("--raiz-imagens", type=Path, required=True, help="Pasta que contém dataset/, Milho/ e Soja/")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="Pasta das rodadas (padrão: runs/)")
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO, help="Índice das amostras")
    parser.add_argument("--pesos", type=Path, default=PESOS_PADRAO, help="Pesos das classes")
    args = parser.parse_args()
    config = carregar_config(args.config, tuple(backbones.REGISTRO))
    pasta = treinar(
        config,
        args.raiz_imagens,
        args.saida,
        caminho_indice=args.indice,
        caminho_pesos=args.pesos,
        caminho_config=args.config,
    )
    metricas = json.loads((pasta / "metricas_validacao.json").read_text(encoding="utf-8"))
    print(f"Rodada gravada em: {pasta}")
    print(f"F1 macro na validação: {metricas['validacao']['f1_macro']}")


if __name__ == "__main__":
    main()
