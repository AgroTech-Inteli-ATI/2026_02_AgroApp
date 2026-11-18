# T12.1 — Validação do tamanho do modelo e pacote web

Autor: Karol · Revisor: Lucas · Meta de entrega: a definir

Medição executada em 16/11/2026 (America/Sao_Paulo). Relatório técnico disponível; aceite final pendente.

## Método e escopo

Inventário de todos os arquivos de um build de produção novo (`frontend/dist`). Bytes são o tamanho lógico dos arquivos; MB = 1.000.000 bytes e MiB = 1.048.576 bytes. Não representam RAM ou espaço alocado no disco. O CSV e o JSON registram SHA-256 de cada arquivo.

A coluna gzip usa compressão independente por arquivo (nível padrão 9, mtime=0). É uma referência reproduzível de transferência, não medição HTTP nem tamanho de ZIP; depende da configuração de compressão do servidor. O total bruto inclui todos os recursos publicados, inclusive os dois modelos e as variantes de runtime, mesmo quando não usados numa inferência.

## Modelos finais selecionados na T8.3

| Modelo | Papel | Original (bytes) | Web (bytes) | MB web | MiB web | Proposta RNF-01 ≤ 8 MB |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Float16 | principal | 6833548 | 6833548 | 6.833548 | 6.516979 | Dentro da proposta |
| INT8 | contingencia | 4003624 | 4003624 | 4.003624 | 3.818153 | Dentro da proposta |

As cópias web especializam as dimensões dinâmicas para o LiteRT.js em `prepare-assets.mjs`; por isso têm hashes próprios, conferidos com o manifesto. Os originais também são conferidos. Caminhos e hashes constam no JSON. Float16 e INT8 são medidos individualmente e ambos integram o pacote atual.

### Subtotais de modelo e manifesto (não são pacotes web completos)

| Composição | Bytes | MB | Comparação exploratória com 9 MB |
| --- | ---: | ---: | --- |
| Float16 + manifesto | 6836949 | 6.836949 | Dentro da proposta |
| INT8 + manifesto | 4007025 | 4.007025 | Dentro da proposta |
| Ambos + manifesto | 10840573 | 10.840573 | Acima da proposta |

## Componentes do pacote publicado

| Componente | Arquivos | Bytes | MB | MiB | Gzip por arquivo (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fontes | 8 | 73384 | 0.073384 | 0.069984 | 73336 |
| Imagens | 2 | 37502 | 0.037502 | 0.035765 | 36268 |
| Interface, estilos e suporte offline | 5 | 275386 | 0.275386 | 0.262629 | 85266 |
| Manifesto, rótulos e contratos | 1 | 3401 | 0.003401 | 0.003243 | 1116 |
| Modelos web | 2 | 10837172 | 10.837172 | 10.335133 | 9525232 |
| Runtime LiteRT e worker | 9 | 47034349 | 47.034349 | 44.855451 | 13151518 |
| **Pacote web completo** | **27** | **58261194** | **58.261194** | **55.562204** | **22872736** |

O manifesto contém rótulos, ordem das classes e contratos de tensores; não somamos `classes.json` novamente. Conteúdos e política de confiança importados pelo frontend já compõem o JavaScript gerado. O inventário detalha cada WASM, carregador e worker. Dependências de desenvolvimento, node_modules, datasets, checkpoints e relatórios Python não são recursos publicados e ficam fora da soma.

## Comparação com os limites do parceiro

A seção 2.1 de [Projeto.md](Projeto.md#21-requisitos-e-restrições-técnicas) marca RNF-01 (8 MB por modelo) e RNF-02 (9 MB de acréscimo: modelo + rótulos + índice) com ⧗: **propostas da equipe aguardando resposta do parceiro**. Não foi localizada evidência de ratificação; estes valores não são limites efetivamente acordados.

O pacote web completo soma **58.261194 MB** e ultrapassa 9 MB como comparação exploratória. O RNF-02 descreve acréscimo ao aplicativo e não define explicitamente o escopo de um site completo. Não é possível declarar atendimento ou reprovação contratual da versão web com esse parâmetro.

| Medida | Referência disponível | Resultado de aceite |
| --- | --- | --- |
| Modelo individual | RNF-01 ≤ 8 MB, proposto | Comparação numérica acima; ratificação pendente |
| Acréscimo ao aplicativo | RNF-02 ≤ 9 MB, proposto | Baseline e escopo do acréscimo não definidos para web |
| Site completo e recursos de runtime | Sem limite web ratificado localizado | Tamanho medido; aceite pendente |

Para encerrar o critério de aceite, Lucas deve revisar as evidências e registrar com o parceiro: limites em bytes, se valem para modelo individual ou ambos, recursos incluídos, tamanho bruto ou comprimido, e se RNF-02 vale para o site completo ou incremento sobre uma versão de referência. Registrar data, responsável e ata ou mensagem de aprovação. Não atribuímos aprovação ao parceiro.

## Reprodução

Na raiz do repositório:

```powershell
cd frontend
npm ci --no-audit --no-fund
npm run build
cd ..
python -m src.validacao_tamanho_t12_1
```

Saídas: este relatório, `assets/data/validacao_T12_1/inventario.csv` e `assets/data/validacao_T12_1/medicoes.json`. O comando exige build com manifesto e recusa modelos divergentes. Não altera os modelos nem o build.
