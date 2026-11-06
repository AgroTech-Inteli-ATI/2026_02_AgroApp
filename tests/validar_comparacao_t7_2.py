"""Testes da comparação de quantização T7.2.

A maior parte não depende de TensorFlow nem do acervo externo; o teste de
conversão é pulado quando o TensorFlow não está instalado.
"""

import copy
import importlib.util
from math import comb
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import comparacao_quantizacao_t7_2 as c
from src.avaliacao import calcular_metricas

TEM_TF = importlib.util.find_spec("tensorflow") is not None


def resultado_fixture(tamanho_int8=300):
    nomes = [f"classe {i}" for i in range(13)]
    rotulos = np.arange(26) % 13
    previstos = {"fp32": rotulos.copy(), "faixa_dinamica": rotulos.copy(), "float16": rotulos.copy(),
                 "int8": rotulos.copy(), "keras": rotulos.copy()}
    previstos["int8"][0] = 1  # um erro na classe 0
    metricas = {}
    for particao in ("validacao", "teste"):
        metricas[particao] = {}
        for n, p in previstos.items():
            item = {"metricas": calcular_metricas(rotulos, p, 13, nomes),
                    "vs_fp32": {"top1_igual_fp32": float(np.mean(p == rotulos)), "divergencias_top1": int(np.sum(p != rotulos)),
                                "erro_absoluto_maximo": 0.1}, "vs_keras": {}}
            if n not in ("fp32", "keras"):
                item["estatistica"] = {"mcnemar": c.mcnemar_exato(rotulos, previstos["fp32"], p),
                                       "bootstrap": c.bootstrap_pareado(rotulos, previstos["fp32"], p, 13, reamostras=50)}
            metricas[particao][n] = item
    lat = {n: c.resumo_latencia([1.0, 2.0, 3.0]) for n in c.ESTRATEGIAS}
    lat_lenta = {n: c.resumo_latencia([400.0, 500.0]) for n in c.ESTRATEGIAS}
    tamanhos = {"fp32": 9_000_000, "faixa_dinamica": 280, "float16": 500, "int8": tamanho_int8}
    resultado = {"modelo_keras_sha256": "a" * 64,
            "estrategias": {n: {"rotulo": c.ROTULOS[n], "tamanho_bytes": t, "tamanho_relativo_fp32": t / 9_000_000,
                                "tensores": {"entrada": {"dtype": "int8" if n == "int8" else "float32"},
                                             "saida": {"dtype": "int8" if n == "int8" else "float32"}}}
                            for n, t in tamanhos.items()},
            "metricas": metricas,
            "sem_delegate": {n: {"atende": True, "top1_igual_xnnpack": 1.0, "erro_absoluto_maximo_vs_xnnpack": 0.0}
                             for n in c.ESTRATEGIAS},
            "latencia": {"descricao": "fixture", "por_config": {"xnnpack_1t": lat, "sem_delegate_1t": lat_lenta}},
            "int8_reprodutibilidade": {"identico_byte_a_byte": True},
            "ambiente": {"sistema": "s", "processador": "p", "alimentacao": "tomada", "python": "3", "tensorflow": "t"},
            "limite_interpretacao": "fixture"}
    resultado["rnf"] = c.avaliar_rnf(resultado)
    return resultado


