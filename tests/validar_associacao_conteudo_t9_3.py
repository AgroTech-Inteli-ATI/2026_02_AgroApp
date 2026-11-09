"""Valida a associação classe -> conteúdo técnico (T9.3), com catálogo sintético para o caminho completo."""
import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import associacao_conteudo_t9_3 as t93

PASTA = RAIZ / t93.SAIDA


def item(chave, titulo="Título", validated=True):
    return {"chave": chave, "titulo": titulo, "texto": f"texto de {chave}", "fonte": "fonte de teste",
            "revisado_em": "2026-11-07", "validated": validated}


def validar_classe(assoc, base, indice, chave):
    c = assoc["classes"][indice]
    c.update({"chave_conteudo": chave, "status_conteudo": "validado",
              "validacao_conteudo": {"responsavel": "Parceiro", "data": "2026-11-07", "evidencia": "ata de teste"}})
    base["itens"].append(item(chave, titulo=c["nome"]))


class AssociacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assoc, cls.base = t93.carregar(RAIZ)
        cls.modelo = json.loads((RAIZ / t93.CLASSES).read_text(encoding="utf-8"))

    def novo(self):
        return copy.deepcopy(self.assoc), copy.deepcopy(self.base)

    def test_publicado_reproduz_as_fontes(self):
        self.assertEqual(t93.montar(RAIZ, self.assoc), self.assoc, "rode: python -m src.associacao_conteudo_t9_3 gerar")
        for fonte in self.assoc["fontes"].values():
            self.assertEqual(t93.hash_arquivo(RAIZ / fonte["arquivo"]), fonte["sha256"], fonte["arquivo"])

    def test_cobre_as_13_classes_na_ordem_do_modelo(self):
        classes = self.assoc["classes"]
        self.assertEqual([c["indice"] for c in classes], list(range(13)))
        self.assertEqual([c["nome"] for c in classes], [m["nome"] for m in self.modelo])
        self.assertEqual(self.assoc["total_classes"], 13)
        t93.validar_contrato(self.assoc, self.base)

    def test_chaves_propostas_unicas_e_nunca_urls(self):
        chaves = [c["chave_conteudo_proposta"] for c in self.assoc["classes"]]
        self.assertEqual(len(set(chaves)), 13)
        self.assertTrue(all(re.fullmatch(r"praga\.[a-z_]+", k) for k in chaves))

    def test_ids_do_inventario_e_do_acervo(self):
        por_indice = {c["indice"]: c for c in self.assoc["classes"]}
        self.assertEqual(por_indice[10]["ids_inventario"], [10, 11])
        self.assertEqual({i: [a["id"] for a in c["ids_acervo"]] for i, c in por_indice.items() if c["ids_acervo"]},
                         {1: ["AGRO-001"], 7: ["AGRO-003"], 9: ["AGRO-053"]})
        dicionario = {c["id"]: c for c in json.loads((RAIZ / t93.DICIONARIO).read_text(encoding="utf-8"))["classes"]}
        for c in self.assoc["classes"]:
            for a in c["ids_acervo"]:
                self.assertEqual(a["chave_proposta_dicionario"], dicionario[a["id"]]["chave_conteudo_proposta"])

    def test_relacoes_t6_4_simetricas_e_sem_conteudo_compartilhado(self):
        classes = {c["indice"]: c for c in self.assoc["classes"]}
        pares = {frozenset((c["indice"], r["indice"])) for c in classes.values() for r in c["relacionadas_t6_4"]}
        self.assertEqual(len(pares), 27)
        for c in classes.values():
            for r in c["relacionadas_t6_4"]:
                self.assertIn(c["indice"], [x["indice"] for x in classes[r["indice"]]["relacionadas_t6_4"]])
        self.assertEqual([r["indice"] for r in classes[3]["relacionadas_t6_4"]], [2, 7, 8, 9, 10])

    def test_sem_catalogo_toda_classe_e_indisponivel_sem_usar_a_chave_proposta(self):
        for c in self.assoc["classes"]:
            r = t93.resolver(c["indice"], self.assoc, self.base)
            self.assertFalse(r["disponivel"])
            self.assertIsNone(r["conteudo"])
            self.assertEqual(r["motivo"], "sem_chave_oficial")
            self.assertEqual(r["nome"], c["nome"])
        self.assertEqual(t93.cobertura(self.assoc, self.base),
                         {"classes": 13, "com_registro": 13, "com_conteudo_disponivel": 0,
                          "indisponiveis_por_motivo": {"sem_chave_oficial": 13}})

    def test_nome_exibido_e_o_do_modelo(self):
        r = t93.resolver(11, self.assoc, self.base)
        self.assertEqual(r["nome"], "Astylus variegatus")
        self.assertIsNone(r["nome_comum"])
        self.assertNotIn("angorá", json.dumps(self.assoc, ensure_ascii=False))

    def test_catalogo_completo_resolve_cada_classe_ao_seu_conteudo(self):
        assoc, base = self.novo()
        for i in range(13):
            validar_classe(assoc, base, i, f"catalogo.{i:02d}")
        t93.validar_contrato(assoc, base)
        for i in range(13):
            r = t93.resolver(i, assoc, base)
            self.assertTrue(r["disponivel"])
            self.assertEqual(r["conteudo"]["texto"], f"texto de catalogo.{i:02d}")
            self.assertEqual(r["conteudo"]["titulo"], assoc["classes"][i]["nome"])
        self.assertEqual(t93.cobertura(assoc, base)["com_conteudo_disponivel"], 13)

    def test_estados_intermediarios_nao_afirmam_conteudo(self):
        assoc, base = self.novo()
        validar_classe(assoc, base, 3, "catalogo.03")
        base["itens"][0]["validated"] = False
        self.assertEqual(t93.resolver(3, assoc, base)["motivo"], "item_nao_validado")
        base["itens"].clear()
        self.assertEqual(t93.resolver(3, assoc, base)["motivo"], "item_ausente_na_base")
        assoc["classes"][3]["status_conteudo"] = "aguardando_validacao"
        self.assertEqual(t93.resolver(3, assoc, base)["motivo"], "aguardando_validacao")
        self.assertFalse(t93.resolver(3, assoc, base)["disponivel"])

    def test_contrato_recusa_validacao_incompleta_e_conteudo_compartilhado(self):
        assoc, base = self.novo()
        validar_classe(assoc, base, 3, "catalogo.03")
        assoc["classes"][3]["validacao_conteudo"]["evidencia"] = ""
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)
        assoc, base = self.novo()
        validar_classe(assoc, base, 3, "catalogo.compartilhado")
        validar_classe(assoc, base, 10, "catalogo.compartilhado")
        base["itens"].pop()  # evita item repetido: o problema testado é o conteúdo único do par 3 e 10
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)
        assoc, base = self.novo()
        validar_classe(assoc, base, 3, "https://exemplo.com/conteudo")
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)

    def test_conteudo_de_classes_do_mesmo_par_permanece_separado(self):
        assoc, base = self.novo()
        validar_classe(assoc, base, 3, "catalogo.03")
        validar_classe(assoc, base, 10, "catalogo.10")
        a, b = t93.resolver(3, assoc, base), t93.resolver(10, assoc, base)
        self.assertNotEqual(a["conteudo"]["texto"], b["conteudo"]["texto"])
        self.assertIn(10, a["relacionadas"])
        self.assertIn(3, b["relacionadas"])

    def test_associar_predicoes_mantem_ordem_e_scores_e_recusa_indices_invalidos(self):
        predicoes = [{"indice": 10, "score": 0.61}, {"indice": 3, "score": 0.27}, {"indice": 0, "score": 0.05}]
        saida = t93.associar_predicoes(predicoes, self.assoc, self.base)
        self.assertEqual([s["indice"] for s in saida], [10, 3, 0])
        self.assertEqual([s["score"] for s in saida], [0.61, 0.27, 0.05])
        for invalido in (13, -1, "3", 3.0, True, None):
            with self.subTest(indice=invalido), self.assertRaises(ValueError):
                t93.resolver(invalido, self.assoc, self.base)

    def test_gerar_preserva_o_que_foi_preenchido_a_mao_e_nao_sobrescreve_a_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp)
            t93.gerar(RAIZ, saida)
            assoc, base = json.loads((saida / t93.ASSOCIACAO).read_text(encoding="utf-8")), None
            validar_classe(assoc, self.novo()[1], 7, "catalogo.07")
            t93.gravar_json(saida / t93.ASSOCIACAO, assoc)
            curada = {**t93.base_vazia(), "itens": [item("catalogo.07")]}
            t93.gravar_json(saida / t93.BASE, curada)
            novo = t93.gerar(RAIZ, saida)
            self.assertEqual(novo["classes"][7]["chave_conteudo"], "catalogo.07")
            self.assertEqual(novo["classes"][7]["status_conteudo"], "validado")
            self.assertEqual(json.loads((saida / t93.BASE).read_text(encoding="utf-8")), curada)

    def test_nenhum_acesso_a_rede(self):
        codigo = (RAIZ / "src/associacao_conteudo_t9_3.py").read_text(encoding="utf-8")
        for proibido in ("urllib", "requests", "socket", "http.client", "urlopen", "webbrowser"):
            self.assertNotIn(proibido, codigo)
        dados = (PASTA / t93.ASSOCIACAO).read_text(encoding="utf-8") + (PASTA / t93.BASE).read_text(encoding="utf-8")
        self.assertNotIn("http", dados, "dados locais não devem apontar para a rede")


if __name__ == "__main__":
    unittest.main(verbosity=2)
