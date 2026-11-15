"""Regressão fotográfica do contrato T10.2; não requer TensorFlow."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.preprocessamento import CONTRATO_PREPROCESSAMENTO, decodificar_imagem, preparar_imagem, preparar_pixels
from src.comparacao_preprocessamento_t10_2 import REFERENCE_SOURCES, conferir_codigo

FIXTURES = ROOT / "frontend/tests/fixtures/preprocessing"


class ContratoFotografico(unittest.TestCase):
    def test_referencias_reais_e_normalizacao(self):
        referencia = json.loads((FIXTURES / "reference.json").read_text(encoding="utf-8"))
        self.assertEqual(referencia["contract"], CONTRATO_PREPROCESSAMENTO)
        for caso in referencia["cases"]:
            with self.subTest(caso=caso["file"]):
                caminho = FIXTURES / caso["file"]
                self.assertEqual(hashlib.sha256(caminho.read_bytes()).hexdigest(), caso["sha256"])
                imagem = decodificar_imagem(caminho)
                self.assertEqual(imagem.size, (caso["width"], caso["height"]))
                self.assertEqual(imagem.tobytes(), gzip.decompress((FIXTURES / f'{caso["file"]}.decoded.gz').read_bytes()))
                esperado = gzip.decompress((FIXTURES / f'{caso["file"]}.pixels.gz').read_bytes())
                self.assertEqual(preparar_pixels(caminho).tobytes(), esperado)
                esperado_float = np.frombuffer(esperado, np.uint8).astype(np.float32).reshape(224, 224, 3) / np.float32(255)
                np.testing.assert_array_equal(preparar_imagem(caminho), esperado_float)
                self.assertEqual(hashlib.sha256(esperado_float.astype('<f4').tobytes()).hexdigest(), caso['normalizedSha256'])

    def test_recusa_codigo_desatualizado_ou_incompleto(self):
        hashes = {nome: hashlib.sha256((ROOT / nome).read_bytes()).hexdigest() for nome in REFERENCE_SOURCES}
        conferir_codigo(hashes)
        with self.assertRaisesRegex(ValueError, 'incompleta'):
            conferir_codigo({})
        hashes['src/preprocessamento.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Código alterado'):
            conferir_codigo(hashes)

    def test_ignora_icc_sem_alterar_rgb(self):
        np.testing.assert_array_equal(preparar_pixels(FIXTURES / "photo.png"), preparar_pixels(FIXTURES / "photo-icc.png"))

    def test_oito_orientacoes_sem_mutar_origem(self):
        with Image.open(FIXTURES / "photo.png") as original:
            operacoes = [None, Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.ROTATE_180,
                         Image.Transpose.FLIP_TOP_BOTTOM, Image.Transpose.TRANSPOSE,
                         Image.Transpose.ROTATE_270, Image.Transpose.TRANSVERSE, Image.Transpose.ROTATE_90]
            for i, operacao in enumerate(operacoes, 1):
                with Image.open(FIXTURES / f"exif-{i}.png") as imagem:
                    esperado = original if operacao is None else original.transpose(operacao)
                    self.assertEqual(decodificar_imagem(imagem).tobytes(), esperado.tobytes())
                    self.assertEqual(imagem.getexif()[274], i)
                    np.testing.assert_array_equal(preparar_imagem(imagem), preparar_imagem(imagem))

    def test_recusa_transparencia_inclusive_paleta(self):
        with self.assertRaisesRegex(ValueError, "transparência"):
            preparar_imagem(FIXTURES / "transparent.png")
        paleta = Image.new("P", (2, 2))
        paleta.info["transparency"] = 0
        with self.assertRaisesRegex(ValueError, "transparência"):
            preparar_imagem(paleta)

    def test_valida_tamanho_e_fecha_arquivo(self):
        for tamanho in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                preparar_imagem(FIXTURES / "photo.png", tamanho)
        with Image.open(FIXTURES / "photo.png") as imagem:
            preparado = decodificar_imagem(imagem)
        self.assertEqual(preparado.mode, "RGB")
        self.assertTrue(preparado.tobytes())


if __name__ == "__main__":
    unittest.main()
