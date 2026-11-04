"""Testes do conjunto e do contrato de quantização, sem TensorFlow ou acervo externo."""

import copy
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import quantizacao_t7_3 as q


class QuantizacaoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.pacote = self.raiz / "pacote"
        self.pacote.mkdir()
        self.indice = self.raiz / "indice.csv"
        self.saida = self.raiz / "conjunto"
        classes = [{"indice": i, "nome": f"classe {i}"} for i in range(13)]
        q.gravar(self.pacote / "classes.json", classes)
        self.linhas = []
        for i in range(13):
            caminho = f"imagem_{i}.png"
            Image.new("RGB", (24, 8), (i*18, i*18, i*18)).save(self.raiz / caminho)
            self.linhas.append({"image_id": f"IMG_{i}", "caminho_relativo": caminho,
                "sha256_original": q._hash(self.raiz / caminho), "indice_modelo": str(i),
                "nome_classe_modelo": f"classe {i}", "grupo_particao": f"grupo_{i}", "particao": "treino"})
        # Os arquivos de validação/teste nem existem: preparar não pode abri-los.
        for particao in ("validacao", "teste"):
            self.linhas.append({**self.linhas[0], "image_id": particao, "particao": particao,
                "grupo_particao": particao, "caminho_relativo": f"nao_abrir_{particao}.png",
                "sha256_original": sha256(particao.encode()).hexdigest()})
        self.indice.write_text(q.texto_csv(self.linhas))
        q.gravar(self.pacote / "manifesto.json", {"indice_sha256": q._hash(self.indice),
            "sha256": {"classes.json": q._hash(self.pacote / "classes.json"), "modelo.keras": "modelo_fixture"}})
        q.preparar(self.raiz, self.saida, self.indice, self.pacote, total=13)
        fotos = q.ler_csv(self.saida / "manifesto_calibracao.csv")
        condicoes = ["sombra_ou_baixa_luz", "luz_difusa", "luz_direta_ou_realces"]
        self.revisao = {"imagens": [{"image_id": r["image_id"], "sha256_original": r["sha256_original"],
            "condicoes": [condicoes[i%3]], "observacao": "anotação de fixture"} for i,r in enumerate(fotos)]}
        q.gravar(self.saida / "revisao_iluminacao.json", self.revisao)

    def carregar(self):
        return q.carregar_conjunto(self.raiz, self.saida, self.indice, self.pacote)

    def regravar_manifesto(self, fotos):
        (self.saida / "manifesto_calibracao.csv").write_text(q.texto_csv(fotos))
        prova = q.ler(self.saida / "conjunto.json")
        prova["manifesto_csv_sha256"] = q._hash(self.saida / "manifesto_calibracao.csv")
        q.gravar(self.saida / "conjunto.json", prova)

    def test_treino_real_cobertura_e_entrada_sem_augmentation(self):
        fotos, imagens, prova, classes, _ = self.carregar()
        self.assertEqual(len(fotos), 13)
        self.assertEqual(len(classes), 13)
        self.assertEqual({r["particao"] for r in fotos}, {"treino"})
        self.assertFalse(prova["augmentation"])
        for x in imagens:
            self.assertEqual(x.shape, (224,224,3))
            self.assertEqual(x.dtype, np.float32)
            self.assertTrue(np.isfinite(x).all() and x.min() >= 0 and x.max() <= 1)

    def test_selecao_reproduzivel_balanceada_e_sem_repetir_grupos(self):
        catalogo = []
        for i in range(13):
            for j in range(30):
                catalogo.append({"image_id": f"{i}-{j}", "indice_modelo": str(i),
                    "grupo_particao": f"g{i}-{j}", "sha256_original": f"h{i}-{j}", "faixa_brilho": q.FAIXAS[j%3]})
        a = q.selecionar(catalogo)
        self.assertEqual(a, q.selecionar(list(reversed(catalogo))))
        self.assertNotEqual(a, q.selecionar(catalogo, semente=43))
        self.assertEqual(len(a), 200)
        self.assertEqual(len({r["grupo_particao"] for r in a}), 200)
        for i in range(13):
            rs = [r for r in a if int(r["indice_modelo"]) == i]
            self.assertIn(len(rs), (15,16))
            self.assertEqual({r["faixa_brilho"] for r in rs}, set(q.FAIXAS))

    def test_brilho_exclui_padding(self):
        foto = self.raiz / "branca.png"
        Image.new("RGB", (100, 4), "white").save(foto)
        x, brilho, faixa = q.medir_imagem(foto)
        self.assertLess(float(x.mean()), .6)
        self.assertAlmostEqual(brilho, 1.0, places=6)
        self.assertEqual(faixa, "alto_brilho")

    def test_recusa_validacao_e_teste_mesmo_com_hash_manifesto_atualizado(self):
        originais = q.ler_csv(self.saida / "manifesto_calibracao.csv")
        for particao in ("validacao", "teste"):
            fotos = copy.deepcopy(originais)
            for r in fotos:
                if r["indice_modelo"] == "0":
                    r.update(next(l for l in self.linhas if l["particao"] == particao))
            self.regravar_manifesto(fotos)
            with self.subTest(particao=particao), self.assertRaisesRegex(ValueError, "só aceita fotos do treino"):
                self.carregar()

    def test_recusa_foto_alterada(self):
        Image.new("RGB", (24, 8), "red").save(self.raiz / "imagem_0.png")
        with self.assertRaisesRegex(ValueError, "imagem original alterada"):
            self.carregar()

    def test_recusa_classe_ausente_ou_grupo_repetido(self):
        originais = q.ler_csv(self.saida / "manifesto_calibracao.csv")
        for modo in ("classe_ausente", "grupo_repetido"):
            fotos = copy.deepcopy(originais)
            if modo == "classe_ausente":fotos.pop()
            else:fotos[0]["grupo_particao"] = fotos[1]["grupo_particao"]
            self.regravar_manifesto(fotos)
            with self.subTest(modo=modo), self.assertRaisesRegex(ValueError, "conjunto incompleto"):
                self.carregar()

    def test_recusa_cobertura_documentada_falsa(self):
        prova = q.ler(self.saida / "conjunto.json")
        prova["cobertura_classes"][0]["selecionadas"] = 99
        q.gravar(self.saida / "conjunto.json", prova)
        with self.assertRaisesRegex(ValueError, "cobertura por classe"):
            self.carregar()

    def test_recusa_revisao_incompleta_ou_de_imagem_ausente(self):
        fotos = q.ler_csv(self.saida / "manifesto_calibracao.csv")
        for modo in ("classe", "id", "condicoes"):
            revisao = copy.deepcopy(self.revisao)
            if modo == "classe":revisao["imagens"].pop()
            elif modo == "id":revisao["imagens"][0]["image_id"] = "ausente"
            else:
                for a in revisao["imagens"]:a["condicoes"] = ["nao_inferivel"]
            with self.subTest(modo=modo), self.assertRaises(ValueError):q.validar_revisao(revisao, fotos)

    def test_quantizacao_arredondamento_e_saturacao(self):
        x = np.array([-2.,0.,.125,.25,.5,1.,3.], dtype=np.float32)
        resultado = q.quantizar(x, .25, -1)
        np.testing.assert_array_equal(resultado, [-9,-1,-1,0,1,3,11])
        limites = q.quantizar(np.array([-100.,100.]), .01, -128)
        np.testing.assert_array_equal(limites, [-128,127])

    def test_recusa_indice_e_classes_de_outra_origem(self):
        self.indice.write_text(self.indice.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "índice não corresponde"):
            self.carregar()


if __name__ == "__main__":
    unittest.main()
