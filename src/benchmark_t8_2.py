"""Benchmark reproduzível das versões oficiais T7.1–T7.3 em CPU local."""

import argparse
from contextlib import contextmanager
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

RAIZ = Path(__file__).resolve().parents[1]
BASE = Path("assets/modelos")
COMPARACAO = BASE / "comparacao_T7_2_candidato_T5_6_20261026"
MODELOS = {
    "fp32": BASE / "conversao_T7_1_candidato_T5_6_20261026/modelo.tflite",
    "faixa_dinamica": COMPARACAO / "modelo_faixa_dinamica.tflite",
    "float16": COMPARACAO / "modelo_float16.tflite",
    "int8_t7_3": BASE / "quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite",
    "int8_t7_2": COMPARACAO / "modelo_int8.tflite",
}
REFERENCIAS = {"int8_t7_2": "int8"}


def agora():
    return datetime.now(timezone.utc).isoformat()


def sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def ler(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def gravar(caminho, dados):
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def selecionar_modelos(raiz):
    referencia = ler(raiz / COMPARACAO / "comparacao.json")["estrategias"]
    modelos = {nome: raiz / caminho for nome, caminho in MODELOS.items()}
    for nome, caminho in modelos.items():
        esperado = referencia[REFERENCIAS.get(nome, nome)]
        if caminho.stat().st_size != esperado["tamanho_bytes"] or sha256(caminho) != esperado["sha256"]:
            raise ValueError(f"Artefato diverge da comparação T7.2: {caminho}")
    return modelos


def ordem_rodada(nomes, rodada, sessao):
    nomes = list(nomes)
    offset = (rodada + sessao - 1) % len(nomes)
    return nomes[offset:] + nomes[:offset]


def resumo(amostras):
    import numpy as np
    valores = np.asarray(amostras, dtype=float)
    if len(valores) == 0 or not np.isfinite(valores).all() or (valores <= 0).any():
        raise ValueError("Durações devem ser positivas e finitas")
    return dict(media_ms=float(np.mean(valores)), p50_ms=float(np.percentile(valores, 50)),
                p95_ms=float(np.percentile(valores, 95)), min_ms=float(min(valores)), max_ms=float(max(valores)))


def variacao(valores):
    return 100 * (max(valores) / min(valores) - 1)


def estado_sistema():
    estado = dict(energia="desconhecida", contadores_cpu=None)
    if platform.system() != "Windows":
        return estado
    import ctypes
    from ctypes import wintypes

    class Energia(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                    ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                    ("BatteryLifeTime", wintypes.DWORD), ("BatteryFullLifeTime", wintypes.DWORD)]

    status = Energia()
    if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        estado["energia"] = {0: "bateria", 1: "tomada"}.get(status.ACLineStatus, "desconhecida")
    contadores = [wintypes.FILETIME() for _ in range(3)]
    if ctypes.windll.kernel32.GetSystemTimes(*(ctypes.byref(c) for c in contadores)):
        estado["contadores_cpu"] = [c.dwLowDateTime + (c.dwHighDateTime << 32) for c in contadores]
    return estado


def carga_cpu(antes, depois):
    if antes["contadores_cpu"] is None or depois["contadores_cpu"] is None:
        return None
    idle, kernel, usuario = [b - a for a, b in zip(antes["contadores_cpu"], depois["contadores_cpu"])]
    total = kernel + usuario
    return 100 * (1 - idle / total) if total > 0 else None


def processador():
    if platform.system() == "Windows":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as chave:
            return winreg.QueryValueEx(chave, "ProcessorNameString")[0].strip()
    return platform.processor()


@contextmanager
def controlar_processo(cpu):
    """Fixa um núcleo e prioridade apenas deste processo; restaura ao terminar."""
    if platform.system() != "Windows":
        if cpu is not None:
            raise ValueError("--cpu exige Windows; use --cpu -1 para escalonamento normal")
        yield dict(cpu_fixa=None, prioridade="normal")
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
    kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    processo = kernel.GetCurrentProcess()
    mascara, sistema = ctypes.c_size_t(), ctypes.c_size_t()
    if not kernel.GetProcessAffinityMask(processo, ctypes.byref(mascara), ctypes.byref(sistema)):
        raise OSError("Não foi possível consultar a afinidade")
    original, prioridade = mascara.value, kernel.GetPriorityClass(processo)
    if cpu is not None and (cpu < 0 or cpu >= mascara.value.bit_length() or not mascara.value & (1 << cpu)):
        raise ValueError("CPU fora da afinidade disponível")
    try:
        if cpu is not None and not kernel.SetProcessAffinityMask(processo, ctypes.c_size_t(1 << cpu)):
            raise OSError("Não foi possível fixar a CPU")
        if not kernel.SetPriorityClass(processo, 0x8000):  # ABOVE_NORMAL_PRIORITY_CLASS
            raise OSError("Não foi possível ajustar a prioridade do benchmark")
        yield dict(cpu_fixa=cpu, prioridade="acima_normal", prioridade_codigo=kernel.GetPriorityClass(processo))
    finally:
        kernel.SetProcessAffinityMask(processo, ctypes.c_size_t(original))
        kernel.SetPriorityClass(processo, prioridade)


def validar_parametros(rodadas, repeticoes, aquecimento, sessao):
    if rodadas < 5 or rodadas % len(MODELOS) != 0 or repeticoes < 30 or aquecimento < 20 or sessao < 1:
        raise ValueError("Exige rodadas múltiplas de 5, >=30 repetições, >=20 aquecimentos e sessão positiva")


def executar(raiz, saida, rodadas=5, repeticoes=40, aquecimento=100, sessao=1, cpu=0, energia="tomada"):
    validar_parametros(rodadas, repeticoes, aquecimento, sessao)
    raiz, saida = Path(raiz).resolve(), Path(saida)
    modelos = selecionar_modelos(raiz)
    if saida.exists():
        raise FileExistsError(f"Saída já existe: {saida}")
    if energia not in {"tomada", "bateria"}:
        raise ValueError("Fonte de energia inválida")
    if estado_sistema()["energia"] != energia:
        raise ValueError(f"Fonte de energia deve permanecer em {energia}")
    with controlar_processo(cpu) as controle:
        import numpy as np
        import tensorflow as tf

        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.threading.set_intra_op_parallelism_threads(1)
        if estado_sistema()["energia"] != energia:
            raise ValueError(f"Fonte de energia mudou; esperado: {energia}")
        saida.mkdir(parents=True, exist_ok=False)
        inicio = agora()
        imagem = np.random.default_rng(42).random((1, 224, 224, 3), dtype=np.float32)
        executores, registros, ordem = {}, {}, []
        for nome, modelo in modelos.items():
            inicio_alocacao = time.perf_counter_ns()
            interpreter = tf.lite.Interpreter(model_path=str(modelo), num_threads=1)
            interpreter.allocate_tensors()
            inicializacao_ms = (time.perf_counter_ns() - inicio_alocacao) / 1e6
            entradas, saidas = interpreter.get_input_details(), interpreter.get_output_details()
            if len(entradas) != 1 or len(saidas) != 1:
                raise ValueError("Esperada uma entrada e uma saída")
            entrada, destino = entradas[0], saidas[0]
            if tuple(entrada["shape"]) != (1, 224, 224, 3) or tuple(destino["shape"]) != (1, 13):
                raise ValueError(f"Contrato incompatível: {modelo}")
            tensor = imagem
            if np.issubdtype(entrada["dtype"], np.integer):
                escala, zero = entrada["quantization"]
                if escala <= 0:
                    raise ValueError("Escala de quantização inválida")
                limites = np.iinfo(entrada["dtype"])
                tensor = np.clip(np.rint(imagem / escala + zero), limites.min, limites.max)
            tensor = tensor.astype(entrada["dtype"])
            delegados = sum(op["op_name"] == "DELEGATE" for op in interpreter._get_ops_details())
            if delegados == 0:
                raise ValueError("XNNPACK não foi aplicado ao modelo")
            executores[nome] = (interpreter, entrada, destino, tensor)
            registros[nome] = dict(versao=nome, modelo=modelo.relative_to(raiz).as_posix(),
                sha256=sha256(modelo), bytes=modelo.stat().st_size, inicializacao_ms=inicializacao_ms,
                entrada_dtype=np.dtype(entrada["dtype"]).name, saida_dtype=np.dtype(destino["dtype"]).name,
                entrada_quantizacao=list(entrada["quantization"]), entrada_sha256=hashlib.sha256(tensor.tobytes()).hexdigest(),
                particoes_delegadas=delegados, duracoes_ms=[], blocos=[])

        def inferir(nome):
            interpreter, entrada, destino, tensor = executores[nome]
            interpreter.set_tensor(entrada["index"], tensor)
            interpreter.invoke()
            return interpreter.get_tensor(destino["index"])

        # Aquecimento global não cronometrado, antes de qualquer resultado.
        for nome in modelos:
            for _ in range(aquecimento):
                inferir(nome)
        for rodada in range(rodadas):
            for nome in ordem_rodada(modelos, rodada, sessao):
                # Mesma pausa e reaquecimento por bloco para todas as versões.
                time.sleep(0.1)
                antes = estado_sistema()
                if antes["energia"] != energia:
                    raise ValueError("Fonte de energia mudou; coleta interrompida")
                for _ in range(20):
                    inferir(nome)
                amostras = []
                inicio_cpu = time.process_time_ns()
                inicio_bloco = time.perf_counter_ns()
                for _ in range(repeticoes):
                    inicio_inferencia = time.perf_counter_ns()
                    predicao = inferir(nome)
                    amostras.append((time.perf_counter_ns() - inicio_inferencia) / 1e6)
                parede_ms = (time.perf_counter_ns() - inicio_bloco) / 1e6
                cpu_ms = (time.process_time_ns() - inicio_cpu) / 1e6
                if not np.isfinite(predicao).all() or predicao.shape != (1, 13):
                    raise ValueError("Saída inválida")
                depois = estado_sistema()
                if depois["energia"] != energia:
                    raise ValueError("Fonte de energia mudou; coleta interrompida")
                bloco = dict(rodada=rodada + 1, versao=nome, data_utc=agora(),
                    energia_inicio=antes["energia"], energia_fim=depois["energia"],
                    cpu_total_percentual=carga_cpu(antes, depois), cpu_processo_ms=cpu_ms,
                    parede_bloco_ms=parede_ms, duracoes_ms=amostras, **resumo(amostras))
                registros[nome]["blocos"].append(bloco)
                registros[nome]["duracoes_ms"].extend(amostras)
                ordem.append(dict(rodada=rodada + 1, versao=nome))
                print(f"S{sessao} R{rodada+1}/{rodadas} {nome}: p50={bloco['p50_ms']:.2f} ms", flush=True)
        for r in registros.values():
            r.update(resumo(r["duracoes_ms"]))
            r["variacao_medianas_blocos_percentual"] = variacao([b["p50_ms"] for b in r["blocos"]])
        relatorio = dict(esquema="benchmark_T8_2_v3", sessao=sessao, pid=os.getpid(), inicio_utc=inicio, fim_utc=agora(),
            sistema=platform.platform(), cpu=processador(), cpus_logicas=os.cpu_count(),
            python=platform.python_version(), tensorflow=tf.__version__, numpy=np.__version__,
            controle=controle, energia=energia, threads=1, delegate="xnnpack", batch=1, forma=[1, 224, 224, 3], semente=42,
            entrada_float_sha256=hashlib.sha256(imagem.tobytes()).hexdigest(),
            aquecimento_global=aquecimento, aquecimento_bloco=20, pausa_bloco_ms=100,
            rodadas=rodadas, repeticoes_por_bloco=repeticoes, repeticoes=rodadas * repeticoes,
            metodo="perf_counter_ns: set_tensor + invoke + get_tensor; entrada sintética uniforme [0,1]; sem quantização da entrada, desquantização da saída ou pré-processamento no intervalo",
            temperatura="não medida", ordem=ordem, codigo_sha256=sha256(Path(__file__)),
            escopo="CPU local; não comprova RNF-04, memória ou consumo energético no celular",
            resultados=list(registros.values()))
        gravar(saida / "resultados.json", relatorio)
        # Preserva o código exato usado, incluindo sua codificação e finais de linha.
        (saida / "protocolo.py").write_bytes(Path(__file__).read_bytes())
        escrever_csv(saida / "resumo.csv", relatorio["resultados"])
        return relatorio


def escrever_csv(caminho, resultados):
    campos = ["versao", "modelo", "sha256", "bytes", "media_ms", "p50_ms", "p95_ms", "min_ms", "max_ms"]
    with Path(caminho).open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(resultados)


def consolidar(pastas, saida):
    sessoes = [ler(Path(p) / "resultados.json") for p in pastas]
    if len(sessoes) < 3:
        raise ValueError("Exige pelo menos três sessões independentes")
    campos = ("sistema", "cpu", "python", "tensorflow", "numpy", "controle", "energia", "threads", "delegate",
              "batch", "forma", "semente", "entrada_float_sha256", "aquecimento_global",
              "aquecimento_bloco", "pausa_bloco_ms", "rodadas", "repeticoes_por_bloco", "codigo_sha256")
    for sessao in sessoes[1:]:
        if any(sessao[c] != sessoes[0][c] for c in campos):
            raise ValueError("Sessões com condições/configurações diferentes")
    resultados = []
    for i, nome in enumerate(MODELOS):
        registros = [s["resultados"][i] for s in sessoes]
        if any(r["versao"] != nome or r["sha256"] != registros[0]["sha256"] or r["bytes"] != registros[0]["bytes"] for r in registros):
            raise ValueError("Artefatos diferentes entre sessões")
        amostras = [t for r in registros for t in r["duracoes_ms"]]
        medianas = [r["p50_ms"] for r in registros]
        resultados.append(dict(versao=nome, modelo=registros[0]["modelo"], sha256=registros[0]["sha256"],
            bytes=registros[0]["bytes"], duracoes_ms=amostras, **resumo(amostras),
            medianas_sessoes_ms=medianas, variacao_medianas_sessoes_percentual=variacao(medianas),
            variacao_blocos_por_sessao_percentual=[r["variacao_medianas_blocos_percentual"] for r in registros]))
    relatorio = dict(esquema="benchmark_T8_2_consolidado_v3", data_utc=agora(),
        sessoes=[str(Path(p).relative_to(saida).as_posix()) for p in pastas],
        configuracao={c: sessoes[0][c] for c in campos}, resultados=resultados,
        nota="Estatísticas agrupam todas as amostras, sem excluir valores extremos; rodadas e sessões permanecem disponíveis.")
    gravar(saida / "resultados.json", relatorio)
    escrever_csv(saida / "resumo.csv", resultados)
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=RAIZ, help="Raiz do repositório")
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--rodadas", type=int, default=5)
    parser.add_argument("--repeticoes", type=int, default=40, help="Medições por bloco")
    parser.add_argument("--aquecimento", type=int, default=100)
    parser.add_argument("--cpu", type=int, default=0, help="CPU lógica fixa (Windows); -1 mantém escalonamento normal")
    parser.add_argument("--sessoes", type=int, default=3)
    parser.add_argument("--energia", choices=["tomada", "bateria"], default="tomada", help="Fonte que deve permanecer constante durante todas as sessões")
    parser.add_argument("--sessao", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    validar_parametros(args.rodadas, args.repeticoes, args.aquecimento, args.sessao or 1)
    if args.sessao is not None:
        executar(args.raiz, args.saida, args.rodadas, args.repeticoes, args.aquecimento,
                 args.sessao, None if args.cpu == -1 else args.cpu, args.energia)
        return
    if args.sessoes < 3:
        parser.error("--sessoes exige pelo menos 3")
    if estado_sistema()["energia"] != args.energia:
        parser.error(f"fonte de energia deve estar em {args.energia}")
    args.saida.mkdir(parents=True, exist_ok=False)
    pastas = []
    for numero in range(1, args.sessoes + 1):
        pasta = args.saida / f"sessao_{numero:02d}"
        comando = [sys.executable, "-m", "src.benchmark_t8_2", "--raiz", str(args.raiz),
                   "--saida", str(pasta.resolve()), "--rodadas", str(args.rodadas),
                   "--repeticoes", str(args.repeticoes), "--aquecimento", str(args.aquecimento),
                   "--cpu", str(args.cpu), "--energia", args.energia, "--sessao", str(numero)]
        subprocess.run(comando, cwd=RAIZ, check=True)
        pastas.append(pasta)
    consolidar(pastas, args.saida)


if __name__ == "__main__":
    main()
