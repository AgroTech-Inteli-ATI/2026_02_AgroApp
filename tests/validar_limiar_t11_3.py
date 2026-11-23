"""Valida a avaliação do limiar de confiança (T11.3) sem modelo, imagens ou rede."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import limiar_t11_3 as t

RAIZ = t.RAIZ


def linha(real, previsto, score, modelo="Float16", particao="teste", id_="IMG_X"):
    return {"id": id_, "modelo": modelo, "particao": particao, "real": real, "previsto": previsto, "score": score,
            "top3": [previsto], "decisao_t11_1": ""}


class RegraTest(unittest.TestCase):
    def test_fronteira_do_limiar_igualdade_aceita(self):
        self.assertEqual(t.decisao(0.65, 0.65), "aceito")
        self.assertEqual(t.decisao(0.6499999, 0.65), "inconclusivo")
        self.assertEqual(t.decisao(1.0, 0.65), "aceito")
        self.assertEqual(t.decisao(0.0, 0.65), "inconclusivo")

    def test_limiar_vem_da_politica_versionada(self):
        self.assertEqual(t.limiar_da_politica(), 0.65)

    def test_quadrantes_em_caso_pequeno(self):
        linhas = [linha(0, 0, 0.9), linha(0, 0, 0.5), linha(0, 1, 0.8), linha(1, 0, 0.4), linha(1, 1, 0.65)]
        q = t.quadrantes(linhas, 0.65)
        self.assertEqual((q["acerto_aceito"], q["acerto_inconclusivo"], q["erro_aceito"], q["erro_inconclusivo"]), (2, 1, 1, 1))
        self.assertEqual(q["aceitos"], 3)
        self.assertAlmostEqual(q["acuracia_aceitos"], 2 / 3)
        self.assertAlmostEqual(q["acuracia_sem_limiar"], 3 / 5)
        self.assertAlmostEqual(q["inconclusivos_que_eram_erro"], 1 / 2)

    def test_calibracao_perfeita_tem_ece_baixo_e_a_superconfiante_tem_ece_alto(self):
        # Score 0,95 com 95% de acerto e score 0,55 com 55%: calibrado.
        calibrado = [linha(0, 0, 0.95) for _ in range(19)] + [linha(0, 1, 0.95)] + \
                    [linha(0, 0, 0.55) for _ in range(11)] + [linha(0, 1, 0.55) for _ in range(9)]
        self.assertLess(t.calibracao(calibrado)["ece"], 0.01)
        # Score 0,95 com 50% de acerto: superconfiante.
        super_ = [linha(0, 0, 0.95) for _ in range(10)] + [linha(0, 1, 0.95) for _ in range(10)]
        c = t.calibracao(super_)
        self.assertAlmostEqual(c["ece"], 0.45, places=2)
        self.assertEqual(c["faixas_com_score_acima_do_acerto"], 1)

    def test_erros_altos_e_classe_real_entre_as_tres_hipoteses(self):
        a = dict(linha(0, 1, 0.97, id_="A"), top3=[1, 0, 2])
        b = dict(linha(0, 1, 0.70, id_="B"), top3=[1, 2, 3])
        c = dict(linha(0, 1, 0.50, id_="C"), top3=[1, 0, 2])
        r = t.erros_altos([a, b, c, linha(0, 0, 0.99)], 0.65)
        self.assertEqual((r["erros"], r["aceitos"], r["altos"], r["real_no_top3_entre_aceitos"]), (3, 2, 1, 1))
        self.assertEqual([e["id"] for e in r["lista"]], ["A"])

    def test_regiao_sem_inseto_evita_as_caixas(self):
        caixas = [(0.4, 0.4, 0.6, 0.6)]
        x0, y0, x1, y1 = t.regiao_sem_inseto(caixas)
        for cx0, cy0, cx1, cy1 in caixas:
            separados = x1 <= cx0 or x0 >= cx1 or y1 <= cy0 or y0 >= cy1
            self.assertTrue(separados)
        self.assertIsNone(t.regiao_sem_inseto([(0.0, 0.0, 1.0, 1.0)]))


class HistoricoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = t.carregar_historico()
        cls.res = t.analisar_historico(cls.h, t.limiar_da_politica())
        cls.t11_1 = json.loads((RAIZ / "assets/data/avaliacao_final_T11_1/metricas.json").read_text(encoding="utf-8"))

    def test_politica_bate_com_a_da_t11_1_nos_quatro_conjuntos(self):
        for modelo in t.MODELOS:
            for particao in t.PARTICOES:
                esperado = self.t11_1["resultados"][particao]["modelos"][modelo]["integral"]["politica_confianca"]
                q = self.res[f"{modelo}|{particao}"]["quadrantes"]
                self.assertEqual(q["aceitos"], esperado["aceitos"], (modelo, particao))
                self.assertEqual(q["erro_aceito"], esperado["erros_aceitos"], (modelo, particao))
                self.assertEqual(q["acerto_inconclusivo"], esperado["acertos_inconclusivos"], (modelo, particao))
                self.assertAlmostEqual(q["acuracia_aceitos"], esperado["acuracia_aceitos"])

    def test_quadrantes_somam_o_total_e_curva_em_065_igual_aos_quadrantes(self):
        for chave, r in ((k, v) for k, v in self.res.items() if "|" in k):
            q = r["quadrantes"]
            self.assertEqual(q["acerto_aceito"] + q["acerto_inconclusivo"] + q["erro_aceito"] + q["erro_inconclusivo"], q["total"], chave)
            ponto = next(c for c in r["curva"] if abs(c["limiar"] - 0.65) < 1e-9)
            self.assertEqual((ponto["aceitos"], ponto["erros_aceitos"]), (q["aceitos"], q["erro_aceito"]))
            cobertura = [c["cobertura"] for c in r["curva"]]
            self.assertEqual(cobertura, sorted(cobertura, reverse=True), "a cobertura não pode crescer com o limiar")

    def test_faixas_e_calibracao_cobrem_todas_as_imagens(self):
        for chave, r in ((k, v) for k, v in self.res.items() if "|" in k):
            total = r["quadrantes"]["total"]
            self.assertEqual(sum(f["imagens"] for f in r["faixas"]), total, chave)
            self.assertEqual(sum(f["imagens"] for f in r["calibracao"]["faixas"]), total, chave)
            self.assertEqual(sum(f["acertos"] + f["erros"] for f in r["faixas"]), total, chave)

    def test_score_nao_e_probabilidade_calibrada_no_float16_do_teste(self):
        c = self.res["Float16|teste"]["calibracao"]
        self.assertGreater(c["ece"], 0.05)
        faixas_medias = [f for f in c["faixas"] if 0.7 <= f["de"] < 0.9]
        self.assertTrue(faixas_medias)
        for f in faixas_medias:
            self.assertLess(f["acerto"], f["score_medio"] - 0.1, f)

    def test_erros_aceitos_do_float16_no_teste(self):
        r = self.res["Float16|teste"]["erros_altos"]
        self.assertEqual((r["erros"], r["aceitos"]), (72, 52))
        self.assertTrue(all(e["score"] >= t.ALTO for e in r["lista"]))
        self.assertEqual(len(r["lista"]), r["altos"])

    def test_por_classe_fecha_com_os_quadrantes(self):
        r = self.res["Float16|teste"]
        self.assertEqual(sum(c["suporte"] for c in r["por_classe"]), r["quadrantes"]["total"])
        self.assertEqual(sum(c["aceitos"] for c in r["por_classe"]), r["quadrantes"]["aceitos"])
        self.assertEqual(sum(c["mostrada_como_principal"] for c in r["por_classe"]), r["quadrantes"]["aceitos"])
        self.assertEqual(sum(c["acertos_aceitos"] for c in r["por_classe"]), r["quadrantes"]["acerto_aceito"])


class WebTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifesto, cls.inferencias = t.carregar_web()
        cls.res = t.analisar()

    def test_inferencias_correspondem_ao_manifesto_e_cobrem_todas_as_imagens(self):
        ids = [i["id"] for i in self.manifesto["imagens"]]
        self.assertEqual(len(ids), len(set(ids)))
        for formato in t.MODELOS:
            resultados = self.inferencias["formatos"][formato]
            self.assertEqual([r["id"] for r in resultados], ids, formato)
            for r in resultados:
                self.assertEqual(len(r["scores"]), 13)
                self.assertTrue(all(0 <= s <= 1 for s in r["scores"]), r["id"])
                # O INT8 devolve scores em passos de 1/256; a soma pode se afastar de 1 por até 13 passos de arredondamento.
                self.assertLess(abs(sum(r["scores"]) - 1.0), 0.02 if formato == "INT8" else 1e-5, r["id"])

    def test_modelo_e_formato_medidos_sao_os_do_build(self):
        manifesto_build = json.loads((RAIZ / "frontend/public/models/manifest.json").read_text(encoding="utf-8"))
        formatos = [m["format"] for m in manifesto_build["models"]]
        self.assertEqual(formatos, ["Float16", "INT8"])
        for formato in t.MODELOS:
            info = self.inferencias["modelo"][formato]
            self.assertEqual(info["format"], formato)
            esperado = next(m for m in manifesto_build["models"] if m["format"] == formato)
            self.assertEqual(info["sha256"], esperado["sha256"], formato)
            self.assertEqual(info["runtime"]["name"], "@litertjs/core")
        self.assertEqual(self.inferencias["limiar_politica"], t.limiar_da_politica())

    def test_interface_mostra_as_hipoteses_exatamente_quando_o_score_atinge_o_limiar(self):
        for formato, c in self.res["web"]["consistencia_ui"].items():
            self.assertEqual(c["divergentes"], [], formato)
            self.assertEqual(c["imagens"], len(self.manifesto["imagens"]))
        for formato, d in self.res["web"]["formatos"].items():
            self.assertTrue(all(l["ui"] in ("aceito", "inconclusivo") for l in d["linhas"]), formato)

    def test_decisao_do_app_usa_o_limiar_065_sobre_o_top1(self):
        for d in self.res["web"]["formatos"].values():
            for l in d["linhas"]:
                self.assertEqual(l["decisao"], "aceito" if l["score"] >= 0.65 else "inconclusivo")
                self.assertEqual(l["previsto"], l["top3"][0])

    def test_pares_de_degradacao_apontam_para_um_original_da_mesma_foto(self):
        por_id = {i["id"]: i for i in self.manifesto["imagens"]}
        for i in self.manifesto["imagens"]:
            if i["cenario"] in t.DEGRADACOES:
                pai = por_id[i["pai"]]
                self.assertEqual(pai["cenario"], "original")
                self.assertEqual(pai["origem_imagem"], i["origem_imagem"])
                self.assertEqual(pai["classe_real"], i["classe_real"])

    def test_cenarios_obrigatorios_foram_medidos(self):
        cenarios = {i["cenario"] for i in self.manifesto["imagens"]}
        for c in ("sintetico", "fundo", "original") + t.DEGRADACOES:
            self.assertIn(c, cenarios)
        for formato, d in self.res["web"]["formatos"].items():
            self.assertTrue(set(d["pares_degradacao"]) >= set(t.DEGRADACOES), formato)

    def test_nenhum_arquivo_de_imagem_e_versionado_no_manifesto_e_os_hashes_sao_sha256(self):
        for i in self.manifesto["imagens"]:
            self.assertRegex(i["sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(list(t.SAIDA.glob("*.jpg")) or list(t.SAIDA.glob("*.png")))


class PublicadoTest(unittest.TestCase):
    def test_artefatos_e_relatorio_estao_atualizados(self):
        self.assertEqual(t.divergentes(), [], "rode: python -m src.limiar_t11_3 analisar")

    def test_relatorio_nao_apresenta_score_como_probabilidade_de_acerto(self):
        texto = t.DOC.read_text(encoding="utf-8")
        self.assertIn("não apresenta nenhum score como probabilidade de acerto", texto)
        for linha_ in texto.splitlines():
            if "probabilidade" in linha_.lower():
                self.assertTrue(any(p in linha_.lower() for p in ("não", "nunca", "se o score fosse", "calibrad", "≠")), linha_)

    def test_projeto_md_traz_a_secao_11_3_e_os_numeros_principais(self):
        texto = (RAIZ / "docs/Projeto.md").read_text(encoding="utf-8")
        self.assertIn("## 11.3 Avaliação do limiar de confiança e casos inadequados (T11.3)", texto)
        q = t.analisar_historico(t.carregar_historico(), 0.65)["Float16|teste"]["quadrantes"]
        self.assertIn(f"**{q['erro_aceito']} erros são aceitos**", texto)
        self.assertIn(f"{q['acerto_aceito']} | {q['acerto_inconclusivo']} | {q['erro_aceito']} | {q['erro_inconclusivo']}", texto)

    def test_nao_usa_rede(self):
        codigo = (RAIZ / "src/limiar_t11_3.py").read_text(encoding="utf-8")
        for proibido in ("import requests", "urllib", "socket", "http.client"):
            self.assertNotIn(proibido, codigo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
