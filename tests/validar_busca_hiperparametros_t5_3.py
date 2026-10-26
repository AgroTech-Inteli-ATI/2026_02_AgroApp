"""Valida a busca de hiperparâmetros T5.3.

As partes que dependem de TensorFlow/Keras são puladas se eles não estiverem
instalados, como em tests/validar_treinamento_t5_1.py.
"""

from hashlib import sha256
from pathlib import Path
import csv
import importlib.util
import json
import sys
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from src.busca_hiperparametros_t5_3 import (
    POLITICAS_FINE_TUNING,
    Trial,
    amostrar_trials,
    construir_config,
    executar_busca,
    politicas_validas,
    TAXAS_APRENDIZADO,
    TAMANHOS_LOTE,
    AUGMENTATION,
    verificar_entradas,
)
from src.config_treino import validar_config

TEM_TF = all(importlib.util.find_spec(m) for m in ("tensorflow", "keras"))


def _espera_erro(funcao, trecho: str = "") -> None:
    try:
        funcao()
    except ValueError as erro:
        assert trecho in str(erro), f"mensagem inesperada: {erro}"
    else:
        raise AssertionError("era esperado ValueError")


def validar_amostragem() -> None:
    rng_a = np.random.default_rng(7)
    rng_b = np.random.default_rng(7)
    trials_a = amostrar_trials("efficientnet_lite0", 6, rng_a, semente_base=42)
    trials_b = amostrar_trials("efficientnet_lite0", 6, rng_b, semente_base=42)
    assert trials_a == trials_b, "mesma semente deve produzir os mesmos trials"
    assert len(trials_a) == len({(t.taxa_aprendizado, t.batch, t.augmentation, t.politica_fine_tuning) for t in trials_a})
    assert all(t.politica_fine_tuning in POLITICAS_FINE_TUNING for t in trials_a)
    assert {t.taxa_aprendizado for t in trials_a} == set(TAXAS_APRENDIZADO)
    assert {t.batch for t in trials_a} == set(TAMANHOS_LOTE)
    assert {t.augmentation for t in trials_a} == set(AUGMENTATION)
    assert {t.politica_fine_tuning for t in trials_a} == set(POLITICAS_FINE_TUNING)

    # cnn_baseline não suporta fine-tuning: toda amostra cai em "sem_fine_tuning"
    assert politicas_validas("cnn_baseline") == ["sem_fine_tuning"]
    rng_c = np.random.default_rng(1)
    trials_cnn = amostrar_trials("cnn_baseline", 4, rng_c, semente_base=42)
    assert all(t.politica_fine_tuning == "sem_fine_tuning" for t in trials_cnn)
    print(f"OK: amostragem determinística e sem repetição ({len(trials_a)} trials), política fixa sem fine-tuning.")


def validar_cobertura_sem_tensorflow() -> None:
    with patch("src.busca_hiperparametros_t5_3.politicas_validas", return_value=list(POLITICAS_FINE_TUNING)):
        for quantidade in (3, 8, 54):
            trials = amostrar_trials("candidato", quantidade, np.random.default_rng(42), 42)
            assert len(trials) == quantidade
            assert len({(t.taxa_aprendizado, t.batch, t.augmentation, t.politica_fine_tuning)
                        for t in trials}) == quantidade
            assert {t.taxa_aprendizado for t in trials} == set(TAXAS_APRENDIZADO)
            assert {t.batch for t in trials} == set(TAMANHOS_LOTE)
            assert {t.augmentation for t in trials} == set(AUGMENTATION)
            assert {t.politica_fine_tuning for t in trials} == set(POLITICAS_FINE_TUNING)
        _espera_erro(lambda: amostrar_trials("candidato", 2, np.random.default_rng(1), 1), "entre 3 e 54")
        _espera_erro(lambda: amostrar_trials("candidato", 55, np.random.default_rng(1), 1), "entre 3 e 54")
    for nomes in (("a",), ("a", "a"), ("a", "b", "c", "d")):
        _espera_erro(lambda nomes=nomes: executar_busca(nomes, 3, Path("."), Path("."), 1, 1, 1),
                     "dois ou três backbones distintos")
    _espera_erro(lambda: executar_busca(("a", "b"), 2, Path("."), Path("."), 1, 1, 1),
                 "no mínimo 3")
    print("OK: cada dimensão é coberta por backbone; limites de trials e candidatos são validados.")


