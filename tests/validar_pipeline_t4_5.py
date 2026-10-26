"""Valida reprodução, balanceamento e isolamento do pipeline T4.5."""

from pathlib import Path
import csv
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from src.pipeline_preparacao_t4_5 import executar


def hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def validar():
    auditoria_aprovada = json.loads(
        (ROOT / "assets/data/particionamento_T4_2/auditoria_modelo.json").read_text(
            encoding="utf-8"
        )
    )
    for campo, relativo in (
        ("diagnostico_sha256", "assets/data/diagnostico_qualidade_T3_3_revisado.xlsx"),
        ("dicionario_sha256", "assets/data/dicionario-classes.json"),
        ("classes_modelo_sha256", "assets/data/classes-modelo.csv"),
    ):
        dados = (ROOT / relativo).read_bytes()
        if not relativo.endswith(".xlsx"):
            dados = dados.replace(b"\r\n", b"\n")
        assert auditoria_aprovada[campo] == hashlib.sha256(dados).hexdigest(), campo

    with tempfile.TemporaryDirectory(prefix="teste-t4-5-a-") as a, tempfile.TemporaryDirectory(
        prefix="teste-t4-5-b-"
    ) as b:
        saida_a, saida_b = Path(a), Path(b)
        auditoria_a = executar(ROOT, saida_a)
        auditoria_b = executar(ROOT, saida_b)

        assert auditoria_a == auditoria_b
        assert auditoria_a["particionamento_reproduzido"] is True
        assert auditoria_a["augmentation_somente_treino"] is True
        assert auditoria_a["pesos_calculados_somente_no_treino"] is True
        assert auditoria_a["imagens_por_particao"] == {
            "treino": 2214, "validacao": 475, "teste": 474
        }
        assert auditoria_a["classes_modelo"] == 13

        try:
            executar(ROOT, saida_a, semente=41)
        except ValueError as erro:
            assert "semente fixa 42" in str(erro)
        else:
            raise AssertionError("o pipeline aceitou uma semente diferente da T4.2")

        for nome in ("indice_pipeline.csv", "pesos_classes.json", "parametros.json", "auditoria.json"):
            assert hash_arquivo(saida_a / nome) == hash_arquivo(saida_b / nome), nome

        with (saida_a / "indice_pipeline.csv").open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        assert len(linhas) == 3163
        assert all(
            (linha["particao"] == "treino") == (linha["aplicar_augmentation"] == "sim")
            for linha in linhas
        )
        assert all(
            bool(linha["semente_augmentation"]) == (linha["particao"] == "treino")
            for linha in linhas
        )
        assert all(
            bool(linha["peso_classe_treino"]) == (linha["particao"] == "treino")
            for linha in linhas
        )
        assert all(len(linha["sha256_original"]) == 64 for linha in linhas)
        assert all(len(linha["sha256_preprocessamento"]) == 64 for linha in linhas)
        assert all(not linha["sha256_augmentation"] for linha in linhas)

        pesos = json.loads((saida_a / "pesos_classes.json").read_text(encoding="utf-8"))
        media = sum(
            item["imagens_treino"] * item["peso"] for item in pesos["classes"].values()
        ) / pesos["total_treino"]
        assert abs(media - 1.0) < 1e-12

    print(
        "OK: T4.5 reproduz T4.2; 3.163 imagens/13 classes; pesos só no treino; "
        "augmentation bloqueado em validação e teste."
    )


if __name__ == "__main__":
    validar()
