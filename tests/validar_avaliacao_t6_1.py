"""Avaliação final com imagens e modelo sintéticos; sem necessidade de TensorFlow."""

import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.avaliacao_t6_1 import avaliar


class Modelo:
    input_shape = (None, 16, 16, 3)
    output_shape = (None, 3)

    def __init__(self):
        self.contagem = 0

    def predict_on_batch(self, imagens):
        assert imagens.dtype == np.float32 and 0 <= imagens.min() <= imagens.max() <= 1
        self.contagem += len(imagens)
        return np.tile([0.8, 0.1, 0.1], (len(imagens), 1))


class AvaliacaoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.rodada = self.raiz / "rodada"
        self.rodada.mkdir()
        (self.rodada / "melhor_modelo.keras").write_bytes(b"modelo sintetico")
        self.indice = self.raiz / "indice.csv"
        self.saida = self.raiz / "saida"
        self.linhas = []
        for i, (particao, rotulo) in enumerate([("treino", 2), ("validacao", 0), ("teste", 0), ("teste", 0), ("teste", 1)]):
            imagem = self.raiz / f"{i}.png"
            Image.new("RGB", (20, 10), (i * 40, 30, 50)).save(imagem)
            self.linhas.append({"image_id": str(i), "caminho_relativo": imagem.name,
                                "sha256_original": sha256(imagem.read_bytes()).hexdigest(),
                                "indice_modelo": rotulo, "nome_classe_modelo": str(rotulo),
                                "grupo_particao": f"g{i}", "particao": particao})
        self.gravar_indice()
        dados = {"esquema": "metricas_validacao_T5_1_v1", "backbone": "sintetico", "tamanho_entrada": 16,
                 "validacao": {"por_classe": [{"indice": i, "nome": str(i)} for i in range(3)]}}
        (self.rodada / "metricas_validacao.json").write_text(json.dumps(dados))

    def gravar_indice(self):
        with self.indice.open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(self.linhas[0]))
            escritor.writeheader()
            escritor.writerows(self.linhas)
        (self.rodada / "ambiente.json").write_text(json.dumps({"sha256": {
            "indice_pipeline": sha256(self.indice.read_bytes()).hexdigest()}}))

    def executar(self, modelo=None):
        return avaliar(self.rodada, self.raiz, self.saida, self.indice,
                       batch=2, carregador=lambda _: modelo or Modelo())

    def test_metricas_e_relatorios(self):
        modelo = Modelo()
        resultado = self.executar(modelo)
        m = resultado["teste"]
        self.assertEqual(modelo.contagem, 3)
        self.assertEqual(m["matriz_confusao"], [[2, 0, 0], [1, 0, 0], [0, 0, 0]])
        self.assertAlmostEqual(m["por_classe"][0]["precisao"], 2 / 3)
        self.assertEqual(m["por_classe"][0]["recall"], 1)
        self.assertAlmostEqual(m["por_classe"][0]["f1"], 0.8)
        self.assertEqual(m["por_classe"][1]["f1"], 0)
        self.assertIsNone(m["por_classe"][2]["f1"])
        self.assertAlmostEqual(m["f1_macro"], 0.4)
        self.assertEqual(resultado["metrica_principal"], "f1_macro")
        self.assertEqual(len(list(self.saida.iterdir())), 4)
        with self.assertRaisesRegex(ValueError, "preservar"):
            self.executar()

    def test_conferencia_sklearn(self):
        from sklearn.metrics import precision_recall_fscore_support, f1_score
        m = self.executar()["teste"]
        p, r, f, _ = precision_recall_fscore_support([0, 0, 1], [0, 0, 0], labels=[0, 1], zero_division=0)
        for i in range(2):
            np.testing.assert_allclose([m["por_classe"][i][k] for k in ("precisao", "recall", "f1")], [p[i], r[i], f[i]])
        self.assertAlmostEqual(m["f1_macro"], f1_score([0, 0, 1], [0, 0, 0], average="macro", labels=[0, 1], zero_division=0))

    def test_hash_e_isolamento(self):
        (self.raiz / "0.png").unlink()  # imagem de treino não deve ser aberta
        self.executar()

    def test_recusa_imagem_alterada(self):
        (self.raiz / "2.png").write_bytes(b"alterada")
        with self.assertRaisesRegex(ValueError, "hash original"):
            self.executar()

    def test_recusa_indice_alterado(self):
        with self.indice.open("a") as arquivo:
            arquivo.write("\n")
        with self.assertRaisesRegex(ValueError, "índice diverge"):
            self.executar()

    def test_recusa_grupo_cruzado(self):
        self.linhas[2]["grupo_particao"] = self.linhas[0]["grupo_particao"]
        self.gravar_indice()
        with self.assertRaisesRegex(ValueError, "compartilhado"):
            self.executar()

    def test_recusa_predicoes_invalidas(self):
        class Invalido(Modelo):
            def predict_on_batch(self, imagens):
                return np.full((len(imagens), 3), np.nan)
        with self.assertRaisesRegex(ValueError, "softmax"):
            self.executar(Invalido())


if __name__ == "__main__":
    unittest.main()
