"""Comparação reproduzível Python TFLite × Chromium/LiteRT.js após T10.2.

python -m src.comparacao_preprocessamento_t10_2 referencia
MODEL_COMPARISON=1 npx playwright test tests/preprocessing.spec.ts --project=chromium
python -m src.comparacao_preprocessamento_t10_2 relatorio
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import platform
import runpy
from datetime import datetime, timezone

import numpy as np
from PIL import Image, __version__ as pillow_version

from src.preprocessamento import CONTRATO_PREPROCESSAMENTO, decodificar_imagem, preparar_imagem, preparar_pixels
from src.benchmark_t5_6 import interpretador, prever

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "frontend/tests/fixtures/preprocessing"
WORK = ROOT / "frontend/.work"
OUT = ROOT / "assets/data/comparacao_preprocessamento_T10_2"
POLICY = ROOT / "assets/data/politica_T6_5/parametros.json"
THRESHOLD = json.loads(POLICY.read_text(encoding="utf-8"))["limiar_confianca"]
REFERENCE_SOURCES = (
    "src/preprocessamento.py", "frontend/src/lib/preprocess.ts",
    "frontend/src/lib/inference.worker.ts", "frontend/tests/preprocessing.worker.ts",
    "frontend/tests/preprocessing.spec.ts", "src/comparacao_preprocessamento_t10_2.py",
    "frontend/package-lock.json", "frontend/src/lib/confidence.ts",
    "src/benchmark_t5_6.py", "frontend/scripts/generate-preprocessing-reference.py",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def conferir_codigo(esperado):
    """Recusa referências antigas em vez de atribuir diferenças a outro código."""
    if set(esperado) != set(REFERENCE_SOURCES):
        raise ValueError("Referência de código incompleta; regenere a comparação")
    for nome, hash_esperado in esperado.items():
        if sha((ROOT / nome).read_bytes()) != hash_esperado:
            raise ValueError(f"Código alterado após referência: {nome}")


def models():
    manifest = read(ROOT / "frontend/public/models/manifest.json")
    if sha((ROOT / manifest["classesSource"]["sourcePath"]).read_bytes()) != manifest["classesSource"]["sha256"]:
        raise ValueError("Classes divergentes do manifesto")
    result = {}
    for spec in manifest["models"]:
        source = ROOT / spec["sourcePath"]
        web = ROOT / "frontend/public/models" / spec["filename"]
        if sha(source.read_bytes()) != spec["sourceSha256"] or sha(web.read_bytes()) != spec["sha256"]:
            raise ValueError("Modelo divergente do manifesto")
        result[spec["format"]] = {"spec": spec, "original": interpretador(source, 1), "web": interpretador(web, 1)}
    return manifest, result


def tensor(pixels, spec):
    values = pixels.astype(np.float32) / np.float32(255)
    if spec["input"]["dtype"] == "int8":
        values = np.clip(np.rint(values / np.float32(spec["input"]["scale"]) + spec["input"]["zeroPoint"]), -128, 127).astype(np.int8)
    return values


def stats(actual, expected):
    if actual.shape != expected.shape:
        raise ValueError(f"Formas divergentes: {actual.shape} / {expected.shape}")
    delta = np.abs(actual.astype(np.float64) - expected.astype(np.float64))
    return {"max": float(delta.max()), "mae": float(delta.mean()), "changed": int(np.count_nonzero(delta)), "total": int(delta.size)}


def decision(scores):
    score = float(max(scores))
    return {"class": int(np.argmax(scores)), "score": score,
            "decision": "aceito" if score >= THRESHOLD else "inconclusivo", "margin": score - THRESHOLD}


def referencia():
    import tensorflow as tf
    manifest, interpreters = models()
    # Controlled brightness probes find a crossing on each final model. These
    # are numerical stress cases, not an independent accuracy/calibration set.
    pool = sorted((ROOT / "assets/revisão_imagens").glob("*.jpg"))
    probes = []
    for format, model in interpreters.items():
        ranked = [(float(max(prever(model["original"], preparar_imagem(path)))), path) for path in pool]
        score, source = max(ranked, key=lambda item: item[0])
        if score < THRESHOLD:
            raise ValueError(f"Sem foto aceita para procurar fronteira {format}")
        image = np.asarray(decodificar_imagem(source))

        def predict(factor):
            photo = Image.fromarray(np.rint(image.astype(np.float64) * factor).clip(0, 255).astype(np.uint8))
            return photo, prever(model["original"], preparar_imagem(photo))

        low, high = 0.0, 1.0
        if max(predict(low)[1]) >= THRESHOLD:
            raise ValueError("Extremo escuro não cruza o limiar")
        for _ in range(18):
            middle = (low + high) / 2
            if max(predict(middle)[1]) >= THRESHOLD:
                high = middle
            else:
                low = middle
        for side, factor in [("below", low), ("above", high)]:
            photo, scores = predict(factor)
            filename = f"boundary-{format.lower()}-{side}.png"
            photo.save(FIXTURES / filename)
            probes.append({"file": filename, "source": str(source.relative_to(ROOT)).replace("\\", "/"),
                           "sourceSha256": sha(source.read_bytes()), "operation": "round_even(RGB8 * brightness)",
                           "brightness": factor, "selectedForModel": format, "selectedForRuntime": "sem delegates", **decision(scores)})
    write(FIXTURES / "boundary-provenance.json", probes)
    runpy.run_path(str(ROOT / "frontend/scripts/generate-preprocessing-reference.py"), run_name="__main__")
    cases = read(FIXTURES / "reference.json")["cases"]
    predictions = {}
    for format, model in interpreters.items():
        output = {}
        default_interpreter = interpretador(ROOT / model["spec"]["sourcePath"], 1, "padrao")
        for case in cases:
            image = preparar_imagem(FIXTURES / case["file"])
            scores = prever(model["original"], image)
            np.testing.assert_array_equal(scores, prever(model["web"], image))
            default_scores = prever(default_interpreter, image)
            output[case["file"]] = {"scores": scores.tolist(), **decision(scores),
                                    "defaultDelegateScores": default_scores.tolist(), "defaultDelegate": decision(default_scores),
                                    "tensorSha256": sha(tensor(preparar_pixels(FIXTURES / case["file"]), model["spec"]).tobytes())}
        predictions[format] = {"spec": model["spec"], "cases": output, "originalEqualsWebSpecialization": True}
    write(WORK / "model-comparison-python.json", {
        "contract": CONTRATO_PREPROCESSAMENTO, "createdUtc": datetime.now(timezone.utc).isoformat(),
        "codeSha256": {name: sha((ROOT / name).read_bytes()) for name in REFERENCE_SOURCES},
        "fixturesReferenceSha256": sha((FIXTURES / "reference.json").read_bytes()),
        "environment": {"python": platform.python_version(), "pillow": pillow_version, "numpy": np.__version__,
                        "tensorflow": tf.__version__, "platform": platform.platform(), "delegate": "BUILTIN_WITHOUT_DEFAULT_DELEGATES", "threads": 1},
        "classesSha256": manifest["classesSource"]["sha256"], "policySha256": sha(POLICY.read_bytes()),
        "threshold": THRESHOLD, "cases": cases, "boundaryProbes": probes, "models": predictions,
    })
    print(f"OK: {len(cases)} fotos × 2 modelos; especializações web idênticas no Python")


def relatorio():
    python = read(WORK / "model-comparison-python.json")
    web = read(WORK / "model-comparison-web.json")
    preprocessing = read(WORK / "preprocessing-metrics.json")
    conferir_codigo(python["codeSha256"])
    if web["codeSha256"] != python["codeSha256"]:
        raise ValueError("Código divergente entre as execuções Python e web")
    reference_hash = sha((FIXTURES / "reference.json").read_bytes())
    if any(data["fixturesReferenceSha256"] != reference_hash for data in (python, web, preprocessing)):
        raise ValueError("Referências fotográficas alteradas entre as execuções")
    if web["contract"] != CONTRATO_PREPROCESSAMENTO or preprocessing["contract"] != CONTRATO_PREPROCESSAMENTO:
        raise ValueError("Contrato web divergente da referência Python")
    manifest, interpreters = models()
    if python["contract"] != CONTRATO_PREPROCESSAMENTO or python["policySha256"] != sha(POLICY.read_bytes()):
        raise ValueError("Contrato/política alterado após referência")
    result = {"contract": CONTRATO_PREPROCESSAMENTO, "createdUtc": datetime.now(timezone.utc).isoformat(),
              "pythonEnvironment": python["environment"], "webEnvironment": {"browser": web["browser"], "platform": web["platform"]},
              "classesSha256": python["classesSha256"], "classes": manifest["classes"], "policySha256": python["policySha256"], "threshold": THRESHOLD,
              "codeSha256": python["codeSha256"], "fixturesReferenceSha256": reference_hash,
              "fixtures": python["cases"], "boundaryProbes": python["boundaryProbes"], "preprocessing": preprocessing, "models": {}}
    for model in web["models"]:
        format = model["format"]
        spec = interpreters[format]["spec"]
        if model["spec"] != spec or python["models"][format]["spec"] != spec:
            raise ValueError("Versão final divergente entre ambientes")
        if {c["file"] for c in model["cases"]} != {c["file"] for c in python["cases"]}:
            raise ValueError("Cobertura de casos divergente")
        rows = []
        default_interpreter = interpretador(ROOT / spec["sourcePath"], 1, "padrao")
        for case in model["cases"]:
            name = case["file"]
            source = FIXTURES / name
            fixture = next(c for c in python["cases"] if c["file"] == name)
            if sha(source.read_bytes()) != fixture["sha256"]:
                raise ValueError("Fixture alterada após referência")
            pixels = np.frombuffer(base64.b64decode(case["pixels"]), np.uint8).reshape(224, 224, 3)
            expected_pixels = preparar_pixels(source)
            web_tensor_bytes = base64.b64decode(case["tensor"])
            # This exact check distinguishes normalization/quantization bugs
            # from decoding differences before comparing native input tensors.
            if tensor(pixels, spec).tobytes() != web_tensor_bytes:
                raise ValueError(f"Normalização/quantização divergente: {format}/{name}")
            native_tensor = tensor(expected_pixels, spec)
            actual_tensor = np.frombuffer(web_tensor_bytes, native_tensor.dtype).reshape(native_tensor.shape)
            py_native = np.asarray(python["models"][format]["cases"][name]["scores"])
            py_web_input = prever(interpreters[format]["original"], pixels.astype(np.float32) / np.float32(255))
            py_default = prever(default_interpreter, pixels.astype(np.float32) / np.float32(255))
            web_scores = np.asarray(case["scores"])
            row = {"file": name, "pixels": stats(pixels, expected_pixels), "tensor": stats(actual_tensor, native_tensor),
                   "pythonTensorSha256": sha(native_tensor.tobytes()), "webTensorSha256": sha(web_tensor_bytes),
                   "pythonScores": py_native.tolist(), "pythonOnWebTensorScores": py_web_input.tolist(), "pythonDefaultDelegateOnWebTensorScores": py_default.tolist(), "webScores": web_scores.tolist(),
                   "scoresEndToEnd": stats(web_scores, py_native), "scoresPreprocessingOnly": stats(py_web_input, py_native),
                   "scoresRuntimeOnly": stats(web_scores, py_web_input), "scoresWebVsPythonDefaultDelegate": stats(web_scores, py_default),
                   "python": decision(py_native), "web": decision(web_scores)}
            row["pythonDefaultDelegate"] = decision(py_default)
            row["defaultDelegateClassChanged"] = row["pythonDefaultDelegate"]["class"] != row["web"]["class"]
            row["defaultDelegateDecisionChanged"] = row["pythonDefaultDelegate"]["decision"] != row["web"]["decision"]
            if row["web"]["decision"] != case["decision"]:
                raise ValueError("Política web divergente")
            row["classChanged"] = row["python"]["class"] != row["web"]["class"]
            row["decisionChanged"] = row["python"]["decision"] != row["web"]["decision"]
            # A score can cross whenever the error bound reaches the threshold.
            row["thresholdAtRisk"] = abs(row["python"]["margin"]) <= row["scoresEndToEnd"]["max"]
            row["exceedsHistoricalTolerance"] = row["scoresEndToEnd"]["max"] > 2 / 256
            rows.append(row)
        result["models"][format] = {"spec": spec, "runtime": model["runtime"], "originalEqualsWebSpecialization": True,
                                     "cases": rows, "summary": {
            "cases": len(rows), "maxPixelDifference": max(r["pixels"]["max"] for r in rows),
            "maxTensorDifference": max(r["tensor"]["max"] for r in rows),
            "maxScoreDifference": max(r["scoresEndToEnd"]["max"] for r in rows),
            "meanAbsoluteScoreDifference": float(np.mean([r["scoresEndToEnd"]["mae"] for r in rows])),
            "maxPreprocessingScoreDifference": max(r["scoresPreprocessingOnly"]["max"] for r in rows),
            "maxRuntimeScoreDifference": max(r["scoresRuntimeOnly"]["max"] for r in rows),
            "maxWebVsPythonDefaultDelegateDifference": max(r["scoresWebVsPythonDefaultDelegate"]["max"] for r in rows),
            "defaultDelegateClassChanges": sum(r["defaultDelegateClassChanged"] for r in rows),
            "defaultDelegateDecisionChanges": sum(r["defaultDelegateDecisionChanged"] for r in rows),
            "casesExceedingHistoricalTolerance": sum(r["exceedsHistoricalTolerance"] for r in rows),
            "classChanges": sum(r["classChanged"] for r in rows), "decisionChanges": sum(r["decisionChanged"] for r in rows),
            "thresholdAtRisk": sum(r["thresholdAtRisk"] for r in rows),
        }}
    cross = []
    for a, b in zip(result["models"]["Float16"]["cases"], result["models"]["INT8"]["cases"], strict=True):
        if a["file"] != b["file"]:
            raise ValueError("Ordem divergente entre modelos")
        cross.append({"file": a["file"], "pythonScores": stats(np.array(a["pythonScores"]), np.array(b["pythonScores"])),
                      "pythonClassChanged": a["python"]["class"] != b["python"]["class"],
                      "pythonDecisionChanged": a["python"]["decision"] != b["python"]["decision"],
                      "webClassChanged": a["web"]["class"] != b["web"]["class"],
                      "webDecisionChanged": a["web"]["decision"] != b["web"]["decision"]})
    result["betweenModels"] = cross
    aligned = all(m["summary"]["maxWebVsPythonDefaultDelegateDifference"] <= (0 if f == "INT8" else 1e-5)
                  and not m["summary"]["defaultDelegateClassChanges"] and not m["summary"]["defaultDelegateDecisionChanges"]
                  for f, m in result["models"].items())
    result["status"] = "correspondencia_com_XNNPACK_divergencia_INT8_sem_delegate" if aligned else "requer_analise_mesmo_com_delegate_alinhado"
    write(OUT / "comparacao.json", result)
    # Consulte a analise descritiva na secao 10.3 de docs/Projeto.md.
    print(json.dumps({k: v["summary"] for k, v in result["models"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["referencia", "relatorio"])
    (referencia if parser.parse_args().acao == "referencia" else relatorio)()
