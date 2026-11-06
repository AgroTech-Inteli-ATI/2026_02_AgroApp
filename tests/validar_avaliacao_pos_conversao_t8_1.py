"""Testa proveniência e comparação T8.1 sem TensorFlow ou acervo externo."""

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import avaliacao_pos_conversao_t8_1 as a
from src.avaliacao import calcular_metricas


def json_gravar(p, valor):
    p.write_text(json.dumps(valor, ensure_ascii=False), encoding="utf-8", newline="")


def csv_gravar(p, linhas):
    p.write_text(a.csv_texto(linhas), encoding="utf-8", newline="")


class AvaliacaoPosConversaoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raiz = Path(self.tmp.name)
        self.fontes = {n: raiz / n for n in ("comparacao", "original", "pacote", "fp32", "int8")}
        for p in self.fontes.values():
            p.mkdir()
        self.fontes["indice"] = raiz / "indice.csv"
        self.saida = raiz / "saida"
        self.criar_fixture()

    def criar_fixture(self):
        f = self.fontes
        classes = [{"indice": i, "nome": f"Classe {i}"} for i in range(13)]
        nomes = [c["nome"] for c in classes]
        indice = [{"image_id": f"IMG_{i:03}", "indice_modelo": i % 13,
                   "nome_classe_modelo": nomes[i % 13], "particao": "teste",
                   "caminho_relativo": f"dataset/{i}.jpg", "grupo_particao": f"G{i}",
                   "sha256_original": f"hash{i}"} for i in range(26)]
        csv_gravar(f["indice"], indice)
        y = np.arange(26) % 13
        self.previstos = {n: y.copy() for n in a.VERSOES}
        self.previstos["keras"][0] = 1
        self.previstos["fp32"] = self.previstos["keras"].copy()
        self.previstos["fp32"][4] = 5  # referências distintas para testar os deltas
        self.previstos["float16"] = self.previstos["keras"].copy()
        self.previstos["faixa_dinamica"][1] = 2  # ganha um acerto, perde outro
        self.previstos["int8_t7_3"][2] = 3
        self.previstos["int8"][3] = 4
        metricas = {n: calcular_metricas(y, p, 13, nomes) for n, p in self.previstos.items()}
        pacote = f["pacote"]
        (pacote / "modelo.keras").write_bytes(b"keras-fixture")
        json_gravar(pacote / "classes.json", classes)
        json_gravar(pacote / "avaliacao_validacao.json", {"fixture": True})
        manifesto = {"sha256": {n: a.hash_arquivo(pacote / n) for n in
                                 ("modelo.keras", "classes.json", "avaliacao_validacao.json")},
                     "indice_sha256": a.hash_arquivo(f["indice"]), "execucao_t5_5": "fixture"}
        json_gravar(pacote / "manifesto.json", manifesto)
        original = f["original"]
        json_gravar(original / "metricas_teste.json", {
            "sha256": {"modelo": manifesto["sha256"]["modelo.keras"], "indice_pipeline": a.hash_arquivo(f["indice"])},
            "teste": metricas["keras"]})
        csv_gravar(original / "predicoes_teste.csv", [{"image_id": r["image_id"],
                   "indice_real": i % 13, "indice_previsto": int(self.previstos["keras"][i])}
                  for i, r in enumerate(indice)])
        self.regravar_proveniencia_original()
        origem = {"manifesto_sha256": a.hash_arquivo(pacote / "manifesto.json"),
                  "classes_sha256": manifesto["sha256"]["classes.json"],
                  "metricas_validacao_sha256": manifesto["sha256"]["avaliacao_validacao.json"],
                  "execucao_t5_5": "fixture"}
        estrategias = {}
        for n in a.VERSOES[1:]:
            p = (f["fp32"] / "modelo.tflite" if n == "fp32" else
                 f["int8"] / "modelo_int8.tflite" if n == "int8_t7_3" else
                 f["comparacao"] / f"modelo_{n}.tflite")
            p.write_bytes(n.encode("ascii"))
            estrategias[n] = {"sha256": a.hash_arquivo(p), "tamanho_bytes": p.stat().st_size}
            if n in ("fp32", "int8", "int8_t7_3"):
                c = {"classes": classes, "sha256": {"keras": manifesto["sha256"]["modelo.keras"], "tflite": a.hash_arquivo(p)},
                     "modelo_keras_sha256": manifesto["sha256"]["modelo.keras"], "modelo_int8_sha256": a.hash_arquivo(p)}
                nome = "contrato_tensores.json" if n == "fp32" else "contrato_int8.json" if n == "int8_t7_3" else "contrato_int8_regenerado.json"
                json_gravar(p.parent / nome, c)
        fonte = {"esquema": "comparacao_quantizacao_T7_2_v2", "origem_selecao": origem,
                 "modelo_keras_sha256": manifesto["sha256"]["modelo.keras"], "indice_sha256": a.hash_arquivo(f["indice"]),
                 "codigo_sha256": {"src/avaliacao.py": a.hash_arquivo(a.RAIZ / "src/avaliacao.py")},
                 "estrategias": estrategias, "metricas": {"teste": {n: {"metricas": m} for n, m in metricas.items()}},
                 "ambiente": {"fixture": True}}
        json_gravar(f["comparacao"] / "comparacao.json", fonte)
        csv_gravar(f["comparacao"] / "predicoes.csv", [{"particao": "teste", "image_id": r["image_id"],
                   "indice_real": i % 13, **{f"previsto_{n}": int(self.previstos[n][i]) for n in a.VERSOES}}
                  for i, r in enumerate(indice)])

    def regravar_proveniencia_original(self):
        f = self.fontes
        pacote, original = f["pacote"], f["original"]
        json_gravar(original / "proveniencia_avaliacao.json", {
            "artefatos_sha256": {n: a.hash_arquivo(original / n) for n in ("metricas_teste.json", "predicoes_teste.csv")},
            "manifesto_pacote_sha256": a.hash_arquivo(pacote / "manifesto.json"),
            "modelo_sha256": a.hash_arquivo(pacote / "modelo.keras"), "indice_sha256": a.hash_arquivo(f["indice"]),
            "execucao_t5_5": "fixture"})

    def alterar_predicoes(self, mudar):
        p = self.fontes["comparacao"] / "predicoes.csv"
        linhas = a.ler_csv(p)
        mudar(linhas)
        csv_gravar(p, linhas)

    def test_publicacao_com_proveniencia_e_deltas(self):
        dados = a.executar(self.saida, **self.fontes)
        gerais = {r["versao"]: r for r in a.ler_csv(self.saida / "metricas_gerais.csv")}
        for n, m in dados["metricas"].items():
            delta = 100 * (m["f1_macro"] - dados["metricas"]["keras"]["f1_macro"])
            self.assertEqual(float(gerais[n]["delta_f1_macro_vs_keras_pp"]), delta)
            delta_fp32 = 100 * (m["f1_macro"] - dados["metricas"]["fp32"]["f1_macro"])
            self.assertEqual(float(gerais[n]["delta_f1_macro_vs_fp32_pp"]), delta_fp32)
            self.assertEqual(sum(map(sum, m["matriz_confusao"])), 26)
            self.assertEqual(len(a.ler_csv(self.saida / "matrizes" / f"{n}.csv")), 13)
        self.assertEqual(gerais["faixa_dinamica"]["acertos_perdidos_vs_keras"], "1")
        self.assertEqual(gerais["faixa_dinamica"]["acertos_ganhos_vs_keras"], "1")
        self.assertEqual(len(a.ler_csv(self.saida / "comparacao_por_classe.csv")), 78)
        self.assertEqual(len(a.ler_csv(self.saida / "predicoes_teste.csv")), 26)
        self.assertNotEqual(gerais["float16"]["delta_f1_macro_vs_keras_pp"],
                            gerais["float16"]["delta_f1_macro_vs_fp32_pp"])
        prov = a.ler_json(self.saida / "proveniencia.json")
        self.assertFalse(prov["nova_inferencia"])
        self.assertFalse(prov["teste_independente"])
        self.assertEqual(prov["referencia_principal"], "keras")
        for n, h in prov["artefatos_sha256"].items():
            self.assertEqual(a.hash_arquivo(self.saida / n), h)
            self.assertNotIn(b"\r\n", (self.saida / n).read_bytes())

    def test_ordem_das_linhas_nao_altera_resultados(self):
        antes = a.carregar(**self.fontes)
        self.alterar_predicoes(lambda ls: ls.reverse())
        depois = a.carregar(**self.fontes)
        self.assertEqual(antes["metricas"], depois["metricas"])
        self.assertEqual(a.comparar(antes), a.comparar(depois))

    def test_recusa_id_ausente(self):
        self.alterar_predicoes(lambda ls: ls.pop())
        with self.assertRaisesRegex(ValueError, "IDs de teste"):
            a.executar(self.saida, **self.fontes)
        self.assertFalse(self.saida.exists())

    def test_recusa_id_duplicado(self):
        self.alterar_predicoes(lambda ls: ls.append(ls[0].copy()))
        with self.assertRaisesRegex(ValueError, "repetida"):
            a.carregar(**self.fontes)

    def test_recusa_rotulo_divergente(self):
        self.alterar_predicoes(lambda ls: ls[0].update(indice_real="2"))
        with self.assertRaisesRegex(ValueError, "rótulo real"):
            a.carregar(**self.fontes)

    def test_recusa_classe_fora_da_faixa(self):
        self.alterar_predicoes(lambda ls: ls[0].update(previsto_int8="13"))
        with self.assertRaisesRegex(ValueError, "fora das classes"):
            a.carregar(**self.fontes)

    def test_recusa_particao_trocada(self):
        self.alterar_predicoes(lambda ls: ls[0].update(particao="validacao"))
        with self.assertRaisesRegex(ValueError, "partição declarada"):
            a.carregar(**self.fontes)

    def test_recusa_modelo_alterado(self):
        (self.fontes["int8"] / "modelo_int8.tflite").write_bytes(b"modelo substituido")
        with self.assertRaisesRegex(ValueError, "hash divergente"):
            a.carregar(**self.fontes)

    def test_recusa_previsao_incompativel_com_metricas(self):
        self.alterar_predicoes(lambda ls: ls[0].update(previsto_float16="4"))
        with self.assertRaisesRegex(ValueError, "métricas recalculadas"):
            a.carregar(**self.fontes)

    def test_recusa_referencia_keras_trocada(self):
        self.alterar_predicoes(lambda ls: ls[0].update(previsto_keras="4"))
        with self.assertRaisesRegex(ValueError, "referência original"):
            a.carregar(**self.fontes)

    def test_recusa_indice_alterado(self):
        with self.fontes["indice"].open("a", encoding="utf-8") as f:
            f.write("\n")
        with self.assertRaises(ValueError):
            a.carregar(**self.fontes)

    def test_recusa_classes_do_contrato_trocadas(self):
        p = self.fontes["int8"] / "contrato_int8.json"
        c = a.ler_json(p)
        c["classes"][0]["nome"] = "Outra classe"
        json_gravar(p, c)
        with self.assertRaisesRegex(ValueError, "classes do contrato"):
            a.carregar(**self.fontes)

    def test_recusa_origem_de_outro_candidato(self):
        p = self.fontes["comparacao"] / "comparacao.json"
        c = a.ler_json(p)
        c["origem_selecao"]["manifesto_sha256"] = "0" * 64
        json_gravar(p, c)
        with self.assertRaisesRegex(ValueError, "candidato"):
            a.carregar(**self.fontes)

    def test_recusa_troca_do_int8_oficial_pelo_regenerado(self):
        oficial = self.fontes["int8"] / "modelo_int8.tflite"
        regenerado = self.fontes["comparacao"] / "modelo_int8.tflite"
        oficial.write_bytes(regenerado.read_bytes())
        with self.assertRaisesRegex(ValueError, "hash divergente"):
            a.carregar(**self.fontes)

    def test_recusa_sobrescrita(self):
        a.executar(self.saida, **self.fontes)
        antes = (self.saida / "proveniencia.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "saída já existe"):
            a.executar(self.saida, **self.fontes)
        self.assertEqual(antes, (self.saida / "proveniencia.json").read_bytes())

    def test_dados_reais_versionados(self):
        dados = a.carregar()
        self.assertEqual(len(dados["ids"]), 473)
        self.assertEqual(dados["metricas"]["keras"]["classes_avaliadas"], 13)
        np.testing.assert_array_equal(dados["previstos"]["keras"], dados["previstos"]["fp32"])
        np.testing.assert_array_equal(dados["previstos"]["keras"], dados["previstos"]["float16"])
        gerais, classes, _, mudancas = a.comparar(dados)
        oficial = next(r for r in gerais if r["versao"] == "int8_t7_3")
        self.assertLess(oficial["delta_acuracia_vs_keras_pp"], 0)
        self.assertGreater(oficial["delta_f1_macro_vs_keras_pp"], 0)
        self.assertTrue(any(r["versao"] == "int8_t7_3" and r["delta_f1_vs_keras_pp"] < 0 for r in classes))
        self.assertEqual(sum(r["tipo"] == "acerto_perdido" and r["versao"] == "int8_t7_3" for r in mudancas),
                         oficial["acertos_perdidos_vs_keras"])


if __name__ == "__main__":
    unittest.main()
