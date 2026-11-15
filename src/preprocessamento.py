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
CONTRATO_PREPROCESSAMENTO = "T10.2-rgb8-sem-conversao-icc-v1"
MAX_PIXELS = 40_000_000


def decodificar_imagem(origem: Path | str | Image.Image) -> Image.Image:
    """RGB8 independente da origem; EXIF uma vez, ICC deliberadamente ignorado.

    Preserva os valores codificados usados no treinamento T4.1. Não usar
    ImageCms aqui: na web createImageBitmap usa colorSpaceConversion='none'.
    Consulte a seção 10.2 de docs/Projeto.md para o domínio e as tolerâncias.
    """
    if not isinstance(origem, Image.Image):
        with Image.open(origem) as imagem:
            return decodificar_imagem(imagem)
    if origem.width * origem.height > MAX_PIXELS:
        raise ValueError("A foto é grande demais. Reduza para até 40 megapixels.")
    imagem = ImageOps.exif_transpose(origem)
    if "A" in imagem.getbands() or "transparency" in imagem.info:
        if imagem.convert("RGBA").getchannel("A").getextrema() != (255, 255):
            raise ValueError("A imagem tem transparência. Escolha uma imagem opaca.")
    # convert('RGB') não aplica perfis ICC, gAMA ou correção de exposição.
    return imagem.convert("RGB")


def preparar_pixels(
    origem: Path | str | Image.Image, tamanho: int = TAMANHO_ENTRADA
) -> np.ndarray:
    """Retorna RGB uint8 HWC após EXIF, resize e padding, antes da normalização."""
    if not isinstance(tamanho, int) or isinstance(tamanho, bool) or tamanho < 1:
        raise ValueError("O tamanho deve ser um inteiro positivo.")
    imagem = decodificar_imagem(origem)
    escala = tamanho / max(imagem.size)
    nova_largura = max(1, round(imagem.width * escala))
    nova_altura = max(1, round(imagem.height * escala))
    redimensionada = imagem.resize((nova_largura, nova_altura), Image.Resampling.BICUBIC)
    quadro = Image.new("RGB", (tamanho, tamanho), COR_PREENCHIMENTO)
    quadro.paste(redimensionada, ((tamanho - nova_largura) // 2, (tamanho - nova_altura) // 2))
    return np.asarray(quadro, dtype=np.uint8)


def preparar_imagem(
    origem: Path | str | Image.Image, tamanho: int = TAMANHO_ENTRADA
) -> np.ndarray:
    """Retorna array float32 (tamanho, tamanho, 3) com valores em [0, 1].

    Aplica a orientação EXIF (fotos de celular), ignora ICC, converte para RGB, redimensiona
    preservando a proporção e completa o quadro com cinza neutro. Não faz
    recorte, para não cortar lesões nas bordas.
    """
    return preparar_pixels(origem, tamanho).astype(np.float32) / np.float32(255)
