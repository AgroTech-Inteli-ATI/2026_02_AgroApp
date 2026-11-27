"""Vincula as previsões Keras por foto das três MobileNets ao manifesto T4.2.

Uso: python -m src.consolidar_predicoes_t6_2 [--verificar]
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

from .analise_confusao_t6_2 import PASTA, ler_classes
from .revisar_erros_t6_2 import (
    COLUNAS, RODADAS, carregar_teste, conferir_matriz_modelo,
)


FONTES = {
    "small_100": "mobilenetv3_small_100_keras_origem.csv",
    "large_075": "mobilenetv3_large_075_keras_origem.csv",
    "large_100": "mobilenetv3_large_100_keras_origem.csv",
}
SAIDA = PASTA / "predicoes_por_imagem_keras_3_modelos.csv"
SAIDA_ERROS = PASTA / "erros_por_imagem_keras_3_modelos.csv"
COLUNAS_ERROS = [
    "image_id", "caminho_relativo", "indice_real", "classe_real",
    "modelos_com_erro", "quantidade_modelos_com_erro", "previsoes_erradas",
    "maior_confianca_erro", "revisao_visual", "observacao_revisao",
]


def gerar_conteudo() -> tuple[str, list[dict[str, str]]]:
    classes = ler_classes()
    manifesto = carregar_teste(classes)
    por_caminho = {linha["caminho_relativo"]: linha for linha in manifesto}
    if len(por_caminho) != len(manifesto):
        raise ValueError("caminhos duplicados na partição de teste")
    registros = []
    for modelo, arquivo in FONTES.items():
        with (PASTA / arquivo).open(encoding="utf-8-sig", newline="") as origem:
            linhas = list(csv.DictReader(origem))
        if len(linhas) != len(manifesto):
            raise ValueError(f"{modelo}: esperadas 474 previsões")
        vistos = set()
        for linha in linhas:
            caminho = linha["caminho_relativo"]
            if caminho not in por_caminho or caminho in vistos:
                raise ValueError(f"{modelo}: caminho ausente ou duplicado: {caminho}")
            vistos.add(caminho)
            referencia = por_caminho[caminho]
            real = int(referencia["indice_modelo"])
            previsto = int(linha["indice_previsto"])
            confianca = float(linha["confianca"])
            if (
                int(linha["indice_gabarito"]) != real
                or linha["gabarito"] != classes[real]
                or not 0 <= previsto < len(classes)
                or linha["previsao"] != classes[previsto]
                or not 0 <= confianca <= 1
                or linha["acertou"] != str(real == previsto)
            ):
                raise ValueError(f"{modelo}: previsão inválida em {caminho}")
            registros.append({
                "image_id": referencia["image_id"],
                "caminho_relativo": caminho,
                "sha256_original": referencia["sha256"],
                "modelo": modelo,
                "rodada": RODADAS[modelo][0],
                "origem_inferencia": "Keras FP32",
                "indice_real": real,
                "classe_real": classes[real],
                "indice_previsto": previsto,
                "classe_prevista": classes[previsto],
                "confianca_top1": linha["confianca"],
                "acerto": "sim" if real == previsto else "nao",
                "revisao_visual": "",
                "observacao_revisao": "",
            })
        conferir_matriz_modelo(registros, classes, modelo)
    saida = io.StringIO(newline="")
    escritor = csv.DictWriter(saida, fieldnames=COLUNAS, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(registros)
    return saida.getvalue(), registros


def gerar_erros(registros: list[dict[str, str]]) -> tuple[str, int]:
    por_imagem: dict[str, list[dict[str, str]]] = {}
    for linha in registros:
        if linha["acerto"] == "nao":
            por_imagem.setdefault(linha["image_id"], []).append(linha)
    linhas = []
    for image_id, erros in por_imagem.items():
        primeiro = erros[0]
        linhas.append({
            "image_id": image_id,
            "caminho_relativo": primeiro["caminho_relativo"],
            "indice_real": primeiro["indice_real"],
            "classe_real": primeiro["classe_real"],
            "modelos_com_erro": "; ".join(linha["modelo"] for linha in erros),
            "quantidade_modelos_com_erro": len(erros),
            "previsoes_erradas": "; ".join(
                f"{linha['modelo']}: {linha['classe_prevista']} ({float(linha['confianca_top1']):.1%})"
                for linha in erros
            ),
            "maior_confianca_erro": f"{max(float(linha['confianca_top1']) for linha in erros):.8f}",
            "revisao_visual": "",
            "observacao_revisao": "",
        })
    linhas.sort(key=lambda linha: (
        -int(linha["quantidade_modelos_com_erro"]),
        -float(linha["maior_confianca_erro"]),
        linha["image_id"],
    ))
    saida = io.StringIO(newline="")
    escritor = csv.DictWriter(saida, fieldnames=COLUNAS_ERROS, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(linhas)
    return saida.getvalue(), len(linhas)


def main(verificar: bool) -> None:
    conteudo, registros = gerar_conteudo()
    conteudo_erros, quantidade_imagens_com_erro = gerar_erros(registros)
    if verificar:
        if SAIDA.read_text(encoding="utf-8") != conteudo:
            raise ValueError(f"CSV derivado divergente: {SAIDA}")
        if SAIDA_ERROS.read_text(encoding="utf-8") != conteudo_erros:
            raise ValueError(f"CSV derivado divergente: {SAIDA_ERROS}")
    else:
        SAIDA.write_text(conteudo, encoding="utf-8", newline="\n")
        SAIDA_ERROS.write_text(conteudo_erros, encoding="utf-8", newline="\n")
    erros = {modelo: sum(
        linha["modelo"] == modelo and linha["acerto"] == "nao" for linha in registros
    ) for modelo in FONTES}
    print(
        f"{len(registros)} previsões / 474 fotos / 3 modelos; "
        f"{quantidade_imagens_com_erro} fotos com erro; erros: {erros}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true")
    main(parser.parse_args().verificar)
