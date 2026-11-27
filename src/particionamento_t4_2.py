"""Agrupamento por origem e distribuição das classes selecionadas na T4.2.

Os grupos identificados não comprovam que fotos de catálogo retratem plantas
independentes quando faltam metadados de planta ou sessão.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import json
import random
import unicodedata

import pandas as pd


ABAS_REVISAO = ("Revisao Milho", "Revisao Soja", "Revisao Milho-Soja")
PARTICOES = ("treino", "validacao", "teste")
PROPORCOES = {"treino": 0.70, "validacao": 0.15, "teste": 0.15}


def hash_texto_versionado(caminho: Path) -> str:
    """Calcula o SHA-256 do texto com as quebras LF usadas no repositório."""
    return sha256(caminho.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def normalizar(valor: object) -> str:
    return unicodedata.normalize("NFC", str(valor)).strip().casefold()


class Uniao:
    def __init__(self, ids: list[str]) -> None:
        self.pai = {identificador: identificador for identificador in ids}

    def achar(self, identificador: str) -> str:
        pai = self.pai[identificador]
        if pai != identificador:
            self.pai[identificador] = self.achar(pai)
        return self.pai[identificador]

    def unir(self, primeiro: str, segundo: str) -> None:
        a, b = self.achar(primeiro), self.achar(segundo)
        if a != b:
            self.pai[max(a, b)] = min(a, b)


def carregar_dados(raiz: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    caminho = raiz / "assets/data/diagnostico_qualidade_T3_3_revisado.xlsx"
    dicionario = raiz / "assets/data/dicionario-classes.json"
    abas = pd.read_excel(caminho, sheet_name=[*ABAS_REVISAO, "Duplicatas visuais"])
    registros = pd.concat([abas[nome] for nome in ABAS_REVISAO], ignore_index=True)
    registros = registros.loc[registros["image_id"].notna()].copy()
    assert registros["image_id"].is_unique, "image_id repetido"
    assert set(registros["decisao_final"]) <= {"manter", "excluir", "revisar"}
    mantidas = registros.loc[registros["decisao_final"].eq("manter")].copy()
    assert mantidas["grupo_origem"].notna().all(), "Há imagem sem grupo_origem"

    conteudo = json.loads(dicionario.read_text(encoding="utf-8"))
    indice = {
        (normalizar(item["cultura"]), normalizar(item["rotulo_origem"])): item["id"]
        for item in conteudo["classes"]
    }

    def classe_candidata(linha: pd.Series) -> str:
        if str(linha["fonte"]).startswith("acervo_"):
            chave = (normalizar(linha["cultura"]), normalizar(linha["ocorrencia"]))
            if chave not in indice:
                raise ValueError(f"Ocorrência do acervo sem ID T3.4: {chave}")
            return indice[chave]
        identificador = linha["class_id"]
        if pd.isna(identificador):
            raise ValueError(f"Imagem de dataset sem class_id: {linha['image_id']}")
        return f"DATASET-{int(identificador):02d}"

    mantidas["classe_candidata"] = mantidas.apply(classe_candidata, axis=1)
    proveniencia = {
        "diagnostico_sha256": sha256(caminho.read_bytes()).hexdigest(),
        "dicionario_sha256": hash_texto_versionado(dicionario),
        "total_diagnostico": len(registros),
        "total_mantidas": len(mantidas),
        "classes_candidatas": mantidas["classe_candidata"].nunique(),
    }
    return mantidas, abas["Duplicatas visuais"], proveniencia


def construir_grupos(
    mantidas: pd.DataFrame, pares_visuais: pd.DataFrame, vinculos: Path | None = None
) -> tuple[pd.DataFrame, dict]:
    dados = mantidas.copy()
    ids = dados["image_id"].astype(str).tolist()
    presentes = set(ids)
    uniao = Uniao(ids)

    def unir_mesma_coluna(coluna: str) -> None:
        for _, linhas in dados.loc[dados[coluna].notna()].groupby(coluna):
            membros = linhas["image_id"].astype(str).tolist()
            for membro in membros[1:]:
                uniao.unir(membros[0], membro)

    unir_mesma_coluna("grupo_origem")
    unir_mesma_coluna("grupo_duplicata_exata")
    pares_confirmados = 0
    pares_falsos = 0
    for linha in pares_visuais.itertuples(index=False):
        resultado = str(linha.resultado_revisao).strip().casefold()
        a, b = str(linha.image_id_1), str(linha.image_id_2)
        if resultado.startswith("imagens diferentes"):
            pares_falsos += 1
        elif resultado.startswith("mesma foto") or resultado.startswith("mesma fotografia"):
            pares_confirmados += 1
            if a in presentes and b in presentes:
                uniao.unir(a, b)
        else:
            raise ValueError(f"Par visual sem conclusão reconhecida: {a}, {b}: {resultado}")

    vinculos_manuais = 0
    if vinculos is not None and vinculos.exists():
        manual = pd.read_csv(vinculos, dtype=str).fillna("")
        assert {"image_id_1", "image_id_2"} <= set(manual.columns)
        for a, b in manual[["image_id_1", "image_id_2"]].itertuples(index=False, name=None):
            if a not in presentes or b not in presentes:
                raise ValueError(f"Vínculo manual contém ID não selecionado: {a}, {b}")
            uniao.unir(a, b)
            vinculos_manuais += 1

    componentes: dict[str, list[str]] = defaultdict(list)
    for identificador in ids:
        componentes[uniao.achar(identificador)].append(identificador)
    grupo_por_id = {}
    for membros in componentes.values():
        chave = sha256("|".join(sorted(membros)).encode("utf-8")).hexdigest()[:16]
        for identificador in membros:
            grupo_por_id[identificador] = f"GRP-{chave}"
    dados["grupo_particao"] = dados["image_id"].map(grupo_por_id)
    assert dados["grupo_particao"].notna().all()
    return dados, {
        "grupos_independentes": len(componentes),
        "pares_visuais_confirmados": pares_confirmados,
        "pares_visuais_falsos": pares_falsos,
        "vinculos_manuais": vinculos_manuais,
        "vinculos_manuais_sha256": sha256(vinculos.read_bytes()).hexdigest()
        if vinculos is not None and vinculos.exists() else None,
    }


def separar_grupos(
    dados: pd.DataFrame, semente: int = 42, proporcoes: dict[str, float] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    proporcoes = dict(PROPORCOES if proporcoes is None else proporcoes)
    assert set(proporcoes) == set(PARTICOES)
    assert abs(sum(proporcoes.values()) - 1) < 1e-9

    grupos = {}
    grupos_por_classe: dict[str, set[str]] = defaultdict(set)
    totais_classe = Counter(dados["classe_candidata"])
    totais_fonte = Counter(dados["fonte"])
    for identificador, linhas in dados.groupby("grupo_particao"):
        classes = Counter(linhas["classe_candidata"])
        grupos[identificador] = {
            "tamanho": len(linhas),
            "classes": classes,
            "fontes": Counter(linhas["fonte"]),
        }
        for classe in classes:
            grupos_por_classe[classe].add(identificador)

    exploratorias = {c for c, gs in grupos_por_classe.items() if len(gs) < 3}
    elegiveis = set(grupos_por_classe) - exploratorias
    atribuicao: dict[str, str] = {}
    travados = set()
    for classe in exploratorias:
        for grupo in grupos_por_classe[classe]:
            atribuicao[grupo] = "treino"
            travados.add(grupo)

    pendencias = []
    for classe in sorted(elegiveis, key=lambda c: (len(grupos_por_classe[c]), c)):
        associados = grupos_por_classe[classe]
        for particao in PARTICOES:
            if any(atribuicao.get(g) == particao for g in associados):
                continue
            livres = [g for g in associados if g not in atribuicao]
            if not livres:
                pendencias.append(f"{classe}: sem grupo livre para {particao}")
                continue
            if particao == "treino":
                escolhido = max(livres, key=lambda g: (grupos[g]["classes"][classe], grupos[g]["tamanho"], g))
            else:
                escolhido = min(livres, key=lambda g: (grupos[g]["tamanho"], g))
            atribuicao[escolhido] = particao

    total = len(dados)
    atual_tamanho = Counter()
    atual_classe = {p: Counter() for p in PARTICOES}
    atual_fonte = {p: Counter() for p in PARTICOES}

    def atualizar(grupo: str, particao: str) -> None:
        info = grupos[grupo]
        atual_tamanho[particao] += info["tamanho"]
        atual_classe[particao].update(info["classes"])
        atual_fonte[particao].update(info["fontes"])

    for grupo, particao in atribuicao.items():
        atualizar(grupo, particao)

    def custo_incremental(grupo: str, particao: str) -> float:
        info = grupos[grupo]
        fracao = proporcoes[particao]

        def delta(atual: int, adicao: int, alvo: float) -> float:
            return ((atual + adicao - alvo) ** 2 - (atual - alvo) ** 2) / max(alvo, 1)

        custo = delta(atual_tamanho[particao], info["tamanho"], fracao * total)
        for classe, quantidade in info["classes"].items():
            if classe in elegiveis:
                custo += 2 * delta(
                    atual_classe[particao][classe], quantidade, fracao * totais_classe[classe]
                )
        for fonte, quantidade in info["fontes"].items():
            custo += 0.5 * delta(
                atual_fonte[particao][fonte], quantidade, fracao * totais_fonte[fonte]
            )
        return custo

    rng = random.Random(semente)
    livres = [g for g in grupos if g not in atribuicao]
    rng.shuffle(livres)
    livres.sort(key=lambda g: -grupos[g]["tamanho"])
    for grupo in livres:
        particao = min(PARTICOES, key=lambda p: (custo_incremental(grupo, p), PARTICOES.index(p)))
        atribuicao[grupo] = particao
        atualizar(grupo, particao)

    resultado = dados.copy()
    resultado["particao"] = resultado["grupo_particao"].map(atribuicao)
    resultado["status_classe"] = resultado["classe_candidata"].map(
        lambda c: "exploratoria_menos_de_3_grupos" if c in exploratorias else "candidata_a_avaliacao"
    )
    resumo = []
    for classe, linhas in resultado.groupby("classe_candidata"):
        item = {
            "classe_candidata": classe,
            "ocorrencia": " | ".join(sorted(map(str, linhas["ocorrencia"].unique()))),
            "status_classe": linhas["status_classe"].iloc[0],
            "imagens": len(linhas),
            "grupos": linhas["grupo_particao"].nunique(),
        }
        for particao in PARTICOES:
            parte = linhas.loc[linhas["particao"].eq(particao)]
            item[f"imagens_{particao}"] = len(parte)
            item[f"grupos_{particao}"] = parte["grupo_particao"].nunique()
        item["cobertura_tres_particoes"] = all(item[f"grupos_{p}"] > 0 for p in PARTICOES)
        resumo.append(item)
    resumo = pd.DataFrame(resumo).sort_values("classe_candidata").reset_index(drop=True)

    # Esses testes são a condição mínima para evitar vazamento identificável.
    assert resultado.groupby("grupo_particao")["particao"].nunique().eq(1).all()
    assert resultado.groupby("grupo_origem")["particao"].nunique().eq(1).all()
    sha_validos = resultado.loc[resultado["sha256"].notna()]
    assert sha_validos.groupby("sha256")["particao"].nunique().eq(1).all()
    assert resultado.loc[resultado["status_classe"].eq("exploratoria_menos_de_3_grupos"), "particao"].eq("treino").all()

    sem_cobertura = resumo.loc[
        resumo["status_classe"].eq("candidata_a_avaliacao")
        & ~resumo["cobertura_tres_particoes"],
        "classe_candidata",
    ].tolist()
    auditoria = {
        "semente": semente,
        "proporcoes_alvo": proporcoes,
        "imagens_por_particao": {p: int(atual_tamanho[p]) for p in PARTICOES},
        "grupos_por_particao": {p: sum(v == p for v in atribuicao.values()) for p in PARTICOES},
        "classes_exploratorias": len(exploratorias),
        "classes_candidatas_a_avaliacao": len(elegiveis),
        "classes_candidatas_sem_cobertura": sem_cobertura,
        "pendencias_da_ancoragem": pendencias,
        "rotulos_finais_aprovados": False,
        "inspecao_visual_completa": False,
        "independencia_de_planta_confirmada_para_catalogo": False,
    }
    return resultado, resumo, auditoria
