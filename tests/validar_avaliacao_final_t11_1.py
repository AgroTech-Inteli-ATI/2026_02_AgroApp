"""Valida as regras da T11.1 e a coerência dos artefatos publicados (sem TensorFlow)."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import avaliacao_final_t11_1 as t11
from src.avaliacao import calcular_metricas

SAIDA = t11.SAIDA


class RegrasTest(unittest.TestCase):
    def test_sensibilidade_exclui_so_vinculos_com_particoes_anteriores(self):
        grupos = t11._csv(t11.GRUPOS_T10_1)
        self.assertEqual(t11.excluidos_por_vinculo(grupos, "teste"), ["IMG_01835", "IMG_01874"])
        # IMG_01752 (validação) só tem vínculo com o teste, que não influenciou o modelo.
        self.assertEqual(t11.excluidos_por_vinculo(grupos, "validacao"), [])

    def test_acuracia_um_contra_todos_top3_e_politica(self):
        nomes = ["a", "b", "c", "d"]
        rotulos = np.array([0, 0, 1, 2])
        scores = np.array([[.9, .05, .03, .02], [.4, .5, .05, .05], [.1, .7, .1, .1], [.3, .3, .2, .2]])
        m = t11.metricas(rotulos, scores, nomes, 0.65, bootstrap=False)
        a = {c["indice"]: c for c in m["por_classe"]}
        self.assertAlmostEqual(a[0]["acuracia_ovr"], 2 / 4)  # 1 FN em 0, 1 FP em 0 (classe 2 → 0)
        self.assertAlmostEqual(a[1]["acuracia_ovr"], 3 / 4)
        self.assertEqual(m["top3_acuracia"], 1.0)
        pc = m["politica_confianca"]
        self.assertEqual((pc["aceitos"], pc["erros_aceitos"], pc["acertos_inconclusivos"]), (2, 0, 0))

    def test_bootstrap_reproduzivel(self):
        rng = np.random.default_rng(0)
        rotulos = rng.integers(0, 13, 60)
        scores = rng.random((60, 13))
        a = t11.metricas(rotulos, scores, [str(i) for i in range(13)], 0.65)["ic95_bootstrap"]
        b = t11.metricas(rotulos, scores, [str(i) for i in range(13)], 0.65)["ic95_bootstrap"]
        self.assertEqual(a, b)
        self.assertLessEqual(a["acuracia"][0], a["acuracia"][1])


class BuildTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.build = self.root / "dist"
        (self.build / "models").mkdir(parents=True)
        (self.root / "classes.json").write_bytes(b"[]")
        (self.build / "models/m.tflite").write_bytes(b"modelo")
        manifesto = {
            "classesSource": {"sourcePath": "classes.json", "sha256": hashlib.sha256(b"[]").hexdigest()},
            "classes": [{"indice": i, "nome": str(i)} for i in range(13)],
            "models": [{"filename": "m.tflite", "bytes": 6, "sha256": hashlib.sha256(b"modelo").hexdigest()}],
        }
        (self.build / "models/manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")

    def conferir(self):
        with patch.object(t11, "RAIZ", self.root):
            return t11.conferir_build(self.build)

    def test_aceita_build_integro(self):
        self.assertEqual(len(self.conferir()["classes"]), 13)

    def test_recusa_modelo_adulterado(self):
        (self.build / "models/m.tflite").write_bytes(b"modelX")
        with self.assertRaisesRegex(ValueError, "modelo do build diverge"):
            self.conferir()

    def test_recusa_classes_adulteradas(self):
        (self.root / "classes.json").write_bytes(b"[1]")
        with self.assertRaisesRegex(ValueError, "classes.json diverge"):
            self.conferir()

    def test_recusa_indice_diferente_do_auditado(self):
        outro = self.root / "indice.csv"
        outro.write_text("image_id\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "auditado na T10.1"):
            t11.carregar_indice(outro, [])


@unittest.skipUnless((SAIDA / "metricas.json").is_file(), "artefatos da T11.1 ainda não gerados")
class ArtefatosTest(unittest.TestCase):
    """Os artefatos publicados são coerentes entre si e com a T8.1."""

    @classmethod
    def setUpClass(cls):
        cls.dados = json.loads((SAIDA / "metricas.json").read_text(encoding="utf-8"))
        cls.predicoes = t11._csv(SAIDA / "predicoes.csv")

    def test_metricas_recalculadas_das_predicoes(self):
        for particao, r in self.dados["resultados"].items():
            for formato, m in r["modelos"].items():
                linhas = [l for l in self.predicoes if l["particao"] == particao and l["modelo"] == formato]
                scores = np.array([[float(l[f"score_{k}"]) for k in range(13)] for l in linhas])
                rotulos = np.array([int(l["indice_real"]) for l in linhas])
                self.assertTrue((scores.argmax(axis=1) == [int(l["indice_previsto"]) for l in linhas]).all())
                novo = calcular_metricas(rotulos, scores.argmax(axis=1), 13)
                self.assertEqual(novo["matriz_confusao"], m["integral"]["matriz_confusao"])
                self.assertAlmostEqual(novo["f1_macro"], m["integral"]["f1_macro"], places=12)

    def test_teste_reproduz_t8_1(self):
        with (t11.RAIZ / "assets/data/avaliacao_T8_1/candidato_T5_6_20261026/metricas_gerais.csv").open(encoding="utf-8") as f:
            t8 = {l["versao"]: l for l in csv.DictReader(f)}
        for formato, versao in (("Float16", "float16"), ("INT8", "int8_t7_3")):
            m = self.dados["resultados"]["teste"]["modelos"][formato]
            self.assertAlmostEqual(m["integral"]["f1_macro"], float(t8[versao]["f1_macro"]), places=12)
            self.assertEqual(m["concordancia_T8_1"]["iguais"], m["concordancia_T8_1"]["total"])

    def test_identifica_build_e_classificacao(self):
        p = self.dados["proveniencia"]
        self.assertEqual(self.dados["classificacao"], "exploratoria")
        self.assertFalse(self.dados["generalizacao_comprovada"])
        manifesto = json.loads((t11.BUILD / "models/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({f: a["sha256"] for f, a in p["arquivos_modelo"].items()},
                         {m["format"]: m["sha256"] for m in manifesto["models"]})
        for r in self.dados["resultados"].values():
            for m in r["modelos"].values():
                self.assertEqual(len(m["integral"]["por_classe"]), 13)


if __name__ == "__main__":
    unittest.main()
