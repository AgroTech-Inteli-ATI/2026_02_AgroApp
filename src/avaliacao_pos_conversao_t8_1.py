"""Consolida a avaliação T8.1 a partir das inferências versionadas da T7.2.

Não treina, converte ou executa modelos: recalcula métricas de teste, pareadas
por image_id, e confere a referência Keras com a avaliação original da T6.1.
Requer apenas NumPy e a biblioteca padrão.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import platform

import numpy as np

from src.avaliacao import calcular_metricas
from src.matriz_candidato_t6_2 import carregar as carregar_original

RAIZ = Path(__file__).resolve().parents[1]
PACOTE = RAIZ / "assets/modelos/candidato_T5_6_20261026"
COMPARACAO = RAIZ / "assets/modelos/comparacao_T7_2_candidato_T5_6_20261026"
ORIGINAL = RAIZ / "assets/data/avaliacao_T6_1/candidato_T5_6_20261026_keras"
INDICE = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
FP32 = RAIZ / "assets/modelos/conversao_T7_1_candidato_T5_6_20261026"
INT8 = RAIZ / "assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026"
SAIDA = RAIZ / "assets/data/avaliacao_T8_1/candidato_T5_6_20261026"
VERSOES = ("keras", "fp32", "faixa_dinamica", "float16", "int8_t7_3", "int8")
ROTULOS = {
    "keras": "Keras original (T5.6/T6.1)", "fp32": "TFLite FP32 (T7.1)",
    "faixa_dinamica": "Faixa dinâmica (T7.2)", "float16": "Float16 (T7.2)",
    "int8_t7_3": "INT8 oficial (T7.3)", "int8": "INT8 regenerado (T7.2)",
}
METRICAS = ("f1_macro", "balanced_accuracy", "acuracia")
POR_CLASSE = ("precisao", "recall", "f1")
LIMITACAO = (
    "Teste exploratório, consultado em etapas anteriores; não é avaliação final "
    "independente. Não fundamenta seleção de modelo, ajuste de pesos ou limiares. "
    "Deltas descrevem esta amostra e não comprovam equivalência estatística nem "
    "atendimento definitivo ao RNF-06. Não houve nova inferência. A revisão visual "
    "dos acertos perdidos pelo INT8 oficial está em aprofundamento/ e não "
    "determina a causa das mudanças."
)


def ler_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def ler_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def hash_arquivo(p: Path) -> str:
    return sha256(p.read_bytes()).hexdigest()


def conferir_hash(p: Path, esperado: str) -> None:
    if hash_arquivo(p) != esperado:
        raise ValueError(f"hash divergente: {p.name}")


def caminho_registrado(p: Path) -> str:
    try:
        return p.resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return str(p.resolve())


def parear(linhas: list[dict], teste: dict, campos: tuple[str, ...], nomes: list[str]) -> dict:
    """Exige cobertura exata e rótulos válidos antes de ordenar por ID."""
    ids = [r["image_id"] for r in linhas]
    if len(set(ids)) != len(ids) or set(ids) != set(teste):
        raise ValueError("previsões devem cobrir exatamente os IDs de teste, sem repetição")
    for r in linhas:
        original = teste[r["image_id"]]
        real = int(r["indice_real"])
        if (real != int(original["indice_modelo"]) or not 0 <= real < len(nomes)
                or original["nome_classe_modelo"] != nomes[real]):
            raise ValueError("rótulo real ou classe divergente do índice")
        for campo in campos:
            if not 0 <= int(r[campo]) < len(nomes):
                raise ValueError(f"previsão fora das classes: {campo}")
    return {r["image_id"]: r for r in linhas}


def carregar(comparacao=COMPARACAO, original=ORIGINAL, pacote=PACOTE,
             indice=INDICE, fp32=FP32, int8=INT8) -> dict:
    anterior = carregar_original(original, pacote, indice)
    manifesto = ler_json(pacote / "manifesto.json")
    conferir_hash(pacote / "modelo.keras", manifesto["sha256"]["modelo.keras"])
    conferir_hash(pacote / "avaliacao_validacao.json", manifesto["sha256"]["avaliacao_validacao.json"])
    conferir_hash(indice, manifesto["indice_sha256"])
    nomes = anterior["nomes"]
    if len(nomes) != 13:
        raise ValueError("esperadas as 13 classes do candidato")
    fonte = ler_json(comparacao / "comparacao.json")
    if fonte.get("esquema") != "comparacao_quantizacao_T7_2_v2":
        raise ValueError("esquema da comparação T7.2 incompatível")
    origem = fonte["origem_selecao"]
    if (fonte["modelo_keras_sha256"] != manifesto["sha256"]["modelo.keras"]
            or fonte["indice_sha256"] != hash_arquivo(indice)
            or origem["manifesto_sha256"] != hash_arquivo(pacote / "manifesto.json")
            or origem["classes_sha256"] != manifesto["sha256"]["classes.json"]
            or origem["metricas_validacao_sha256"] != manifesto["sha256"]["avaliacao_validacao.json"]
            or origem["execucao_t5_5"] != manifesto["execucao_t5_5"]):
        raise ValueError("comparação não corresponde ao candidato e ao índice selecionados")
    conferir_hash(RAIZ / "src/avaliacao.py", fonte["codigo_sha256"]["src/avaliacao.py"])

    contratos = {
        "fp32": fp32 / "contrato_tensores.json",
        "int8_t7_3": int8 / "contrato_int8.json",
        "int8": comparacao / "contrato_int8_regenerado.json",
    }
    modelos = {
        "keras": pacote / "modelo.keras", "fp32": fp32 / "modelo.tflite",
        "int8_t7_3": int8 / "modelo_int8.tflite",
        **{n: comparacao / f"modelo_{n}.tflite" for n in ("faixa_dinamica", "float16", "int8")},
    }
    classes = [{"indice": i, "nome": n} for i, n in enumerate(nomes)]
    for n in VERSOES[1:]:
        e = fonte["estrategias"][n]
        conferir_hash(modelos[n], e["sha256"])
        if modelos[n].stat().st_size != e["tamanho_bytes"]:
            raise ValueError(f"tamanho do modelo divergente: {n}")
        if n in contratos:
            c = ler_json(contratos[n])
            keras_sha = c["sha256"]["keras"] if n == "fp32" else c["modelo_keras_sha256"]
            tflite_sha = c["sha256"]["tflite"] if n == "fp32" else c["modelo_int8_sha256"]
            if (keras_sha != manifesto["sha256"]["modelo.keras"] or tflite_sha != e["sha256"]
                    or c["classes"] != classes):
                raise ValueError(f"origem ou classes do contrato divergentes: {n}")

    linhas = ler_csv(indice)
    grupos, imagens = {}, {}
    for r in linhas:
        if r["particao"] not in {"treino", "validacao", "teste"}:
            raise ValueError("partição inválida no índice")
        for campo, mapa in (("grupo_particao", grupos), ("sha256_original", imagens)):
            v = r[campo]
            if not v or v in mapa and mapa[v] != r["particao"]:
                raise ValueError("grupo ou imagem compartilhado entre partições")
            mapa[v] = r["particao"]
    teste = {r["image_id"]: r for r in linhas if r["particao"] == "teste"}
    if not teste:
        raise ValueError("partição de teste vazia")
    novas = ler_csv(comparacao / "predicoes.csv")
    indice_por_id = {r["image_id"]: r for r in linhas}
    chaves = [(r["particao"], r["image_id"]) for r in novas]
    if len(set(chaves)) != len(chaves):
        raise ValueError("previsão repetida na comparação T7.2")
    for r in novas:
        if (r["particao"] not in {"validacao", "teste"}
                or r["image_id"] not in indice_por_id
                or indice_por_id[r["image_id"]]["particao"] != r["particao"]):
            raise ValueError("previsão T7.2 não pertence à partição declarada")
    novas = parear([r for r in novas if r["particao"] == "teste"], teste,
                   tuple(f"previsto_{n}" for n in VERSOES), nomes)
    antigas = parear(ler_csv(original / "predicoes_teste.csv"), teste, ("indice_previsto",), nomes)
    ids = sorted(teste)
    if any(novas[i]["previsto_keras"] != antigas[i]["indice_previsto"] for i in ids):
        raise ValueError("previsões Keras da T7.2 divergem da referência original T6.1")
    rotulos = np.array([int(teste[i]["indice_modelo"]) for i in ids])
    previstos = {n: np.array([int(novas[i][f"previsto_{n}"]) for i in ids]) for n in VERSOES}
    metricas = {n: calcular_metricas(rotulos, p, len(nomes), nomes) for n, p in previstos.items()}
    for n, m in metricas.items():
        if m != fonte["metricas"]["teste"][n]["metricas"]:
            raise ValueError(f"métricas recalculadas divergem da T7.2: {n}")
    if metricas["keras"] != anterior["metricas"]:
        raise ValueError("métricas Keras divergem da avaliação original T6.1")

    fontes = [indice, pacote / "manifesto.json", pacote / "classes.json", pacote / "avaliacao_validacao.json",
              original / "proveniencia_avaliacao.json", original / "metricas_teste.json",
              original / "predicoes_teste.csv", comparacao / "comparacao.json", comparacao / "predicoes.csv",
              *contratos.values(), *modelos.values()]
    proveniencia = {
        "esquema": "avaliacao_pos_conversao_T8_1_v1", "particao": "teste",
        "tipo": "consolidação das inferências versionadas da T7.2, conferidas com a T6.1",
        "nova_inferencia": False, "treinamento_realizado": False, "teste_independente": False,
        "referencia_principal": "keras", "referencia_conversao": "fp32",
        "total_amostras": len(ids), "classes": classes, "image_ids": ids,
        "fontes_sha256": {caminho_registrado(p): hash_arquivo(p) for p in fontes},
        "codigo_sha256": {f"src/{n}": hash_arquivo(RAIZ / "src" / n) for n in
                           ("avaliacao_pos_conversao_t8_1.py", "avaliacao.py", "matriz_candidato_t6_2.py")},
        "ambiente_inferencia_T7_2": fonte["ambiente"],
        "protocolo_inferencia": "T7.2: T4.1 sem augmentation; Keras batch 32; TFLite batch 1, CPU com 4 threads e delegates padrão",
        "ambiente_consolidacao": {"python": platform.python_version(), "numpy": np.__version__,
                                  "sistema": platform.platform()},
        "limite_interpretacao": LIMITACAO,
    }
    return {"ids": ids, "indice": teste, "nomes": nomes, "rotulos": rotulos,
            "previstos": previstos, "metricas": metricas, "proveniencia": proveniencia}


def comparar(dados: dict) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    gerais, classes, predicoes, mudancas = [], [], [], []
    ms, ps, y = dados["metricas"], dados["previstos"], dados["rotulos"]
    for n in VERSOES:
        m = ms[n]
        linha = {"versao": n, "rotulo": ROTULOS[n], "total_amostras": m["total_amostras"],
                 "classes_avaliadas": m["classes_avaliadas"], **{k: m[k] for k in METRICAS}}
        for ref in ("keras", "fp32"):
            linha.update({f"delta_{k}_vs_{ref}_pp": 100 * (m[k] - ms[ref][k]) for k in METRICAS})
            linha.update({f"divergencias_top1_vs_{ref}": int(np.sum(ps[n] != ps[ref])),
                          f"acertos_perdidos_vs_{ref}": int(np.sum((ps[ref] == y) & (ps[n] != y))),
                          f"acertos_ganhos_vs_{ref}": int(np.sum((ps[ref] != y) & (ps[n] == y)))})
        gerais.append(linha)
        for i, c in enumerate(m["por_classe"]):
            linha = {"versao": n, "indice": i, "classe": c["nome"], "suporte": c["suporte"],
                     "status": c["status"], **{k: c[k] for k in POR_CLASSE}}
            for ref in ("keras", "fp32"):
                for k in POR_CLASSE:
                    v, r = c[k], ms[ref]["por_classe"][i][k]
                    linha[f"delta_{k}_vs_{ref}_pp"] = None if v is None or r is None else 100 * (v - r)
            classes.append(linha)
    for pos, image_id in enumerate(dados["ids"]):
        original = dados["indice"][image_id]
        real, ref = int(y[pos]), int(ps["keras"][pos])
        predicoes.append({"image_id": image_id, "indice_real": real,
                          "caminho_relativo": original["caminho_relativo"],
                          "sha256_original": original["sha256_original"],
                          **{f"previsto_{n}": int(ps[n][pos]) for n in VERSOES}})
        for n in VERSOES[1:]:
            p = int(ps[n][pos])
            if p != ref:
                mudancas.append({"image_id": image_id, "versao": n, "indice_real": real,
                                 "previsto_keras": ref, "previsto_convertido": p,
                                 "tipo": "acerto_perdido" if ref == real else "acerto_ganho" if p == real else "erro_alterado"})
    return gerais, classes, predicoes, mudancas


def numero(v: float, sinal=False) -> str:
    return (f"{v:+.4f}" if sinal else f"{v:.4f}").replace(".", ",")


def relatorio(dados: dict, gerais: list, classes: list) -> str:
    texto = ["# Avaliação pós-conversão — T8.1", "",
             f"**{len(dados['ids'])} imagens de teste; {len(dados['nomes'])} classes; referência principal: Keras original.**", "",
             "Métricas recalculadas a partir das previsões salvas da T7.2, pareadas por image_id e conferidas com a T6.1. "
             "Nenhum modelo foi executado novamente nesta etapa. Valores abaixo arredondados a quatro casas; deltas calculados antes do arredondamento.", "",
             "## Métricas gerais", "",
             "| Versão | F1 macro | Balanced accuracy | Acurácia | Δ F1 vs Keras (p.p.) | Δ balanced accuracy vs Keras (p.p.) | Δ acurácia vs Keras (p.p.) | Acertos perdidos / ganhos vs Keras |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in gerais:
        texto.append(f"| {r['rotulo']} | " + " | ".join(numero(r[k]) for k in METRICAS)
                     + " | " + " | ".join(numero(r[f'delta_{k}_vs_keras_pp'], True) for k in METRICAS)
                     + f" | {r['acertos_perdidos_vs_keras']} / {r['acertos_ganhos_vs_keras']} |")
    texto += ["", "## Perdas por classe", "",
              "Todas as classes, inclusive as sem queda, estão em comparacao_por_classe.csv. "
              "Para cada conversão, a tabela destaca a maior queda de F1 e a maior queda de recall frente ao Keras; empates são preservados.", "",
              "| Versão | Métrica | Classe | Suporte | Keras | Convertido | Δ (p.p.) |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for n in VERSOES[1:]:
        linhas = [r for r in classes if r["versao"] == n]
        for k in ("f1", "recall"):
            validas = [r for r in linhas if r[f"delta_{k}_vs_keras_pp"] is not None]
            pior = min((r[f"delta_{k}_vs_keras_pp"] for r in validas), default=0)
            if pior >= 0:
                texto.append(f"| {ROTULOS[n]} | {k} | Sem queda observada | — | — | — | — |")
            else:
                for r in validas:
                    if r[f"delta_{k}_vs_keras_pp"] == pior:
                        ref = dados["metricas"]["keras"]["por_classe"][r["indice"]][k]
                        texto.append(f"| {ROTULOS[n]} | {k} | {r['classe']} | {r['suporte']} | "
                                     f"{numero(ref)} | {numero(r[k])} | {numero(pior, True)} |")
    texto += ["", "## Protocolo e interpretação", "",
              "- A referência principal é o checkpoint selecionado na T5.6, avaliado na T6.1. As previsões Keras da T7.2 coincidem por ID com as da T6.1.",
              "- O CSV geral e o CSV por classe incluem deltas contra Keras e contra TFLite FP32. Deltas negativos indicam perda. Balanced accuracy é a média dos recalls e não é F1 macro.",
              "- O protocolo de inferência herdado da T7.2 usa T4.1, sem augmentation, ponderação ou limiar de confiança. Não há mudança de pesos, calibração ou pré-processamento nesta consolidação.",
              "- As matrizes mantêm a ordem das classes do candidato: linhas reais, colunas previstas. Os suportes são iguais entre as versões.",
              "- mudancas_por_imagem.csv lista toda troca de argmax frente ao Keras, distinguindo acerto perdido, acerto ganho e erro alterado. Não descreve alterações de scores que preservam o argmax.",
              "- Melhor média global pode coexistir com perdas por classe. Suportes pequenos limitam a interpretação; a revisão visual dos sete acertos perdidos pelo INT8 oficial está em aprofundamento/ e não determina a causa das mudanças.",
              "- INT8 oficial T7.3 e INT8 regenerado T7.2 são artefatos distintos. Esta análise não substitui o oficial pelo modelo de maior F1 no teste.",
              "- Esta etapa não calcula novos testes estatísticos. McNemar e os ICs da T7.2 têm FP32 como referência e não são usados como prova de equivalência ao Keras ou entre os dois INT8.",
              "", LIMITACAO, "",
              "Tamanho e latência estão na seção 7.2 de docs/Projeto.md; benchmark no aparelho pertence à T8.2 e seleção à T8.3.", "",
              "## Artefatos", "",
              "metricas_gerais.csv; comparacao_por_classe.csv; predicoes_teste.csv; mudancas_por_imagem.csv; matrizes/<versao>.csv; proveniencia.json.", "",
              "## Reprodução", "", "```bash",
              "python -m src.avaliacao_pos_conversao_t8_1 --saida runs/reproducao_T8_1",
              "python tests/validar_avaliacao_pos_conversao_t8_1.py", "```", ""]
    return "\n".join(texto)


def csv_texto(linhas: list[dict], campos=None) -> str:
    s = io.StringIO(newline="")
    w = csv.DictWriter(s, fieldnames=campos or list(linhas[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(linhas)
    return s.getvalue()


def executar(saida=SAIDA, **fontes) -> dict:
    if saida.exists():
        raise ValueError("saída já existe; escolha outra pasta para preservar os resultados")
    dados = carregar(**fontes)
    gerais, classes, predicoes, mudancas = comparar(dados)
    conteudos = {
        "metricas_gerais.csv": csv_texto(gerais), "comparacao_por_classe.csv": csv_texto(classes),
        "predicoes_teste.csv": csv_texto(predicoes),
        "mudancas_por_imagem.csv": csv_texto(mudancas, ["image_id", "versao", "indice_real", "previsto_keras", "previsto_convertido", "tipo"]),
        "relatorio_avaliacao.md": relatorio(dados, gerais, classes),
    }
    for n in VERSOES:
        matriz = dados["metricas"][n]["matriz_confusao"]
        linhas = [{"indice_real": i, "classe_real": nome,
                   **{f"previsto_{j}": v for j, v in enumerate(matriz[i])}}
                  for i, nome in enumerate(dados["nomes"])]
        conteudos[f"matrizes/{n}.csv"] = csv_texto(linhas)
    proveniencia = dados["proveniencia"]
    proveniencia["data_consolidacao_utc"] = datetime.now(timezone.utc).isoformat()
    proveniencia["artefatos_sha256"] = {n: sha256(t.encode("utf-8")).hexdigest() for n, t in conteudos.items()}
    conteudos["proveniencia.json"] = json.dumps(proveniencia, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    saida.mkdir(parents=True, exist_ok=False)
    for nome, texto in conteudos.items():
        p = saida / nome
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8", newline="")
    return dados


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for nome, padrao in (("saida", SAIDA), ("comparacao", COMPARACAO), ("original", ORIGINAL),
                         ("pacote", PACOTE), ("indice", INDICE), ("fp32", FP32), ("int8", INT8)):
        p.add_argument("--" + nome, type=Path, default=padrao)
    dados = executar(**vars(p.parse_args()))
    print(f"T8.1: {len(dados['ids'])} imagens; métricas e matrizes de {len(VERSOES)} versões conferidas.")


if __name__ == "__main__":
    main()
