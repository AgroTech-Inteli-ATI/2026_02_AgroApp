"""Prepara o recorte reproduzível usado pelo baseline T5.2.

O baseline usa somente a fonte nova ``dataset/``. O índice original da T4.5
permanece intacto; este módulo filtra as sete imagens dos acervos antigos e
recalcula os pesos exclusivamente sobre o treino resultante.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import csv
import json


RAIZ = Path(__file__).resolve().parents[1]
INDICE_ORIGEM = RAIZ / "assets/data/pipeline_T4_5/indice_pipeline.csv"
SAIDA_PADRAO = RAIZ / "assets/data/treino_T5_2"
PREFIXO_INCLUIDO = "dataset/"


def _hash(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def gerar(saida: Path = SAIDA_PADRAO, indice_origem: Path = INDICE_ORIGEM) -> dict:
    with Path(indice_origem).open(encoding="utf-8-sig", newline="") as arquivo:
        todas = list(csv.DictReader(arquivo))
    if not todas:
        raise ValueError("índice da T4.5 vazio")

    incluidas = [linha for linha in todas if linha["caminho_relativo"].startswith(PREFIXO_INCLUIDO)]
    excluidas = [linha for linha in todas if linha not in incluidas]
    contagens_particao = Counter(linha["particao"] for linha in incluidas)
    if len(incluidas) != 3156 or contagens_particao != {
        "treino": 2209,
        "validacao": 474,
        "teste": 473,
    }:
        raise ValueError(f"recorte dataset inesperado: {len(incluidas)}; {dict(contagens_particao)}")

    nomes = {int(linha["indice_modelo"]): linha["nome_classe_modelo"] for linha in incluidas}
    if sorted(nomes) != list(range(13)):
        raise ValueError("o recorte não preservou as 13 classes")
    treino = [linha for linha in incluidas if linha["particao"] == "treino"]
    contagens_classes = Counter(int(linha["indice_modelo"]) for linha in treino)
    if sorted(contagens_classes) != list(range(13)):
        raise ValueError("há classe sem imagem de treino no recorte")

    total_treino = len(treino)
    quantidade_classes = len(nomes)
    pesos = {
        str(indice): {
            "nome_classe": nomes[indice],
            "imagens_treino": contagens_classes[indice],
            "peso": total_treino / (quantidade_classes * contagens_classes[indice]),
        }
        for indice in sorted(nomes)
    }

    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    caminho_indice = saida / "indice_dataset.csv"
    with caminho_indice.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(incluidas[0]))
        escritor.writeheader()
        escritor.writerows(incluidas)

    caminho_pesos = saida / "pesos_dataset.json"
    caminho_pesos.write_text(
        json.dumps(
            {
                "formula": "N / (K * n_c)",
                "calculado_somente_sobre": "imagens de treino da fonte dataset/",
                "total_treino": total_treino,
                "quantidade_classes": quantidade_classes,
                "classes": pesos,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    auditoria = {
        "regra_inclusao": f"caminho_relativo começa com {PREFIXO_INCLUIDO}",
        "indice_origem": "assets/data/pipeline_T4_5/indice_pipeline.csv",
        "indice_origem_sha256": _hash(Path(indice_origem)),
        "imagens_incluidas": len(incluidas),
        "imagens_excluidas": len(excluidas),
        "ids_excluidos": [linha["image_id"] for linha in excluidas],
        "imagens_por_particao": dict(contagens_particao),
        "classes": quantidade_classes,
        "indice_dataset_sha256": _hash(caminho_indice),
        "pesos_dataset_sha256": _hash(caminho_pesos),
    }
    (saida / "auditoria_dataset.json").write_text(
        json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return auditoria


if __name__ == "__main__":
    print(json.dumps(gerar(), ensure_ascii=False, indent=2))
