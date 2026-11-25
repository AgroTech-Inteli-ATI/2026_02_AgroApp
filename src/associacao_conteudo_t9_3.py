"""Associação da saída do modelo às fichas técnicas locais (T9.3 e T13).

Liga o índice de cada classe do modelo ao dicionário de classes e a uma base local de fichas técnicas.
Só usa arquivos versionados e a biblioteca padrão; nenhuma função acessa a rede. Não depende do limiar
de confiança (T9.2): quem decide quais previsões aparecem chama `associar_predicoes` depois, com a lista
já filtrada.

As fichas são elaboradas pela equipe, em redação própria, a partir de fontes públicas citadas (T13.1). Uma
classe só resolve como disponível quando tem chave de conteúdo, status `validado` (revisão registrada) e
ficha validada na base; antes disso, resolve como indisponível, sem inventar texto.
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from pathlib import Path
import argparse
import csv
import json
import sys

RAIZ = Path(__file__).resolve().parents[1]
PACOTE = "assets/modelos/candidato_T5_6_20261026"
CLASSES = f"{PACOTE}/classes.json"
MANIFESTO = f"{PACOTE}/manifesto.json"
CLASSES_CSV = "assets/data/classes-modelo.csv"
DICIONARIO = "assets/data/dicionario-classes.json"
TRATAMENTO = "assets/data/tratamento_T6_4/proposta_tratamento.json"
SAIDA = "assets/data/conteudo_T9_3"
ASSOCIACAO = "associacao_classes.json"
BASE = "base_conteudo.json"
FONTES = "fontes_conteudo.json"
CONTENT_TS = "frontend/src/data/content.ts"
PROJETO_MD = "docs/Projeto.md"
MARCA_INICIO, MARCA_FIM = "<!-- fichas:inicio -->", "<!-- fichas:fim -->"

ESQUEMA_ASSOCIACAO = "associacao_conteudo_T9_3_v2"
ESQUEMA_BASE = "base_conteudo_T9_3_v2"
CAMPOS_VALIDACAO = ("responsavel", "data", "evidencia")  # responsável: papel (ex.: equipe), não nome de pessoa
CAMPOS_ITEM = ("chave", "titulo", "nome_cientifico", "contexto", "secoes", "elaborado_por", "elaborado_em",
               "revisado_em", "validated")
ORIGENS_CHAVE = ("oficial_agro_app", "equipe")
SECOES = {"como_reconhecer": "Como reconhecer", "danos": "Danos ou sintomas", "confusao": "Pode ser confundido com"}
SECOES_OBRIGATORIAS = ("como_reconhecer", "danos")
LIMITE_TEXTO_ITEM = 240  # frases curtas, para leitura no celular; também barra trecho copiado
PRESERVADOS = ("chave_conteudo", "origem_chave", "status_conteudo", "validacao_conteudo")
FONTE_IDENTIFICACAO = ("Tabela da seção 2 do instruções.md do dataset (Drive Agro_App, dataset/dataset). "
                       "Nomes científicos são referência a validar por agrônomo.")

# índice do modelo -> (slug da chave proposta, nome comum, nome científico). O nome exibido é o do modelo.
IDENTIFICACAO = {
    0: ("diabrotica_speciosa", "Vaquinha", "Diabrotica speciosa"),
    1: ("dalbulus_maidis", "Cigarrinha-do-milho", "Dalbulus maidis"),
    2: ("dichelops_sp", "Percevejo-barriga-verde", "Diceraeus spp. (ex-Dichelops)"),
    3: ("spodoptera_frugiperda", "Lagarta-do-cartucho", "Spodoptera frugiperda"),
    4: ("euschistus_heros", "Percevejo-marrom", "Euschistus heros"),
    5: ("nezara_viridula", "Percevejo-verde", "Nezara viridula"),
    6: ("edessa_meditabunda", "Percevejo-asa-preta", "Edessa meditabunda"),
    7: ("leptoglossus_zonatus", "Percevejo-do-milho", "Leptoglossus zonatus"),
    8: ("chrysodeixis_includens", "Lagarta-falsa-medideira", "Chrysodeixis includens"),
    9: ("anticarsia_gemmatalis", "Lagarta-da-soja", "Anticarsia gemmatalis"),
    10: ("spodoptera_eridania_cosmioides", "Lagarta-das-vagens", "Spodoptera eridania e S. cosmioides"),
    11: ("astylus_variegatus", None, "Astylus variegatus"),
    12: ("deois_flavopicta", "Cigarrinha-das-pastagens", "Deois flavopicta"),
}


def hash_arquivo(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8-sig"))


def gravar_json(caminho: Path, dados) -> None:
    # newline="\n": no Windows o padrão gravaria CRLF e deixaria o arquivo versionado como modificado.
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8",
                       newline="\n")


def _inteiros(texto: str) -> list[int]:
    return [int(x) for x in texto.split(";") if x.strip()]


def _relacionadas(raiz: Path) -> dict[int, list[dict]]:
    """Pares da T6.4: as classes continuam separadas; a relação só indica hipóteses concorrentes."""
    mapa: dict[int, list[dict]] = {i: [] for i in IDENTIFICACAO}
    for decisao in ler_json(raiz / TRATAMENTO)["decisoes"]:
        a, b = decisao["indices_classes"]
        mapa[a].append({"indice": b, "par": decisao["id"]})
        mapa[b].append({"indice": a, "par": decisao["id"]})
    return {i: sorted(v, key=lambda r: r["indice"]) for i, v in mapa.items()}


def _status(classes: list[dict]) -> str:
    if all(c["status_conteudo"] == "validado" for c in classes):
        return "fichas_da_equipe_validadas"
    if any(c["chave_conteudo"] is not None for c in classes):
        return "fichas_da_equipe_em_revisao"
    return "parcial_aguardando_catalogo_do_parceiro"


def montar(raiz: Path = RAIZ, anterior: dict | None = None) -> dict:
    """Gera a associação a partir das fontes; preserva o que foi preenchido à mão (chave e validação)."""
    classes_modelo = ler_json(raiz / CLASSES)
    if [c["indice"] for c in classes_modelo] != list(range(len(classes_modelo))) or len(classes_modelo) != len(IDENTIFICACAO):
        raise ValueError("classes.json fora da ordem ou com total diferente da identificação")
    manifesto = ler_json(raiz / MANIFESTO)
    if hash_arquivo(raiz / CLASSES) != manifesto["sha256"]["classes.json"]:
        raise ValueError("classes.json diverge do manifesto do pacote")
    with (raiz / CLASSES_CSV).open(encoding="utf-8-sig", newline="") as f:
        csv_modelo = {int(r["indice_modelo"]): r for r in csv.DictReader(f, delimiter=";")}
    dicionario = {c["id"]: c for c in ler_json(raiz / DICIONARIO)["classes"]}
    relacionadas = _relacionadas(raiz)
    antigas = {c["indice"]: c for c in (anterior or {}).get("classes", [])}

    classes = []
    for c in classes_modelo:
        i, nome = c["indice"], c["nome"]
        slug, comum, cientifico = IDENTIFICACAO[i]
        if nome != cientifico and not (comum and nome.startswith(comum)):
            raise ValueError(f"identificação da classe {i} não corresponde ao nome do modelo: {nome}")
        linha = csv_modelo[i]
        if linha["classe"] != nome:
            raise ValueError(f"classes-modelo.csv diverge do modelo na classe {i}")
        ids_acervo = [x for x in linha["ids_acervo"].split(";") if x]
        antiga = antigas.get(i, {})
        classes.append({
            "indice": i,
            "nome": nome,
            "nome_comum": comum,
            "nome_cientifico": cientifico,
            "cultura": linha["cultura"].split("/"),
            "ids_inventario": _inteiros(linha["ids_inventario"]),
            "ids_acervo": [{"id": a, "chave_proposta_dicionario": dicionario[a]["chave_conteudo_proposta"]}
                           for a in ids_acervo],
            "chave_conteudo_proposta": f"praga.{slug}",
            "chave_conteudo": antiga.get("chave_conteudo"),
            "origem_chave": antiga.get("origem_chave"),
            "status_conteudo": antiga.get("status_conteudo", "aguardando_catalogo_agroapp"),
            "validacao_conteudo": antiga.get("validacao_conteudo"),
            "relacionadas_t6_4": relacionadas[i],
        })
    fontes = {nome: {"arquivo": caminho, "sha256": hash_arquivo(raiz / caminho)}
              for nome, caminho in (("classes_modelo", CLASSES), ("classes_modelo_csv", CLASSES_CSV),
                                    ("dicionario_t3_4", DICIONARIO), ("tratamento_t6_4", TRATAMENTO))}
    return {
        "esquema": ESQUEMA_ASSOCIACAO,
        "versao": "2.0.0",
        "status": _status(classes),
        "pacote": PACOTE,
        "total_classes": len(classes),
        "identificacao_fonte": FONTE_IDENTIFICACAO,
        "regras": [
            "O conteúdo só é aberto pela chave_conteudo (oficial do Agro App ou da equipe, conforme origem_chave); "
            "a chave proposta nunca abre conteúdo.",
            "Classes relacionadas na T6.4 mantêm conteúdo e chave separados; a relação não une classes nem altera o ranking.",
            "Sem chave, status validado e ficha validada na base, a classe resolve como indisponível.",
            "Ficha da equipe: redação própria com citação de fonte e página; não é conteúdo oficial nem aprovado pelo parceiro.",
        ],
        "fontes": fontes,
        "classes": classes,
    }


def base_vazia() -> dict:
    return {"esquema": ESQUEMA_BASE, "versao": "0.0.0", "status": "vazia", "campos_item": list(CAMPOS_ITEM),
            "secoes": SECOES, "itens": []}


def carregar(raiz: Path = RAIZ) -> tuple[dict, dict]:
    pasta = raiz / SAIDA
    return ler_json(pasta / ASSOCIACAO), ler_json(pasta / BASE)


def carregar_fontes(raiz: Path = RAIZ) -> dict:
    return ler_json(raiz / SAIDA / FONTES)


def _fontes_por_id(fontes: dict) -> dict:
    return {f["id"]: f for f in fontes["fontes"]} | {f["id"]: f for f in fontes.get("fontes_internas", [])}


def _paginas(ref: dict) -> tuple[int, int] | None:
    """Intervalo de páginas impressas citado por uma referência ("78" ou "70-72")."""
    valor = ref.get("paginas", ref.get("pagina"))
    if valor is None:
        return None
    partes = str(valor).split("-")
    return int(partes[0]), int(partes[-1])


def citacao(ref: dict, fontes: dict) -> str:
    """Citação curta de uma referência de item (fonte + página ou seção)."""
    f = _fontes_por_id(fontes).get(ref["id"])
    if f is None:
        raise ValueError(f"fonte {ref['id']} fora do mapa de fontes")
    if f["id"] in {i["id"] for i in fontes.get("fontes_internas", [])}:
        return f["citacao_curta"]
    if "secao" in ref:
        return f"{f['citacao_curta']}, seção “{ref['secao']}”"
    p = _paginas(ref)
    if p is None:
        raise ValueError(f"referência a {ref['id']} sem página nem seção")
    return f"{f['citacao_curta']}, p. {p[0]}" if p[0] == p[1] else f"{f['citacao_curta']}, p. {p[0]}-{p[1]}"


def validar_item(item: dict, fontes: dict | None = None) -> None:
    if set(item) != set(CAMPOS_ITEM):
        raise ValueError(f"campos do item {item.get('chave')} diferem do esquema")
    if not all(item[k] for k in ("chave", "titulo", "nome_cientifico", "elaborado_por", "elaborado_em")):
        raise ValueError(f"item {item['chave']} sem identificação ou autoria")
    ids = [s["id"] for s in item["secoes"]]
    if len(set(ids)) != len(ids) or not set(ids) <= set(SECOES) or not set(SECOES_OBRIGATORIAS) <= set(ids):
        raise ValueError(f"seções inválidas no item {item['chave']}: {ids}")
    for s in item["secoes"]:
        if s["titulo"] != SECOES[s["id"]] or not s["itens"]:
            raise ValueError(f"seção {s['id']} do item {item['chave']} com título errado ou vazia")
        for linha in s["itens"]:
            if set(linha) != {"texto", "fonte"} or not linha["texto"].strip() or len(linha["texto"]) > LIMITE_TEXTO_ITEM:
                raise ValueError(f"linha inválida em {item['chave']}/{s['id']}: {linha}")
            if not isinstance(linha["fonte"], dict) or "id" not in linha["fonte"]:
                raise ValueError(f"linha sem fonte em {item['chave']}/{s['id']}")
            if fontes is not None:
                citacao(linha["fonte"], fontes)  # falha se a fonte não existir no mapa
    if item["validated"] and not item["revisado_em"]:
        raise ValueError(f"item validado sem data de revisão: {item['chave']}")


def validar_contrato(associacao: dict, base: dict, fontes: dict | None = None) -> None:
    """Regras que valem agora e quando as fichas forem validadas."""
    classes = associacao["classes"]
    if [c["indice"] for c in classes] != list(range(len(classes))) or len(classes) != associacao["total_classes"]:
        raise ValueError("índices fora de ordem ou total divergente")
    if len({c["chave_conteudo_proposta"] for c in classes}) != len(classes):
        raise ValueError("chaves propostas repetidas")
    itens = {}
    for item in base["itens"]:
        validar_item(item, fontes)
        if item["chave"] in itens:
            raise ValueError(f"item repetido: {item['chave']}")
        itens[item["chave"]] = item
    por_indice = {c["indice"]: c for c in classes}
    for c in classes:
        chave = c["chave_conteudo"]
        if chave is not None and "://" in chave:
            raise ValueError("a chave de conteúdo não pode ser uma URL")
        if (chave is None) != (c["origem_chave"] is None) or c["origem_chave"] not in (None, *ORIGENS_CHAVE):
            raise ValueError(f"classe {c['indice']}: chave e origem_chave inconsistentes")
        if c["status_conteudo"] == "validado":
            validacao = c["validacao_conteudo"] or {}
            if not chave or not all(validacao.get(k) for k in CAMPOS_VALIDACAO):
                raise ValueError(f"classe {c['indice']} validada sem chave ou sem registro de validação")
        elif chave is not None and c["status_conteudo"] != "aguardando_validacao":
            raise ValueError(f"classe {c['indice']} com chave e status inesperado: {c['status_conteudo']}")
        for r in c["relacionadas_t6_4"]:
            outra = por_indice[r["indice"]]
            if chave is not None and chave == outra["chave_conteudo"]:
                raise ValueError(f"classes relacionadas {c['indice']} e {r['indice']} compartilham o conteúdo")


def resolver(indice: int, associacao: dict, base: dict) -> dict:
    """Identificação e estado da ficha de uma classe; levanta ValueError para índice fora do modelo."""
    if isinstance(indice, bool) or not isinstance(indice, int) or not 0 <= indice < associacao["total_classes"]:
        raise ValueError(f"índice fora das classes do modelo: {indice!r}")
    c = associacao["classes"][indice]
    resultado = {k: c[k] for k in ("indice", "nome", "nome_comum", "nome_cientifico", "cultura")}
    resultado["relacionadas"] = [r["indice"] for r in c["relacionadas_t6_4"]]
    conteudo, motivo = None, None
    if c["chave_conteudo"] is None:
        motivo = "sem_chave_oficial"
    elif c["status_conteudo"] != "validado":
        motivo = "aguardando_validacao"
    else:
        item = next((x for x in base["itens"] if x["chave"] == c["chave_conteudo"]), None)
        if item is None:
            motivo = "item_ausente_na_base"
        elif not item["validated"]:
            motivo = "item_nao_validado"
        else:
            conteudo = {k: item[k] for k in ("titulo", "nome_cientifico", "contexto", "secoes", "elaborado_por",
                                             "revisado_em")}
    resultado.update({"conteudo": conteudo, "disponivel": conteudo is not None, "motivo": motivo})
    return resultado


def associar_predicoes(predicoes: list[dict], associacao: dict, base: dict) -> list[dict]:
    """Enriquece cada previsão (`indice`, `score`) mantendo ordem e score; não aplica limiar."""
    return [{"score": p["score"], **resolver(p["indice"], associacao, base)} for p in predicoes]


def cobertura(associacao: dict, base: dict) -> dict:
    estados = [resolver(c["indice"], associacao, base) for c in associacao["classes"]]
    motivos: dict[str, int] = {}
    for e in estados:
        if e["motivo"]:
            motivos[e["motivo"]] = motivos.get(e["motivo"], 0) + 1
    return {"classes": len(estados), "com_registro": len(estados),
            "com_conteudo_disponivel": sum(e["disponivel"] for e in estados), "indisponiveis_por_motivo": motivos}


def gerar(raiz: Path = RAIZ, saida: Path | None = None) -> dict:
    saida = saida or raiz / SAIDA
    saida.mkdir(parents=True, exist_ok=True)
    anterior = ler_json(saida / ASSOCIACAO) if (saida / ASSOCIACAO).is_file() else None
    associacao = montar(raiz, anterior)
    gravar_json(saida / ASSOCIACAO, associacao)
    if not (saida / BASE).is_file():  # a base é preenchida à mão; nunca é sobrescrita
        gravar_json(saida / BASE, base_vazia())
    return associacao


def _fontes_da_ficha(item: dict, fontes: dict) -> tuple[list[str], list[str]]:
    """Citações agregadas por fonte (com intervalo de páginas) e referências completas das fontes externas."""
    por_id = _fontes_por_id(fontes)
    internas = {i["id"] for i in fontes.get("fontes_internas", [])}
    agregadas: dict[str, list[int]] = {}
    secoes: dict[str, list[str]] = {}
    for s in item["secoes"]:
        for linha in s["itens"]:
            ref = linha["fonte"]
            agregadas.setdefault(ref["id"], [])
            p = _paginas(ref)
            if p:
                agregadas[ref["id"]] += list(p)
            if "secao" in ref:
                secoes.setdefault(ref["id"], [])
                if ref["secao"] not in secoes[ref["id"]]:
                    secoes[ref["id"]].append(ref["secao"])
    curtas, completas = [], []
    for fid, paginas in agregadas.items():
        f = por_id[fid]
        if fid in internas:
            curtas.append(f["citacao_curta"])
            continue
        if paginas:
            lo, hi = min(paginas), max(paginas)
            curtas.append(f"{f['citacao_curta']}, p. {lo}" if lo == hi else f"{f['citacao_curta']}, p. {lo}-{hi}")
        else:
            curtas.append(f"{f['citacao_curta']}, seção “{secoes[fid][0]}”")
        completas.append(f["referencia_abnt"])
    return curtas, completas


def content_ts(associacao: dict, base: dict, fontes: dict | None = None) -> str:
    """Texto do frontend/src/data/content.ts: só as classes que o resolvedor dá como disponíveis."""
    fontes = fontes if fontes is not None else carregar_fontes()
    validar_contrato(associacao, base, fontes)
    por_chave = {i["chave"]: i for i in base["itens"]}
    conteudo = {}
    for c in associacao["classes"]:
        r = resolver(c["indice"], associacao, base)
        if r["disponivel"]:
            item = por_chave[c["chave_conteudo"]]
            curtas, completas = _fontes_da_ficha(item, fontes)
            conteudo[c["indice"]] = {
                "title": item["titulo"],
                "scientificName": item["nome_cientifico"],
                "context": item["contexto"],
                "sections": [{"id": s["id"], "title": s["titulo"],
                              "items": [{"text": x["texto"], "source": citacao(x["fonte"], fontes)} for x in s["itens"]]}
                             for s in item["secoes"]],
                "sources": curtas,
                "references": completas,
                "author": item["elaborado_por"],
                "reviewedAt": item["revisado_em"],
                "validated": True,
            }
    return f"""// Gerado por `python -m src.associacao_conteudo_t9_3 frontend` (T9.3/T13). Não edite à mão:
