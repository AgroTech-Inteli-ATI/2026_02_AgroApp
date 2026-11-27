"""Gera referências sintéticas com o pré-processamento e o TFLite Python.

Ferramenta de desenvolvimento; não é necessária para executar o frontend.
Requer TensorFlow 2.21.0, Pillow 12.2.0 e NumPy 2.4.4 em um ambiente Python separado.
"""

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.preprocessamento import preparar_imagem
from src.benchmark_t5_6 import prever

OUT = ROOT / "frontend/tests/fixtures"
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads((ROOT / "frontend/public/models/manifest.json").read_text(encoding="utf-8"))
if [model["format"] for model in manifest["models"]] != ["Float16", "INT8"]:
    raise ValueError("Esperados Float16 principal e INT8 de contingência")
classes_path = ROOT / manifest["classesSource"]["sourcePath"]
if hashlib.sha256(classes_path.read_bytes()).hexdigest() != manifest["classesSource"]["sha256"]:
    raise ValueError("Hash das classes diverge do manifesto web")
if json.loads(classes_path.read_text(encoding="utf-8")) != manifest["classes"]:
    raise ValueError("Ordem das classes diverge do manifesto web")

def pattern(width, height):
    indices = np.arange(width * height * 3, dtype=np.uint64)
    return ((indices * 37 + indices // 7 * 19) % 256).astype(np.uint8).reshape(height, width, 3)

cases = []
for width, height in [(17, 9), (391, 173), (45, 301), (7, 7), (448, 223), (1, 13)]:
    image = Image.fromarray(pattern(width, height))
    rgb = np.rint(preparar_imagem(image) * 255).astype(np.uint8)
    cases.append({"width": width, "height": height, "sha256": hashlib.sha256(rgb.tobytes()).hexdigest()})

image = Image.fromarray(pattern(391, 173))
image.save(OUT / "pattern.png")
exif = Image.Exif()
exif[274] = 6
image.save(OUT / "orientation.jpg", quality=90, exif=exif)

models = {}
for spec in manifest["models"]:
    model = ROOT / spec["sourcePath"]
    web_model = ROOT / "frontend/public/models" / spec["filename"]
    for model_path, expected_hash in ((model, spec["sourceSha256"]), (web_model, spec["sha256"])):
        if hashlib.sha256(model_path.read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"Hash divergente do manifesto web: {model_path}")
    interpreter = tf.lite.Interpreter(model_path=str(model), num_threads=1)
    interpreter.allocate_tensors()
    web_interpreter = tf.lite.Interpreter(model_path=str(web_model), num_threads=1)
    web_interpreter.allocate_tensors()
    predictions = {}
    for filename in ("pattern.png", "orientation.jpg"):
        prepared = preparar_imagem(OUT / filename)
        expected = prever(interpreter, prepared)
        np.testing.assert_array_equal(expected, prever(web_interpreter, prepared))
        predictions[filename] = expected.tolist()
    models[spec["format"]] = {
        "modelSha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "webModelSha256": hashlib.sha256(web_model.read_bytes()).hexdigest(),
        "webSpecializationVerified": True,
        "modelSourcePath": spec["sourcePath"],
        "modelVersion": spec["version"],
        "predictions": predictions,
        "quantization": {
            "input": interpreter.get_input_details()[0]["quantization"],
            "output": interpreter.get_output_details()[0]["quantization"],
        },
    }

data = {
    "classesSha256": manifest["classesSource"]["sha256"],
    "preprocessing": cases,
    "models": models,
}
(OUT / "reference.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="")
print(json.dumps({"reference": str(OUT), "preprocessing_cases": len(cases), "models_verified": list(models)}))
