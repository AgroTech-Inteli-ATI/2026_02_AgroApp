"""Regressões da revisão de duplicatas entre partições, sem inferência ou treino."""

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, PngImagePlugin

from src.independencia_t10_1 import (
    assinatura, candidatos_cruzados, grupos_relacionados, juntar_revisao, sobreposicoes,
)


class IndependenciaTeste(unittest.TestCase):
    def test_mesma_foto_com_bytes_diferentes(self):
        with tempfile.TemporaryDirectory() as pasta:
            primeiro = Path(pasta) / "primeiro.png"
            segundo = Path(pasta) / "segundo.png"
            imagem = Image.fromarray(np.random.default_rng(42).integers(0, 256, (80, 120, 3), dtype=np.uint8))
            imagem.save(primeiro)
            metadados = PngImagePlugin.PngInfo()
            metadados.add_text("origem", "outra cópia")
            imagem.save(segundo, pnginfo=metadados)
            self.assertNotEqual(sha256(primeiro.read_bytes()).hexdigest(), sha256(segundo.read_bytes()).hexdigest())
            self.assertEqual(assinatura(primeiro), assinatura(segundo))
            linhas = [{"image_id": "A", "particao": "treino", **assinatura(primeiro)},
                      {"image_id": "B", "particao": "teste", **assinatura(segundo)}]
            self.assertEqual(candidatos_cruzados(linhas)[0]["distancia_phash"], 0)

    def test_colisao_perceptual_exige_revisao(self):
        linhas = [{"image_id": "A", "particao": "treino", "phash64": "0"},
                  {"image_id": "B", "particao": "teste", "phash64": "0"},
                  {"image_id": "C", "particao": "treino", "phash64": "ffffffffffffffff"}]
        candidatos = candidatos_cruzados(linhas)
        self.assertEqual(len(candidatos), 1)
        resultado = juntar_revisao(candidatos, [{"image_id_1": "B", "image_id_2": "A",
            "resultado": "sem_vinculo_confirmado", "justificativa": "Insetos diferentes."}])
        self.assertEqual(resultado[0]["resultado"], "sem_vinculo_confirmado")

    def test_recusa_revisao_incompleta_repetida_ou_de_outros_pares(self):
        candidatos = [{"image_id_1": "A", "image_id_2": "B", "distancia_phash": 2}]
        revisao = {"image_id_1": "A", "image_id_2": "B", "resultado": "duplicata_confirmada",
                   "justificativa": "Mesmos detalhes da fotografia."}
        for linhas in ([], [revisao, revisao], [{**revisao, "image_id_2": "C"}]):
            with self.assertRaisesRegex(ValueError, "exatamente"):
                juntar_revisao(candidatos, linhas)

    def test_grupo_inclui_membros_da_observacao_e_preserva_suspeita(self):
        linhas = [{"image_id": identificador, "particao": particao, "grupo_particao": grupo,
                   "inat_obs_id": observacao, "caminho_relativo": f"{identificador}.jpg",
                   "sha256_original": identificador, "indice_modelo": "0"}
                  for identificador, particao, grupo, observacao in (
                      ("A", "treino", "g1", "obs1"), ("B", "teste", "g2", ""),
                      ("C", "treino", "g1", "obs1"), ("D", "teste", "g3", ""))]
        pares = [{"image_id_1": "A", "image_id_2": "B", "resultado": "relacao_suspeita"},
                 {"image_id_1": "A", "image_id_2": "D", "resultado": "sem_vinculo_confirmado"}]
        grupos = grupos_relacionados(linhas, pares)
        self.assertEqual({linha["image_id"] for linha in grupos}, {"A", "B", "C"})
        self.assertEqual({linha["natureza"] for linha in grupos}, {"relacao_suspeita"})
        self.assertEqual(linhas[0]["grupo_particao"], "g1")
        self.assertEqual(linhas[1]["particao"], "teste")

    def test_metadado_cruzado_e_detectado_e_ausencia_e_ignorada(self):
        linhas = [{"image_id": "A", "particao": "treino", "inat_obs_id": "obs1"},
                  {"image_id": "B", "particao": "teste", "inat_obs_id": "obs1"},
                  {"image_id": "C", "particao": "validacao", "inat_obs_id": ""},
                  {"image_id": "D", "particao": "treino", "inat_obs_id": ""}]
        resultado = sobreposicoes(linhas, "inat_obs_id")
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ids"], "A|B")


if __name__ == "__main__":
    unittest.main()
