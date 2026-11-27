"""Benchmark local de um TFLite; não certifica latência no celular de referência."""

from pathlib import Path
import argparse
import platform
import time

from src.selecao_t5_6 import gravar, hash_arquivo


def interpretador(caminho: Path, threads: int = 4, delegate: str = "desativado"):
    import tensorflow as tf
    if threads < 1 or delegate not in {"padrao", "desativado"}:
        raise ValueError("threads/delegate inválidos")
    kwargs = {}
    if delegate == "desativado":
        kwargs["experimental_op_resolver_type"] = tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES
    interpreter = tf.lite.Interpreter(model_path=str(caminho), num_threads=threads, **kwargs)
    interpreter.allocate_tensors()
    return interpreter


def prever(interpreter, imagem):
    import numpy as np
    entrada = interpreter.get_input_details()[0]
    saida = interpreter.get_output_details()[0]
    valor = np.asarray(imagem, dtype=np.float32)[None]
    if np.issubdtype(entrada["dtype"], np.integer):
        escala, zero = entrada["quantization"]
        if escala <= 0:
            raise ValueError("escala de quantização inválida")
        limites = np.iinfo(entrada["dtype"])
        valor = np.clip(np.round(valor / escala + zero), limites.min, limites.max).astype(entrada["dtype"])
    interpreter.set_tensor(entrada["index"], valor)
    interpreter.invoke()
    probs = interpreter.get_tensor(saida["index"])[0]
    if np.issubdtype(saida["dtype"], np.integer):
        escala, zero = saida["quantization"]
        probs = (probs.astype(np.float32) - zero) * escala
    if probs.shape != (13,) or not np.isfinite(probs).all():
        raise ValueError("saída do modelo incompatível")
    return probs


def medir(modelo: Path, saida: Path, dispositivo: str, threads: int = 4,
          delegate: str = "desativado", aquecimento: int = 20, repeticoes: int = 100):
    import numpy as np
    import tensorflow as tf
    if aquecimento < 1 or repeticoes < 30 or not dispositivo.strip():
        raise ValueError("informar dispositivo, aquecimento positivo e ao menos 30 repetições")
    if saida.exists():
        raise ValueError("relatório já existe; preservar a medição")
    interpreter = interpretador(modelo, threads, delegate)
    forma = tuple(interpreter.get_input_details()[0]["shape"])
    if forma != (1, 224, 224, 3):
        raise ValueError("entrada deve ser batch 1, 224 x 224 x 3")
    imagem = np.zeros(forma[1:], dtype=np.float32)
    for _ in range(aquecimento):
        prever(interpreter, imagem)
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter_ns()
        prever(interpreter, imagem)
        tempos.append((time.perf_counter_ns() - inicio) / 1e6)
    dados = {"modelo_sha256": hash_arquivo(modelo), "dispositivo_informado": dispositivo,
             "sistema": platform.platform(), "maquina": platform.machine(),
             "runtime": f"TensorFlow Lite {tf.__version__}", "python": platform.python_version(),
             "threads": threads, "delegate": delegate, "batch": 1,
             "entrada_dtype": str(interpreter.get_input_details()[0]["dtype"]),
             "aquecimento": aquecimento, "repeticoes": repeticoes,
             "p50_ms": float(np.percentile(tempos, 50)), "p95_ms": float(np.percentile(tempos, 95)),
             "metodo": "tensor sintético de zeros; inclui set_tensor, invoke e get_tensor; sem preparação da fotografia",
             "escopo": "medição local; não comprova RNF-04 no celular de referência",
             "duracoes_ms": tempos}
    saida.parent.mkdir(parents=True, exist_ok=True)
    gravar(saida, dados)
    return dados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--dispositivo", required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--delegate", choices=("padrao", "desativado"), default="desativado")
    parser.add_argument("--aquecimento", type=int, default=20)
    parser.add_argument("--repeticoes", type=int, default=100)
    args = parser.parse_args()
    resultado = medir(args.modelo, args.saida, args.dispositivo, args.threads,
                      args.delegate, args.aquecimento, args.repeticoes)
    print({k: resultado[k] for k in ("p50_ms", "p95_ms", "escopo")})


if __name__ == "__main__":
    main()
