"""Pipeline reproduzível de preparação dos dados (T4.5).

O pipeline recompõe a partição T4.2 a partir das fontes versionadas, confere-a
contra o manifesto aprovado e produz o contrato consumido pelo treinamento:
índice das amostras, pesos calculados apenas no treino e parâmetros de T4.1-T4.4.

As imagens permanecem fora do repositório. Quando ``--raiz-imagens`` é
informado, todas as entradas são abertas e os hashes das saídas determinísticas
de preprocessamento e augmentation são incluídos no índice para auditoria.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import csv
import json
import platform
import tempfile

import numpy as np
import pandas as pd
import PIL

from src.aumento import PROBABILIDADE, aplicar_aumento
from src.gerar_manifesto_modelo_t4_2 import gerar
from src.preprocessamento import COR_PREENCHIMENTO, TAMANHO_ENTRADA, preparar_imagem


SEMENTE = 42
PARTICOES = ("treino", "validacao", "teste")
ARQUIVOS_PARTICAO = (
    "manifesto_modelo.csv",
    "resumo_modelo.csv",
    "fora_modelo.csv",
    "auditoria_modelo.json",
)


def _hash_arquivo(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def _hash_array(array: np.ndarray) -> str:
    dados = np.ascontiguousarray(array, dtype=np.float32)
    return sha256(dados.tobytes()).hexdigest()


def _semente_amostra(image_id: str, semente: int = SEMENTE) -> int:
    material = f"{semente}:{image_id}".encode("utf-8")
    return int.from_bytes(sha256(material).digest()[:8], "big")


def _resolver_imagem(raiz_imagens: Path, relativo: str) -> Path:
    partes = Path(relativo).parts
    candidatos = [raiz_imagens.joinpath(*partes)]
    if partes and partes[0] == raiz_imagens.name:
        candidatos.append(raiz_imagens.joinpath(*partes[1:]))
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    return candidatos[0]


def _carregar_csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def _carregar_referencia_t41(
    raiz: Path, registros: list[dict[str, str]]
) -> dict[str, str]:
    caminho = raiz / "assets/data/padronizacao_T4_1/referencia_entrada.csv"
    referencia = _carregar_csv(caminho)
    por_id = {linha["image_id"]: linha for linha in referencia}
    if len(por_id) != len(referencia):
        raise ValueError("a referência da T4.1 contém image_id duplicado")
    ids_manifesto = {linha["image_id"] for linha in registros}
    if set(por_id) != ids_manifesto:
        raise ValueError("a referência da T4.1 não corresponde ao manifesto da T4.2")
    divergentes = [
        linha["image_id"]
        for linha in registros
        if por_id[linha["image_id"]]["particao"] != linha["particao"]
    ]
    if divergentes:
        raise ValueError(
            "a referência da T4.1 diverge da partição da T4.2: "
            + ", ".join(divergentes[:3])
        )
    return {image_id: linha["sha256_entrada"] for image_id, linha in por_id.items()}


def _validar_parametros(parametros_t41: dict, parametros_t44: dict) -> None:
    if parametros_t41["tamanho_entrada"] != TAMANHO_ENTRADA:
        raise ValueError("o tamanho registrado na T4.1 diverge do código")
    if tuple(parametros_t41["cor_preenchimento"]) != COR_PREENCHIMENTO:
        raise ValueError("a cor de preenchimento registrada na T4.1 diverge do código")
    if parametros_t44["probabilidade_por_transformacao"] != PROBABILIDADE:
        raise ValueError("a probabilidade registrada na T4.4 diverge do código")
    if parametros_t44["aplicado_somente_em"] != "treino":
        raise ValueError("os parâmetros da T4.4 permitem augmentation fora do treino")


def _pesos_balanceados(registros: list[dict[str, str]]) -> dict[int, dict[str, float | int | str]]:
    treino = [registro for registro in registros if registro["particao"] == "treino"]
    contagens = Counter(int(registro["indice_modelo"]) for registro in treino)
    nomes = {int(r["indice_modelo"]): r["nome_classe_modelo"] for r in registros}
    indices = sorted(nomes)
    if indices != list(range(len(indices))):
        raise ValueError("índices das classes não são consecutivos")
    if set(contagens) != set(indices):
        raise ValueError("há classe sem imagem de treino")
    total = len(treino)
    quantidade_classes = len(indices)
    return {
        indice: {
            "nome_classe": nomes[indice],
            "imagens_treino": contagens[indice],
            "peso": total / (quantidade_classes * contagens[indice]),
        }
        for indice in indices
    }


def _comparar_particionamento(raiz: Path, reproduzido: Path) -> dict[str, str]:
    aprovado = raiz / "assets/data/particionamento_T4_2"
    hashes = {}
    divergentes = []
    for nome in ARQUIVOS_PARTICAO:
        esperado = aprovado / nome
        obtido = reproduzido / nome
        hashes[nome] = _hash_arquivo(obtido)
        if esperado.read_bytes() != obtido.read_bytes():
            divergentes.append(nome)
    if divergentes:
        raise ValueError(
            "a execução não reproduziu os artefatos aprovados da T4.2: "
            + ", ".join(divergentes)
        )
    return hashes


def executar(
    raiz: Path,
    pasta_saida: Path,
    raiz_imagens: Path | None = None,
    semente: int = SEMENTE,
) -> dict:
    """Executa T4.5 e retorna a auditoria produzida."""
    if semente != SEMENTE:
        raise ValueError(
            f"a T4.2 aprovada usa a semente fixa {SEMENTE}; recebida: {semente}"
        )
    raiz = raiz.resolve()
    pasta_saida.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="agroapp-t4-5-") as temporario:
        pasta_reproduzida = gerar(raiz, Path(temporario))
        hashes_particao = _comparar_particionamento(raiz, pasta_reproduzida)
        registros = _carregar_csv(pasta_reproduzida / "manifesto_modelo.csv")

    if not registros:
        raise ValueError("manifesto do modelo está vazio")
    if {registro["particao"] for registro in registros} != set(PARTICOES):
        raise ValueError("manifesto não contém as três partições esperadas")

    referencia_t41 = _carregar_referencia_t41(raiz, registros)
    pesos = _pesos_balanceados(registros)
    contagens_particao = Counter(registro["particao"] for registro in registros)
    ausentes: list[str] = []
    falhas: list[str] = []
    indice = []
    for registro in registros:
        particao = registro["particao"]
        usar_aumento = particao == "treino"
        semente_amostra = _semente_amostra(registro["image_id"], semente) if usar_aumento else None
        hash_preprocessamento = referencia_t41[registro["image_id"]]
        hash_aumento = ""
        if raiz_imagens is not None:
            caminho = _resolver_imagem(raiz_imagens, registro["caminho_relativo"])
            if not caminho.is_file():
                ausentes.append(registro["caminho_relativo"])
            else:
                try:
                    if _hash_arquivo(caminho) != registro["sha256"]:
                        raise ValueError("hash do arquivo original diverge do manifesto")
                    imagem = preparar_imagem(caminho)
                    hash_obtido = _hash_array(imagem)
                    if hash_obtido != hash_preprocessamento:
                        raise ValueError("hash de preprocessamento diverge da T4.1")
                    if usar_aumento:
                        rng = np.random.default_rng(semente_amostra)
                        hash_aumento = _hash_array(aplicar_aumento(imagem, particao, rng))
                except (OSError, ValueError) as erro:
                    falhas.append(f"{registro['image_id']}: {erro}")
        indice.append(
            {
                "image_id": registro["image_id"],
                "caminho_relativo": registro["caminho_relativo"],
                "sha256_original": registro["sha256"],
                "indice_modelo": registro["indice_modelo"],
                "nome_classe_modelo": registro["nome_classe_modelo"],
                "grupo_particao": registro["grupo_particao"],
                "particao": particao,
                "peso_classe_treino": f"{pesos[int(registro['indice_modelo'])]['peso']:.12f}"
                if usar_aumento else "",
                "aplicar_augmentation": "sim" if usar_aumento else "nao",
                "semente_augmentation": str(semente_amostra) if usar_aumento else "",
                "sha256_preprocessamento": hash_preprocessamento,
                "sha256_augmentation": hash_aumento,
            }
        )

    if ausentes or falhas:
        detalhes = []
        if ausentes:
            detalhes.append(
                f"{len(ausentes)} imagens não encontradas; exemplos: {', '.join(ausentes[:3])}"
            )
        if falhas:
            detalhes.append(f"{len(falhas)} imagens inválidas; exemplos: {'; '.join(falhas[:3])}")
        raise RuntimeError(" | ".join(detalhes))

    campos = list(indice[0])
    with (pasta_saida / "indice_pipeline.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(indice)

    pesos_serializaveis = {
        str(indice_classe): dados for indice_classe, dados in pesos.items()
    }
    (pasta_saida / "pesos_classes.json").write_text(
        json.dumps(
            {
                "formula": "N / (K * n_c)",
                "calculado_somente_sobre": "imagens originais de treino",
                "total_treino": contagens_particao["treino"],
                "quantidade_classes": len(pesos),
                "classes": pesos_serializaveis,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    parametros_t41 = json.loads(
        (raiz / "assets/data/padronizacao_T4_1/parametros.json").read_text(encoding="utf-8")
    )
    parametros_t44 = json.loads(
        (raiz / "assets/data/aumento_T4_4/parametros.json").read_text(encoding="utf-8")
    )
    _validar_parametros(parametros_t41, parametros_t44)
    parametros = {
        "semente_global": semente,
        "manifesto": "assets/data/particionamento_T4_2/manifesto_modelo.csv",
        "classes": "assets/data/classes-modelo.csv",
        "padronizacao_T4_1": parametros_t41,
        "balanceamento_T4_3": {
            "estrategia_inicial": "ponderacao_de_classes",
            "formula": "N / (K * n_c)",
            "somente_treino": True,
        },
        "augmentation_T4_4": parametros_t44,
        "augmentation_em_validacao": False,
        "augmentation_em_teste": False,
    }
    (pasta_saida / "parametros.json").write_text(
        json.dumps(parametros, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    auditoria = {
        "semente": semente,
        "ambiente": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "pillow": PIL.__version__,
        },
        "entradas_sha256": {
            "classes_modelo": _hash_arquivo(raiz / "assets/data/classes-modelo.csv"),
            "referencia_T4_1": _hash_arquivo(
                raiz / "assets/data/padronizacao_T4_1/referencia_entrada.csv"
            ),
            "parametros_T4_1": _hash_arquivo(
                raiz / "assets/data/padronizacao_T4_1/parametros.json"
            ),
            "parametros_T4_4": _hash_arquivo(
                raiz / "assets/data/aumento_T4_4/parametros.json"
            ),
        },
        "particionamento_reproduzido": True,
        "hashes_particionamento": hashes_particao,
        "total_imagens": len(registros),
        "classes_modelo": len(pesos),
        "imagens_por_particao": {
            particao: contagens_particao[particao] for particao in PARTICOES
        },
        "augmentation_somente_treino": all(
            (linha["particao"] == "treino") == (linha["aplicar_augmentation"] == "sim")
            for linha in indice
        ),
        "pesos_calculados_somente_no_treino": True,
        "imagens_verificadas": raiz_imagens is not None,
        "imagens_ausentes": len(ausentes),
        "indice_pipeline_sha256": _hash_arquivo(pasta_saida / "indice_pipeline.csv"),
    }
    (pasta_saida / "auditoria.json").write_text(
        json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return auditoria


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o pipeline reproduzível T4.5")
    parser.add_argument(
        "--raiz-imagens",
        type=Path,
        help="Pasta que contém dataset/, Milho/ e Soja/; omitida, valida somente índices",
    )
    parser.add_argument("--semente", type=int, default=SEMENTE)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    saida = raiz / "assets/data/pipeline_T4_5"
    auditoria = executar(raiz, saida, args.raiz_imagens, args.semente)
    print(json.dumps(auditoria, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
