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

from preprocessamento import COR_PREENCHIMENTO

PARTICAO_TREINO = "treino"
PROBABILIDADE = 0.5


def _mascara_preenchimento(imagem: np.ndarray) -> np.ndarray:
    """Identifica as faixas inteiras de preenchimento criadas pela T4.1."""
    cor = np.asarray(COR_PREENCHIMENTO, dtype=np.float32) / 255.0
    pixels_neutros = np.all(np.isclose(imagem, cor, atol=1e-7), axis=2)
    linhas = np.all(pixels_neutros, axis=1)
    colunas = np.all(pixels_neutros, axis=0)
    return linhas[:, None] | colunas[None, :]


def aplicar_aumento(imagem: np.ndarray, particao: str, rng: np.random.Generator) -> np.ndarray:
    """Retorna uma variação de `imagem` (saída de preparar_imagem), float32 em [0, 1].

    Cada transformação é sorteada de forma independente com probabilidade PROBABILIDADE.
    """
    if particao != PARTICAO_TREINO:
        raise ValueError(f"aumento só é permitido no treino, não na partição '{particao}'")

    saida = np.array(imagem, dtype=np.float32)
    mascara_preenchimento = _mascara_preenchimento(saida)
    conteudo = ~mascara_preenchimento

    if rng.random() < PROBABILIDADE and np.any(conteudo):  # sol forte ou sombra
        pixels = saida[conteudo]
        media = pixels.mean()
        saida[conteudo] = (pixels - media) * rng.uniform(0.8, 1.2) + media
        saida[conteudo] = saida[conteudo] * rng.uniform(0.75, 1.25)

    if rng.random() < PROBABILIDADE and np.any(conteudo):  # balanço de branco diferente entre celulares
        ganhos = rng.uniform(0.95, 1.05, size=3).astype(np.float32)
        saida[conteudo] = saida[conteudo] * ganhos

    if rng.random() < PROBABILIDADE:  # ângulo de captura: rotação de 90° e espelhamento
        giros = int(rng.integers(4))
        saida = np.rot90(saida, k=giros)
        mascara_preenchimento = np.rot90(mascara_preenchimento, k=giros)
        if rng.random() < 0.5:
            saida = saida[:, ::-1]
            mascara_preenchimento = mascara_preenchimento[:, ::-1]
        saida = np.ascontiguousarray(saida)
        mascara_preenchimento = np.ascontiguousarray(mascara_preenchimento)
        conteudo = ~mascara_preenchimento

    if rng.random() < PROBABILIDADE and np.any(conteudo):  # foto tremida ou levemente fora de foco
        linhas, colunas = np.where(conteudo)
        y0, y1 = linhas.min(), linhas.max() + 1
        x0, x1 = colunas.min(), colunas.max() + 1
        recorte = saida[y0:y1, x0:x1]
        u8 = np.clip(recorte * 255.0 + 0.5, 0, 255).astype(np.uint8)
        borrada = Image.fromarray(u8).filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 1.5)))
        saida[y0:y1, x0:x1] = np.asarray(borrada, dtype=np.float32) / 255.0

    if rng.random() < PROBABILIDADE and np.any(conteudo):  # ruído do sensor do celular
        desvio = rng.uniform(0.005, 0.03)
        ruido = rng.normal(0.0, desvio, size=saida[conteudo].shape).astype(np.float32)
        saida[conteudo] = saida[conteudo] + ruido

    saida = np.clip(saida, 0.0, 1.0).astype(np.float32)
    cor = np.asarray(COR_PREENCHIMENTO, dtype=np.float32) / 255.0
    saida[mascara_preenchimento] = cor
    return saida
