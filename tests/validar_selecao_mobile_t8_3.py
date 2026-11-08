"""Valida a decisão da T8.3 contra as evidências e o contrato dos critérios."""
import copy
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import selecao_mobile_t8_3 as t83

PASTA = RAIZ / t83.SAIDA


def sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


class SelecaoMobileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.salvo = json.loads((PASTA / "decisao.json").read_text(encoding="utf-8"))
        cls.fontes = t83.carregar(RAIZ)
        cls.arquivos = t83.conferir_arquivos(RAIZ, cls.fontes)

    def test_decisao_publicada_reproduz_as_evidencias(self):
        atual = t83.decidir(RAIZ)
        for chave in atual:
            if chave != "t8_1":
                self.assertEqual(self.salvo[chave], atual[chave], f"{chave} desatualizado; rode o script")

    def test_registro_da_t8_1_esta_atualizado(self):
        atual = t83.conferir_t8_1(RAIZ, self.fontes)
        self.assertNotEqual(atual["status"], "divergente", atual.get("divergencias"))
        self.assertEqual(self.salvo["t8_1"]["status"], atual["status"],
                         "a T8.1 entrou ou saiu da árvore; execute python -m src.selecao_mobile_t8_3")

    def test_escolhido_e_contingencia_sao_arquivos_verificados(self):
        for papel in ("escolhido", "contingencia"):
            with self.subTest(papel=papel):
                r = self.salvo[papel]
                caminho = RAIZ / r["arquivo"]
                self.assertTrue(caminho.is_file())
                self.assertEqual(sha(caminho), r["sha256"])
                self.assertEqual(caminho.stat().st_size, r["bytes"])
                self.assertLessEqual(r["bytes"], t83.LIMITE_BYTES)
        self.assertNotEqual(self.salvo["escolhido"]["sha256"], self.salvo["contingencia"]["sha256"])
        for r in self.salvo["tabela"]:
            self.assertEqual(r["sha256"], self.arquivos[r["versao"]]["sha256"])

    def test_escolhido_atende_criterios_e_lidera_a_ordem(self):
        linhas = {r["versao"]: r for r in self.salvo["tabela"]}
        e = linhas[self.salvo["escolhido"]["versao"]]
        self.assertTrue(e["elegivel"])
        self.assertTrue(all(e["criterios_eliminatorios"].values()))
        self.assertEqual(self.salvo["ordem_de_elegiveis"][0], e["versao"])
        self.assertTrue(e["rnf06_demonstrado_pelo_ic95"])
        self.assertGreaterEqual(e["ic95_inferior_acuracia_macro_pp_validacao"], t83.LIMITE_PERDA_PP)
        self.assertLess(e["p95_ms_local_t8_2"], t83.LIMITE_P95_MS)
        self.assertEqual(self.salvo["eliminados"], {"fp32": ["rnf01_ate_8mb"]})

    def test_politica_t6_5_do_escolhido_mantem_a_meta(self):
        e = next(r for r in self.salvo["tabela"] if r["versao"] == self.salvo["escolhido"]["versao"])
        meta = self.fontes["politica"]["base"]["meta_acerto"]
        self.assertGreaterEqual(e["politica_t6_5_top1_validacao"]["acerto_nas_aceitas"], meta)
        self.assertEqual(e["politica_t6_5_top1_validacao"]["imagens"], 474)

    def test_pacote_t5_6_nao_e_confundido_com_o_int8_oficial(self):
        pacote = self.salvo["pacote_t5_6"]
        self.assertEqual(pacote["sha256"], sha(RAIZ / pacote["arquivo"]))
        self.assertEqual(pacote["e_o_int8_da_t7_3"], pacote["sha256"] == self.arquivos["int8_t7_3"]["sha256"])

    def test_teste_exploratorio_nao_altera_a_decisao(self):
        base = [r["versao"] for r in sorted((t83.avaliar_versao(v, self.fontes, self.arquivos) for v in t83.VERSOES),
                                            key=t83.chave_ordem)]
        alterado = copy.deepcopy(self.fontes)
        for r in alterado["por_classe"]:
            if r["particao"] == "teste":
                r["f1"] = "0"
        for t in alterado["tabela"].values():
            t["f1_macro_teste"] = "0"
        novo = [r["versao"] for r in sorted((t83.avaliar_versao(v, alterado, self.arquivos) for v in t83.VERSOES),
                                            key=t83.chave_ordem)]
        self.assertEqual(base, novo)

    def test_ordem_segue_a_sequencia_da_task(self):
        def r(rnf06, queda, p95, tamanho):
            return {"rnf06_demonstrado_pelo_ic95": rnf06, "pior_classe_validacao": {"delta_f1": queda},
                    "p95_ms_local_t8_2": p95, "bytes": tamanho}
        acuracia = r(True, -0.2, 99.0, 9)
        classe = r(False, 0.0, 99.0, 9)
        latencia = r(False, -0.1, 1.0, 9)
        tamanho = r(False, -0.1, 5.0, 1)
        ordenados = sorted([tamanho, latencia, classe, acuracia], key=t83.chave_ordem)
        self.assertEqual(ordenados, [acuracia, classe, latencia, tamanho])

    def test_arquivos_derivados_acompanham_a_decisao(self):
        with (PASTA / "tabela_decisao.csv").open(encoding="utf-8", newline="") as f:
            linhas = list(csv.DictReader(f, delimiter=";"))
        self.assertEqual([r["versao"] for r in linhas], list(t83.VERSOES))
        self.assertEqual(sum(r["elegivel"] == "True" for r in linhas), len(t83.VERSOES) - 1)
        texto = (PASTA / "relatorio.md").read_text(encoding="utf-8")
        self.assertIn(self.salvo["escolhido"]["sha256"], texto)
        self.assertIn(self.salvo["contingencia"]["arquivo"], texto)

    def test_conferencia_com_a_t8_1_detecta_divergencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            self.assertEqual(t83.conferir_t8_1(raiz, self.fontes)["status"], "nao_integrada")
            pasta = raiz / t83.T8_1
            pasta.mkdir(parents=True)
            with (pasta / "metricas_gerais.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, ["versao", "f1_macro", "balanced_accuracy", "acuracia"])
                w.writeheader()
                for v in t83.VERSOES:
                    t = self.fontes["tabela"][v]
                    w.writerow({"versao": v, "f1_macro": t["f1_macro_teste"],
                                "balanced_accuracy": t["balanced_accuracy_teste"], "acuracia": t["acuracia_teste"]})
            with (pasta / "comparacao_por_classe.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, ["versao", "indice", "f1"])
                w.writeheader()
                for r in self.fontes["por_classe"]:
                    if r["particao"] == "teste" and r["estrategia"] in t83.VERSOES:
                        w.writerow({"versao": r["estrategia"], "indice": r["indice"], "f1": r["f1"]})
            self.assertEqual(t83.conferir_t8_1(raiz, self.fontes)["status"], "conferida")
            texto = (pasta / "metricas_gerais.csv").read_text(encoding="utf-8")
            (pasta / "metricas_gerais.csv").write_text(
                texto.replace(self.fontes["tabela"]["float16"]["f1_macro_teste"], "0.5", 1), encoding="utf-8")
            resultado = t83.conferir_t8_1(raiz, self.fontes)
            self.assertEqual(resultado["status"], "divergente")
            # float16 e FP32 têm o mesmo F1 no teste; a troca pode atingir qualquer uma das duas linhas.
            self.assertTrue(any(d.startswith(("fp32", "float16")) for d in resultado["divergencias"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
