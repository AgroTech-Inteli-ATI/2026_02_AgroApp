"""Verifica soma sem duplicação e recusa de artefatos adulterados."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import validacao_tamanho_t12_1 as medicao


class InventarioTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root / 'frontend/dist'
        (self.build / 'models').mkdir(parents=True)
        (self.root / 'docs').mkdir()
        original = b'original'
        web = b'web adaptado'
        (self.root / 'original.tflite').write_bytes(original)
        (self.build / 'models/modelo.tflite').write_bytes(web)
        manifest = {'models': [dict(format='Float16', role='principal',
                    filename='modelo.tflite', sourcePath='original.tflite', bytes=len(web),
                    sha256=hashlib.sha256(web).hexdigest(),
                    sourceSha256=hashlib.sha256(original).hexdigest())]}
        (self.build / 'models/manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        (self.build / 'index.html').write_bytes(b'<html>teste</html>')
        self.saida = self.root / 'saida'

    def executar(self):
        with patch.object(medicao, 'ROOT', self.root), contextlib.redirect_stdout(io.StringIO()):
            medicao.gerar(self.build, self.saida)

    def test_total_sem_duplicar_original_e_gzip_reproduzivel(self):
        self.executar()
        antes = (self.saida / 'medicoes.json').read_bytes()
        dados = json.loads(antes)
        self.assertEqual(dados['total_bytes'], sum(p.stat().st_size for p in self.build.rglob('*') if p.is_file()))
        self.assertEqual(dados['total_bytes'], sum(g['bytes'] for g in dados['componentes'].values()))
        self.assertEqual(len(dados['arquivos']), 3)
        self.executar()
        self.assertEqual(antes, (self.saida / 'medicoes.json').read_bytes())

    def test_recusa_modelo_web_adulterado(self):
        (self.build / 'models/modelo.tflite').write_bytes(b'adulterado')
        with self.assertRaisesRegex(ValueError, 'Modelo web diverge'):
            self.executar()

    def test_recusa_original_adulterado(self):
        (self.root / 'original.tflite').write_bytes(b'adulterado')
        with self.assertRaisesRegex(ValueError, 'Modelo original diverge'):
            self.executar()

    def test_modelo_ausente_impede_relatorio(self):
        (self.build / 'models/modelo.tflite').unlink()
        with self.assertRaises(KeyError):
            self.executar()
        self.assertFalse(self.saida.exists())


if __name__ == '__main__':
    unittest.main()
