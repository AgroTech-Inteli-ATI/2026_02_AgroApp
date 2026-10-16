"""Carregamento dos dados de treino e validação a partir do contrato da T4.5.

Cada imagem é padronizada uma única vez com preparar_imagem, no tamanho do
backbone, e guardada em memória como uint8 (a saída da T4.1 é múltiplo exato de
1/255, então a conversão não perde informação). O augmentation da T4.4 é
aplicado só no treino, a cada época, com rng derivado da semente da imagem
registrada no índice e do número da época. A partição de teste é recusada:
ela fica reservada para a avaliação final.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import csv
import json

import numpy as np

try:
    from keras.utils import PyDataset as _BaseSequencia
except ImportError:  # sem Keras: as funções de leitura continuam utilizáveis
    _BaseSequencia = object

from src.aumento import PARTICAO_TREINO, aplicar_aumento
from src.pipeline_preparacao_t4_5 import _resolver_imagem
from src.preprocessamento import preparar_imagem

RAIZ = Path(__file__).resolve().parents[1]
INDICE_PADRAO = RAIZ / "assets/data/pipeline_T4_5/indice_pipeline.csv"
PESOS_PADRAO = RAIZ / "assets/data/pipeline_T4_5/pesos_classes.json"
PARTICOES_PERMITIDAS = (PARTICAO_TREINO, "validacao")


def carregar_indice(caminho: Path = INDICE_PADRAO) -> list[dict[str, str]]:
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    if not linhas:
        raise ValueError("índice da T4.5 vazio")
    for linha in linhas:
        if not linha["indice_modelo"].isdigit():
            raise ValueError(f"rótulo não inteiro em {linha['image_id']}: {linha['indice_modelo']!r}")
    return linhas


def carregar_class_weight(caminho: Path = PESOS_PADRAO, quantidade_classes: int | None = None) -> dict[int, float]:
    """Converte pesos_classes.json para o formato {índice: peso} do Keras."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    pesos = {int(chave): float(item["peso"]) for chave, item in dados["classes"].items()}
    esperado = quantidade_classes if quantidade_classes is not None else dados["quantidade_classes"]
    if sorted(pesos) != list(range(esperado)):
        raise ValueError(f"pesos devem cobrir exatamente as classes 0 a {esperado - 1}")
    if any(peso <= 0 for peso in pesos.values()):
        raise ValueError("há peso de classe não positivo")
    return pesos


def nomes_classes(indice: list[dict[str, str]]) -> list[str]:
    nomes = {int(linha["indice_modelo"]): linha["nome_classe_modelo"] for linha in indice}
    if sorted(nomes) != list(range(len(nomes))):
        raise ValueError("índices das classes não são consecutivos a partir de 0")
    return [nomes[i] for i in range(len(nomes))]


def _conferir_particao(particao: str) -> None:
    if particao not in PARTICOES_PERMITIDAS:
        raise ValueError(
            f"a partição '{particao}' não pode ser carregada no treinamento; "
            "o teste fica reservado para a avaliação final"
        )


def preparar_particao(
    indice: list[dict[str, str]], particao: str, raiz_imagens: Path, tamanho: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Retorna imagens uint8 (n, t, t, 3), rótulos int64 e sementes de augmentation."""
    _conferir_particao(particao)
    linhas = [linha for linha in indice if linha["particao"] == particao]
    if not linhas:
        raise ValueError(f"nenhuma imagem na partição '{particao}'")
    imagens = np.empty((len(linhas), tamanho, tamanho, 3), dtype=np.uint8)
    rotulos = np.array([int(linha["indice_modelo"]) for linha in linhas], dtype=np.int64)
    sementes = np.array(
        [int(linha["semente_augmentation"]) if linha["semente_augmentation"] else 0 for linha in linhas],
        dtype=np.uint64,
    )
    falhas = []
    for posicao, linha in enumerate(linhas):
        caminho = _resolver_imagem(Path(raiz_imagens), linha["caminho_relativo"])
        try:
            if sha256(caminho.read_bytes()).hexdigest() != linha["sha256_original"]:
                raise ValueError("hash do arquivo original diverge do índice")
            entrada = preparar_imagem(caminho, tamanho)
        except (OSError, ValueError) as erro:
            falhas.append(f"{linha['image_id']} ({linha['caminho_relativo']}): {erro}")
            continue
        imagens[posicao] = np.round(entrada * 255.0).astype(np.uint8)
    if falhas:
        raise RuntimeError(f"{len(falhas)} imagens de {particao} não carregadas; exemplos: {'; '.join(falhas[:3])}")
    return imagens, rotulos, sementes


class SequenciaImagens(_BaseSequencia):
    """Lotes de (imagens float32 em [0, 1], rótulos) para o Keras.

    No treino, a ordem é embaralhada a cada época com default_rng([semente, época]) e,
    se `aumentar`, cada imagem recebe aplicar_aumento com
    default_rng([semente_augmentation, época]). Na validação a ordem é fixa e não há
    augmentation.
    """

    def __init__(
        self,
        imagens: np.ndarray,
        rotulos: np.ndarray,
        particao: str,
        batch: int,
        semente: int = 0,
        sementes_augmentation: np.ndarray | None = None,
        aumentar: bool = False,
    ):
        super().__init__()
        _conferir_particao(particao)
        if aumentar and particao != PARTICAO_TREINO:
            raise ValueError("augmentation só é permitido na partição de treino")
        if aumentar and sementes_augmentation is None:
            raise ValueError("augmentation exige as sementes por imagem da T4.5")
        self.imagens = imagens
        self.rotulos = rotulos
        self.particao = particao
        self.batch = batch
        self.semente = semente
        self.sementes_augmentation = sementes_augmentation
        self.aumentar = aumentar
        self.epoca = 0
        self._ordenar()

    def _ordenar(self) -> None:
        if self.particao == PARTICAO_TREINO:
            self.ordem = np.random.default_rng([self.semente, self.epoca]).permutation(len(self.rotulos))
        else:
            self.ordem = np.arange(len(self.rotulos))

    def __len__(self) -> int:
        return int(np.ceil(len(self.rotulos) / self.batch))

    def amostra(self, posicao: int) -> np.ndarray:
        imagem = self.imagens[posicao].astype(np.float32) / 255.0
        if self.aumentar:
            rng = np.random.default_rng([int(self.sementes_augmentation[posicao]), self.epoca])
            imagem = aplicar_aumento(imagem, self.particao, rng)
        return imagem

    def __getitem__(self, lote: int) -> tuple[np.ndarray, np.ndarray]:
        posicoes = self.ordem[lote * self.batch:(lote + 1) * self.batch]
        return np.stack([self.amostra(p) for p in posicoes]), self.rotulos[posicoes]

    def definir_epoca(self, epoca: int) -> None:
        """Chamado no início de cada época pelo treinamento (callback SincronizarEpoca)."""
        self.epoca = epoca
        self._ordenar()

    def on_epoch_end(self) -> None:
        # A época é definida explicitamente em definir_epoca, não por contagem de chamadas.
        pass
