"""Confere a matriz publicada contra as previsões reais e recusa fontes incoerentes."""

import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np
from sklearn.metrics import confusion_matrix

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import matriz_candidato_t6_2 as matriz


class MatrizTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = Path(self.tmp.name)
        self.avaliacao = p / "avaliacao"
        shutil.copytree(matriz.AVALIACAO, self.avaliacao)
        self.pacote = p / "pacote"
        self.pacote.mkdir()
        for n in ("manifesto.json", "classes.json"):
            shutil.copy2(matriz.PACOTE / n, self.pacote / n)
        self.indice = p / "indice.csv"
        shutil.copy2(matriz.INDICE, self.indice)

    def carregar(self):
        return matriz.carregar(self.avaliacao, self.pacote, self.indice)

    def atualizar_hash_fonte(self, nome):
        p = self.avaliacao / "proveniencia_avaliacao.json"
        fonte = matriz.ler_json(p)
        fonte["artefatos_sha256"][nome] = matriz.hash_arquivo(self.avaliacao / nome)
        p.write_text(json.dumps(fonte), encoding="utf-8")

    def test_reconstroi_matriz_real_e_pares_sem_perda(self):
        dados = self.carregar()
        linhas = matriz.ler_csv(self.avaliacao / "predicoes_teste.csv")
        esperado = confusion_matrix([int(r["indice_real"]) for r in linhas],
                                    [int(r["indice_previsto"]) for r in linhas], labels=list(range(13)))
        np.testing.assert_array_equal(dados["matriz"], esperado)
        self.assertEqual(int(esperado.sum()), 473)
        self.assertEqual(int(np.trace(esperado)), 401)
        self.assertEqual(len(dados["erros"]), 72)
        self.assertEqual(sum(p[2] for p in dados["pares"]), 72)
        self.assertEqual(dados["matriz"][8, 3], 6)
        self.assertEqual(dados["matriz"][6, 5], 5)
        self.assertAlmostEqual(dados["proporcoes"][8, 3], .5)
        np.testing.assert_allclose(dados["proporcoes"].sum(axis=1), 1)
        arquivos = matriz.conteudos(dados, 2)
        pares = list(csv.DictReader(io.StringIO(arquivos["pares_confundidos.csv"]), delimiter=";"))
        self.assertEqual(sum(int(r["erros"]) for r in pares), 72)
        self.assertTrue(any(r["destacado"] == "nao" for r in pares))
        self.assertEqual(len(list(csv.DictReader(io.StringIO(arquivos["erros_por_imagem.csv"])))), 72)
        self.assertEqual(arquivos, matriz.conteudos(self.carregar(), 2))

    def test_recusa_previsoes_alteradas_sem_atualizar_prova(self):
        with (self.avaliacao / "predicoes_teste.csv").open("a", encoding="utf-8") as f:
            f.write("\n")
        with self.assertRaisesRegex(ValueError, "artefato da T6.1 alterado"):
            self.carregar()

    def test_recusa_ids_repetidos_mesmo_com_hash_atualizado(self):
        caminho = self.avaliacao / "predicoes_teste.csv"
        linhas = matriz.ler_csv(caminho)
        linhas[1]["image_id"] = linhas[0]["image_id"]
        with caminho.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0]))
            w.writeheader()
            w.writerows(linhas)
        self.atualizar_hash_fonte(caminho.name)
        with self.assertRaisesRegex(ValueError, "IDs de teste"):
            self.carregar()

    def test_recusa_matriz_incoerente_mesmo_com_hash_atualizado(self):
        p = self.avaliacao / "metricas_teste.json"
        d = matriz.ler_json(p)
        d["teste"]["matriz_confusao"][0][0] -= 1
        d["teste"]["matriz_confusao"][0][1] += 1
        p.write_text(json.dumps(d), encoding="utf-8")
        self.atualizar_hash_fonte(p.name)
        with self.assertRaisesRegex(ValueError, "matriz ou métricas"):
            self.carregar()

    def test_recusa_outro_checkpoint_e_indice(self):
        p = self.avaliacao / "metricas_teste.json"
        d = matriz.ler_json(p)
        d["sha256"]["modelo"] = "checkpoint diferente"
        p.write_text(json.dumps(d), encoding="utf-8")
        self.atualizar_hash_fonte(p.name)
        with self.assertRaisesRegex(ValueError, "checkpoint selecionado"):
            self.carregar()
        shutil.copy2(matriz.AVALIACAO / p.name, p)
        self.atualizar_hash_fonte(p.name)
        with self.indice.open("a", encoding="utf-8") as f:
            f.write("\n")
        with self.assertRaisesRegex(ValueError, "índice não corresponde"):
            self.carregar()


if __name__ == "__main__":
    unittest.main()
