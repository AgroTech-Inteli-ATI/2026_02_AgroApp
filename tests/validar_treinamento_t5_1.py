"""Valida o pipeline de treinamento modular T5.1.

As partes que dependem de TensorFlow/Keras são puladas se eles não estiverem
instalados. O smoke test treina duas configs que diferem só na linha `backbone`,
com imagens sintéticas.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import copy
import csv
import importlib.util
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from src.avaliacao import NAO_AVALIADA, calcular_metricas
from src.config_treino import carregar_config, validar_config
from src.dados_treino import (
    SequenciaImagens,
    carregar_class_weight,
    carregar_indice,
    nomes_classes,
    preparar_particao,
)

CONFIG_BASE = ROOT / "assets/data/treino_T5_1/config_base.json"
PESOS = ROOT / "assets/data/pipeline_T4_5/pesos_classes.json"
TEM_TF = all(importlib.util.find_spec(m) for m in ("tensorflow", "keras"))


def _espera_erro(funcao, trecho: str = "") -> None:
    try:
        funcao()
    except ValueError as erro:
        assert trecho in str(erro), f"mensagem inesperada: {erro}"
    else:
        raise AssertionError("era esperado ValueError")


def validar_config_base() -> None:
    config = carregar_config(CONFIG_BASE)
    for alteracao, trecho in (
        (lambda c: c.pop("parada"), "faltando"),
        (lambda c: c.update(tamanho_entrada=224), "desconhecidas"),
        (lambda c: c.update(batch="32"), "inteiro"),
        (lambda c: c["parada"].update(monitor="val_accuracy"), "monitor"),
        (lambda c: c["fine_tuning"].update(taxa_aprendizado=0.01), "menor"),
        (lambda c: c["cabeca"].update(dropout=1.0), "dropout"),
    ):
        alterada = copy.deepcopy(config)
        alteracao(alterada)
        _espera_erro(lambda: validar_config(alterada), trecho)
    _espera_erro(lambda: validar_config(config, ("outro",)), "não registrado")
    print("OK: esquema da config e rejeição de chaves, tipos e faixas inválidos.")


def validar_metricas() -> None:
    # 4 classes; a classe 3 não tem exemplo. Valores calculados à mão:
    # classe 0: P=1/3, R=1/2, F1=0,4 | classe 1: P=R=F1=2/3 | classe 2: P=R=F1=0
    rotulos = np.array([0, 0, 1, 1, 1, 2])
    previstos = np.array([0, 1, 1, 1, 0, 0])
    m = calcular_metricas(rotulos, previstos, 4, ["a", "b", "c", "d"])
    assert m["matriz_confusao"] == [[1, 1, 0, 0], [1, 2, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]]
    c0, c1, c2, c3 = m["por_classe"]
    assert np.isclose(c0["precisao"], 1 / 3) and np.isclose(c0["recall"], 1 / 2) and np.isclose(c0["f1"], 0.4)
    assert np.isclose(c1["precisao"], 2 / 3) and np.isclose(c1["recall"], 2 / 3) and np.isclose(c1["f1"], 2 / 3)
    assert c2["precisao"] == 0 and c2["recall"] == 0 and c2["f1"] == 0 and c2["suporte"] == 1
    assert c3["status"] == NAO_AVALIADA and c3["f1"] is None and c3["suporte"] == 0
    assert np.isclose(m["f1_macro"], (0.4 + 2 / 3 + 0) / 3)
    assert np.isclose(m["balanced_accuracy"], (1 / 2 + 2 / 3 + 0) / 3)
    assert np.isclose(m["acuracia"], 0.5)
    assert m["classes_avaliadas"] == 3 and m["classes_nao_avaliadas"] == [3]
    print("OK: métricas conferidas com caso calculado à mão, incluindo classe não avaliada.")


def validar_dados() -> None:
    indice = carregar_indice()
    assert len(indice) == 3163 and len(nomes_classes(indice)) == 13

    # class_weight igual ao JSON da T4.5, com chaves inteiras 0..12
    pesos = carregar_class_weight(PESOS, 13)
    bruto = json.loads(PESOS.read_text(encoding="utf-8"))["classes"]
    assert pesos == {int(k): v["peso"] for k, v in bruto.items()} and list(pesos) == list(range(13))
    _espera_erro(lambda: carregar_class_weight(PESOS, 12), "0 a 11")

    # o teste é recusado no carregamento e na sequência
    _espera_erro(lambda: preparar_particao(indice, "teste", Path("."), 224), "reservado")
    imagens = np.random.default_rng(0).integers(0, 256, (6, 32, 32, 3), dtype=np.uint8)
    rotulos = np.arange(6) % 3
    sementes = np.array([11, 22, 33, 44, 55, 66], dtype=np.uint64)
    _espera_erro(lambda: SequenciaImagens(imagens, rotulos, "teste", 2), "reservado")
    _espera_erro(lambda: SequenciaImagens(imagens, rotulos, "validacao", 2, 0, sementes, aumentar=True), "treino")

    # augmentation: muda entre épocas, igual para a mesma (imagem, época)
    treino = SequenciaImagens(imagens, rotulos, "treino", 2, 42, sementes, aumentar=True)
    outra = SequenciaImagens(imagens, rotulos, "treino", 2, 42, sementes, aumentar=True)
    epoca0 = [treino.amostra(i) for i in range(6)]
    assert all(np.array_equal(a, outra.amostra(i)) for i, a in enumerate(epoca0)), "mesma (imagem, época) diverge"
    ordem0 = treino.ordem.copy()
    treino.definir_epoca(1)
    epoca1 = [treino.amostra(i) for i in range(6)]
    assert sum(not np.array_equal(a, b) for a, b in zip(epoca0, epoca1)) >= 5, "augmentation repetido entre épocas"
    assert not np.array_equal(ordem0, treino.ordem), "ordem de treino não muda entre épocas"
    treino.definir_epoca(0)
    assert all(np.array_equal(a, treino.amostra(i)) for i, a in enumerate(epoca0))

    # validação: nunca aumentada e sempre na mesma ordem
    validacao = SequenciaImagens(imagens, rotulos, "validacao", 4)
    for epoca in range(3):
        validacao.definir_epoca(epoca)
        lote, alvo = validacao[0]
        assert np.array_equal(lote, imagens[:4].astype(np.float32) / 255.0) and np.array_equal(alvo, rotulos[:4])
    print("OK: índice, class_weight, recusa do teste e augmentation por (imagem, época) só no treino.")


def validar_backbones() -> None:
    import keras
    from src import backbones
    from src.treinamento_t5_1 import construir_modelo, descongelar_blocos

    zeros_uns = np.stack([np.zeros((2, 2, 3)), np.ones((2, 2, 3))]).astype(np.float32)
    media = np.array(backbones.MEDIA_IMAGENET, np.float32)
    desvio = np.array(backbones.DESVIO_IMAGENET, np.float32)
    esperado = {
        "cnn_baseline": (0.0, 1.0),
        "mobilenet_v2": (-1.0, 1.0),
        "efficientnet_lite0": (-media / desvio, (1 - media) / desvio),
    }
    blocos_por_backbone = {}
    for nome, backbone in backbones.REGISTRO.items():
        convertido = backbone.camada_conversao()(zeros_uns).numpy()
        minimo, maximo = esperado.get(nome, (0.0, 255.0))
        assert np.allclose(convertido[0, 0, 0], minimo, atol=1e-5) and np.allclose(convertido[1, 0, 0], maximo, atol=1e-4), nome
        try:
            modelo, base = construir_modelo(backbone, 13, 0.2, pesos_pre_treinados=False)
        except Exception as erro:  # a Lite0 precisa baixar a config do preset na primeira vez
            if nome == "efficientnet_lite0":
                print(f"AVISO: {nome} pulado ({type(erro).__name__}: {erro})")
                continue
            raise
        t = backbone.tamanho_entrada
        assert modelo.input_shape == (None, t, t, 3) and modelo.output_shape == (None, 13), nome
        assert modelo.layers[1].name == "conversao_entrada"
        assert base.trainable == (not backbone.congelar_inicialmente), nome
        assert modelo.layers[1](np.ones((1, t, t, 3), np.float32)).shape == (1, t, t, 3)
        blocos = backbone.blocos(base)
        blocos_por_backbone[nome] = len(blocos)

        if not backbone.suporta_fine_tuning:
            _espera_erro(lambda: descongelar_blocos(base, backbone, 1), "não suporta")
            assert base.trainable, f"{nome}: a base do baseline deve treinar desde o início"
            continue

        assert base.layers[1] not in blocos[0], f"{nome}: stem não deveria contar como bloco"
        # fine-tuning: últimos 2 blocos, BatchNorm congelado, stem congelado
        total = descongelar_blocos(base, backbone, 2)
        selecionadas = {id(c) for bloco in blocos[-2:] for c in bloco}
        for camada in base.layers:
            if camada.trainable:
                assert id(camada) in selecionadas and not isinstance(camada, keras.layers.BatchNormalization), camada.name
        assert any(c.trainable and c.weights for c in blocos[-1]), f"{nome}: último bloco não descongelado"
        _espera_erro(lambda: descongelar_blocos(base, backbone, total + 1), "fora de")
        _espera_erro(
            lambda: descongelar_blocos(base, replace(backbone, suporta_fine_tuning=False), 1), "não suporta"
        )

        if nome == "efficientnet_lite0":
            import keras_hub
            conversor = keras_hub.layers.ImageConverter.from_preset(backbones.PRESET_LITE0)
            amostra = np.random.default_rng(0).random((1, t, t, 3), dtype=np.float32)
            nosso = backbone.camada_conversao()(amostra).numpy()
            deles = conversor(amostra * 255.0).numpy()
            assert np.allclose(nosso, deles, atol=1e-4), "conversão da Lite0 diverge do pré-processador do preset"
    print(f"OK: {len(blocos_por_backbone)} backbones montados sem pesos; blocos por backbone: {blocos_por_backbone}.")


def validar_epoca_no_fit() -> None:
    """Durante o fit, cada lote usa a época corrente, inclusive com initial_epoch (fine-tuning)."""
    import keras
    from src.treinamento_t5_1 import SincronizarEpoca

    class Registradora(SequenciaImagens):
        """Separa os lotes gerados dentro das épocas das leituras que o Keras faz
        no início do fit só para inferir o formato dos dados."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.dentro_da_epoca = False
            self.chamadas, self.leituras_de_formato = [], 0

        def __getitem__(self, lote):
            if self.dentro_da_epoca:
                self.chamadas.append(self.epoca)
            else:
                self.leituras_de_formato += 1
            return super().__getitem__(lote)

    class MarcarEpoca(keras.callbacks.Callback):
        def __init__(self, sequencia):
            super().__init__()
            self.sequencia = sequencia

        def on_epoch_begin(self, epoch, logs=None):
            self.sequencia.dentro_da_epoca = True

        def on_epoch_end(self, epoch, logs=None):
            self.sequencia.dentro_da_epoca = False

    imagens = np.random.default_rng(0).integers(0, 256, (8, 8, 8, 3), dtype=np.uint8)
    sequencia = Registradora(imagens, np.arange(8) % 3, "treino", 4, 42, np.arange(8, dtype=np.uint64), aumentar=True)
    modelo = keras.Sequential([keras.Input((8, 8, 3)), keras.layers.Flatten(), keras.layers.Dense(3, activation="softmax")])
    modelo.compile("sgd", "sparse_categorical_crossentropy")
    callbacks = [SincronizarEpoca(sequencia), MarcarEpoca(sequencia)]
    modelo.fit(sequencia, epochs=3, callbacks=callbacks, verbose=0)
    modelo.fit(sequencia, initial_epoch=3, epochs=5, callbacks=callbacks, verbose=0)
    esperadas = [e for e in range(5) for _ in range(len(sequencia))]
    assert sequencia.chamadas == esperadas, sequencia.chamadas
    print(
        "OK: no fit, cada lote de treino é gerado com a época corrente (0 a 4, com initial_epoch "
        f"no fine-tuning); {sequencia.leituras_de_formato} leituras de formato fora das épocas."
    )