def validar_construcao_config() -> None:
    from src import backbones

    trial_sem = Trial("efficientnet_lite0", 1e-3, 32, True, "sem_fine_tuning", 42)
    config_sem = construir_config(trial_sem, blocos_base=10, epocas_max_cabeca=5, paciencia=2)
    validar_config(config_sem, tuple(backbones.REGISTRO))
    assert config_sem["fine_tuning"]["ativo"] is False
    assert config_sem["fine_tuning"]["blocos_descongelados"] == 0
    assert config_sem["augmentation"]["ativo"] is True
    assert config_sem["batch"] == 32

    trial_raso = Trial("mobilenet_v3_large", 1e-2, 16, False, "raso", 7)
    config_raso = construir_config(trial_raso, blocos_base=10, epocas_max_cabeca=5, paciencia=2)
    validar_config(config_raso, tuple(backbones.REGISTRO))
    assert config_raso["fine_tuning"]["ativo"] is True
    assert config_raso["fine_tuning"]["blocos_descongelados"] == max(1, round(0.15 * 10))
    assert config_raso["fine_tuning"]["taxa_aprendizado"] < config_raso["otimizador"]["taxa_aprendizado"]

    trial_profundo = Trial("mobilenet_v3_large", 1e-2, 16, False, "profundo", 7)
    config_profundo = construir_config(trial_profundo, blocos_base=10, epocas_max_cabeca=5, paciencia=2)
    assert config_profundo["fine_tuning"]["blocos_descongelados"] == max(1, round(0.5 * 10))
    assert config_profundo["fine_tuning"]["blocos_descongelados"] > config_raso["fine_tuning"]["blocos_descongelados"]

    # blocos_base pequeno: a fração nunca deve passar do total disponível
    trial_pequeno = Trial("mobilenet_v3_large", 1e-2, 16, False, "profundo", 7)
    config_pequeno = construir_config(trial_pequeno, blocos_base=1, epocas_max_cabeca=5, paciencia=2)
    assert config_pequeno["fine_tuning"]["blocos_descongelados"] == 1
    print("OK: configs geradas passam em validar_config; frações de blocos crescem com a política e respeitam o total.")


def validar_selecao_melhores() -> None:
    from src.busca_hiperparametros_t5_3 import _selecionar_melhores

    linhas = [
        {"backbone": "a", "val_f1_macro": 0.3},
        {"backbone": "a", "val_f1_macro": 0.5},
        {"backbone": "a", "val_f1_macro": None},  # trial que falhou, deve ser ignorado
        {"backbone": "b", "val_f1_macro": 0.4},
    ]
    melhores = _selecionar_melhores(linhas)
    assert melhores["por_backbone"]["a"]["val_f1_macro"] == 0.5
    assert melhores["por_backbone"]["b"]["val_f1_macro"] == 0.4
    assert [l["backbone"] for l in melhores["ranking_geral"]] == ["a", "b"]
    print("OK: seleção dos melhores ignora trials com erro e ranqueia por val_f1_macro.")


def validar_auditoria_cobertura() -> None:
    from src.busca_hiperparametros_t5_3 import _auditar_cobertura

    with patch("src.busca_hiperparametros_t5_3.politicas_validas", return_value=list(POLITICAS_FINE_TUNING)):
        trials = amostrar_trials("candidato", 3, np.random.default_rng(42), 42)
        linhas = [dict(backbone="candidato", taxa_aprendizado=t.taxa_aprendizado,
                       batch=t.batch, augmentation=t.augmentation,
                       politica_fine_tuning=t.politica_fine_tuning, val_f1_macro=0.5)
                  for t in trials]
        completa = _auditar_cobertura(linhas, ("candidato",))["candidato"]
        assert completa["cobertura_completa"]
        linhas[0]["val_f1_macro"] = None
        incompleta = _auditar_cobertura(linhas, ("candidato",))["candidato"]
        assert not incompleta["cobertura_completa"]
        assert incompleta["trials_concluidos"] == 2
        assert any(incompleta["valores_sem_avaliacao"].values())
    print("OK: auditoria distingue trials concluídos de trials com erro.")


