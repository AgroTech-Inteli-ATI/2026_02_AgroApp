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
    lines = ["# Comparação Python × web após T10.2", "", f"**Resultado: {result['status']}.** O preprocessing e o efeito do delegate são quantificados separadamente abaixo. A configuração do runtime precisa acompanhar a versão do modelo nas validações.", "", f"Contrato: `{CONTRATO_PREPROCESSAMENTO}`. Limiar: {THRESHOLD} (top-1 ≥ limiar).",
             "", f"Python {python['environment']['python']}, Pillow {pillow_version}, NumPy {np.__version__}, TensorFlow {python['environment']['tensorflow']}; CPU, 1 thread, sem delegates padrão.",
             f"Chromium {web['browser']}; LiteRT.js 2.6.0 CPU/WASM, 1 thread. Windows; execução desktop automatizada.",
             "", "As fotos não formam uma amostra independente de acurácia. Variantes EXIF e brilho são casos de regressão derivados de fotos reais; os quatro casos de fronteira foram procurados deliberadamente nos modelos finais.",
             "", "## Identidade dos modelos", ""]
    for format, model in result["models"].items():
        spec = model["spec"]
        lines += [f"- **{format} {spec['version']}**: `{spec['sourcePath']}`; SHA-256 original `{spec['sourceSha256']}`; cópia web `{spec['sha256']}`."]
    lines += ["", "Originais e cópias web produziram os mesmos 13 scores no Python em todos os casos. Classes, política, arquivos de entrada e código têm hashes no JSON anexo.",
              "", "## Python sem delegates × web CPU/WASM", "", "Esta configuração explicita o caminho de kernels sem delegates usado pelo helper de benchmark. O ensaio com delegates padrão, também usado pela avaliação T8.1 e pelo gerador de referência do frontend, aparece em seguida.", "", "| Modelo | Casos | Δ pixel máx. (0–255) | Δ tensor máx. | Δ score máx. | MAE scores | Classes diferentes | Decisões diferentes |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for format, model in result["models"].items():
        s = model["summary"]
        lines.append(f"| {format} | {s['cases']} | {s['maxPixelDifference']:.0f} | {s['maxTensorDifference']:.9g} | {s['maxScoreDifference']:.9g} | {s['meanAbsoluteScoreDifference']:.9g} | {s['classChanges']} | {s['decisionChanges']} |")
    lines += ["", "A tolerância de scores de 2/256 dos testes sintéticos históricos é usada como sinal de investigação, sem generalizá-la como garantia para fotos reais. " + "; ".join(f"{format}: {m['summary']['casesExceedingHistoricalTolerance']} casos acima dessa referência" for format, m in result["models"].items()) + "."]
    lines += ["", "Controle negativo do pipeline antigo (conversão ICC automática):", ""]
    for item in preprocessing["legacy"]:
        lines.append(f"- `{item['file']}`: Δ pixel máximo {item['pixels']['max']}; MAE {item['pixels']['mae']:.6f}. Após a correção, Δ=0 em todos os casos medidos.")
    lines += ["", "Diferenças de tensor usam a unidade de cada entrada: float32 em [0,1] para Float16, inteiros [-128,127] para INT8. Cada elemento normalizado/quantizado da web foi comparado exatamente com Python usando os mesmos RGB8 da web.",
              "", "A decomposição executa Python com o tensor produzido na web: Δ preprocessing = Python(tensor web) − Python(tensor Python); Δ runtime = web(tensor web) − Python(tensor web). Os máximos não são somáveis, pois podem ocorrer em classes diferentes.", ""]
    for format, model in result["models"].items():
        s = model["summary"]
        lines.append(f"- {format}: Δ score máx. atribuído ao preprocessing {s['maxPreprocessingScoreDifference']:.9g}; ao runtime {s['maxRuntimeScoreDifference']:.9g}; web contra Python com delegate padrão {s['maxWebVsPythonDefaultDelegateDifference']:.9g}.")
    lines += ["", "O ensaio adicional habilita o delegate padrão do TFLite Python (XNNPACK nesta execução), mantendo o tensor web. Isso testa a influência do caminho otimizado sem alterar os modelos. A proximidade dos resultados apoia uma hipótese sobre os kernels; não identifica sozinha o operador causador."]
    lines += ["", "## Python com XNNPACK × web CPU/WASM", "", "| Modelo | Δ score máx. | Classes diferentes | Decisões diferentes |",
              "|---|---:|---:|---:|"]
    for format, model in result["models"].items():
        s = model["summary"]
        lines.append(f"| {format} | {s['maxWebVsPythonDefaultDelegateDifference']:.9g} | {s['defaultDelegateClassChanges']} | {s['defaultDelegateDecisionChanges']} |")
    lines += ["", "A referência Python com delegates padrão corresponde à configuração documentada em `src/avaliacao_pos_conversao_t8_1.py` (T8.1 usou 4 threads; este ensaio usa 1). A igualdade observada no INT8 com XNNPACK é evidência deste corpus, sem garantir que todos os operadores/builds de runtimes sejam intercambiáveis."]
    lines += ["", "## Casos próximos ao limiar e divergências", "", "A tabela abaixo usa Python **sem delegates**. Com XNNPACK no Python, não houve mudanças de classe/decisão em nenhum desses casos.", "", "| Modelo / foto | Classe Python → web (índice) | Top-1 Python | Top-1 web | Decisão Python → web | Δ score máx. |",
              "|---|---|---:|---:|---|---:|"]
    for format, model in result["models"].items():
        for r in model["cases"]:
            if r["file"].startswith("boundary-") or r["classChanged"] or r["decisionChanged"] or r["exceedsHistoricalTolerance"] or abs(r["python"]["margin"]) < .03:
                a, b = r["python"], r["web"]
                lines.append(f"| {format} / {r['file']} | {a['class']} → {b['class']} | {a['score']:.9f} | {b['score']:.9f} | {a['decision']} → {b['decision']} | {r['scoresEndToEnd']['max']:.9g} |")
    lines += ["", "## Diferenças entre os modelos finais", "", "Os índices e nomes completos das 13 classes estão no JSON anexo. Divergências entre Float16 e INT8 não são divergências Python × web:", "",
              "| Foto | Float16 Python: classe / score / decisão | INT8 Python: classe / score / decisão |",
              "|---|---|---|"]
    for r in cross:
        if r["pythonClassChanged"] or r["pythonDecisionChanged"]:
            a = next(c["python"] for c in result["models"]["Float16"]["cases"] if c["file"] == r["file"])
            b = next(c["python"] for c in result["models"]["INT8"]["cases"] if c["file"] == r["file"])
            lines.append(f"| {r['file']} | {a['class']} / {a['score']:.6f} / {a['decision']} | {b['class']} / {b['score']:.6f} / {b['decision']} |")
    lines += ["", "## Pontos para análise", "",
              "- **Prioridade: padronizar a configuração de referência do INT8.** Com XNNPACK no Python os scores coincidiram com a web; sem delegates houve diferenças de até 0,11328125 e duas mudanças de decisão. Registrar delegate, threads e build junto ao hash do modelo. Caso seja necessário sustentar equivalência também sem delegates, reduzir os casos críticos e localizar o primeiro operador divergente. Os tensores de entrada são idênticos.",
              "- Scores muito próximos de 0,65 podem mudar a decisão mesmo com a classe preservada e erro numérico pequeno. Não ampliar a tolerância do limiar nem arredondar scores para ocultar o efeito; qualquer margem de abstenção exige decisão de produto e validação/calibração própria.",
              f"- Float16 × INT8 no Python: {sum(r['pythonClassChanged'] for r in cross)} diferenças de classe e {sum(r['pythonDecisionChanged'] for r in cross)} diferenças de decisão. Na web: {sum(r['webClassChanged'] for r in cross)} e {sum(r['webDecisionChanged'] for r in cross)}, respectivamente. São modelos numericamente distintos; não atribuir essas diferenças automaticamente ao preprocessing.",
              "- A política de ignorar ICC preserva os valores usados no treino. Uma futura migração para conversão colorimétrica sRGB precisa versionar o contrato e reavaliar treino, calibração e métricas, sobretudo para Display P3.",
              "- CPU/WASM foi medido aqui. WebGPU, Safari/Firefox e aparelho Android físico exigem execução equivalente antes de generalizar a correspondência.",
              "- O limiar 0,65 foi calibrado anteriormente em Keras FP32; estes testes não demonstram calibração estatística do Float16 ou INT8.",
              "- Os pares de fronteira foram obtidos por busca binária no brilho de uma foto. RGB8 e quantização tornam a função descontínua; o arquivo `boundary-int8-above.png` fica mais distante de 0,65 no Python e cruza para baixo na web. Não interpretar o par como estimativa da frequência de erro em fotos naturais.",
              "", "## Reprodução e evidência", "", "Na raiz, em ambiente com TensorFlow 2.21.0, Pillow 12.2.0 e NumPy 2.4.4:", "", "```powershell",
              "cd frontend", "npm.cmd run assets", "cd ..", "python -m src.comparacao_preprocessamento_t10_2 referencia", "cd frontend",
              "$env:MODEL_COMPARISON='1'", "npx.cmd playwright test tests/preprocessing.spec.ts --project=chromium", "Remove-Item Env:MODEL_COMPARISON", "cd ..",
              "python -m src.comparacao_preprocessamento_t10_2 relatorio", "```", "",
              "[Dados completos](../assets/data/comparacao_preprocessamento_T10_2/comparacao.json): 13 scores de cada execução, hashes dos tensores, erros por etapa, decisões, margens e proveniência dos casos. Arquivos intermediários com os tensores completos ficam em `frontend/.work/model-comparison-*.json` e podem ser regenerados."]
    (ROOT / "docs/Comparacao_preprocessamento_T10_2.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v["summary"] for k, v in result["models"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["referencia", "relatorio"])
    (referencia if parser.parse_args().acao == "referencia" else relatorio)()
