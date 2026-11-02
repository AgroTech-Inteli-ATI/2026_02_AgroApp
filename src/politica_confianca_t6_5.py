r"""Política de confiança (T6.5): top-k e limiar sobre probabilidades de VALIDAÇÃO.

Regra avaliada: se a confiança do top-1 for >= limiar, o app mostra as k hipóteses
mais prováveis; se for menor, o resultado é inconclusivo (RF-06). Este módulo mede,
para cada limiar, a cobertura e o acerto, e nunca abre a partição de teste.

Uso:
    python -m src.politica_confianca_t6_5 \
        --probabilidades assets/data/politica_T6_5/probabilidades_validacao.csv \
        [--limiar 0.60] [--meta-acerto 0.90]

Entrada: CSV gerado por src.probabilidades_validacao_t6_5 (image_id, indice_real,
p_0..p_N). Cada image_id é conferido no índice T5.2 do candidato: todos devem ser da validação,
com o mesmo rótulo, e a validação inteira deve estar presente.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "assets/data/politica_T6_5"
INDICE_PADRAO = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
CLASSES_PADRAO = RAIZ / "assets/data/classes-modelo.csv"
PARTICAO = "validacao"
TOLERANCIA_SOMA = 1e-4
LIMIARES = tuple(round(0.30 + 0.05 * i, 2) for i in range(14))  # 0,30 a 0,95
KS = (1, 2, 3, 5)
COLUNAS_CURVA = [
    "limiar", "cobertura", "aceitas", "inconclusivos",
    "acerto_top1_aceitas", "acerto_top2_aceitas", "acerto_top3_aceitas", "acerto_top5_aceitas",
]
COLUNAS_CLASSE = [
    "indice", "classe", "suporte", "aceitas", "cobertura", "acertos_aceitas",
    "recall_no_limiar", "recall_sem_limiar",
]


def ler_nomes_classes(caminho: Path = CLASSES_PADRAO) -> list[str]:
    """Nomes das classes na ordem de saída do modelo (assets/data/classes-modelo.csv)."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))
    nomes = {int(linha["indice_modelo"]): linha["classe"] for linha in linhas}
    if not nomes or sorted(nomes) != list(range(len(nomes))):
        raise ValueError("índices de classes-modelo.csv não são consecutivos a partir de 0")
    return [nomes[i] for i in range(len(nomes))]


def ler_indice(caminho: Path = INDICE_PADRAO) -> dict[str, tuple[str, int]]:
    """image_id -> (partição, índice da classe), do índice da T4.5."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    indice = {}
    for linha in linhas:
        if linha["image_id"] in indice:
            raise ValueError(f"image_id duplicado no índice: {linha['image_id']}")
        indice[linha["image_id"]] = (linha["particao"], int(linha["indice_modelo"]))
    return indice


def validar_matriz(probabilidades: np.ndarray, quantidade_classes: int) -> None:
    """Recusa formato, valores não finitos, fora de [0, 1] ou soma por linha != 1."""
    if probabilidades.ndim != 2 or probabilidades.shape[1] != quantidade_classes:
        raise ValueError(
            f"esperadas {quantidade_classes} colunas de probabilidade; "
            f"recebido formato {probabilidades.shape}"
        )
    if probabilidades.shape[0] == 0:
        raise ValueError("nenhuma linha de probabilidades")
    if not np.isfinite(probabilidades).all():
        raise ValueError("há probabilidade não finita (NaN ou infinito)")
    if (probabilidades < 0).any() or (probabilidades > 1).any():
        raise ValueError("há probabilidade fora de [0, 1]")
    desvio = np.abs(probabilidades.sum(axis=1) - 1.0)
    if (desvio > TOLERANCIA_SOMA).any():
        raise ValueError(
            f"{int((desvio > TOLERANCIA_SOMA).sum())} linhas não somam 1 "
            f"(tolerância {TOLERANCIA_SOMA}); maior desvio {desvio.max():.6f}"
        )


def ler_probabilidades(
    caminho: Path, indice: dict[str, tuple[str, int]], quantidade_classes: int
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Lê e valida o CSV; retorna (image_ids, rótulos reais, matriz de probabilidades)."""
    esperado = ["image_id", "indice_real"] + [f"p_{i}" for i in range(quantidade_classes)]
    with Path(caminho).open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor, None)
        if cabecalho != esperado:
            raise ValueError(f"cabeçalho inesperado; esperado {esperado[:3]}…{esperado[-1]}")
        linhas = list(leitor)
    ids, rotulos, valores = [], [], []
    for numero, linha in enumerate(linhas, 2):
        if len(linha) != len(esperado):
            raise ValueError(f"linha {numero}: número de colunas inválido")
        try:
            rotulos.append(int(linha[1]))
            valores.append([float(texto) for texto in linha[2:]])
        except ValueError as erro:
            raise ValueError(f"linha {numero}: valor não numérico") from erro
        ids.append(linha[0])
    if len(set(ids)) != len(ids):
        raise ValueError("image_id duplicado nas probabilidades")
    probabilidades = np.array(valores, dtype=np.float64)
    validar_matriz(probabilidades, quantidade_classes)
    rotulos = np.array(rotulos, dtype=np.int64)
    if (rotulos < 0).any() or (rotulos >= quantidade_classes).any():
        raise ValueError("indice_real fora do intervalo das classes")
    fora = [i for i in ids if i not in indice]
    if fora:
        raise ValueError(f"{len(fora)} image_id ausentes do índice; exemplo: {fora[0]}")
    outras = [i for i in ids if indice[i][0] != PARTICAO]
    if outras:
        raise ValueError(
            f"{len(outras)} imagens não são da validação (ex.: {outras[0]}, "
            f"partição '{indice[outras[0]][0]}'); a política só usa a validação"
        )
    validacao = {i for i, (particao, _) in indice.items() if particao == PARTICAO}
    if set(ids) != validacao:
        raise ValueError(
            f"as probabilidades cobrem {len(ids)} imagens, mas a validação do índice "
            f"tem {len(validacao)}"
        )
    if any(indice[i][1] != r for i, r in zip(ids, rotulos)):
        raise ValueError("indice_real diverge do rótulo do índice")
    return ids, rotulos, probabilidades


