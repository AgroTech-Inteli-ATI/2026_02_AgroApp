"""Avaliação do limiar de confiança e dos casos inadequados (T11.3).

Testa a política da T6.5 (top-1 >= 0,65 mostra três hipóteses; abaixo disso, resultado inconclusivo) em dois
conjuntos de cenários:

1. **Conjunto histórico** (teste e validação), com as predições do build final publicadas na T11.1: previsões
   corretas e incorretas, aceitas e inconclusivas, erros com score alto, relação entre score e acerto e
   sensibilidade ao limiar. Não recalibra nada.
2. **Imagens fora do recorte e inadequadas**, medidas no próprio aplicativo (LiteRT.js no Chromium, com o modelo
   do build): controles sintéticos sem inseto, fotos reais sem o inseto (recortes do fundo das imagens do
   AgroInsect), a mesma foto degradada (desfoque, escuro, superexposição, cinza, ruído, JPEG, sujeito pequeno)
   e, se houver, fotos reais enviadas pela equipe.

O score exibido é o softmax do modelo, **não calibrado**: não é probabilidade de acerto. Os resultados são
exploratórios (o teste histórico já foi consultado; T10.1).

python -m src.limiar_t11_3 preparar --raiz-imagens "C:/.../agroapp - imagens" --saida-imagens "C:/tmp/t11_3"
    # gera as imagens dos cenários e o manifesto (a inferência é feita pelo spec Playwright limiar-t11-3.spec.ts)
python -m src.limiar_t11_3 analisar     # lê o manifesto e as inferências do navegador e gera artefatos e relatório
python -m src.limiar_t11_3 --verificar  # falha se algum artefato publicado estiver desatualizado
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import random
import statistics

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "assets/data"
POLITICA = DADOS / "politica_T6_5/parametros.json"
PREDICOES = DADOS / "avaliacao_final_T11_1/predicoes.csv"
CLASSES = RAIZ / "assets/modelos/candidato_T5_6_20261026/classes.json"
INDICE = DADOS / "treino_T5_2/indice_dataset.csv"
SAIDA = DADOS / "limiar_T11_3"
MANIFESTO = SAIDA / "manifesto.json"
INFERENCIAS = SAIDA / "inferencias_web.json"
DOC = RAIZ / "docs/Avaliacao_Limiar_T11_3.md"
ESQUEMA = "limiar_T11_3_v1"
MODELOS = ("Float16", "INT8")
PARTICOES = ("teste", "validacao")
REFERENCIA = ("Float16", "teste")
SEMENTE = 42
LIMIARES = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
FAIXAS_SCORE = ((0.0, 0.50), (0.50, 0.65), (0.65, 0.80), (0.80, 0.90), (0.90, 0.95), (0.95, 0.99), (0.99, 1.0001))
ALTO = 0.90  # "score elevado": erros com score a partir daqui são listados
CENARIOS = {
    "sintetico": "Controles sintéticos sem inseto",
    "fundo": "Fotos reais sem o inseto (recorte do fundo)",
    "foto_real_extra": "Fotos reais fora do recorte (enviadas pela equipe)",
    "original": "Foto original (referência dos pares)",
    "desfoque": "Desfoque forte",
    "escuro": "Foto escura",
    "superexposto": "Foto superexposta",
    "cinza": "Escala de cinza",
    "ruido": "Ruído forte",
    "jpeg_q10": "Compressão JPEG q=10",
    "sujeito_pequeno": "Sujeito pequeno e distante",
}
DEGRADACOES = ("desfoque", "escuro", "superexposto", "cinza", "ruido", "jpeg_q10", "sujeito_pequeno")
FORA_DO_RECORTE = ("sintetico", "fundo", "foto_real_extra")


def _csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def _sha(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%".replace(".", ",")


def _dec(x: float, n: int = 2) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def limiar_da_politica() -> float:
    politica = _json(POLITICA)
    if politica["regra_limiar"] != "top1_maior_ou_igual" or politica["abaixo_do_limiar"]["indica_classe"]:
        raise ValueError("política de confiança incompatível com esta avaliação")
    return float(politica["limiar_confianca"])


def decisao(top1: float, limiar: float) -> str:
    """Regra do app: top-1 maior ou igual ao limiar é aceito; abaixo, inconclusivo."""
    return "aceito" if top1 >= limiar else "inconclusivo"


# ---------- parte 1: conjunto histórico ----------
def carregar_historico() -> dict:
    nomes = [c["nome"] for c in _json(CLASSES)]
    linhas = []
    for l in _csv(PREDICOES):
        scores = [float(l[f"score_{i}"]) for i in range(13)]
        ordem = sorted(range(13), key=lambda i: (-scores[i], i))
        linhas.append({"id": l["image_id"], "modelo": l["modelo"], "particao": l["particao"], "real": int(l["indice_real"]),
                       "previsto": ordem[0], "score": scores[ordem[0]], "top3": ordem[:3], "decisao_t11_1": l["decisao"]})
        if linhas[-1]["previsto"] != int(l["indice_previsto"]):
            raise ValueError(f"classe prevista diverge do maior score: {l['image_id']}")
    origem = {r["image_id"]: ("iNaturalist" if "/inat" in r["caminho_relativo"] or r["caminho_relativo"].rsplit("/", 1)[-1].startswith("inat")
                              else "AgroInsect") for r in _csv(INDICE)}
    return {"nomes": nomes, "linhas": linhas, "origem": origem}


def quadrantes(linhas: list[dict], limiar: float) -> dict:
    q = {"acerto_aceito": 0, "acerto_inconclusivo": 0, "erro_aceito": 0, "erro_inconclusivo": 0}
    for l in linhas:
        acerto = l["real"] == l["previsto"]
        q[("acerto" if acerto else "erro") + "_" + ("aceito" if l["score"] >= limiar else "inconclusivo")] += 1
    q["total"] = len(linhas)
    aceitos = q["acerto_aceito"] + q["erro_aceito"]
    q["aceitos"] = aceitos
    q["cobertura"] = aceitos / len(linhas)
    q["acuracia_aceitos"] = q["acerto_aceito"] / aceitos if aceitos else None
    q["acuracia_sem_limiar"] = (q["acerto_aceito"] + q["acerto_inconclusivo"]) / len(linhas)
    inconclusivos = q["acerto_inconclusivo"] + q["erro_inconclusivo"]
    q["inconclusivos"] = inconclusivos
    q["inconclusivos_que_eram_erro"] = q["erro_inconclusivo"] / inconclusivos if inconclusivos else None
    return q


def curva(linhas: list[dict]) -> list[dict]:
    saida = []
    for limiar in LIMIARES:
        q = quadrantes(linhas, limiar)
        saida.append({"limiar": limiar, "cobertura": q["cobertura"], "aceitos": q["aceitos"],
                      "acuracia_aceitos": q["acuracia_aceitos"], "erros_aceitos": q["erro_aceito"],
                      "acertos_inconclusivos": q["acerto_inconclusivo"]})
    return saida


def faixas(linhas: list[dict]) -> list[dict]:
    saida = []
    for ini, fim in FAIXAS_SCORE:
        grupo = [l for l in linhas if ini <= l["score"] < fim]
        acertos = sum(1 for l in grupo if l["real"] == l["previsto"])
        saida.append({"de": ini, "ate": min(fim, 1.0), "imagens": len(grupo), "acertos": acertos, "erros": len(grupo) - acertos,
                      "score_medio": statistics.fmean(l["score"] for l in grupo) if grupo else None,
                      "acerto": acertos / len(grupo) if grupo else None})
    return saida


def calibracao(linhas: list[dict], largura: float = 0.1) -> dict:
    """Erro de calibração esperado (ECE) e tabela de confiabilidade em faixas de 0,1 do score top-1."""
    n = len(linhas)
    tabela, ece = [], 0.0
    for k in range(10):
        ini, fim = k * largura, (k + 1) * largura + (1e-9 if k == 9 else 0)
        grupo = [l for l in linhas if ini <= l["score"] < fim]
        if not grupo:
            continue
        acerto = sum(1 for l in grupo if l["real"] == l["previsto"]) / len(grupo)
        medio = statistics.fmean(l["score"] for l in grupo)
        ece += len(grupo) / n * abs(acerto - medio)
        tabela.append({"de": round(ini, 1), "ate": round(min(fim, 1.0), 1), "imagens": len(grupo), "score_medio": medio, "acerto": acerto})
    superestima = sum(1 for t in tabela if t["score_medio"] > t["acerto"] + 0.05)
    return {"ece": ece, "faixas": tabela, "faixas_com_score_acima_do_acerto": superestima}


def erros_altos(linhas: list[dict], limiar: float) -> dict:
    erros = [l for l in linhas if l["real"] != l["previsto"]]
    aceitos = [e for e in erros if e["score"] >= limiar]
    altos = sorted((e for e in erros if e["score"] >= ALTO), key=lambda e: (-e["score"], e["id"]))
    return {
        "erros": len(erros), "aceitos": len(aceitos), "altos": len(altos), "limite_alto": ALTO,
        "real_no_top3_entre_aceitos": sum(1 for e in aceitos if e["real"] in e["top3"]),
        "lista": [{"id": e["id"], "real": e["real"], "previsto": e["previsto"], "score": e["score"], "real_no_top3": e["real"] in e["top3"]}
                  for e in altos],
    }


def por_classe(linhas: list[dict], nomes: list[str], limiar: float) -> list[dict]:
    saida = []
    for i in range(13):
        reais = [l for l in linhas if l["real"] == i]
        aceitos = [l for l in reais if l["score"] >= limiar]
        mostrados = [l for l in linhas if l["previsto"] == i and l["score"] >= limiar]
        certos = sum(1 for l in mostrados if l["real"] == i)
        saida.append({
            "indice": i, "classe": nomes[i], "suporte": len(reais), "aceitos": len(aceitos),
            "cobertura": len(aceitos) / len(reais) if reais else None,
            "acertos_aceitos": sum(1 for l in aceitos if l["previsto"] == i),
            "recall_no_limiar": sum(1 for l in aceitos if l["previsto"] == i) / len(reais) if reais else None,
            "mostrada_como_principal": len(mostrados), "precisao_quando_mostrada": certos / len(mostrados) if mostrados else None,
        })
    return saida


def analisar_historico(h: dict, limiar: float) -> dict:
    res: dict = {}
    for modelo in MODELOS:
        for particao in PARTICOES:
            linhas = [l for l in h["linhas"] if (l["modelo"], l["particao"]) == (modelo, particao)]
            res[f"{modelo}|{particao}"] = {
                "quadrantes": quadrantes(linhas, limiar), "curva": curva(linhas), "faixas": faixas(linhas),
                "calibracao": calibracao(linhas), "erros_altos": erros_altos(linhas, limiar),
                "por_classe": por_classe(linhas, h["nomes"], limiar),
            }
    ref = [l for l in h["linhas"] if (l["modelo"], l["particao"]) == REFERENCIA]
    # Erros aceitos por origem da foto (iNaturalist x AgroInsect), no teste de referência.
    por_origem: dict[str, dict] = {}
    for l in ref:
        o = h["origem"][l["id"]]
        d = por_origem.setdefault(o, {"imagens": 0, "aceitos": 0, "erros_aceitos": 0})
        d["imagens"] += 1
        if l["score"] >= limiar:
            d["aceitos"] += 1
            d["erros_aceitos"] += l["real"] != l["previsto"]
    res["origem_teste_referencia"] = por_origem
    return res


# ---------- parte 2: imagens fora do recorte e inadequadas ----------
def carregar_web() -> tuple[dict, dict]:
    manifesto = _json(MANIFESTO)
    inferencias = _json(INFERENCIAS)
    if inferencias["manifesto_sha256"] != _sha(MANIFESTO):
        raise ValueError("as inferências não correspondem ao manifesto atual")
    return manifesto, inferencias


def linha_web(item: dict, resultado: dict, limiar: float) -> dict:
    scores = resultado["scores"]
    ordem = sorted(range(13), key=lambda i: (-scores[i], i))
    return {"id": item["id"], "cenario": item["cenario"], "pai": item.get("pai"), "classe_real": item.get("classe_real"),
            "previsto": ordem[0], "score": scores[ordem[0]], "top3": ordem[:3],
            "decisao": decisao(scores[ordem[0]], limiar), "ui": resultado["ui_decisao"]}


def analisar_web(manifesto: dict, inferencias: dict, nomes: list[str], limiar: float) -> dict:
    por_id = {i["id"]: i for i in manifesto["imagens"]}
    saida: dict = {"formatos": {}, "consistencia_ui": {}}
    for formato, resultados in inferencias["formatos"].items():
        linhas = [linha_web(por_id[r["id"]], r, limiar) for r in resultados]
        por_cenario: dict[str, dict] = {}
        for cenario in CENARIOS:
            grupo = [l for l in linhas if l["cenario"] == cenario]
            if not grupo:
                continue
            aceitos = [l for l in grupo if l["decisao"] == "aceito"]
            scores = sorted(l["score"] for l in grupo)
            destinos: dict[int, int] = {}
            for l in aceitos:
                destinos[l["previsto"]] = destinos.get(l["previsto"], 0) + 1
            d = {"imagens": len(grupo), "aceitos": len(aceitos), "pct_aceitos": len(aceitos) / len(grupo),
                 "score_mediano": statistics.median(scores), "score_maximo": scores[-1], "score_minimo": scores[0],
                 "score_p90": scores[min(len(scores) - 1, math.ceil(0.9 * len(scores)) - 1)],
                 "classes_mostradas": {str(k): v for k, v in sorted(destinos.items(), key=lambda x: (-x[1], x[0]))}}
            if grupo[0]["classe_real"] is not None and cenario in ("original",) + DEGRADACOES:
                certos = sum(1 for l in aceitos if l["previsto"] == l["classe_real"])
                d.update({"acertos_aceitos": certos, "acuracia_aceitos": certos / len(aceitos) if aceitos else None,
                          "acertos_sem_limiar": sum(1 for l in grupo if l["previsto"] == l["classe_real"])})
            por_cenario[cenario] = d
        # pares original x degradação (mesma foto)
        originais = {l["id"]: l for l in linhas if l["cenario"] == "original"}
        pares: dict[str, dict] = {}
        for cenario in DEGRADACOES:
            membros = [l for l in linhas if l["cenario"] == cenario and l["pai"] in originais]
            if not membros:
                continue
            mudou = sum(1 for l in membros if l["decisao"] != originais[l["pai"]]["decisao"])
            perdeu = sum(1 for l in membros if originais[l["pai"]]["decisao"] == "aceito" and l["decisao"] == "inconclusivo")
            ganhou = sum(1 for l in membros if originais[l["pai"]]["decisao"] == "inconclusivo" and l["decisao"] == "aceito")
            classe_mudou = sum(1 for l in membros if l["previsto"] != originais[l["pai"]]["previsto"])
            errado_aceito = sum(1 for l in membros if l["decisao"] == "aceito" and l["previsto"] != l["classe_real"])
            errado_novo = sum(1 for l in membros if l["decisao"] == "aceito" and l["previsto"] != l["classe_real"]
                              and not (originais[l["pai"]]["decisao"] == "aceito" and originais[l["pai"]]["previsto"] != l["classe_real"]))
            pares[cenario] = {"pares": len(membros), "decisao_mudou": mudou, "aceito_para_inconclusivo": perdeu,
                              "inconclusivo_para_aceito": ganhou, "classe_prevista_mudou": classe_mudou,
                              "erros_aceitos": errado_aceito, "erros_aceitos_novos": errado_novo,
                              "queda_media_do_score": statistics.fmean(originais[l["pai"]]["score"] - l["score"] for l in membros)}
        saida["formatos"][formato] = {"por_cenario": por_cenario, "pares_degradacao": pares, "linhas": linhas}
        saida["consistencia_ui"][formato] = {"imagens": len(linhas), "divergentes": [l["id"] for l in linhas if l["ui"] != l["decisao"]]}
    return saida


def analisar(raiz: Path = RAIZ) -> dict:
    limiar = limiar_da_politica()
    h = carregar_historico()
    manifesto, inferencias = carregar_web()
    return {"limiar": limiar, "historico": analisar_historico(h, limiar), "web": analisar_web(manifesto, inferencias, h["nomes"], limiar),
            "nomes": h["nomes"], "manifesto": manifesto, "inferencias_meta": {k: v for k, v in inferencias.items() if k != "formatos"}}


# ---------- artefatos ----------
def _csv_texto(campos: list[str], linhas: list[dict]) -> str:
    buffer = io.StringIO()
    escritor = csv.writer(buffer, lineterminator="\n")
    escritor.writerow(campos)
    for l in linhas:
        escritor.writerow(["" if l.get(c) is None else (f"{l[c]:.6f}" if isinstance(l[c], float) else l[c]) for c in campos])
    return buffer.getvalue()


def _nome(nomes: list[str], i: int) -> str:
    return nomes[i].split(" (")[0]


def relatorio(res: dict) -> str:
    nomes, limiar = res["nomes"], res["limiar"]
    h = res["historico"]
    ref = h["Float16|teste"]
    q = ref["quadrantes"]
    ea = ref["erros_altos"]
    web = res["web"]["formatos"]
    fp = web.get("Float16")
    L: list[str] = []
    L.append("# T11.3 — Avaliação do limiar de confiança e casos inadequados\n")
    L.append("Relatório gerado por [`limiar_t11_3.py`](../src/limiar_t11_3.py) a partir das predições da [T11.1](Avaliacao_Final_T11_1.md) "
             "e das inferências feitas no próprio aplicativo (LiteRT.js no Chromium) com o modelo do build; artefatos em "
             "[`assets/data/limiar_T11_3`](../assets/data/limiar_T11_3/resultados.json).\n")
    L.append("> **Classificação: exploratória.** O teste histórico já foi consultado no desenvolvimento e não é independente "
             "([T10.1](../assets/data/independencia_T10_1/README.md)). Esta avaliação **não recalibra** o limiar e **não apresenta nenhum score "
             "como probabilidade de acerto**: o valor mostrado é o softmax do modelo, sem calibração.\n")
    L.append("## Resumo\n")
    L.append(f"- Regra testada: top-1 **≥ {_dec(limiar)}** (igualdade aceita) mostra as três hipóteses; abaixo disso, resultado inconclusivo, sem indicar classe.")
    L.append(f"- Float16 no teste histórico ({q['total']} imagens): {q['aceitos']} aceitas ({_pct(q['cobertura'])}), com acerto de "
             f"{_pct(q['acuracia_aceitos'])} entre elas; **{q['erro_aceito']} erros foram aceitos** e {q['acerto_inconclusivo']} acertos ficaram inconclusivos.")
    L.append(f"- **Erros com score alto:** {ea['altos']} dos {ea['erros']} erros têm score ≥ {_dec(ALTO)}; a classe real aparece entre as três hipóteses em "
             f"{ea['real_no_top3_entre_aceitos']} dos {ea['aceitos']} erros aceitos.")
    cal = ref["calibracao"]
    L.append(f"- **O score não é probabilidade calibrada:** o erro de calibração esperado (ECE) do Float16 no teste é {_dec(cal['ece'], 3)}, e "
             f"{cal['faixas_com_score_acima_do_acerto']} das {len(cal['faixas'])} faixas de score têm score médio acima do acerto observado.")
    if fp:
        fora = [c for c in FORA_DO_RECORTE if c in fp["por_cenario"]]
        total = sum(fp["por_cenario"][c]["imagens"] for c in fora)
        aceitos = sum(fp["por_cenario"][c]["aceitos"] for c in fora)
        L.append(f"- **Fora do recorte:** das {total} imagens sem o inseto ou sem relação com as 13 classes, o app **aceitou e indicou uma classe em {aceitos}** "
                 f"({_pct(aceitos / total)}) com o Float16. O limiar não funciona como detector de imagem fora do escopo.")
        con = res["web"]["consistencia_ui"]["Float16"]
        L.append(f"- **Interface:** em {con['imagens']} imagens, a tela mostrou as hipóteses exatamente quando o score atingiu o limiar "
                 f"({'nenhuma divergência' if not con['divergentes'] else str(len(con['divergentes'])) + ' divergências'}).")
    L.append("")
    L.append("## Cenários do conjunto histórico\n")
    L.append("Cada imagem cai em um de quatro cenários, conforme o top-1 esteja certo e atinja ou não o limiar. Float16 e INT8, teste histórico e validação "
             f"(a validação participou da seleção do checkpoint e do limiar; é otimista).\n")
    L.append("| Modelo | Conjunto | Imagens | Acerto aceito | Acerto inconclusivo | Erro aceito | Erro inconclusivo | Cobertura | Acerto entre aceitas |")
    L.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for modelo in MODELOS:
        for particao in PARTICOES:
            x = h[f"{modelo}|{particao}"]["quadrantes"]
            L.append(f"| {modelo} | {'teste histórico' if particao == 'teste' else 'validação'} | {x['total']} | {x['acerto_aceito']} | {x['acerto_inconclusivo']} | "
                     f"{x['erro_aceito']} | {x['erro_inconclusivo']} | {_pct(x['cobertura'])} | {_pct(x['acuracia_aceitos'])} |")
    L.append("\n- **Acerto aceito:** o caso desejado; o usuário vê a classe certa entre as hipóteses.")
    L.append("- **Acerto inconclusivo:** o modelo acertou, mas o score ficou abaixo do limiar; o usuário recebe a mensagem de resultado inconclusivo (custo de cobertura).")
    L.append("- **Erro aceito:** o caso mais sensível; o app mostra uma classe errada como hipótese principal, e o score pode ser alto.")
    L.append(f"- **Erro inconclusivo:** o limiar evitou mostrar uma classe errada. No Float16 do teste, {_pct(q['inconclusivos_que_eram_erro'])} das imagens inconclusivas eram erros.\n")
    L.append("### Quando o app mostra uma classe, quanto ela acerta (Float16, teste)\n")
    L.append("| Classe mostrada como principal | Vezes mostrada | Acerto quando mostrada | Cobertura da classe real | Recall no limiar |")
    L.append("| --- | ---: | ---: | ---: | ---: |")
    for c in ref["por_classe"]:
        L.append(f"| {c['indice']} · {_nome(nomes, c['indice'])} | {c['mostrada_como_principal']} | "
                 f"{_pct(c['precisao_quando_mostrada']) if c['precisao_quando_mostrada'] is not None else '—'} | "
                 f"{_pct(c['cobertura']) if c['cobertura'] is not None else '—'} | {_pct(c['recall_no_limiar']) if c['recall_no_limiar'] is not None else '—'} |")
    L.append("\nO acerto quando a classe é mostrada varia bastante entre classes com o mesmo limiar: um limiar único não dá a mesma garantia a todas.\n")
    L.append("## Erros com score elevado\n")
    L.append(f"No Float16, teste histórico, {ea['altos']} erros têm score ≥ {_dec(ALTO)} e seriam apresentados com aparência de alta confiança. "
             "Faixas de score do top-1:\n")
    L.append("| Faixa de score | Imagens | Acertos | Erros | Acerto | Score médio |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for f in ref["faixas"]:
        if not f["imagens"]:
            continue
        fim = "1,00" if f["ate"] >= 1.0 else _dec(f["ate"])
        L.append(f"| {_dec(f['de'])} a {fim} | {f['imagens']} | {f['acertos']} | {f['erros']} | {_pct(f['acerto'])} | {_dec(f['score_medio'])} |")
    L.append("\nErros com score ≥ 0,90 (Float16, teste):\n")
    L.append("| Imagem | Real → Prevista | Score | Classe real entre as 3 hipóteses |")
    L.append("| --- | --- | ---: | --- |")
    for e in ea["lista"]:
        L.append(f"| {e['id']} | {_nome(nomes, e['real'])} → {_nome(nomes, e['previsto'])} | {_dec(e['score'], 3)} | {'sim' if e['real_no_top3'] else 'não'} |")
    L.append("\n## O score não é probabilidade de acerto\n")
    L.append("Se o score fosse uma probabilidade calibrada, as imagens com score médio próximo de 0,9 acertariam cerca de 90% das vezes. A tabela compara o score "
             "médio de cada faixa com o acerto observado (Float16, teste histórico):\n")
    L.append("| Faixa | Imagens | Score médio | Acerto observado | Diferença |")
    L.append("| --- | ---: | ---: | ---: | ---: |")
    for t in cal["faixas"]:
        L.append(f"| {_dec(t['de'])} a {_dec(t['ate'])} | {t['imagens']} | {_dec(t['score_medio'])} | {_pct(t['acerto'])} | {_dec(t['acerto'] - t['score_medio'], 2)} |")
    vcal = h["Float16|validacao"]["calibracao"]
    L.append(f"\nECE: {_dec(cal['ece'], 3)} no teste e {_dec(vcal['ece'], 3)} na validação (Float16). O texto do aplicativo e os documentos devem chamar o valor de "
             "*score do modelo*, nunca de chance ou probabilidade de acerto; a política T6.5 já determina isso.\n")
    L.append("## Sensibilidade ao limiar\n")
    L.append("Não é uma recalibração: o teste histórico já foi consultado. Serve para mostrar o que o limiar de 0,65 troca entre cobertura e erros aceitos "
             "(Float16).\n")
    L.append("| Limiar | Teste: cobertura | Teste: acerto entre aceitas | Teste: erros aceitos | Validação: cobertura | Validação: acerto entre aceitas | Validação: erros aceitos |")
    L.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    cv = h["Float16|validacao"]["curva"]
    for a, b in zip(ref["curva"], cv):
        marca = "**" if abs(a["limiar"] - limiar) < 1e-9 else ""
        L.append(f"| {marca}{_dec(a['limiar'])}{marca} | {_pct(a['cobertura'])} | {_pct(a['acuracia_aceitos'])} | {a['erros_aceitos']} | "
                 f"{_pct(b['cobertura'])} | {_pct(b['acuracia_aceitos'])} | {b['erros_aceitos']} |")
    L.append("\nSubir o limiar reduz erros aceitos, mas também aceita menos fotos; mesmo em 0,95 ainda há erros aceitos. A meta de 0,90 de acerto entre aceitas "
             "foi definida na validação (T6.5).\n")
    if web:
        L.append("## Imagens fora do recorte e inadequadas (inferência no aplicativo)\n")
        meta = res["inferencias_meta"]
        L.append(f"As imagens foram enviadas ao aplicativo real (Playwright, {meta.get('navegador', 'Chromium')}, {meta.get('runtime', 'LiteRT.js')}), "
                 f"com o modelo do build e a política de {_dec(limiar)}; o resultado foi lido da saída do worker e da tela. "
                 "O manifesto (`manifesto.json`) lista cada imagem, o cenário, a origem e o hash do arquivo.\n")
        for formato, f in web.items():
            L.append(f"### {formato}\n")
            L.append("| Cenário | Imagens | Aceitas (app indica classe) | Score mediano | Score máximo | Classe mais mostrada |")
            L.append("| --- | ---: | ---: | ---: | ---: | --- |")
            for cenario, d in f["por_cenario"].items():
                top = next(iter(d["classes_mostradas"].items()), None)
                topo = f"{_nome(nomes, int(top[0]))} ({top[1]})" if top else "—"
                L.append(f"| {CENARIOS[cenario]} | {d['imagens']} | {d['aceitos']} ({_pct(d['pct_aceitos'])}) | {_dec(d['score_mediano'])} | {_dec(d['score_maximo'])} | {topo} |")
            L.append("")
            aceitas_fora = sorted((l for l in f["linhas"] if l["cenario"] in FORA_DO_RECORTE and l["decisao"] == "aceito"),
                                  key=lambda l: (-l["score"], l["id"]))
            if aceitas_fora:
                L.append(f"Imagens fora do recorte que o {formato} **aceitou** (as {min(10, len(aceitas_fora))} de maior score, de {len(aceitas_fora)}):\n")
                L.append("| Imagem | Cenário | Classe indicada | Score |")
                L.append("| --- | --- | --- | ---: |")
                for l in aceitas_fora[:10]:
                    L.append(f"| {l['id']} | {CENARIOS[l['cenario']]} | {_nome(nomes, l['previsto'])} | {_dec(l['score'], 3)} |")
                L.append("")
            if f["pares_degradacao"]:
                L.append(f"**Mesma foto, degradada** (comparação com a foto original, {formato}):\n")
                L.append("| Degradação | Pares | Decisão mudou | Aceito → inconclusivo | Inconclusivo → aceito | Classe mudou | Erros aceitos | Erros aceitos novos | Queda média do score |")
                L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
                for cenario, p in f["pares_degradacao"].items():
                    L.append(f"| {CENARIOS[cenario]} | {p['pares']} | {p['decisao_mudou']} | {p['aceito_para_inconclusivo']} | {p['inconclusivo_para_aceito']} | "
                             f"{p['classe_prevista_mudou']} | {p['erros_aceitos']} | {p['erros_aceitos_novos']} | {_dec(p['queda_media_do_score'])} |")
                orig = f["por_cenario"].get("original")
                if orig and orig.get("acuracia_aceitos") is not None:
                    L.append(f"\nAs fotos originais dos pares: {orig['aceitos']}/{orig['imagens']} aceitas, com {_pct(orig['acuracia_aceitos'])} de acerto entre elas.\n")
            con = res["web"]["consistencia_ui"][formato]
            L.append(f"**Consistência da interface:** {con['imagens']} imagens; a tela mostrou as hipóteses quando e somente quando o top-1 atingiu o limiar "
                     f"({'0 divergências' if not con['divergentes'] else str(len(con['divergentes'])) + ' divergências: ' + ', '.join(con['divergentes'])}).\n")
    L.append("## Limitações das previsões\n")
    L.append("1. **Sem conjunto independente.** O teste histórico já foi consultado; os números descrevem o build nesse recorte e não estimam o desempenho em fotos novas de campo.")
    L.append("2. **O limiar não detecta imagem fora do escopo.** O modelo escolhe sempre uma das 13 classes; fotos sem inseto, de outras pragas, de doenças ou de plantas sadias "
             "podem receber score alto. As medições acima usam controles sintéticos e recortes de fundo, não doenças, outras culturas ou insetos de outras espécies; "
             "para esses casos reais, incluir fotos da equipe (opção `--pasta-extras`) e repetir a avaliação.")
    L.append("3. **Score ≠ probabilidade.** É um softmax não calibrado (T6.5); o limiar de 0,65 foi escolhido na validação em Keras FP32 e não foi recalibrado para o Float16 nem para o INT8.")
    L.append("4. **Classes pequenas.** Suportes de 6 a 157 imagens tornam instáveis os percentuais por classe; não há intervalo de confiança por classe.")
    L.append("5. **Fotos do AgroInsect e do iNaturalist.** As degradações e os recortes usam fotos do AgroInsect (com caixas YOLO); a origem iNaturalist não foi reprocessada no navegador. "
             "Os recortes de fundo não foram revisados um a um: são regiões fora das caixas anotadas, e um recorte pode conter um inseto pequeno não anotado "
             "(por exemplo, há uma formiga minúscula em `fundo_IMG_01779`). A degradação sintética não substitui fotos reais com problemas de captura no campo.")
    L.append("6. **Runtime.** O Chromium desktop com LiteRT.js CPU/WASM representa o app, mas não WebGPU, Safari, Firefox ou aparelhos físicos.\n")
    L.append("## Reprodução\n")
    L.append("```powershell\n"
             "python -m src.limiar_t11_3 preparar --raiz-imagens \"C:\\caminho\\agroapp - imagens\" --saida-imagens \"C:\\tmp\\t11_3\" [--pasta-extras \"C:\\caminho\\fotos\"]\n"
             "cd frontend\n"
             "$env:T11_3_IMAGENS = \"C:\\tmp\\t11_3\"; npx playwright test tests/limiar-t11-3.spec.ts --project=chromium\n"
             "cd ..\n"
             "python -m src.limiar_t11_3 analisar\n"
             "python -m src.limiar_t11_3 --verificar\n"
             "python tests/validar_limiar_t11_3.py\n```\n")
    L.append("O passo do navegador grava `assets/data/limiar_T11_3/inferencias_web.json` (scores das 13 classes e decisão exibida por imagem, para o Float16 e o INT8). "
             "A análise e os testes usam apenas arquivos versionados, sem modelo, imagens ou rede.")
    return "\n".join(L) + "\n"


def montar(res: dict) -> dict[str, str]:
    base = SAIDA.relative_to(RAIZ).as_posix()
    nomes = res["nomes"]
    h = res["historico"]
    arquivos: dict[str, str] = {}
    saida_json = {"esquema": ESQUEMA, "classificacao": "exploratoria", "generalizacao_comprovada": False, "limiar": res["limiar"],
                  "score": "softmax_nao_calibrado", "entradas_sha256": {"predicoes_t11_1": _sha(PREDICOES), "politica": _sha(POLITICA),
                                                                       "manifesto": _sha(MANIFESTO), "inferencias_web": _sha(INFERENCIAS)},
                  "historico": {k: {kk: vv for kk, vv in v.items()} for k, v in h.items() if "|" in k},
                  "origem_teste_referencia": h["origem_teste_referencia"],
                  "web": {f: {"por_cenario": d["por_cenario"], "pares_degradacao": d["pares_degradacao"]} for f, d in res["web"]["formatos"].items()},
                  "consistencia_ui": res["web"]["consistencia_ui"], "inferencias": res["inferencias_meta"]}
    arquivos[f"{base}/resultados.json"] = json.dumps(saida_json, ensure_ascii=False, indent=2) + "\n"
    linhas = []
    for chave, v in h.items():
        if "|" not in chave:
            continue
        modelo, particao = chave.split("|")
        for c in v["curva"]:
            linhas.append(dict(c, modelo=modelo, particao=particao))
    arquivos[f"{base}/curva_limiar.csv"] = _csv_texto(
        ["modelo", "particao", "limiar", "cobertura", "aceitos", "acuracia_aceitos", "erros_aceitos", "acertos_inconclusivos"], linhas)
    linhas = []
    for chave, v in h.items():
        if "|" not in chave:
            continue
        modelo, particao = chave.split("|")
        linhas += [dict(f, modelo=modelo, particao=particao) for f in v["faixas"]]
    arquivos[f"{base}/faixas_de_score.csv"] = _csv_texto(["modelo", "particao", "de", "ate", "imagens", "acertos", "erros", "score_medio", "acerto"], linhas)
    linhas = []
    for chave, v in h.items():
        if "|" not in chave:
            continue
        modelo, particao = chave.split("|")
        linhas += [dict(t, modelo=modelo, particao=particao, ece=v["calibracao"]["ece"]) for t in v["calibracao"]["faixas"]]
    arquivos[f"{base}/calibracao.csv"] = _csv_texto(["modelo", "particao", "de", "ate", "imagens", "score_medio", "acerto", "ece"], linhas)
    linhas = []
    for chave, v in h.items():
        if "|" not in chave:
            continue
        modelo, particao = chave.split("|")
        linhas += [dict(c, modelo=modelo, particao=particao) for c in v["por_classe"]]
    arquivos[f"{base}/cenarios_por_classe.csv"] = _csv_texto(
        ["modelo", "particao", "indice", "classe", "suporte", "aceitos", "cobertura", "acertos_aceitos", "recall_no_limiar",
         "mostrada_como_principal", "precisao_quando_mostrada"], linhas)
    linhas = []
    for chave, v in h.items():
        if "|" not in chave:
            continue
        modelo, particao = chave.split("|")
        linhas += [dict(e, modelo=modelo, particao=particao, real_no_top3="sim" if e["real_no_top3"] else "nao")
                   for e in v["erros_altos"]["lista"]]
    arquivos[f"{base}/erros_com_score_alto.csv"] = _csv_texto(["modelo", "particao", "id", "real", "previsto", "score", "real_no_top3"], linhas)
    linhas = []
    for formato, d in res["web"]["formatos"].items():
        for l in d["linhas"]:
            linhas.append({"formato": formato, "id": l["id"], "cenario": l["cenario"], "pai": l["pai"], "classe_real": l["classe_real"],
                           "previsto": l["previsto"], "score_top1": l["score"], "decisao": l["decisao"], "ui": l["ui"],
                           "top3": ";".join(str(i) for i in l["top3"])})
    arquivos[f"{base}/decisoes_web.csv"] = _csv_texto(
        ["formato", "id", "cenario", "pai", "classe_real", "previsto", "score_top1", "decisao", "ui", "top3"], linhas)
    arquivos[DOC.relative_to(RAIZ).as_posix()] = relatorio(res)
    return arquivos


def gerar() -> list[str]:
    arquivos = montar(analisar())
    for caminho, texto in arquivos.items():
        destino = RAIZ / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8", newline="\n")
    return sorted(arquivos)


def divergentes() -> list[str]:
    esperado = montar(analisar())
    return sorted(c for c, t in esperado.items()
                  if not (RAIZ / c).exists() or (RAIZ / c).read_text(encoding="utf-8").replace("\r\n", "\n") != t)


# ---------- preparação das imagens ----------
def _caixas(rotulo: Path) -> list[tuple[float, float, float, float]]:
    caixas = []
    if rotulo.exists():
        for linha in rotulo.read_text().splitlines():
            p = linha.split()
            if len(p) >= 5:
                cx, cy, w, h = (float(x) for x in p[1:5])
                caixas.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    return caixas


def regiao_sem_inseto(caixas: list[tuple], minimo: float = 0.30):
    """Maior faixa retangular (esquerda, direita, topo ou base) que não toca nenhuma caixa, em coordenadas normalizadas.
    Sem nenhuma caixa anotada não há como saber onde está o inseto, então não devolve região."""
    if not caixas:
        return None
    candidatas = []
    esq = min((c[0] for c in caixas), default=1.0)
    dire = max((c[2] for c in caixas), default=0.0)
    topo = min((c[1] for c in caixas), default=1.0)
    base = max((c[3] for c in caixas), default=0.0)
    candidatas.append((0.0, 0.0, esq, 1.0))
    candidatas.append((dire, 0.0, 1.0, 1.0))
    candidatas.append((0.0, 0.0, 1.0, topo))
    candidatas.append((0.0, base, 1.0, 1.0))
    validas = [c for c in candidatas if (c[2] - c[0]) >= minimo and (c[3] - c[1]) >= minimo]
    return max(validas, key=lambda c: (c[2] - c[0]) * (c[3] - c[1])) if validas else None


def gerar_sinteticos(saida: Path) -> list[dict]:
    from PIL import Image, ImageDraw
    rng = random.Random(SEMENTE)
    itens = []
    tam = 640

    def salvar(nome: str, img, parametro: str):
        caminho = saida / "sintetico" / f"{nome}.png"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        img.save(caminho)
        itens.append({"id": f"sintetico_{nome}", "cenario": "sintetico", "arquivo": f"sintetico/{nome}.png", "parametro": parametro})

    for nome, cor in [("preto", (0, 0, 0)), ("branco", (255, 255, 255)), ("cinza", (128, 128, 128)), ("verde_folha", (60, 140, 60)),
                      ("marrom_solo", (110, 80, 50)), ("amarelo", (230, 200, 30)), ("vermelho", (200, 30, 30)), ("azul_ceu", (100, 150, 220))]:
        salvar(nome, Image.new("RGB", (tam, tam), cor), f"cor {cor}")
    grad_h = Image.new("RGB", (tam, tam))
    grad_v = Image.new("RGB", (tam, tam))
    for i in range(tam):
        f = i / (tam - 1)
        cor_h = (int(60 + 50 * f), int(140 - 60 * f), int(60 - 10 * f))
        grad_h.paste(cor_h, (i, 0, i + 1, tam))
        grad_v.paste((int(255 * f),) * 3, (0, i, tam, i + 1))
    salvar("gradiente_verde_marrom", grad_h, "horizontal")
    salvar("gradiente_cinza", grad_v, "vertical")
    ruido = Image.frombytes("RGB", (tam, tam), rng.randbytes(tam * tam * 3))
    salvar("ruido_colorido", ruido, f"semente {SEMENTE}")
    cinza = rng.randbytes(tam * tam)
    salvar("ruido_cinza", Image.frombytes("L", (tam, tam), cinza).convert("RGB"), f"semente {SEMENTE}")
    xadrez = Image.new("RGB", (tam, tam), (255, 255, 255))
    d = ImageDraw.Draw(xadrez)
    for y in range(0, tam, 32):
        for x in range(0, tam, 32):
            if (x // 32 + y // 32) % 2 == 0:
                d.rectangle([x, y, x + 31, y + 31], fill=(0, 0, 0))
    salvar("xadrez", xadrez, "casas de 32 px")
    listras = Image.new("RGB", (tam, tam), (240, 240, 240))
    d = ImageDraw.Draw(listras)
    for k in range(-tam, tam * 2, 40):
        d.line([(k, 0), (k - tam, tam)], fill=(30, 90, 30), width=16)
    salvar("listras_diagonais", listras, "largura 16 px")
    circulos = Image.new("RGB", (tam, tam), (255, 255, 255))
    d = ImageDraw.Draw(circulos)
    for r in range(300, 0, -30):
        d.ellipse([tam / 2 - r, tam / 2 - r, tam / 2 + r, tam / 2 + r], fill=(int(255 - r * 0.6), int(120 + r * 0.3), 60))
    salvar("circulos_concentricos", circulos, "raios de 30 em 30")
    texto = Image.new("RGB", (tam, tam), (250, 250, 245))
    d = ImageDraw.Draw(texto)
    for k in range(18):
        d.text((24, 20 + k * 34), "Texto de exemplo sem inseto " * 2, fill=(20, 20, 20))
    salvar("pagina_de_texto", texto, "fonte padrão")
    mosaico = Image.new("RGB", (tam, tam))
    d = ImageDraw.Draw(mosaico)
    for y in range(0, tam, 64):
        for x in range(0, tam, 64):
            d.rectangle([x, y, x + 63, y + 63], fill=tuple(rng.randrange(256) for _ in range(3)))
    salvar("mosaico_aleatorio", mosaico, "blocos de 64 px")
    return itens


def preparar(raiz_imagens: Path, saida: Path, pasta_extras: Path | None = None, n_fundo: int = 60, n_degradadas: int = 40) -> dict:
    """Gera as imagens dos cenários em `saida` e o manifesto. Determinístico (semente 42)."""
    import numpy as np
    from PIL import Image, ImageFilter, ImageOps
    rng = random.Random(SEMENTE)
    nrng = np.random.default_rng(SEMENTE)
    indice = [r for r in _csv(INDICE) if r["particao"] == "teste" and "/dataset/image/" in "/" + r["caminho_relativo"]]
    indice.sort(key=lambda r: r["image_id"])
    saida.mkdir(parents=True, exist_ok=True)
    imagens = gerar_sinteticos(saida)

    def abrir(r):
        return raiz_imagens / "image" / r["caminho_relativo"].rsplit("/", 1)[-1]

    # recortes do fundo (sem o inseto)
    candidatos = []
    for r in indice:
        arquivo = abrir(r)
        if not arquivo.exists():
            continue
        regiao = regiao_sem_inseto(_caixas(raiz_imagens / "label" / (arquivo.stem + ".txt")))
        if regiao:
            candidatos.append((r, arquivo, regiao))
    rng.shuffle(candidatos)
    (saida / "fundo").mkdir(exist_ok=True)
    for r, arquivo, (x0, y0, x1, y1) in candidatos[:n_fundo]:
        with Image.open(arquivo) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            w, h = im.size
            recorte = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        nome = f"{r['image_id']}.jpg"
        recorte.save(saida / "fundo" / nome, quality=95)
        imagens.append({"id": f"fundo_{r['image_id']}", "cenario": "fundo", "arquivo": f"fundo/{nome}", "pai": r["image_id"],
                        "parametro": f"região {x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}"})
    # mesma foto degradada
    base = [r for r in indice if abrir(r).exists()]
    rng.shuffle(base)
    for pasta in ("original",) + DEGRADACOES:
        (saida / pasta).mkdir(exist_ok=True)
    for r in base[:n_degradadas]:
        arquivo = abrir(r)
        real = int(r["indice_modelo"])
        with Image.open(arquivo) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        lado = min(w, h)
        variantes = {
            "original": im,
            "desfoque": im.filter(ImageFilter.GaussianBlur(radius=max(2, int(lado * 0.03)))),
            "escuro": Image.eval(im, lambda v: int(v * 0.2)),
            "superexposto": Image.eval(im, lambda v: min(255, int(v * 3.0))),
            "cinza": ImageOps.grayscale(im).convert("RGB"),
            "ruido": Image.fromarray(np.clip(np.asarray(im, dtype=np.float32) + nrng.normal(0, 60, (h, w, 3)), 0, 255).astype("uint8")),
        }
        pequeno = im.resize((max(1, int(w * 0.3)), max(1, int(h * 0.3))))
        tela = Image.new("RGB", (w, h), (128, 128, 128))
        tela.paste(pequeno, ((w - pequeno.width) // 2, (h - pequeno.height) // 2))
        variantes["sujeito_pequeno"] = tela
        for cenario, img in variantes.items():
            nome = f"{r['image_id']}.jpg"
            if cenario == "jpeg_q10":
                continue
            img.save(saida / cenario / nome, quality=95)
            imagens.append({"id": f"{cenario}_{r['image_id']}", "cenario": cenario, "arquivo": f"{cenario}/{nome}", "pai": r["image_id"] if cenario != "original" else None,
                            "classe_real": real, "origem_imagem": r["image_id"], "parametro": cenario})
        im.save(saida / "jpeg_q10" / f"{r['image_id']}.jpg", quality=10)
        imagens.append({"id": f"jpeg_q10_{r['image_id']}", "cenario": "jpeg_q10", "arquivo": f"jpeg_q10/{r['image_id']}.jpg", "pai": r["image_id"],
                        "classe_real": real, "origem_imagem": r["image_id"], "parametro": "qualidade 10"})
    # os originais viram o "pai" das degradações; ajusta o campo pai para o id do cenário original
    ids_originais = {i["origem_imagem"]: i["id"] for i in imagens if i["cenario"] == "original"}
    for i in imagens:
        if i["cenario"] in DEGRADACOES:
            i["pai"] = ids_originais[i["origem_imagem"]]
    # fotos reais enviadas pela equipe (opcional)
    if pasta_extras and pasta_extras.exists():
        (saida / "extras").mkdir(exist_ok=True)
        for arquivo in sorted(p for p in pasta_extras.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")):
            destino = saida / "extras" / arquivo.name
            destino.write_bytes(arquivo.read_bytes())
            imagens.append({"id": f"extra_{arquivo.stem}", "cenario": "foto_real_extra", "arquivo": f"extras/{arquivo.name}",
                            "parametro": "foto enviada pela equipe"})
    for i in imagens:
        i["sha256"] = _sha(saida / i["arquivo"])
    manifesto = {"esquema": ESQUEMA, "semente": SEMENTE, "regra": "imagens geradas por `python -m src.limiar_t11_3 preparar`; "
                 "os arquivos não são versionados, e os hashes identificam os usados na medição", "imagens": imagens}
    MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
    MANIFESTO.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifesto


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", nargs="?", choices=("preparar", "analisar"))
    ap.add_argument("--raiz-imagens", type=Path, help="pasta com image/ e label/ do AgroInsect")
    ap.add_argument("--saida-imagens", type=Path, help="onde gerar as imagens dos cenários")
    ap.add_argument("--pasta-extras", type=Path, help="fotos reais fora do recorte enviadas pela equipe")
    ap.add_argument("--verificar", action="store_true")
    args = ap.parse_args()
    if args.verificar:
        ruins = divergentes()
        if ruins:
            raise SystemExit("Desatualizados (rode python -m src.limiar_t11_3 analisar): " + ", ".join(ruins))
        print("Artefatos da T11.3 atualizados.")
    elif args.comando == "preparar":
        if not (args.raiz_imagens and args.saida_imagens):
            raise SystemExit("preparar exige --raiz-imagens e --saida-imagens")
        m = preparar(args.raiz_imagens, args.saida_imagens, args.pasta_extras)
        print(f"{len(m['imagens'])} imagens geradas em {args.saida_imagens}; manifesto em {MANIFESTO}.")
    elif args.comando == "analisar":
        print(f"{len(gerar())} arquivos gerados.")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
