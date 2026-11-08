"""Confere a seleção visual e os dados dos gráficos, sem depender das fotos externas."""

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from hashlib import sha256

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import aprofundamento_t8_1 as v


class AprofundamentoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = v.carregar()

    def test_cobre_exatamente_os_sete_acertos_perdidos_oficiais(self):
        ids = {r["image_id"] for r in self.dados["perdidos"]}
        self.assertEqual(ids, {"IMG_00263", "IMG_01540", "IMG_01741", "IMG_01812", "IMG_02004", "IMG_02168", "IMG_02637"})
        self.assertEqual(ids, set(self.dados["anotacoes"]["anotacoes"]))
        for r in self.dados["perdidos"]:
            self.assertEqual(r["indice_real"], r["previsto_keras"])
            self.assertNotEqual(r["indice_real"], r["previsto_convertido"])
            self.assertEqual(r["versao"], "int8_t7_3")

    def test_normalizacao_preserva_suportes_e_recall(self):
        matrizes, linhas = v.matrizes_normalizadas(self.dados)
        self.assertEqual(len(linhas), 6 * 13 * 13)
        for n, m in matrizes.items():
            np.testing.assert_allclose(m.sum(axis=1), 1)
            np.testing.assert_allclose(np.diag(m), [r["recall"] for r in self.dados["metricas"][n]["por_classe"]])
            linhas_n = [r for r in linhas if r["versao"] == n]
            self.assertEqual(sum(r["contagem"] for r in linhas_n), 473)
            for r in linhas_n:
                self.assertAlmostEqual(r["percentual_da_classe_real"], 100 * r["contagem"] / r["suporte_real"])

    def test_recusa_revisao_incompleta_e_caso_fora_da_selecao(self):
        notas = copy.deepcopy(self.dados["anotacoes"]["anotacoes"])
        notas.pop("IMG_00263")
        with self.assertRaisesRegex(ValueError, "exatamente"):
            v.validar_anotacoes(notas, self.dados["perdidos"])
        notas["IMG_99999"] = next(iter(notas.values()))
        with self.assertRaisesRegex(ValueError, "exatamente"):
            v.validar_anotacoes(notas, self.dados["perdidos"])

    def test_recusa_anotacao_sem_observacao(self):
        notas = copy.deepcopy(self.dados["anotacoes"]["anotacoes"])
        notas["IMG_00263"]["observacao_entrada"] = " "
        with self.assertRaisesRegex(ValueError, "incompleta"):
            v.validar_anotacoes(notas, self.dados["perdidos"])

    def test_recusa_hipotese_nao_documentada(self):
        notas = copy.deepcopy(self.dados["anotacoes"]["anotacoes"])
        notas["IMG_00263"]["hipoteses"] = ["causa_confirmada"]
        with self.assertRaises(ValueError):
            v.validar_anotacoes(notas, self.dados["perdidos"])

    def test_resolve_original_e_colecao_por_id_com_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            original = raiz / "dataset/x.jpg"
            exportada = raiz / "classe/IMG_B__y.jpg"
            for p in (original, exportada):
                p.parent.mkdir(parents=True)
                p.write_bytes(p.name.encode())
            dados = {"perdidos": [{"image_id": "IMG_A"}, {"image_id": "IMG_B"}],
                     "indice": {"IMG_A": {"caminho_relativo": "dataset/x.jpg", "sha256_original": sha256(original.read_bytes()).hexdigest()},
                                "IMG_B": {"caminho_relativo": "dataset/y.jpg", "sha256_original": sha256(exportada.read_bytes()).hexdigest()}}}
            caminhos = v.resolver_imagens(raiz, dados)
            self.assertEqual(caminhos, {"IMG_A": original, "IMG_B": exportada})
            exportada.write_bytes(b"alterada")
            with self.assertRaisesRegex(ValueError, "hash divergente"):
                v.resolver_imagens(raiz, dados)

    def test_recusa_fontes_publicadas_alteradas(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            alvo = p / "metricas_gerais.csv"
            alvo.write_text("alterado", encoding="utf-8")
            prov = {"esquema": "avaliacao_pos_conversao_T8_1_v1", "referencia_principal": "keras", "particao": "teste",
                    "artefatos_sha256": {"metricas_gerais.csv": "0" * 64}}
            (p / "proveniencia.json").write_text(v.json.dumps(prov), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash divergente"):
                v.carregar(base=p)

    def test_nao_publica_se_faltam_fotos(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            saida = raiz / "saida"
            with self.assertRaisesRegex(ValueError, "foto ausente"):
                v.executar(raiz, saida=saida)
            self.assertFalse(saida.exists())

    def test_recusa_sobrescrita_antes_de_ler_fotos(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "saída já existe"):
                v.executar(Path("inexistente"), saida=Path(tmp))


if __name__ == "__main__":
    unittest.main()
