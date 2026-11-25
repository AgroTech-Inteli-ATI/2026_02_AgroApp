"""Valida as fichas técnicas da equipe (T13.1): estrutura, citação de cada frase, ausência de manejo químico e
coerência das frases "pode ser confundido" com a análise de erros do modelo.

Os testes valem antes e depois da revisão técnica: não dependem de a ficha estar validada.
"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import associacao_conteudo_t9_3 as t93

NOMES = {0: "vaquinha", 1: "cigarrinha-do-milho", 2: "percevejo-barriga-verde", 3: "lagarta-do-cartucho",
         4: "percevejo-marrom", 5: "percevejo-verde", 6: "percevejo-asa-preta", 7: "percevejo-do-milho",
         8: "lagarta-falsa-medideira", 9: "lagarta-da-soja", 10: "lagarta-das-vagens", 11: "astylus",
         12: "cigarrinha-das-pastagens"}
# Manejo, produtos e doses não entram nas fichas: dependem de validação agronômica e de registro (T13.1).
PROIBIDOS = ("inseticida", "dose", "l/ha", "g/ha", "ml/ha", "kg/ha", "pulveriz", "tratamento de sementes", "carbofuran",
             "imidacloprid", "tiametoxam", "thiamethoxan", "bioinseticida", "controle químico", "produto registrado",
             "aplicar", "aplicação", "http")
LIMIAR_ERROS_MODELO = 3  # só entram na ficha os trocas com pelo menos 3 erros no teste exploratório


def erros_do_modelo():
    """erros[i][j]: quantas vezes o app indicou a classe i quando a foto era da classe j (teste de 473 imagens)."""
    dados = json.loads((RAIZ / t93.TRATAMENTO).read_text(encoding="utf-8"))
    erros: dict[int, dict[int, int]] = {}
    for decisao in dados["decisoes"]:
        for d in decisao["direcoes_candidato"]:
            alvo = erros.setdefault(d["indice_previsto"], {})
            alvo[d["indice_real"]] = alvo.get(d["indice_real"], 0) + d["erros"]
    return erros


class FichasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assoc, cls.base = t93.carregar(RAIZ)
        cls.fontes = t93.carregar_fontes(RAIZ)
        cls.por_id = {f["id"]: f for f in cls.fontes["fontes"]}
        cls.internas = {f["id"] for f in cls.fontes["fontes_internas"]}
        cls.por_chave = {i["chave"]: i for i in cls.base["itens"]}
        cls.mapa = {c["indice"]: c for c in cls.fontes["classes"]}

    def fichas(self):
        for c in self.assoc["classes"]:
            yield c, self.por_chave[c["chave_conteudo"]]

    def frases(self, item):
        for s in item["secoes"]:
            for linha in s["itens"]:
                yield s["id"], linha

    def test_uma_ficha_por_classe_com_a_identificacao_do_modelo(self):
        self.assertEqual(len(self.base["itens"]), 13)
        self.assertEqual([i["chave"] for i in self.base["itens"]], [c["chave_conteudo"] for c in self.assoc["classes"]])
        for c, item in self.fichas():
            self.assertEqual(item["titulo"], c["nome_comum"] or c["nome_cientifico"])
            self.assertEqual(item["nome_cientifico"], c["nome_cientifico"])
            self.assertEqual(c["origem_chave"], "equipe")
        t93.validar_contrato(self.assoc, self.base, self.fontes)

    def test_estrutura_curta_e_organizada_para_leitura_no_celular(self):
        for c, item in self.fichas():
            ids = [s["id"] for s in item["secoes"]]
            self.assertEqual(ids, [i for i in ("como_reconhecer", "danos", "confusao") if i in ids], c["indice"])
            self.assertTrue({"como_reconhecer", "danos"} <= set(ids), c["indice"])
            como = next(s for s in item["secoes"] if s["id"] == "como_reconhecer")
            self.assertGreaterEqual(len(como["itens"]), 2, c["indice"])
            for _, linha in self.frases(item):
                self.assertLessEqual(len(linha["texto"]), t93.LIMITE_TEXTO_ITEM)
            self.assertTrue(item["contexto"] and item["contexto"].startswith("Descrição baseada"), c["indice"])

    def test_toda_frase_tem_fonte_conhecida_com_pagina_ou_secao_dentro_do_que_o_mapa_declara(self):
        for c, item in self.fichas():
            entradas = [e for e in self.mapa[c["indice"]]["fontes"]]
            for _, linha in self.frases(item):
                ref = linha["fonte"]
                if ref["id"] in self.internas:
                    continue
                fonte = self.por_id[ref["id"]]
                candidatas = [e for e in entradas if e["fonte"] == ref["id"]]
                self.assertTrue(candidatas, f"classe {c['indice']}: fonte {ref['id']} fora do mapa da classe")
                if "secao" in ref:
                    self.assertIn(ref["secao"], [e.get("secao") for e in candidatas])
                    continue
                lo, hi = t93._paginas(ref)
                self.assertTrue(1 <= lo - fonte["deslocamento_pagina_impressa"] <= fonte["paginas_total"], (c["indice"], ref))
                self.assertTrue(1 <= hi - fonte["deslocamento_pagina_impressa"] <= fonte["paginas_total"], (c["indice"], ref))
                dentro = False
                for e in candidatas:
                    a, b = (int(x) for x in e["paginas_citadas"].split("-")[0:1] + e["paginas_citadas"].split("-")[-1:])
                    dentro = dentro or (a <= lo and hi <= b)
                self.assertTrue(dentro, f"classe {c['indice']}: páginas {lo}-{hi} fora do intervalo do mapa")

    def test_toda_ficha_cita_ao_menos_uma_fonte_externa(self):
        for c, item in self.fichas():
            externas = [x for _, x in self.frases(item) if x["fonte"]["id"] not in self.internas]
            self.assertTrue(externas, c["indice"])

    def test_fichas_nao_trazem_manejo_quimico_nem_links(self):
        for c, item in self.fichas():
            for _, linha in self.frases(item):
                texto = linha["texto"].lower()
                for termo in PROIBIDOS:
                    self.assertNotIn(termo, texto, f"classe {c['indice']}: '{termo}' em '{linha['texto']}'")

    def test_frases_de_confusao_do_modelo_batem_com_a_analise_de_erros(self):
        erros = erros_do_modelo()
        for c, item in self.fichas():
            i = c["indice"]
            esperado = {j for j, e in erros.get(i, {}).items() if e >= LIMIAR_ERROS_MODELO}
            citadas = set()
            for sid, linha in self.frases(item):
                if linha["fonte"]["id"] == "ANALISE-MODELO":
                    self.assertEqual(sid, "confusao")
                    citadas |= {j for j, nome in NOMES.items() if j != i and nome in linha["texto"].lower()}
            self.assertEqual(citadas, esperado, f"classe {i}: frase do modelo x erros do teste")

    def test_confusao_com_especie_de_literatura_cita_a_fonte(self):
        for c, item in self.fichas():
            for sid, linha in self.frases(item):
                if sid == "confusao" and linha["fonte"]["id"] != "ANALISE-MODELO":
                    self.assertIn(linha["fonte"]["id"], self.por_id, c["indice"])

    def test_fichas_de_classes_diferentes_nao_repetem_frases(self):
        vistas: dict[str, int] = {}
        for c, item in self.fichas():
            for _, linha in self.frases(item):
                if linha["fonte"]["id"] == "ANALISE-MODELO":
                    continue
                self.assertNotIn(linha["texto"], vistas, f"frase repetida nas classes {vistas.get(linha['texto'])} e {c['indice']}")
                vistas[linha["texto"]] = c["indice"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
