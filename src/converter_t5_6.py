"""Converte o checkpoint da rodada e mede desempenho somente na validação."""

from pathlib import Path
import argparse
import csv
import tempfile

from src.selecao_t5_6 import gravar, hash_arquivo, validar_rodada


def amostra_calibracao(linhas: list[dict], total: int = 200, semente: int = 42) -> list[dict]:
    """Amostra determinística do treino; garante cobertura das 13 classes."""
    import random
    treino = [r for r in linhas if r["particao"] == "treino"]
    classes = sorted({int(r["indice_modelo"]) for r in linhas})
    if len(classes) != 13 or total < 13 or len(treino) < total:
        raise ValueError("calibração exige treino suficiente e cobertura de 13 classes")
    rng = random.Random(semente)
    escolhidas = []
    for classe in classes:
        candidatas = [r for r in treino if int(r["indice_modelo"]) == classe]
        if not candidatas:
            raise ValueError("classe sem amostras de treino")
        escolhidas.append(rng.choice(candidatas))
    ids = {r["image_id"] for r in escolhidas}
    escolhidas += rng.sample([r for r in treino if r["image_id"] not in ids], total - len(escolhidas))
    return escolhidas


def converter(rodada: Path, raiz_imagens: Path, indice: Path, pesos: Path, saida: Path):
    import numpy as np
    import tensorflow as tf
    import keras
    import keras_hub  # registra os componentes do preset no carregamento
    from tensorflow.lite.python import schema_py_generated as schema
    from src.avaliacao import calcular_metricas
    from src.dados_treino import preparar_particao
    from src.benchmark_t5_6 import interpretador, prever

    auditada = validar_rodada(rodada, indice, pesos)
    if saida.exists():
        raise ValueError("saída de conversão já existe; preservar os artefatos")
    with indice.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    selecionadas = amostra_calibracao(linhas)
    calibracao, _, _ = preparar_particao(selecionadas, "treino", raiz_imagens, 224)
    validacao, rotulos, _ = preparar_particao(linhas, "validacao", raiz_imagens, 224)
    modelo = keras.models.load_model(rodada / "melhor_modelo.keras", compile=False)
    if tuple(modelo.input_shape[1:]) != (224, 224, 3) or tuple(modelo.output_shape[1:]) != (13,):
        raise ValueError("dimensões do modelo incompatíveis")
    previsoes = np.concatenate([np.asarray(modelo(validacao[i:i+32].astype(np.float32) / 255., training=False))
                                for i in range(0, len(validacao), 32)])
    if not np.isfinite(previsoes).all() or not np.allclose(previsoes.sum(axis=1), 1, atol=1e-5):
        raise ValueError("checkpoint não produz probabilidades válidas")
    nomes = [c["nome"] for c in auditada["classes"]]
    keras_met = calcular_metricas(rotulos, previsoes.argmax(axis=1), 13, nomes)
    if keras_met != auditada["metricas"]["validacao"]:
        raise ValueError("checkpoint carregado não reproduz as métricas da rodada")
    saida.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="exportacao-t5-6-") as tmp:
        exportado = Path(tmp) / "saved_model"
        modelo.export(str(exportado))
        fp32 = tf.lite.TFLiteConverter.from_saved_model(str(exportado)).convert()
        (saida / "modelo_fp32.tflite").write_bytes(fp32)

        def representativo():
            for img in calibracao:
                yield [img[None].astype(np.float32) / 255.]

        conversor = tf.lite.TFLiteConverter.from_saved_model(str(exportado))
        conversor.optimizations = [tf.lite.Optimize.DEFAULT]
        conversor.representative_dataset = representativo
        conversor.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        conversor.inference_input_type = tf.int8
        conversor.inference_output_type = tf.int8
        int8 = conversor.convert()
        (saida / "modelo_int8.tflite").write_bytes(int8)
    # Conferir o grafo real, além da intenção declarada no conversor.
    grafo = schema.Model.GetRootAsModel(int8, 0)
    if any(grafo.Subgraphs(s).Tensors(i).Type() == schema.TensorType.FLOAT32
           for s in range(grafo.SubgraphsLength())
           for i in range(grafo.Subgraphs(s).TensorsLength())):
        raise ValueError("o modelo INT8 ainda contém tensores FLOAT32")
    resultados = {}
    contratos = {}
    for precisao in ("fp32", "int8"):
        interpreter = interpretador(saida / f"modelo_{precisao}.tflite", 4, "desativado")
        contratos[precisao] = {}
        for nome, tensor in (("entrada", interpreter.get_input_details()[0]),
                             ("saida", interpreter.get_output_details()[0])):
            escala, zero = tensor["quantization"]
            contratos[precisao][nome] = {"forma": tensor["shape"].tolist(),
                                       "dtype": np.dtype(tensor["dtype"]).name,
                                       "escala": float(escala), "zero_point": int(zero)}
        previstos = np.array([prever(interpreter, img.astype(np.float32) / 255.).argmax()
                             for img in validacao])
        resultados[precisao] = calcular_metricas(rotulos, previstos, 13, nomes)
    dados = {"esquema": "conversao_T5_6_v1",
             "modelo_origem_sha256": auditada["sha256"]["melhor_modelo.keras"],
             "indice_sha256": hash_arquivo(indice), "pesos_sha256": hash_arquivo(pesos),
             "tensorflow": tf.__version__, "keras": keras.__version__,
             "calibracao": {"particao": "treino", "semente": 42,
                            "image_ids": [r["image_id"] for r in selecionadas], "classes": 13},
             "teste_acessado": False, "particao_avaliacao": "validacao",
             "entrada": {"forma": [1, 224, 224, 3], "faixa_original": [0, 1],
                         "int8": "quantizar por escala e zero_point do tensor"},
             "tipo_quantizacao": "inteira, entrada/saída INT8; grafo sem FLOAT32",
             "contrato_tflite": contratos,
             "fp32_sha256": hash_arquivo(saida / "modelo_fp32.tflite"),
             "int8_sha256": hash_arquivo(saida / "modelo_int8.tflite"),
             "fp32_bytes": len(fp32), "int8_bytes": len(int8),
             "validacao_keras": keras_met, "validacao_tflite": resultados,
             "delta_f1_macro_int8_fp32_pp": 100 * (resultados["int8"]["f1_macro"] - resultados["fp32"]["f1_macro"]),
             "rnf_06": "não comprovado; F1 macro de validação não substitui o critério de acurácia macro no teste"}
    gravar(saida / "conversao.json", dados)
    return dados


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("rodada", "raiz-imagens", "indice", "pesos", "saida"):
        p.add_argument("--" + nome, required=True, type=Path)
    a = p.parse_args()
    resultado = converter(a.rodada, a.raiz_imagens, a.indice, a.pesos, a.saida)
    print({k: resultado[k] for k in ("fp32_bytes", "int8_bytes", "delta_f1_macro_int8_fp32_pp")})


if __name__ == "__main__":
    main()
