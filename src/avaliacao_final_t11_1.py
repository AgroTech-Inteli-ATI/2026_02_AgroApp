"""Avaliação final (T11.1) dos modelos do build entregue, por classe.

Avalia os arquivos .tflite publicados em `frontend/dist/models` (os mesmos que o
navegador baixa), com o preprocessing T10.2 e o runtime TFLite + XNNPACK, 1 thread,
que a T10.2 mostrou equivalente ao LiteRT.js. Antes de avaliar, reconfere essa
equivalência nos 18 casos com scores gravados do navegador.

O índice histórico é exploratório (T10.1): os resultados não comprovam generalização.

python -m src.avaliacao_final_t11_1 --raiz-imagens "C:/.../Agro App"
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess

import numpy as np

from src.avaliacao import calcular_metricas
from src.benchmark_t5_6 import interpretador, prever
from src.preprocessamento import CONTRATO_PREPROCESSAMENTO, preparar_imagem

RAIZ = Path(__file__).resolve().parents[1]
BUILD = RAIZ / "frontend/dist"
INDICE = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
DECISAO_T10_1 = RAIZ / "assets/data/independencia_T10_1/decisao_avaliacao.json"
GRUPOS_T10_1 = RAIZ / "assets/data/independencia_T10_1/grupos_relacionados.csv"
COMPARACAO_T10_2 = RAIZ / "assets/data/comparacao_preprocessamento_T10_2/comparacao.json"
FIXTURES_T10_2 = RAIZ / "frontend/tests/fixtures/preprocessing"
POLITICA = RAIZ / "assets/data/politica_T6_5/parametros.json"
PREDICOES_T8_1 = RAIZ / "assets/data/avaliacao_T8_1/candidato_T5_6_20261026/predicoes_teste.csv"
SAIDA = RAIZ / "assets/data/avaliacao_final_T11_1"
DOC = RAIZ / "docs/Avaliacao_Final_T11_1.md"
PARTICOES = ("teste", "validacao")
PAPEL = {"principal": "principal", "contingencia": "contingência"}
# Partições que o modelo já "viu" antes de cada partição avaliada (treino; seleção).
ANTERIORES = {"validacao": {"treino"}, "teste": {"treino", "validacao"}}
COLUNA_T8_1 = {"Float16": "previsto_float16", "INT8": "previsto_int8_t7_3"}
TOLERANCIA_WEB = 1e-5  # mesma tolerância Float16 do teste de navegador T10.2
REAMOSTRAS, SEMENTE = 2000, 42
CODIGO = ("src/avaliacao_final_t11_1.py", "src/avaliacao.py", "src/preprocessamento.py", "src/benchmark_t5_6.py")


def _sha(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def conferir_build(build: Path) -> dict:
    """Recusa build cujo modelo ou catálogo de classes divirja do manifesto servido."""
    manifesto = _json(build / "models/manifest.json")
    fonte = manifesto["classesSource"]
    if _sha(RAIZ / fonte["sourcePath"]) != fonte["sha256"]:
        raise ValueError("classes.json diverge do manifesto do build")
    if [c["indice"] for c in manifesto["classes"]] != list(range(13)):
        raise ValueError("o manifesto do build não tem as 13 classes em ordem")
    for spec in manifesto["models"]:
        arquivo = build / "models" / spec["filename"]
        if arquivo.stat().st_size != spec["bytes"] or _sha(arquivo) != spec["sha256"]:
            raise ValueError(f"modelo do build diverge do manifesto: {spec['filename']}")
    return manifesto


def carregar_indice(indice: Path, nomes: list[str]) -> list[dict]:
    esperado = _json(DECISAO_T10_1)["indice_sha256"]
    if _sha(indice) != esperado:
        raise ValueError("índice diverge do índice auditado na T10.1")
    linhas, ids = _csv(indice), set()
    for linha in linhas:
        if linha["image_id"] in ids:
            raise ValueError("image_id duplicado no índice")
        ids.add(linha["image_id"])
        rotulo = int(linha["indice_modelo"])
        if not 0 <= rotulo < len(nomes) or linha["nome_classe_modelo"] != nomes[rotulo]:
            raise ValueError(f"classe do índice diverge do manifesto: {linha['image_id']}")
    return linhas


def excluidos_por_vinculo(grupos: list[dict], particao: str) -> list[str]:
    """IDs da partição com vínculo registrado (T10.1) a imagens de partições anteriores."""
    por_grupo: dict[str, list[dict]] = {}
    for linha in grupos:
        por_grupo.setdefault(linha["grupo_revisao"], []).append(linha)
    return sorted(
        l["image_id"] for membros in por_grupo.values() for l in membros
        if l["particao"] == particao and any(m["particao"] in ANTERIORES[particao] for m in membros)
    )


def metricas(rotulos: np.ndarray, scores: np.ndarray, nomes: list[str], limiar: float,
             bootstrap: bool = True) -> dict:
    previstos = scores.argmax(axis=1)
    base = calcular_metricas(rotulos, previstos, len(nomes), nomes)
    matriz = np.array(base["matriz_confusao"])
    total = matriz.sum()
    for c in base["por_classe"]:
        i = c["indice"]
        # Acurácia por classe = um-contra-todos: (VP + VN) / N.
        erros = matriz[i].sum() + matriz[:, i].sum() - 2 * matriz[i, i]
        c["acuracia_ovr"] = float((total - erros) / total) if total else None
    top3 = np.argsort(-scores, axis=1, kind="stable")[:, :3]
    aceitos = scores.max(axis=1) >= limiar  # política T6.5: top-1 >= limiar
    acertos = previstos == rotulos
    base["top3_acuracia"] = float(np.mean((top3 == rotulos[:, None]).any(axis=1)))
    base["politica_confianca"] = {
        "limiar": limiar, "aceitos": int(aceitos.sum()), "cobertura": float(aceitos.mean()),
        "acuracia_aceitos": float(acertos[aceitos].mean()) if aceitos.any() else None,
        "erros_aceitos": int((aceitos & ~acertos).sum()),
        "acertos_inconclusivos": int((~aceitos & acertos).sum()),
    }
    if bootstrap:
        rng = np.random.default_rng(SEMENTE)
        amostras = [rng.integers(0, len(rotulos), len(rotulos)) for _ in range(REAMOSTRAS)]
        acc = [float(np.mean(acertos[a])) for a in amostras]
        f1 = [calcular_metricas(rotulos[a], previstos[a], len(nomes))["f1_macro"] for a in amostras]
        base["ic95_bootstrap"] = {
            "reamostras": REAMOSTRAS, "semente": SEMENTE, "unidade": "imagem",
            "acuracia": [float(v) for v in np.percentile(acc, [2.5, 97.5])],
            "f1_macro": [float(v) for v in np.percentile(f1, [2.5, 97.5])],
        }
    return base


def conferir_runtime_web(interpretadores: dict, limiar: float) -> dict:
    """Reexecuta os 18 casos T10.2 e compara com os scores medidos no navegador."""
    comparacao = _json(COMPARACAO_T10_2)
    # Os casos de fronteira não têm hash registrado; uma alteração neles muda os scores e é recusada abaixo.
    hashes = {f["file"]: f["sha256"] for f in comparacao["fixtures"]}
    resultado = {}
    for formato, interp in interpretadores.items():
        casos = comparacao["models"][formato]["cases"]
        diffs, mudancas = [], 0
        for caso in casos:
            caminho = FIXTURES_T10_2 / caso["file"]
            if caso["file"] in hashes and _sha(caminho) != hashes[caso["file"]]:
                raise ValueError(f"fixture T10.2 alterada: {caso['file']}")
            atual = prever(interp, preparar_imagem(caminho))
            web = np.array(caso["webScores"], dtype=np.float64)
            diffs.append(float(np.abs(atual - web).max()))
            mudancas += int(atual.argmax() != web.argmax() or (atual.max() >= limiar) != (web.max() >= limiar))
        if max(diffs) > TOLERANCIA_WEB or mudancas:
            raise ValueError(f"{formato}: runtime Python não reproduz o navegador (máx {max(diffs)}, mudanças {mudancas})")
        resultado[formato] = {"casos": len(casos), "diferenca_maxima_score": max(diffs),
                              "mudancas_classe_ou_decisao": mudancas, "navegador": comparacao["webEnvironment"],
                              "runtime_web": comparacao["models"][formato]["runtime"]}
    return resultado


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "indisponível"


def avaliar(raiz_imagens: Path, build: Path = BUILD, indice: Path = INDICE,
            saida: Path = SAIDA, doc: Path = DOC) -> dict:
    import tensorflow as tf
    from PIL import __version__ as pillow

    manifesto = conferir_build(build)
    nomes = [c["nome"] for c in manifesto["classes"]]
    linhas = carregar_indice(indice, nomes)
    limiar = float(_json(POLITICA)["limiar_confianca"])
    grupos = _csv(GRUPOS_T10_1)
    specs = {m["format"]: m for m in manifesto["models"]}
    interps = {f: interpretador(build / "models" / s["filename"], 1, "padrao") for f, s in specs.items()}
    equivalencia = conferir_runtime_web(interps, limiar)

    previsoes_t8 = {l["image_id"]: l for l in _csv(PREDICOES_T8_1)}
    resultados, predicoes, por_classe = {}, [], []
    for particao in PARTICOES:
        alvo = [l for l in linhas if l["particao"] == particao]
        rotulos = np.array([int(l["indice_modelo"]) for l in alvo])
        scores = {f: np.zeros((len(alvo), 13)) for f in specs}
        for i, linha in enumerate(alvo):
            caminho = raiz_imagens / linha["caminho_relativo"]
            if _sha(caminho) != linha["sha256_original"]:
                raise ValueError(f"hash original divergente: {linha['image_id']}")
            imagem = preparar_imagem(caminho)
            for formato, interp in interps.items():
                scores[formato][i] = prever(interp, imagem)
        excluir = excluidos_por_vinculo(grupos, particao)
        manter = np.array([l["image_id"] not in excluir for l in alvo])
        resultados[particao] = {"imagens": len(alvo), "excluidos_sensibilidade": excluir, "modelos": {}}
        for formato in specs:
            s = scores[formato]
            r = {"integral": metricas(rotulos, s, nomes, limiar)}
            if excluir:
                r["sensibilidade_sem_vinculos"] = metricas(rotulos[manter], s[manter], nomes, limiar, bootstrap=False)
            if particao == "teste":
                anteriores = [int(previsoes_t8[l["image_id"]][COLUNA_T8_1[formato]]) for l in alvo]
                r["concordancia_T8_1"] = {"coluna": COLUNA_T8_1[formato],
                                          "iguais": int((s.argmax(axis=1) == anteriores).sum()), "total": len(alvo)}
            resultados[particao]["modelos"][formato] = r
            for recorte, m in (("integral", r["integral"]), ("sem_vinculos", r.get("sensibilidade_sem_vinculos"))):
                for c in (m or {}).get("por_classe", []):
                    por_classe.append({"modelo": formato, "particao": particao, "recorte": recorte, **c})
            for linha, valores in zip(alvo, s):
                predicoes.append({
                    "image_id": linha["image_id"], "particao": particao, "modelo": formato,
                    "indice_real": linha["indice_modelo"], "indice_previsto": int(valores.argmax()),
                    "score_top1": f"{valores.max():.8f}",
                    "decisao": "aceito" if valores.max() >= limiar else "inconclusivo",
                    **{f"score_{k}": f"{v:.8f}" for k, v in enumerate(valores)},
                })

    agora = datetime.now(timezone(timedelta(hours=-3)))
    proveniencia = {
        "data": agora.strftime("%Y-%m-%d"),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_alteracoes_locais": bool(_git("status", "--porcelain", "--untracked-files=no", "--", "src", "frontend")),
        "build": build.relative_to(RAIZ).as_posix(),
        "manifesto_sha256": _sha(build / "models/manifest.json"),
        "modelo": {"id": manifesto["id"], "versao": manifesto["version"], "arquitetura": manifesto["architecture"],
                   "selecao": manifesto["selection"]},
        "arquivos_modelo": {f: {k: s[k] for k in ("role", "version", "filename", "bytes", "sha256", "sourcePath", "sourceSha256")}
                            for f, s in specs.items()},
        "classes_sha256": manifesto["classesSource"]["sha256"],
        "indice": {"caminho": indice.relative_to(RAIZ).as_posix(), "sha256": _sha(indice)},
        "preprocessamento": CONTRATO_PREPROCESSAMENTO,
        "politica_confianca": {"caminho": POLITICA.relative_to(RAIZ).as_posix(), "sha256": _sha(POLITICA), "limiar": limiar,
                               "meta_acerto": float(_json(POLITICA)["base"]["meta_acerto"])},
        "runtime": {"interpretador": "tf.lite.Interpreter", "delegate": "padrao (XNNPACK)", "threads": 1,
                    "tensorflow": tf.__version__, "python": platform.python_version(), "numpy": np.__version__,
                    "pillow": pillow, "plataforma": platform.platform()},
        "equivalencia_runtime_web": equivalencia,
        "codigo_sha256": {p: _sha(RAIZ / p) for p in CODIGO},
    }
    resultado = {"esquema": "avaliacao_final_T11_1_v1", "classificacao": "exploratoria",
                 "generalizacao_comprovada": False, "proveniencia": proveniencia, "resultados": resultados}

    saida.mkdir(parents=True, exist_ok=True)
    (saida / "metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                                         encoding="utf-8", newline="\n")
    for nome, linhas_csv in (("metricas_por_classe.csv", por_classe), ("predicoes.csv", predicoes)):
        with (saida / nome).open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(linhas_csv[0]), lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(linhas_csv)
    doc.write_text(relatorio(resultado, nomes), encoding="utf-8", newline="\n")
    return resultado


def _n(valor, casas=4):
    return "—" if valor is None else f"{valor:.{casas}f}".replace(".", ",")


def _pct(valor):
    return "—" if valor is None else f"{100 * valor:.1f}%".replace(".", ",")


def relatorio(r: dict, nomes: list[str]) -> str:
    p, res = r["proveniencia"], r["resultados"]
    meta = p["politica_confianca"]["meta_acerto"]
    arq = p["arquivos_modelo"]
    eq = p["equivalencia_runtime_web"]
    t = [
        "# T11.1 — Avaliação final do modelo e métricas por classe", "",
        "Autor: Glauco · Revisor: Rui · Meta de entrega: a definir", "",
        f"Execução registrada em {datetime.strptime(p['data'], '%Y-%m-%d').strftime('%d/%m/%Y')} (America/Sao_Paulo). "
        "Relatório gerado por [`avaliacao_final_t11_1.py`](../src/avaliacao_final_t11_1.py); "
        "dados completos em [`assets/data/avaliacao_final_T11_1`](../assets/data/avaliacao_final_T11_1/metricas.json).", "",
        "> **Classificação: avaliação exploratória.** Não existe conjunto independente reservado "
        "([T10.1](../assets/data/independencia_T10_1/README.md)). Os números abaixo descrevem o desempenho do build "
        "entregue no recorte histórico e **não comprovam generalização** para fotos novas de campo.", "",
        "## Resumo", "",
        "| Modelo (papel) | Conjunto | Imagens | Acurácia | IC 95% acurácia | F1 macro | IC 95% F1 macro | Precisão macro | Recall macro | Top-3 |",
        "| --- | --- | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for particao in PARTICOES:
        for formato, m in res[particao]["modelos"].items():
            i = m["integral"]
            av = [c for c in i["por_classe"] if c["status"] == "avaliada"]
            ic = i["ic95_bootstrap"]
            t.append(f"| {formato} ({PAPEL[arq[formato]['role']]}) | {_rotulo(particao)} | {i['total_amostras']} | {_n(i['acuracia'])} | "
                     f"{_n(ic['acuracia'][0])}–{_n(ic['acuracia'][1])} | {_n(i['f1_macro'])} | "
                     f"{_n(ic['f1_macro'][0])}–{_n(ic['f1_macro'][1])} | {_n(np.mean([c['precisao'] for c in av]))} | "
                     f"{_n(i['balanced_accuracy'])} | {_n(i['top3_acuracia'])} |")
    t += ["",
          "O resultado de referência para a entrega é o **Float16 (principal) no teste histórico**. O INT8 só é carregado "
          "pelo aplicativo quando o Float16 falha ao compilar ou validar. A validação participou da seleção do checkpoint e do "
          "limiar, por isso tende a ser otimista e aparece apenas como complemento. Recall macro é igual à balanced accuracy. "
          "Os intervalos são bootstrap percentil por imagem e, por ignorarem a correlação entre fotos do mesmo grupo, "
          "tendem a ser estreitos demais.", "",
          "## Identificação do que foi avaliado", "",
          "| Item | Valor |", "| --- | --- |",
          f"| Modelo | `{p['modelo']['id']}` · versão **{p['modelo']['versao']}** · {p['modelo']['arquitetura']} · seleção `{p['modelo']['selecao']['status']}` |"]
    for formato, a in arq.items():
        tamanho = f"{a['bytes']:_}".replace("_", ".")
        t.append(f"| Arquivo {formato} ({PAPEL[a['role']]}, {a['version']}) | `{p['build']}/models/{a['filename']}` · "
                 f"{tamanho} bytes · SHA-256 `{a['sha256']}` (origem `{a['sourceSha256'][:16]}…`) |")
    t += [f"| Build | `{p['build']}` · manifesto SHA-256 `{p['manifesto_sha256']}` · commit `{p['git_commit']}`"
          + (" (com alterações locais)" if p["git_alteracoes_locais"] else "") + " |",
          f"| Runtime | TFLite `{p['runtime']['interpretador']}` {p['runtime']['tensorflow']}, delegate {p['runtime']['delegate'].replace('padrao', 'padrão')}, {p['runtime']['threads']} thread · Python {p['runtime']['python']}, NumPy {p['runtime']['numpy']}, Pillow {p['runtime']['pillow']} |",
          f"| Preprocessing | contrato `{p['preprocessamento']}` ([seção 10.2](Projeto.md#102-correspondência-do-preprocessing-python-e-web)) |",
          f"| Índice | `{p['indice']['caminho']}` · SHA-256 `{p['indice']['sha256']}` (o mesmo auditado na T10.1) |",
          f"| Classes | 13, ordem do manifesto · SHA-256 `{p['classes_sha256']}` |",
          f"| Política de confiança | top-1 ≥ {_n(p['politica_confianca']['limiar'], 2)} ([T6.5](../{p['politica_confianca']['caminho']})) |",
          f"| Conjuntos | teste histórico ({res['teste']['imagens']} imagens) e validação ({res['validacao']['imagens']} imagens); treino não avaliado |",
          "", "### Equivalência com o runtime do navegador", "",
          "O avaliador lê os `.tflite` do build, verifica tamanho e SHA-256 contra o manifesto servido e recusa divergências. "
          "Antes da avaliação, reexecuta os 18 casos fotográficos da T10.2 e compara os scores com os registrados no navegador "
          f"(tolerância `{TOLERANCIA_WEB:g}`, sem mudança de classe ou decisão):", "",
          "| Modelo | Runtime web de referência | Casos | Diferença máxima de score | Mudanças de classe/decisão |",
          "| --- | --- | ---: | ---: | ---: |"]
    for formato, e in eq.items():
        t.append(f"| {formato} | {e['runtime_web']} (Chromium {e['navegador']['browser']}) | {e['casos']} | `{e['diferenca_maxima_score']:.3g}` | {e['mudancas_classe_ou_decisao']} |")
    t += ["", "## Métricas por classe", "",
          "Acurácia por classe é calculada um-contra-todos: `(VP + VN) / N`. Como VN domina com 13 classes, ela fica sempre alta; "
          "o recall mostra a taxa de acerto das imagens da própria classe. Precisão de classe nunca prevista vale 0.", ""]
    for particao in PARTICOES:
        for formato, m in res[particao]["modelos"].items():
            t += [f"### {formato} ({PAPEL[arq[formato]['role']]}) — {_rotulo(particao)}", "",
                  "| Índice | Classe | Acurácia (OvR) | Precisão | Recall | F1 | Suporte |",
                  "| ---: | --- | ---: | ---: | ---: | ---: | ---: |"]
            for c in m["integral"]["por_classe"]:
                t.append(f"| {c['indice']} | {c['nome']} | {_n(c['acuracia_ovr'])} | {_n(c['precisao'])} | {_n(c['recall'])} | {_n(c['f1'])} | {c['suporte']} |")
            t.append(f"| | **Total / macro** | **{_n(m['integral']['acuracia'])}** (global) | | **{_n(m['integral']['balanced_accuracy'])}** | **{_n(m['integral']['f1_macro'])}** | **{m['integral']['total_amostras']}** |")
            t.append("")
    principal = next(f for f, a in arq.items() if a["role"] == "principal")
    ref = res["teste"]["modelos"][principal]["integral"]
    matriz = ref["matriz_confusao"]
    fracas = [c for c in ref["por_classe"] if c["f1"] is not None and c["f1"] < 0.6]
    confusoes = sorted(((v, i, j) for i, linha in enumerate(matriz) for j, v in enumerate(linha) if i != j and v),
                       key=lambda x: (-x[0], x[1], x[2]))[:5]
    t += [f"### Leitura dos resultados ({principal}, teste histórico)", "",
          f"A diferença entre acurácia global ({_n(ref['acuracia'])}) e F1 macro ({_n(ref['f1_macro'])}) vem do desbalanceamento: "
          "as classes com mais imagens (Vaquinha, Astylus, Lagarta-do-cartucho) têm F1 alto e dominam a acurácia, enquanto o F1 macro "
          "pesa igualmente as classes pequenas. Classes com F1 abaixo de 0,60: "
          + "; ".join(f"{c['nome']} (F1 {_n(c['f1'], 2)}, recall {_n(c['recall'], 2)}, suporte {c['suporte']})" for c in fracas)
          + ". Principais confusões (real → prevista): "
          + "; ".join(f"{nomes[i]} → {nomes[j]} ({v})" for v, i, j in confusoes) + ".", ""]
    t += [f"### Matriz de confusão — {principal}, teste histórico", "",
          "Linhas: classe real; colunas: classe prevista (índices da tabela acima).", "",
          "| Real \\ Prevista | " + " | ".join(str(i) for i in range(13)) + " |",
          "| ---: | " + " | ".join("---:" for _ in range(13)) + " |"]
    t += [f"| **{i}** | " + " | ".join(f"**{v}**" if i == j else (str(v) if v else "·") for j, v in enumerate(linha)) + " |"
          for i, linha in enumerate(matriz)]
    t += ["", "## Política de confiança no aplicativo", "",
          "O aplicativo só indica a classe quando o top-1 atinge o limiar; abaixo dele, mostra resultado inconclusivo. "
          "O limiar foi calibrado em Keras FP32 na validação e não foi recalibrado para os arquivos entregues.", "",
          "| Modelo | Conjunto | Cobertura (aceitos) | Acurácia nos aceitos | Erros aceitos | Acertos tornados inconclusivos |",
          "| --- | --- | ---: | ---: | ---: | ---: |"]
    for particao in PARTICOES:
        for formato, m in res[particao]["modelos"].items():
            pc = m["integral"]["politica_confianca"]
            t.append(f"| {formato} | {_rotulo(particao)} | {pc['aceitos']}/{m['integral']['total_amostras']} ({_pct(pc['cobertura'])}) | "
                     f"{_n(pc['acuracia_aceitos'])} | {pc['erros_aceitos']} | {pc['acertos_inconclusivos']} |")
    t.append("")
    t.append(f"A meta de acerto nos aceitos definida na T6.5 é {_n(meta, 2)}, medida na validação em Keras FP32.")
    excl = res["teste"]["excluidos_sensibilidade"]
    suportes = [c["suporte"] for c in ref["por_classe"]]
    t += ["", "## Análise de sensibilidade (retrospectiva)", "",
          "Regra: excluir da partição avaliada as imagens com vínculo registrado na T10.1 a imagens de partições usadas antes dela "
          f"(treino e validação, no caso do teste). IDs removidos do teste: {', '.join(f'`{i}`' for i in excl)}. "
          "Na validação nenhuma imagem atende à regra. A exclusão não restaura a independência; serve só para dimensionar o efeito.", "",
          "| Modelo | Recorte | Imagens | Acurácia | F1 macro | Precisão macro | Recall macro |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for formato, m in res["teste"]["modelos"].items():
        for rotulo, x in (("integral", m["integral"]), ("sem vínculos", m.get("sensibilidade_sem_vinculos"))):
            if x:
                av = [c for c in x["por_classe"] if c["status"] == "avaliada"]
                t.append(f"| {formato} | {rotulo} | {x['total_amostras']} | {_n(x['acuracia'])} | {_n(x['f1_macro'])} | "
                         f"{_n(np.mean([c['precisao'] for c in av]))} | {_n(x['balanced_accuracy'])} |")
    t += ["", "Os suportes por classe do recorte reduzido estão em `metricas_por_classe.csv` (`recorte = sem_vinculos`).", "",
          "## Consistência com avaliações anteriores", "",
          "Classe prevista no teste histórico comparada às predições da [T8.1](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/relatorio_avaliacao.md), "
          "que usou os arquivos de origem dos mesmos modelos:", "",
          "| Modelo | Coluna T8.1 | Predições iguais |", "| --- | --- | ---: |"]
    for formato, m in res["teste"]["modelos"].items():
        c = m["concordancia_T8_1"]
        t.append(f"| {formato} | `{c['coluna']}` | {c['iguais']}/{c['total']} |")
    t += ["", "## Limitações metodológicas", "",
          "1. **Sem conjunto independente.** O teste histórico já foi consultado durante o desenvolvimento (T6/T8). Todas as métricas "
          "são exploratórias e servem para comparação descritiva, regressão e análise de erros, não como estimativa de generalização.",
          "2. **Vazamento conhecido e vínculos desconhecidos.** Há uma fotografia repetida entre treino e teste (`IMG_01019`/`IMG_01874`) "
          "e uma relação suspeita entre validação e teste (`IMG_01752`/`IMG_01835`). A busca perceptual da T10.1 não é exaustiva. "
          "O efeito real sobre as métricas é desconhecido; a análise de sensibilidade cobre só os casos registrados.",
          "3. **Validação usada na seleção.** Checkpoint, formato final e limiar de confiança foram escolhidos na validação, "
          "cujo resultado é otimista.",
          f"4. **Suporte pequeno e desbalanceado.** No teste, o suporte vai de {min(suportes)} a {max(suportes)} imagens por classe, "
          f"e {sum(s < 30 for s in suportes)} das 13 classes têm menos de 30. Uma única imagem altera o recall da menor classe em "
          f"{_n(100 / min(suportes), 1)} pontos percentuais. As métricas dessas classes são instáveis. Os intervalos de confiança "
          "globais tratam as imagens como independentes e subestimam a incerteza; não foram calculados intervalos por classe.",
          "5. **Domínio das imagens.** O acervo combina iNaturalist e AgroInsect, com enquadramento e qualidade diferentes das fotos "
          "que um produtor tira no campo com o celular. Classes, estágios e condições de captura não foram validados com o parceiro.",
          "6. **Runtime representado.** A inferência roda em Python com TFLite + XNNPACK, configuração que reproduziu o LiteRT.js "
          "CPU/WASM do Chromium desktop nos 18 casos da T10.2. WebGPU (tentado primeiro para o Float16 quando disponível), Safari, "
          "Firefox e Android físico não foram reavaliados; o TensorFlow desta execução pode diferir do usado na T10.2.",
          "7. **Limiar não recalibrado.** A política de confiança foi definida em Keras FP32. Cobertura e acurácia nos aceitos "
          "descrevem o comportamento atual, sem ajuste do limiar no teste.", "",
          "## Reprodução", "",
          "Na raiz do repositório, com o build já gerado em `frontend/dist` e o acervo de imagens contendo `dataset/`:", "",
          "```powershell",
          "python -m src.avaliacao_final_t11_1 --raiz-imagens \"C:\\caminho\\para\\Agro App\"",
          "python -m unittest tests/validar_avaliacao_final_t11_1.py",
          "```", "",
          "O comando recusa build com modelo ou classes divergentes do manifesto, índice diferente do auditado na T10.1, imagem com "
          "hash divergente e runtime que não reproduza os scores do navegador. Não altera modelos, build nem índice. Saídas: este "
          "relatório, `metricas.json` (métricas, matrizes e proveniência), `metricas_por_classe.csv` e `predicoes.csv` "
          "(13 scores por imagem e modelo).", ""]
    return "\n".join(t)


def _rotulo(particao: str) -> str:
    return {"teste": "teste histórico", "validacao": "validação"}[particao]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raiz-imagens", type=Path, required=True)
    parser.add_argument("--build", type=Path, default=BUILD)
    parser.add_argument("--saida", type=Path, default=SAIDA)
    parser.add_argument("--doc", type=Path, default=DOC)
    args = parser.parse_args()
    r = avaliar(args.raiz_imagens, args.build.resolve(), saida=args.saida, doc=args.doc)
    for particao in PARTICOES:
        for formato, m in r["resultados"][particao]["modelos"].items():
            print(f"{particao} {formato}: acurácia {m['integral']['acuracia']:.4f}, F1 macro {m['integral']['f1_macro']:.4f}")


if __name__ == "__main__":
    main()
