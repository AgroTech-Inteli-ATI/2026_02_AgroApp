"""Aumento de dados para o treinamento (T4.4).

As transformações simulam variações de captura em campo: luz forte e sombra,
balanço de branco do celular, ângulo da folha, tremor e ruído do sensor. Não
há recorte, para não remover lesões nas bordas (mesma decisão da T4.1).

Aplicar aumento a validação ou teste inflaria as métricas, por isso a função
recusa qualquer partição que não seja de treino.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

PARTICAO_TREINO = "treino"
PROBABILIDADE = 0.5


def aplicar_aumento(imagem: np.ndarray, particao: str, rng: np.random.Generator) -> np.ndarray:
    """Retorna uma variação de `imagem` (saída de preparar_imagem), float32 em [0, 1].

    Cada transformação é sorteada de forma independente com probabilidade PROBABILIDADE.
    """
    if particao != PARTICAO_TREINO:
        raise ValueError(f"aumento só é permitido no treino, não na partição '{particao}'")

    saida = np.array(imagem, dtype=np.float32)

    if rng.random() < PROBABILIDADE:  # sol forte ou sombra
        media = saida.mean()
        saida = (saida - media) * rng.uniform(0.8, 1.2) + media
        saida = saida * rng.uniform(0.75, 1.25)

    if rng.random() < PROBABILIDADE:  # balanço de branco diferente entre celulares
        saida = saida * rng.uniform(0.95, 1.05, size=3).astype(np.float32)

    if rng.random() < PROBABILIDADE:  # ângulo de captura: rotação de 90° e espelhamento
        saida = np.rot90(saida, k=int(rng.integers(4)))
        if rng.random() < 0.5:
            saida = saida[:, ::-1]
        saida = np.ascontiguousarray(saida)

    if rng.random() < PROBABILIDADE:  # foto tremida ou levemente fora de foco
        u8 = np.clip(saida * 255.0 + 0.5, 0, 255).astype(np.uint8)
        borrada = Image.fromarray(u8).filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 1.5)))
        saida = np.asarray(borrada, dtype=np.float32) / 255.0

    if rng.random() < PROBABILIDADE:  # ruído do sensor do celular
        saida = saida + rng.normal(0.0, rng.uniform(0.005, 0.03), size=saida.shape).astype(np.float32)

    return np.clip(saida, 0.0, 1.0).astype(np.float32)
