"""Valida rastreabilidade, comparabilidade e isolamento do conjunto de teste."""

from pathlib import Path
import csv
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.converter_t5_6 import amostra_calibracao
from src.selecao_t5_6 import comparar, gravar, hash_arquivo, publicar, validar_rodada, verificar_pacote


class SelecaoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.modelos = self.raiz / "modelos"
        self.modelos.mkdir()
        self.indice = self.raiz / "indice.csv"
        self.pesos = self.raiz / "pesos.json"
        gravar(self.pesos, {"teste": "pesos sintéticos"})
        self.linhas = [{"image_id": f"{p}-{i}-{j}", "indice_modelo": str(i),
                        "nome_classe_modelo": f"classe-{i}", "particao": p,
                        "grupo_particao": f"{p}-{i}-{j}", "sha256_original": f"{p}-{i}-{j}"}
                       for p in ("treino", "validacao", "teste") for i in range(13)
                       for j in range(16 if p == "treino" else 1)]
        with self.indice.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(self.linhas[0]))
            w.writeheader()
            w.writerows(self.linhas)

    def rodada(self, nome, f1=1.):
        p = self.modelos / nome
        p.mkdir()
        (p / "melhor_modelo.keras").write_bytes(b"checkpoint sintetico " + nome.encode())
        config = {"backbone": nome, "semente": 42, "epocas_max": 30,
                  "parada": {"monitor": "val_f1_macro", "paciencia": 5},
                  "fine_tuning": {"epocas_max": 20}}
        gravar(p / "config_usada.json", config)
        gravar(p / "ambiente.json", {"sha256": {
            "config": hash_arquivo(p / "config_usada.json"),
            "indice_pipeline": hash_arquivo(self.indice), "pesos_classes": hash_arquivo(self.pesos)}})
        classes = [{"indice": i, "nome": f"classe-{i}", "suporte": 1,
                    "f1": f1, "precisao": f1, "recall": f1} for i in range(13)]
        gravar(p / "metricas_validacao.json", {"esquema": "metricas_validacao_T5_1_v1",
                "backbone": nome, "semente": 42, "pesos_finais": "melhor época",
                "imagens": {"treino": 208, "validacao": 13},
                "validacao": {"por_classe": classes, "f1_macro": f1, "balanced_accuracy": f1}})
        (p / "historico.csv").write_text(f"epoca,val_f1_macro\n1,{f1}\n", encoding="utf-8")
        conv = p / "conversao_t5_6"
        conv.mkdir()
        (conv / "modelo_int8.tflite").write_bytes(b"int8 sintetico")
        (conv / "modelo_fp32.tflite").write_bytes(b"fp32 sintetico")
        gravar(conv / "conversao.json", {"modelo_origem_sha256": hash_arquivo(p / "melhor_modelo.keras"),
                "indice_sha256": hash_arquivo(self.indice), "pesos_sha256": hash_arquivo(self.pesos),
                "int8_sha256": hash_arquivo(conv / "modelo_int8.tflite"),
                "fp32_sha256": hash_arquivo(conv / "modelo_fp32.tflite"),
                "teste_acessado": False, "particao_avaliacao": "validacao"})
        return p

    def test_calibracao_nao_usa_validacao_ou_teste(self):
        amostra = amostra_calibracao(self.linhas)
        self.assertEqual(len(amostra), 200)
        self.assertEqual(len({r["image_id"] for r in amostra}), 200)
        self.assertEqual({r["particao"] for r in amostra}, {"treino"})
        self.assertEqual(len({r["indice_modelo"] for r in amostra}), 13)
        self.assertEqual(amostra, amostra_calibracao(self.linhas))

    def test_comparacao_publicacao_e_vinculo(self):
        pastas = [self.rodada(n, f) for n, f in (("efficientnet_lite0", .8),
                  ("mobilenet_v3_large", .7), ("mobilenet_v2", .6))]
        ranking = comparar(pastas, self.indice, self.pesos)
        self.assertEqual(ranking[0]["arquitetura"], "efficientnet_lite0")
        saida = self.raiz / "pacote"
        m = publicar(pastas[0], pastas[0] / "conversao_t5_6", self.indice, self.pesos,
                     saida, self.modelos, self.raiz / "tabela", "2026-10-26")
        self.assertFalse(m["teste_utilizado_na_selecao"])
        self.assertEqual(m["latencia_celular"]["status"], "pendente")
        self.assertEqual(m["execucao_t5_5"], "efficientnet_lite0")
        self.assertEqual(len(m["comparacao"]), 3)
        for n, h in m["sha256"].items():
            self.assertEqual(hash_arquivo(saida / n), h)
        self.assertEqual(verificar_pacote(saida, self.raiz / "tabela"), m)
        with self.assertRaisesRegex(ValueError, "pacote já existe"):
            publicar(pastas[0], pastas[0] / "conversao_t5_6", self.indice, self.pesos,
                     saida, self.modelos, self.raiz / "tabela", "2026-10-26")
        with self.assertRaisesRegex(ValueError, "vencedor"):
            publicar(pastas[1], pastas[1] / "conversao_t5_6", self.indice, self.pesos,
                     self.raiz / "outro", self.modelos, self.raiz / "tabela", "2026-10-26")
        (saida / "modelo.keras").write_bytes(b"arquivo adulterado")
        with self.assertRaisesRegex(ValueError, "artefato alterado"):
            verificar_pacote(saida, self.raiz / "tabela")

    def test_recusa_evidencias_de_outra_rodada(self):
        p = self.rodada("efficientnet_lite0")
        arquivo = p / "config_usada.json"
        arquivo.write_text(arquivo.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "hash"):
            validar_rodada(p, self.indice, self.pesos)

    def test_recusa_classes_incompativeis(self):
        p = self.rodada("efficientnet_lite0")
        arquivo = p / "metricas_validacao.json"
        m = json.loads(arquivo.read_text())
        m["validacao"]["por_classe"].reverse()
        gravar(arquivo, m)
        with self.assertRaisesRegex(ValueError, "classes"):
            validar_rodada(p, self.indice, self.pesos)

    def test_recusa_rodada_incompleta(self):
        with self.assertRaisesRegex(ValueError, "incompleta"):
            validar_rodada(self.modelos, self.indice, self.pesos)

    def test_recusa_comparacao_com_outro_indice(self):
        p = self.rodada("efficientnet_lite0")
        f = p / "ambiente.json"
        a = json.loads(f.read_text())
        a["sha256"]["indice_pipeline"] = "indice de outra partição"
        gravar(f, a)
        with self.assertRaisesRegex(ValueError, "indice_pipeline"):
            validar_rodada(p, self.indice, self.pesos)

    def test_recusa_orcamentos_diferentes(self):
        pastas = [self.rodada(n) for n in
                  ("efficientnet_lite0", "mobilenet_v3_large", "mobilenet_v2")]
        f = pastas[1] / "config_usada.json"
        c = json.loads(f.read_text())
        c["epocas_max"] = 10
        gravar(f, c)
        a = json.loads((pastas[1] / "ambiente.json").read_text())
        a["sha256"]["config"] = hash_arquivo(f)
        gravar(pastas[1] / "ambiente.json", a)
        with self.assertRaisesRegex(ValueError, "orçamento"):
            comparar(pastas, self.indice, self.pesos)

    def test_recusa_conversao_de_outro_checkpoint(self):
        p = self.rodada("efficientnet_lite0")
        f = p / "conversao_t5_6/conversao.json"
        dados = json.loads(f.read_text())
        dados["modelo_origem_sha256"] = "outro-modelo"
        gravar(f, dados)
        with self.assertRaisesRegex(ValueError, "outro checkpoint"):
            publicar(p, f.parent, self.indice, self.pesos,
                     self.raiz / "pacote", self.modelos, self.raiz / "tabela", "2026-10-26")

    def test_exclui_candidato_acima_do_limite(self):
        a = self.rodada("efficientnet_lite0", .9)
        b = self.rodada("mobilenet_v3_large", .8)
        self.rodada("mobilenet_v2", .7)
        arquivo = a / "conversao_t5_6/modelo_int8.tflite"
        arquivo.write_bytes(b"x" * 8_000_001)
        f = arquivo.parent / "conversao.json"
        evidencia = json.loads(f.read_text())
        evidencia["int8_sha256"] = hash_arquivo(arquivo)
        gravar(f, evidencia)
        manifesto = publicar(b, b / "conversao_t5_6", self.indice, self.pesos,
                             self.raiz / "pacote", self.modelos, self.raiz / "tabela", "2026-10-26")
        self.assertEqual(manifesto["arquitetura"], "mobilenet_v3_large")


if __name__ == "__main__":
    unittest.main()
