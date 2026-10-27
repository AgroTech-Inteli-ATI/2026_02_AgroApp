"""Regressões da T6.3 sem depender das imagens ou dos metadados externos."""

import csv
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import analise_erros_t6_3 as analise


class AnaliseTest(unittest.TestCase):
    def setUp(self):
        self.pares = analise.ler_pares()
        self.erros = analise.ler_erros()

    def gerar(self, field=None):
        return list(csv.DictReader(io.StringIO(
            analise.gerar_revisao_visual(self.pares, self.erros, field or {}))))

    def test_preserva_ambos_os_pares_da_mesma_foto(self):
        linhas = self.gerar()
        self.assertEqual(len(linhas), 49)
        self.assertEqual(len({r["image_id"] for r in linhas}), 48)
        self.assertEqual(len({(r["image_id"], r["classe_prevista"]) for r in linhas}), 49)
        foto = [r for r in linhas if r["image_id"] == "IMG_03008"]
        self.assertEqual({r["classe_prevista"] for r in foto}, {
            "Lagarta-do-cartucho (Spodoptera frugiperda)",
            "Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)"})

    def test_reproduz_independente_da_ordem_e_da_semente_python(self):
        esperado = analise.gerar_revisao_visual(self.pares, self.erros, {})
        self.assertEqual(esperado, analise.gerar_revisao_visual(
            list(reversed(self.pares)), list(reversed(self.erros)), {}))
        codigo = ("from src.analise_erros_t6_3 import gerar_revisao_visual,ler_pares,ler_erros; "
                  "print(gerar_revisao_visual(ler_pares(),ler_erros(),{}),end='')")
        for semente in ("1", "2", "3"):
            resultado = subprocess.check_output([sys.executable, "-c", codigo], cwd=RAIZ,
                env={**os.environ, "PYTHONHASHSEED": semente, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(resultado.decode(), esperado)

    def test_observacoes_diferentes_vem_do_metadado(self):
        por_id = {r["image_id"]: r for r in self.erros}
        field = {por_id[i]["caminho_relativo"]: {"inat_obs_id": obs, "life_stage": ""}
                 for i, obs in (("IMG_02978", "10704962"), ("IMG_03037", "396445719"))}
        linhas = {r["image_id"]: r for r in self.gerar(field)}
        self.assertEqual(linhas["IMG_02978"]["inat_obs_id"], "10704962")
        self.assertEqual(linhas["IMG_03037"]["inat_obs_id"], "396445719")
        self.assertEqual(linhas["IMG_02978"]["life_stage_metadado"], "")
        self.assertNotEqual(linhas["IMG_02978"]["inat_obs_id"], linhas["IMG_03037"]["inat_obs_id"])

    def test_adulto_nao_e_classificado_como_erro_taxonomico(self):
        linhas = self.gerar()
        adultos = [r for r in linhas if "variacao_estagio_de_vida" in r["causas_identificadas"]]
        self.assertEqual(len({r["image_id"] for r in adultos}), 19)
        self.assertTrue(all("rotulo_inconsistente" not in r["causas_identificadas"] for r in adultos))
        self.assertTrue(all(r["status_causa"] == "indeterminada" for r in adultos))

    def test_qualidade_e_multiplos_insetos_nao_forcam_semelhanca(self):
        linhas = self.gerar()
        qualidade = {"IMG_01069", "IMG_01070", "IMG_01071", "IMG_01894", "IMG_02030"}
        fotos = [r for r in linhas if r["image_id"] in qualidade]
        self.assertEqual(len(fotos), 5)
        self.assertTrue(all(r["causas_identificadas"] == "qualidade_imagem" for r in fotos))
        multiplos = [r for r in linhas if r["image_id"] in {"IMG_01175", "IMG_01176"}]
        self.assertEqual(len(multiplos), 2)
        self.assertTrue(all(r["status_causa"] == "indeterminada" for r in multiplos))
        self.assertTrue(all("conteudo_multiplos_insetos" in r["causas_identificadas"] for r in multiplos))

    def test_recusa_cobertura_incompleta_e_categoria_desconhecida(self):
        dados = dict(analise.REVISAO_VISUAL)
        dados.pop("IMG_03008")
        with patch.dict(analise.REVISAO_VISUAL, dados, clear=True):
            with self.assertRaisesRegex(ValueError, "cobre exatamente"):
                self.gerar()
        with patch.dict(analise.REVISAO_VISUAL, {"IMG_03008": ("inexistente", "observação")}):
            with self.assertRaisesRegex(ValueError, "inválidas"):
                self.gerar()


if __name__ == "__main__":
    unittest.main()