class ComparacaoTest(unittest.TestCase):
    def test_resumo_latencia(self):
        r = c.resumo_latencia([4.0, 1.0, 3.0, 2.0, 5.0])
        self.assertEqual((r["execucoes"], r["mediana_ms"], r["min_ms"], r["max_ms"]), (5, 3.0, 1.0, 5.0))
        self.assertAlmostEqual(r["p90_ms"], 4.6)
        self.assertAlmostEqual(r["p95_ms"], 4.8)
        self.assertAlmostEqual(r["media_ms"], 3.0)
        with self.assertRaises(ValueError):
            c.resumo_latencia([1.0])

    def test_concordancia(self):
        ref = np.array([[0.9, 0.1], [0.2, 0.8], [0.6, 0.4]], dtype=np.float32)
        outra = np.array([[0.8, 0.2], [0.3, 0.7], [0.4, 0.6]], dtype=np.float32)
        r = c.concordancia(ref, outra)
        self.assertAlmostEqual(r["top1_igual_fp32"], 2 / 3)
        self.assertEqual(r["divergencias_top1"], 1)
        self.assertAlmostEqual(r["erro_absoluto_maximo"], 0.2, places=6)
        with self.assertRaises(ValueError):
            c.concordancia(ref, outra[:2])

    def test_mcnemar_exato(self):
        y = np.zeros(20, dtype=int)
        self.assertEqual(c.mcnemar_exato(y, y, y)["p_valor"], 1.0)
        ref = np.zeros(20, dtype=int)
        outra = ref.copy()
        outra[:6] = 1           # 6 acertos perdidos, nenhum ganho
        r = c.mcnemar_exato(y, ref, outra)
        self.assertEqual((r["so_referencia_acertou"], r["so_quantizado_acertou"]), (6, 0))
        self.assertAlmostEqual(r["p_valor"], 2 * comb(6, 0) / 2 ** 6)
        outra[6] = 1
        ref2 = ref.copy()
        ref2[7] = 1             # 1 ganho: b=7, c=1
        r = c.mcnemar_exato(y, ref2, outra)
        self.assertAlmostEqual(r["p_valor"], 2 * (comb(8, 0) + comb(8, 1)) / 2 ** 8)

    def test_bootstrap_pareado(self):
        y = np.arange(60) % 3
        r = c.bootstrap_pareado(y, y, y, 3, reamostras=100)
        self.assertEqual(r["f1_macro"], {"ic95_inferior": 0.0, "ic95_superior": 0.0})
        pior = y.copy()
        pior[:15] = (pior[:15] + 1) % 3
        r = c.bootstrap_pareado(y, y, pior, 3, reamostras=200)
        self.assertLess(r["f1_macro"]["ic95_superior"], 0)
        self.assertLess(r["balanced_accuracy"]["ic95_inferior"], r["balanced_accuracy"]["ic95_superior"])
        self.assertEqual(r, c.bootstrap_pareado(y, y, pior, 3, reamostras=200))  # semente fixa

    def test_pior_classe(self):
        nomes = ["a", "b", "c"]
        y = np.array([0, 1, 2, 0, 1, 2])
        ref = calcular_metricas(y, y, 3, nomes)
        self.assertIsNone(c.pior_classe(ref, ref))
        nome, delta = c.pior_classe(ref, calcular_metricas(y, np.array([0, 1, 2, 1, 1, 2]), 3, nomes))
        self.assertEqual(nome, "a")
        self.assertLess(delta, 0)

    def test_rnf(self):
        rnf = resultado_fixture()["rnf"]
        self.assertFalse(rnf["fp32"]["RNF-01"]["atende"])           # 9 MB > 8 MB
        self.assertTrue(rnf["int8"]["RNF-01"]["atende"])
        self.assertNotIn("RNF-06_validacao", rnf["fp32"])
        self.assertTrue(rnf["float16"]["RNF-06_validacao"]["atende_ponto"])
        # Um erro em 2 imagens da classe 0 derruba a acurácia macro em 50/13 p.p.
        self.assertAlmostEqual(rnf["int8"]["RNF-06_validacao"]["delta_pp"], -100 * 0.5 / 13)
        self.assertFalse(rnf["int8"]["RNF-06_validacao"]["atende_ponto"])
        self.assertTrue(rnf["int8"]["RNF-04_indicativo_local"]["xnnpack_1t"]["abaixo_de_300ms"])
        self.assertFalse(rnf["int8"]["RNF-04_indicativo_local"]["sem_delegate_1t"]["abaixo_de_300ms"])
        self.assertTrue(rnf["int8"]["RNF-09"]["atende"])

    def test_tabela_e_relatorio(self):
        r = resultado_fixture()
        tab = c.linhas_tabela(r)
        self.assertEqual([l["estrategia"] for l in tab], list(c.ESTRATEGIAS))
        por_nome = {l["estrategia"]: l for l in tab}
        self.assertEqual(por_nome["fp32"]["delta_f1_vs_fp32_val"], 0)
        self.assertEqual(por_nome["fp32"]["mcnemar_p_val"], "")
        self.assertLess(por_nome["int8"]["delta_f1_vs_fp32_val"], 0)
        self.assertFalse(por_nome["fp32"]["rnf01_ate_8mb"])
        for chave in ("tamanho_bytes", "latencia_mediana_ms_xnnpack_1t", "latencia_p95_ms_sem_delegate_1t",
                      "f1_macro_val", "f1_macro_teste", "ic95_delta_f1_val", "delta_acuracia_macro_pp_val",
                      "mcnemar_p_val", "rnf09_sem_delegate"):
            self.assertIn(chave, tab[0])
        texto = c.relatorio(r)
        for trecho in ("FP32 (referência, T7.1)", "INT8 inteira (regenerada na T7.2)", "idêntica byte a byte",
                       "validação (partição principal)", "teste (exploratório, já consultado)",
                       "| classe 0 (", "RNF-09", "alimentação: tomada"):
            self.assertIn(trecho, texto)

    def test_publicar_e_recusa_de_sobrescrita(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "comparacao"
            binarios = {"faixa_dinamica": b"dr", "float16": b"f16", "int8": b"i8"}
            predicoes = [{"particao": "validacao", "image_id": "IMG_1", "indice_real": 0}]
            c.publicar(saida, binarios, {"contrato": 1}, resultado_fixture(), predicoes)
            self.assertEqual(sorted(p.name for p in saida.iterdir()), sorted(c.ARQUIVOS))
            self.assertEqual((saida / "modelo_int8.tflite").read_bytes(), b"i8")
            self.assertNotIn(b"\r\n", (saida / "relatorio_comparacao.md").read_bytes())
            self.assertNotIn(b"\r\n", (saida / "comparacao.json").read_bytes())
            with self.assertRaises(ValueError):
                c.comparar(Path(tmp), saida)

    def test_validacao_obrigatoria_e_bateria(self):
        with tempfile.TemporaryDirectory() as tmp:
            for particoes in (("teste",), ("validacao", "treino")):
                with self.assertRaises(ValueError):
                    c.comparar(Path(tmp), Path(tmp) / "nova", particoes=particoes)
            original = c.alimentacao
            c.alimentacao = lambda: "bateria"
            try:
                with self.assertRaisesRegex(ValueError, "bateria"):
                    c.comparar(Path(tmp), Path(tmp) / "nova")
            finally:
                c.alimentacao = original
        self.assertIn(c.alimentacao(), {"tomada", "bateria", "desconhecida"})

    def test_recusa_artefatos_divergentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            pacote, fp32, int8 = raiz / "pacote", raiz / "fp32", raiz / "int8"
            for p in (pacote, fp32, int8):
                p.mkdir()
            (fp32 / "modelo.tflite").write_bytes(b"fp32")
            (int8 / "modelo_int8.tflite").write_bytes(b"int8")
            c.gravar(pacote / "manifesto.json", {"sha256": {"modelo.keras": "k"}})
            contrato32 = {"sha256": {"keras": "k", "tflite": c._hash(fp32 / "modelo.tflite")}}
            contrato8 = {"modelo_keras_sha256": "k", "modelo_int8_sha256": c._hash(int8 / "modelo_int8.tflite")}
            c.gravar(fp32 / "contrato_tensores.json", contrato32)
            c.gravar(int8 / "contrato_int8.json", contrato8)
            self.assertEqual(c.carregar_artefatos(pacote, fp32, int8), {"fp32": b"fp32", "int8_t7_3": b"int8"})
            for alterar in ("keras32", "keras8", "arquivo32", "arquivo8"):
                c32, c8 = copy.deepcopy(contrato32), copy.deepcopy(contrato8)
                if alterar == "keras32":
                    c32["sha256"]["keras"] = "outro"
                elif alterar == "keras8":
                    c8["modelo_keras_sha256"] = "outro"
                elif alterar == "arquivo32":
                    c32["sha256"]["tflite"] = "0" * 64
                else:
                    c8["modelo_int8_sha256"] = "0" * 64
                c.gravar(fp32 / "contrato_tensores.json", c32)
                c.gravar(int8 / "contrato_int8.json", c8)
                with self.subTest(alterar=alterar), self.assertRaises(ValueError):
                    c.carregar_artefatos(pacote, fp32, int8)

    def test_regenerar_int8_recusa_calibracao_diferente(self):
        original = c.t7_3.converter

        def falso(raiz, conjunto, destino, indice, pacote):
            destino.mkdir(parents=True)
            (destino / "modelo_int8.tflite").write_bytes(b"novo")
            return {"calibracao": {"image_ids": ["A", "B"], "manifesto_sha256": "m"}}
        c.t7_3.converter = falso
        try:
            conteudo, _ = c.regenerar_int8(Path("."), Path("."), Path("."), Path("."),
                                           {"calibracao": {"image_ids": ["A", "B"], "manifesto_sha256": "m"}})
            self.assertEqual(conteudo, b"novo")
            for contrato in ({"calibracao": {"image_ids": ["A"], "manifesto_sha256": "m"}},
                             {"calibracao": {"image_ids": ["A", "B"], "manifesto_sha256": "outro"}}):
                with self.assertRaises(ValueError):
                    c.regenerar_int8(Path("."), Path("."), Path("."), Path("."), contrato)
        finally:
            c.t7_3.converter = original

    @unittest.skipUnless(TEM_TF, "TensorFlow não instalado")
    def test_conversoes_e_executor(self):
        import keras
        entrada = keras.Input((224, 224, 3))
        x = keras.layers.Conv2D(64, 3, strides=4, activation="relu")(entrada)
        x = keras.layers.GlobalAveragePooling2D()(x)
        modelo = keras.Model(entrada, keras.layers.Dense(13, activation="softmax")(x))
        binarios = c.converter_estrategias(modelo)
        self.assertIn("INT8", c.tipos_tensores(binarios["faixa_dinamica"]))
        self.assertIn("FLOAT16", c.tipos_tensores(binarios["float16"]))
        amostra = np.random.default_rng(42).random((1, 224, 224, 3), dtype=np.float32)
        referencia = np.asarray(modelo(amostra, training=False))
        for nome, conteudo in binarios.items():
            for delegate in ("xnnpack", "sem_delegate"):
                ex = c.Executor(conteudo, threads=1, delegate=delegate)
                self.assertEqual(ex.descricao()["entrada"]["dtype"], "float32")
                y = ex(amostra)
                self.assertEqual(y.shape, (1, 13))
                self.assertTrue(np.allclose(y, referencia, atol=0.05), (nome, delegate))
        with self.assertRaises(ValueError):
            c.Executor(binarios["float16"], 1, delegate="gpu")
        lat = c.medir_latencia({"f16": c.Executor(binarios["float16"], 1)}, amostra, 1, 2, 2)
        self.assertEqual(lat["f16"]["execucoes"], 4)


if __name__ == "__main__":
    unittest.main()
