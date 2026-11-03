"""Validação T7.1; integração real requer requirements-treino.txt."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.conversao_t7_1 import converter


class ConversaoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rodada = Path(self.temp.name) / "rodada"
        self.rodada.mkdir()
        self.saida = Path(self.temp.name) / "saida"
        (self.rodada / "melhor_modelo.keras").write_bytes(b"checkpoint")
        self.metricas = {"esquema": "metricas_validacao_T5_1_v1", "backbone": "sintetico",
                         "tamanho_entrada": 8, "validacao": {"por_classe": [
                             {"indice": 0, "nome": "a"}, {"indice": 1, "nome": "b"}]}}
        self.salvar_metricas()

    def salvar_metricas(self):
        (self.rodada / "metricas_validacao.json").write_text(json.dumps(self.metricas), encoding="utf-8")

    def test_recusa_classes_desordenadas(self):
        self.metricas["validacao"]["por_classe"].reverse()
        self.salvar_metricas()
        with self.assertRaisesRegex(ValueError, "ordem"):
            converter(self.rodada, self.saida)
        self.assertFalse(self.saida.exists())

    def test_recusa_rodada_sem_checkpoint(self):
        (self.rodada / "melhor_modelo.keras").unlink()
        with self.assertRaisesRegex(ValueError, "arquivo obrigatório ausente"):
            converter(self.rodada, self.saida)
        self.assertFalse(self.saida.exists())

    def test_recusa_tamanho_invalido(self):
        self.metricas["tamanho_entrada"] = -1
        self.salvar_metricas()
        with self.assertRaisesRegex(ValueError, "tamanho_entrada"):
            converter(self.rodada, self.saida)
        self.assertFalse(self.saida.exists())

    def test_preserva_artefato_existente(self):
        self.saida.mkdir()
        destino = self.saida / "modelo.tflite"
        destino.write_bytes(b"preservar")
        with self.assertRaisesRegex(ValueError, "já contém"):
            converter(self.rodada, self.saida)
        self.assertEqual(destino.read_bytes(), b"preservar")

    @unittest.skipUnless(importlib.util.find_spec("tensorflow") and importlib.util.find_spec("keras_hub"),
                         "integração requer TensorFlow e KerasHub")
    def test_conversao_real_e_contrato(self):
        import keras
        import numpy as np
        import tensorflow as tf
        from PIL import Image
        keras.utils.set_random_seed(42)
        entrada = keras.Input((8, 8, 3), name="imagem")
        x = keras.layers.GlobalAveragePooling2D()(entrada)
        modelo = keras.Model(entrada, keras.layers.Dense(2, activation="softmax")(x))
        modelo.save(self.rodada / "melhor_modelo.keras")
        imagem = self.rodada / "foto.png"
        Image.new("RGB", (12, 6), (40, 120, 80)).save(imagem)
        resultado = converter(self.rodada, self.saida, [imagem])
        self.assertEqual(resultado["entrada"]["shape"], [1, 8, 8, 3])
        self.assertEqual(resultado["saida"]["shape"], [1, 2])
        self.assertEqual(len(resultado["validacao"]["amostras"]), 4)
        interpretador = tf.lite.Interpreter(model_path=str(self.saida / "modelo.tflite"))
        interpretador.allocate_tensors()
        interpretador.set_tensor(interpretador.get_input_details()[0]["index"], np.zeros((1, 8, 8, 3), np.float32))
        interpretador.invoke()
        self.assertTrue((self.saida / "relatorio_conversao.md").is_file())
        self.assertEqual(json.loads((self.saida / "contrato_tensores.json").read_text(encoding="utf-8")), resultado)

    @unittest.skipUnless(importlib.util.find_spec("tensorflow") and importlib.util.find_spec("keras_hub"),
                         "integração requer TensorFlow e KerasHub")
    def test_recusa_saida_sem_softmax(self):
        import keras
        entrada = keras.Input((8, 8, 3))
        x = keras.layers.GlobalAveragePooling2D()(entrada)
        modelo = keras.Model(entrada, keras.layers.Dense(2, kernel_initializer="zeros",
                                                       bias_initializer="zeros")(x))
        modelo.save(self.rodada / "melhor_modelo.keras")
        with self.assertRaisesRegex(ValueError, "softmax"):
            converter(self.rodada, self.saida)
        self.assertFalse(self.saida.exists())

    @unittest.skipUnless(importlib.util.find_spec("tensorflow") and importlib.util.find_spec("keras_hub"),
                         "integração requer TensorFlow e KerasHub")
    def test_backbone_do_projeto_sem_download_de_pesos(self):
        from src import backbones
        from src.treinamento_t5_1 import construir_modelo
        backbone = backbones.REGISTRO["mobilenet_v3_small"]
        modelo, _ = construir_modelo(backbone, 2, 0.2, pesos_pre_treinados=False)
        self.metricas["tamanho_entrada"] = backbone.tamanho_entrada
        self.metricas["backbone"] = backbone.nome
        self.salvar_metricas()
        modelo.save(self.rodada / "melhor_modelo.keras")
        resultado = converter(self.rodada, self.saida)
        self.assertEqual(resultado["entrada"]["shape"], [1, backbone.tamanho_entrada, backbone.tamanho_entrada, 3])
        self.assertEqual(resultado["saida"]["shape"], [1, 2])


if __name__ == "__main__":
    unittest.main()
