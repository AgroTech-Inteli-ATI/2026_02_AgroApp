"""Gera a figura da matriz Lite0 FP32 a partir dos CSVs publicados.

Uso: python -m src.plotar_matriz_confusao_t6_2
"""

from __future__ import annotations

import csv
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Patch, Rectangle
import numpy as np

from .analise_confusao_t6_2 import (
    MATRIZES,
    PASTA,
    RAIZ,
    ler_classes,
    ler_matriz,
    ler_suportes,
    pares_recorrentes,
)


def main() -> None:
    classes = ler_classes()
    suportes = ler_suportes()
    matrizes = {
        nome: ler_matriz(PASTA / arquivo, classes, suportes)
        for nome, arquivo in MATRIZES.items()
    }
    matriz = np.asarray(matrizes["lite0"], dtype=int)
    proporcoes = matriz / np.asarray(suportes)[:, None]
    pares = {
        (int(linha["indice_real"]), int(linha["indice_previsto"]))
        for linha in csv.DictReader(
            io.StringIO(pares_recorrentes(matrizes, classes, suportes)),
            delimiter=";",
        )
    }
    nomes = [classe.split(" (")[0] for classe in classes]

    fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
    fig.patch.set_facecolor("white")
    cmap = plt.get_cmap("Blues").copy()
    mapa = ax.imshow(proporcoes, cmap=cmap, norm=Normalize(0, 1), aspect="equal")

    for real in range(len(classes)):
        for previsto in range(len(classes)):
            quantidade = matriz[real, previsto]
            if not quantidade:
                continue
            destaque = (real, previsto) in pares
            rotulo = str(quantidade)
            if destaque:
                rotulo += f"\n({100 * quantidade / suportes[real]:.1f}%)".replace(".", ",")
                ax.add_patch(
                    Rectangle(
                        (previsto - 0.48, real - 0.48),
                        0.96,
                        0.96,
                        fill=False,
                        edgecolor="#b45309",
                        linewidth=2.3,
                    )
                )
            ax.text(
                previsto,
                real,
                rotulo,
                ha="center",
                va="center",
                color="white" if proporcoes[real, previsto] >= 0.48 else "#102342",
                fontsize=7.8 if destaque else 9,
                fontweight="bold" if destaque else "normal",
                linespacing=1.15,
            )

    ax.set_xticks(range(len(classes)), nomes, rotation=52, ha="right", fontsize=9)
    ax.set_yticks(
        range(len(classes)),
        [f"{nome} (n={suporte})" for nome, suporte in zip(nomes, suportes)],
        fontsize=9,
    )
    ax.set_xticks(np.arange(-0.5, len(classes), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(classes), 1), minor=True)
    ax.grid(which="minor", color="#d9e0e7", linewidth=0.6)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_xlabel("Classe prevista", fontsize=11, labelpad=10)
    ax.set_ylabel("Classe real", fontsize=11, labelpad=15)
    ax.set_title(
        "T6.2 — Matriz de confusão | EfficientNet-Lite0 FP32 | 474 imagens de teste exploratório",
        fontsize=15,
        pad=19,
    )
    barra = fig.colorbar(mapa, ax=ax, fraction=0.036, pad=0.025)
    barra.set_label("Parcela da classe real", fontsize=10)
    barra.ax.tick_params(labelsize=9)
    ax.legend(
        handles=[
            Patch(
                facecolor="none",
                edgecolor="#b45309",
                linewidth=2.3,
                label="Par recorrente nos 4 modelos FP32: contagem e % da classe real",
            )
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.30),
        frameon=False,
        fontsize=9,
    )
    fig.subplots_adjust(left=0.28, right=0.92, top=0.90, bottom=0.32)
    destino = RAIZ / "assets/matriz_confusao_T6_2_lite0_fp32.png"
    fig.savefig(destino, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(f"Figura gerada: {destino} ({len(pares)} pares destacados)")


if __name__ == "__main__":
    main()
