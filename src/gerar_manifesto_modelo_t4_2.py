"""Gera a partição T4.2 para as classes selecionadas na T3.5."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from src.particionamento_t4_2 import (
    carregar_dados,
    construir_grupos,
    hash_texto_versionado,
    separar_grupos,
)


# O dicionário T3.4 registra o agente de AGRO-003 como indeterminado.
ACERVO_SEM_IDENTIFICACAO_CONFIRMADA = {"AGRO-003"}


def carregar_classes(caminho: Path) -> tuple[pd.DataFrame, dict[str, tuple[int, str]]]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        classes = pd.DataFrame(csv.DictReader(arquivo, delimiter=";"))
    indices = classes["indice_modelo"].astype(int).tolist()
    assert indices == list(range(len(indices))), "Índices do modelo não são consecutivos"
    assert len(classes) == 13, "A T3.5 deve definir 13 classes"
    mapa: dict[str, tuple[int, str]] = {}
    for linha in classes.itertuples(index=False):
        ids_dataset = str(linha.ids_inventario).split(";")
        ids_acervo = str(linha.ids_acervo).split(";") if linha.ids_acervo else []
        for identificador in ids_dataset:
            chave = f"DATASET-{int(identificador):02d}"
            assert chave not in mapa
            mapa[chave] = (int(linha.indice_modelo), linha.classe)
        for chave in ids_acervo:
            if chave not in ACERVO_SEM_IDENTIFICACAO_CONFIRMADA:
                assert chave not in mapa
                mapa[chave] = (int(linha.indice_modelo), linha.classe)
    assert {f"DATASET-{i:02d}" for i in range(14)} <= set(mapa)
    return classes, mapa


def gerar(raiz: Path, pasta_saida: Path | None = None) -> Path:
    caminho_classes = raiz / "assets/data/classes-modelo.csv"
    classes, mapa = carregar_classes(caminho_classes)
    mantidas, pares_visuais, proveniencia = carregar_dados(raiz)
    selecionadas = mantidas.loc[mantidas["classe_candidata"].isin(mapa)].copy()
    excluidas = mantidas.loc[~mantidas["classe_candidata"].isin(mapa)].copy()
    selecionadas["id_origem_classe"] = selecionadas["classe_candidata"]
    selecionadas["indice_modelo"] = selecionadas["id_origem_classe"].map(
        lambda chave: mapa[chave][0]
    )
    selecionadas["nome_classe_modelo"] = selecionadas["id_origem_classe"].map(
        lambda chave: mapa[chave][1]
    )
    # A rotina de separação equilibra pela classe final, inclusive as duas Spodoptera.
    selecionadas["classe_candidata"] = selecionadas["indice_modelo"].map(
        lambda indice: f"MODELO-{indice:02d}"
    )

    vinculos = raiz / "assets/data/vinculos_mesma_planta.csv"
    agrupadas, grupos = construir_grupos(selecionadas, pares_visuais, vinculos)
    manifesto, resumo, auditoria = separar_grupos(agrupadas, semente=42)
    assert len(manifesto) + len(excluidas) == len(mantidas)
    assert manifesto["indice_modelo"].nunique() == len(classes)
    assert not auditoria["classes_candidatas_sem_cobertura"]
    assert not auditoria["pendencias_da_ancoragem"]
    assert auditoria["classes_exploratorias"] == 0
    manifesto["status_classe"] = "avaliavel"
    resumo["status_classe"] = "avaliavel"

    resumo["indice_modelo"] = resumo["classe_candidata"].str[-2:].astype(int)
    resumo["nome_classe_modelo"] = resumo["indice_modelo"].map(
        dict(zip(classes["indice_modelo"].astype(int), classes["classe"]))
    )
    resumo = resumo.drop(columns=["classe_candidata", "ocorrencia"]).sort_values("indice_modelo")
    cols = ["indice_modelo", "nome_classe_modelo"] + [
        coluna for coluna in resumo if coluna not in ("indice_modelo", "nome_classe_modelo")
    ]
    resumo = resumo[cols]

    pasta = pasta_saida or raiz / "assets/data/particionamento_T4_2"
    pasta.mkdir(parents=True, exist_ok=True)
    colunas = [
        "image_id", "caminho_relativo", "indice_modelo", "nome_classe_modelo",
        "id_origem_classe", "cultura", "classe", "ocorrencia", "fonte",
        "grupo_origem", "grupo_duplicata_exata", "grupo_duplicata_visual",
        "grupo_particao", "particao", "status_classe", "decisao_final", "sha256", "revisor",
    ]
    manifesto[colunas].sort_values("image_id").to_csv(
        pasta / "manifesto_modelo.csv", index=False, encoding="utf-8-sig"
    )
    resumo.to_csv(pasta / "resumo_modelo.csv", index=False, encoding="utf-8-sig")
    fora = excluidas.groupby("classe_candidata").size().rename("imagens_mantidas_fora_modelo").reset_index()
    fora["motivo"] = fora["classe_candidata"].map(
        lambda chave: "agente indeterminado no acervo" if chave in ACERVO_SEM_IDENTIFICACAO_CONFIRMADA
        else "classe fora do escopo T3.5"
    )
    fora.to_csv(pasta / "fora_modelo.csv", index=False, encoding="utf-8-sig")

    contagens_csv = classes["imagens_aproveitaveis"].astype(int)
    contagens_manifesto = resumo.set_index("indice_modelo")["imagens"]
    diferencas = {
        str(int(linha.indice_modelo)): {
            "csv_t3_5": int(linha.imagens_aproveitaveis),
            "manifesto_t3_3": int(contagens_manifesto[int(linha.indice_modelo)]),
            "diferenca": int(linha.imagens_aproveitaveis) - int(contagens_manifesto[int(linha.indice_modelo)]),
        }
        for linha in classes.itertuples(index=False)
    }
    proveniencia.pop("classes_candidatas")
    auditoria_modelo = {
        **proveniencia, **grupos, **auditoria,
        "classes_modelo_sha256": hash_texto_versionado(caminho_classes),
        "status_revisao": "aprovado_por_glauco_no_pr_21",
        "rotulos_finais_aprovados": False,
        "criterio_rotulos": "lista T3.5 aplicada como escopo interno; AGRO-003 retido até identificação da espécie",
        "classes_modelo": len(classes),
        "imagens_no_modelo": len(manifesto),
        "imagens_mantidas_fora_modelo": len(excluidas),
        "imagens_agro_003_retidas": int((excluidas["classe_candidata"] == "AGRO-003").sum()),
        "contagens_t3_5_versus_manifesto": diferencas,
        "diferenca_total_t3_5": int(contagens_csv.sum()) - len(manifesto),
    }
    (pasta / "auditoria_modelo.json").write_text(
        json.dumps(auditoria_modelo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return pasta


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[1]
    pasta = gerar(raiz)
    print(f"Manifesto do modelo: {pasta / 'manifesto_modelo.csv'}")
