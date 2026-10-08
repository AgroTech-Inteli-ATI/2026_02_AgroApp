"""Padronização das imagens para a entrada do modelo (T4.1).

O mesmo processamento deve ser usado no treino e na inferência. Por isso a
função fica aqui, e não no notebook.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

TAMANHO_ENTRADA = 224
COR_PREENCHIMENTO = (128, 128, 128)


def preparar_imagem(
    origem: Path | str | Image.Image, tamanho: int = TAMANHO_ENTRADA
) -> np.ndarray:
    """Retorna array float32 (tamanho, tamanho, 3) com valores em [0, 1].

    Aplica a orientação EXIF (fotos de celular), converte para RGB, redimensiona
    preservando a proporção e completa o quadro com cinza neutro. Não faz
    recorte, para não cortar lesões nas bordas.
    """
    if isinstance(origem, Image.Image):
        imagem = origem
    else:
        imagem = Image.open(origem)
    imagem = ImageOps.exif_transpose(imagem).convert("RGB")

    escala = tamanho / max(imagem.size)
    nova_largura = max(1, round(imagem.width * escala))
    nova_altura = max(1, round(imagem.height * escala))
    redimensionada = imagem.resize((nova_largura, nova_altura), Image.Resampling.BICUBIC)

    quadro = Image.new("RGB", (tamanho, tamanho), COR_PREENCHIMENTO)
    quadro.paste(redimensionada, ((tamanho - nova_largura) // 2, (tamanho - nova_altura) // 2))
    return np.asarray(quadro, dtype=np.float32) / 255.0
