r"""Gera as probabilidades por classe da partição de VALIDAÇÃO (insumo da T6.5).

Uso (requer TensorFlow/Keras: Colab ou .venv-treino):
    python -m src.probabilidades_validacao_t6_5 --modelo runs/<rodada>/melhor_modelo.keras \
        --indice assets/data/pipeline_T4_5/indice_pipeline.csv \
        --raiz-imagens /caminho/para/as/fontes \
        --saida assets/data/politica_T6_5/probabilidades_validacao.csv

Não treina e não abre o teste: preparar_particao recusa qualquer partição que não seja
treino ou validação. A saída tem image_id, indice_real e p_0..p_N, na ordem do índice.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from pathlib import Path

import numpy as np

from src.avaliacao_t6_1 import _carregar_modelo
from src.dados_treino import INDICE_PADRAO, carregar_indice, nomes_classes, preparar_particao
from src.politica_confianca_t6_5 import (
    CLASSES_PADRAO, PARTICAO, PASTA, ler_nomes_classes, validar_matriz,
)

def _hash(caminho: Path) -> str:
    return sha256(Path(caminho).read_bytes()).hexdigest()


def gerar(
    modelo: Path, indice: Path, raiz_imagens: Path, saida: Path,
    batch: int = 32, classes: Path = CLASSES_PADRAO, carregador=None,
) -> dict:
    if isinstance(batch, bool) or not isinstance(batch, int) or batch < 1:
        raise ValueError("batch deve ser inteiro positivo")
    saida = Path(saida)
    if saida.exists():
        raise ValueError(f"{saida} já existe; remova ou escolha outro caminho para preservar o resultado")

    linhas_indice = carregar_indice(indice)
    nomes = nomes_classes(linhas_indice)
    if nomes != ler_nomes_classes(classes):
        raise ValueError("classes do índice divergem da ordem de assets/data/classes-modelo.csv")
    linhas = [linha for linha in linhas_indice if linha["particao"] == PARTICAO]
    if not linhas:
        raise ValueError("o índice informado não tem imagens de validação")

    hash_modelo, hash_indice = _hash(modelo), _hash(indice)
    rede = (carregador or _carregar_modelo)(Path(modelo))
    forma = tuple(rede.input_shape[1:])
    if len(forma) != 3 or forma[0] != forma[1] or forma[2] != 3:
        raise ValueError(f"entrada do modelo deve ser quadrada com 3 canais; recebido {forma}")
    if tuple(rede.output_shape[1:]) != (len(nomes),):
        raise ValueError("saída do modelo incompatível com o número de classes do índice")
    tamanho = int(forma[0])

    imagens, rotulos, _ = preparar_particao(linhas_indice, PARTICAO, Path(raiz_imagens), tamanho)
    if [int(linha["indice_modelo"]) for linha in linhas] != rotulos.tolist():
        raise ValueError("rótulos carregados divergem do índice")

    blocos = []
    for inicio in range(0, len(imagens), batch):
        lote = imagens[inicio:inicio + batch].astype(np.float32) / 255.0
        blocos.append(np.asarray(rede.predict_on_batch(lote), dtype=np.float64))
    probabilidades = np.concatenate(blocos)
    validar_matriz(probabilidades, len(nomes))
    probabilidades = np.round(probabilidades, 6)
    validar_matriz(probabilidades, len(nomes))  # a soma continua válida após o arredondamento
    if len(probabilidades) != len(linhas):
        raise ValueError("quantidade de previsões diverge da validação")

    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(["image_id", "indice_real"] + [f"p_{i}" for i in range(len(nomes))])
        for linha, rotulo, valores in zip(linhas, rotulos, probabilidades):
            escritor.writerow([linha["image_id"], int(rotulo)] + [f"{v:.6f}" for v in valores])
    return {
        "linhas": len(linhas), "classes": len(nomes), "tamanho_entrada": tamanho,
        "modelo_sha256": hash_modelo, "indice_sha256": hash_indice, "saida": str(saida),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", type=Path, required=True, help="melhor_modelo.keras da rodada")
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO)
    parser.add_argument("--raiz-imagens", type=Path, required=True)
    parser.add_argument("--saida", type=Path, default=PASTA / "probabilidades_validacao.csv")
    parser.add_argument("--batch", type=int, default=32, help="só o tamanho do lote de inferência")
    args = parser.parse_args()
    resumo = gerar(args.modelo, args.indice, args.raiz_imagens, args.saida, args.batch)
    print(f"{resumo['linhas']} linhas, {resumo['classes']} classes, entrada {resumo['tamanho_entrada']}px")
    print(f"sha256 do modelo: {resumo['modelo_sha256']}")
    print(f"sha256 do índice: {resumo['indice_sha256']}")
    print(f"Gravado: {resumo['saida']}")


if __name__ == "__main__":
    main()
