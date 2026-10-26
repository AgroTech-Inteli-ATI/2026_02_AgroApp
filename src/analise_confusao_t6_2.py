"""Reproduz os quatro campos e os pares recorrentes das matrizes T5.3 FP32.

Uso: python -m src.analise_confusao_t6_2 [--verificar]
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "assets/data/avaliacao_T6_2"
MATRIZES = {
    "lite0": "efficientnet_lite0_fp32.csv",
    "small_100": "mobilenetv3_small_100_fp32.csv",
    "large_075": "mobilenetv3_large_075_fp32.csv",
    "large_100": "mobilenetv3_large_100_fp32.csv",
}
MATRIZES_INT8 = {
    nome: arquivo.replace("_fp32.csv", "_int8.csv")
    for nome, arquivo in MATRIZES.items()
}
TOTAL_TESTE = 474


def ler_classes() -> list[str]:
    with (RAIZ / "assets/data/classes-modelo.csv").open(
        encoding="utf-8-sig", newline=""
    ) as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))
    assert [int(linha["indice_modelo"]) for linha in linhas] == list(range(13))
    return [linha["classe"] for linha in linhas]


def ler_suportes() -> list[int]:
    with (RAIZ / "assets/data/particionamento_T4_2/resumo_modelo.csv").open(
        encoding="utf-8-sig", newline=""
    ) as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert [int(linha["indice_modelo"]) for linha in linhas] == list(range(13))
    return [int(linha["imagens_teste"]) for linha in linhas]


def ler_matriz(caminho: Path, classes: list[str], suportes: list[int]) -> list[list[int]]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.reader(arquivo, delimiter=";"))
    if linhas[0] != ["classe_real", *classes]:
        raise ValueError(f"Cabeçalho ou ordem de classes divergente: {caminho}")
    if [linha[0] for linha in linhas[1:]] != classes:
        raise ValueError(f"Classes reais divergentes: {caminho}")
    matriz = [[int(valor) for valor in linha[1:]] for linha in linhas[1:]]
    if len(matriz) != 13 or any(len(linha) != 13 for linha in matriz):
        raise ValueError(f"Matriz diferente de 13 × 13: {caminho}")
    if any(valor < 0 for linha in matriz for valor in linha):
        raise ValueError(f"Contagem negativa: {caminho}")
    if [sum(linha) for linha in matriz] != suportes:
        raise ValueError(f"Suportes divergentes do manifesto: {caminho}")
    if sum(map(sum, matriz)) != TOTAL_TESTE:
        raise ValueError(f"Total diferente de {TOTAL_TESTE}: {caminho}")
    return matriz


def gerar_csv(cabecalho: list[str], linhas: list[list[object]]) -> str:
    saida = io.StringIO(newline="")
    escritor = csv.writer(saida, delimiter=";", lineterminator="\n")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return saida.getvalue()


def quatro_campos(matriz: list[list[int]], classes: list[str]) -> str:
    linhas = []
    for indice, classe in enumerate(classes):
        vp = matriz[indice][indice]
        fn = sum(matriz[indice]) - vp
        fp = sum(linha[indice] for linha in matriz) - vp
        vn = TOTAL_TESTE - vp - fp - fn
        linhas.append([indice, classe, vp, fp, fn, vn, vp + fn])
    return gerar_csv(["indice_modelo", "classe", "VP", "FP", "FN", "VN", "suporte"], linhas)


def pares_recorrentes(
    matrizes: dict[str, list[list[int]]], classes: list[str], suportes: list[int]
) -> str:
    selecionados = []
    for real in range(len(classes)):
        for previsto in range(len(classes)):
            if real == previsto:
                continue
            contagens = [matrizes[modelo][real][previsto] for modelo in MATRIZES]
            if contagens[0] >= 3 and all(valor >= 2 for valor in contagens):
                selecionados.append((real, previsto, contagens))
    selecionados.sort(key=lambda item: (-sum(item[2]), item[0], item[1]))
    linhas = [
        [
            real,
            classes[real],
            previsto,
            classes[previsto],
            suportes[real],
            *contagens,
            f"{100 * contagens[0] / suportes[real]:.1f}",
        ]
        for real, previsto, contagens in selecionados
    ]
    return gerar_csv(
        [
            "indice_real", "classe_real", "indice_previsto", "classe_prevista",
            "suporte_real", "lite0_fp32", "small_100_fp32", "large_075_fp32",
            "large_100_fp32", "percentual_lite0",
        ],
        linhas,
    )


def executar(verificar: bool = False) -> None:
    classes = ler_classes()
    suportes = ler_suportes()
    matrizes = {
        nome: ler_matriz(PASTA / arquivo, classes, suportes)
        for nome, arquivo in MATRIZES.items()
    }
    for arquivo in MATRIZES_INT8.values():
        ler_matriz(PASTA / arquivo, classes, suportes)
    saidas = {
        "quatro_campos_lite0_fp32.csv": quatro_campos(matrizes["lite0"], classes),
        "pares_recorrentes_fp32.csv": pares_recorrentes(matrizes, classes, suportes),
    }
    for nome, conteudo in saidas.items():
        caminho = PASTA / nome
        if verificar:
            if caminho.read_text(encoding="utf-8") != conteudo:
                raise ValueError(f"Artefato divergente: {caminho}")
        else:
            caminho.write_text(conteudo, encoding="utf-8", newline="\n")
    modo = "verificados" if verificar else "gerados"
    print(f"T6.2: {len(matrizes) + len(MATRIZES_INT8)} matrizes, {len(classes)} classes; artefatos {modo}.")


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--verificar", action="store_true")
    executar(verificar=argumentos.parse_args().verificar)
