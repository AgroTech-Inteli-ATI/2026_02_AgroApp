"""Documenta imagens reais de treino e calibra o candidato selecionado em INT8."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import random
import tempfile

import numpy as np
from PIL import Image, ImageOps

from src.conversao_t7_1 import PACOTE, RAIZ, _hash, _validar_selecao
from src.preprocessamento import preparar_imagem

INDICE = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
CONJUNTO = RAIZ / "assets/data/calibracao_T7_3"
SAIDA = RAIZ / "assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026"
FAIXAS = ("baixo_brilho", "brilho_intermediario", "alto_brilho")
CONDICOES = {"sombra_ou_baixa_luz", "luz_difusa", "luz_direta_ou_realces", "iluminacao_mista", "nao_inferivel"}


def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def gravar(p, valor):
    Path(p).write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def ler_csv(p):
    with Path(p).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def texto_csv(linhas):
    s = io.StringIO(newline="")
    w = csv.DictWriter(s, fieldnames=list(linhas[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(linhas)
    return s.getvalue()


def indice_selecionado(indice: Path, pacote: Path) -> tuple[list, list, dict]:
    manifesto = ler(pacote / "manifesto.json")
    if manifesto["indice_sha256"] != _hash(indice):
        raise ValueError("índice não corresponde à seleção T5.6")
    classes = ler(pacote / "classes.json")
    if _hash(pacote / "classes.json") != manifesto["sha256"]["classes.json"]:
        raise ValueError("classes do pacote alteradas")
    if len(classes) != 13 or [c["indice"] for c in classes] != list(range(13)):
        raise ValueError("esperadas as 13 classes do MVP em ordem")
    linhas = ler_csv(indice)
    if len({r["image_id"] for r in linhas}) != len(linhas):
        raise ValueError("IDs repetidos no índice")
    grupos, hashes = {}, {}
    for r in linhas:
        i = int(r["indice_modelo"])
        if not 0 <= i < 13 or r["nome_classe_modelo"] != classes[i]["nome"]:
            raise ValueError("classe do índice incompatível")
        if r["particao"] not in {"treino", "validacao", "teste"}:
            raise ValueError("partição inválida")
        for campo, mapa in (("grupo_particao", grupos), ("sha256_original", hashes)):
            v = r[campo]
            if not v or v in mapa and mapa[v] != r["particao"]:
                raise ValueError("grupo ou imagem compartilhado entre partições")
            mapa[v] = r["particao"]
    return linhas, classes, manifesto


def medir_imagem(caminho: Path, tamanho: int = 224) -> tuple[np.ndarray, float, str]:
    """Brilho no conteúdo redimensionado; exclui o padding cinza da estatística."""
    with Image.open(caminho) as original:
        im = ImageOps.exif_transpose(original).convert("RGB")
        x = preparar_imagem(im, tamanho)
        escala = tamanho / max(im.size)
        w, h = max(1, round(im.width * escala)), max(1, round(im.height * escala))
    left, top = (tamanho - w) // 2, (tamanho - h) // 2
    conteudo = x[top:top+h, left:left+w]
    y = float(np.mean(conteudo @ np.array([.2126, .7152, .0722], dtype=np.float32)))
    faixa = FAIXAS[0] if y < .30 else FAIXAS[1] if y < .60 else FAIXAS[2]
    return x, y, faixa


def selecionar(catalogo: list[dict], total: int = 200, semente: int = 42) -> list[dict]:
    """Equilibra classes, alterna brilho e evita repetir grupos e imagens."""
    if isinstance(total, bool) or not isinstance(total, int) or total < 13:
        raise ValueError("total deve cobrir as 13 classes")
    rng = random.Random(semente)
    usados, hashes, selecionadas = set(), set(), []
    for i in range(13):
        quota = total // 13 + int(i < total % 13)
        candidatos = sorted((r for r in catalogo if int(r["indice_modelo"]) == i), key=lambda r: r["image_id"])
        rng.shuffle(candidatos)
        caixas = {f: [r for r in candidatos if r["faixa_brilho"] == f] for f in FAIXAS}
        fotos = []
        while len(fotos) < quota:
            avancou = False
            for faixa in FAIXAS:
                r = next((r for r in caixas[faixa] if r["grupo_particao"] not in usados
                          and r["sha256_original"] not in hashes), None)
                if r is not None:
                    fotos.append(r)
                    usados.add(r["grupo_particao"])
                    hashes.add(r["sha256_original"])
                    avancou = True
                if len(fotos) == quota:
                    break
            if not avancou:
                raise ValueError(f"grupos distintos insuficientes para a classe {i}")
        selecionadas.extend(fotos)
    return sorted(selecionadas, key=lambda r: (int(r["indice_modelo"]), r["image_id"]))


def preparar(raiz: Path, saida: Path = CONJUNTO, indice: Path = INDICE,
             pacote: Path = PACOTE, total: int = 200, semente: int = 42) -> dict:
    if saida.exists():
        raise ValueError("conjunto já existe; preservar a seleção e escolher outra saída")
    linhas, classes, modelo = indice_selecionado(indice, pacote)
    catalogo = []
    for r in linhas:
        if r["particao"] != "treino":
            continue
        caminho = raiz / r["caminho_relativo"]
        if _hash(caminho) != r["sha256_original"]:
            raise ValueError(f"imagem original alterada: {r['image_id']}")
        x, brilho, faixa = medir_imagem(caminho)
        catalogo.append({**{k: r[k] for k in ("image_id", "caminho_relativo", "sha256_original",
            "indice_modelo", "nome_classe_modelo", "grupo_particao", "particao")},
            "origem": "field" if r["caminho_relativo"].startswith("dataset/field/") else "agroinsect",
            "brilho_medio_sem_padding": f"{brilho:.8f}", "faixa_brilho": faixa,
            "entrada_float32_sha256": sha256(x.tobytes()).hexdigest()})
    escolhidas = selecionar(catalogo, total, semente)
    cobertura = []
    for c in classes:
        disponiveis = [r for r in catalogo if int(r["indice_modelo"]) == c["indice"]]
        fotos = [r for r in escolhidas if int(r["indice_modelo"]) == c["indice"]]
        cobertura.append({**c, "treino_disponivel": len(disponiveis), "selecionadas": len(fotos),
            "grupos_distintos": len({r["grupo_particao"] for r in fotos}),
            "faixas_disponiveis": dict(Counter(r["faixa_brilho"] for r in disponiveis)),
            "faixas_selecionadas": dict(Counter(r["faixa_brilho"] for r in fotos)),
            "origens": dict(Counter(r["origem"] for r in fotos))})
    manifesto_csv = texto_csv(escolhidas)
    conjunto = {"esquema": "conjunto_calibracao_T7_3_v1", "total": len(escolhidas),
        "particao": "treino", "semente": semente, "augmentation": False,
        "origem": "imagens reais do acervo indexado pela preparação de Dados T4.2/T4.5; seleção documentada na T7.3",
        "indice_sha256": _hash(indice), "classes_sha256": _hash(pacote / "classes.json"),
        "modelo_keras_sha256": modelo["sha256"]["modelo.keras"],
        "manifesto_csv_sha256": sha256(manifesto_csv.encode()).hexdigest(),
        "preprocessamento_sha256": _hash(RAIZ / "src/preprocessamento.py"),
        "entrada": {"shape": [1,224,224,3], "dtype": "float32", "faixa": [0,1]},
        "amostragem": "quotas por classe (15 ou 16 em 200), alternância entre faixas de brilho disponíveis, um arquivo por grupo e hash, sem reposição",
        "brilho": {"estatistica": "média de 0.2126 R + 0.7152 G + 0.0722 B no conteúdo RGB redimensionado, sem padding; canais em [0,1]",
            "limites": {"baixo_brilho": "Y < 0.30", "brilho_intermediario": "0.30 <= Y < 0.60", "alto_brilho": "Y >= 0.60"},
            "limite_interpretacao": "proxy de brilho da imagem, afetado pelo fundo e cor do sujeito; não determina iluminação física; exige revisão visual documentada"},
        "cobertura_classes": cobertura, "faixas_selecionadas": dict(Counter(r["faixa_brilho"] for r in escolhidas)),
        "revisao_frente_dados": "não registrada para esta seleção específica; as fontes são as mesmas do índice versionado",
        "teste_acessado": False, "validacao_acessada": False}
    saida.mkdir(parents=True)
    (saida / "manifesto_calibracao.csv").write_text(manifesto_csv, encoding="utf-8")
    gravar(saida / "conjunto.json", conjunto)
    return conjunto


def validar_revisao(revisao: dict, fotos: list[dict]) -> None:
    por_id = {r["image_id"]: r for r in fotos}
    vistos, classes, condicoes = set(), set(), set()
    for a in revisao["imagens"]:
        id_ = a["image_id"]
        if id_ not in por_id or id_ in vistos or a["sha256_original"] != por_id[id_]["sha256_original"]:
            raise ValueError("revisão visual contém imagem ausente, repetida ou alterada")
        if not a["condicoes"] or not set(a["condicoes"]) <= CONDICOES or not a["observacao"].strip():
            raise ValueError("revisão visual sem condição ou observação válida")
        vistos.add(id_)
        classes.add(int(por_id[id_]["indice_modelo"]))
        condicoes.update(a["condicoes"])
    if classes != set(range(13)) or not {"sombra_ou_baixa_luz", "luz_difusa", "luz_direta_ou_realces"} <= condicoes:
        raise ValueError("revisão deve cobrir 13 classes e sombra, luz difusa e luz direta/realces")


def carregar_conjunto(raiz: Path, conjunto: Path, indice: Path = INDICE, pacote: Path = PACOTE):
    linhas, classes, modelo = indice_selecionado(indice, pacote)
    prova = ler(conjunto / "conjunto.json")
    if (prova["indice_sha256"] != _hash(indice) or prova["classes_sha256"] != _hash(pacote / "classes.json")
            or prova["modelo_keras_sha256"] != modelo["sha256"]["modelo.keras"]
            or prova["preprocessamento_sha256"] != _hash(RAIZ / "src/preprocessamento.py")
            or prova["manifesto_csv_sha256"] != _hash(conjunto / "manifesto_calibracao.csv")
            or prova["augmentation"] is not False or prova["particao"] != "treino"):
        raise ValueError("proveniência do conjunto incompatível")
    fotos = ler_csv(conjunto / "manifesto_calibracao.csv")
    if (len(fotos) != prova["total"] or len({r["image_id"] for r in fotos}) != len(fotos)
            or len({r["grupo_particao"] for r in fotos}) != len(fotos)
            or len({r["sha256_original"] for r in fotos}) != len(fotos)
            or {int(r["indice_modelo"]) for r in fotos} != set(range(13))):
        raise ValueError("conjunto incompleto ou com imagens/grupos repetidos")
    if prova["entrada"] != {"shape": [1,224,224,3], "dtype": "float32", "faixa": [0,1]}:
        raise ValueError("contrato de entrada do conjunto incompatível")
    if prova["faixas_selecionadas"] != dict(Counter(r["faixa_brilho"] for r in fotos)):
        raise ValueError("cobertura de brilho divergente")
    for c in classes:
        rows = [r for r in fotos if int(r["indice_modelo"]) == c["indice"]]
        cobertura = next((v for v in prova["cobertura_classes"] if v["indice"] == c["indice"]), None)
        if (cobertura is None or cobertura["nome"] != c["nome"] or cobertura["selecionadas"] != len(rows)
                or cobertura["grupos_distintos"] != len(rows)
                or cobertura["faixas_selecionadas"] != dict(Counter(r["faixa_brilho"] for r in rows))
                or cobertura["origens"] != dict(Counter(r["origem"] for r in rows))):
            raise ValueError("cobertura por classe divergente")
    originais = {r["image_id"]: r for r in linhas}
    imagens = []
    for r in fotos:
        original = originais.get(r["image_id"])
        if original is None or any(r[k] != original[k] for k in ("caminho_relativo", "sha256_original", "grupo_particao", "particao", "indice_modelo", "nome_classe_modelo")) or original["particao"] != "treino":
            raise ValueError("calibração só aceita fotos do treino original, sem alteração de rótulo")
        caminho = raiz / r["caminho_relativo"]
        if _hash(caminho) != r["sha256_original"]:
            raise ValueError(f"imagem original alterada: {r['image_id']}")
        x, brilho, faixa = medir_imagem(caminho)
        if (sha256(x.tobytes()).hexdigest() != r["entrada_float32_sha256"]
                or f"{brilho:.8f}" != r["brilho_medio_sem_padding"] or faixa != r["faixa_brilho"]):
            raise ValueError("entrada ou medida de brilho divergente")
        imagens.append(x)
    revisao = ler(conjunto / "revisao_iluminacao.json")
    validar_revisao(revisao, fotos)
    return fotos, imagens, prova, classes, revisao


def tensor_int8(detalhe):
    escala, zero = detalhe["quantization"]
    if detalhe["dtype"] != np.int8 or not np.isfinite(escala) or escala <= 0:
        raise ValueError("tensor sem contrato INT8 válido")
    return {"nome": detalhe["name"], "indice": int(detalhe["index"]),
            "shape": detalhe["shape"].tolist(), "shape_signature": detalhe["shape_signature"].tolist(),
            "dtype": "int8", "escala": float(escala), "zero_point": int(zero)}


def quantizar(x, escala, zero):
    return np.clip(np.rint(x / escala) + zero, -128, 127).astype(np.int8)


def converter(raiz: Path, conjunto: Path = CONJUNTO, saida: Path = SAIDA,
              indice: Path = INDICE, pacote: Path = PACOTE) -> dict:
    if saida.exists():
        raise ValueError("saída já existe; preservar conversões anteriores")
    metricas = ler(pacote / "avaliacao_validacao.json")
    origem = _validar_selecao(pacote / "modelo.keras", pacote / "avaliacao_validacao.json", metricas["validacao"]["por_classe"], pacote)
    fotos, imagens, prova, classes, revisao = carregar_conjunto(raiz, conjunto, indice, pacote)
    import tensorflow as tf
    from tensorflow.lite.python import schema_py_generated as schema
    from src.avaliacao_t6_1 import _carregar_modelo
    modelo = _carregar_modelo(pacote / "modelo.keras")
    if tuple(modelo.input_shape[1:]) != (224,224,3) or tuple(modelo.output_shape[1:]) != (13,):
        raise ValueError("contrato do candidato incompatível")
    consumidas = []

    def representativo():
        for r, x in zip(fotos, imagens):
            consumidas.append(r["image_id"])
            yield [x[None]]

    conversor = tf.lite.TFLiteConverter.from_keras_model(modelo)
    conversor.optimizations = [tf.lite.Optimize.DEFAULT]
    conversor.representative_dataset = representativo
    conversor.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conversor.inference_input_type = tf.int8
    conversor.inference_output_type = tf.int8
    convertido = conversor.convert()
    if consumidas != [r["image_id"] for r in fotos]:
        raise ValueError("conversor não consumiu exatamente o conjunto documentado")
    grafo = schema.Model.GetRootAsModel(convertido, 0)
    tipos = Counter(grafo.Subgraphs(s).Tensors(i).Type() for s in range(grafo.SubgraphsLength())
                    for i in range(grafo.Subgraphs(s).TensorsLength()))
    if any(tipos[t] for t in (schema.TensorType.FLOAT32, schema.TensorType.FLOAT16, schema.TensorType.FLOAT64)):
        raise ValueError("conversão ainda contém tensores em ponto flutuante")
    verificacoes = []
    with tempfile.TemporaryDirectory(prefix="int8-t7-3-") as tmp:
        arquivo = Path(tmp) / "modelo_int8.tflite"
        arquivo.write_bytes(convertido)
        interpreter = tf.lite.Interpreter(model_path=str(arquivo), num_threads=4)
        interpreter.allocate_tensors()
        es, ss = interpreter.get_input_details(), interpreter.get_output_details()
        if len(es) != 1 or len(ss) != 1:
            raise ValueError("esperada uma entrada e uma saída")
        entrada, saida_tensor = tensor_int8(es[0]), tensor_int8(ss[0])
        if entrada["shape"] != [1,224,224,3] or saida_tensor["shape"] != [1,13]:
            raise ValueError("dimensões INT8 incompatíveis")
        ids_visuais = {a["image_id"] for a in revisao["imagens"]}
        for r,x in zip(fotos, imagens):
            if r["image_id"] not in ids_visuais:
                continue
            interpreter.set_tensor(entrada["indice"], quantizar(x[None], entrada["escala"], entrada["zero_point"]))
            interpreter.invoke()
            y = (interpreter.get_tensor(saida_tensor["indice"]).astype(np.float32) - saida_tensor["zero_point"]) * saida_tensor["escala"]
            tolerancia = 13 * saida_tensor["escala"] / 2 + 1e-6
            if not np.isfinite(y).all() or (y < 0).any() or (y > 1).any() or abs(float(y.sum()) - 1) > tolerancia:
                raise ValueError("saída desquantizada inválida")
            referencia = np.asarray(modelo(x[None], training=False))
            verificacoes.append({"image_id": r["image_id"], "indice_real": int(r["indice_modelo"]),
                "argmax_keras": int(referencia.argmax()), "argmax_int8": int(y.argmax()),
                "erro_absoluto_maximo": float(np.abs(referencia-y).max()), "soma_desquantizada": float(y.sum())})
    nomes_tipos = {valor: nome for nome,valor in vars(schema.TensorType).items() if isinstance(valor,int)}
    resultado = {"esquema": "quantizacao_T7_3_v1", "origem_selecao": origem,
        "modelo_keras_sha256": _hash(pacote / "modelo.keras"), "modelo_int8_sha256": sha256(convertido).hexdigest(),
        "tamanho_bytes": len(convertido), "tensorflow": tf.__version__, "classes": classes,
        "quantizacao": "inteira; TFLITE_BUILTINS_INT8; entrada e saída INT8; grafo sem tensores FLOAT16/FLOAT32/FLOAT64",
        "tipos_tensores_grafo": {nomes_tipos.get(k,str(k)): v for k,v in sorted(tipos.items())},
        "codigo_sha256": _hash(Path(__file__)),
        "entrada": entrada, "saida": saida_tensor,
        "preprocessamento": "T4.1: EXIF, RGB, proporção e padding cinza; float32 [0,1] sem augmentation; a normalização do backbone já está no modelo",
        "quantizacao_entrada": "clip(round(x/escala)+zero_point,-128,127); usar escala e zero_point do tensor de entrada",
        "desquantizacao_saida": "(q-zero_point)*escala; valores não são probabilidades calibradas de acerto",
        "calibracao": {"particao": "treino", "imagens_consumidas": len(consumidas), "image_ids": consumidas,
            "conjunto_sha256": _hash(conjunto / "conjunto.json"), "manifesto_sha256": _hash(conjunto / "manifesto_calibracao.csv"),
            "revisao_iluminacao_sha256": _hash(conjunto / "revisao_iluminacao.json"),
            "indice_sha256": _hash(indice), "augmentation": False},
        "verificacoes_execucao": verificacoes, "teste_acessado": False, "validacao_acessada": False,
        "limite_interpretacao": "execução em imagens da própria calibração; não mede generalização, perda de F1, política de confiança ou latência no aparelho"}
    texto = ["# Quantização INT8 — T7.3", "", f"Imagens reais consumidas: {len(consumidas)}; 13 classes; somente treino, sem augmentation.",
        f"Tamanho: {len(convertido)} bytes. SHA-256 INT8: `{resultado['modelo_int8_sha256']}`.", "",
        "| Tensor | Shape | Tipo | Escala | Zero point |", "| --- | --- | --- | --- | --- |"]
    for nome,t in (("entrada",entrada),("saída",saida_tensor)):
        texto.append(f"| {nome} | {t['shape']} | int8 | {t['escala']} | {t['zero_point']} |")
    texto += ["", resultado["preprocessamento"], resultado["quantizacao_entrada"], resultado["desquantizacao_saida"],
        "", f"Arquivo reaberto e executado em {len(verificacoes)} fotos reais revisadas visualmente, cobrindo as 13 classes.",
        "O grafo foi inspecionado e não contém tensores em ponto flutuante.",
        "Conjunto, IDs, revisão de iluminação, hashes e diferenças por imagem constam no contrato JSON.",
        resultado["limite_interpretacao"], ""]
    saida.mkdir(parents=True)
    (saida / "modelo_int8.tflite").write_bytes(convertido)
    gravar(saida / "contrato_int8.json", resultado)
    (saida / "relatorio_quantizacao.md").write_text("\n".join(texto), encoding="utf-8")
    return resultado


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="acao", required=True)
    for nome in ("preparar", "converter"):
        s = sp.add_parser(nome)
        s.add_argument("--raiz-imagens", type=Path, required=True)
        s.add_argument("--indice", type=Path, default=INDICE)
        s.add_argument("--pacote", type=Path, default=PACOTE)
        s.add_argument("--saida", type=Path, default=CONJUNTO if nome == "preparar" else SAIDA)
        if nome == "preparar":
            s.add_argument("--total", type=int, default=200)
            s.add_argument("--semente", type=int, default=42)
        else:
            s.add_argument("--conjunto", type=Path, default=CONJUNTO)
    a = p.parse_args()
    if a.acao == "preparar":
        r = preparar(a.raiz_imagens, a.saida, a.indice, a.pacote, a.total, a.semente)
        print(f"Conjunto documentado: {r['total']} imagens. Revisar iluminação antes de converter.")
    else:
        r = converter(a.raiz_imagens, a.conjunto, a.saida, a.indice, a.pacote)
        print(f"INT8 convertido: {r['tamanho_bytes']} bytes; {r['calibracao']['imagens_consumidas']} imagens reais consumidas.")


if __name__ == "__main__":
    main()
