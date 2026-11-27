"""Gera a tabela documental a partir do JSON; não altera o inventário."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def tabela(classes):
    linhas = [
        '| ID | Cultura | Categoria | Rótulo no inventário / nome comum | Agente causal de referência | Chave proposta |',
        '| --- | --- | --- | --- | --- | --- |',
    ]
    for c in classes:
        agente = c['agente_causal'] or 'Indeterminado — revisão necessária'
        linhas.append(f"| {c['id']} | {c['cultura']} | {c['categoria']} | {c['nome_comum']} | {agente} | `{c['chave_conteudo_proposta']}` |")
    return '\n'.join(linhas)


if __name__ == '__main__':
    dados = json.loads((ROOT / 'assets/data/dicionario-classes.json').read_text(encoding='utf-8'))
    documento = ROOT / 'docs/Projeto.md'
    texto = documento.read_text(encoding='utf-8')
    inicio, restante = texto.split('<!-- tabela:inicio -->', 1)
    _, fim = restante.split('<!-- tabela:fim -->', 1)
    documento.write_text(inicio + '<!-- tabela:inicio -->\n' + tabela(dados['classes']) + '\n<!-- tabela:fim -->' + fim, encoding='utf-8')
