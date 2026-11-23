"""Valida o mapa de fontes das fichas técnicas (T9.3 e T13): cobertura, citações, páginas, direitos e texto copiado."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import associacao_conteudo_t9_3 as t93

MAPA = RAIZ / t93.SAIDA / "fontes_conteudo.json"
SECOES = {"descricao_das_fases", "danos", "sintomas_nas_plantas", "periodo_de_controle", "manejo_quimico_e_biologico"}
COBERTURAS = {"descricao_e_danos", "sintomas_e_manejo", "sem_fonte"}
DIREITOS = {"direitos_reservados", "acesso_aberto_sem_licenca_declarada", "cc_by_nc_nd_4_0", "nao_declarado_no_documento",
            "reproducao_parcial_com_citacao"}
LIMITE_TEXTO = 260  # nenhum campo de texto livre pode ser longo o bastante para conter trecho copiado
LIMITE_REFERENCIA = 600  # a referência completa tem formato próprio e limite próprio


def textos(valor, caminho=""):
    """Percorre o JSON devolvendo (caminho, texto) das strings que não são URLs, hashes nem referências completas."""
    if isinstance(valor, dict):
        for k, v in valor.items():
            yield from textos(v, f"{caminho}.{k}")
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            yield from textos(v, f"{caminho}[{i}]")
    elif isinstance(valor, str) and caminho.split(".")[-1] != "referencia_abnt" \
            and not caminho.split(".")[-1].startswith(("url_", "sha256_")):
        yield caminho, valor


def validar(mapa, associacao):
    """Regras do mapa; levanta AssertionError na primeira violação."""
    fontes = {f["id"]: f for f in mapa["fontes"]}
    assert len(fontes) == len(mapa["fontes"]), "ids de fonte repetidos"
    internas = [i["id"] for i in mapa["fontes_internas"]]
    assert len(set(internas)) == len(internas) and not set(internas) & set(fontes), "fontes internas repetidas"
    for f in fontes.values():
        ref = f["referencia_abnt"]
        assert len(ref) <= LIMITE_REFERENCIA and f["titulo"] in ref, f"{f['id']}: referência incompleta"
        if f["ano"] is None:  # sem ano na própria fonte: a citação usa [s. d.]
            assert "[s. d.]" in ref and "s.d." in f["citacao_curta"], f"{f['id']}: ano ausente sem [s. d.]"
        else:
            assert isinstance(f["ano"], int) and str(f["ano"]) in ref, f"{f['id']}: ano ausente"
            assert str(f["ano"]) in f["citacao_curta"], f"{f['id']}: citação curta sem ano"
        assert re.search(r"Disponível em: https?://\S+\. Acesso em: \d{1,2} \w{3,4}\. 20\d\d\.$", ref), f"{f['id']}: sem link e data de acesso"
        assert re.fullmatch(r"[0-9a-f]{64}", f["sha256_arquivo_consultado"]), f["id"]
        assert f["direitos"] in DIREITOS, f["id"]
        if f["uso_do_texto"] != "nao_autorizado":
            aut = f.get("autorizacao") or {}
            assert all(aut.get(k) for k in ("responsavel", "data", "evidencia")), f"{f['id']}: uso sem autorização registrada"
    ids_ident = [i["id"] for i in mapa["fontes_identificacao"]]
    assert len(set(ids_ident)) == len(ids_ident) >= 3, "fontes de identificação ausentes ou repetidas"
    for i in mapa["fontes_identificacao"]:
        assert 0 < len(i["referencia_abnt"]) <= LIMITE_REFERENCIA and i["citacao_curta"] and i["licenca"] and i["uso"], i["id"]
    classes = mapa["classes"]
    assert [c["indice"] for c in classes] == list(range(len(associacao["classes"])))
    assert [c["nome"] for c in classes] == [c["nome"] for c in associacao["classes"]]
    sem_fonte = []
    for c in classes:
        assert c["cobertura"] in COBERTURAS, c["indice"]
        assert (c["cobertura"] == "sem_fonte") == (not c["fontes"]), f"classe {c['indice']}: cobertura incoerente"
        if not c["fontes"]:
            sem_fonte.append(c["indice"])
        for ref in c["fontes"]:
            f = fontes[ref["fonte"]]
            assert ref["secoes"] and set(ref["secoes"]) <= SECOES, (c["indice"], ref["secoes"])
            assert ref["nome_na_fonte"].strip()
            if "secao" in ref:  # página de revista na internet: o localizador é a seção
                assert f["paginas_total"] is None and not {"pagina_pdf", "pagina_impressa", "paginas_citadas"} & set(ref), c["indice"]
                assert ref["citacao"] == f"{f['citacao_curta']}, seção “{ref['secao']}”", (c["indice"], ref["citacao"])
                continue
            assert 1 <= ref["pagina_pdf"] <= f["paginas_total"], (c["indice"], ref["pagina_pdf"])
            assert ref["pagina_impressa"] == ref["pagina_pdf"] + f["deslocamento_pagina_impressa"], (c["indice"], ref)
            assert re.fullmatch(r"\d+(-\d+)?", ref["paginas_citadas"]), (c["indice"], ref["paginas_citadas"])
            assert int(ref["paginas_citadas"].split("-")[0]) == ref["pagina_impressa"], (c["indice"], ref)
            assert ref["citacao"] == f"{f['citacao_curta']}, p. {ref['paginas_citadas']}", (c["indice"], ref["citacao"])
        tem_manejo = any("manejo_quimico_e_biologico" in r["secoes"] for r in c["fontes"])
        assert (c["cobertura"] == "sintomas_e_manejo") == tem_manejo, f"classe {c['indice']}: cobertura x seções"
    assert sorted(sem_fonte) == sorted(l["indice"] for l in mapa["lacunas"]), "lacunas divergem das classes sem fonte"
    for caminho, texto in textos(mapa):
        assert len(texto) <= LIMITE_TEXTO, f"texto longo demais em {caminho} ({len(texto)} caracteres)"


class FontesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapa = json.loads(MAPA.read_text(encoding="utf-8"))
        cls.assoc, _ = t93.carregar(RAIZ)

    def test_mapa_publicado_e_valido(self):
        validar(self.mapa, self.assoc)

    def test_cobertura_publicada(self):
        por_classe = {c["indice"]: c for c in self.mapa["classes"]}
        self.assertEqual(self.mapa["lacunas"], [])
        self.assertEqual(sum(bool(c["fontes"]) for c in por_classe.values()), 13)
        self.assertEqual(por_classe[1]["cobertura"], "sintomas_e_manejo")
        self.assertEqual({por_classe[i]["cobertura"] for i in (0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)}, {"descricao_e_danos"})
        self.assertEqual([r["paginas_citadas"] for r in por_classe[10]["fontes"]], ["70-72", "1-3"])
        self.assertEqual([r["fonte"] for r in por_classe[7]["fontes"]], ["AN-SEB-1994", "CULT-199", "EPAGRI-BT170"])
        self.assertEqual([r["fonte"] for r in por_classe[12]["fontes"]], ["EMB-SANTOS-2002", "EMB-CT144", "EMB-CT59", "ABMS-MISOSUL-2024", "EPAGRI-BT170"])

    def test_nenhuma_fonte_autoriza_o_uso_do_texto(self):
        for f in self.mapa["fontes"]:
            self.assertEqual(f["uso_do_texto"], "nao_autorizado")
            self.assertIn(f["direitos"], DIREITOS)

    def test_toda_fonte_tem_referencia_completa(self):
        self.assertEqual({f["id"]: f["ano"] for f in self.mapa["fontes"]},
                         {"EMB-DOC269": 2014, "CULT-312-CIGARRINHA": 2025, "EMB-CT41": 2004, "AN-SEB-1994": 1994,
                          "CULT-199": None, "EMB-SANTOS-2002": 2002, "EMB-CT59": 2002, "EMB-CT208": 2015, "EMB-CT144": 2010,
                          "EMB-DOC129": 2011, "ABMS-MISOSUL-2024": 2024, "EMB-CT30": 2000, "EMB-CT131": 2013,
                          "EPAGRI-BT170": 2016, "EMB-CT47": 2019, "EMB-JA-DOC328": 2011})
        self.assertEqual({i["id"] for i in self.mapa["fontes_identificacao"]}, {"AGROINSECT", "INATURALIST", "DATASET-INSTRUCOES"})
        por_classe = {c["indice"]: c for c in self.mapa["classes"]}
        self.assertEqual(por_classe[4]["fontes"][0]["citacao"], "SOSA-GÓMEZ et al., 2014, p. 78")
        self.assertEqual([r["citacao"] for r in por_classe[1]["fontes"]], ["WAQUIL, 2004, p. 1-4", "OLIVEIRA, 2025, p. 12-14", "EICHOLZ et al., 2024, p. 91-92"])
        self.assertEqual(por_classe[7]["fontes"][1]["citacao"], "ÁVILA; PAPA, s.d., seção “Percevejo-do-milho”")
        self.assertEqual(por_classe[12]["fontes"][0]["citacao"], "SANTOS; BALSALOBRE, 2002, p. 1")

    def test_a_fonte_com_licenca_sem_derivacoes_so_serve_de_referencia(self):
        santos = next(f for f in self.mapa["fontes"] if f["id"] == "EMB-SANTOS-2002")
        self.assertEqual(santos["direitos"], "cc_by_nc_nd_4_0")
        self.assertIn("redação própria", santos["base_dos_direitos"])
        self.assertEqual(santos["uso_do_texto"], "nao_autorizado")

    def test_recusa_pagina_fora_do_documento(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][4]["fontes"][0]["pagina_pdf"] = 103
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_pagina_impressa_inconsistente(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][4]["fontes"][0]["pagina_impressa"] = 79
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_fonte_inexistente_e_secao_desconhecida(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][0]["fontes"][0]["fonte"] = "EMB-XXXX"
        with self.assertRaises(KeyError):
            validar(m, self.assoc)
        m = copy.deepcopy(self.mapa)
        m["classes"][0]["fontes"][0]["secoes"] = ["texto_completo"]
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_classe_sem_fonte_fora_das_lacunas(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][5].update({"cobertura": "sem_fonte", "fontes": []})
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_uso_do_texto_sem_autorizacao_registrada(self):
        m = copy.deepcopy(self.mapa)
        m["fontes"][0]["uso_do_texto"] = "autorizado"
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)
        m["fontes"][0]["autorizacao"] = {"responsavel": "Embrapa", "data": "2026-11-09", "evidencia": "e-mail de teste"}
        validar(m, self.assoc)

    def test_recusa_citacao_inconsistente_com_a_pagina_ou_a_secao(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][4]["fontes"][0]["citacao"] = "SOSA-GÓMEZ et al., 2014, p. 79"
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)
        m = copy.deepcopy(self.mapa)
        m["classes"][7]["fontes"][1]["citacao"] = "ÁVILA; PAPA, s.d., p. 1"
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_referencia_sem_link_e_data_de_acesso(self):
        m = copy.deepcopy(self.mapa)
        m["fontes"][0]["referencia_abnt"] = m["fontes"][0]["referencia_abnt"].split(" Disponível em:")[0]
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_referencia_sem_ano_e_ano_ausente_sem_sd(self):
        m = copy.deepcopy(self.mapa)
        m["fontes"][1]["ano"] = None  # a referência cita 2025: sem [s. d.] a combinação é inconsistente
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)
        m = copy.deepcopy(self.mapa)
        m["fontes"][1]["referencia_abnt"] = m["fontes"][1]["referencia_abnt"].replace("2025", "2024")
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_direitos_desconhecidos(self):
        m = copy.deepcopy(self.mapa)
        m["fontes"][2]["direitos"] = "dominio_publico"
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_texto_copiado(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][4]["fontes"][0]["observacao"] = "x" * (LIMITE_TEXTO + 1)
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
