"""Política de confiança (T6.5) com probabilidades sintéticas; sem TensorFlow.

Seis imagens e quatro classes, com os resultados calculados à mão:

    imagem  probabilidades             real  ordem decrescente  confiança top-1
    A       .50 .30 .15 .05            0     0 1 2 3           .50  (top-1 certo)
    B       .40 .40 .10 .10            1     0 1 2 3 (empate)  .40  (top-1 errado, top-2 certo)
    C       .10 .20 .30 .40            2     3 2 1 0           .40  (top-1 errado, top-2 certo)
    D       .90 .05 .03 .02            0     0 1 2 3           .90  (top-1 certo)
    E       .25 .25 .25 .25            3     0 1 2 3 (empate)  .25  (top-1 errado, certo só no top-4)
    F       .05 .15 .20 .60            3     3 2 1 0           .60  (top-1 certo)
"""

import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

from hashlib import sha256

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import politica_confianca_t6_5 as politica
from src import probabilidades_validacao_t6_5 as geracao

PROBABILIDADES = np.array([
    [0.50, 0.30, 0.15, 0.05],
    [0.40, 0.40, 0.10, 0.10],
    [0.10, 0.20, 0.30, 0.40],
    [0.90, 0.05, 0.03, 0.02],
    [0.25, 0.25, 0.25, 0.25],
    [0.05, 0.15, 0.20, 0.60],
])
ROTULOS = np.array([0, 1, 2, 0, 3, 3])
IDS = ["V1", "V2", "V3", "V4", "V5", "V6"]
NOMES = ["Classe A", "Classe B", "Classe C", "Classe D"]
# A linha de comando calcula o top-5; as duas classes extras têm probabilidade 0 (ficam por último)
PROBABILIDADES_6 = np.hstack([PROBABILIDADES, np.zeros((6, 2))])
NOMES_6 = NOMES + ["Classe E", "Classe F"]
PARAMETROS = Path(__file__).resolve().parents[1] / "assets/data/politica_T6_5/parametros.json"


class OrdemTopKTest(unittest.TestCase):
    def test_ordem_e_desempate_pelo_menor_indice(self):
        esperado = [[0, 1, 2, 3], [0, 1, 2, 3], [3, 2, 1, 0], [0, 1, 2, 3], [0, 1, 2, 3], [3, 2, 1, 0]]
        self.assertEqual(politica.ordem_topk(PROBABILIDADES, 4).tolist(), esperado)
        self.assertEqual(politica.ordem_topk(PROBABILIDADES, 2).tolist(), [r[:2] for r in esperado])

    def test_k_invalido(self):
        for k in (0, 5):
            with self.assertRaises(ValueError):
                politica.ordem_topk(PROBABILIDADES, k)

    def test_acerto_topk_sem_limiar(self):
        # top-1: A, D, F; top-2: todas menos E; top-3 igual; top-4: todas
        self.assertEqual(politica.acerto_topk(PROBABILIDADES, ROTULOS, 1).tolist(), [1, 0, 0, 1, 0, 1])
        self.assertEqual(politica.acerto_topk(PROBABILIDADES, ROTULOS, 2).tolist(), [1, 1, 1, 1, 0, 1])
        self.assertEqual(politica.acerto_topk(PROBABILIDADES, ROTULOS, 3).tolist(), [1, 1, 1, 1, 0, 1])
        self.assertEqual(politica.acerto_topk(PROBABILIDADES, ROTULOS, 4).tolist(), [1] * 6)


