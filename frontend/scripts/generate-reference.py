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
MODEL = ROOT / "assets/modelos/candidato_T5_6_20261026/modelo_int8.tflite"
interpreter = tf.lite.Interpreter(model_path=str(MODEL), num_threads=1)
interpreter.allocate_tensors()
web_model = ROOT / "frontend/public/models/modelo_int8_web.tflite"
web_interpreter = tf.lite.Interpreter(model_path=str(web_model), num_threads=1)
web_interpreter.allocate_tensors()

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

predictions = {}
for filename in ("pattern.png", "orientation.jpg"):
    prepared = preparar_imagem(OUT / filename)
    expected = prever(interpreter, prepared)
    np.testing.assert_array_equal(expected, prever(web_interpreter, prepared))
    predictions[filename] = expected.tolist()

data = {
    "modelSha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
    "webModelSha256": hashlib.sha256(web_model.read_bytes()).hexdigest(),
    "webSpecializationVerified": True,
    "preprocessing": cases,
    "predictions": predictions,
    "quantization": {
        "input": interpreter.get_input_details()[0]["quantization"],
        "output": interpreter.get_output_details()[0]["quantization"],
    },
}
(OUT / "reference.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"reference": str(OUT), "preprocessing_cases": len(cases), "predictions": predictions}))
