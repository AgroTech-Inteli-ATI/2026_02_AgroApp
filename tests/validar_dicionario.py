"""Verifica o contrato do dicionário e a cobertura do XLSX original."""
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'assets/data'))
from gerar_dicionario import tabela


def validar():
    dados = json.loads((ROOT / 'assets/data/dicionario-classes.json').read_text(encoding='utf-8'))
    classes = dados['classes']
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(ROOT / dados['origem']) as z:
        strings = [''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
        registros = []
        for linha in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:row', ns):
            valores = []
            for celula in linha.findall('s:c', ns):
                v = celula.find('s:v', ns)
                valor = v.text if v is not None else ''.join(celula.itertext())
                valores.append(strings[int(valor)] if celula.get('t') == 's' else valor)
            if len(valores) == 4 and valores[0] in ('Soja', 'Milho'):
                registros.append((valores[0], 'Doenças' if valores[1] == 'Doencas' else valores[1], valores[2], int(float(valores[3]))))
    esperado = sorted(registros)
    obtido = sorted((c['cultura'], c['categoria'], c['rotulo_origem'], c['quantidade_imagens']) for c in classes)
    assert esperado == obtido, 'Cobertura ou contagens divergentes do inventário'
    ids = {c['id'] for c in classes}
    assert len(ids) == len(classes) == 55
    assert sum(c['quantidade_imagens'] for c in classes) == 126
    assert len({c['chave_conteudo_proposta'] for c in classes}) == len(classes)
    for c in classes:
        assert re.fullmatch(r'AGRO-\d{3}', c['id'])
        assert c['chave_conteudo_proposta'] == f"{c['cultura'].lower()}.ocorrencia.{c['id'].lower()}"
        assert c['nome_comum']
        assert c['status_agente'] in ('indeterminado', 'referencia_a_validar')
        assert bool(c['agente_causal']) == (c['status_agente'] == 'referencia_a_validar')
        assert bool(c['fontes']) == bool(c['agente_causal'])
        assert all(f in dados['fontes'] for f in c['fontes'])
        assert c['status_conteudo'] in ('aguardando_catalogo_agroapp', 'validado')
        if c['status_conteudo'] == 'validado':
            assert c['chave_conteudo'] and all(c['validacao_conteudo'][f] for f in ('responsavel', 'data', 'evidencia'))
        else:
            assert c['chave_conteudo'] is None
        for relacao in c['relacoes']:
            assert relacao['id'] in ids and relacao['id'] != c['id']
            assert relacao['tipo'] in ('possivel_duplicidade', 'revisao_de_identidade')
    texto = (ROOT / 'docs/Projeto.md').read_text(encoding='utf-8')
    assert texto.split('<!-- tabela:inicio -->\n')[1].split('\n<!-- tabela:fim -->')[0] == tabela(classes), 'Tabela desatualizada; execute o gerador'
    print('OK: 55 ocorrências, 126 imagens; IDs, chaves, relações e documentação consistentes.')


if __name__ == '__main__':
    validar()