class CurvaTest(unittest.TestCase):
    def setUp(self):
        linhas = politica.curva(PROBABILIDADES, ROTULOS, (0.25, 0.4, 0.5, 0.6, 0.95), ks=(1, 2, 3))
        self.por_limiar = {linha["limiar"]: linha for linha in linhas}

    def test_fronteira_igual_ao_limiar_e_aceita(self):
        # E tem top-1 exatamente 0,25; B e C têm exatamente 0,40; A tem exatamente 0,50
        self.assertEqual(self.por_limiar[0.25]["aceitas"], 6)
        self.assertEqual(self.por_limiar[0.4]["aceitas"], 5)
        self.assertEqual(self.por_limiar[0.5]["aceitas"], 3)
        # 0,599999 fica abaixo de 0,60 e 0,600000 é aceito
        valores = np.array([[0.599999, 0.400001], [0.6, 0.4]])
        linha = politica.curva(valores, np.array([0, 0]), (0.6,), ks=(1,))[0]
        self.assertEqual(linha["aceitas"], 1)
        self.assertAlmostEqual(linha["cobertura"], 0.5)

    def test_contagens_de_cobertura(self):
        self.assertAlmostEqual(self.por_limiar[0.25]["cobertura"], 6 / 6)
        self.assertAlmostEqual(self.por_limiar[0.4]["cobertura"], 5 / 6)
        self.assertAlmostEqual(self.por_limiar[0.5]["cobertura"], 3 / 6)
        self.assertAlmostEqual(self.por_limiar[0.6]["cobertura"], 2 / 6)
        self.assertAlmostEqual(self.por_limiar[0.5]["inconclusivos"], 3 / 6)
        self.assertEqual(self.por_limiar[0.95]["aceitas"], 0)
        self.assertEqual(self.por_limiar[0.95]["cobertura"], 0.0)

    def test_acerto_entre_aceitas(self):
        self.assertAlmostEqual(self.por_limiar[0.25]["acerto_top1_aceitas"], 3 / 6)
        self.assertAlmostEqual(self.por_limiar[0.25]["acerto_top2_aceitas"], 5 / 6)
        self.assertAlmostEqual(self.por_limiar[0.25]["acerto_top3_aceitas"], 5 / 6)
        self.assertAlmostEqual(self.por_limiar[0.4]["acerto_top1_aceitas"], 3 / 5)
        self.assertAlmostEqual(self.por_limiar[0.4]["acerto_top2_aceitas"], 5 / 5)
        self.assertAlmostEqual(self.por_limiar[0.5]["acerto_top1_aceitas"], 3 / 3)
        self.assertAlmostEqual(self.por_limiar[0.6]["acerto_top1_aceitas"], 2 / 2)

    def test_sem_aceitas_o_acerto_e_indefinido_e_nao_zero(self):
        self.assertIsNone(self.por_limiar[0.95]["acerto_top1_aceitas"])
        self.assertIsNone(self.por_limiar[0.95]["acerto_top3_aceitas"])

    def test_grade_padrao(self):
        self.assertEqual(len(politica.LIMIARES), 14)
        self.assertEqual(politica.LIMIARES[0], 0.30)
        self.assertEqual(politica.LIMIARES[-1], 0.95)
        passos = np.diff(politica.LIMIARES)
        self.assertTrue(np.allclose(passos, 0.05))
        self.assertEqual(politica.KS, (1, 2, 3, 5))

    def test_sugestao_do_menor_limiar_que_atinge_a_meta(self):
        linhas = politica.curva(PROBABILIDADES, ROTULOS, (0.25, 0.4, 0.5, 0.6, 0.95), ks=(1,))
        self.assertEqual(politica.sugerir_limiar(linhas, 0.9), 0.5)
        self.assertEqual(politica.sugerir_limiar(linhas, 1.0), 0.5)
        self.assertEqual(politica.sugerir_limiar(linhas, 0.6), 0.4)  # 3/5 = 0,6 atinge a meta
        self.assertEqual(politica.sugerir_limiar(linhas, 0.5), 0.25)
        self.assertIsNone(politica.sugerir_limiar(linhas[:2], 0.9))

    def test_cobertura_por_classe(self):
        por_classe = politica.cobertura_por_classe(PROBABILIDADES, ROTULOS, 0.5, NOMES)
        esperado = {
            # indice: (suporte, aceitas, acertos nas aceitas, recall no limiar, recall sem limiar)
            0: (2, 2, 2, 1.0, 1.0),   # A e D
            1: (1, 0, 0, 0.0, 0.0),   # B: 0,40 < 0,50 e o argmax é a classe 0
            2: (1, 0, 0, 0.0, 0.0),   # C: 0,40 < 0,50 e o argmax é a classe 3
            3: (2, 1, 1, 0.5, 0.5),   # F aceita e certa; E inconclusiva e errada
        }
        for linha in por_classe:
            suporte, aceitas, certas, recall, recall_puro = esperado[linha["indice"]]
            self.assertEqual(
                (linha["suporte"], linha["aceitas"], linha["acertos_aceitas"]), (suporte, aceitas, certas)
            )
            self.assertAlmostEqual(linha["cobertura"], aceitas / suporte)
            self.assertAlmostEqual(linha["recall_no_limiar"], recall)
            self.assertAlmostEqual(linha["recall_sem_limiar"], recall_puro)
            self.assertEqual(linha["classe"], NOMES[linha["indice"]])


class EntradaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.indice = self.raiz / "indice.csv"
        with self.indice.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, lineterminator="\n")
            escritor.writerow(["image_id", "particao", "indice_modelo"])
            escritor.writerows((i, "validacao", int(r)) for i, r in zip(IDS, ROTULOS))
            escritor.writerows([("T1", "teste", 0), ("T2", "teste", 1), ("R1", "treino", 2)])
        self.classes = self.raiz / "classes.csv"
        self.classes.write_text(
            "indice_modelo;classe\n" + "".join(f"{i};{n}\n" for i, n in enumerate(NOMES_6)),
            encoding="utf-8-sig",
        )

    def _csv(self, nome="prob.csv", ids=IDS, rotulos=ROTULOS, matriz=PROBABILIDADES, cabecalho=None, bom=False):
        caminho = self.raiz / nome
        n = matriz.shape[1]
        with caminho.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, lineterminator="\n")
            escritor.writerow(cabecalho or ["image_id", "indice_real"] + [f"p_{i}" for i in range(n)])
            for i, r, linha in zip(ids, rotulos, matriz):
                escritor.writerow([i, int(r)] + [f"{v:.6f}" for v in linha])
        return caminho

    def _ler(self, caminho, classes=4):
        return politica.ler_probabilidades(caminho, politica.ler_indice(self.indice), classes)

    def test_entrada_valida(self):
        ids, rotulos, matriz = self._ler(self._csv())
        self.assertEqual(ids, IDS)
        self.assertEqual(rotulos.tolist(), ROTULOS.tolist())
        self.assertTrue(np.allclose(matriz, PROBABILIDADES))

    def test_recusa_particao_que_nao_e_validacao(self):
        caminho = self._csv(ids=["V1", "V2", "V3", "V4", "V5", "T1"])
        with self.assertRaisesRegex(ValueError, "não são da validação"):
            self._ler(caminho)
        caminho = self._csv(ids=["T1", "T2", "R1", "V4", "V5", "V6"], rotulos=[0, 1, 2, 0, 3, 3])
        with self.assertRaisesRegex(ValueError, "não são da validação"):
            self._ler(caminho)

    def test_recusa_validacao_incompleta_ou_id_desconhecido(self):
        with self.assertRaisesRegex(ValueError, "cobrem 5 imagens"):
            self._ler(self._csv(ids=IDS[:5], rotulos=ROTULOS[:5], matriz=PROBABILIDADES[:5]))
        with self.assertRaisesRegex(ValueError, "ausentes do índice"):
            self._ler(self._csv(ids=IDS[:5] + ["X9"]))

    def test_recusa_soma_invalida_nan_e_valores_fora_de_faixa(self):
        ruim = PROBABILIDADES.copy()
        ruim[0, 0] = 0.51  # soma 1,01
        with self.assertRaisesRegex(ValueError, "não somam 1"):
            self._ler(self._csv(matriz=ruim))
        com_nan = PROBABILIDADES.copy()
        com_nan[2, 1] = np.nan
        caminho = self._csv(matriz=com_nan)
        with self.assertRaisesRegex(ValueError, "não numérico|não finita"):
            self._ler(caminho)
        with self.assertRaises(ValueError):
            politica.validar_matriz(np.array([[np.inf, 0.0], [0.5, 0.5]]), 2)
        with self.assertRaisesRegex(ValueError, "fora de"):
            politica.validar_matriz(np.array([[1.5, -0.5], [0.5, 0.5]]), 2)

    def test_recusa_numero_de_classes_cabecalho_bom_e_rotulo(self):
        cinco = np.hstack([PROBABILIDADES, np.zeros((6, 1))])
        with self.assertRaisesRegex(ValueError, "cabeçalho inesperado"):
            self._ler(self._csv(matriz=cinco))
        with self.assertRaisesRegex(ValueError, "cabeçalho inesperado"):
            self._ler(self._csv("bom.csv", bom=True))
        with self.assertRaisesRegex(ValueError, "diverge do rótulo"):
            self._ler(self._csv(rotulos=[1, 1, 2, 0, 3, 3]))
        with self.assertRaisesRegex(ValueError, "duplicado"):
            self._ler(self._csv(ids=["V1", "V1", "V3", "V4", "V5", "V6"]))

    def test_execucao_grava_curva_e_cobertura_por_classe(self):
        saida = self.raiz / "saida"
        argumentos = [
            "--probabilidades", str(self._csv(matriz=PROBABILIDADES_6)), "--indice", str(self.indice),
            "--classes", str(self.classes), "--saida", str(saida),
            "--limiar", "0.5", "--meta-acerto", "0.9",
        ]
        texto = io.StringIO()
        with contextlib.redirect_stdout(texto):
            politica.main(argumentos)
        curva = (saida / "curva_limiar_validacao.csv").read_bytes()
        self.assertFalse(curva.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", curva)
        linhas = list(csv.reader(curva.decode("utf-8").splitlines()))
        self.assertEqual(linhas[0], politica.COLUNAS_CURVA)
        self.assertEqual(len(linhas) - 1, 14)
        # a 0,45 só A, D e F passam (top-1 de B e C é 0,40) e as três estão certas
        self.assertEqual(linhas[4][:3], ["0.450000", "0.500000", "3"])
        self.assertEqual(linhas[1][4], "0.600000")  # 0,30: A, B, C, D e F aceitas, 3 certas
        self.assertIn("Limiar sugerido (menor da grade com acerto top-1 >= 0.90): 0.45", texto.getvalue())
        por_classe = list(csv.reader((saida / "cobertura_por_classe_validacao.csv").read_text(encoding="utf-8").splitlines()))
        self.assertEqual(por_classe[0], politica.COLUNAS_CLASSE)
        self.assertEqual(por_classe[4][:5], ["3", "Classe D", "2", "1", "0.500000"])

    def test_sem_limiar_nao_grava_cobertura_por_classe(self):
        saida = self.raiz / "saida"
        texto = io.StringIO()
        with contextlib.redirect_stdout(texto):
            politica.main([
                "--probabilidades", str(self._csv(matriz=PROBABILIDADES_6)), "--indice", str(self.indice),
                "--classes", str(self.classes), "--saida", str(saida), "--meta-acerto", "0.99",
            ])
        self.assertTrue((saida / "curva_limiar_validacao.csv").exists())
        self.assertFalse((saida / "cobertura_por_classe_validacao.csv").exists())
        self.assertIn("Limiar sugerido (menor da grade com acerto top-1 >= 0.99): 0.45", texto.getvalue())


class ModeloFalso:
    """Substitui o Keras: saída softmax fixa; registra o tamanho das imagens recebidas."""

    def __init__(self, tamanho=24, classes=4):
        self.input_shape = (None, tamanho, tamanho, 3)
        self.output_shape = (None, classes)
        self.tamanhos = set()

    def predict_on_batch(self, imagens):
        assert imagens.dtype == np.float32 and 0 <= imagens.min() <= imagens.max() <= 1
        self.tamanhos.add(imagens.shape[1])
        saida = np.tile([0.55, 0.25, 0.15, 0.05], (len(imagens), 1))
        return saida


class GeradorProbabilidadesTest(unittest.TestCase):
    """src.probabilidades_validacao_t6_5 com modelo falso; o número de linhas vem do índice."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        (self.raiz / "imgs").mkdir()
        colunas = [
            "image_id", "caminho_relativo", "sha256_original", "indice_modelo",
            "nome_classe_modelo", "particao", "semente_augmentation",
        ]
        linhas = []
        for numero in range(5):  # 5 de validação, com arquivos reais
            caminho = self.raiz / "imgs" / f"v{numero}.png"
            Image.fromarray(np.random.default_rng(numero).integers(0, 255, (20, 30, 3), dtype=np.uint8)).save(caminho)
            linhas.append([f"V{numero}", f"imgs/v{numero}.png", sha256(caminho.read_bytes()).hexdigest(),
                           numero % 4, NOMES[numero % 4], "validacao", ""])
        # teste e treino apontam para arquivos inexistentes: se fossem abertos, o gerador falharia
        linhas += [["T0", "imgs/inexistente_t.png", "0" * 64, 0, NOMES[0], "teste", ""],
                   ["R0", "imgs/inexistente_r.png", "0" * 64, 1, NOMES[1], "treino", "7"]]
        # garante as 4 classes no índice
        linhas += [["R1", "imgs/inexistente_r1.png", "0" * 64, 2, NOMES[2], "treino", "7"],
                   ["R2", "imgs/inexistente_r2.png", "0" * 64, 3, NOMES[3], "treino", "7"]]
        self.indice = self.raiz / "indice.csv"
        with self.indice.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, lineterminator="\n")
            escritor.writerow(colunas)
            escritor.writerows(linhas)
        self.classes = self.raiz / "classes.csv"
        self.classes.write_text(
            "indice_modelo;classe\n" + "".join(f"{i};{n}\n" for i, n in enumerate(NOMES)), encoding="utf-8-sig"
        )
        self.modelo = self.raiz / "melhor_modelo.keras"
        self.modelo.write_bytes(b"modelo sintetico")

    def _gerar(self, modelo=None, saida="saida/p.csv", **extra):
        modelo = modelo or ModeloFalso()
        argumentos = dict(classes=self.classes, carregador=lambda caminho: modelo)
        argumentos.update(extra)
        return geracao.gerar(self.modelo, argumentos.pop("indice", self.indice), self.raiz, self.raiz / saida, **argumentos), modelo

    def test_numero_de_linhas_vem_do_indice_e_o_tamanho_vem_do_modelo(self):
        resumo, modelo = self._gerar(ModeloFalso(tamanho=24))
        self.assertEqual((resumo["linhas"], resumo["classes"], resumo["tamanho_entrada"]), (5, 4, 24))
        self.assertEqual(modelo.tamanhos, {24})
        bruto = (self.raiz / "saida/p.csv").read_bytes()
        self.assertFalse(bruto.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", bruto)
        linhas = list(csv.reader(bruto.decode("utf-8").splitlines()))
        self.assertEqual(linhas[0], ["image_id", "indice_real", "p_0", "p_1", "p_2", "p_3"])
        self.assertEqual([l[0] for l in linhas[1:]], ["V0", "V1", "V2", "V3", "V4"])
        self.assertEqual([l[1] for l in linhas[1:]], ["0", "1", "2", "3", "0"])
        self.assertEqual(linhas[1][2:], ["0.550000", "0.250000", "0.150000", "0.050000"])
        self.assertRegex(resumo["modelo_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(resumo["indice_sha256"], r"^[0-9a-f]{64}$")

    def test_saida_e_aceita_pela_politica_para_o_mesmo_indice(self):
        self._gerar()
        ids, rotulos, matriz = politica.ler_probabilidades(
            self.raiz / "saida/p.csv", politica.ler_indice(self.indice), 4
        )
        self.assertEqual((len(ids), matriz.shape), (5, (5, 4)))

    def test_recusas(self):
        self._gerar()
        with self.assertRaisesRegex(ValueError, "já existe"):
            self._gerar()
        with self.assertRaisesRegex(ValueError, "saída do modelo incompatível"):
            self._gerar(ModeloFalso(classes=5), saida="saida/outro.csv")
        with self.assertRaisesRegex(ValueError, "quadrada"):
            modelo = ModeloFalso()
            modelo.input_shape = (None, 24, 30, 3)
            self._gerar(modelo, saida="saida/outro2.csv")
        outras = self.raiz / "classes_trocadas.csv"
        outras.write_text("indice_modelo;classe\n" + "".join(f"{i};{n}\n" for i, n in enumerate(reversed(NOMES))))
        with self.assertRaisesRegex(ValueError, "divergem da ordem"):
            self._gerar(saida="saida/outro3.csv", classes=outras)
        sem_validacao = self.raiz / "sem_validacao.csv"
        sem_validacao.write_text(
            "\n".join(l for l in self.indice.read_text(encoding="utf-8").splitlines() if ",validacao," not in l) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "não tem imagens de validação"):
            self._gerar(saida="saida/outro4.csv", indice=sem_validacao)


class ParametrosTest(unittest.TestCase):
    @unittest.skipUnless(PARAMETROS.exists(), "parametros.json ainda não foi criado")
    def test_esquema_do_parametros_json(self):
        bruto = PARAMETROS.read_bytes()
        self.assertFalse(bruto.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", bruto)
        dados = json.loads(bruto.decode("utf-8"))
        self.assertIsInstance(dados["numero_hipoteses"], int)
        self.assertTrue(1 <= dados["numero_hipoteses"] <= 13)
        self.assertTrue(0 < dados["limiar_confianca"] < 1)
        self.assertEqual(dados["regra_limiar"], "top1_maior_ou_igual")
        abaixo = dados["abaixo_do_limiar"]
        self.assertIs(abaixo["indica_classe"], False)
        self.assertTrue(abaixo["mensagem"].strip())
        self.assertTrue(abaixo["orientacao_nova_foto"].strip())
        self.assertIs(abaixo["conteudos_relacionados_quando_catalogo"], True)
        for texto in (abaixo["mensagem"], abaixo["orientacao_nova_foto"]):
            self.assertNotIn("não é uma praga", texto.lower())
        base = dados["base"]
        self.assertEqual(base["particao"], "validacao")
        self.assertIsInstance(base["n_imagens"], int)
        self.assertTrue(base["modelo"])
        self.assertRegex(base["modelo_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(base["origem_inferencia"], "Keras FP32")
        self.assertTrue(base["curva"])


if __name__ == "__main__":
    unittest.main()
