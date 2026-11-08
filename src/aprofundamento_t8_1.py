"""Publica gráficos e a inspeção visual dos sete acertos perdidos pelo INT8 oficial.

Usa os resultados consolidados da T8.1, sem nova inferência. As fotos originais
permanecem externas; são publicadas cópias redimensionadas em fotos/, pranchas de
revisão, gráficos, CSVs e relatório visual.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import textwrap

import numpy as np
from PIL import Image, ImageOps

from src import avaliacao_pos_conversao_t8_1 as a
from src.preprocessamento import preparar_imagem

BASE = a.SAIDA
ANOTACOES = BASE / "anotacoes_visuais_int8.json"
SAIDA = BASE / "aprofundamento"
MATRIZES_FIGURAS = ("keras", "int8_t7_3")
FATORES = {"sujeito_pequeno", "sujeito_muito_pequeno", "fundo_detalhado", "corpo_visivel",
           "sujeito_escuro", "fundo_dominante", "fundo_floral", "baixo_contraste_local",
           "oclusao_parcial", "formato_vertical", "fundo_foliar", "fundo_texturizado",
           "imagem_composta", "texto_incorporado", "moldura_colorida", "duas_vistas_de_insetos",
           "adulto_alado_aparente", "corpo_grande_no_quadro", "cores_semelhantes_ao_fundo"}
HIPOTESES = {"sensibilidade_a_detalhes_finos", "influencia_do_fundo", "oclusao",
             "conteudo_composto", "semelhanca_visual", "variacao_de_estagio"}


def carregar(base=BASE, anotacoes=ANOTACOES) -> dict:
    prov = a.ler_json(base / "proveniencia.json")
    if (prov.get("esquema") != "avaliacao_pos_conversao_T8_1_v1"
            or prov.get("referencia_principal") != "keras" or prov.get("particao") != "teste"):
        raise ValueError("proveniência T8.1 incompatível")
    for nome, h in prov["artefatos_sha256"].items():
        p = (base / nome).resolve()
        if not p.is_relative_to(base.resolve()):
            raise ValueError("artefato fora da pasta da avaliação")
        a.conferir_hash(p, h)
    dados = a.carregar()
    contrato_execucao = a.ler_json(a.COMPARACAO / "comparacao.json")
    a.conferir_hash(a.RAIZ / "src/preprocessamento.py", contrato_execucao["codigo_sha256"]["src/preprocessamento.py"])
    if prov["image_ids"] != dados["ids"] or prov["classes"] != dados["proveniencia"]["classes"]:
        raise ValueError("avaliação publicada não corresponde às fontes")
    gerais, classes, predicoes, mudancas = a.comparar(dados)
    for nome, linhas in (("metricas_gerais.csv", gerais), ("comparacao_por_classe.csv", classes),
                         ("predicoes_teste.csv", predicoes), ("mudancas_por_imagem.csv", mudancas)):
        # Compara semanticamente os CSVs publicados com a consolidação validada.
        if a.ler_csv(base / nome) != list_csv(a.csv_texto(linhas)):
            raise ValueError(f"publicação T8.1 diverge das fontes: {nome}")
    perdidos = [r for r in mudancas if r["versao"] == "int8_t7_3" and r["tipo"] == "acerto_perdido"]
    notas = a.ler_json(anotacoes)
    if notas.get("esquema") != "anotacoes_visuais_T8_1_v1":
        raise ValueError("esquema das anotações incompatível")
    validar_anotacoes(notas["anotacoes"], perdidos)
    dados.update(perdidos=perdidos, anotacoes=notas, classes_comparadas=classes)
    return dados


def list_csv(texto: str) -> list[dict]:
    import csv
    import io
    return list(csv.DictReader(io.StringIO(texto)))


def validar_anotacoes(notas: dict, perdidos: list[dict]) -> None:
    if set(notas) != {r["image_id"] for r in perdidos}:
        raise ValueError("anotações devem cobrir exatamente os acertos perdidos pelo INT8 oficial")
    for image_id, n in notas.items():
        if (not n["fatores_observados"] or not set(n["fatores_observados"]) <= FATORES
                or not set(n["hipoteses"]) <= HIPOTESES
                or any(not n[k].strip() for k in ("observacao_original", "observacao_entrada", "verificacao_sugerida"))):
            raise ValueError(f"anotação incompleta ou categoria desconhecida: {image_id}")


def resolver_imagens(raiz: Path, dados: dict) -> dict[str, Path]:
    """Aceita a estrutura original dataset/ e a coleção exportada por image_id."""
    arquivos = None
    caminhos = {}
    for r in dados["perdidos"]:
        image_id = r["image_id"]
        original = dados["indice"][image_id]
        relativo = Path(original["caminho_relativo"])
        candidatos = [raiz / relativo, raiz / f"{image_id}.jpg"]
        if relativo.parts and relativo.parts[0] == raiz.name:
            candidatos.append(raiz.joinpath(*relativo.parts[1:]))
        if not any(p.is_file() for p in candidatos):
            if arquivos is None:
                arquivos = list(raiz.rglob("*"))
            candidatos += [p for p in arquivos if p.is_file() and
                           (p.name.startswith(image_id + "__") or p.name == relativo.name)]
        existentes = [p for p in candidatos if p.is_file()]
        certos = [p for p in existentes if a.hash_arquivo(p) == original["sha256_original"]]
        if not certos:
            raise ValueError(f"foto ausente ou hash divergente: {image_id}")
        caminhos[image_id] = certos[0]
    return caminhos


def matrizes_normalizadas(dados: dict) -> tuple[dict, list[dict]]:
    matrizes, linhas = {}, []
    for n in a.VERSOES:
        matriz = np.asarray(dados["metricas"][n]["matriz_confusao"], dtype=int)
        suporte = matriz.sum(axis=1)
        proporcoes = np.divide(matriz, suporte[:, None], out=np.zeros_like(matriz, dtype=float),
                               where=suporte[:, None] != 0)
        matrizes[n] = proporcoes
        for i in range(len(suporte)):
            for j in range(len(suporte)):
                linhas.append({"versao": n, "indice_real": i, "indice_previsto": j,
                               "contagem": int(matriz[i, j]), "suporte_real": int(suporte[i]),
                               "percentual_da_classe_real": 100 * float(proporcoes[i, j])})
    return matrizes, linhas


def configurar_graficos():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "figure.facecolor": "white",
                         "savefig.facecolor": "white", "axes.titleweight": "bold"})
    return plt


def plotar_matrizes(dados, matrizes, pasta, plt):
    nomes = [f"{i:02d}  {n.split(' (')[0]}  (n={dados['metricas']['keras']['por_classe'][i]['suporte']})"
             for i, n in enumerate(dados["nomes"])]
    for n in MATRIZES_FIGURAS:
        fig, ax = plt.subplots(figsize=(12.5, 9.8))
        matriz = matrizes[n]
        im = ax.imshow(matriz, cmap="Blues", vmin=0, vmax=1)
        for i, j in zip(*np.nonzero(matriz)):
            percentual = f"{100 * matriz[i,j]:.1f}%".replace(".", ",")
            ax.text(j, i, percentual, ha="center", va="center",
                    color="white" if matriz[i,j] > .55 else "#15334b", fontsize=8.5)
        ax.set(xticks=range(13), yticks=range(13), yticklabels=nomes,
               xlabel="Classe prevista (índice)", ylabel="Classe real e suporte")
        ax.tick_params(axis="both", length=0, pad=8)
        ax.set_xticks(np.arange(-.5, 13, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 13, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=.7)
        ax.tick_params(which="minor", bottom=False, left=False)
        fig.suptitle(f"Matriz de confusão — {a.ROTULOS[n]}", fontsize=18, x=.04, ha="left", y=.97)
        fig.text(.04, .91, "Teste exploratório · 473 imagens · 13 classes · normalização por classe real", fontsize=11, color="#425466")
        fig.subplots_adjust(left=.35, right=.87, top=.84, bottom=.12)
        cax = fig.add_axes([.90, .24, .018, .50])
        barra = fig.colorbar(im, cax=cax, ticks=[0, .25, .5, .75, 1])
        barra.ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        barra.set_label("Parcela da classe real")
        fig.text(.04, .035, "n = suporte da classe. Diagonal: recall. Percentuais arredondados; linhas completas somam 100%.", fontsize=10, color="#425466")
        fig.savefig(pasta / f"matriz_{n}.png", dpi=160)
        plt.close(fig)


def plotar_f1(dados, pasta, plt):
    from matplotlib.colors import TwoSlopeNorm
    versoes = a.VERSOES[1:]
    tabela = {(r["versao"], r["indice"]): r for r in dados["classes_comparadas"]}
    valores = np.array([[tabela[n, i]["delta_f1_vs_keras_pp"] for n in versoes] for i in range(13)])
    limite = max(1, float(np.ceil(np.abs(valores).max())))
    fig, ax = plt.subplots(figsize=(13.5, 10))
    im = ax.imshow(valores, cmap="BrBG", norm=TwoSlopeNorm(vmin=-limite, vcenter=0, vmax=limite), aspect="auto")
    for i in range(13):
        for j in range(len(versoes)):
            v = valores[i, j]
            ax.text(j, i, (f"{v:+.2f}" if v else "0,00").replace(".", ","), ha="center", va="center",
                    color="white" if abs(v) > limite * .55 else "#182b34", fontsize=11, fontweight="bold" if j == 3 else "normal")
    nomes = [f"{i:02d}  {n.split(' (')[0]}  (n={dados['metricas']['keras']['por_classe'][i]['suporte']})"
             for i, n in enumerate(dados["nomes"])]
    ax.set(yticks=range(13), yticklabels=nomes, xticks=range(5),
           xticklabels=["FP32\nT7.1", "Faixa\ndinâmica", "Float16", "INT8 oficial\nT7.3", "INT8 regenerado\nT7.2"])
    ax.tick_params(axis="both", length=0, pad=9)
    ax.set_xticks(np.arange(-.5, 5, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 13, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for borda in ax.spines.values():
        borda.set_visible(False)
    fig.suptitle("Variação de F1 por classe após a conversão", x=.035, y=.975, ha="left", fontsize=20)
    fig.text(.035, .931, "Variação de F1 frente ao Keras, em pontos percentuais · teste exploratório: 473 imagens", fontsize=11, color="#425466")
    fig.subplots_adjust(left=.40, right=.87, top=.87, bottom=.12)
    cax = fig.add_axes([.90, .25, .02, .50])
    fig.colorbar(im, cax=cax).set_label("Δ F1 (p.p.): negativo = perda; positivo = ganho")
    fig.text(.035, .035, "n = suporte da classe. Valores pontuais nesta amostra; não comprovam significância ou equivalência estatística.", fontsize=10, color="#425466")
    fig.savefig(pasta / "delta_f1_por_classe.png", dpi=160)
    plt.close(fig)


def pranchas(dados, caminhos, pasta, plt):
    for inicio in range(0, len(dados["perdidos"]), 4):
        lote = dados["perdidos"][inicio:inicio + 4]
        fig = plt.figure(figsize=(16, 13))
        for pos, r in enumerate(lote):
            linha, coluna = divmod(pos, 2)
            x0, topo = .025 + coluna * .50, .97 - linha * .48
            image_id = r["image_id"]
            nome = dados["nomes"][r["indice_real"]].split(" (")[0]
            destino = dados["nomes"][r["previsto_convertido"]].split(" (")[0]
            nota = dados["anotacoes"]["anotacoes"][image_id]
            fig.text(x0, topo, f"{image_id} · rótulo real: {nome}", fontsize=12, va="top")
            eixos = [fig.add_axes([x0 + deslocamento, topo - .345, .215, .29]) for deslocamento in (0, .24)]
            with Image.open(caminhos[image_id]) as foto:
                original = ImageOps.exif_transpose(foto).convert("RGB")
                eixos[0].imshow(original)
            eixos[1].imshow(preparar_imagem(caminhos[image_id]), interpolation="nearest")
            for ax, titulo in zip(eixos, ("Original (vista geral)", "Entrada T4.1 · 224 × 224")):
                ax.set_title(titulo, fontsize=10, color="#425466")
                ax.axis("off")
            fig.text(x0, topo - .367, f"Keras: {nome}\nINT8 oficial: {destino}", fontsize=9, fontweight="bold", va="top")
            fig.text(x0, topo - .410, textwrap.fill(nota["observacao_entrada"], 95), fontsize=9, va="top")
        fig.text(.025, .008, "Acervo de Dados do projeto. Originais conferidos por SHA-256; entrada conforme T4.1. Observações preliminares.", fontsize=10, color="#425466")
        fig.savefig(pasta / f"revisao_visual_{inicio // 4 + 1:02d}.png", dpi=120)
        plt.close(fig)


def executar(raiz_imagens: Path, saida=SAIDA, base=BASE, anotacoes=ANOTACOES):
    if saida.exists():
        raise ValueError("saída já existe; preservar o aprofundamento anterior")
    dados = carregar(base, anotacoes)
    caminhos = resolver_imagens(raiz_imagens, dados)
    matrizes, linhas_matriz = matrizes_normalizadas(dados)
    # Só publica após validar todas as fontes, fotos e anotações.
    saida.mkdir(parents=True, exist_ok=False)
    figuras, folhas, fotos = saida / "figuras", saida / "pranchas", saida / "fotos"
    figuras.mkdir()
    folhas.mkdir()
    fotos.mkdir()
    for image_id, caminho in caminhos.items():
        with Image.open(caminho) as foto:
            previa = ImageOps.exif_transpose(foto).convert("RGB")
            previa.thumbnail((640, 640), Image.Resampling.LANCZOS)
            previa.save(fotos / f"{image_id}.jpg", quality=92)
    plt = configurar_graficos()
    import matplotlib
    import PIL
    plotar_matrizes(dados, matrizes, figuras, plt)
    plotar_f1(dados, figuras, plt)
    pranchas(dados, caminhos, folhas, plt)
    linhas = []
    for pos, r in enumerate(dados["perdidos"]):
        image_id = r["image_id"]
        nota = dados["anotacoes"]["anotacoes"][image_id]
        with Image.open(caminhos[image_id]) as foto:
            w, h = ImageOps.exif_transpose(foto).size
        escala = 224 / max(w, h)
        area = max(1, round(w * escala)) * max(1, round(h * escala))
        linhas.append({**r, "classe_real": dados["nomes"][r["indice_real"]],
                       "classe_keras": dados["nomes"][r["previsto_keras"]],
                       "classe_int8_oficial": dados["nomes"][r["previsto_convertido"]],
                       "caminho_relativo_original": dados["indice"][image_id]["caminho_relativo"],
                       "sha256_original": dados["indice"][image_id]["sha256_original"],
                       "largura_original": w, "altura_original": h, "fracao_padding_entrada": 1 - area / 224 ** 2,
                       "fatores_observados": ";".join(nota["fatores_observados"]),
                       "observacao_original": nota["observacao_original"], "observacao_entrada": nota["observacao_entrada"],
                       "hipoteses": ";".join(nota["hipoteses"]), "status_causa": "hipotese_nao_confirmada",
                       "validacao_taxonomica": "pendente", "verificacao_sugerida": nota["verificacao_sugerida"],
                       "prancha": f"pranchas/revisao_visual_{pos // 4 + 1:02d}.png",
                       "foto_documentacao": f"fotos/{image_id}.jpg"})
    (saida / "revisao_visual.csv").write_text(a.csv_texto(linhas), encoding="utf-8", newline="")
    (saida / "matrizes_normalizadas.csv").write_text(a.csv_texto(linhas_matriz), encoding="utf-8", newline="")
    texto = ["# Revisão visual dos acertos perdidos pelo INT8 oficial — T8.1", "",
             dados["anotacoes"]["metodo"], "", dados["anotacoes"]["limites"], "",
             "Foram inspecionados todos os sete casos selecionados pelas previsões, sem seleção por aparência. "
             "Os originais foram conferidos por SHA-256; cada caso foi observado também após T4.1. "
             "O rótulo real é o histórico do dataset, sem revalidação de espécie.", "",
             "| ID | Rótulo real / Keras | INT8 oficial | Observação na entrada |",
             "| --- | --- | --- | --- |"]
    for r in linhas:
        texto.append(f"| {r['image_id']} | {r['classe_real']} | {r['classe_int8_oficial']} | {r['observacao_entrada']} |")
    texto += ["", "## Imagens inspecionadas", "",
              "Fonte: acervo de Dados do projeto. As cópias abaixo foram redimensionadas, sem recorte, "
              "para apresentação; não substituem os originais conferidos por SHA-256 nem a entrada T4.1.", ""]
    for r in linhas:
        texto += [f"### {r['image_id']}", "",
                  f"![{r['image_id']}: imagem inspecionada]({r['foto_documentacao']})", "",
                  f"Rótulo histórico e Keras: {r['classe_real']}. INT8 oficial: {r['classe_int8_oficial']}.", ""]
    texto += ["", "## Fotos originais e entradas do modelo", "",
              "![Casos 1 a 4: original e entrada T4.1](pranchas/revisao_visual_01.png)", "",
              "![Casos 5 a 7: original e entrada T4.1](pranchas/revisao_visual_02.png)", "",
              "O arquivo revisao_visual.csv reúne observações, hipóteses, hashes e verificações sugeridas. "
              "IMG_02168 contém uma montagem com texto; IMG_02637 apresenta um adulto alado aparente. "
              "Ambos os casos ficam registrados para revisão da frente de Dados. Os rótulos do teste foram preservados.", "",
              "## Gráficos", ""]
    for numero, n in enumerate(MATRIZES_FIGURAS, 1):
        texto += [f"### Figura {numero} — Matriz de confusão: {a.ROTULOS[n]}", "",
                  f"![Matriz normalizada: {a.ROTULOS[n]}](figuras/matriz_{n}.png)", "",
                  "Fonte: previsões da T7.2, consolidadas na T8.1 (2026).", ""]
    texto += ["![Variação de F1 por classe](figuras/delta_f1_por_classe.png)", "",
              "As matrizes são normalizadas por linha e usam a mesma escala de cores. "
              "O mapa de F1 inclui as cinco conversões frente ao Keras, em pontos percentuais. "
              "Suporte e valores exatos estão nos CSVs; os gráficos não indicam significância estatística.", ""]
    (saida / "relatorio_visual.md").write_text("\n".join(texto), encoding="utf-8", newline="")
    prov = {"esquema": "aprofundamento_T8_1_v1", "data_utc": datetime.now(timezone.utc).isoformat(),
            "nova_inferencia": False, "revisao_visual_realizada": True, "validacao_taxonomica": "pendente",
            "modelo_revisado": "int8_t7_3", "image_ids": [r["image_id"] for r in linhas],
            "metodo": dados["anotacoes"]["metodo"],
            "apoio_revisao": dados["anotacoes"]["apoio_revisao"],
            "ambiente": {"numpy": np.__version__, "matplotlib": matplotlib.__version__, "pillow": PIL.__version__},
            "fontes_sha256": {a.caminho_registrado(p): a.hash_arquivo(p) for p in
                              (base / "proveniencia.json", base / "mudancas_por_imagem.csv", base / "comparacao_por_classe.csv", anotacoes)},
            "originais_sha256": {r["image_id"]: r["sha256_original"] for r in linhas},
            "codigo_sha256": {f"src/{n}": a.hash_arquivo(a.RAIZ / "src" / n) for n in
                               ("aprofundamento_t8_1.py", "preprocessamento.py", "avaliacao_pos_conversao_t8_1.py")},
            "artefatos_sha256": {p.relative_to(saida).as_posix(): a.hash_arquivo(p) for p in sorted(saida.rglob("*")) if p.is_file()},
            "limites": dados["anotacoes"]["limites"]}
    (saida / "proveniencia_aprofundamento.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    return dados


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raiz-imagens", required=True, type=Path)
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument("--base", type=Path, default=BASE)
    p.add_argument("--anotacoes", type=Path, default=ANOTACOES)
    args = p.parse_args()
    dados = executar(**vars(args))
    print(f"T8.1: {len(dados['perdidos'])} fotos revisadas; gráficos e pranchas publicados.")


if __name__ == "__main__":
    main()