// altere associacao_classes.json e base_conteudo.json em {SAIDA} e gere de novo.
export interface TechnicalItem {{
  text: string;
  source: string;
}}

export interface TechnicalSection {{
  id: string;
  title: string;
  items: TechnicalItem[];
}}

export interface TechnicalContent {{
  title: string;
  scientificName: string;
  context: string | null;
  sections: TechnicalSection[];
  sources: string[];
  references: string[];
  author: string;
  reviewedAt: string;
  validated: boolean;
}}

// Chaves são os índices de classes.json do modelo versionado.
export const technicalContent: Partial<Record<number, TechnicalContent>> = {json.dumps(conteudo, ensure_ascii=False, indent=2)};
"""


def fichas_markdown(associacao: dict, base: dict, fontes: dict | None = None) -> str:
    """Fichas em texto legível, com a citação de cada frase (rastreabilidade), para o Projeto.md."""
    fontes = fontes if fontes is not None else carregar_fontes()
    por_chave = {i["chave"]: i for i in base["itens"]}
    blocos = []
    for c in associacao["classes"]:
        item = por_chave.get(c["chave_conteudo"])
        if item is None:
            blocos.append(f"#### {c['indice']}. {c['nome']}\n\nSem ficha.")
            continue
        linhas = [f"#### {c['indice']}. {item['titulo']} (*{item['nome_cientifico']}*)", ""]
        if item["contexto"]:
            linhas += [f"*{item['contexto']}*", ""]
        for s in item["secoes"]:
            linhas.append(f"**{s['titulo']}**")
            linhas += [f"- {x['texto']} ({citacao(x['fonte'], fontes)})" for x in s["itens"]]
            linhas.append("")
        blocos.append("\n".join(linhas).rstrip())
    return "\n\n".join(blocos)


def atualizar_projeto(raiz: Path = RAIZ) -> bool:
    """Regrava o bloco de fichas do Projeto.md entre as marcas; devolve True se mudou."""
    caminho = raiz / PROJETO_MD
    texto = caminho.read_text(encoding="utf-8")
    inicio, resto = texto.split(MARCA_INICIO, 1)
    _, fim = resto.split(MARCA_FIM, 1)
    novo = f"{inicio}{MARCA_INICIO}\n{fichas_markdown(*carregar(raiz), carregar_fontes(raiz))}\n{MARCA_FIM}{fim}"
    caminho.write_text(novo, encoding="utf-8", newline="\n")
    return novo != texto


def aprovar(raiz: Path, responsavel: str, evidencia: str, dia: str, indices: list[int] | None = None) -> list[int]:
    """Libera as fichas das classes escolhidas e registra a validação (responsável, data e evidência).

    Sem `indices`, libera só as classes ainda não validadas: rodar de novo não reescreve datas já registradas.
    Para registrar nova revisão de uma ficha já liberada, passe o índice dela.
    """
    if not responsavel.strip() or not evidencia.strip():
        raise ValueError("aprovar exige responsável e evidência")
    try:
        date.fromisoformat(dia)
    except ValueError:
        raise ValueError(f"data fora do formato AAAA-MM-DD: {dia!r}") from None
    associacao, base = carregar(raiz)
    por_chave = {i["chave"]: i for i in base["itens"]}
    total = len(associacao["classes"])
    if indices is None:
        alvo = [c["indice"] for c in associacao["classes"] if c["status_conteudo"] != "validado"]
    else:
        fora = [i for i in indices if isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < total]
        if fora:
            raise ValueError(f"índices fora das classes do modelo (0 a {total - 1}): {fora}")
        alvo = sorted(set(indices))
    for i in alvo:
        c = associacao["classes"][i]
        if c["chave_conteudo"] not in por_chave:
            raise ValueError(f"classe {i} sem ficha na base")
        por_chave[c["chave_conteudo"]].update({"validated": True, "revisado_em": dia})
        c.update({"status_conteudo": "validado",
                  "validacao_conteudo": {"responsavel": responsavel, "data": dia, "evidencia": evidencia}})
    associacao["status"] = _status(associacao["classes"])
    validar_contrato(associacao, base, carregar_fontes(raiz))
    gravar_json(raiz / SAIDA / ASSOCIACAO, associacao)
    gravar_json(raiz / SAIDA / BASE, base)
    return alvo


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("comando", choices=("gerar", "verificar", "frontend", "docs", "aprovar"))
    ap.add_argument("--saida", type=Path, default=None, help=f"pasta de saída do gerar (padrão: {SAIDA})")
    ap.add_argument("--exigir-conteudo", action="store_true",
                    help="falha se alguma classe não tiver conteúdo validado (RNF-08 completo)")
    ap.add_argument("--responsavel", help="aprovar: papel de quem libera (ex.: \"Equipe do projeto\"), não nome de pessoa")
    ap.add_argument("--evidencia", help="aprovar: onde a decisão de liberar e a validação estão registradas")
    ap.add_argument("--data", default=date.today().isoformat(), help="aprovar: data da validação (AAAA-MM-DD)")
    ap.add_argument("--classes", help="aprovar: índices separados por vírgula (padrão: as ainda não validadas)")
    args = ap.parse_args()
    if args.comando == "frontend":
        (RAIZ / CONTENT_TS).write_text(content_ts(*carregar()), encoding="utf-8", newline="\n")
        print(f"{CONTENT_TS} gerado.")
    elif args.comando == "docs":
        print("Projeto.md atualizado." if atualizar_projeto() else "Projeto.md já estava atualizado.")
    elif args.comando == "aprovar":
        if not args.responsavel or not args.evidencia:
            sys.exit("aprovar exige --responsavel e --evidencia")
        try:
            alvo = [int(x) for x in args.classes.split(",")] if args.classes else None
            feitos = aprovar(RAIZ, args.responsavel, args.evidencia, args.data, alvo)
        except ValueError as erro:
            sys.exit(f"aprovar: {erro}")
        (RAIZ / CONTENT_TS).write_text(content_ts(*carregar()), encoding="utf-8", newline="\n")
        print(f"{len(feitos)} classes validadas; {CONTENT_TS} gerado. Rode também: python -m src.associacao_conteudo_t9_3 docs")
    elif args.comando == "gerar":
        print(f"{gerar(saida=args.saida)['total_classes']} classes associadas.")
    else:
        assoc, base = carregar()
        validar_contrato(assoc, base, carregar_fontes())
        resumo = cobertura(assoc, base)
        print(json.dumps(resumo, ensure_ascii=False))
        if args.exigir_conteudo and resumo["com_conteudo_disponivel"] != resumo["classes"]:
            sys.exit("Conteúdo técnico validado ausente em parte das classes.")