def ordem_topk(probabilidades: np.ndarray, k: int) -> np.ndarray:
    """Índices das k classes mais prováveis; empate: menor índice primeiro."""
    if not 1 <= k <= probabilidades.shape[1]:
        raise ValueError(f"k deve estar entre 1 e {probabilidades.shape[1]}")
    return np.argsort(-probabilidades, axis=1, kind="stable")[:, :k]


def acerto_topk(probabilidades: np.ndarray, rotulos: np.ndarray, k: int) -> np.ndarray:
    """Para cada imagem, se a classe real está entre as k mais prováveis."""
    return (ordem_topk(probabilidades, k) == rotulos[:, None]).any(axis=1)


def curva(
    probabilidades: np.ndarray, rotulos: np.ndarray,
    limiares: tuple[float, ...] = LIMIARES, ks: tuple[int, ...] = KS,
) -> list[dict]:
    """Por limiar: cobertura (top-1 >= limiar) e acerto top-k entre as aceitas.

    Sem imagens aceitas, os acertos ficam None (indefinidos), nunca zero.
    """
    confianca = probabilidades.max(axis=1)
    acertos = {k: acerto_topk(probabilidades, rotulos, k) for k in ks}
    total = len(rotulos)
    linhas = []
    for limiar in limiares:
        aceita = confianca >= limiar
        n = int(aceita.sum())
        linha = {
            "limiar": limiar, "cobertura": n / total, "aceitas": n,
            "inconclusivos": (total - n) / total,
        }
        for k in ks:
            linha[f"acerto_top{k}_aceitas"] = float(acertos[k][aceita].mean()) if n else None
        linhas.append(linha)
    return linhas


def sugerir_limiar(linhas: list[dict], meta_acerto: float) -> float | None:
    """Menor limiar da grade com acerto top-1 entre as aceitas >= meta; None se nenhum."""
    for linha in linhas:
        acerto = linha["acerto_top1_aceitas"]
        if acerto is not None and acerto >= meta_acerto - 1e-12:
            return linha["limiar"]
    return None


