"""Compara faixa dinâmica, float16 e INT8 do candidato selecionado (T7.2).

As três estratégias de quantização pós-treinamento são geradas a partir do
mesmo checkpoint Keras e avaliadas contra a referência FP32 em tamanho de
arquivo, latência de inferência no CPU local (com e sem XNNPACK) e métricas
de classificação, com intervalos de confiança pareados e confronto com os
RNF-01, RNF-04 (indicativo local), RNF-06 e RNF-09.

- FP32: reaproveita o FlatBuffer publicado na T7.1 (sem quantização).
- Faixa dinâmica: `Optimize.DEFAULT` sem conjunto representativo; pesos INT8,
  ativações em ponto flutuante, entrada/saída float32.
- Float16: `Optimize.DEFAULT` + `supported_types=[tf.float16]`; pesos float16,
  entrada/saída float32.
- INT8: regenerada nesta etapa pelo fluxo da T7.3, com o mesmo conjunto de
  calibração versionado (200 imagens de treino), e comparada byte a byte com o
  artefato publicado na T7.3.

A validação é a partição principal; o teste já foi consultado em etapas
anteriores e entra apenas como leitura exploratória complementar.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import platform
import statistics
import tempfile
import time

import numpy as np

from src.avaliacao import calcular_metricas
from src.conversao_t7_1 import PACOTE, RAIZ, _hash, _validar_selecao
from src.preprocessamento import preparar_imagem
from src import quantizacao_t7_3 as t7_3

INDICE = t7_3.INDICE
CONJUNTO = t7_3.CONJUNTO
FP32 = RAIZ / "assets/modelos/conversao_T7_1_candidato_T5_6_20261026"
INT8 = RAIZ / "assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026"
SAIDA = RAIZ / "assets/modelos/comparacao_T7_2_candidato_T5_6_20261026"
ESTRATEGIAS = ("fp32", "faixa_dinamica", "float16", "int8")
ROTULOS = {"fp32": "FP32 (referência, T7.1)", "faixa_dinamica": "Faixa dinâmica",
           "float16": "Float16", "int8": "INT8 inteira (regenerada na T7.2)",
           "int8_t7_3": "INT8 inteira (artefato T7.3)"}
PARTICOES = ("validacao", "teste")
CONFIGS_LATENCIA = (("xnnpack", 1), ("xnnpack", 2), ("xnnpack", 4), ("sem_delegate", 1), ("sem_delegate", 4))
LIMITE_RNF01_BYTES = 8_000_000      # RNF-01: tamanho do .tflite <= 8 MB
LIMITE_RNF04_P95_MS = 300.0         # RNF-04: p95 da inferência isolada <= 300 ms (no aparelho)
LIMITE_RNF06_PP = 2.0               # RNF-06: perda de acurácia macro float -> quantizado <= 2 p.p.
ARQUIVOS = ("modelo_faixa_dinamica.tflite", "modelo_float16.tflite", "modelo_int8.tflite",
            "contrato_int8_regenerado.json", "comparacao.json", "tabela_comparativa.csv",
            "metricas_por_classe.csv", "predicoes.csv", "relatorio_comparacao.md")


def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def gravar(p, valor):
    Path(p).write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                       encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- estatística

def resumo_latencia(amostras_ms: list[float]) -> dict:
    """Mediana, p90, p95, p99, média e desvio em milissegundos."""
    if len(amostras_ms) < 2:
        raise ValueError("latência exige pelo menos duas medições")
    ordenadas = sorted(amostras_ms)

    def percentil(p):
        return float(np.percentile(ordenadas, p, method="linear"))

    return {"execucoes": len(ordenadas), "mediana_ms": percentil(50), "p90_ms": percentil(90),
            "p95_ms": percentil(95), "p99_ms": percentil(99), "media_ms": float(statistics.fmean(ordenadas)),
            "desvio_ms": float(statistics.stdev(ordenadas)), "min_ms": ordenadas[0], "max_ms": ordenadas[-1]}


def concordancia(referencia: np.ndarray, outra: np.ndarray) -> dict:
    """Concordância do argmax e diferença dos scores frente à referência."""
    referencia, outra = np.asarray(referencia), np.asarray(outra)
    if referencia.shape != outra.shape or referencia.ndim != 2:
        raise ValueError("saídas com formatos diferentes")
    diff = np.abs(referencia - outra)
    return {"top1_igual_fp32": float(np.mean(referencia.argmax(1) == outra.argmax(1))),
            "divergencias_top1": int(np.sum(referencia.argmax(1) != outra.argmax(1))),
            "erro_absoluto_maximo": float(diff.max()), "erro_absoluto_medio": float(diff.mean())}


def mcnemar_exato(rotulos, prev_ref, prev_outra) -> dict:
    """Teste exato de McNemar (bicaudal) sobre acertos pareados."""
    rotulos, prev_ref, prev_outra = map(np.asarray, (rotulos, prev_ref, prev_outra))
    acerto_ref, acerto_outra = prev_ref == rotulos, prev_outra == rotulos
    b = int(np.sum(acerto_ref & ~acerto_outra))   # só a referência acertou
    c = int(np.sum(~acerto_ref & acerto_outra))   # só a outra acertou
    n = b + c
    p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)
    return {"so_referencia_acertou": b, "so_quantizado_acertou": c, "p_valor": p}


def bootstrap_pareado(rotulos, prev_ref, prev_outra, quantidade_classes: int,
                      reamostras: int = 2000, semente: int = 42) -> dict:
    """IC 95% percentil da diferença (outra − referência) de F1 macro e acurácia macro.

    Reamostra imagens com reposição, aplicando os mesmos índices às duas versões.
    """
    rotulos, prev_ref, prev_outra = map(np.asarray, (rotulos, prev_ref, prev_outra))
    rng = np.random.default_rng(semente)
    deltas = {"f1_macro": [], "balanced_accuracy": []}
    for _ in range(reamostras):
        i = rng.integers(0, len(rotulos), len(rotulos))
        m_ref = calcular_metricas(rotulos[i], prev_ref[i], quantidade_classes)
        m_out = calcular_metricas(rotulos[i], prev_outra[i], quantidade_classes)
        for k in deltas:
            deltas[k].append(m_out[k] - m_ref[k])
    return {k: {"ic95_inferior": float(np.percentile(v, 2.5)), "ic95_superior": float(np.percentile(v, 97.5))}
            for k, v in deltas.items()} | {"reamostras": reamostras, "semente": semente,
                                          "unidade": "imagem (não grupo)"}


def pior_classe(referencia: dict, outra: dict):
    """Classe com a maior queda de F1 frente à referência, ou None se nenhuma caiu."""
    deltas = [(o["nome"], o["f1"] - r["f1"]) for r, o in zip(referencia["por_classe"], outra["por_classe"])
              if r["f1"] is not None and o["f1"] is not None]
    pior = min(deltas, key=lambda d: d[1], default=None)
    return pior if pior is not None and pior[1] < 0 else None


def avaliar_rnf(resultado: dict) -> dict:
    """Confronta cada estratégia com os RNFs mensuráveis nesta etapa."""
    rnf = {}
    for nome, e in resultado["estrategias"].items():
        r = {"RNF-01": {"limite_bytes": LIMITE_RNF01_BYTES, "valor_bytes": e["tamanho_bytes"],
                        "atende": e["tamanho_bytes"] <= LIMITE_RNF01_BYTES}}
        if nome != "fp32":
            for particao, por_modelo in resultado["metricas"].items():
                delta_pp = 100 * (por_modelo[nome]["metricas"]["balanced_accuracy"]
                                  - por_modelo["fp32"]["metricas"]["balanced_accuracy"])
                ic = por_modelo[nome]["estatistica"]["bootstrap"]["balanced_accuracy"]["ic95_inferior"] * 100
                r[f"RNF-06_{particao}"] = {"metrica": "acurácia macro (balanced accuracy)", "limite_pp": -LIMITE_RNF06_PP,
                                            "delta_pp": delta_pp, "ic95_inferior_pp": ic,
                                            "atende_ponto": delta_pp >= -LIMITE_RNF06_PP,
                                            "atende_ic95": ic >= -LIMITE_RNF06_PP}
        lat = resultado["latencia"]["por_config"]
        r["RNF-04_indicativo_local"] = {f"{cfg}": {"p95_ms": lat[cfg][nome]["p95_ms"],
                                                    "abaixo_de_300ms": lat[cfg][nome]["p95_ms"] <= LIMITE_RNF04_P95_MS}
                                        for cfg in lat}
        r["RNF-09"] = resultado["sem_delegate"][nome]
        rnf[nome] = r
    return rnf


# ---------------------------------------------------------------- ambiente

def alimentacao() -> str:
    """'tomada', 'bateria' ou 'desconhecida' (consulta só no Windows)."""
    if platform.system() != "Windows":
        return "desconhecida"
    import ctypes

    class Status(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                    ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                    ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
    s = Status()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
        return "desconhecida"
    return {0: "bateria", 1: "tomada"}.get(s.ACLineStatus, "desconhecida")


def processador() -> str:
    if platform.system() == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return platform.processor()


# ---------------------------------------------------------------- TFLite

def tipos_tensores(conteudo: bytes) -> dict:
    from tensorflow.lite.python import schema_py_generated as schema
    grafo = schema.Model.GetRootAsModel(conteudo, 0)
    nomes = {v: k for k, v in vars(schema.TensorType).items() if isinstance(v, int)}
    tipos = Counter(grafo.Subgraphs(s).Tensors(i).Type() for s in range(grafo.SubgraphsLength())
                    for i in range(grafo.Subgraphs(s).TensorsLength()))
    return {nomes.get(k, str(k)): v for k, v in sorted(tipos.items())}


class Executor:
    """Encapsula um interpreter TFLite e a (des)quantização de entrada/saída."""

    def __init__(self, conteudo: bytes, threads: int, delegate: str = "xnnpack"):
        import tensorflow as tf
        if delegate not in {"xnnpack", "sem_delegate"}:
            raise ValueError("delegate inválido")
        kwargs = {}
        if delegate == "sem_delegate":
            kwargs["experimental_op_resolver_type"] = tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES
        self.interpreter = tf.lite.Interpreter(model_content=conteudo, num_threads=threads, **kwargs)
        self.interpreter.allocate_tensors()
        es, ss = self.interpreter.get_input_details(), self.interpreter.get_output_details()
        if len(es) != 1 or len(ss) != 1:
            raise ValueError("esperada uma entrada e uma saída")
        self.e, self.s = es[0], ss[0]
        if list(self.e["shape"]) != [1, 224, 224, 3] or list(self.s["shape"]) != [1, 13]:
            raise ValueError("contrato de tensores incompatível")

    def __call__(self, x: np.ndarray) -> np.ndarray:
        e, s = self.e, self.s
        if e["dtype"] == np.int8:
            escala, zero = e["quantization"]
            x = t7_3.quantizar(x, escala, zero)
        self.interpreter.set_tensor(e["index"], x.astype(e["dtype"], copy=False))
        self.interpreter.invoke()
        y = self.interpreter.get_tensor(s["index"])
        if s["dtype"] == np.int8:
            escala, zero = s["quantization"]
            y = (y.astype(np.float32) - zero) * escala
        return np.asarray(y, dtype=np.float32)

    def descricao(self) -> dict:
        def t(d):
            return {"dtype": np.dtype(d["dtype"]).name, "shape": d["shape"].tolist(),
                    "escala": float(d["quantization"][0]), "zero_point": int(d["quantization"][1])}
        return {"entrada": t(self.e), "saida": t(self.s)}


def carregar_artefatos(pacote: Path, fp32: Path, int8: Path) -> dict:
    """Confere FP32 (T7.1) e INT8 (T7.3) contra os contratos e o modelo selecionado."""
    keras_sha = ler(pacote / "manifesto.json")["sha256"]["modelo.keras"]
    contrato32 = ler(fp32 / "contrato_tensores.json")
    contrato8 = ler(int8 / "contrato_int8.json")
    if contrato32["sha256"]["keras"] != keras_sha or contrato8["modelo_keras_sha256"] != keras_sha:
        raise ValueError("FP32 ou INT8 não derivam do checkpoint selecionado")
    if _hash(fp32 / "modelo.tflite") != contrato32["sha256"]["tflite"]:
        raise ValueError("modelo FP32 diverge do contrato T7.1")
    if _hash(int8 / "modelo_int8.tflite") != contrato8["modelo_int8_sha256"]:
        raise ValueError("modelo INT8 diverge do contrato T7.3")
    return {"fp32": (fp32 / "modelo.tflite").read_bytes(), "int8_t7_3": (int8 / "modelo_int8.tflite").read_bytes()}


def converter_estrategias(modelo) -> dict:
    import tensorflow as tf
    saidas = {}
    for nome in ("faixa_dinamica", "float16"):
        conversor = tf.lite.TFLiteConverter.from_keras_model(modelo)
        conversor.optimizations = [tf.lite.Optimize.DEFAULT]
        if nome == "float16":
            conversor.target_spec.supported_types = [tf.float16]
        saidas[nome] = conversor.convert()
    tipos = tipos_tensores(saidas["faixa_dinamica"])
    if not tipos.get("INT8") or tipos.get("FLOAT16"):
        raise ValueError("faixa dinâmica sem pesos INT8")
    if not tipos_tensores(saidas["float16"]).get("FLOAT16"):
        raise ValueError("float16 sem tensores FLOAT16")
    return saidas


def regenerar_int8(raiz: Path, conjunto: Path, indice: Path, pacote: Path, contrato_t7_3: dict) -> tuple[bytes, dict]:
    """Reexecuta a conversão INT8 da T7.3 com o mesmo conjunto de calibração versionado."""
    with tempfile.TemporaryDirectory(prefix="int8-t7-2-") as tmp:
        destino = Path(tmp) / "int8"
        contrato = t7_3.converter(raiz, conjunto, destino, indice, pacote)
        conteudo = (destino / "modelo_int8.tflite").read_bytes()
    if contrato["calibracao"]["image_ids"] != contrato_t7_3["calibracao"]["image_ids"]:
        raise ValueError("calibração regenerada não consumiu os mesmos IDs da T7.3")
    if contrato["calibracao"]["manifesto_sha256"] != contrato_t7_3["calibracao"]["manifesto_sha256"]:
        raise ValueError("manifesto de calibração difere do usado na T7.3")
    return conteudo, contrato


def medir_latencia(executores: dict, x: np.ndarray, aquecimento: int, rodadas: int, por_rodada: int) -> dict:
    """Intercala os modelos em rodadas para diluir variações térmicas/de carga."""
    for ex in executores.values():
        for _ in range(aquecimento):
            ex(x)
    amostras = {n: [] for n in executores}
    for _ in range(rodadas):
        for nome, ex in executores.items():
            for _ in range(por_rodada):
                t0 = time.perf_counter_ns()
                ex(x)
                amostras[nome].append((time.perf_counter_ns() - t0) / 1e6)
    return {n: resumo_latencia(a) for n, a in amostras.items()}


# ---------------------------------------------------------------- fluxo

def comparar(raiz: Path, saida: Path = SAIDA, indice: Path = INDICE, pacote: Path = PACOTE,
             fp32: Path = FP32, int8: Path = INT8, conjunto: Path = CONJUNTO,
             configs: tuple = CONFIGS_LATENCIA, aquecimento: int = 20, rodadas: int = 5, por_rodada: int = 40,
             particoes: tuple = PARTICOES, reamostras: int = 2000, permitir_bateria: bool = False) -> dict:
    if saida.exists():
        raise ValueError("saída já existe; preservar a comparação anterior")
    if not set(particoes) <= set(PARTICOES) or "validacao" not in particoes:
        raise ValueError("a validação é obrigatória; o teste é apenas complementar")
    energia = alimentacao()
    if energia == "bateria" and not permitir_bateria:
        raise ValueError("computador na bateria: conecte à tomada para medir latência (ou use --permitir-bateria)")
    metricas_pacote = ler(pacote / "avaliacao_validacao.json")
    origem = _validar_selecao(pacote / "modelo.keras", pacote / "avaliacao_validacao.json",
                              metricas_pacote["validacao"]["por_classe"], pacote)
    linhas, classes, _ = t7_3.indice_selecionado(indice, pacote)
    nomes = [c["nome"] for c in classes]
    binarios = carregar_artefatos(pacote, fp32, int8)

    # INT8 regenerada pelo fluxo T7.3, com o mesmo conjunto de calibração.
    contrato_t7_3 = ler(int8 / "contrato_int8.json")
    binarios["int8"], contrato_int8 = regenerar_int8(raiz, conjunto, indice, pacote, contrato_t7_3)
    int8_identico = binarios["int8"] == binarios["int8_t7_3"]

    import tensorflow as tf
    import keras
    import keras_hub
    from src.avaliacao_t6_1 import _carregar_modelo
    modelo = _carregar_modelo(pacote / "modelo.keras")
    binarios.update(converter_estrategias(modelo))
    estrategias = list(ESTRATEGIAS) + ([] if int8_identico else ["int8_t7_3"])
    binarios = {n: binarios[n] for n in estrategias}
    executores = {n: Executor(b, threads=4) for n, b in binarios.items()}

    resultados, predicoes = {}, []
    for particao in particoes:
        fotos = [r for r in linhas if r["particao"] == particao]
        rotulos = np.array([int(r["indice_modelo"]) for r in fotos])
        saidas = {n: [] for n in ("keras", *estrategias)}
        for inicio in range(0, len(fotos), 32):
            lote = []
            for r in fotos[inicio:inicio + 32]:
                caminho = raiz / r["caminho_relativo"]
                if _hash(caminho) != r["sha256_original"]:
                    raise ValueError(f"imagem original alterada: {r['image_id']}")
                lote.append(preparar_imagem(caminho, 224))
            lote = np.stack(lote)
            saidas["keras"].append(np.asarray(modelo.predict_on_batch(lote), dtype=np.float32))
            for nome, ex in executores.items():
                saidas[nome].append(np.concatenate([ex(x[None]) for x in lote]))
        saidas = {n: np.concatenate(v) for n, v in saidas.items()}
        for nome, y in saidas.items():
            if not np.isfinite(y).all():
                raise ValueError(f"saída não finita em {nome}")
        previstos = {n: y.argmax(1) for n, y in saidas.items()}
        resultados[particao] = {}
        for nome, y in saidas.items():
            item = {"metricas": calcular_metricas(rotulos, previstos[nome], len(nomes), nomes),
                    "vs_fp32": concordancia(saidas["fp32"], y), "vs_keras": concordancia(saidas["keras"], y)}
            if nome not in ("fp32", "keras"):
                item["estatistica"] = {
                    "mcnemar": mcnemar_exato(rotulos, previstos["fp32"], previstos[nome]),
                    "bootstrap": bootstrap_pareado(rotulos, previstos["fp32"], previstos[nome], len(nomes), reamostras)}
            resultados[particao][nome] = item
        for i, r in enumerate(fotos):
            predicoes.append({"particao": particao, "image_id": r["image_id"], "indice_real": int(rotulos[i]),
                              **{f"previsto_{n}": int(previstos[n][i]) for n in saidas},
                              **{f"score_{n}": f"{float(saidas[n][i].max()):.6f}" for n in saidas}})
        del saidas

    referencia_val = metricas_pacote["validacao"]["f1_macro"]
    obtido_val = resultados["validacao"]["keras"]["metricas"]["f1_macro"]
    if abs(obtido_val - referencia_val) > 1e-6:
        raise ValueError(f"Keras não reproduz o F1 de validação do pacote ({obtido_val} != {referencia_val})")
    del modelo

    # RNF-09: execução sem delegates em uma imagem de validação por classe.
    validacao = sorted((r for r in linhas if r["particao"] == "validacao"), key=lambda r: r["image_id"])
    amostra = [next(r for r in validacao if int(r["indice_modelo"]) == i) for i in range(len(nomes))]
    xs = [preparar_imagem(raiz / r["caminho_relativo"], 224)[None] for r in amostra]
    sem_delegate = {}
    for nome, conteudo in binarios.items():
        ex_sem = Executor(conteudo, threads=4, delegate="sem_delegate")
        y_sem = np.concatenate([ex_sem(x) for x in xs])
        y_com = np.concatenate([executores[nome](x) for x in xs])
        valido = bool(np.isfinite(y_sem).all() and (y_sem >= 0).all() and (y_sem <= 1 + 1e-6).all())
        sem_delegate[nome] = {"imagens": [r["image_id"] for r in amostra], "executou": True, "saidas_validas": valido,
                              "top1_igual_xnnpack": float(np.mean(y_sem.argmax(1) == y_com.argmax(1))),
                              "erro_absoluto_maximo_vs_xnnpack": float(np.abs(y_sem - y_com).max()),
                              "atende": valido}

    x = xs[0]
    latencia = {}
    for delegate, n_threads in configs:
        exs = {n: Executor(b, threads=n_threads, delegate=delegate) for n, b in binarios.items()}
        latencia[f"{delegate}_{n_threads}t"] = medir_latencia(exs, x, aquecimento, rodadas, por_rodada)
        del exs

    resumo = {}
    for nome, conteudo in binarios.items():
        resumo[nome] = {"rotulo": ROTULOS[nome], "tamanho_bytes": len(conteudo),
            "tamanho_relativo_fp32": len(conteudo) / len(binarios["fp32"]),
            "sha256": sha256(conteudo).hexdigest(), "tipos_tensores_grafo": tipos_tensores(conteudo),
            "tensores": executores[nome].descricao()}

    resultado = {"esquema": "comparacao_quantizacao_T7_2_v2", "origem_selecao": origem,
        "modelo_keras_sha256": _hash(pacote / "modelo.keras"), "indice_sha256": _hash(indice),
        "codigo_sha256": {f"src/{p}": _hash(RAIZ / "src" / p) for p in
                          ("comparacao_quantizacao_t7_2.py", "quantizacao_t7_3.py", "preprocessamento.py", "avaliacao.py")},
        "estrategias": resumo,
        "conversao": {"fp32": "reaproveitado de T7.1 (sem otimização)",
            "faixa_dinamica": "TFLiteConverter.from_keras_model; optimizations=[Optimize.DEFAULT]; sem representative_dataset",
            "float16": "TFLiteConverter.from_keras_model; optimizations=[Optimize.DEFAULT]; target_spec.supported_types=[tf.float16]",
            "int8": "regenerada nesta etapa por src.quantizacao_t7_3.converter com o conjunto versionado (200 imagens de treino); TFLITE_BUILTINS_INT8, entrada/saída int8"},
        "int8_reprodutibilidade": {"sha256_regenerado": sha256(binarios["int8"]).hexdigest(),
            "sha256_t7_3": contrato_t7_3["modelo_int8_sha256"], "identico_byte_a_byte": int8_identico,
            "mesmos_ids_calibracao": True, "ambiente_t7_3": "macOS arm64, Python 3.12.15, TensorFlow 2.21.0"},
        "metricas": resultados, "sem_delegate": sem_delegate,
        "latencia": {"descricao": "tempo de set_tensor + invoke + get_tensor (inclui (des)quantização INT8) em uma imagem real 1x224x224x3, tf.lite.Interpreter",
                     "imagem_id": amostra[0]["image_id"], "aquecimento": aquecimento,
                     "rodadas_intercaladas": rodadas, "execucoes_por_rodada": por_rodada, "por_config": latencia},
        "ambiente": {"sistema": platform.platform(), "processador": processador(), "alimentacao": energia,
                     "python": platform.python_version(), "tensorflow": tf.__version__,
                     "keras": keras.__version__, "keras_hub": keras_hub.__version__, "numpy": np.__version__},
        "particao_principal": "validacao", "teste_exploratorio": "teste" in particoes,
        "limite_interpretacao": ("latência medida no CPU x86 de desenvolvimento, não no celular de referência; serve para "
            "comparar estratégias entre si e não aprova o RNF-04. O teste já foi consultado em etapas anteriores e é "
            "apenas exploratório; nenhuma estratégia foi escolhida por ele. Intervalos por bootstrap de imagens não "
            "consideram a dependência entre fotos do mesmo grupo. Scores não são probabilidades calibradas.")}
    resultado["rnf"] = avaliar_rnf(resultado)
    publicar(saida, binarios, contrato_int8, resultado, predicoes)
    return resultado


# ---------------------------------------------------------------- saídas

def linhas_tabela(resultado: dict) -> list[dict]:
    linhas = []
    lat = resultado["latencia"]["por_config"]
    for nome, e in resultado["estrategias"].items():
        linha = {"estrategia": nome, "rotulo": e["rotulo"], "tamanho_bytes": e["tamanho_bytes"],
                 "tamanho_mb": round(e["tamanho_bytes"] / 1e6, 3),
                 "reducao_vs_fp32_pct": round(100 * (1 - e["tamanho_relativo_fp32"]), 2),
                 "rnf01_ate_8mb": e["tamanho_bytes"] <= LIMITE_RNF01_BYTES,
                 "entrada": e["tensores"]["entrada"]["dtype"], "saida": e["tensores"]["saida"]["dtype"]}
        for cfg, v in lat.items():
            linha[f"latencia_mediana_ms_{cfg}"] = round(v[nome]["mediana_ms"], 3)
            linha[f"latencia_p95_ms_{cfg}"] = round(v[nome]["p95_ms"], 3)
        for particao, por_modelo in resultado["metricas"].items():
            m, c = por_modelo[nome]["metricas"], por_modelo[nome]["vs_fp32"]
            ref = por_modelo["fp32"]["metricas"]
            s = "val" if particao == "validacao" else "teste"
            linha[f"f1_macro_{s}"] = round(m["f1_macro"], 6)
            linha[f"balanced_accuracy_{s}"] = round(m["balanced_accuracy"], 6)
            linha[f"acuracia_{s}"] = round(m["acuracia"], 6)
            linha[f"delta_f1_vs_fp32_{s}"] = round(m["f1_macro"] - ref["f1_macro"], 6)
            linha[f"delta_acuracia_macro_pp_{s}"] = round(100 * (m["balanced_accuracy"] - ref["balanced_accuracy"]), 4)
            est = por_modelo[nome].get("estatistica")
            if est:
                b = est["bootstrap"]
                linha[f"ic95_delta_f1_{s}"] = f"[{b['f1_macro']['ic95_inferior']:.4f}; {b['f1_macro']['ic95_superior']:.4f}]"
                linha[f"ic95_delta_acuracia_macro_pp_{s}"] = (f"[{100 * b['balanced_accuracy']['ic95_inferior']:.2f}; "
                                                              f"{100 * b['balanced_accuracy']['ic95_superior']:.2f}]")
                linha[f"mcnemar_p_{s}"] = round(est["mcnemar"]["p_valor"], 4)
            else:
                linha[f"ic95_delta_f1_{s}"] = linha[f"ic95_delta_acuracia_macro_pp_{s}"] = linha[f"mcnemar_p_{s}"] = ""
            linha[f"top1_igual_fp32_{s}"] = round(c["top1_igual_fp32"], 6)
            linha[f"divergencias_top1_{s}"] = c["divergencias_top1"]
            linha[f"erro_abs_max_vs_fp32_{s}"] = round(c["erro_absoluto_maximo"], 6)
        linha["rnf09_sem_delegate"] = resultado["sem_delegate"][nome]["atende"]
        linhas.append(linha)
    return linhas


def relatorio(resultado: dict) -> str:
    tab = linhas_tabela(resultado)
    configs = list(resultado["latencia"]["por_config"])
    f = lambda v, d=4: f"{v:.{d}f}".replace(".", ",")
    sim = lambda b: "sim" if b else "**não**"
    rep = resultado["int8_reprodutibilidade"]
    texto = ["# Comparação das estratégias de quantização — T7.2", "",
             "Candidato: EfficientNet-Lite0 do pacote `candidato_T5_6_20261026` "
             f"(Keras `{resultado['modelo_keras_sha256'][:12]}…`).", "",
             "INT8 regenerada nesta etapa com o conjunto de calibração da T7.3: "
             + ("**idêntica byte a byte** ao artefato publicado na T7.3." if rep["identico_byte_a_byte"]
                else "difere em bytes do artefato T7.3 (ambos avaliados abaixo)."), "",
             "## Tamanho (RNF-01: até 8 MB)", "",
             "| Estratégia | Entrada/saída | Tamanho (bytes) | Redução vs FP32 | Até 8 MB |",
             "| --- | --- | ---: | ---: | --- |"]
    for l in tab:
        bytes_ = f"{l['tamanho_bytes']:,}".replace(",", ".")
        texto.append(f"| {l['rotulo']} | {l['entrada']}/{l['saida']} | {bytes_} | {f(l['reducao_vs_fp32_pct'], 1)}% | {sim(l['rnf01_ate_8mb'])} |")
    texto += ["", "## Latência no CPU local — mediana / p95 (ms)", "",
              "| Estratégia | " + " | ".join(c.replace("_", " ") for c in configs) + " |",
              "| --- | " + " | ".join("---:" for _ in configs) + " |"]
    for l in tab:
        texto.append(f"| {l['rotulo']} | " + " | ".join(
            f"{f(l[f'latencia_mediana_ms_{c}'], 2)} / {f(l[f'latencia_p95_ms_{c}'], 2)}" for c in configs) + " |")
    for particao in resultado["metricas"]:
        s = "val" if particao == "validacao" else "teste"
        por_modelo = resultado["metricas"][particao]
        total = por_modelo["fp32"]["metricas"]["total_amostras"]
        titulo = "validação (partição principal)" if particao == "validacao" else "teste (exploratório, já consultado)"
        texto += ["", f"## Desempenho — {titulo}, {total} imagens", "",
                  "| Estratégia | F1 macro | Δ F1 vs FP32 | IC 95% Δ F1 | Acurácia macro | Δ acurácia macro (p.p.) | IC 95% Δ (p.p.) | RNF-06 (≥ −2 p.p.) | Acurácia | Divergências top-1 | McNemar p | Maior queda de F1 por classe |",
                  "| --- | ---: | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |"]
        for l in tab:
            pior = pior_classe(por_modelo["fp32"]["metricas"], por_modelo[l["estrategia"]]["metricas"])
            pior = "—" if pior is None else f"{pior[0]} ({f(pior[1], 3)})"
            rnf = resultado["rnf"][l["estrategia"]].get(f"RNF-06_{particao}")
            rnf = "—" if rnf is None else f"{sim(rnf['atende_ponto'])} (IC: {sim(rnf['atende_ic95'])})"
            delta = f"{l[f'delta_f1_vs_fp32_{s}']:+.4f}".replace(".", ",")
            delta_pp = f"{l[f'delta_acuracia_macro_pp_{s}']:+.2f}".replace(".", ",")
            mc = "—" if l[f"mcnemar_p_{s}"] == "" else f(l[f"mcnemar_p_{s}"], 3)
            texto.append(f"| {l['rotulo']} | {f(l[f'f1_macro_{s}'])} | {delta} | {l[f'ic95_delta_f1_{s}'].replace('.', ',') or '—'} | "
                         f"{f(l[f'balanced_accuracy_{s}'])} | {delta_pp} | {l[f'ic95_delta_acuracia_macro_pp_{s}'].replace('.', ',') or '—'} | {rnf} | "
                         f"{f(l[f'acuracia_{s}'])} | {l[f'divergencias_top1_{s}']} | {mc} | {pior} |")
        keras = por_modelo["keras"]["metricas"]["f1_macro"]
        texto += ["", f"F1 macro do checkpoint Keras na mesma partição: {f(keras)}."]
    texto += ["", "## Execução sem delegates (RNF-09)", "",
              "| Estratégia | Executou com saídas válidas | Top-1 igual ao XNNPACK | Erro abs. máx. vs XNNPACK |",
              "| --- | --- | ---: | ---: |"]
    for nome, r in resultado["sem_delegate"].items():
        texto.append(f"| {ROTULOS[nome]} | {sim(r['atende'])} | {f(100 * r['top1_igual_xnnpack'], 1)}% | {f(r['erro_absoluto_maximo_vs_xnnpack'], 6)} |")
    a = resultado["ambiente"]
    texto += ["", "## Ambiente e limites", "",
              f"{a['sistema']}; {a['processador']}; alimentação: {a['alimentacao']}; Python {a['python']}; TensorFlow {a['tensorflow']}.",
              resultado["latencia"]["descricao"] + ".", resultado["limite_interpretacao"], ""]
    return "\n".join(texto)


def publicar(saida: Path, binarios: dict, contrato_int8: dict, resultado: dict, predicoes: list) -> None:
    saida.mkdir(parents=True)
    (saida / ARQUIVOS[0]).write_bytes(binarios["faixa_dinamica"])
    (saida / ARQUIVOS[1]).write_bytes(binarios["float16"])
    (saida / ARQUIVOS[2]).write_bytes(binarios["int8"])
    gravar(saida / ARQUIVOS[3], contrato_int8)
    gravar(saida / ARQUIVOS[4], resultado)
    tab = linhas_tabela(resultado)
    with (saida / ARQUIVOS[5]).open("w", encoding="utf-8", newline="") as arq:
        w = csv.DictWriter(arq, fieldnames=list(tab[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(tab)
    with (saida / ARQUIVOS[6]).open("w", encoding="utf-8", newline="") as arq:
        w = csv.writer(arq, lineterminator="\n")
        w.writerow(["particao", "estrategia", "indice", "classe", "suporte", "precisao", "recall", "f1"])
        for particao, por_modelo in resultado["metricas"].items():
            for nome, r in por_modelo.items():
                for c in r["metricas"]["por_classe"]:
                    w.writerow([particao, nome, c["indice"], c["nome"], c["suporte"],
                                *(None if c[k] is None else f"{c[k]:.6f}" for k in ("precisao", "recall", "f1"))])
    with (saida / ARQUIVOS[7]).open("w", encoding="utf-8", newline="") as arq:
        w = csv.DictWriter(arq, fieldnames=list(predicoes[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(predicoes)
    (saida / ARQUIVOS[8]).write_text(relatorio(resultado), encoding="utf-8", newline="\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raiz-imagens", type=Path, required=True)
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument("--indice", type=Path, default=INDICE)
    p.add_argument("--pacote", type=Path, default=PACOTE)
    p.add_argument("--conjunto", type=Path, default=CONJUNTO, help="conjunto de calibração INT8 (T7.3)")
    p.add_argument("--sem-teste", action="store_true", help="avalia somente a validação")
    p.add_argument("--rodadas", type=int, default=5)
    p.add_argument("--por-rodada", type=int, default=40)
    p.add_argument("--reamostras", type=int, default=2000)
    p.add_argument("--permitir-bateria", action="store_true", help="mede latência mesmo fora da tomada")
    a = p.parse_args()
    comparar(a.raiz_imagens, a.saida, a.indice, a.pacote, conjunto=a.conjunto, rodadas=a.rodadas,
             por_rodada=a.por_rodada, particoes=("validacao",) if a.sem_teste else PARTICOES,
             reamostras=a.reamostras, permitir_bateria=a.permitir_bateria)
    print(f"Comparação publicada em {a.saida}")


if __name__ == "__main__":
    main()
