"""Converte o checkpoint selecionado da T5.1 e valida inferência TFLite float32."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import numpy as np

from src.preprocessamento import preparar_imagem


def _tensor(detalhe):
    return {
        "nome": detalhe["name"], "indice": int(detalhe["index"]),
        "shape": detalhe["shape"].tolist(),
        "shape_signature": detalhe["shape_signature"].tolist(),
        "dtype": np.dtype(detalhe["dtype"]).name,
    }


def converter(rodada: Path, saida: Path, imagens=()) -> dict:
    """Publica os artefatos apenas depois de carregar e executar o FlatBuffer."""
    rodada, saida = Path(rodada), Path(saida)
    checkpoint = rodada / "melhor_modelo.keras"
    for caminho in (checkpoint, rodada / "metricas_validacao.json"):
        if not caminho.is_file():
            raise ValueError(f"arquivo obrigatório ausente na rodada selecionada: {caminho}")
    conteudo = checkpoint.read_bytes()
    metricas = json.loads((rodada / "metricas_validacao.json").read_text(encoding="utf-8"))
    if metricas.get("esquema") != "metricas_validacao_T5_1_v1":
        raise ValueError("esquema da rodada não suportado")
    classes = metricas["validacao"]["por_classe"]
    if not classes or [c["indice"] for c in classes] != list(range(len(classes))):
        raise ValueError("ordem das classes inválida")
    tamanho = metricas["tamanho_entrada"]
    if isinstance(tamanho, bool) or not isinstance(tamanho, int) or tamanho < 1:
        raise ValueError("tamanho_entrada deve ser inteiro positivo")
    arquivos = ("modelo.tflite", "contrato_tensores.json", "relatorio_conversao.md")
    if any((saida / nome).exists() for nome in arquivos):
        raise ValueError("saída já contém conversão; escolha outra pasta")

    import tensorflow as tf
    from src.avaliacao_t6_1 import _carregar_modelo

    modelo = _carregar_modelo(checkpoint)
    if (tuple(modelo.input_shape) not in ((None, tamanho, tamanho, 3), (1, tamanho, tamanho, 3))
            or tuple(modelo.output_shape[1:]) != (len(classes),)):
        raise ValueError("dimensões do modelo incompatíveis com a rodada")
    conversor = tf.lite.TFLiteConverter.from_keras_model(modelo)
    # Baseline float32; quantização pertence às próximas etapas da A7.
    conversor.optimizations = []
    conversor.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    convertido = conversor.convert()
    verificacoes = []
    with tempfile.TemporaryDirectory() as temporario:
        caminho = Path(temporario) / "modelo.tflite"
        caminho.write_bytes(convertido)
        interpretador = tf.lite.Interpreter(model_path=str(caminho))
        interpretador.allocate_tensors()
        entradas, saidas = interpretador.get_input_details(), interpretador.get_output_details()
        if len(entradas) != 1 or len(saidas) != 1:
            raise ValueError("esperada uma entrada e uma saída")
        entrada, saida_tensor = entradas[0], saidas[0]
        for detalhe, formato in ((entrada, (1, tamanho, tamanho, 3)), (saida_tensor, (1, len(classes)))):
            if tuple(detalhe["shape"]) != formato or detalhe["dtype"] != np.float32:
                raise ValueError("contrato TFLite incompatível com float32/batch 1")
        rng = np.random.default_rng(42)
        amostras = [("sintetica_zeros", np.zeros((tamanho, tamanho, 3), np.float32)),
                    ("sintetica_uns", np.ones((tamanho, tamanho, 3), np.float32)),
                    ("sintetica_aleatoria", rng.random((tamanho, tamanho, 3), dtype=np.float32))]
        amostras += [(str(p), preparar_imagem(p, tamanho)) for p in imagens]
        for origem, imagem in amostras:
            lote = imagem[None, ...]
            referencia = np.asarray(modelo(lote, training=False))
            interpretador.set_tensor(entrada["index"], lote)
            interpretador.invoke()
            previsto = interpretador.get_tensor(saida_tensor["index"])
            for valores in (referencia, previsto):
                if (valores.shape != (1, len(classes)) or not np.isfinite(valores).all()
                        or (valores < 0).any() or (valores > 1).any()
                        or not np.allclose(valores.sum(axis=1), 1, atol=1e-5)):
                    raise ValueError("saída não é uma distribuição softmax válida")
            if not np.allclose(referencia, previsto, atol=1e-5, rtol=1e-4):
                raise ValueError(f"divergência numérica Keras/TFLite: {origem}")
            verificacoes.append({"amostra": origem,
                "erro_absoluto_maximo": float(np.max(np.abs(referencia - previsto))),
                "argmax_keras": int(referencia.argmax()), "argmax_tflite": int(previsto.argmax())})
    resultado = {
        "esquema": "conversao_T7_1_v1", "backbone": metricas["backbone"],
        "tensorflow": tf.__version__, "quantizacao": None, "operadores": "TFLITE_BUILTINS",
        "sha256": {"keras": sha256(conteudo).hexdigest(), "tflite": sha256(convertido).hexdigest()},
        "tamanho_bytes": len(convertido), "entrada": _tensor(entrada), "saida": _tensor(saida_tensor),
        "preprocessamento": "T4.1: EXIF, RGB, proporção preservada, padding cinza 128, float32 / 255",
        "classes": [{"indice": c["indice"], "nome": c["nome"]} for c in classes],
        "validacao": {"atol": 1e-5, "rtol": 1e-4, "amostras": verificacoes},
    }
    texto = ["# Conversão T7.1", "", f"Backbone: {metricas['backbone']}. Modelo float32, sem quantização.",
             "", "| Tensor | Nome | Shape alocado | Assinatura | Tipo |",
             "| --- | --- | --- | --- | --- |"]
    for papel in ("entrada", "saida"):
        t = resultado[papel]
        texto.append(f"| {papel} | {t['nome']} | {t['shape']} | {t['shape_signature']} | {t['dtype']} |")
    texto += ["", resultado["preprocessamento"] + ". Layout NHWC, batch 1; entrada em [0, 1].",
              "Saída: probabilidades softmax; argmax identifica o índice da classe em contrato_tensores.json.",
              "", f"FlatBuffer carregado do disco e executado em {len(verificacoes)} amostras.",
              "Comparação Keras/TFLite: atol=1e-5, rtol=1e-4. Detalhes no JSON.",
              "As amostras sintéticas verificam execução e equivalência numérica, sem medir acurácia."]
    saida.mkdir(parents=True, exist_ok=True)
    (saida / arquivos[0]).write_bytes(convertido)
    (saida / arquivos[1]).write_text(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (saida / arquivos[2]).write_text("\n".join(texto) + "\n", encoding="utf-8")
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rodada", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--imagem", type=Path, action="append", default=[], help="imagem opcional; repetível")
    args = parser.parse_args()
    try:
        resultado = converter(args.rodada, args.saida, args.imagem)
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Conversão não concluída: {erro}\n")
    print(f"Modelo convertido e validado: {args.saida / 'modelo.tflite'} ({resultado['tamanho_bytes']} bytes)")


if __name__ == "__main__":
    main()