def _criar_base_sintetica(pasta: Path) -> tuple[Path, Path]:
    """3 classes; 3 imagens de treino, 2 de validação e 1 de teste por classe."""
    from src.pipeline_preparacao_t4_5 import _semente_amostra

    cores = [(200, 40, 40), (40, 200, 40), (40, 40, 200)]
    rng = np.random.default_rng(0)
    linhas = []
    for classe, cor in enumerate(cores):
        for particao, quantidade in (("treino", 3), ("validacao", 2), ("teste", 1)):
            for n in range(quantidade):
                relativo = f"dataset/field/classe_{classe}/{particao}_{n}.png"
                arquivo = pasta / "imagens" / relativo
                arquivo.parent.mkdir(parents=True, exist_ok=True)
                ruido = rng.integers(-30, 30, (90, 120, 3))
                Image.fromarray(np.clip(np.array(cor) + ruido, 0, 255).astype(np.uint8)).save(arquivo)
                image_id = f"IMG_{classe}{particao[0]}{n}"
                linhas.append({
                    "image_id": image_id,
                    "caminho_relativo": relativo,
                    "sha256_original": sha256(arquivo.read_bytes()).hexdigest(),
                    "indice_modelo": str(classe),
                    "nome_classe_modelo": f"Classe {classe}",
                    "grupo_particao": f"GRP-{image_id}",
                    "particao": particao,
                    "peso_classe_treino": "1.0" if particao == "treino" else "",
                    "aplicar_augmentation": "sim" if particao == "treino" else "nao",
                    "semente_augmentation": str(_semente_amostra(image_id)) if particao == "treino" else "",
                    "sha256_preprocessamento": "",
                    "sha256_augmentation": "",
                })
    indice = pasta / "indice_pipeline.csv"
    with indice.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    pesos = pasta / "pesos_classes.json"
    pesos.write_text(json.dumps({
        "quantidade_classes": 3,
        "classes": {str(c): {"nome_classe": f"Classe {c}", "imagens_treino": 3, "peso": 1.0} for c in range(3)},
    }), encoding="utf-8")
    return indice, pesos


