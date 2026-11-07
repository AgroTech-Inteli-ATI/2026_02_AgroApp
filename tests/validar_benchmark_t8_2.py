"""Confere integridade dos artefatos medidos e estatísticas publicadas."""
import argparse
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.benchmark_t8_2 import (
    COMPARACAO, MODELOS, executar, ordem_rodada, resumo, selecionar_modelos,
    validar_parametros, variacao,
)

DADOS = RAIZ / "assets/data/benchmark_T8_2/oficiais_20261106"


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
                self.assertAlmostEqual(r["media_ms"], float(np.mean(tempos)))
                self.assertAlmostEqual(r["p50_ms"], float(np.percentile(tempos, 50)))
                self.assertAlmostEqual(r["p95_ms"], float(np.percentile(tempos, 95)))

    def conferir_estatisticas(self, registro):
        for campo, valor in resumo(registro["duracoes_ms"]).items():
            self.assertAlmostEqual(registro[campo], valor)

    def test_sessoes_oficiais_e_consolidacao(self):
        dados = json.loads((DADOS / "resultados.json").read_text(encoding="utf-8"))
        self.assertEqual(dados["esquema"], "benchmark_T8_2_consolidado_v3")
        self.assertGreaterEqual(len(dados["sessoes"]), 3)
        self.assertEqual(len(set(dados["sessoes"])), len(dados["sessoes"]))
        config = dados["configuracao"]
        self.assertEqual(config["threads"], 1)
        self.assertEqual(config["delegate"], "xnnpack")
        self.assertEqual(config["forma"], [1, 224, 224, 3])
        self.assertEqual(config["batch"], 1)
        oficiais = selecionar_modelos(RAIZ)
        sessoes = []
        for i, pasta in enumerate(dados["sessoes"], 1):
            sessao = json.loads((DADOS / pasta / "resultados.json").read_text(encoding="utf-8"))
            sessoes.append(sessao)
            with self.subTest(sessao=i):
                self.assertEqual(sessao["sessao"], i)
                for campo, valor in config.items():
                    self.assertEqual(sessao[campo], valor)
                self.assertEqual(sessao["codigo_sha256"], hashlib.sha256((DADOS / pasta / "protocolo.py").read_bytes()).hexdigest())
                self.assertEqual([r["versao"] for r in sessao["resultados"]], list(MODELOS))
                self.assertEqual(sessao["repeticoes"], sessao["rodadas"] * sessao["repeticoes_por_bloco"])
                self.assertGreaterEqual(sessao["aquecimento_global"], 20)
                self.assertEqual(sessao["aquecimento_bloco"], 20)
                esperado = [{"rodada": rodada + 1, "versao": nome}
                            for rodada in range(sessao["rodadas"])
                            for nome in ordem_rodada(MODELOS, rodada, i)]
                self.assertEqual(sessao["ordem"], esperado)
                entradas = {}
                for r in sessao["resultados"]:
                    modelo = oficiais[r["versao"]]
                    self.assertEqual(RAIZ / r["modelo"], modelo)
                    self.assertEqual(r["sha256"], hashlib.sha256(modelo.read_bytes()).hexdigest())
                    self.assertEqual(r["bytes"], modelo.stat().st_size)
                    self.assertGreater(r["particoes_delegadas"], 0)
                    self.assertEqual(len(r["duracoes_ms"]), sessao["repeticoes"])
                    self.assertEqual(len(r["blocos"]), sessao["rodadas"])
                    self.conferir_estatisticas(r)
                    entradas.setdefault(r["entrada_dtype"], set()).add(r["entrada_sha256"])
                    concatenadas = []
                    for rodada, bloco in enumerate(r["blocos"], 1):
                        self.assertEqual(bloco["rodada"], rodada)
                        self.assertEqual(bloco["versao"], r["versao"])
                        self.assertEqual(len(bloco["duracoes_ms"]), sessao["repeticoes_por_bloco"])
                        self.conferir_estatisticas(bloco)
                        self.assertGreaterEqual(bloco["cpu_processo_ms"], 0)
                        self.assertGreater(bloco["parede_bloco_ms"], 0)
                        if sessao["sistema"].startswith("Windows"):
                            self.assertEqual(bloco["energia_inicio"], config["energia"])
                            self.assertEqual(bloco["energia_fim"], config["energia"])
                            self.assertIsNotNone(bloco["cpu_total_percentual"])
                            self.assertTrue(0 <= bloco["cpu_total_percentual"] <= 100)
                        concatenadas.extend(bloco["duracoes_ms"])
                    self.assertEqual(concatenadas, r["duracoes_ms"])
                    self.assertAlmostEqual(r["variacao_medianas_blocos_percentual"], variacao([b["p50_ms"] for b in r["blocos"]]))
                self.assertTrue(all(len(hashes) == 1 for hashes in entradas.values()))
        self.assertEqual(len({s["pid"] for s in sessoes}), len(sessoes))
        self.assertEqual([r["versao"] for r in dados["resultados"]], list(MODELOS))
        for posicao, r in enumerate(dados["resultados"]):
            registros = [s["resultados"][posicao] for s in sessoes]
            self.assertEqual(r["duracoes_ms"], [t for registro in registros for t in registro["duracoes_ms"]])
            self.assertEqual(r["medianas_sessoes_ms"], [registro["p50_ms"] for registro in registros])
            self.assertAlmostEqual(r["variacao_medianas_sessoes_percentual"], variacao(r["medianas_sessoes_ms"]))
            self.assertEqual(r["variacao_blocos_por_sessao_percentual"], [registro["variacao_medianas_blocos_percentual"] for registro in registros])
            self.conferir_estatisticas(r)

    def test_csv_corresponde_ao_json(self):
        consolidado = json.loads((DADOS / "resultados.json").read_text(encoding="utf-8"))
        for pasta in [DADOS, *(DADOS / s for s in consolidado["sessoes"])]:
            dados = json.loads((pasta / "resultados.json").read_text(encoding="utf-8"))
            with (pasta / "resumo.csv").open(encoding="utf-8", newline="") as arquivo:
                linhas = list(csv.DictReader(arquivo))
            self.assertEqual(len(linhas), len(dados["resultados"]))
            for linha, registro in zip(linhas, dados["resultados"]):
                for campo, valor in linha.items():
                    self.assertEqual(valor, str(registro[campo]))

    def test_ordem_balanceada(self):
        for sessao in range(1, 4):
            ordens = [ordem_rodada(MODELOS, i, sessao) for i in range(5)]
            for nome in MODELOS:
                self.assertEqual({ordem.index(nome) for ordem in ordens}, set(range(5)))

    def test_recusa_artefato_alterado(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / COMPARACAO).mkdir(parents=True)
            (raiz / COMPARACAO / "comparacao.json").write_bytes((RAIZ / COMPARACAO / "comparacao.json").read_bytes())
            modelo = raiz / MODELOS["fp32"]
            modelo.parent.mkdir(parents=True)
            modelo.write_bytes(b"modelo alterado")
            with self.assertRaisesRegex(ValueError, "diverge"):
                selecionar_modelos(raiz)

    def test_recusa_sobrescrita(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta)
            marcador = saida / "preservar.txt"
            marcador.write_text("medição existente", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                executar(RAIZ, saida)
            self.assertEqual(marcador.read_text(encoding="utf-8"), "medição existente")

    def test_recusa_energia_diferente_da_declarada(self):
        with tempfile.TemporaryDirectory() as pasta:
            for esperada, observada in (("tomada", "bateria"), ("bateria", "tomada")):
                saida = Path(pasta) / esperada
                with patch("src.benchmark_t8_2.estado_sistema", return_value={"energia": observada}):
                    with self.assertRaisesRegex(ValueError, "Fonte de energia"):
                        executar(RAIZ, saida, energia=esperada)
                self.assertFalse(saida.exists())

    def test_recusa_protocolo_e_amostras_invalidos(self):
        for parametros in ((4, 40, 100, 1), (5, 29, 100, 1), (5, 40, 0, 1), (5, 40, 100, 0)):
            with self.subTest(parametros=parametros), self.assertRaises(ValueError):
                validar_parametros(*parametros)
        for amostras in ([], [0], [-1], [float("inf")], [float("nan")]):
            with self.subTest(amostras=amostras), self.assertRaises(ValueError):
                resumo(amostras)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=DADOS)
    args, restantes = parser.parse_known_args()
    DADOS = args.dados
    unittest.main(argv=[sys.argv[0], *restantes])
