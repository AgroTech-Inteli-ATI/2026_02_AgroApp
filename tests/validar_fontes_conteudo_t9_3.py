"""Valida o mapa de fontes de conteúdo técnico (T9.3): cobertura, páginas, direitos e ausência de texto copiado."""
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
LIMITE_TEXTO = 260  # nenhum campo de texto livre pode ser longo o bastante para conter trecho copiado
LIMITE_REFERENCIA = 600  # a referência completa tem formato próprio e limite próprio


def textos(valor, caminho=""):
    """Percorre o JSON devolvendo (caminho, texto) das strings que não são URLs nem hashes."""
    if isinstance(valor, dict):
        for k, v in valor.items():
            yield from textos(v, f"{caminho}.{k}")
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            yield from textos(v, f"{caminho}[{i}]")
    elif isinstance(valor, str) and caminho.split(".")[-1] != "referencia_abnt"             and not caminho.split(".")[-1].startswith(("url_", "sha256_")):
        yield caminho, valor


def validar(mapa, associacao):
    """Regras do mapa; levanta AssertionError na primeira violação."""
    fontes = {f["id"]: f for f in mapa["fontes"]}
    assert len(fontes) == len(mapa["fontes"]), "ids de fonte repetidos"
    for f in fontes.values():
        assert isinstance(f["ano"], int), f"{f['id']}: ano ausente"
        ref = f["referencia_abnt"]
        assert len(ref) <= LIMITE_REFERENCIA and f["titulo"] in ref and str(f["ano"]) in ref, f"{f['id']}: referência incompleta"
        assert re.search(r"Disponível em: https://\S+\. Acesso em: \d{1,2} \w{3,4}\. 20\d\d\.$", ref), f"{f['id']}: sem link e data de acesso"
        assert str(f["ano"]) in f["citacao_curta"], f"{f['id']}: citação curta sem ano"
        assert re.fullmatch(r"[0-9a-f]{64}", f["sha256_arquivo_consultado"]), f["id"]
        assert f["direitos"] == "direitos_reservados", f["id"]
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
            assert 1 <= ref["pagina_pdf"] <= f["paginas_total"], (c["indice"], ref["pagina_pdf"])
            assert ref["pagina_impressa"] == ref["pagina_pdf"] + f["deslocamento_pagina_impressa"], (c["indice"], ref)
            assert ref["secoes"] and set(ref["secoes"]) <= SECOES, (c["indice"], ref["secoes"])
            assert ref["nome_na_fonte"].strip()
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
        self.assertEqual([i for i, c in por_classe.items() if c["cobertura"] == "sem_fonte"], [7, 12])
        self.assertEqual(sum(bool(c["fontes"]) for c in por_classe.values()), 11)
        self.assertEqual(por_classe[1]["cobertura"], "sintomas_e_manejo")
        self.assertEqual({por_classe[i]["cobertura"] for i in (0, 2, 3, 4, 5, 6, 8, 9, 10, 11)}, {"descricao_e_danos"})
        self.assertEqual([r["pagina_pdf"] for r in por_classe[10]["fontes"]], [71, 73])

    def test_nenhuma_fonte_autoriza_o_uso_do_texto(self):
        for f in self.mapa["fontes"]:
            self.assertEqual(f["uso_do_texto"], "nao_autorizado")
            self.assertEqual(f["direitos"], "direitos_reservados")

    def test_mapa_nao_altera_a_associacao_nem_abre_conteudo(self):
        for c in self.assoc["classes"]:
            self.assertIsNone(c["chave_conteudo"])
            self.assertEqual(c["status_conteudo"], "aguardando_catalogo_agroapp")
        codigo = (RAIZ / "src/associacao_conteudo_t9_3.py").read_text(encoding="utf-8")
        self.assertNotIn("fontes_conteudo", codigo)

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

    def test_toda_fonte_tem_referencia_completa(self):
        self.assertEqual({f["id"]: f["ano"] for f in self.mapa["fontes"]}, {"EMB-DOC269": 2014, "CULT-312-CIGARRINHA": 2025})
        self.assertEqual({i["id"] for i in self.mapa["fontes_identificacao"]}, {"AGROINSECT", "INATURALIST", "DATASET-INSTRUCOES"})
        por_classe = {c["indice"]: c for c in self.mapa["classes"]}
        self.assertEqual(por_classe[4]["fontes"][0]["citacao"], "SOSA-GÓMEZ et al., 2014, p. 78")
        self.assertEqual(por_classe[1]["fontes"][0]["citacao"], "OLIVEIRA, 2025, p. 12-14")

    def test_recusa_citacao_inconsistente_com_a_pagina(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][4]["fontes"][0]["citacao"] = "SOSA-GÓMEZ et al., 2014, p. 79"
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_referencia_sem_link_e_data_de_acesso(self):
        m = copy.deepcopy(self.mapa)
        m["fontes"][0]["referencia_abnt"] = m["fontes"][0]["referencia_abnt"].split(" Disponível em:")[0]
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_referencia_sem_ano(self):
        m = copy.deepcopy(self.mapa)
        m["fontes"][1]["ano"] = None
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)

    def test_recusa_texto_copiado(self):
        m = copy.deepcopy(self.mapa)
        m["classes"][4]["fontes"][0]["observacao"] = "x" * (LIMITE_TEXTO + 1)
        with self.assertRaises(AssertionError):
            validar(m, self.assoc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
