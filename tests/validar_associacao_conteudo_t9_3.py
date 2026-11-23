"""Valida a associação classe -> ficha técnica (T9.3 e T13), com fichas sintéticas para o caminho completo.

Os testes valem antes e depois da revisão técnica das fichas: o que muda com a aprovação é só o estado
publicado, e os testes que dependem dele partem de um estado sem chaves ("vazio") ou comparam com os dados.
"""
import copy
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import associacao_conteudo_t9_3 as t93

PASTA = RAIZ / t93.SAIDA


def ficha(chave, titulo="Título", validated=True):
    linha = {"texto": "frase de teste", "fonte": {"id": "EMB-DOC269", "pagina": 78}}
    return {"chave": chave, "titulo": titulo, "nome_cientifico": "Gênero espécie", "contexto": None,
            "secoes": [{"id": "como_reconhecer", "titulo": "Como reconhecer", "itens": [linha]},
                       {"id": "danos", "titulo": "Danos ou sintomas", "itens": [linha]}],
            "elaborado_por": "Equipe de teste", "elaborado_em": "2026-11-20",
            "revisado_em": "2026-11-21" if validated else None, "validated": validated}


def validar_classe(assoc, base, indice, chave, origem="equipe"):
    c = assoc["classes"][indice]
    c.update({"chave_conteudo": chave, "origem_chave": origem, "status_conteudo": "validado",
              "validacao_conteudo": {"data": "2026-11-21", "evidencia": "ata de teste"}})
    base["itens"].append(ficha(chave, titulo=c["nome"]))


class AssociacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assoc, cls.base = t93.carregar(RAIZ)
        cls.fontes = t93.carregar_fontes(RAIZ)
        cls.modelo = json.loads((RAIZ / t93.CLASSES).read_text(encoding="utf-8"))

    def vazio(self):
        """Estado sem chaves nem fichas, para testar o contrato sem depender do que foi aprovado."""
        assoc, base = copy.deepcopy(self.assoc), copy.deepcopy(self.base)
        for c in assoc["classes"]:
            c.update({"chave_conteudo": None, "origem_chave": None, "status_conteudo": "aguardando_catalogo_agroapp",
                      "validacao_conteudo": None})
        base["itens"] = []
        return assoc, base

    def test_publicado_reproduz_as_fontes(self):
        self.assertEqual(t93.montar(RAIZ, self.assoc), self.assoc, "rode: python -m src.associacao_conteudo_t9_3 gerar")
        for fonte in self.assoc["fontes"].values():
            self.assertEqual(t93.hash_arquivo(RAIZ / fonte["arquivo"]), fonte["sha256"], fonte["arquivo"])

    def test_cobre_as_13_classes_na_ordem_do_modelo(self):
        classes = self.assoc["classes"]
        self.assertEqual([c["indice"] for c in classes], list(range(13)))
        self.assertEqual([c["nome"] for c in classes], [m["nome"] for m in self.modelo])
        self.assertEqual(self.assoc["total_classes"], 13)
        t93.validar_contrato(self.assoc, self.base, self.fontes)

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

    def test_estado_publicado_e_coerente_com_a_aprovacao(self):
        """Disponível só com chave, status validado e ficha validada; nunca pela chave proposta."""
        for c in self.assoc["classes"]:
            r = t93.resolver(c["indice"], self.assoc, self.base)
            item = next((x for x in self.base["itens"] if x["chave"] == c["chave_conteudo"]), None)
            esperado = c["status_conteudo"] == "validado" and item is not None and item["validated"]
            self.assertEqual(r["disponivel"], esperado, c["indice"])
            self.assertEqual(r["conteudo"] is not None, esperado)
            if not esperado:
                self.assertIn(r["motivo"], {"aguardando_validacao", "item_nao_validado", "sem_chave_oficial"})
            self.assertEqual(r["nome"], c["nome"])

    def test_sem_chave_toda_classe_e_indisponivel_sem_usar_a_chave_proposta(self):
        assoc, base = self.vazio()
        for c in assoc["classes"]:
            r = t93.resolver(c["indice"], assoc, base)
            self.assertFalse(r["disponivel"])
            self.assertIsNone(r["conteudo"])
            self.assertEqual(r["motivo"], "sem_chave_oficial")
        self.assertEqual(t93.cobertura(assoc, base),
                         {"classes": 13, "com_registro": 13, "com_conteudo_disponivel": 0,
                          "indisponiveis_por_motivo": {"sem_chave_oficial": 13}})

    def test_nome_exibido_e_o_do_modelo(self):
        r = t93.resolver(11, self.assoc, self.base)
        self.assertEqual(r["nome"], "Astylus variegatus")
        self.assertIsNone(r["nome_comum"])
        self.assertNotIn("angorá", json.dumps(self.assoc, ensure_ascii=False))

    def test_fichas_completas_resolvem_cada_classe_a_sua_ficha(self):
        assoc, base = self.vazio()
        for i in range(13):
            validar_classe(assoc, base, i, f"equipe.teste_{i:02d}")
        t93.validar_contrato(assoc, base, self.fontes)
        for i in range(13):
            r = t93.resolver(i, assoc, base)
            self.assertTrue(r["disponivel"])
            self.assertEqual(r["conteudo"]["titulo"], assoc["classes"][i]["nome"])
            self.assertEqual([s["id"] for s in r["conteudo"]["secoes"]], ["como_reconhecer", "danos"])
        self.assertEqual(t93.cobertura(assoc, base)["com_conteudo_disponivel"], 13)

    def test_estados_intermediarios_nao_afirmam_conteudo(self):
        assoc, base = self.vazio()
        validar_classe(assoc, base, 3, "equipe.teste_03")
        base["itens"][0]["validated"] = False
        self.assertEqual(t93.resolver(3, assoc, base)["motivo"], "item_nao_validado")
        base["itens"].clear()
        self.assertEqual(t93.resolver(3, assoc, base)["motivo"], "item_ausente_na_base")
        assoc["classes"][3]["status_conteudo"] = "aguardando_validacao"
        self.assertEqual(t93.resolver(3, assoc, base)["motivo"], "aguardando_validacao")
        self.assertFalse(t93.resolver(3, assoc, base)["disponivel"])

    def test_contrato_recusa_validacao_incompleta_conteudo_compartilhado_e_chave_invalida(self):
        assoc, base = self.vazio()
        validar_classe(assoc, base, 3, "equipe.teste_03")
        assoc["classes"][3]["validacao_conteudo"]["evidencia"] = ""
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)
        assoc, base = self.vazio()
        validar_classe(assoc, base, 3, "equipe.compartilhada")
        validar_classe(assoc, base, 10, "equipe.compartilhada")
        base["itens"].pop()  # evita item repetido: o problema testado é o conteúdo único do par 3 e 10
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)
        assoc, base = self.vazio()
        validar_classe(assoc, base, 3, "https://exemplo.com/conteudo")
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)
        assoc, base = self.vazio()
        validar_classe(assoc, base, 3, "equipe.teste_03", origem="parceiro")
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)
        assoc, base = self.vazio()
        assoc["classes"][3]["chave_conteudo"] = "equipe.teste_03"  # chave sem origem
        with self.assertRaises(ValueError):
            t93.validar_contrato(assoc, base)

    def test_contrato_recusa_ficha_mal_formada(self):
        for alteracao in (lambda i: i["secoes"].pop(1),                                   # falta a seção obrigatória
                          lambda i: i["secoes"][0]["itens"].append({"texto": "x" * 241, "fonte": {"id": "EMB-DOC269", "pagina": 78}}),
                          lambda i: i["secoes"][0]["itens"].append({"texto": "sem fonte"}),
                          lambda i: i["secoes"][0]["itens"].append({"texto": "fonte inexistente", "fonte": {"id": "XXX", "pagina": 1}}),
                          lambda i: i.update({"revisado_em": None}),                       # validada sem data
                          lambda i: i.update({"extra": 1})):
            assoc, base = self.vazio()
            validar_classe(assoc, base, 3, "equipe.teste_03")
            alteracao(base["itens"][0])
            with self.subTest(), self.assertRaises((ValueError, KeyError)):
                t93.validar_contrato(assoc, base, self.fontes)

    def test_conteudo_de_classes_do_mesmo_par_permanece_separado(self):
        assoc, base = self.vazio()
        validar_classe(assoc, base, 3, "equipe.teste_03")
        validar_classe(assoc, base, 10, "equipe.teste_10")
        a, b = t93.resolver(3, assoc, base), t93.resolver(10, assoc, base)
        self.assertNotEqual(a["conteudo"]["titulo"], b["conteudo"]["titulo"])
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
            assoc, base = self.vazio()
            validar_classe(assoc, base, 7, "equipe.teste_07")
            t93.gravar_json(saida / t93.ASSOCIACAO, assoc)
            curada = {**t93.base_vazia(), "itens": [ficha("equipe.teste_07")]}
            t93.gravar_json(saida / t93.BASE, curada)
            novo = t93.gerar(RAIZ, saida)
            self.assertEqual(novo["classes"][7]["chave_conteudo"], "equipe.teste_07")
            self.assertEqual(novo["classes"][7]["origem_chave"], "equipe")
            self.assertEqual(novo["classes"][7]["status_conteudo"], "validado")
            self.assertEqual(json.loads((saida / t93.BASE).read_text(encoding="utf-8")), curada)

    def test_content_ts_do_frontend_reproduz_a_associacao_e_traz_as_fontes(self):
        atual = (RAIZ / t93.CONTENT_TS).read_text(encoding="utf-8")
        self.assertEqual(t93.content_ts(self.assoc, self.base, self.fontes), atual,
                         "rode: python -m src.associacao_conteudo_t9_3 frontend")
        assoc, base = self.vazio()
        validar_classe(assoc, base, 4, "equipe.teste_04")
        gerado = t93.content_ts(assoc, base, self.fontes)
        self.assertIn('"4": {', gerado)
        self.assertIn('"source": "SOSA-GÓMEZ et al., 2014, p. 78"', gerado)
        self.assertIn('"sources": [\n      "SOSA-GÓMEZ et al., 2014, p. 78"', gerado)
        self.assertIn("SOSA-GÓMEZ, D. R. et al. Manual de identificação", gerado)  # referência completa no app
        self.assertNotIn('"0": {', gerado)  # classe sem ficha validada não entra

    def test_aprovar_valida_so_as_classes_escolhidas_e_exige_ficha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / t93.SAIDA).mkdir(parents=True)
            for nome in (t93.ASSOCIACAO, t93.BASE, t93.FONTES):
                shutil.copy(PASTA / nome, raiz / t93.SAIDA / nome)
            # parte do estado "aguardando": o teste não depende de a equipe já ter aprovado
            assoc, base = t93.carregar(raiz)
            for c in assoc["classes"]:
                c.update({"status_conteudo": "aguardando_validacao", "validacao_conteudo": None})
            for i in base["itens"]:
                i.update({"validated": False, "revisado_em": None})
            t93.gravar_json(raiz / t93.SAIDA / t93.ASSOCIACAO, assoc)
            t93.gravar_json(raiz / t93.SAIDA / t93.BASE, base)
            feitos = t93.aprovar(raiz, "ata de teste", "2026-11-21", [0, 1])
            assoc, base = t93.carregar(raiz)
            self.assertEqual(feitos, [0, 1])
            self.assertEqual([c["status_conteudo"] for c in assoc["classes"][:3]], ["validado", "validado", "aguardando_validacao"])
            self.assertEqual(assoc["status"], "fichas_da_equipe_em_revisao")
            self.assertEqual(t93.cobertura(assoc, base)["com_conteudo_disponivel"], 2)
            self.assertEqual(assoc["classes"][0]["validacao_conteudo"], {"data": "2026-11-21", "evidencia": "ata de teste"})
            self.assertNotIn("responsavel", assoc["classes"][0]["validacao_conteudo"])
            t93.aprovar(raiz, "ata de teste", "2026-11-21")
            assoc, base = t93.carregar(raiz)
            self.assertEqual(assoc["status"], "fichas_da_equipe_validadas")
            self.assertEqual(t93.cobertura(assoc, base)["com_conteudo_disponivel"], 13)
            self.assertEqual(t93.content_ts(assoc, base, t93.carregar_fontes(raiz)).count('"validated": true'), 13)
            base["itens"].pop()  # classe sem ficha na base não pode ser aprovada
            t93.gravar_json(raiz / t93.SAIDA / t93.BASE, base)
            with self.assertRaises(ValueError):
                t93.aprovar(raiz, "ata de teste", "2026-11-21", [12])

    def test_fichas_do_projeto_md_estao_atualizadas(self):
        texto = (RAIZ / t93.PROJETO_MD).read_text(encoding="utf-8")
        bloco = texto.split(t93.MARCA_INICIO, 1)[1].split(t93.MARCA_FIM, 1)[0].strip("\n")
        self.assertEqual(bloco, t93.fichas_markdown(self.assoc, self.base, self.fontes),
                         "rode: python -m src.associacao_conteudo_t9_3 docs")

    def test_nenhum_acesso_a_rede(self):
        codigo = (RAIZ / "src/associacao_conteudo_t9_3.py").read_text(encoding="utf-8")
        for proibido in ("urllib", "requests", "socket", "http.client", "urlopen", "webbrowser"):
            self.assertNotIn(proibido, codigo)
        dados = (PASTA / t93.ASSOCIACAO).read_text(encoding="utf-8") + (PASTA / t93.BASE).read_text(encoding="utf-8")
        self.assertNotIn("http", dados, "dados locais não devem apontar para a rede")


if __name__ == "__main__":
    unittest.main(verbosity=2)
