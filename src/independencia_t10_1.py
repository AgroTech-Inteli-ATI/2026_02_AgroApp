"""Revisa a separação histórica sem modificar índices, modelos ou métricas."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
import platform

import numpy as np
from PIL import Image, ImageOps, __version__ as pillow_version
import scipy
from scipy.fft import dctn

from src.particionamento_t4_2 import Uniao

RAIZ = Path(__file__).resolve().parents[1]
INDICE = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
PACOTE = RAIZ / "assets/modelos/candidato_T5_6_20261026"
DESTINO = RAIZ / "assets/data/independencia_T10_1"
RESULTADOS_REVISAO = {"duplicata_confirmada", "relacao_suspeita", "sem_vinculo_confirmado"}


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def hash_arquivo(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def gravar_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def assinatura(caminho: Path) -> dict:
    with Image.open(caminho) as original:
        imagem = ImageOps.exif_transpose(original).convert("RGB")
        pixels = sha256(str(imagem.size).encode() + imagem.tobytes()).hexdigest()
        reduzida = imagem.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        frequencias = dctn(np.asarray(reduzida, dtype=float), type=2)[:8, :8]
        bits = (frequencias > np.median(frequencias)).ravel()
        perceptual = sum(int(bit) << i for i, bit in enumerate(bits))
    return {"sha256_pixels_rgb_exif": pixels, "phash64": f"{perceptual:016x}"}


def candidatos_cruzados(linhas: list[dict], limite: int = 6) -> list[dict]:
    hashes = np.array([int(linha["phash64"], 16) for linha in linhas], dtype=np.uint64)
    pares = []
    for i, primeira in enumerate(linhas):
        distancias = np.bitwise_count(hashes[i + 1:] ^ hashes[i])
        for deslocamento in np.flatnonzero(distancias <= limite):
            segunda = linhas[i + 1 + int(deslocamento)]
            if primeira["particao"] != segunda["particao"]:
                pares.append({"image_id_1": primeira["image_id"],
                              "image_id_2": segunda["image_id"],
                              "distancia_phash": int(distancias[deslocamento])})
    return sorted(pares, key=lambda par: (par["distancia_phash"], par["image_id_1"], par["image_id_2"]))


def juntar_revisao(pares: list[dict], revisoes: list[dict]) -> list[dict]:
    chave = lambda linha: tuple(sorted((linha["image_id_1"], linha["image_id_2"])))
    por_par = {chave(linha): linha for linha in revisoes}
    if len(por_par) != len(revisoes) or set(por_par) != {chave(par) for par in pares}:
        raise ValueError("Revisão deve cobrir exatamente os pares candidatos, sem repetições.")
    resultado = []
    for par in pares:
        revisao = por_par[chave(par)]
        if revisao["resultado"] not in RESULTADOS_REVISAO or not revisao["justificativa"].strip():
            raise ValueError("Par sem resultado ou justificativa reconhecidos.")
        resultado.append({**par, "resultado": revisao["resultado"],
                          "justificativa": revisao["justificativa"]})
    return resultado


def sobreposicoes(linhas: list[dict], coluna: str) -> list[dict]:
    grupos = defaultdict(list)
    for linha in linhas:
        if linha[coluna]:
            grupos[linha[coluna]].append(linha)
    return [{"campo": coluna, "valor": valor,
             "ids": "|".join(sorted(linha["image_id"] for linha in membros)),
             "particoes": "|".join(sorted({linha["particao"] for linha in membros}))}
            for valor, membros in sorted(grupos.items())
            if len({linha["particao"] for linha in membros}) > 1]


def grupos_relacionados(linhas: list[dict], pares: list[dict]) -> list[dict]:
    uniao = Uniao([linha["image_id"] for linha in linhas])
    for coluna in ("grupo_particao", "inat_obs_id"):
        grupos = defaultdict(list)
        for linha in linhas:
            if linha[coluna]:
                grupos[linha[coluna]].append(linha["image_id"])
        for membros in grupos.values():
            for membro in membros[1:]:
                uniao.unir(membros[0], membro)
    relacionados = [par for par in pares if par["resultado"] != "sem_vinculo_confirmado"]
    for par in relacionados:
        uniao.unir(par["image_id_1"], par["image_id_2"])
    tipos = defaultdict(set)
    for par in relacionados:
        tipos[uniao.achar(par["image_id_1"])].add(par["resultado"])
    return [{"grupo_revisao": f"REV-{uniao.achar(linha['image_id'])}",
             "natureza": "|".join(sorted(tipos[uniao.achar(linha["image_id"])])),
             **{chave: linha[chave] for chave in (
                 "image_id", "particao", "grupo_particao", "inat_obs_id",
                 "caminho_relativo", "sha256_original", "indice_modelo")}}
            for linha in linhas if uniao.achar(linha["image_id"]) in tipos]


def executar(acervo: Path, saida: Path, revisao: Path) -> dict:
    manifesto = json.loads((PACOTE / "manifesto.json").read_text(encoding="utf-8"))
    indice_hash = hash_arquivo(INDICE)
    if indice_hash != manifesto["indice_sha256"]:
        raise ValueError("Índice divergente do candidato selecionado.")
    linhas = ler_csv(INDICE)
    if len({linha["image_id"] for linha in linhas}) != len(linhas):
        raise ValueError("IDs repetidos no índice.")
    metadados = acervo / "dataset/field/field_labels.csv"
    observacoes = {f"dataset/field/{linha['filename']}": linha["inat_obs_id"]
                   for linha in ler_csv(metadados)}
    registros = []
    for numero, linha in enumerate(linhas, 1):
        relativo = Path(linha["caminho_relativo"])
        caminho = (acervo / relativo).resolve()
        if relativo.is_absolute() or not caminho.is_relative_to(acervo.resolve()):
            raise ValueError("Caminho fora do acervo.")
        if hash_arquivo(caminho) != linha["sha256_original"]:
            raise ValueError(f"Original divergente do índice: {linha['image_id']}")
        registros.append({**linha, **assinatura(caminho),
                          "inat_obs_id": observacoes.get(linha["caminho_relativo"], "")})
        if numero % 500 == 0:
            print(f"Imagens verificadas: {numero}/{len(linhas)}", flush=True)
    pares = juntar_revisao(candidatos_cruzados(registros), ler_csv(revisao))
    grupos = grupos_relacionados(registros, pares)
    campos = ("grupo_particao", "sha256_original", "sha256_pixels_rgb_exif", "inat_obs_id")
    overlaps = [item for campo in campos for item in sobreposicoes(registros, campo)]
    resumo = {
        "esquema": "revisao_independencia_T10_1_v1",
        "indice": str(INDICE.relative_to(RAIZ)), "indice_sha256": indice_hash,
        "metadados_sha256": hash_arquivo(metadados),
        "manifesto_candidato_sha256": hash_arquivo(PACOTE / "manifesto.json"),
        "codigo_sha256": hash_arquivo(Path(__file__)), "revisao_pares_sha256": hash_arquivo(revisao),
        "agrupamento_codigo_sha256": hash_arquivo(RAIZ / "src/particionamento_t4_2.py"),
        "ambiente": {"python": platform.python_version(), "numpy": np.__version__,
                     "pillow": pillow_version, "scipy": scipy.__version__},
        "imagens_verificadas": len(registros),
        "particoes": dict(sorted(Counter(linha["particao"] for linha in registros).items())),
        "sobreposicoes": {campo: sum(item["campo"] == campo for item in overlaps) for campo in campos},
        "busca_perceptual": {"algoritmo": "L EXIF, Lanczos 32x32, DCT-II 8x8, mediana incluindo DC",
                             "bits": 64, "distancia_maxima": 6, "pares": len(pares)},
        "revisao_visual": dict(sorted(Counter(par["resultado"] for par in pares).items())),
        "grupos_relacionados": len({linha["grupo_revisao"] for linha in grupos}),
        "imagens_em_grupos_relacionados": len(grupos),
        "classificacao_avaliacao_historica": "exploratoria",
        "independencia_comprovada": False,
        "novo_teste_independente": "nenhum_conjunto_reservado_identificado_nesta_revisao",
    }
    saida_resolvida = saida.resolve()
    protegidos = [INDICE.parent, PACOTE, acervo]
    if any(saida_resolvida == p.resolve() or saida_resolvida.is_relative_to(p.resolve()) for p in protegidos):
        raise ValueError("A saída deve ficar fora do acervo, do índice e do pacote do modelo.")
    saida.mkdir(parents=True, exist_ok=True)
    colunas = ["image_id", "caminho_relativo", "particao", "indice_modelo", "grupo_particao",
               "inat_obs_id", "sha256_original", "sha256_pixels_rgb_exif", "phash64"]
    gravar_csv(saida / "assinaturas_imagens.csv", registros_filtrados(registros, colunas), colunas)
    gravar_csv(saida / "pares_revisados.csv", pares,
               ["image_id_1", "image_id_2", "distancia_phash", "resultado", "justificativa"])
    gravar_csv(saida / "grupos_relacionados.csv", grupos,
               ["grupo_revisao", "natureza", "image_id", "particao", "grupo_particao", "inat_obs_id",
                "caminho_relativo", "sha256_original", "indice_modelo"])
    gravar_csv(saida / "sobreposicoes_exatas.csv", overlaps, ["campo", "valor", "ids", "particoes"])
    resumo["artefatos_sha256"] = {nome: hash_arquivo(saida / nome) for nome in (
        "assinaturas_imagens.csv", "pares_revisados.csv", "grupos_relacionados.csv", "sobreposicoes_exatas.csv")}
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resumo


def registros_filtrados(linhas: list[dict], colunas: list[str]) -> list[dict]:
    return [{coluna: linha[coluna] for coluna in colunas} for linha in linhas]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acervo", type=Path, required=True, help="Pasta que contém dataset/.")
    parser.add_argument("--saida", type=Path, default=DESTINO)
    parser.add_argument("--revisao", type=Path, default=DESTINO / "revisao_visual.csv")
    argumentos = parser.parse_args()
    print(json.dumps(executar(argumentos.acervo, argumentos.saida, argumentos.revisao),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
