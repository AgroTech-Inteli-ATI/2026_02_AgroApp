"""Matriz de confusão e análise de erros do build final (T11.2).

Parte das predições que a T11.1 publicou (`predicoes.csv`: 13 scores por imagem, para o
Float16 principal e o INT8 de contingência, no teste histórico e na validação) e do índice
histórico auditado na T10.1. Não roda modelo nem precisa das imagens: tudo o que está aqui é
recalculável a partir de arquivos versionados.

Produz, em `assets/data/matriz_erros_T11_2`: as matrizes de confusão (contagens, CSV e JSON),
um mapa de calor em SVG, os pares de confusão, o desempenho por classe, a lista de erros por
imagem e as observações do iNaturalist com mais de um erro. O relatório vai para
`docs/Matriz_Erros_T11_2.md`.

Os resultados são exploratórios: o teste histórico já foi consultado no desenvolvimento e não
é um conjunto independente (T10.1). Uma observação do iNaturalist reúne várias fotos do mesmo
indivíduo ou cena; as fotos do AgroInsect não têm esse identificador, e cada uma é contada como
uma origem separada, o que pode superestimar a independência.

python -m src.matriz_erros_t11_2            # regenera os artefatos e o relatório
python -m src.matriz_erros_t11_2 --verificar  # falha se algo publicado estiver desatualizado
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "assets/data"
PREDICOES = DADOS / "avaliacao_final_T11_1/predicoes.csv"
METRICAS_T11_1 = DADOS / "avaliacao_final_T11_1/metricas.json"
INDICE = DADOS / "treino_T5_2/indice_dataset.csv"
GRUPOS_T10_1 = DADOS / "independencia_T10_1/grupos_relacionados.csv"
CLASSES = RAIZ / "assets/modelos/candidato_T5_6_20261026/classes.json"
REVISAO_T6_3 = DADOS / "avaliacao_T6_3/candidato_T5_6_20261026_keras/revisao_por_imagem.csv"
PARES_T6_3 = DADOS / "avaliacao_T6_3/candidato_T5_6_20261026_keras/analise_por_par.csv"
SAIDA = DADOS / "matriz_erros_T11_2"
DOC = RAIZ / "docs/Matriz_Erros_T11_2.md"
MODELOS = ("Float16", "INT8")
PARTICOES = ("teste", "validacao")
REFERENCIA = ("Float16", "teste")  # resultado de referência da entrega (T11.1)
F1_BAIXO = 0.60  # F1 abaixo disso, como na leitura da T11.1; aqui vale também para o recall
# Grupos por tipo de inseto (nome comum), para medir quantas confusões ocorrem entre classes parecidas.
GRUPOS = {"percevejos": (2, 4, 5, 6, 7), "lagartas": (3, 8, 9, 10), "besouros": (0, 11), "cigarrinhas": (1, 12)}
MIN_ERROS_PAR = 2
ESQUEMA = "matriz_erros_T11_2_v1"
# Figura de referência em assets, como as da T6.2 (matriz_confusao_T6_2_*.png).
FIGURA_REFERENCIA = "assets/matriz_confusao_T11_2_float16_teste.svg"
ENTRADAS = {"predicoes_t11_1": PREDICOES, "metricas_t11_1": METRICAS_T11_1, "indice": INDICE, "grupos_t10_1": GRUPOS_T10_1,
            "classes": CLASSES, "revisao_t6_3": REVISAO_T6_3, "pares_t6_3": PARES_T6_3}


def _csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def _sha(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def _txt(texto: str) -> str:
    return texto.replace("\r\n", "\n")


def carregar(raiz: Path = RAIZ) -> dict:
    """Lê as entradas e valida a coerência entre predições, índice e classes."""
    caminhos = {k: raiz / v.relative_to(RAIZ) for k, v in ENTRADAS.items()}
    nomes = [c["nome"] for c in json.loads(caminhos["classes"].read_text(encoding="utf-8"))]
    if len(nomes) != 13:
        raise ValueError("o catálogo de classes não tem 13 classes")
    indice = {}
    for linha in _csv(caminhos["indice"]):
        arquivo = linha["caminho_relativo"].rsplit("/", 1)[-1]
        achado = re.match(r"inat(\d+)_", arquivo)
        indice[linha["image_id"]] = {
            "caminho": linha["caminho_relativo"], "particao": linha["particao"], "grupo": linha["grupo_particao"],
            "classe": int(linha["indice_modelo"]), "obs": achado.group(1) if achado else None,
        }
    predicoes = []
    for linha in _csv(caminhos["predicoes_t11_1"]):
        real, previsto = int(linha["indice_real"]), int(linha["indice_previsto"])
        scores = [float(linha[f"score_{i}"]) for i in range(13)]
        ref = indice[linha["image_id"]]
        if ref["classe"] != real or ref["particao"] != linha["particao"]:
            raise ValueError(f"predição diverge do índice: {linha['image_id']}")
        if max(range(13), key=lambda i: scores[i]) != previsto:
            raise ValueError(f"classe prevista não é o maior score: {linha['image_id']}")
        predicoes.append({"id": linha["image_id"], "modelo": linha["modelo"], "particao": linha["particao"], "real": real,
                          "previsto": previsto, "score": float(linha["score_top1"]), "decisao": linha["decisao"]})
    vinculos = {linha["image_id"]: linha["natureza"] for linha in _csv(caminhos["grupos_t10_1"])}
    revisao = {linha["image_id"]: linha for linha in _csv(caminhos["revisao_t6_3"])}
    pares_t6_3 = {(int(l["indice_real"]), int(l["indice_previsto"])): int(l["erros"]) for l in _csv(caminhos["pares_t6_3"])}
    return {"nomes": nomes, "indice": indice, "predicoes": predicoes, "vinculos": vinculos, "revisao": revisao,
            "pares_t6_3": pares_t6_3, "hashes": {k: _sha(v) for k, v in caminhos.items()}}


def pearson(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx, syy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def matriz(linhas: list[dict]) -> list[list[int]]:
    m = [[0] * 13 for _ in range(13)]
    for l in linhas:
        m[l["real"]][l["previsto"]] += 1
    return m


def por_classe(m: list[list[int]], nomes: list[str]) -> list[dict]:
    saida = []
    for i in range(13):
        suporte, vp = sum(m[i]), m[i][i]
        previstos = sum(m[j][i] for j in range(13))
        recall = vp / suporte if suporte else 0.0
        precisao = vp / previstos if previstos else 0.0
        f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
        saida.append({"indice": i, "classe": nomes[i], "suporte": suporte, "vp": vp, "fn": suporte - vp, "fp": previstos - vp,
                      "recall": recall, "precisao": precisao, "f1": f1})
    return saida


def analisar(dados: dict) -> dict:
    """Todas as tabelas da T11.2, em estruturas simples e determinísticas."""
    nomes, indice = dados["nomes"], dados["indice"]
    obs_por_particao: dict[str, set[str]] = {}
    treino_por_classe = {i: {"imagens": 0, "grupos": set(), "obs": set(), "agroinsect": 0} for i in range(13)}
    teste_obs_por_classe = {i: set() for i in range(13)}
    for ref in indice.values():
        if ref["obs"]:
            obs_por_particao.setdefault(ref["obs"], set()).add(ref["particao"])
        if ref["particao"] == "treino":
            t = treino_por_classe[ref["classe"]]
            t["imagens"] += 1
            t["grupos"].add(ref["grupo"])
            if ref["obs"]:
                t["obs"].add(ref["obs"])
            t["agroinsect"] += 0 if ref["obs"] else 1
        elif ref["particao"] == "teste" and ref["obs"]:
            teste_obs_por_classe[ref["classe"]].add(ref["obs"])

    por_modelo: dict[tuple, list[dict]] = {}
    for p in dados["predicoes"]:
        por_modelo.setdefault((p["modelo"], p["particao"]), []).append(p)
    por_id = {k: {p["id"]: p for p in v} for k, v in por_modelo.items()}

    resultado = {"matrizes": {}, "classes": {}, "pares": [], "erros": [], "observacoes": [], "correlacoes": {}}
    for modelo in MODELOS:
        for particao in PARTICOES:
            linhas = por_modelo[(modelo, particao)]
            m = matriz(linhas)
            resultado["matrizes"][f"{modelo}|{particao}"] = m
            classes = por_classe(m, nomes)
            erros = [p for p in linhas if p["real"] != p["previsto"]]
            for c in classes:
                i = c["indice"]
                fn = [p for p in erros if p["real"] == i]
                fp = [p for p in erros if p["previsto"] == i]
                destinos = sorted(((m[i][j], j) for j in range(13) if j != i and m[i][j]), reverse=True)
                origens = sorted(((m[j][i], j) for j in range(13) if j != i and m[j][i]), reverse=True)
                obs_fn = [indice[p["id"]]["obs"] for p in fn]
                c.update({
                    "treino_imagens": treino_por_classe[i]["imagens"], "treino_grupos": len(treino_por_classe[i]["grupos"]),
                    "treino_obs_inat": len(treino_por_classe[i]["obs"]), "treino_agroinsect": treino_por_classe[i]["agroinsect"],
                    "obs_inat_no_suporte": len(teste_obs_por_classe[i]) if particao == "teste" else None,
                    "fn_obs_inat_distintas": len({o for o in obs_fn if o}), "fn_agroinsect": sum(1 for o in obs_fn if not o),
                    "destino_principal": destinos[0][1] if destinos else None,
                    "destino_principal_erros": destinos[0][0] if destinos else 0,
                    "origem_principal_fp": origens[0][1] if origens else None,
                    "origem_principal_fp_erros": origens[0][0] if origens else 0,
                    "menor_desempenho": c["f1"] < F1_BAIXO or c["recall"] < F1_BAIXO,
                })
            resultado["classes"][f"{modelo}|{particao}"] = classes
            if particao == "teste":
                x = [math.log10(c["treino_imagens"]) for c in classes]
                resultado["correlacoes"][modelo] = {
                    "log10_treino_vs_f1": pearson(x, [c["f1"] for c in classes]),
                    "log10_treino_vs_recall": pearson(x, [c["recall"] for c in classes]),
                }
            # pares direcionais
            pares: dict[tuple, list[dict]] = {}
            for p in erros:
                pares.setdefault((p["real"], p["previsto"]), []).append(p)
            outro = "INT8" if modelo == "Float16" else "Float16"
            for (real, previsto), lista in pares.items():
                obs = [indice[p["id"]]["obs"] for p in lista]
                outro_iguais = sum(1 for p in lista if por_id[(outro, particao)][p["id"]]["previsto"] == previsto)
                resultado["pares"].append({
                    "modelo": modelo, "particao": particao, "real": real, "previsto": previsto, "erros": len(lista),
                    "suporte_real": sum(m[real]), "pct_da_classe": len(lista) / sum(m[real]),
                    "pct_dos_erros": len(lista) / len(erros), "obs_inat_distintas": len({o for o in obs if o}),
                    "agroinsect": sum(1 for o in obs if not o), "grupos_distintos": len({indice[p["id"]]["grupo"] for p in lista}),
                    "erros_com_score_aceito": sum(1 for p in lista if p["decisao"] == "aceito"),
                    "score_medio": sum(p["score"] for p in lista) / len(lista), "score_maximo": max(p["score"] for p in lista),
                    "repetido_no_outro_modelo": outro_iguais,
                    "erros_t6_3_keras_fp32": dados["pares_t6_3"].get((real, previsto), 0) if particao == "teste" else None,
                    "ids": sorted(p["id"] for p in lista),
                })
            # erros por imagem
            for p in sorted(erros, key=lambda e: e["id"]):
                ref = indice[p["id"]]
                rev = dados["revisao"].get(p["id"]) if particao == "teste" else None
                resultado["erros"].append({
                    "modelo": modelo, "particao": particao, "image_id": p["id"], "caminho": ref["caminho"], "real": p["real"],
                    "previsto": p["previsto"], "score_top1": p["score"], "decisao": p["decisao"],
                    "origem": "iNaturalist" if ref["obs"] else "AgroInsect", "obs_inat": ref["obs"] or "", "grupo": ref["grupo"],
                    "obs_em_outras_particoes": ";".join(sorted(obs_por_particao.get(ref["obs"], set()) - {particao})) if ref["obs"] else "",
                    "vinculo_t10_1": dados["vinculos"].get(p["id"], ""),
                    "outro_modelo_previu": por_id[(outro, particao)][p["id"]]["previsto"],
                    "estagio_t6_3": rev["life_stage_metadado"] if rev else "", "fatores_t6_3": rev["fatores_observados"] if rev else "",
                    "causa_t6_3": rev["status_causa"] if rev else "",
                })
            # observações com vários erros
            por_obs: dict[str, list[dict]] = {}
            for p in erros:
                if indice[p["id"]]["obs"]:
                    por_obs.setdefault(indice[p["id"]]["obs"], []).append(p)
            for obs, lista in por_obs.items():
                if len(lista) > 1:
                    resultado["observacoes"].append({
                        "modelo": modelo, "particao": particao, "obs_inat": obs, "erros": len(lista),
                        "classes_reais": ";".join(sorted({str(p["real"]) for p in lista})),
                        "classes_previstas": ";".join(sorted({str(p["previsto"]) for p in lista})),
                        "ids": ";".join(sorted(p["id"] for p in lista)),
                    })
    resultado["pares"].sort(key=lambda r: (r["modelo"], r["particao"], -r["erros"], r["real"], r["previsto"]))
    resultado["observacoes"].sort(key=lambda r: (r["modelo"], r["particao"], -r["erros"], r["obs_inat"]))
    return resultado


# ---------- escrita ----------
def _num(x) -> str:
    return "" if x is None else (f"{x:.6f}" if isinstance(x, float) else str(x))


def _csv_texto(campos: list[str], linhas: list[dict]) -> str:
    buffer = io.StringIO()
    escritor = csv.writer(buffer, lineterminator="\n")
    escritor.writerow(campos)
    for linha in linhas:
        escritor.writerow([(";".join(linha[c]) if isinstance(linha[c], list) else _num(linha[c])) for c in campos])
    return buffer.getvalue()


FONTE = "DejaVu Sans, Verdana, Arial, sans-serif"
COR_DESTAQUE = "#7f1d1d"  # borda dos pares com >= MIN_ERROS_PAR erros (vermelho escuro, da mesma paleta)


def cor_acerto(f: float) -> tuple[int, int, int]:
    """Diagonal: verde que escurece com a fração da classe real."""
    return int(235 - 150 * f), int(244 - 70 * f), int(236 - 130 * f)


def cor_erro(f: float) -> tuple[int, int, int]:
    """Fora da diagonal: vermelho que satura quando a fração chega a cerca de 45%."""
    t = min(f * 2.2, 1.0)
    return int(255 - 25 * t), int(255 - 150 * t), int(255 - 190 * t)


def _rgb(c: tuple[int, int, int]) -> str:
    return f"rgb({c[0]},{c[1]},{c[2]})"


def svg_matriz(m: list[list[int]], nomes: list[str], linha1: str, linha2: str) -> str:
    """Matriz 13x13 no padrão das figuras da T6.2: título em duas linhas, rótulos 'Classe (n=suporte)',
    contagem em cada célula e, nos pares com pelo menos MIN_ERROS_PAR erros, contagem e % da classe real
    destacadas com borda. Verde = acerto (diagonal); vermelho = confusão. Cor = fração da classe real."""
    lado, x0, y0 = 50, 262, 104
    lado_matriz = 13 * lado
    largura, altura = x0 + lado_matriz + 150, y0 + lado_matriz + 250
    curtos = [n.split(" (")[0] for n in nomes]
    suportes = [sum(l) for l in m]
    f = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" width="{largura}" height="{altura}" '
         f'font-family="{FONTE}" role="img" aria-label="{linha1}. {linha2}">']
    stops_a = "".join(f'<stop offset="{o}" stop-color="{_rgb(cor_acerto(o))}"/>' for o in (0, 0.5, 1))
    stops_e = "".join(f'<stop offset="{o:.4f}" stop-color="{_rgb(cor_erro(o))}"/>' for o in (0, 1 / 2.2, 1))
    f.append('<defs><linearGradient id="gAcerto" x1="0" y1="1" x2="0" y2="0">' + stops_a + "</linearGradient>"
             '<linearGradient id="gErro" x1="0" y1="1" x2="0" y2="0">' + stops_e + "</linearGradient></defs>")
    f.append(f'<rect width="{largura}" height="{altura}" fill="#ffffff"/>')
    cx = x0 + lado_matriz / 2
    f.append(f'<text x="{cx}" y="36" text-anchor="middle" font-size="21" fill="#111">{linha1}</text>')
    f.append(f'<text x="{cx}" y="64" text-anchor="middle" font-size="21" fill="#111">{linha2}</text>')
    for i in range(13):
        for j in range(13):
            frac = m[i][j] / suportes[i] if suportes[i] else 0.0
            cor = cor_acerto(frac) if i == j else cor_erro(frac)
            f.append(f'<rect class="celula" x="{x0 + j * lado}" y="{y0 + i * lado}" width="{lado}" height="{lado}" '
                     f'fill="{_rgb(cor)}" stroke="#d9e0e7" stroke-width="0.8"/>')
    for i in range(13):
        for j in range(13):
            n = m[i][j]
            if not n:
                continue
            x, y = x0 + j * lado + lado / 2, y0 + i * lado + lado / 2
            if i != j and n >= MIN_ERROS_PAR:
                f.append(f'<rect class="destaque" x="{x0 + j * lado + 2}" y="{y0 + i * lado + 2}" width="{lado - 4}" '
                         f'height="{lado - 4}" fill="none" stroke="{COR_DESTAQUE}" stroke-width="2.4"/>')
                pct = f"{100 * n / suportes[i]:.1f}%".replace(".", ",")
                f.append(f'<text x="{x}" y="{y - 3}" text-anchor="middle" font-size="12" font-weight="700" fill="#2a1111">{n}</text>')
                f.append(f'<text x="{x}" y="{y + 12}" text-anchor="middle" font-size="11" font-weight="700" fill="#2a1111">{pct}</text>')
            else:
                f.append(f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="13" fill="#10241a">{n}</text>')
    f.append(f'<rect x="{x0}" y="{y0}" width="{lado_matriz}" height="{lado_matriz}" fill="none" stroke="#000" stroke-width="1"/>')
    for i in range(13):
        y = y0 + i * lado + lado / 2
        f.append(f'<line x1="{x0 - 5}" y1="{y}" x2="{x0}" y2="{y}" stroke="#000"/>')
        f.append(f'<text x="{x0 - 10}" y="{y + 4.5}" text-anchor="end" font-size="12.5" fill="#111">{curtos[i]} (n={suportes[i]})</text>')
    for j in range(13):
        x = x0 + j * lado + lado / 2
        yb = y0 + lado_matriz
        f.append(f'<line x1="{x}" y1="{yb}" x2="{x}" y2="{yb + 5}" stroke="#000"/>')
        f.append(f'<text x="{x + 4}" y="{yb + 18}" text-anchor="end" font-size="12.5" fill="#111" '
                 f'transform="rotate(-52 {x + 4} {yb + 18})">{curtos[j]}</text>')
    f.append(f'<text x="{cx}" y="{y0 + lado_matriz + 188}" text-anchor="middle" font-size="15" fill="#111">Classe prevista</text>')
    f.append(f'<text x="26" y="{y0 + lado_matriz / 2}" text-anchor="middle" font-size="15" fill="#111" '
             f'transform="rotate(-90 26 {y0 + lado_matriz / 2})">Classe real</text>')
    bx = x0 + lado_matriz + 26
    f.append(f'<text x="{bx + 7}" y="{y0 - 28}" text-anchor="middle" font-size="10.5" fill="#444">acerto</text>')
    f.append(f'<text x="{bx + 27}" y="{y0 - 14}" text-anchor="middle" font-size="10.5" fill="#444">erro</text>')
    f.append(f'<rect x="{bx}" y="{y0}" width="14" height="{lado_matriz}" fill="url(#gAcerto)" stroke="#000" stroke-width="0.8"/>')
    f.append(f'<rect x="{bx + 20}" y="{y0}" width="14" height="{lado_matriz}" fill="url(#gErro)" stroke="#000" stroke-width="0.8"/>')
    for k in range(6):
        y = y0 + lado_matriz * (1 - k / 5)
        f.append(f'<line x1="{bx + 34}" y1="{y}" x2="{bx + 39}" y2="{y}" stroke="#000"/>')
        f.append(f'<text x="{bx + 43}" y="{y + 4}" font-size="12" fill="#111">{k / 5:.1f}</text>')
    f.append(f'<text x="{bx + 98}" y="{y0 + lado_matriz / 2}" text-anchor="middle" font-size="13" fill="#111" '
             f'transform="rotate(-90 {bx + 98} {y0 + lado_matriz / 2})">Fração da classe real</text>')
    yl = y0 + lado_matriz + 226
    f.append(f'<rect class="legenda" x="{cx - 250}" y="{yl - 11}" width="28" height="14" fill="none" stroke="{COR_DESTAQUE}" stroke-width="2.4"/>')
    f.append(f'<text x="{cx - 214}" y="{yl}" font-size="12.5" fill="#111">Pares com ≥ {MIN_ERROS_PAR} erros nesta amostra: contagem e % da classe real</text>')
    f.append("</svg>")
    return "\n".join(f) + "\n"


def titulos_figura(modelo: str, particao: str, imagens: int) -> tuple[str, str]:
    papel = "principal" if modelo == "Float16" else "contingência"
    conjunto = "Teste exploratório" if particao == "teste" else "Validação (usada na seleção)"
    return f"EfficientNet-Lite0 | Build final {modelo} ({papel})", f"{conjunto}: {imagens} imagens — T11.2"


def _pct(x) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def _dec(x) -> str:
    return f"{x:.2f}".replace(".", ",")


def _dec4(x) -> str:
    return f"{x:.4f}".replace(".", ",")


def tabela_matriz(m: list[list[int]], titulo_linha: str = "Real \\ Prevista", normalizada: bool = False) -> str:
    cab = f"| {titulo_linha} | " + " | ".join(str(j) for j in range(13)) + " | Suporte |"
    sep = "| ---: | " + " | ".join("---:" for _ in range(13)) + " | ---: |"
    linhas = [cab, sep]
    for i in range(13):
        suporte = sum(m[i])
        celulas = []
        for j in range(13):
            v = m[i][j]
            if not v:
                celulas.append("·")
            elif normalizada:
                celulas.append(f"**{_pct(v / suporte)}**" if i == j else _pct(v / suporte))
            else:
                celulas.append(f"**{v}**" if i == j else str(v))
        linhas.append(f"| **{i}** | " + " | ".join(celulas) + f" | {suporte} |")
    return "\n".join(linhas)


def resumo_modelo(res: dict, modelo: str, particao: str) -> dict:
    m = res["matrizes"][f"{modelo}|{particao}"]
    total = sum(sum(l) for l in m)
    acertos = sum(m[i][i] for i in range(13))
    return {"imagens": total, "acertos": acertos, "erros": total - acertos, "acuracia": acertos / total}


def relatorio(dados: dict, res: dict) -> str:
    nomes = dados["nomes"]
    m = res["matrizes"]["Float16|teste"]
    resumo = resumo_modelo(res, *REFERENCIA)
    classes = res["classes"]["Float16|teste"]
    pares = [p for p in res["pares"] if (p["modelo"], p["particao"]) == REFERENCIA]
    erros_ref = [e for e in res["erros"] if (e["modelo"], e["particao"]) == REFERENCIA]
    aceitos = sum(1 for e in erros_ref if e["decisao"] == "aceito")
    obs_erros = {e["obs_inat"] for e in erros_ref if e["obs_inat"]}
    agro = sum(1 for e in erros_ref if not e["obs_inat"])
    vis = sum(1 for e in erros_ref if e["causa_t6_3"])
    L: list[str] = []
    L.append("# T11.2 — Matriz de confusão e análise de erros\n")
    L.append("Relatório gerado por [`matriz_erros_t11_2.py`](../src/matriz_erros_t11_2.py) a partir das predições da "
             "[T11.1](Avaliacao_Final_T11_1.md) (build entregue, versão 1.0.0); artefatos em "
             "[`assets/data/matriz_erros_T11_2`](../assets/data/matriz_erros_T11_2/matrizes.json).\n")
    L.append("> **Classificação: análise exploratória.** O teste histórico já foi consultado no desenvolvimento e não é um conjunto "
             "independente ([T10.1](../assets/data/independencia_T10_1/README.md)). As matrizes descrevem o comportamento do build "
             "nesse recorte; não estimam desempenho em fotos novas de campo.\n")
    L.append("## Resumo\n")
    L.append(f"- Resultado de referência: **Float16 (principal) no teste histórico**, {resumo['imagens']} imagens, "
             f"{resumo['acertos']} acertos e **{resumo['erros']} erros** (acurácia {_dec4(resumo['acuracia'])}).")
    L.append(f"- Os {resumo['erros']} erros formam {len(pares)} pares direcionais (real → previsto); "
             f"{sum(1 for p in pares if p['erros'] >= MIN_ERROS_PAR)} deles têm pelo menos {MIN_ERROS_PAR} erros e reúnem "
             f"{sum(p['erros'] for p in pares if p['erros'] >= MIN_ERROS_PAR)} imagens.")
    L.append(f"- Os erros vêm de **{len(obs_erros)} observações do iNaturalist e {agro} fotos do AgroInsect** "
             f"(estas sem identificador de observação). {aceitos} dos {resumo['erros']} erros têm score ≥ 0,65 e, portanto, "
             "seriam mostrados ao usuário como hipótese principal.")
    L.append(f"- {sum(1 for c in classes if c['menor_desempenho'])} das 13 classes têm F1 ou recall abaixo de {_dec(F1_BAIXO)}: "
             + "; ".join(f"{c['classe'].split(' (')[0]}" for c in classes if c["menor_desempenho"]) + ".")
    inat = [e for e in erros_ref if e["obs_inat"]]
    por_obs_ref: dict[str, int] = {}
    for e in inat:
        por_obs_ref[e["obs_inat"]] = por_obs_ref.get(e["obs_inat"], 0) + 1
    varias = {o: n for o, n in por_obs_ref.items() if n > 1}
    L.append(f"- Os {len(inat)} erros em fotos do iNaturalist vêm de {len(por_obs_ref)} observações ({_dec(len(inat) / len(por_obs_ref))} por observação); "
             f"{len(varias)} observações têm mais de um erro e reúnem {sum(varias.values())} deles. Contar erros por foto superestima o número de ocorrências independentes.")
    de_grupo = {n: g for g, ids in GRUPOS.items() for n in ids}
    dentro = sum(p["erros"] for p in pares if de_grupo[p["real"]] == de_grupo[p["previsto"]])
    cruzam = [p for p in pares if de_grupo[p["real"]] != de_grupo[p["previsto"]]]
    com_vaquinha = sum(p["erros"] for p in cruzam if 0 in (p["real"], p["previsto"]))
    L.append(f"- {dentro} dos {resumo['erros']} erros ({_pct(dentro / resumo['erros'])}) ocorrem entre classes do mesmo tipo de inseto "
             f"(percevejos, lagartas, besouros ou cigarrinhas). Os outros {sum(p['erros'] for p in cruzam)} cruzam tipos, e {com_vaquinha} deles "
             "envolvem a Vaquinha, a classe com mais imagens.")
    for modelo, valores in res["correlacoes"].items():
        if modelo == "Float16":
            L.append(f"- Entre as 13 classes, o F1 tem correlação de {_dec(valores['log10_treino_vs_f1'])} com o logaritmo do número de "
                     "fotos de treino (Pearson, n = 13): classes com menos fotos tendem a ir pior, mas 13 pontos não permitem concluir causa.")
    L.append("")
    L.append("## Matriz de confusão — Float16 (principal), teste histórico\n")
    L.append("Linhas: classe real; colunas: classe prevista (índices da tabela de classes abaixo). Diagonal em negrito. "
             "É a mesma matriz da T11.1, reproduzida aqui das predições; o teste confere a igualdade.\n")
    L.append(tabela_matriz(m))
    L.append("\n![Matriz de confusão do build final Float16 no teste exploratório, com classe real nas linhas e classe prevista nas colunas](../assets/matriz_confusao_T11_2_float16_teste.svg)\n")
    L.append("### Matriz normalizada por classe real (recall na diagonal)\n")
    L.append(tabela_matriz(m, normalizada=True))
    L.append("\nCom suportes de 6 a 157 imagens, um erro move o percentual da menor classe em até 16,7 pontos; "
             "as porcentagens das classes pequenas são instáveis.\n")
    L.append("### Classes\n")
    L.append("| Índice | Classe | Suporte (teste) | Treino: fotos / grupos | Recall | Precisão | F1 | Erros (FN) | Falsos positivos (FP) |")
    L.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for c in classes:
        L.append(f"| {c['indice']} | {c['classe']} | {c['suporte']} | {c['treino_imagens']} / {c['treino_grupos']} | {_dec(c['recall'])} | "
                 f"{_dec(c['precisao'])} | {_dec(c['f1'])} | {c['fn']} | {c['fp']} |")
    L.append("\n## Principais confusões\n")
    L.append(f"Pares direcionais com pelo menos {MIN_ERROS_PAR} erros no Float16, teste histórico. "
             "\"Obs.\" conta observações distintas do iNaturalist; \"Agro\" conta fotos do AgroInsect, que não têm esse identificador. "
             "\"Aceitos\" são erros com score ≥ 0,65. \"INT8\" é quantos desses erros o INT8 repete com a mesma classe prevista; "
             "\"T6.3\" é o número de erros do mesmo par no candidato Keras FP32.\n")
    L.append("| Real → Prevista | Erros / suporte | % da classe | Obs. | Agro | Aceitos | Score médio / máx. | INT8 | T6.3 |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for p in pares:
        if p["erros"] < MIN_ERROS_PAR:
            continue
        L.append(f"| {nomes[p['real']]} → {nomes[p['previsto']]} | {p['erros']} / {p['suporte_real']} | {_pct(p['pct_da_classe'])} | "
                 f"{p['obs_inat_distintas']} | {p['agroinsect']} | {p['erros_com_score_aceito']} | "
                 f"{_dec(p['score_medio'])} / {_dec(p['score_maximo'])} | {p['repetido_no_outro_modelo']} | {p['erros_t6_3_keras_fp32']} |")
    unicos = [p for p in pares if p["erros"] < MIN_ERROS_PAR]
    L.append(f"\nOs outros {len(unicos)} pares têm um único erro cada (lista completa em `pares_confusao.csv`).\n")
    L.append("### Confusões nos dois sentidos\n")
    simetricos = {}
    for p in pares:
        chave = tuple(sorted((p["real"], p["previsto"])))
        simetricos[chave] = simetricos.get(chave, 0) + p["erros"]
    L.append("| Par | Erros somados | Sentidos |")
    L.append("| --- | ---: | --- |")
    for (a, b), n in sorted(simetricos.items(), key=lambda x: (-x[1], x[0]))[:8]:
        ab = next((p["erros"] for p in pares if (p["real"], p["previsto"]) == (a, b)), 0)
        ba = next((p["erros"] for p in pares if (p["real"], p["previsto"]) == (b, a)), 0)
        L.append(f"| {nomes[a].split(' (')[0]} ↔ {nomes[b].split(' (')[0]} | {n} | {a}→{b}: {ab}; {b}→{a}: {ba} |")
    L.append("\n## Classes com menor desempenho\n")
    L.append(f"Critério: F1 ou recall abaixo de {_dec(F1_BAIXO)} no Float16, teste histórico. Para cada classe aparecem o suporte e "
             "a cobertura de treino, o destino dos erros e quantas observações independentes estão por trás deles.\n")
    for c in classes:
        if not c["menor_desempenho"]:
            continue
        erros_c = [e for e in erros_ref if e["real"] == c["indice"]]
        por_obs: dict[str, int] = {}
        for e in erros_c:
            por_obs[e["obs_inat"] or "AgroInsect"] = por_obs.get(e["obs_inat"] or "AgroInsect", 0) + 1
        destinos = {}
        for e in erros_c:
            destinos[e["previsto"]] = destinos.get(e["previsto"], 0) + 1
        dest = "; ".join(f"{nomes[j].split(' (')[0]} ({n})" for j, n in sorted(destinos.items(), key=lambda x: (-x[1], x[0])))
        obs_txt = ", ".join(f"{o} ({n} erro{'s' if n > 1 else ''})" for o, n in sorted(por_obs.items(), key=lambda x: (-x[1], x[0])))
        L.append(f"### {c['classe']}\n")
        L.append(f"- **Desempenho:** recall {_dec(c['recall'])} ({c['vp']}/{c['suporte']}), precisão {_dec(c['precisao'])}, F1 {_dec(c['f1'])}; "
                 f"{c['fn']} falsos negativos e {c['fp']} falsos positivos.")
        L.append(f"- **Amostras:** {c['suporte']} imagens no teste (de {c['obs_inat_no_suporte']} observações do iNaturalist); "
                 f"treino com {c['treino_imagens']} fotos em {c['treino_grupos']} grupos "
                 f"({c['treino_obs_inat']} observações do iNaturalist e {c['treino_agroinsect']} fotos do AgroInsect).")
        L.append(f"- **Para onde erra:** {dest or 'sem erros'}.")
        L.append(f"- **Observações por trás dos erros:** {obs_txt or 'nenhuma'} — "
                 f"{c['fn_obs_inat_distintas']} das {c['obs_inat_no_suporte']} observações do iNaturalist da classe no teste e "
                 f"{c['fn_agroinsect']} foto(s) do AgroInsect.")
        if c["fp"]:
            L.append(f"- **Falsos positivos:** vêm sobretudo de {nomes[c['origem_principal_fp']].split(' (')[0]} ({c['origem_principal_fp_erros']}).")
        L.append("")
    L.append("## Imagens da mesma observação\n")
    multiplas = [o for o in res["observacoes"] if (o["modelo"], o["particao"]) == REFERENCIA]
    L.append("Fotos da mesma observação do iNaturalist costumam ser do mesmo indivíduo e da mesma cena, de modo que erros repetidos nelas "
             "não são ocorrências independentes. No Float16, teste histórico, " + (
                 "as observações abaixo concentram mais de um erro:\n" if multiplas else "nenhuma observação concentra mais de um erro.\n"))
    if multiplas:
        L.append("| Observação | Erros | Real | Prevista | Imagens |")
        L.append("| --- | ---: | --- | --- | --- |")
        for o in multiplas:
            reais = ", ".join(nomes[int(i)].split(" (")[0] for i in o["classes_reais"].split(";"))
            previstas = ", ".join(nomes[int(i)].split(" (")[0] for i in o["classes_previstas"].split(";"))
            L.append(f"| [{o['obs_inat']}](https://www.inaturalist.org/observations/{o['obs_inat']}) | {o['erros']} | {reais} | {previstas} | {o['ids'].replace(';', ', ')} |")
        L.append("")
    em_outras = [e for e in erros_ref if e["obs_em_outras_particoes"]]
    vinculados = [e for e in erros_ref if e["vinculo_t10_1"]]
    L.append(f"- {len(em_outras)} dos {len(erros_ref)} erros têm a observação também em outra partição"
             + (f" ({', '.join(e['image_id'] for e in em_outras)})" if em_outras else "") + ".")
    L.append(f"- {len(vinculados)} erros estão entre as imagens com vínculo registrado na T10.1"
             + (f" ({', '.join(e['image_id'] for e in vinculados)})" if vinculados else "") + ".")
    L.append(f"- {agro} dos {len(erros_ref)} erros são fotos do AgroInsect; elas não têm identificador de observação, "
             "então a independência entre elas é desconhecida (os grupos do índice vêm da separação por hash e metadados, não de indivíduo).")
    L.append(f"- {vis} dos {len(erros_ref)} erros têm anotação na revisão visual da T6.3 (`revisao_por_imagem.csv`: estágio de vida e fatores observados); "
             "a coluna correspondente está em `erros_por_imagem.csv`. As anotações são hipóteses, não validação taxonômica.\n")
    L.append("## Float16 e INT8\n")
    L.append("| Modelo | Conjunto | Imagens | Erros | Acurácia | Erros em pares com ≥ 2 erros |")
    L.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for modelo in MODELOS:
        for particao in PARTICOES:
            r = resumo_modelo(res, modelo, particao)
            em_pares = sum(p["erros"] for p in res["pares"] if (p["modelo"], p["particao"]) == (modelo, particao) and p["erros"] >= MIN_ERROS_PAR)
            L.append(f"| {modelo} | {'teste histórico' if particao == 'teste' else 'validação'} | {r['imagens']} | {r['erros']} | "
                     f"{_dec4(r['acuracia'])} | {em_pares} |")
    f16 = {e["image_id"] for e in erros_ref}
    i8 = {e["image_id"] for e in res["erros"] if (e["modelo"], e["particao"]) == ("INT8", "teste")}
    L.append(f"\nNo teste histórico, {len(f16 & i8)} imagens são erradas nos dois formatos, {len(f16 - i8)} só no Float16 e {len(i8 - f16)} só no INT8.\n")
    L.append("## Limitações\n")
    L.append("1. **Sem conjunto independente.** O teste histórico foi consultado durante o desenvolvimento; os números servem à descrição e à análise de erros, não à estimativa de generalização.")
    L.append("2. **Suporte pequeno.** 9 das 13 classes têm menos de 30 imagens no teste. Os percentuais por classe e por par são instáveis, e não há intervalo de confiança por classe.")
    L.append("3. **Observações e grupos.** Só as fotos do iNaturalist têm identificador de observação. Contar observações distintas é um limite inferior da dependência entre fotos; para o AgroInsect não há como medir.")
    L.append("4. **Causas.** As contagens mostram onde o modelo erra e quão independentes são os erros, mas não provam por que erra. A revisão visual (T6.3) é por imagem e é hipótese, não validação por especialista; esta análise não reabriu as fotos.")
    L.append("5. **Rótulos.** Os rótulos são os do índice histórico e os nomes científicos seguem como referência a validar por agrônomo.")
    L.append("6. **Runtime.** As predições vêm do TFLite com XNNPACK em Python (T11.1), equivalente ao LiteRT.js CPU/WASM nos 18 casos da T10.2; WebGPU e aparelhos físicos não foram reavaliados.\n")
    L.append("## Reprodução\n")
    L.append("```powershell\npython -m src.matriz_erros_t11_2\npython -m src.matriz_erros_t11_2 --verificar\npython tests/validar_matriz_erros_t11_2.py\n```\n")
    L.append("O comando só lê arquivos versionados (predições da T11.1, índice, classes, vínculos da T10.1 e revisão da T6.3). "
             "Saídas: `matrizes.json`, `matriz_confusao_<modelo>_<conjunto>.csv`, as quatro figuras (`assets/matriz_confusao_T11_2_float16_teste.svg` e `matriz_<modelo>_<conjunto>.svg`), `pares_confusao.csv`, "
             "`desempenho_por_classe.csv`, `erros_por_imagem.csv`, `observacoes_com_varios_erros.csv` e este relatório.")
    return "\n".join(L) + "\n"


def montar(dados: dict, res: dict) -> dict[str, str]:
    """Nome do arquivo (relativo à raiz) -> conteúdo, para escrita e verificação."""
    nomes = dados["nomes"]
    arquivos: dict[str, str] = {}
    base = SAIDA.relative_to(RAIZ).as_posix()
    cabecalho = {
        "esquema": ESQUEMA, "classificacao": "exploratoria", "generalizacao_comprovada": False,
        "entradas_sha256": dados["hashes"], "limiar_menor_desempenho": F1_BAIXO, "referencia": list(REFERENCIA),
        "classes": nomes,
    }
    json_dados = dict(cabecalho)
    json_dados["resultados"] = {
        chave: {"matriz": res["matrizes"][chave], "por_classe": res["classes"][chave]} for chave in res["matrizes"]
    }
    json_dados["correlacoes_treino_vs_desempenho"] = res["correlacoes"]
    arquivos[f"{base}/matrizes.json"] = json.dumps(json_dados, ensure_ascii=False, indent=2) + "\n"
    for chave, m in res["matrizes"].items():
        modelo, particao = chave.split("|")
        linhas = [{"real": nomes[i], **{f"prev_{j}": m[i][j] for j in range(13)}} for i in range(13)]
        arquivos[f"{base}/matriz_confusao_{modelo.lower()}_{particao}.csv"] = _csv_texto(
            ["real"] + [f"prev_{j}" for j in range(13)], linhas)
    for chave, m in res["matrizes"].items():
        modelo, particao = chave.split("|")
        figura = svg_matriz(m, nomes, *titulos_figura(modelo, particao, sum(sum(l) for l in m)))
        destino = FIGURA_REFERENCIA if (modelo, particao) == REFERENCIA else f"{base}/matriz_{modelo.lower()}_{particao}.svg"
        arquivos[destino] = figura
    campos_par = ["modelo", "particao", "real", "previsto", "erros", "suporte_real", "pct_da_classe", "pct_dos_erros",
                  "obs_inat_distintas", "agroinsect", "grupos_distintos", "erros_com_score_aceito", "score_medio",
                  "score_maximo", "repetido_no_outro_modelo", "erros_t6_3_keras_fp32", "ids"]
    linhas_par = [dict(p, ids=";".join(p["ids"])) for p in res["pares"]]
    arquivos[f"{base}/pares_confusao.csv"] = _csv_texto(campos_par, linhas_par)
    campos_cl = ["modelo", "particao", "indice", "classe", "suporte", "vp", "fn", "fp", "recall", "precisao", "f1",
                 "treino_imagens", "treino_grupos", "treino_obs_inat", "treino_agroinsect", "obs_inat_no_suporte",
                 "fn_obs_inat_distintas", "fn_agroinsect", "destino_principal", "destino_principal_erros",
                 "origem_principal_fp", "origem_principal_fp_erros", "menor_desempenho"]
    linhas_cl = []
    for chave, lista in res["classes"].items():
        modelo, particao = chave.split("|")
        linhas_cl += [dict(c, modelo=modelo, particao=particao, menor_desempenho="sim" if c["menor_desempenho"] else "nao") for c in lista]
    arquivos[f"{base}/desempenho_por_classe.csv"] = _csv_texto(campos_cl, linhas_cl)
    campos_er = ["modelo", "particao", "image_id", "caminho", "real", "previsto", "score_top1", "decisao", "origem", "obs_inat",
                 "grupo", "obs_em_outras_particoes", "vinculo_t10_1", "outro_modelo_previu", "estagio_t6_3", "fatores_t6_3", "causa_t6_3"]
    arquivos[f"{base}/erros_por_imagem.csv"] = _csv_texto(campos_er, res["erros"])
    campos_ob = ["modelo", "particao", "obs_inat", "erros", "classes_reais", "classes_previstas", "ids"]
    arquivos[f"{base}/observacoes_com_varios_erros.csv"] = _csv_texto(campos_ob, res["observacoes"])
    arquivos[DOC.relative_to(RAIZ).as_posix()] = relatorio(dados, res)
    return arquivos


def gerar(raiz: Path = RAIZ) -> list[str]:
    dados = carregar(raiz)
    arquivos = montar(dados, analisar(dados))
    for caminho, texto in arquivos.items():
        destino = raiz / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8", newline="\n")
    return sorted(arquivos)


def divergentes(raiz: Path = RAIZ) -> list[str]:
    dados = carregar(raiz)
    esperado = montar(dados, analisar(dados))
    return sorted(c for c, texto in esperado.items()
                  if not (raiz / c).exists() or _txt((raiz / c).read_text(encoding="utf-8")) != texto)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verificar", action="store_true", help="falha se algum artefato publicado estiver desatualizado")
    args = ap.parse_args()
    if args.verificar:
        ruins = divergentes()
        if ruins:
            raise SystemExit("Desatualizados (rode python -m src.matriz_erros_t11_2): " + ", ".join(ruins))
        print("Artefatos da T11.2 atualizados.")
    else:
        print(f"{len(gerar())} arquivos gerados.")


if __name__ == "__main__":
    main()
