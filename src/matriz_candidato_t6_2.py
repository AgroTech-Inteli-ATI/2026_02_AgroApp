"""Publica a matriz do candidato usando somente as previsões salvas na T6.1."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import csv
import io
import json

import numpy as np

from .analise_confusao_t6_2 import gerar_csv
from .avaliacao import calcular_metricas

RAIZ = Path(__file__).resolve().parents[1]
AVALIACAO = RAIZ / "assets/data/avaliacao_T6_1/candidato_T5_6_20261026_keras"
PACOTE = RAIZ / "assets/modelos/candidato_T5_6_20261026"
INDICE = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
SAIDA = RAIZ / "assets/data/avaliacao_T6_2/candidato_T5_6_20261026_keras"
FIGURA = RAIZ / "assets/matriz_confusao_T6_2_candidato_keras.png"


def hash_arquivo(p: Path) -> str:
    return sha256(p.read_bytes()).hexdigest()


def ler_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def ler_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def carregar(avaliacao: Path, pacote: Path, indice: Path) -> dict:
    """Recusa outro modelo/índice, previsões incompletas e matriz inconsistente."""
    fonte = ler_json(avaliacao / "proveniencia_avaliacao.json")
    for nome, esperado in fonte["artefatos_sha256"].items():
        if Path(nome).name != nome or hash_arquivo(avaliacao / nome) != esperado:
            raise ValueError(f"artefato da T6.1 alterado: {nome}")
    manifesto = ler_json(pacote / "manifesto.json")
    metricas = ler_json(avaliacao / "metricas_teste.json")
    if (fonte["manifesto_pacote_sha256"] != hash_arquivo(pacote / "manifesto.json")
            or fonte["modelo_sha256"] != manifesto["sha256"]["modelo.keras"]
            or metricas["sha256"]["modelo"] != fonte["modelo_sha256"]):
        raise ValueError("avaliação não corresponde ao checkpoint selecionado")
    if (metricas["sha256"]["indice_pipeline"] != hash_arquivo(indice)
            or fonte["indice_sha256"] != hash_arquivo(indice)):
        raise ValueError("índice não corresponde à avaliação")
    classes = metricas["teste"]["por_classe"]
    if [c["indice"] for c in classes] != list(range(len(classes))) or not classes:
        raise ValueError("índices das classes inválidos")
    nomes = [c["nome"] for c in classes]
    lista_classes = [{"indice": c["indice"], "nome": c["nome"]} for c in classes]
    if (lista_classes != ler_json(pacote / "classes.json")
            or hash_arquivo(pacote / "classes.json") != manifesto["sha256"]["classes.json"]):
        raise ValueError("ordem das classes diverge do candidato")
    linhas_indice = ler_csv(indice)
    if len({r["image_id"] for r in linhas_indice}) != len(linhas_indice):
        raise ValueError("ID repetido no índice")
    teste = {r["image_id"]: r for r in linhas_indice if r["particao"] == "teste"}
    previsoes = ler_csv(avaliacao / "predicoes_teste.csv")
    ids = [r["image_id"] for r in previsoes]
    if len(set(ids)) != len(ids) or set(ids) != set(teste):
        raise ValueError("previsões devem cobrir exatamente os IDs de teste, sem repetição")
    reais, previstos, erros = [], [], []
    for r in previsoes:
        original = teste[r["image_id"]]
        real, previsto = int(r["indice_real"]), int(r["indice_previsto"])
        if (real != int(original["indice_modelo"]) or not 0 <= real < len(nomes)
                or not 0 <= previsto < len(nomes) or original["nome_classe_modelo"] != nomes[real]):
            raise ValueError("rótulo ou nome da classe incompatível com o índice")
        reais.append(real)
        previstos.append(previsto)
        if real != previsto:
            erros.append({"image_id": r["image_id"], "caminho_relativo": original["caminho_relativo"],
                          "indice_real": real, "classe_real": nomes[real],
                          "indice_previsto": previsto, "classe_prevista": nomes[previsto],
                          "sha256_original": original["sha256_original"]})
    recalculadas = calcular_metricas(np.asarray(reais), np.asarray(previstos), len(nomes), nomes)
    if recalculadas != metricas["teste"]:
        raise ValueError("matriz ou métricas divergem das previsões da T6.1")
    matriz = np.asarray(recalculadas["matriz_confusao"], dtype=int)
    suportes = matriz.sum(axis=1)
    proporcoes = np.divide(matriz, suportes[:, None], out=np.zeros_like(matriz, dtype=float),
                           where=suportes[:, None] != 0)
    pares = [(i, j, int(matriz[i, j]), float(proporcoes[i, j]))
             for i in range(len(nomes)) for j in range(len(nomes)) if i != j and matriz[i, j] > 0]
    pares.sort(key=lambda p: (-p[2], -p[3], p[0], p[1]))
    fontes = {"metricas_teste.json": hash_arquivo(avaliacao / "metricas_teste.json"),
              "predicoes_teste.csv": hash_arquivo(avaliacao / "predicoes_teste.csv"),
              "proveniencia_avaliacao.json": hash_arquivo(avaliacao / "proveniencia_avaliacao.json"),
              "indice": hash_arquivo(indice), "manifesto_candidato": hash_arquivo(pacote / "manifesto.json")}
    return {"nomes": nomes, "matriz": matriz, "suportes": suportes, "proporcoes": proporcoes,
            "pares": pares, "erros": sorted(erros, key=lambda r: r["image_id"]),
            "metricas": recalculadas, "fontes_sha256": fontes,
            "modelo_sha256": fonte["modelo_sha256"], "execucao_t5_5": fonte["execucao_t5_5"]}


def conteudos(dados: dict, minimo: int) -> dict[str, str]:
    if isinstance(minimo, bool) or minimo < 2:
        raise ValueError("o destaque descritivo exige pelo menos dois erros")
    nomes, matriz = dados["nomes"], dados["matriz"]
    repetidos = [p for p in dados["pares"] if p[2] >= minimo]
    contagens = gerar_csv(["classe_real", *nomes], [[n, *linha] for n, linha in zip(nomes, matriz.tolist())])
    normalizada = gerar_csv(["classe_real", *nomes],
        [[n, *[f"{v:.8f}" for v in linha]] for n, linha in zip(nomes, dados["proporcoes"])])
    pares = gerar_csv(["indice_real", "classe_real", "indice_previsto", "classe_prevista",
                       "erros", "suporte_real", "percentual_da_classe", "destacado"],
        [[i, nomes[i], j, nomes[j], q, int(dados["suportes"][i]), f"{100 * p:.6f}",
          "sim" if q >= minimo else "nao"] for i, j, q, p in dados["pares"]])
    fila = io.StringIO(newline="")
    escritor = csv.DictWriter(fila, fieldnames=["image_id", "caminho_relativo", "indice_real",
        "classe_real", "indice_previsto", "classe_prevista", "sha256_original"], lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(dados["erros"])
    texto = ["# Matriz do candidato Keras FP32 — T6.2", "",
             f"Teste exploratório: {int(matriz.sum())} imagens, {len(nomes)} classes, "
             f"{int(np.trace(matriz))} acertos e {len(dados['erros'])} erros.", "",
             "Linhas: classe real. Colunas: classe prevista. Cores: fração da classe real.",
             f"Destaque descritivo: pares direcionais com pelo menos {minimo} erros nesta amostra.",
             "Não demonstra confusão sistemática em dados novos, independência entre fotos ou causa do erro.", "",
             "| Classe real → prevista | Erros | Suporte real | Parcela da classe |",
             "| --- | ---: | ---: | ---: |"]
    texto += [f"| {nomes[i]} → {nomes[j]} | {q} | {int(dados['suportes'][i])} | {100*p:.1f}% |"
              for i, j, q, p in repetidos]
    texto += ["", "Todos os pares, inclusive os de um único erro, estão em pares_confundidos.csv.",
              "Os IDs e caminhos das fotos erradas estão em erros_por_imagem.csv; não há revisão visual ou causa atribuída nesse arquivo.",
              "Não houve nova inferência, treinamento, mudança de pesos ou ajuste de limiar.",
              "O resultado corresponde ao checkpoint Keras, não ao TFLite INT8.",
              "A partição foi consultada historicamente; esta publicação não é avaliação final independente."]
    return {"matriz_contagens.csv": contagens, "matriz_normalizada.csv": normalizada,
            "pares_confundidos.csv": pares, "erros_por_imagem.csv": fila.getvalue(),
            "relatorio_matriz.md": "\n".join(texto) + "\n"}


def plotar(dados: dict, destino: Path, minimo: int) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    nomes = [n.split(" (")[0] for n in dados["nomes"]]
    matriz, proporcoes = dados["matriz"], dados["proporcoes"]
    fig, ax = plt.subplots(figsize=(16, 12), dpi=180)
    mapa = ax.imshow(proporcoes, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(nomes)):
        for j in range(len(nomes)):
            q = int(matriz[i, j])
            if not q:
                continue
            destaque = i != j and q >= minimo
            texto = str(q)
            if destaque:
                texto += f"\n{100*proporcoes[i,j]:.1f}%".replace(".", ",")
                ax.add_patch(Rectangle((j-.48, i-.48), .96, .96, fill=False,
                                       edgecolor="#b45309", linewidth=2))
            ax.text(j, i, texto, ha="center", va="center", fontsize=8.5,
                    color="white" if proporcoes[i,j] >= .48 else "#102342",
                    fontweight="bold" if destaque else "normal")
    ax.set_xticks(range(len(nomes)), nomes, rotation=52, ha="right", fontsize=9)
    ax.set_yticks(range(len(nomes)), [f"{n} (n={s})" for n,s in zip(nomes,dados["suportes"])], fontsize=9)
    ax.set_xticks(np.arange(-.5, len(nomes), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(nomes), 1), minor=True)
    ax.grid(which="minor", color="#d9e0e7", linewidth=.6)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_xlabel("Classe prevista", fontsize=11)
    ax.set_ylabel("Classe real", fontsize=11)
    ax.set_title(f"EfficientNet-Lite0 | Candidato Keras FP32\nTeste exploratório: {int(matriz.sum())} imagens — T6.2",
                 fontsize=15, pad=18)
    fig.colorbar(mapa, ax=ax, fraction=.036, pad=.025).set_label("Fração da classe real")
    ax.legend(handles=[Patch(facecolor="none", edgecolor="#b45309", linewidth=2,
              label=f"Pares com ≥ {minimo} erros nesta amostra: contagem e % da classe real")],
              loc="upper center", bbox_to_anchor=(.5, -.31), frameon=False, fontsize=9)
    fig.subplots_adjust(left=.28, right=.92, top=.90, bottom=.32)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, bbox_inches="tight", pad_inches=.2, facecolor="white")
    plt.close(fig)


def executar(avaliacao: Path = AVALIACAO, pacote: Path = PACOTE, indice: Path = INDICE,
             saida: Path = SAIDA, figura: Path = FIGURA, minimo: int = 2, verificar: bool = False) -> dict:
    dados = carregar(avaliacao, pacote, indice)
    arquivos = conteudos(dados, minimo)
    prova = {"esquema": "matriz_candidato_T6_2_v1", "formato_avaliado": "Keras FP32",
             "modelo_sha256": dados["modelo_sha256"], "execucao_t5_5": dados["execucao_t5_5"],
             "fontes_sha256": dados["fontes_sha256"], "minimo_erros_destaque": minimo,
             "total_imagens": int(dados["matriz"].sum()), "acertos": int(np.trace(dados["matriz"])),
             "erros": len(dados["erros"]), "inferencia_repetida": False,
             "tipo_avaliacao": "exploratoria", "codigo_sha256": hash_arquivo(Path(__file__))}
    if verificar:
        for nome, texto in arquivos.items():
            if (saida / nome).read_text(encoding="utf-8") != texto:
                raise ValueError(f"artefato divergente: {nome}")
        prova["artefatos_sha256"] = {n: hash_arquivo(saida / n) for n in arquivos}
        prova["figura_sha256"] = hash_arquivo(figura)
        if ler_json(saida / "proveniencia.json") != prova:
            raise ValueError("proveniência ou figura divergente")
    else:
        saida.mkdir(parents=True, exist_ok=True)
        for nome, texto in arquivos.items():
            (saida / nome).write_text(texto, encoding="utf-8")
        plotar(dados, figura, minimo)
        prova["artefatos_sha256"] = {n: hash_arquivo(saida / n) for n in arquivos}
        prova["figura_sha256"] = hash_arquivo(figura)
        (saida / "proveniencia.json").write_text(json.dumps(prova, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return prova


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for nome, padrao in (("avaliacao", AVALIACAO), ("pacote", PACOTE), ("indice", INDICE),
                         ("saida", SAIDA), ("figura", FIGURA)):
        p.add_argument("--" + nome, type=Path, default=padrao)
    p.add_argument("--minimo-erros", type=int, default=2)
    p.add_argument("--verificar", action="store_true")
    a = p.parse_args()
    resultado = executar(a.avaliacao, a.pacote, a.indice, a.saida, a.figura, a.minimo_erros, a.verificar)
    print(f"T6.2: {resultado['total_imagens']} imagens, {resultado['acertos']} acertos, "
          f"{resultado['erros']} erros; {'verificado' if a.verificar else 'publicado'}.")


if __name__ == "__main__":
    main()
