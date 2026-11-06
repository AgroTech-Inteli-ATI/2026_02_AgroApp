"""Benchmark comparável das versões TFLite versionadas (CPU local)."""

import argparse
import csv
import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path


def executar(raiz, saida, threads=1, aquecimento=20, repeticoes=100):
    import numpy as np
    import tensorflow as tf

    if threads < 1 or aquecimento < 1 or repeticoes < 30:
        raise ValueError("Exige threads e aquecimento positivos e >=30 repetições")
    modelos = sorted(raiz.glob("*/conversao_t5_6/modelo_*.tflite"))
    if not modelos:
        raise ValueError("Nenhum modelo encontrado")
    saida.mkdir(parents=True, exist_ok=False)
    resultados = []
    for modelo in modelos:
        interpreter = tf.lite.Interpreter(
            model_path=str(modelo), num_threads=threads,
            experimental_op_resolver_type=tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES,
        )
        inicio = time.perf_counter_ns()
        interpreter.allocate_tensors()
        alocacao_ms = (time.perf_counter_ns() - inicio) / 1e6
        entrada = interpreter.get_input_details()[0]
        destino = interpreter.get_output_details()[0]
        if tuple(entrada["shape"]) != (1, 224, 224, 3):
            raise ValueError(f"Entrada incompatível: {modelo}")
        # Mesmos pixels em [0,1]; quantização preparada fora da medição.
        imagem = np.random.default_rng(42).random((1, 224, 224, 3), dtype=np.float32)
        if np.issubdtype(entrada["dtype"], np.integer):
            escala, zero = entrada["quantization"]
            if escala <= 0:
                raise ValueError("Escala inválida")
            limites = np.iinfo(entrada["dtype"])
            imagem = np.clip(np.rint(imagem / escala + zero), limites.min, limites.max)
        imagem = imagem.astype(entrada["dtype"])
        def inferir():
            interpreter.set_tensor(entrada["index"], imagem)
            interpreter.invoke()
            return interpreter.get_tensor(destino["index"])
        for _ in range(aquecimento):
            inferir()
        tempos = []
        for _ in range(repeticoes):
            inicio = time.perf_counter_ns()
            predicao = inferir()
            tempos.append((time.perf_counter_ns() - inicio) / 1e6)
        if predicao.shape != (1, 13) or not np.isfinite(predicao).all():
            raise ValueError("Saída incompatível")
        registro = dict(modelo=modelo.as_posix(), sha256=hashlib.sha256(modelo.read_bytes()).hexdigest(),
                        bytes=modelo.stat().st_size, entrada_dtype=np.dtype(entrada["dtype"]).name,
                        alocacao_ms=alocacao_ms, media_ms=float(np.mean(tempos)),
                        p50_ms=float(np.percentile(tempos, 50)), p95_ms=float(np.percentile(tempos, 95)),
                        duracoes_ms=tempos)
        resultados.append(registro)
        print(f"{modelo.parent.parent.name}/{modelo.name}: p50={registro['p50_ms']:.2f} ms", flush=True)
        del interpreter
    relatorio = dict(data_utc=datetime.now(timezone.utc).isoformat(), sistema=platform.platform(),
                     cpu=os.environ.get("PROCESSOR_IDENTIFIER", platform.processor()),
                     cpus_logicas=os.cpu_count(), python=platform.python_version(), tensorflow=tf.__version__,
                     numpy=np.__version__, threads=threads, delegate="desativado", batch=1,
                     forma=[1, 224, 224, 3], semente=42, aquecimento=aquecimento, repeticoes=repeticoes,
                     metodo="set_tensor + invoke + get_tensor; entrada sintética uniforme [0,1]; sem preprocessamento, carregamento ou quantização da entrada",
                     escopo="CPU local; não certifica latência, RAM ou consumo energético em celular",
                     resultados=resultados)
    (saida / "resultados.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    campos = [c for c in resultados[0] if c != "duracoes_ms"]
    with (saida / "resumo.csv").open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(resultados)
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=Path("assets/modelos/rodadas_T5_6_20261026"))
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--aquecimento", type=int, default=20)
    parser.add_argument("--repeticoes", type=int, default=100)
    args = parser.parse_args()
    executar(args.raiz, args.saida, args.threads, args.aquecimento, args.repeticoes)


if __name__ == "__main__":
    main()
