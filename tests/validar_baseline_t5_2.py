"""Valida o recorte dos dados e a configuração do baseline T5.2."""

from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from src.config_treino import carregar_config
from src.preparar_baseline_t5_2 import gerar


def _hash(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def validar() -> None:
    with tempfile.TemporaryDirectory(prefix="t5-2-a-") as a, tempfile.TemporaryDirectory(
        prefix="t5-2-b-"
    ) as b:
        saida_a, saida_b = Path(a), Path(b)
        auditoria_a = gerar(saida_a)
        auditoria_b = gerar(saida_b)
        assert auditoria_a == auditoria_b
        assert auditoria_a["imagens_incluidas"] == 3156
        assert auditoria_a["imagens_excluidas"] == 7
        assert auditoria_a["imagens_por_particao"] == {
            "treino": 2209,
            "validacao": 474,
            "teste": 473,
        }
        assert auditoria_a["classes"] == 13
        for nome in ("indice_dataset.csv", "pesos_dataset.json", "auditoria_dataset.json"):
            assert _hash(saida_a / nome) == _hash(saida_b / nome), nome

        with (saida_a / "indice_dataset.csv").open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        assert all(linha["caminho_relativo"].startswith("dataset/") for linha in linhas)
        pesos = json.loads((saida_a / "pesos_dataset.json").read_text(encoding="utf-8"))
        media = sum(
            item["imagens_treino"] * item["peso"] for item in pesos["classes"].values()
        ) / pesos["total_treino"]
        assert abs(media - 1.0) < 1e-12

    config = carregar_config(ROOT / "assets/data/treino_T5_2/config_baseline.json")
    assert config["backbone"] == "cnn_baseline"
    assert config["fine_tuning"]["ativo"] is False
    assert config["augmentation"]["ativo"] is True
    assert config["balanceamento"]["class_weight"] is True

    pasta_modelo = ROOT / "assets/modelos/baseline_T5_2"
    metricas = json.loads((pasta_modelo / "metricas_validacao.json").read_text(encoding="utf-8"))
    reproducao = json.loads((pasta_modelo / "reprodutibilidade.json").read_text(encoding="utf-8"))
    assert metricas["backbone"] == "cnn_baseline"
    assert metricas["imagens"] == {"treino": 2209, "validacao": 474}
    assert metricas["melhor_epoca"] == 10
    assert abs(metricas["validacao"]["f1_macro"] - 0.12027512666905406) < 1e-15
    assert reproducao["historicos_identicos"] is True
    assert reproducao["metricas_identicas"] is True
    assert reproducao["pesos_identicos"] is True

    if importlib.util.find_spec("keras"):
        import keras

        modelo = keras.models.load_model(pasta_modelo / "melhor_modelo.keras")
        assert modelo.input_shape == (None, 224, 224, 3)
        assert modelo.output_shape == (None, 13)
        assert modelo.count_params() == 24429
    print("OK: baseline usa somente dataset/, preserva 13 classes e recalcula os pesos do treino.")


if __name__ == "__main__":
    validar()