def cobertura_por_classe(
    probabilidades: np.ndarray, rotulos: np.ndarray, limiar: float, nomes: list[str]
) -> list[dict]:
    """Por classe real: cobertura (top-1 >= limiar) e recall com e sem o limiar.

    recall_no_limiar conta como não reconhecida a imagem inconclusiva;
    recall_sem_limiar é o recall do argmax puro.
    """
    previsto = probabilidades.argmax(axis=1)
    aceita = probabilidades.max(axis=1) >= limiar
    linhas = []
    for indice, nome in enumerate(nomes):
        da_classe = rotulos == indice
        suporte = int(da_classe.sum())
        aceitas = int((da_classe & aceita).sum())
        certas_aceitas = int((da_classe & aceita & (previsto == indice)).sum())
        certas = int((da_classe & (previsto == indice)).sum())
        linhas.append({
            "indice": indice, "classe": nome, "suporte": suporte, "aceitas": aceitas,
            "cobertura": aceitas / suporte if suporte else None,
            "acertos_aceitas": certas_aceitas,
            "recall_no_limiar": certas_aceitas / suporte if suporte else None,
            "recall_sem_limiar": certas / suporte if suporte else None,
        })
    return linhas


def _formatar(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float):
        return f"{valor:.6f}"
    return str(valor)


def gravar_csv(caminho: Path, colunas: list[str], linhas: list[dict]) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(colunas)
        escritor.writerows([_formatar(linha[coluna]) for coluna in colunas] for linha in linhas)


def _percentual(valor) -> str:
    return "  n/d " if valor is None else f"{valor * 100:5.1f}%"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--probabilidades", type=Path, required=True)
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO)
    parser.add_argument("--classes", type=Path, default=CLASSES_PADRAO)
    parser.add_argument("--saida", type=Path, default=PASTA)
    parser.add_argument("--limiar", type=float, default=None,
                        help="grava também a cobertura por classe neste limiar")
    parser.add_argument("--meta-acerto", type=float, default=0.90)
    args = parser.parse_args(argv)
    if not 0 < args.meta_acerto <= 1:
        parser.error("--meta-acerto deve estar em (0, 1]")
    if args.limiar is not None and not 0 <= args.limiar <= 1:
        parser.error("--limiar deve estar em [0, 1]")

    nomes = ler_nomes_classes(args.classes)
    if len(nomes) < max(KS):
        parser.error(f"são necessárias ao menos {max(KS)} classes para calcular o top-{max(KS)}")
    ids, rotulos, probabilidades = ler_probabilidades(
        args.probabilidades, ler_indice(args.indice), len(nomes)
    )
    print(f"Validação: {len(ids)} imagens, {len(nomes)} classes.")

    print("\nAcerto sem limiar (todas as imagens):")
    geral = {k: float(acerto_topk(probabilidades, rotulos, k).mean()) for k in KS}
    anterior = None
    for k in KS:
        ganho = "" if anterior is None else f"  (+{(geral[k] - anterior) * 100:.1f} p.p. sobre k anterior)"
        print(f"  top-{k}: {_percentual(geral[k])}{ganho}")
        anterior = geral[k]

    linhas = curva(probabilidades, rotulos)
    caminho_curva = args.saida / "curva_limiar_validacao.csv"
    gravar_csv(caminho_curva, COLUNAS_CURVA, linhas)
    print("\nCurva por limiar (acerto entre as aceitas):")
    print("  limiar  cobertura  inconcl.   top-1    top-2    top-3    top-5")
    for linha in linhas:
        print(
            f"  {linha['limiar']:.2f}   {_percentual(linha['cobertura'])}   "
            f"{_percentual(linha['inconclusivos'])}  "
            + "  ".join(_percentual(linha[f"acerto_top{k}_aceitas"]) for k in KS)
        )
    print(f"Gravado: {caminho_curva}")

    sugerido = sugerir_limiar(linhas, args.meta_acerto)
    if sugerido is None:
        print(f"\nNenhum limiar da grade atinge acerto top-1 >= {args.meta_acerto:.2f} entre as aceitas.")
    else:
        print(f"\nLimiar sugerido (menor da grade com acerto top-1 >= {args.meta_acerto:.2f}): {sugerido:.2f}")

    if args.limiar is not None:
        por_classe = cobertura_por_classe(probabilidades, rotulos, args.limiar, nomes)
        caminho_classe = args.saida / "cobertura_por_classe_validacao.csv"
        gravar_csv(caminho_classe, COLUNAS_CLASSE, por_classe)
        print(f"\nCobertura por classe no limiar {args.limiar:.2f}:")
        for linha in por_classe:
            print(
                f"  {linha['indice']:2d} {linha['classe'][:46]:46s} suporte {linha['suporte']:3d}  "
                f"cobertura {_percentual(linha['cobertura'])}  recall {_percentual(linha['recall_no_limiar'])}"
            )
        print(f"Gravado: {caminho_classe}")


if __name__ == "__main__":
    main()
