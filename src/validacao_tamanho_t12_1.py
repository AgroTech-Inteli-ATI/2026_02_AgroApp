"""Inventário reproduzível do build web, sem dependências externas."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def medir(path, nome, categoria):
    dados = path.read_bytes()
    return dict(arquivo=nome, categoria=categoria, bytes=len(dados),
                gzip_bytes=len(gzip.compress(dados, mtime=0)),
                sha256=hashlib.sha256(dados).hexdigest())


def categoria(nome):
    if nome.endswith('.tflite'):
        return 'Modelos web'
    if nome == 'models/manifest.json':
        return 'Manifesto, rótulos e contratos'
    if nome.startswith('runtime/'):
        return 'Runtime LiteRT e worker'
    if nome.endswith(('.woff', '.woff2', '.ttf')):
        return 'Fontes'
    if nome.endswith(('.png', '.jpg', '.svg', '.ico', '.webp')):
        return 'Imagens'
    return 'Interface, estilos e suporte offline'


def gerar(build, saida):
    manifesto = json.loads((build / 'models/manifest.json').read_text(encoding='utf-8'))
    arquivos = [medir(p, p.relative_to(build).as_posix(), categoria(p.relative_to(build).as_posix()))
                for p in sorted(build.rglob('*')) if p.is_file()]
    por_nome = {a['arquivo']: a for a in arquivos}
    modelos = []
    for m in manifesto['models']:
        web = por_nome['models/' + m['filename']]
        original = medir(ROOT / m['sourcePath'], m['sourcePath'], 'Modelo original')
        if web['sha256'] != m['sha256'] or web['bytes'] != m['bytes']:
            raise ValueError('Modelo web diverge do manifesto: ' + m['filename'])
        if original['sha256'] != m['sourceSha256']:
            raise ValueError('Modelo original diverge do manifesto: ' + m['sourcePath'])
        modelos.append(dict(formato=m['format'], papel=m['role'], original=original, web=web))
    grupos = {}
    for a in arquivos:
        g = grupos.setdefault(a['categoria'], dict(arquivos=0, bytes=0, gzip_bytes=0))
        g['arquivos'] += 1
        for k in ('bytes', 'gzip_bytes'):
            g[k] += a[k]
    total = sum(a['bytes'] for a in arquivos)
    gzip_total = sum(a['gzip_bytes'] for a in arquivos)
    resultado = dict(esquema='tamanho_T12_1_v1', build=build.relative_to(ROOT).as_posix(),
                     modelos=modelos, componentes=grupos, arquivos=arquivos,
                     total_bytes=total, gzip_por_arquivo_total_bytes=gzip_total,
                     limites=dict(fonte='docs/Projeto.md, seção 2.1',
                                  status='propostas da equipe; confirmação do parceiro pendente',
                                  modelo_bytes=8_000_000, acrescimo_pacote_bytes=9_000_000),
                     aceite='pendente de limites acordados e escopo web confirmado')
    resultado['proveniencia'] = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
        for p in ('frontend/package-lock.json', 'frontend/model-sources.json',
                  'frontend/scripts/prepare-assets.mjs', 'frontend/vite.config.ts',
                  'src/validacao_tamanho_t12_1.py') if (ROOT / p).is_file()
    }
    data = datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y')
    linhas = ['# T12.1 — Validação do tamanho do modelo e pacote web', '',
              'Autor: Karol · Revisor: Lucas · Meta de entrega: a definir', '',
              f'Medição executada em {data} (America/Sao_Paulo). Relatório técnico disponível; aceite final pendente.', '',
              '## Método e escopo', '',
              'Inventário de todos os arquivos de um build de produção novo (`frontend/dist`). '
              'Bytes são o tamanho lógico dos arquivos; MB = 1.000.000 bytes e MiB = 1.048.576 bytes. '
              'Não representam RAM ou espaço alocado no disco. O CSV e o JSON registram SHA-256 de cada arquivo.', '',
              'A coluna gzip usa compressão independente por arquivo (nível padrão 9, mtime=0). '
              'É uma referência reproduzível de transferência, não medição HTTP nem tamanho de ZIP; '
              'depende da configuração de compressão do servidor. O total bruto inclui todos os recursos publicados, '
              'inclusive os dois modelos e as variantes de runtime, mesmo quando não usados numa inferência.', '',
              '## Modelos finais selecionados na T8.3', '',
              '| Modelo | Papel | Original (bytes) | Web (bytes) | MB web | MiB web | Proposta RNF-01 ≤ 8 MB |',
              '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for m in modelos:
        n = m['web']['bytes']
        linhas.append(f"| {m['formato']} | {m['papel']} | {m['original']['bytes']} | {n} | {n/1e6:.6f} | {n/2**20:.6f} | {'Dentro' if n <= 8_000_000 else 'Acima'} da proposta |")
    linhas += ['', 'As cópias web especializam as dimensões dinâmicas para o LiteRT.js em '
               '`prepare-assets.mjs`; por isso têm hashes próprios, conferidos com o manifesto. '
               'Os originais também são conferidos. Caminhos e hashes constam no JSON. '
               'Float16 e INT8 são medidos individualmente e ambos integram o pacote atual.', '',
               '### Subtotais de modelo e manifesto (não são pacotes web completos)', '',
               '| Composição | Bytes | MB | Comparação exploratória com 9 MB |',
               '| --- | ---: | ---: | --- |']
    manifesto_bytes = por_nome['models/manifest.json']['bytes']
    for m in modelos:
        subtotal = m['web']['bytes'] + manifesto_bytes
        linhas.append(f"| {m['formato']} + manifesto | {subtotal} | {subtotal/1e6:.6f} | {'Dentro' if subtotal <= 9_000_000 else 'Acima'} da proposta |")
    subtotal = sum(m['web']['bytes'] for m in modelos) + manifesto_bytes
    linhas += [f'| Ambos + manifesto | {subtotal} | {subtotal/1e6:.6f} | {"Dentro" if subtotal <= 9_000_000 else "Acima"} da proposta |', '',
               '## Componentes do pacote publicado', '',
               '| Componente | Arquivos | Bytes | MB | MiB | Gzip por arquivo (bytes) |',
               '| --- | ---: | ---: | ---: | ---: | ---: |']
    for nome, g in sorted(grupos.items()):
        n = g['bytes']
        linhas.append(f"| {nome} | {g['arquivos']} | {n} | {n/1e6:.6f} | {n/2**20:.6f} | {g['gzip_bytes']} |")
    linhas += [f'| **Pacote web completo** | **{len(arquivos)}** | **{total}** | **{total/1e6:.6f}** | **{total/2**20:.6f}** | **{gzip_total}** |', '',
               'O manifesto contém rótulos, ordem das classes e contratos de tensores; não somamos '
               '`classes.json` novamente. Conteúdos e política de confiança importados pelo frontend '
               'já compõem o JavaScript gerado. O inventário detalha cada WASM, carregador e worker. '
               'Dependências de desenvolvimento, node_modules, datasets, checkpoints e relatórios Python '
               'não são recursos publicados e ficam fora da soma.', '',
               '## Comparação com os limites do parceiro', '',
               'A seção 2.1 de [Projeto.md](Projeto.md#21-requisitos-e-restrições-técnicas) '
               'marca RNF-01 (8 MB por modelo) e RNF-02 (9 MB de acréscimo: modelo + rótulos + índice) '
               'com ⧗: **propostas da equipe aguardando resposta do parceiro**. '
               'Não foi localizada evidência de ratificação; estes valores não são limites efetivamente acordados.', '',
               f'O pacote web completo soma **{total/1e6:.6f} MB** e '
               f"{'ultrapassa' if total > 9_000_000 else 'fica dentro de'} 9 MB como comparação exploratória. "
               'O RNF-02 descreve acréscimo ao aplicativo e não define explicitamente o escopo de um site completo. '
               'Não é possível declarar atendimento ou reprovação contratual da versão web com esse parâmetro.', '',
               '| Medida | Referência disponível | Resultado de aceite |',
               '| --- | --- | --- |',
               '| Modelo individual | RNF-01 ≤ 8 MB, proposto | Comparação numérica acima; ratificação pendente |',
               '| Acréscimo ao aplicativo | RNF-02 ≤ 9 MB, proposto | Baseline e escopo do acréscimo não definidos para web |',
               '| Site completo e recursos de runtime | Sem limite web ratificado localizado | Tamanho medido; aceite pendente |', '',
               'Para encerrar o critério de aceite, Lucas deve revisar as evidências e registrar com o parceiro: '
               'limites em bytes, se valem para modelo individual ou ambos, recursos incluídos, '
               'tamanho bruto ou comprimido, e se RNF-02 vale para o site completo ou incremento sobre uma versão de referência. '
               'Registrar data, responsável e ata ou mensagem de aprovação. Não atribuímos aprovação ao parceiro.', '',
               '## Reprodução', '', 'Na raiz do repositório:', '', '```powershell',
               'cd frontend', 'npm ci --no-audit --no-fund', 'npm run build', 'cd ..',
               'python -m src.validacao_tamanho_t12_1', '```', '',
               'Saídas: este relatório, `assets/data/validacao_T12_1/inventario.csv` e '
               '`assets/data/validacao_T12_1/medicoes.json`. O comando exige build com manifesto '
               'e recusa modelos divergentes. Não altera os modelos nem o build.']
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'medicoes.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=['arquivo', 'categoria', 'bytes', 'gzip_bytes', 'sha256'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(arquivos)
    (saida / 'inventario.csv').write_text(buf.getvalue(), encoding='utf-8', newline='\n')
    (ROOT / 'docs/Validacao_T12_1.md').write_text('\n'.join(linhas) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(arquivos)} arquivos; {total} bytes; relatório docs/Validacao_T12_1.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'frontend/dist')
    parser.add_argument('--saida', type=Path, default=ROOT / 'assets/data/validacao_T12_1')
    args = parser.parse_args()
    gerar(args.build.resolve(), args.saida.resolve())
