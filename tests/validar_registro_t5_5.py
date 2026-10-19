"""Casos sintéticos do consolidador, sem TensorFlow e sem resultados fictícios na entrega."""

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.registro_experimentos_t5_5 import consolidar, gerar


class RegistroTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.entrada = self.raiz / "runs"

    def gravar(self, rodada, nome, valor):
        pasta = self.entrada / rodada
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / nome).write_text(json.dumps(valor), encoding="utf-8")
        return pasta

    def test_consolidacao_e_reprodutibilidade(self):
        config = {"backbone": "mobilenet_v3_small", "batch": 32, "semente": 42}
        pasta = self.gravar("a", "config_usada.json", config)
        classes = [{"indice": 0, "nome": "classe", "precisao": 0.5,
                    "recall": 1, "f1": 2 / 3, "suporte": 1},
                   {"indice": 1, "nome": "ausente", "precisao": None,
                    "recall": None, "f1": None, "suporte": 0}]
        self.gravar("a", "metricas_validacao.json", {
            "esquema": "metricas_validacao_T5_1_v1", "backbone": config["backbone"],
            "validacao": {"f1_macro": 2 / 3, "por_classe": classes}})
        (pasta / "melhor_modelo.keras").write_bytes(b"modelo sintetico")
        self.gravar("a", "registro_t5_5.json", {"latencia": {
            "estimativa_ms": 12.5, "dispositivo": "CPU teste", "runtime": "Keras",
            "precisao": "float32", "batch": 1, "metodo": "mediana de 30 inferências",
            "fonte": "benchmark local sintético"}})
        self.gravar("b", "config_usada.json", config)
        self.gravar("b", "registro_t5_5.json", {
            "status": "descartada", "motivo_descarte": "erro | memória\ninsuficiente"})
        self.gravar("c", "config_usada.json", config)
        saida = self.raiz / "saida"
        linhas = gerar(self.entrada, saida)
        self.assertEqual(len(linhas), 3)
        self.assertEqual(linhas[0]["tamanho_modelo_bytes"], 16)
        self.assertEqual(linhas[0]["latencia_estimada_ms"], 12.5)
        self.assertEqual(json.loads(linhas[0]["hiperparametros"]), config)
        self.assertEqual(json.loads(linhas[0]["desempenho_por_classe"]), classes)
        self.assertEqual(linhas[1]["status"], "descartada")
        self.assertIsNone(linhas[1]["f1_macro_validacao"])
        self.assertEqual(linhas[2]["status"], "incompleta")
        with (saida / "experimentos.csv").open(encoding="utf-8", newline="") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 3)
        antes = (saida / "experimentos.md").read_bytes()
        gerar(self.entrada, saida)
        self.assertEqual(antes, (saida / "experimentos.md").read_bytes())
        self.assertIn(b"&#124;", antes)

    def test_vazio(self):
        saida = self.raiz / "saida"
        self.assertEqual(gerar(self.entrada, saida), [])
        self.assertIn("Nenhuma execução", (saida / "experimentos.md").read_text(encoding="utf-8"))

    def test_recusa_descarte_sem_motivo_e_latencia_sem_contexto(self):
        for registro in ({"status": "descartada"}, {"latencia": {"estimativa_ms": 5}},
                         {"latencia": {"estimativa_ms": -1}},
                         {"artefato_modelo": "../fora.keras"}):
            with self.subTest(registro=registro):
                self.gravar("a", "registro_t5_5.json", registro)
                with self.assertRaises(ValueError):
                    consolidar(self.entrada)

    def test_recusa_metrica_invalida(self):
        self.gravar("a", "metricas_validacao.json", {
            "esquema": "metricas_validacao_T5_1_v1", "validacao": {"f1_macro": 1.5}})
        with self.assertRaises(ValueError):
            consolidar(self.entrada)


if __name__ == "__main__":
    unittest.main()
