"""Confere integridade dos artefatos medidos e estatísticas publicadas."""
import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]


class BenchmarkTest(unittest.TestCase):
    def test_evidencias(self):
        dados = json.loads((RAIZ / "assets/data/benchmark_T8_2/resultados.json").read_text(encoding="utf-8"))
        modelos = set((RAIZ / "assets/modelos/rodadas_T5_6_20261026").glob("*/conversao_t5_6/modelo_*.tflite"))
        self.assertEqual({RAIZ / r["modelo"] for r in dados["resultados"]}, modelos)
        self.assertEqual(len(modelos), 6)
        self.assertGreaterEqual(dados["repeticoes"], 30)
        for r in dados["resultados"]:
            with self.subTest(modelo=r["modelo"]):
                modelo = RAIZ / r["modelo"]
                self.assertEqual(r["bytes"], modelo.stat().st_size)
                self.assertEqual(r["sha256"], hashlib.sha256(modelo.read_bytes()).hexdigest())
                tempos = r["duracoes_ms"]
                self.assertEqual(len(tempos), dados["repeticoes"])
                self.assertTrue(np.isfinite(tempos).all())
                self.assertGreater(min(tempos), 0)
                self.assertAlmostEqual(r["p50_ms"], float(np.percentile(tempos, 50)))
                self.assertAlmostEqual(r["p95_ms"], float(np.percentile(tempos, 95)))


if __name__ == "__main__":
    unittest.main()
