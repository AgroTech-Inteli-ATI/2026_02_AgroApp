"""Registra as previsões FP32 por foto e confere as matrizes da T6.2.

Uso:
    python -m src.revisar_erros_t6_2 --raiz-imagens PASTA_AGRO_APP \
        --outputs PASTA_AGRO_APP/outputs

Requer as imagens originais e os quatro modelos TFLite das rodadas da T5.3.
Não publica linhas parciais ou inferidas a partir de contagens agregadas.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import numpy as np

from .analise_confusao_t6_2 import MATRIZES, PASTA, RAIZ, ler_classes, ler_matriz, ler_suportes
from .preprocessamento import preparar_imagem


RODADAS = {
    "lite0": ("lite0_20261019_130322", "efficientnet_lite0_fp32.tflite"),
    "small_100": ("mobilenetv3_small_100_20261019_143421", "mobilenetv3_small_100_fp32.tflite"),
    "large_075": ("mobilenetv3_large_075_20261020_113954", "mobilenetv3_large_075_fp32.tflite"),
    "large_100": ("mobilenetv3_large_100_20261019_215020", "mobilenetv3_large_100_fp32.tflite"),
}
COLUNAS = [
    "image_id", "caminho_relativo", "sha256_original", "modelo", "rodada", "origem_inferencia",
    "indice_real", "classe_real", "indice_previsto", "classe_prevista",
    "confianca_top1", "acerto", "revisao_visual", "observacao_revisao",
]


def carregar_teste(classes: list[str]) -> list[dict[str, str]]:
    caminho = RAIZ / "assets/data/particionamento_T4_2/manifesto_modelo.csv"
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = [linha for linha in csv.DictReader(arquivo) if linha["particao"] == "teste"]
    if len(linhas) != 474 or len({linha["image_id"] for linha in linhas}) != 474:
        raise ValueError("o manifesto deve ter 474 IDs únicos na partição de teste")
    for linha in linhas:
        indice = int(linha["indice_modelo"])
        if not 0 <= indice < len(classes) or linha["nome_classe_modelo"] != classes[indice]:
            raise ValueError(f"rótulo ou ordem de classe divergente: {linha['image_id']}")
    return linhas


def conferir_entradas(
    linhas: list[dict[str, str]], raiz_imagens: Path, outputs: Path
) -> tuple[list[Path], dict[str, Path]]:
    imagens = [resolver_imagem(raiz_imagens, linha["caminho_relativo"]) for linha in linhas]
    ausentes = [str(caminho) for caminho in imagens if not caminho.is_file()]
    modelos = {
        nome: outputs / pasta / arquivo
        for nome, (pasta, arquivo) in RODADAS.items()
    }
    ausentes += [str(caminho) for caminho in modelos.values() if not caminho.is_file()]
    if ausentes:
        raise FileNotFoundError(
            f"faltam {len(ausentes)} arquivos necessários; exemplos: " + "; ".join(ausentes[:5])
        )
    return imagens, modelos


def resolver_imagem(raiz: Path, relativo: str) -> Path:
    """Aceita a estrutura local e o nível extra dataset/ usado no Drive."""
    partes = Path(relativo).parts
    candidatos = [raiz.joinpath(*partes)]
    if partes and partes[0] == "dataset":
        candidatos.append(raiz / "dataset" / Path(*partes))
    if partes and partes[0] == raiz.name:
        candidatos.append(raiz.joinpath(*partes[1:]))
    return next((caminho for caminho in candidatos if caminho.is_file()), candidatos[0])


def abrir_interpretadores(modelos: dict[str, Path]) -> dict[str, tuple[object, dict, dict]]:
    try:
        import tensorflow as tf
    except ImportError as erro:
        raise RuntimeError("Instale requirements-treino.txt para executar o TFLite") from erro
    interpretadores = {}
    for nome, caminho in modelos.items():
        interpretador = tf.lite.Interpreter(model_path=str(caminho), num_threads=4)
        interpretador.allocate_tensors()
        entrada = interpretador.get_input_details()[0]
        saida = interpretador.get_output_details()[0]
        if (
            entrada["dtype"] != np.float32
            or saida["dtype"] != np.float32
            or list(entrada["shape"]) != [1, 224, 224, 3]
            or list(saida["shape"]) != [1, 13]
        ):
            raise ValueError(f"contrato FP32 inesperado no modelo {nome}")
        interpretadores[nome] = (interpretador, entrada, saida)
    return interpretadores


def conferir_matrizes(registros: list[dict[str, str]], classes: list[str]) -> None:
    for modelo in MATRIZES:
        conferir_matriz_modelo(registros, classes, modelo)


def conferir_matriz_modelo(
    registros: list[dict[str, str]], classes: list[str], modelo: str
) -> None:
    esperada = ler_matriz(PASTA / MATRIZES[modelo], classes, ler_suportes())
    obtida = [[0] * len(classes) for _ in classes]
    linhas = [linha for linha in registros if linha["modelo"] == modelo]
    if len(linhas) != 474 or len({linha["image_id"] for linha in linhas}) != 474:
        raise ValueError(f"{modelo}: esperadas 474 previsões para IDs únicos")
    for linha in linhas:
        obtida[int(linha["indice_real"])][int(linha["indice_previsto"])] += 1
    if obtida != esperada:
        divergencias = [
            (classes[i], classes[j], obtida[i][j], esperada[i][j])
            for i in range(len(classes)) for j in range(len(classes))
            if obtida[i][j] != esperada[i][j]
        ]
        raise ValueError(
            f"{modelo}: previsões não reproduzem a matriz publicada; "
            f"primeiras divergências (real, prevista, obtido, esperado): {divergencias[:5]}"
        )


def gerar(raiz_imagens: Path, outputs: Path, saida: Path) -> None:
    classes = ler_classes()
    linhas = carregar_teste(classes)
    imagens, modelos = conferir_entradas(linhas, raiz_imagens, outputs)
    interpretadores = abrir_interpretadores(modelos)
    registros = []
    for numero, (linha, caminho) in enumerate(zip(linhas, imagens), 1):
        dados = caminho.read_bytes()
        if sha256(dados).hexdigest() != linha["sha256"]:
            raise ValueError(f"hash da imagem diverge do manifesto: {linha['image_id']}")
        # Reproduz o arredondamento uint8 usado pelos notebooks da T5.3.
        imagem = np.round(preparar_imagem(caminho) * 255).astype(np.uint8)
        entrada_imagem = imagem.astype(np.float32)[None, ...] / 255.0
        real = int(linha["indice_modelo"])
        for modelo, (interpretador, entrada, saida_modelo) in interpretadores.items():
            interpretador.set_tensor(entrada["index"], entrada_imagem)
            interpretador.invoke()
            probabilidades = interpretador.get_tensor(saida_modelo["index"])[0]
            if not np.all(np.isfinite(probabilidades)) or not np.isclose(
                probabilidades.sum(), 1.0, atol=1e-3
            ):
                raise ValueError(f"saída não probabilística em {modelo}, {linha['image_id']}")
            previsto = int(np.argmax(probabilidades))
            registros.append({
                "image_id": linha["image_id"],
                "caminho_relativo": linha["caminho_relativo"],
                "sha256_original": linha["sha256"],
                "modelo": modelo,
                "rodada": RODADAS[modelo][0],
                "origem_inferencia": "TFLite FP32",
                "indice_real": real,
                "classe_real": classes[real],
                "indice_previsto": previsto,
                "classe_prevista": classes[previsto],
                "confianca_top1": f"{float(probabilidades[previsto]):.8f}",
                "acerto": "sim" if previsto == real else "nao",
                "revisao_visual": "",  # preencher após abrir a foto
                "observacao_revisao": "",
            })
        if numero % 50 == 0 or numero == len(linhas):
            print(f"{numero}/{len(linhas)} imagens inferidas")

    conferir_matrizes(registros, classes)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8-sig", newline="", suffix=".csv",
        dir=saida.parent, delete=False,
    ) as arquivo:
        temporario = Path(arquivo.name)
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(registros)
    temporario.replace(saida)
    resumo = {
        "imagens": len(linhas),
        "modelos": list(RODADAS),
        "previsoes": len(registros),
        "erros_por_modelo": {
            modelo: sum(linha["modelo"] == modelo and linha["acerto"] == "nao" for linha in registros)
            for modelo in RODADAS
        },
        "saida": str(saida),
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-imagens", type=Path, required=True)
    parser.add_argument("--outputs", type=Path, required=True, help="pasta outputs que contém as quatro rodadas T5.3")
    parser.add_argument(
        "--saida", type=Path,
        default=PASTA / "predicoes_por_imagem_fp32.csv",
    )
    args = parser.parse_args()
    gerar(args.raiz_imagens, args.outputs, args.saida)
