"""Valida a matriz de confusão e a análise de erros da T11.2 (sem modelo, imagens ou rede)."""
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import matriz_erros_t11_2 as t112

RAIZ = t112.RAIZ


def lido(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


class CalculoTest(unittest.TestCase):
    def test_matriz_e_metricas_por_classe_em_caso_pequeno(self):
        linhas = [{"real": r, "previsto": p} for r, p in [(0, 0), (0, 0), (0, 1), (1, 1), (1, 0), (2, 2)]]
        m = t112.matriz(linhas)
        self.assertEqual(m[0][:3], [2, 1, 0])
        self.assertEqual(m[1][:3], [1, 1, 0])
        classes = t112.por_classe(m, [f"c{i}" for i in range(13)])
        self.assertEqual((classes[0]["suporte"], classes[0]["vp"], classes[0]["fn"], classes[0]["fp"]), (3, 2, 1, 1))
        self.assertAlmostEqual(classes[0]["recall"], 2 / 3)
        self.assertAlmostEqual(classes[0]["precisao"], 2 / 3)
        self.assertAlmostEqual(classes[0]["f1"], 2 / 3)
        self.assertEqual(classes[5]["suporte"], 0)
        self.assertEqual(classes[5]["f1"], 0.0)

    def test_pearson(self):
        self.assertAlmostEqual(t112.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(t112.pearson([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertIsNone(t112.pearson([1, 1, 1], [1, 2, 3]))


class PublicadoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = t112.carregar()
        cls.res = t112.analisar(cls.dados)
        cls.t11_1 = json.loads(t112.METRICAS_T11_1.read_text(encoding="utf-8"))

    def test_matrizes_reproduzem_as_da_t11_1(self):
        for modelo in t112.MODELOS:
            for particao in t112.PARTICOES:
                esperado = self.t11_1["resultados"][particao]["modelos"][modelo]["integral"]["matriz_confusao"]
                self.assertEqual(self.res["matrizes"][f"{modelo}|{particao}"], esperado, (modelo, particao))

    def test_linhas_somam_o_suporte_e_a_acuracia_bate_com_a_t11_1(self):
        indice = self.dados["indice"]
        for particao in t112.PARTICOES:
            suporte = [0] * 13
            for ref in indice.values():
                if ref["particao"] == particao:
                    suporte[ref["classe"]] += 1
            for modelo in t112.MODELOS:
                m = self.res["matrizes"][f"{modelo}|{particao}"]
                self.assertEqual([sum(l) for l in m], suporte)
                r = t112.resumo_modelo(self.res, modelo, particao)
                ref = self.t11_1["resultados"][particao]["modelos"][modelo]["integral"]
                self.assertAlmostEqual(r["acuracia"], ref["acuracia"])
                self.assertEqual(r["imagens"], ref["total_amostras"])

    def test_pares_e_erros_por_imagem_fecham_com_a_matriz(self):
        for modelo in t112.MODELOS:
            for particao in t112.PARTICOES:
                m = self.res["matrizes"][f"{modelo}|{particao}"]
                pares = [p for p in self.res["pares"] if (p["modelo"], p["particao"]) == (modelo, particao)]
                erros = [e for e in self.res["erros"] if (e["modelo"], e["particao"]) == (modelo, particao)]
                self.assertEqual(sum(p["erros"] for p in pares), sum(sum(l) for l in m) - sum(m[i][i] for i in range(13)))
                self.assertEqual(len(erros), sum(p["erros"] for p in pares))
                self.assertEqual(len({e["image_id"] for e in erros}), len(erros))
                for p in pares:
                    self.assertEqual(p["erros"], m[p["real"]][p["previsto"]])
                    self.assertEqual(len(p["ids"]), p["erros"])
                    self.assertLessEqual(p["obs_inat_distintas"] + p["agroinsect"], p["erros"])
                    self.assertLessEqual(p["erros_com_score_aceito"], p["erros"])

    def test_origem_e_observacao_vem_do_nome_do_arquivo(self):
        for ref in self.dados["indice"].values():
            nome = ref["caminho"].rsplit("/", 1)[-1]
            self.assertEqual(ref["obs"] is not None, nome.startswith("inat"))
            if ref["obs"]:
                self.assertTrue(nome.startswith(f"inat{ref['obs']}_"))
        for e in self.res["erros"]:
            self.assertEqual(e["origem"] == "iNaturalist", bool(e["obs_inat"]))

    def test_pares_do_teste_batem_com_os_da_t6_3_no_candidato_keras(self):
        # Mesmo recorte (473 imagens) e predições equivalentes: os pares principais se repetem.
        pares = {(p["real"], p["previsto"]): p for p in self.res["pares"] if (p["modelo"], p["particao"]) == t112.REFERENCIA}
        self.assertEqual(pares[(8, 3)]["erros"], 6)
        self.assertEqual(pares[(8, 3)]["erros_t6_3_keras_fp32"], 6)
        for (real, previsto), p in pares.items():
            if p["erros"] >= t112.MIN_ERROS_PAR:
                self.assertLessEqual(abs(p["erros"] - p["erros_t6_3_keras_fp32"]), 1, (real, previsto))

    def test_observacoes_com_varios_erros_somam_pelo_menos_dois(self):
        obs = [o for o in self.res["observacoes"] if (o["modelo"], o["particao"]) == t112.REFERENCIA]
        self.assertTrue(obs)
        self.assertTrue(all(o["erros"] >= 2 for o in obs))
        mais_frequente = max(obs, key=lambda o: o["erros"])
        self.assertEqual((mais_frequente["obs_inat"], mais_frequente["erros"]), ("147542055", 6))

    def test_classes_de_menor_desempenho_seguem_o_criterio(self):
        classes = self.res["classes"]["Float16|teste"]
        baixos = {c["indice"] for c in classes if c["menor_desempenho"]}
        self.assertEqual(baixos, {4, 5, 6, 8})
        for c in classes:
            self.assertEqual(c["menor_desempenho"], c["f1"] < t112.F1_BAIXO or c["recall"] < t112.F1_BAIXO)

    def test_artefatos_e_relatorio_estao_atualizados(self):
        self.assertEqual(t112.divergentes(), [], "rode: python -m src.matriz_erros_t11_2")

    def test_projeto_md_traz_a_matriz_publicada_e_os_numeros_do_resumo(self):
        texto = (RAIZ / "docs/Projeto.md").read_text(encoding="utf-8")
        self.assertIn("## 11.2 Matriz de confusão e análise de erros (T11.2)", texto)
        self.assertIn(t112.tabela_matriz(self.res["matrizes"]["Float16|teste"]), texto)
        r = t112.resumo_modelo(self.res, *t112.REFERENCIA)
        self.assertIn(f"{r['imagens']} imagens, {r['acertos']} acertos e **{r['erros']} erros**", texto)
        pares = [p for p in self.res["pares"] if (p["modelo"], p["particao"]) == t112.REFERENCIA]
        self.assertIn(f"Os {r['erros']} erros formam {len(pares)} pares direcionais", texto)

    def test_figuras_seguem_o_padrao_da_t6_2_com_verde_e_vermelho(self):
        arquivos = {"Float16|teste": RAIZ / t112.FIGURA_REFERENCIA}
        for chave in ("Float16|validacao", "INT8|teste", "INT8|validacao"):
            modelo, particao = chave.split("|")
            arquivos[chave] = t112.SAIDA / f"matriz_{modelo.lower()}_{particao}.svg"
        for chave, caminho in arquivos.items():
            svg = caminho.read_text(encoding="utf-8")
            m = self.res["matrizes"][chave]
            self.assertEqual(svg.count('class="celula"'), 169, chave)
            # Bordas só nos pares fora da diagonal com pelo menos MIN_ERROS_PAR erros, mais a amostra da legenda.
            pares = sum(1 for i in range(13) for j in range(13) if i != j and m[i][j] >= t112.MIN_ERROS_PAR)
            self.assertEqual(svg.count('class="destaque"'), pares, chave)
            self.assertEqual(svg.count('class="legenda"'), 1)
            self.assertIn("Classe real", svg)
            self.assertIn("Classe prevista", svg)
            self.assertIn("Fração da classe real", svg)
            self.assertIn(f"Pares com ≥ {t112.MIN_ERROS_PAR} erros nesta amostra: contagem e % da classe real", svg)
            self.assertIn("— T11.2", svg)
            self.assertIn("(n=", svg)
        # Cores: verde na diagonal e vermelho fora dela, como na primeira versão da figura.
        r, g, b = t112.cor_acerto(0.9)
        self.assertTrue(g > r and g > b)
        r, g, b = t112.cor_erro(0.3)
        self.assertTrue(r > g and r > b)
        self.assertEqual(t112.cor_acerto(0.0), (235, 244, 236))

    def test_nao_usa_rede(self):
        codigo = (RAIZ / "src/matriz_erros_t11_2.py").read_text(encoding="utf-8")
        for proibido in ("import requests", "urllib", "socket", "http.client"):
            self.assertNotIn(proibido, codigo)


class EntradasTest(unittest.TestCase):
    def copia(self, tmp: Path) -> Path:
        for caminho in t112.ENTRADAS.values():
            destino = tmp / caminho.relative_to(RAIZ)
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(caminho, destino)
        return tmp

    def test_recusa_classe_prevista_que_nao_e_o_maior_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = self.copia(Path(tmp))
            caminho = raiz / t112.PREDICOES.relative_to(RAIZ)
            linhas = lido(caminho)
            linhas[0]["indice_previsto"] = str((int(linhas[0]["indice_previsto"]) + 1) % 13)
            with caminho.open("w", encoding="utf-8", newline="") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
                escritor.writeheader()
                escritor.writerows(linhas)
            with self.assertRaises(ValueError):
                t112.carregar(raiz)

    def test_recusa_predicao_com_classe_real_diferente_do_indice(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = self.copia(Path(tmp))
            caminho = raiz / t112.PREDICOES.relative_to(RAIZ)
            linhas = lido(caminho)
            linhas[0]["indice_real"] = str((int(linhas[0]["indice_real"]) + 1) % 13)
            with caminho.open("w", encoding="utf-8", newline="") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
                escritor.writeheader()
                escritor.writerows(linhas)
            with self.assertRaises(ValueError):
                t112.carregar(raiz)

    def test_gerar_em_pasta_temporaria_reproduz_os_arquivos_publicados(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = self.copia(Path(tmp))
            gerados = t112.gerar(raiz)
            self.assertEqual(len(gerados), 14)
            for caminho in gerados:
                self.assertEqual((raiz / caminho).read_text(encoding="utf-8"), (RAIZ / caminho).read_text(encoding="utf-8"), caminho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
