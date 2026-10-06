"""Verifica o contrato de aplicar_aumento e a regra de uso somente no treino (T4.4)."""
import csv
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'src'))
from aumento import aplicar_aumento
from preprocessamento import COR_PREENCHIMENTO, preparar_imagem

MANIFESTO = ROOT / 'assets/data/particionamento_T4_2/manifesto_provisorio.csv'


def validar():
    base = np.random.default_rng(0).random((224, 224, 3), dtype=np.float32)
    original = base.copy()

    # Formato, faixa e entrada não alterada
    saida = aplicar_aumento(base, 'treino', np.random.default_rng(1))
    assert saida.shape == base.shape and saida.dtype == np.float32
    assert saida.min() >= 0 and saida.max() <= 1
    assert np.array_equal(base, original), 'a entrada não pode ser alterada no lugar'

    # Determinismo: mesma semente, mesma saída
    a = aplicar_aumento(base, 'treino', np.random.default_rng(7))
    b = aplicar_aumento(base, 'treino', np.random.default_rng(7))
    assert np.array_equal(a, b)

    # O preenchimento sintético da T4.1 não representa a cena e deve permanecer neutro.
    larga = preparar_imagem(Image.new('RGB', (448, 112), (0, 255, 0)))
    cinza = np.asarray(COR_PREENCHIMENTO, dtype=np.float32) / 255.0
    for semente in range(20):
        aumentada = aplicar_aumento(larga, 'treino', np.random.default_rng(semente))
        horizontal = np.allclose(aumentada[0], cinza) and np.allclose(aumentada[-1], cinza)
        vertical = np.allclose(aumentada[:, 0], cinza) and np.allclose(aumentada[:, -1], cinza)
        assert horizontal or vertical, f'preenchimento alterado com a semente {semente}'

    # Há variação real: a maioria dos sorteios altera a imagem
    rng = np.random.default_rng(2)
    iguais = sum(np.array_equal(aplicar_aumento(base, 'treino', rng), base) for _ in range(200))
    assert iguais < 20, f'aumento quase sem efeito: {iguais}/200 saídas iguais à entrada'

    # Validação e teste são recusados
    for particao in ('validacao', 'teste'):
        try:
            aplicar_aumento(base, particao, np.random.default_rng(0))
        except ValueError:
            pass
        else:
            raise AssertionError(f'aumento deveria ser recusado na partição {particao}')

    # Regra aplicada a todas as linhas do manifesto real da T4.2
    with MANIFESTO.open(encoding='utf-8-sig', newline='') as arquivo:
        linhas = list(csv.DictReader(arquivo))
    recusadas = 0
    for linha in linhas:
        if linha['particao'] == 'treino':
            continue
        try:
            aplicar_aumento(base, linha['particao'], np.random.default_rng(0))
        except ValueError:
            recusadas += 1
        else:
            raise AssertionError(f"aumento aceito indevidamente para {linha['image_id']}")
    treino = sum(1 for linha in linhas if linha['particao'] == 'treino')
    assert recusadas == len(linhas) - treino

    print(f'OK: contrato, determinismo, preenchimento neutro, variação e bloqueio fora do treino '
          f'({treino} de treino, {recusadas} recusadas no manifesto).')


if __name__ == '__main__':
    validar()
