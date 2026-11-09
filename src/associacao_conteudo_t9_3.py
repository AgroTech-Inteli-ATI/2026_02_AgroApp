"""Associação da saída do modelo ao conteúdo técnico local (T9.3).

Liga o índice de cada classe do modelo ao dicionário de classes e a uma base local de conteúdo
técnico. Só usa arquivos versionados e a biblioteca padrão; nenhuma função acessa a rede. Não
depende do limiar de confiança (T9.2): quem decide quais previsões aparecem chama `associar_predicoes`
depois, com a lista já filtrada.

O catálogo oficial de conteúdo do Agro App ainda não foi recebido. Enquanto `chave_conteudo` for nula,
cada classe resolve como indisponível, sem usar a chave proposta e sem inventar texto.
"""

from __future__ import annotations

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
CONTENT_TS = "frontend/src/data/content.ts"

ESQUEMA_ASSOCIACAO = "associacao_conteudo_T9_3_v1"
ESQUEMA_BASE = "base_conteudo_T9_3_v1"
CAMPOS_VALIDACAO = ("responsavel", "data", "evidencia")
CAMPOS_ITEM = ("chave", "titulo", "texto", "fonte", "revisado_em", "validated")
PRESERVADOS = ("chave_conteudo", "status_conteudo", "validacao_conteudo")
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
            "status_conteudo": antiga.get("status_conteudo", "aguardando_catalogo_agroapp"),
            "validacao_conteudo": antiga.get("validacao_conteudo"),
            "relacionadas_t6_4": relacionadas[i],
        })
    fontes = {nome: {"arquivo": caminho, "sha256": hash_arquivo(raiz / caminho)}
              for nome, caminho in (("classes_modelo", CLASSES), ("classes_modelo_csv", CLASSES_CSV),
                                    ("dicionario_t3_4", DICIONARIO), ("tratamento_t6_4", TRATAMENTO))}
    return {
        "esquema": ESQUEMA_ASSOCIACAO,
        "versao": "1.0.0",
        "status": "parcial_aguardando_catalogo_do_parceiro",
        "pacote": PACOTE,
        "total_classes": len(classes),
        "identificacao_fonte": FONTE_IDENTIFICACAO,
        "regras": [
            "O conteúdo só é aberto pela chave_conteudo oficial; a chave proposta nunca abre conteúdo.",
            "Classes relacionadas na T6.4 mantêm conteúdo e chave separados; a relação não une classes nem altera o ranking.",
            "Sem chave oficial, status validado e item validado na base, a classe resolve como indisponível.",
        ],
        "fontes": fontes,
        "classes": classes,
    }


def base_vazia() -> dict:
    return {"esquema": ESQUEMA_BASE, "versao": "0.0.0", "status": "vazia_aguardando_catalogo_do_parceiro",
            "campos_item": list(CAMPOS_ITEM), "itens": []}


def carregar(raiz: Path = RAIZ) -> tuple[dict, dict]:
    pasta = raiz / SAIDA
    return ler_json(pasta / ASSOCIACAO), ler_json(pasta / BASE)


def validar_contrato(associacao: dict, base: dict) -> None:
    """Regras que valem agora e quando o catálogo for preenchido."""
    classes = associacao["classes"]
    if [c["indice"] for c in classes] != list(range(len(classes))) or len(classes) != associacao["total_classes"]:
        raise ValueError("índices fora de ordem ou total divergente")
    if len({c["chave_conteudo_proposta"] for c in classes}) != len(classes):
        raise ValueError("chaves propostas repetidas")
    itens = {}
    for item in base["itens"]:
        if set(item) != set(CAMPOS_ITEM) or item["chave"] in itens:
            raise ValueError(f"item inválido ou repetido: {item.get('chave')}")
        if item["validated"] and not all(item[k] for k in ("titulo", "texto", "fonte", "revisado_em")):
            raise ValueError(f"item validado incompleto: {item['chave']}")
        itens[item["chave"]] = item
    por_indice = {c["indice"]: c for c in classes}
    for c in classes:
        if c["chave_conteudo"] is not None and "://" in c["chave_conteudo"]:
            raise ValueError("a chave de conteúdo não pode ser uma URL")
        if c["status_conteudo"] == "validado":
            if not c["chave_conteudo"] or not c["validacao_conteudo"] or \
                    not all(c["validacao_conteudo"].get(k) for k in CAMPOS_VALIDACAO):
                raise ValueError(f"classe {c['indice']} validada sem chave oficial ou sem registro de validação")
        elif c["chave_conteudo"] is not None and c["status_conteudo"] != "aguardando_validacao":
            raise ValueError(f"classe {c['indice']} com chave e status inesperado: {c['status_conteudo']}")
        for r in c["relacionadas_t6_4"]:
            outra = por_indice[r["indice"]]
            if c["chave_conteudo"] is not None and c["chave_conteudo"] == outra["chave_conteudo"]:
                raise ValueError(f"classes relacionadas {c['indice']} e {r['indice']} compartilham o conteúdo")


def resolver(indice: int, associacao: dict, base: dict) -> dict:
    """Identificação e estado do conteúdo de uma classe; levanta ValueError para índice fora do modelo."""
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
            conteudo = {k: item[k] for k in ("titulo", "texto", "fonte", "revisado_em")}
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


def content_ts(associacao: dict, base: dict) -> str:
    """Texto do frontend/src/data/content.ts: só as classes que o resolvedor dá como disponíveis."""
    validar_contrato(associacao, base)
    conteudo = {}
    for c in associacao["classes"]:
        r = resolver(c["indice"], associacao, base)
        if r["disponivel"]:
            x = r["conteudo"]
            conteudo[c["indice"]] = {"title": x["titulo"], "text": x["texto"], "source": x["fonte"],
                                     "reviewedAt": x["revisado_em"], "validated": True}
    return f"""// Gerado por `python -m src.associacao_conteudo_t9_3 frontend` (T9.3). Não edite à mão:
// altere associacao_classes.json e base_conteudo.json em {SAIDA} e gere de novo.
export interface TechnicalContent {{
  title: string;
  text: string;
  source: string;
  reviewedAt: string;
  validated: boolean;
}}

// Chaves são os índices de classes.json do modelo versionado.
export const technicalContent: Partial<Record<number, TechnicalContent>> = {json.dumps(conteudo, ensure_ascii=False, indent=2)};
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("comando", choices=("gerar", "verificar", "frontend"))
    ap.add_argument("--saida", type=Path, default=None, help=f"pasta de saída do gerar (padrão: {SAIDA})")
    ap.add_argument("--exigir-conteudo", action="store_true",
                    help="falha se alguma classe não tiver conteúdo validado (RNF-08 completo)")
    args = ap.parse_args()
    if args.comando == "frontend":
        (RAIZ / CONTENT_TS).write_text(content_ts(*carregar()), encoding="utf-8", newline="\n")
        print(f"{CONTENT_TS} gerado.")
    elif args.comando == "gerar":
        print(f"{gerar(saida=args.saida)['total_classes']} classes associadas.")
    else:
        assoc, base = carregar()
        validar_contrato(assoc, base)
        resumo = cobertura(assoc, base)
        print(json.dumps(resumo, ensure_ascii=False))
        if args.exigir_conteudo and resumo["com_conteudo_disponivel"] != resumo["classes"]:
            sys.exit("Conteúdo técnico validado ausente em parte das classes.")
