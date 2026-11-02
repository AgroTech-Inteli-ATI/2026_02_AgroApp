"""Confere cobertura e evidências da revisão sem exigir as fotos externas."""

import copy
import csv
import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import analise_candidato_t6_3 as analise
from src import matriz_candidato_t6_2 as matriz


def linhas(texto):
    return list(csv.DictReader(io.StringIO(texto)))


class AnaliseCandidatoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = matriz.carregar(matriz.AVALIACAO, matriz.PACOTE, matriz.INDICE)
        cls.anotacoes = matriz.ler_json(analise.ANOTACOES)

    def test_cobertura_e_contagens_da_entrega(self):
        pasta = analise.SAIDA
        revisao = matriz.ler_csv(pasta / "revisao_por_imagem.csv")
        pares = matriz.ler_csv(pasta / "analise_por_par.csv")
        cobertura = matriz.ler_csv(pasta / "cobertura_classes.csv")
        analise.validar_anotacoes(self.dados, self.anotacoes)
        erros = {r["image_id"]: r for r in self.dados["erros"]}
        self.assertEqual(len(revisao), 72)
        self.assertEqual({r["image_id"] for r in revisao}, set(erros))
        for r in revisao:
            for campo in ("classe_real", "classe_prevista", "caminho_relativo", "sha256_original"):
                self.assertEqual(r[campo], erros[r["image_id"]][campo])
            self.assertEqual(r["validacao_taxonomica"], "pendente")
        self.assertEqual(len(pares), 35)
        self.assertEqual(sum(int(r["erros"]) for r in pares), 72)
        principais = [r for r in pares if r["principal"] == "sim"]
        self.assertEqual(len(principais), 16)
        self.assertEqual(sum(int(r["erros"]) for r in principais), 53)
        for r in pares:
            par = [p for p in self.dados["pares"] if p[:2] == (int(r["indice_real"]), int(r["indice_previsto"]))][0]
            self.assertEqual(int(r["erros"]), par[2])
            self.assertEqual(r["causa_confirmada"], "nenhuma")
        self.assertEqual(len(cobertura), 39)
        self.assertEqual(sum(int(r["imagens"]) for r in cobertura if r["particao"] == "teste"), 473)

    def test_achados_nao_confundem_fotos_estagios_e_independencia(self):
        pares = matriz.ler_csv(analise.SAIDA / "analise_por_par.csv")
        par = next(r for r in pares if r["indice_real"] == "6" and r["indice_previsto"] == "5")
        self.assertEqual((par["erros"], par["observacoes_inat_nos_erros"]), ("5", "1"))
        cobertura = matriz.ler_csv(analise.SAIDA / "cobertura_classes.csv")
        treino = next(r for r in cobertura if r["indice_classe"] == "6" and r["particao"] == "treino")
        teste = next(r for r in cobertura if r["indice_classe"] == "6" and r["particao"] == "teste")
        self.assertEqual((treino["field_Nymph"], treino["field_sem_estagio"]), ("0", "26"))
        self.assertEqual(teste["field_Nymph"], "7")
        revisao = matriz.ler_csv(analise.SAIDA / "revisao_por_imagem.csv")
        suspeito = next(r for r in revisao if r["image_id"] == "IMG_02602")
        self.assertEqual(suspeito["rotulo_na_fonte"], "spodoptera_frugiperda")
        self.assertIn("rotulo_inconsistente", suspeito["hipoteses_de_causa"])
        self.assertEqual(suspeito["status_causa"], "hipotese")
        adulto = next(r for r in revisao if r["image_id"] == "IMG_02972")
        self.assertNotIn("rotulo_inconsistente", adulto["hipoteses_de_causa"])
        self.assertEqual(adulto["life_stage_metadado"], "")
        self.assertEqual(adulto["estagio_visual"], "adulto_aparente")

    def test_recusa_revisao_incompleta_extra_ou_categoria_invalida(self):
        for modo in ("ausente", "extra", "categoria"):
            a = copy.deepcopy(self.anotacoes)
            if modo == "ausente":
                del a["anotacoes"]["IMG_02602"]
            elif modo == "extra":
                a["anotacoes"]["IMG_EXTRA"] = a["anotacoes"]["IMG_02602"]
            else:
                a["anotacoes"]["IMG_02602"][2] = ["erro_confirmado_por_especialista"]
            with self.subTest(modo=modo), self.assertRaises(ValueError):
                analise.validar_anotacoes(self.dados, a)

    def test_recusa_imagem_diferente_da_avaliada(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp)
            p = raiz / "imagem.jpg"
            p.write_bytes(b"imagem original")
            erro = {"image_id": "exemplo", "caminho_relativo": p.name,
                    "sha256_original": matriz.hash_arquivo(p)}
            analise.conferir_imagens(raiz, [erro])
            p.write_bytes(b"imagem alterada")
            with self.assertRaisesRegex(ValueError, "imagem alterada"):
                analise.conferir_imagens(raiz, [erro])

    def test_construcao_deterministica_e_metadados_incompletos(self):
        dados = {"nomes": ["a", "b"], "erros": [{"image_id": "x", "caminho_relativo": "dataset/field/a/x.jpg",
            "indice_real": 0, "classe_real": "a", "indice_previsto": 1, "classe_prevista": "b",
            "sha256_original": "abc"}], "pares": [(0, 1, 1, 1.0)], "suportes": [1, 0]}
        indice = [{"image_id": "x", "caminho_relativo": "dataset/field/a/x.jpg", "indice_modelo": "0",
                   "particao": "teste", "grupo_particao": "g"}]
        meta = {"dataset/field/a/x.jpg": {"class_name": "a", "inat_obs_id": "1", "life_stage": ""}}
        anotacoes = {"metodo": "teste", "anotacoes": {"x": ["indeterminado", ["corpo_visivel"], [], "observação"]}}
        a = analise.construir(dados, indice, meta, {}, anotacoes)
        self.assertEqual(a, analise.construir(dados, indice, meta, {}, anotacoes))
        with self.assertRaisesRegex(ValueError, "metadado de campo ausente"):
            analise.construir(dados, indice, {}, {}, anotacoes)


if __name__ == "__main__":
    unittest.main()