def _criar_base_sintetica(pasta: Path) -> tuple[Path, Path]:
    """2 classes; 4 imagens de treino e 2 de validação por classe (sem teste)."""
    from src.pipeline_preparacao_t4_5 import _semente_amostra

    cores = [(200, 40, 40), (40, 200, 40)]
    rng = np.random.default_rng(0)
    linhas = []
    for classe, cor in enumerate(cores):
        for particao, quantidade in (("treino", 4), ("validacao", 2)):
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
        "quantidade_classes": 2,
        "classes": {str(c): {"nome_classe": f"Classe {c}", "imagens_treino": 4, "peso": 1.0} for c in range(2)},
    }), encoding="utf-8")
    return indice, pesos


def validar_entradas_sem_tensorflow() -> None:
    with tempfile.TemporaryDirectory(prefix="entradas-t5-4-") as temporario:
        pasta = Path(temporario)
        indice, pesos = _criar_base_sintetica(pasta)
        assert verificar_entradas(pasta / "imagens", indice, pesos) == {"treino": 8, "validacao": 4}
        imagem = next((pasta / "imagens").rglob("*.png"))
        imagem.unlink()
        try:
            verificar_entradas(pasta / "imagens", indice, pesos)
        except FileNotFoundError as erro:
            assert "1 imagens" in str(erro)
        else:
            raise AssertionError("imagem ausente deveria impedir a busca")
    print("OK: pré-verificação das imagens e pesos antes de iniciar a busca.")


def validar_contar_blocos() -> None:
    from src.busca_hiperparametros_t5_3 import contar_blocos

    assert contar_blocos("cnn_baseline") == 0, "cnn_baseline não suporta fine-tuning"
    assert contar_blocos("mobilenet_v2") > 0
    print("OK: contar_blocos devolve 0 para backbone sem fine-tuning e > 0 para os demais.")


def validar_smoke_busca() -> None:
    from src.busca_hiperparametros_t5_3 import executar_busca

    with tempfile.TemporaryDirectory(prefix="teste-t5-3-") as temporario:
        pasta = Path(temporario)
        indice, pesos = _criar_base_sintetica(pasta)
        saida = executar_busca(
            backbones_candidatos=("mobilenet_v2", "mobilenet_v3_small"),
            trials_por_backbone=3,
            saida=pasta / "busca",
            raiz_imagens=pasta / "imagens",
            epocas_max_cabeca=1,
            paciencia=1,
            semente_busca=1,
            caminho_indice=indice,
            caminho_pesos=pesos,
            verbose=0,
        )
        with (saida / "resultados.csv").open(encoding="utf-8") as arquivo:
            resultados = list(csv.DictReader(arquivo))
        assert len(resultados) == 6
        assert {r["backbone"] for r in resultados} == {"mobilenet_v2", "mobilenet_v3_small"}
        assert all(r["erro"] == "" for r in resultados), [r["erro"] for r in resultados]
        melhores = json.loads((saida / "melhores_por_backbone.json").read_text(encoding="utf-8"))
        assert set(melhores["por_backbone"]) == {"mobilenet_v2", "mobilenet_v3_small"}
        assert len(melhores["ranking_geral"]) == 2
        print("OK: smoke test da busca com dados sintéticos (3 trials por backbone).")


if __name__ == "__main__":
    validar_cobertura_sem_tensorflow()
    validar_selecao_melhores()
    validar_auditoria_cobertura()
    validar_entradas_sem_tensorflow()
    if TEM_TF:
        # amostrar_trials passa por politicas_validas -> src.backbones, que importa
        # keras incondicionalmente (mesma convenção de tests/validar_treinamento_t5_1.py).
        validar_amostragem()
        validar_construcao_config()
        validar_contar_blocos()
        validar_smoke_busca()
    else:
        print("AVISO: TensorFlow/Keras não instalados; testes dependentes de backbones foram pulados.")