def validar_smoke() -> None:
    import keras
    from src.treinamento_t5_1 import ESQUEMA_METRICAS, treinar

    base = carregar_config(CONFIG_BASE)
    base.update(batch=4, epocas_max=1)
    base["parada"]["paciencia"] = 1
    base["fine_tuning"].update(ativo=True, blocos_descongelados=1, epocas_max=1)
    config_a = dict(copy.deepcopy(base), backbone="mobilenet_v3_small")
    config_b = dict(copy.deepcopy(base), backbone="mobilenet_v2")
    diferentes = {chave for chave in config_a if config_a[chave] != config_b[chave]}
    assert diferentes == {"backbone"}, diferentes

    with tempfile.TemporaryDirectory(prefix="teste-t5-1-") as temporario:
        pasta = Path(temporario)
        indice, pesos = _criar_base_sintetica(pasta)
        for config in (config_a, config_b):
            caminho_config = pasta / f"config_{config['backbone']}.json"
            caminho_config.write_text(json.dumps(config, indent=2), encoding="utf-8")
            rodada = treinar(
                carregar_config(caminho_config), pasta / "imagens", pasta / "runs", indice, pesos,
                caminho_config, pesos_pre_treinados=False, verbose=0,
            )
            arquivos = {p.name for p in rodada.iterdir()}
            assert arquivos == {"config_usada.json", "ambiente.json", "historico.csv",
                                "metricas_validacao.json", "melhor_modelo.keras"}, arquivos
            assert json.loads((rodada / "config_usada.json").read_text(encoding="utf-8")) == config
            metricas = json.loads((rodada / "metricas_validacao.json").read_text(encoding="utf-8"))
            assert metricas["esquema"] == ESQUEMA_METRICAS and metricas["backbone"] == config["backbone"]
            assert metricas["imagens"] == {"treino": 9, "validacao": 6}, "o teste não pode ser carregado"
            assert metricas["epocas_executadas"] == {"cabeca": 1, "fine_tuning": 1}
            assert 0 < metricas["parametros"]["treinaveis_cabeca"] < metricas["parametros"]["treinaveis_fine_tuning"]
            assert len(metricas["validacao"]["por_classe"]) == 3
            with (rodada / "historico.csv").open(encoding="utf-8") as arquivo:
                historico = list(csv.DictReader(arquivo))
            assert [h["fase"] for h in historico] == ["cabeca", "fine_tuning"]
            assert all(h["val_f1_macro"] and h["val_loss"] for h in historico)
            ambiente = json.loads((rodada / "ambiente.json").read_text(encoding="utf-8"))
            assert ambiente["sha256"]["indice_pipeline"] == sha256(indice.read_bytes()).hexdigest()
            recarregado = keras.models.load_model(rodada / "melhor_modelo.keras")
            assert recarregado.input_shape == (None, metricas["tamanho_entrada"], metricas["tamanho_entrada"], 3)
            print(
                f"   smoke {config['backbone']}: entrada {metricas['tamanho_entrada']} px | "
                f"épocas {metricas['epocas_executadas']} | parâmetros {metricas['parametros']} | "
                f"F1 macro val {metricas['validacao']['f1_macro']:.3f} | arquivos {sorted(arquivos)}"
            )
    print("OK: smoke test de ponta a ponta com duas configs que diferem só no backbone.")


if __name__ == "__main__":
    validar_config_base()
    validar_metricas()
    validar_dados()
    if TEM_TF:
        validar_backbones()
        validar_epoca_no_fit()
        validar_smoke()
    else:
        print("AVISO: TensorFlow/Keras não instalados; testes de backbones e smoke test pulados.")
