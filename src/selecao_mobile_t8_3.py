"""Seleção da versão do modelo convertido para o aplicativo móvel (T8.3).

Lê somente evidências já versionadas (T7.2, T8.2 e política T6.5); não treina,
converte nem executa modelos. A avaliação pós-conversão (T8.1) é opcional: se
estiver na árvore, seus números são conferidos contra os da T7.2; se não, o
registro informa que ela ainda não foi integrada e a decisão permanece a mesma.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import csv
import json

RAIZ = Path(__file__).resolve().parents[1]
T7_2 = "assets/modelos/comparacao_T7_2_candidato_T5_6_20261026"
T8_2 = "assets/data/benchmark_T8_2/oficiais_20261106/resumo.csv"
T6_5 = "assets/data/politica_T6_5/parametros.json"
T8_1 = "assets/data/avaliacao_T8_1/candidato_T5_6_20261026"
PACOTE_T5_6 = "assets/modelos/candidato_T5_6_20261026"
SAIDA = "assets/data/selecao_T8_3"

VERSOES = ("fp32", "faixa_dinamica", "float16", "int8_t7_3", "int8")
# O benchmark T8.2 chama o INT8 regenerado de int8_t7_2; a T7.2 e a T8.1 o chamam de int8.
NOME_T8_2 = {"int8": "int8_t7_2"}
ROTULOS = {
    "fp32": "FP32 (T7.1)",
    "faixa_dinamica": "Faixa dinâmica (T7.2)",
    "float16": "Float16 (T7.2)",
    "int8_t7_3": "INT8 oficial (T7.3)",
    "int8": "INT8 regenerado (T7.2)",
}
LIMITE_BYTES = 8_000_000      # RNF-01
LIMITE_P95_MS = 300.0         # RNF-04 (indicativo local; o aparelho ainda não foi medido)
LIMITE_PERDA_PP = -2.0        # RNF-06
TOLERANCIA_T8_1 = 1e-6
DATA = "2026-11-07"


def hash_arquivo(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8-sig"))


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def carregar(raiz: Path) -> dict:
    d = raiz / T7_2
    comparacao = ler_json(d / "comparacao.json")
    return {
        "comparacao": comparacao,
        "tabela": {r["estrategia"]: r for r in ler_csv(d / "tabela_comparativa.csv")},
        "por_classe": ler_csv(d / "metricas_por_classe.csv"),
        "predicoes": ler_csv(d / "predicoes.csv"),
        "latencia": {r["versao"]: r for r in ler_csv(raiz / T8_2)},
        "politica": ler_json(raiz / T6_5),
    }


def conferir_arquivos(raiz: Path, fontes: dict) -> dict:
    """Confere bytes e SHA-256 de cada versão em T7.2 e T8.2; devolve caminhos e hashes."""
    arquivos = {}
    for v in VERSOES:
        t72 = fontes["comparacao"]["estrategias"][v]
        t82 = fontes["latencia"][NOME_T8_2.get(v, v)]
        caminho = raiz / t82["modelo"]
        if not caminho.is_file():
            raise ValueError(f"arquivo ausente: {t82['modelo']}")
        h = hash_arquivo(caminho)
        if not (h == t72["sha256"] == t82["sha256"]):
            raise ValueError(f"hash divergente entre arquivo, T7.2 e T8.2: {v}")
        if not (caminho.stat().st_size == int(t72["tamanho_bytes"]) == int(t82["bytes"])):
            raise ValueError(f"tamanho divergente: {v}")
        arquivos[v] = {"arquivo": t82["modelo"], "sha256": h, "bytes": caminho.stat().st_size}
    return arquivos


def pior_queda_f1(por_classe: list[dict], particao: str, versao: str) -> dict:
    """Maior queda de F1 por classe em relação ao FP32 (0 se nenhuma classe piora)."""
    base = {int(r["indice"]): float(r["f1"]) for r in por_classe
            if r["particao"] == particao and r["estrategia"] == "fp32"}
    piores = []
    for r in por_classe:
        if r["particao"] == particao and r["estrategia"] == versao:
            i = int(r["indice"])
            piores.append((float(r["f1"]) - base[i], i, r["classe"], int(r["suporte"])))
    delta, indice, classe, suporte = min(piores)
    return {"delta_f1": round(min(delta, 0.0), 6), "indice": indice, "classe": classe,
            "suporte": suporte, "classes_com_queda": sum(1 for p in piores if p[0] < -0.0005)}


def politica_top1(predicoes: list[dict], versao: str, limiar: float, particao: str) -> dict:
    linhas = [r for r in predicoes if r["particao"] == particao]
    aceitas = [r for r in linhas if float(r["score_" + versao]) >= limiar]
    acertos = sum(r["previsto_" + versao] == r["indice_real"] for r in aceitas)
    return {"imagens": len(linhas), "aceitas": len(aceitas),
            "cobertura": round(len(aceitas) / len(linhas), 6),
            "acerto_nas_aceitas": round(acertos / len(aceitas), 6)}


def avaliar_versao(v: str, fontes: dict, arquivos: dict) -> dict:
    t = fontes["tabela"][v]
    rnf = fontes["comparacao"]["rnf"][v]
    rnf06 = rnf.get("RNF-06_validacao") or {"delta_pp": 0.0, "ic95_inferior_pp": 0.0, "atende_ic95": True}
    lat = fontes["latencia"][NOME_T8_2.get(v, v)]
    limiar = fontes["politica"]["limiar_confianca"]
    p95 = float(lat["p95_ms"])
    criterios = {
        "rnf01_ate_8mb": arquivos[v]["bytes"] <= LIMITE_BYTES,
        "rnf09_sem_delegate": bool(rnf["RNF-09"]["atende"]),
        "rnf04_p95_local_abaixo_300ms": p95 < LIMITE_P95_MS,
        "rnf06_estimativa_pontual": float(rnf06["delta_pp"]) >= LIMITE_PERDA_PP,
    }
    return {
        "versao": v,
        "rotulo": ROTULOS[v],
        **arquivos[v],
        "f1_macro_validacao": float(t["f1_macro_val"]),
        "delta_f1_validacao": float(t["delta_f1_vs_fp32_val"]),
        "delta_acuracia_macro_pp_validacao": float(rnf06["delta_pp"]),
        "ic95_inferior_acuracia_macro_pp_validacao": float(rnf06["ic95_inferior_pp"]),
        "rnf06_demonstrado_pelo_ic95": bool(rnf06["atende_ic95"]),
        "pior_classe_validacao": pior_queda_f1(fontes["por_classe"], "validacao", v),
        "f1_macro_teste_exploratorio": float(t["f1_macro_teste"]),
        "pior_classe_teste_exploratorio": pior_queda_f1(fontes["por_classe"], "teste", v),
        "erro_abs_max_scores_vs_fp32_validacao": float(t["erro_abs_max_vs_fp32_val"]),
        "politica_t6_5_top1_validacao": politica_top1(fontes["predicoes"], v, limiar, "validacao"),
        "p95_ms_local_t8_2": round(p95, 4),
        "mediana_ms_local_t8_2": round(float(lat["p50_ms"]), 4),
        "entrada": t["entrada"],
        "saida": t["saida"],
        "criterios_eliminatorios": criterios,
        "elegivel": all(criterios.values()),
    }


def chave_ordem(r: dict):
    """Ordem dos critérios da task: acurácia (RNF-06), desempenho por classe, latência, tamanho."""
    return (not r["rnf06_demonstrado_pelo_ic95"], -r["pior_classe_validacao"]["delta_f1"],
            r["p95_ms_local_t8_2"], r["bytes"])


def conferir_t8_1(raiz: Path, fontes: dict) -> dict:
    """Confere a T8.1 contra a T7.2 quando ela existir; não é requisito da decisão."""
    pasta = raiz / T8_1
    if not (pasta / "metricas_gerais.csv").is_file():
        return {"status": "nao_integrada",
                "nota": "T8.1 fora da árvore; os números vêm das previsões da T7.2, que ela também usa."}
    erros = []
    gerais = {r["versao"]: r for r in ler_csv(pasta / "metricas_gerais.csv")}
    for v in VERSOES:
        t = fontes["tabela"][v]
        for campo, ref in (("f1_macro", "f1_macro_teste"), ("balanced_accuracy", "balanced_accuracy_teste"),
                           ("acuracia", "acuracia_teste")):
            if abs(float(gerais[v][campo]) - float(t[ref])) > TOLERANCIA_T8_1:
                erros.append(f"{v}.{campo}")
    por_classe = {(r["versao"], int(r["indice"])): float(r["f1"]) for r in ler_csv(pasta / "comparacao_por_classe.csv")}
    for r in fontes["por_classe"]:
        if r["particao"] == "teste" and r["estrategia"] in VERSOES:
            if abs(por_classe[(r["estrategia"], int(r["indice"]))] - float(r["f1"])) > TOLERANCIA_T8_1:
                erros.append(f"{r['estrategia']}.f1.classe{r['indice']}")
    return {"status": "conferida" if not erros else "divergente", "divergencias": erros,
            "nota": "T8.1 comparada com a T7.2 (teste, 473 imagens)."}


def decidir(raiz: Path = RAIZ) -> dict:
    fontes = carregar(raiz)
    arquivos = conferir_arquivos(raiz, fontes)
    tabela = [avaliar_versao(v, fontes, arquivos) for v in VERSOES]
    elegiveis = sorted((r for r in tabela if r["elegivel"]), key=chave_ordem)
    if len(elegiveis) < 2:
        raise ValueError("é necessária ao menos uma alternativa elegível além da escolhida")
    escolhido = elegiveis[0]
    # A contingência é o INT8 entregue pela T7.3 (contrato e calibração documentados). O INT8 regenerado
    # só verifica reprodutibilidade; a diferença entre os dois está dentro do IC e não decide nada.
    contingencia = next(r for r in elegiveis[1:] if r["versao"] == "int8_t7_3")
    pacote = raiz / PACOTE_T5_6 / "modelo_int8.tflite"
    return {
        "esquema": "selecao_mobile_T8_3_v1",
        "data": DATA,
        "status": "concluida_versao_oficial_mvp",
        "criterio": ("Eliminatórios: RNF-01 (≤ 8 MB), RNF-09, RNF-04 indicativo local (p95 < 300 ms) e RNF-06 "
                     "pontual. Entre as elegíveis, na ordem da task: (1) RNF-06 demonstrado pelo IC 95% da "
                     "validação; (2) menor queda de F1 em uma classe; (3) menor p95 local; (4) menor tamanho."),
        "particao_de_decisao": "validacao",
        "teste": "exploratório e já consultado em etapas anteriores; não participou da escolha",
        "escolhido": {k: escolhido[k] for k in ("versao", "rotulo", "arquivo", "sha256", "bytes", "entrada", "saida")},
        "contingencia": {
            **{k: contingencia[k] for k in ("versao", "rotulo", "arquivo", "sha256", "bytes", "entrada", "saida")},
            "quando": "Se, no aparelho de referência, o escolhido violar RNF-04 (p95 > 300 ms) ou RNF-07 (memória)."},
        "ordem_de_elegiveis": [r["versao"] for r in elegiveis],
        "eliminados": {r["versao"]: [k for k, ok in r["criterios_eliminatorios"].items() if not ok]
                       for r in tabela if not r["elegivel"]},
        "tabela": tabela,
        "pacote_t5_6": {
            "arquivo": f"{PACOTE_T5_6}/modelo_int8.tflite", "sha256": hash_arquivo(pacote),
            "e_o_int8_da_t7_3": hash_arquivo(pacote) == arquivos["int8_t7_3"]["sha256"],
            "nota": "O pacote T5.6 não é alterado; o artefato de embarque desta decisão é o indicado em `escolhido`."},
        "t8_1": conferir_t8_1(raiz, fontes),
        "limites": [
            "Latência medida em CPU x86 de desenvolvimento; RNF-04, RNF-03 e RNF-07 exigem o aparelho de referência.",
            "RNF-06 em conjunto independente continua pendente; o teste atual já foi consultado.",
            "A política T6.5 foi recontada só no top-1; top-3 e limiar no arquivo embarcado exigem nova inferência.",
            "Aprovação do parceiro pendente.",
        ],
    }


def fmt(x, casas=4):
    return f"{x:.{casas}f}".replace(".", ",")


def tabela_csv(decisao: dict) -> str:
    colunas = ["versao", "rotulo", "bytes", "elegivel", "f1_macro_validacao", "delta_f1_validacao",
               "delta_acuracia_macro_pp_validacao", "ic95_inferior_acuracia_macro_pp_validacao",
               "rnf06_demonstrado_pelo_ic95", "pior_queda_f1_classe", "pior_classe_indice",
               "p95_ms_local_t8_2", "cobertura_t6_5", "acerto_aceitas_t6_5", "eliminado_por"]
    linhas = [";".join(colunas)]
    for r in decisao["tabela"]:
        p = r["politica_t6_5_top1_validacao"]
        linhas.append(";".join(str(x) for x in (
            r["versao"], r["rotulo"], r["bytes"], r["elegivel"], r["f1_macro_validacao"], r["delta_f1_validacao"],
            r["delta_acuracia_macro_pp_validacao"], r["ic95_inferior_acuracia_macro_pp_validacao"],
            r["rnf06_demonstrado_pelo_ic95"], r["pior_classe_validacao"]["delta_f1"],
            r["pior_classe_validacao"]["indice"], r["p95_ms_local_t8_2"], p["cobertura"],
            p["acerto_nas_aceitas"], "|".join(decisao["eliminados"].get(r["versao"], [])))))
    return "\n".join(linhas) + "\n"


def relatorio(decisao: dict) -> str:
    e = decisao["escolhido"]
    c = decisao["contingencia"]
    linhas = [
        "# Seleção do modelo para o aplicativo móvel (T8.3)", "",
        f"**Escolhido:** {e['rotulo']} — `{e['arquivo']}` ({format(e['bytes'], ',').replace(',', '.')} bytes; SHA-256 `{e['sha256']}`).",
        f"**Contingência:** {c['rotulo']} — `{c['arquivo']}`. {c['quando']}", "",
        "| Versão | MB | Elegível | F1 macro (val.) | IC95 inf. Δ acur. macro (p.p.) | Pior queda de F1 por classe | p95 local (ms) |",
        "| --- | ---: | :---: | ---: | ---: | --- | ---: |",
    ]
    for r in decisao["tabela"]:
        q = r["pior_classe_validacao"]
        linhas.append(f"| {r['rotulo']} | {fmt(r['bytes'] / 1e6, 2)} | {'sim' if r['elegivel'] else 'não'} | "
                      f"{fmt(r['f1_macro_validacao'])} | {fmt(r['ic95_inferior_acuracia_macro_pp_validacao'], 2)} | "
                      f"{fmt(q['delta_f1'] * 100, 1)} p.p. (classe {q['indice']}, n={q['suporte']}) | "
                      f"{fmt(r['p95_ms_local_t8_2'], 2)} |")
    linhas += ["", f"T8.1: {decisao['t8_1']['status']}. {decisao['t8_1']['nota']}", ""]
    return "\n".join(linhas)


def gerar(raiz: Path = RAIZ, saida: Path | None = None) -> dict:
    decisao = decidir(raiz)
    saida = saida or raiz / SAIDA
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "decisao.json").write_text(
        json.dumps(decisao, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (saida / "tabela_decisao.csv").write_text(tabela_csv(decisao), encoding="utf-8")
    (saida / "relatorio.md").write_text(relatorio(decisao), encoding="utf-8")
    return decisao


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", type=Path, default=None, help=f"pasta de saída (padrão: {SAIDA})")
    d = gerar(saida=ap.parse_args().saida)
    print(f"Escolhido: {d['escolhido']['rotulo']}; contingência: {d['contingencia']['rotulo']}; "
          f"T8.1: {d['t8_1']['status']}")
