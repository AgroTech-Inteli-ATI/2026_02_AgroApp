"""Verifica o contrato de preparar_imagem com imagens sintéticas."""
import io
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'src'))
from preprocessamento import COR_PREENCHIMENTO, TAMANHO_ENTRADA, preparar_imagem


def validar():
    # Formato e faixa de valores
    saida = preparar_imagem(Image.new('RGB', (640, 480), (10, 200, 30)))
    assert saida.shape == (TAMANHO_ENTRADA, TAMANHO_ENTRADA, 3)
    assert saida.dtype == np.float32
    assert saida.min() >= 0 and saida.max() <= 1

    # Proporção preservada: imagem larga fica com faixas cinzas no topo e na base
    larga = preparar_imagem(Image.new('RGB', (448, 112), (0, 255, 0)))
    cinza = np.array(COR_PREENCHIMENTO, dtype=np.float32) / 255
    assert np.allclose(larga[0], cinza, atol=1e-2), 'faixa superior deveria ser preenchimento'
    assert np.allclose(larga[-1], cinza, atol=1e-2), 'faixa inferior deveria ser preenchimento'
    assert np.allclose(larga[TAMANHO_ENTRADA // 2, 0], [0, 1, 0], atol=1e-2), 'conteúdo deveria ocupar a largura'

    # Imagem pequena (abaixo de 224 px) é ampliada, não rejeitada
    pequena = preparar_imagem(Image.new('RGB', (121, 136), (50, 50, 50)))
    assert pequena.shape == (TAMANHO_ENTRADA, TAMANHO_ENTRADA, 3)

    # Modo não RGB (escala de cinza e RGBA) vira RGB de 3 canais
    assert preparar_imagem(Image.new('L', (300, 300), 90)).shape[-1] == 3
    assert preparar_imagem(Image.new('RGBA', (300, 300), (1, 2, 3, 255))).shape[-1] == 3
    try:
        preparar_imagem(Image.new('RGBA', (300, 300), (1, 2, 3, 0)))
        raise AssertionError('transparência deveria ser recusada como no navegador')
    except ValueError as erro:
        assert 'transparência' in str(erro)

    # Orientação EXIF é aplicada: 100x200 girada 90° vira paisagem
    retrato = Image.new('RGB', (100, 200), (255, 0, 0))
    exif = retrato.getexif()
    exif[0x0112] = 6
    buffer = io.BytesIO()
    retrato.save(buffer, format='JPEG', exif=exif)
    buffer.seek(0)
    girada = preparar_imagem(Image.open(buffer))
    # Após girar, a imagem é paisagem: faixa cinza no topo e conteúdo vermelho no centro
    assert np.allclose(girada[0, TAMANHO_ENTRADA // 2], cinza, atol=1e-2), 'orientação EXIF não aplicada'
    assert np.allclose(girada[TAMANHO_ENTRADA // 2, TAMANHO_ENTRADA // 2], [1, 0, 0], atol=1e-2)

    # Determinismo: mesma entrada, mesma saída
    imagem = Image.new('RGB', (300, 220), (120, 60, 200))
    assert np.array_equal(preparar_imagem(imagem), preparar_imagem(imagem))

    # Caminho de arquivo funciona como entrada
    caminho = ROOT / 'assets/revisão_imagens/IMG_0125.jpg'
    if caminho.exists():
        assert preparar_imagem(caminho).shape == (TAMANHO_ENTRADA, TAMANHO_ENTRADA, 3)

    print('OK: formato, faixa, proporção, EXIF, modos de cor e determinismo verificados.')


if __name__ == '__main__':
    validar()
