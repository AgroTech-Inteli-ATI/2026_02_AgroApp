# T9.1 — O que aproveitar e atualizar no frontend

Análise em 06/11/2026, após atualizar as referências remotas. A `develop` foi atualizada por fast-forward até `d4e0622`; o merge que estava pendente em `feat/frontend` foi conferido e concluído em `d521c48`. Não houve push. As seções 1–9 registram o diagnóstico e o plano inicial; a seção 10 registra a implementação posterior autorizada pelo usuário.

## 1. Escopo e situação real

Em `entregas.md`, a T9.1 exige que uma imagem capturada ou selecionada seja processada e usada pelo modelo para classificar. Ela já está marcada como concluída pelo front básico. O código sustenta o fluxo de seleção de arquivo e inferência local, mas ainda exige atualização do artefato embarcado conforme a T8.3 e evidência em aparelho físico para consolidar a integração mobile.

A tecnologia existente é React + TypeScript + Vite com LiteRT.js no navegador. A dependência de definição da tecnologia mobile, indicada em `entregas.md`, deve ser explicitada na decisão: o caminho atual é aplicação web em navegador de celular. Se o projeto exigir aplicativo nativo, será necessário definir essa integração; não é uma simples troca de modelo no React.

## 2. Entregas que alimentam a T9.1

| Entrega | O que aproveitar | Situação encontrada |
| --- | --- | --- |
| T4.1 — Padronização | `src/preprocessamento.py`: EXIF, RGB, 224 × 224, proporção preservada, interpolação bicúbica, padding cinza 128, float32 em [0,1] | Já reproduzida no front em `src/lib/preprocess.ts`, com testes contra referências Python |
| T5.6 — Candidato | `assets/modelos/candidato_T5_6_20261026/classes.json` e identidade do EfficientNet-Lite0 | As 13 classes e sua ordem já são usadas; os arquivos de modelo usados pelo front ainda são os desta etapa |
| T7.1 — Conversão | `assets/modelos/conversao_T7_1_candidato_T5_6_20261026/modelo.tflite` e `contrato_tensores.json` | FP32 oficial disponível; fonte para contrato e eventual alternativa de compatibilidade |
| T7.2 — Comparação | `assets/modelos/comparacao_T7_2_candidato_T5_6_20261026/tabela_comparativa.csv`, métricas por classe e hashes | Subsídio à escolha; INT8 regenerado da T7.2 e INT8 oficial da T7.3 são arquivos distintos |
| T7.3 — INT8 oficial | `assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite` e `contrato_int8.json` | Disponível, com calibração documentada e contrato INT8; ainda não é a fonte do build web |
| T8.1 — Qualidade pós-conversão | Métricas gerais, por classe, mudanças de predição e revisão visual | Disponível em `origin/feat/avaliacao-pos-conversao`, commits `0316d3d` e `528325c`; ainda fora da `develop` atual e desta branch |
| T8.2 — Benchmark | `assets/data/benchmark_T8_2/oficiais_20261106/` e seção 8.2 de `docs/Projeto.md` | Integrada; benchmark local comparável, sem certificação de desempenho no celular |
| T8.3 — Escolha mobile | Decisão documentada com caminho, hash, classes, contrato e runtime do artefato escolhido | Não foi localizada uma decisão final na `develop` inspecionada; dependência para fechar qual modelo publicar |

A T7.2 recomenda o INT8 da T7.3. Essa recomendação é uma base para a T8.3, não substitui a decisão final. Não é necessário treinar ou converter novamente para começar a integração: os arquivos e contratos já existem.

## 3. O que o front já faz

- `frontend/src/App.tsx`: recebe JPEG, PNG e WebP, valida tipo/tamanho, envia o arquivo ao worker e mostra andamento, erros, foto original, entrada preparada e ranking das hipóteses.
- `frontend/src/lib/preprocess.ts`: aplica orientação EXIF, decodifica RGB, redimensiona com proporção preservada e padding, limita a imagem a 40 megapixels e rejeita transparência. A interface limita o arquivo a 10 MiB.
- `frontend/src/lib/inference.worker.ts`: carrega e aquece o modelo uma vez, prepara a entrada float32 ou INT8, executa localmente, desquantiza a saída e associa os 13 scores aos índices das classes. O processamento fica fora da interface principal.
- `frontend/scripts/prepare-assets.mjs`: confere hashes, lê o contrato do TFLite, gera cópias web com dimensões concretas e empacota runtime/worker. Os originais são preservados.
- `frontend/tests/analysis.spec.ts`: exercita inferência INT8 real, comparação com Python, EXIF, reutilização, ausência de upload, arquivo inválido, recuperação de falha e alternativa FP32.

Esse pipeline deve ser reaproveitado. Não há necessidade de reescrever a normalização nem de criar um servidor de inferência para a T9.1.

## 4. Frentes de atualização

### 4.1 Fixar o artefato selecionado

Concluir/documentar a T8.3 usando T8.1 e T8.2. Depois, atualizar `frontend/scripts/prepare-assets.mjs` para ler o modelo selecionado e seu contrato oficial, mantendo `classes.json` na ordem correta e validando a rastreabilidade de ambos.

Diferença comprovada por SHA-256:

| Arquivo | SHA-256 |
| --- | --- |
| INT8 T5.6 atualmente usado no front | `07e787453ab3775473f15e5081b0e0f0b67b67e4394c13ecbbea01b69c1c90cd` |
| INT8 oficial T7.3 | `456caec54fae3c57684f9afd6842cae611a1f6cb6587b40b0c5bd8256aea1340` |

Ambos têm 4.003.624 bytes. Igualdade de tamanho não permite atribuir ao modelo antigo as métricas do novo. Se a T8.3 confirmar o INT8 T7.3, usar o segundo arquivo. Atualizar também a origem FP32 se essa alternativa for mantida, vinculando-a à T7.1; o FP32 tem 13.531.184 bytes e ultrapassa o limite proposto de 8 MB para o modelo móvel.

O manifesto web deve registrar a origem e os hashes do arquivo original e da cópia web. Manter a especialização de dimensões necessária ao runtime e reconferir equivalência da execução original/web. O worker já lê dtype, escala e zero point; preservar essa lógica em vez de fixar parâmetros sem conferir o arquivo.

### 4.2 Oferecer captura no celular

O input atual tem `type="file"` e `accept`, sem `capture`; não há fluxo de câmera dedicado nem `getUserMedia`. O seletor do sistema pode oferecer câmera em alguns aparelhos, mas isso não foi validado.

Em `frontend/src/App.tsx`, oferecer ações claras de tirar foto e escolher da galeria. A captura deve reaproveitar a mesma função `analyze(File)` e o mesmo worker. Para a versão web básica, avaliar um input de captura com preferência pela câmera traseira e manter o seletor de galeria separado. Confirmar o comportamento no navegador/aparelho escolhido antes de registrar o aceite. Uma prévia de câmera dentro da aplicação só precisa de um fluxo adicional se for requisito do produto.

Validar cancelamento, indisponibilidade da câmera, eventual negativa de permissão, orientação da foto e nova tentativa. Publicar/testar em HTTPS no celular, conforme as exigências do runtime já documentadas no README.

### 4.3 Atualizar as evidências Python e os testes

`frontend/scripts/generate-reference.py` também aponta para o INT8 antigo. Alterar apenas o caminho no empacotamento deixa os scores de referência vinculados ao modelo anterior.

Depois da escolha, atualizar a fonte do gerador, regenerar `frontend/tests/fixtures/reference.json` e conferir o hash da origem e da cópia web. Confirmar equivalência entre original e cópia web, os 13 scores, orientação EXIF, normalização e quantização. Os testes atuais aceitam diferença de até 2/256 por score entre os runtimes Python e navegador.

Adicionar evidência da nova entrada por captura e da galeria. Teste automatizado com arquivo e viewport móvel não comprova uso da câmera física.

### 4.4 Registrar o aceite em aparelho

Documentar em `docs/Projeto.md` uma seção T9.1 com modelo/hash, tecnologia e contrato, aparelho/SO/navegador, entrada pela câmera e galeria, foto original/entrada preparada, classificação e falhas tratadas. Atualizar `frontend/README.md` com os novos caminhos e limitações verificadas.

Medir captura/decodificação/pré-processamento/inferência no aparelho separadamente. O benchmark da T8.2 não inclui toda essa espera e foi executado em CPU de notebook.

## 5. Limites entre a T9.1 e as próximas entregas

| Entrega | Pendência atual | Base disponível |
| --- | --- | --- |
| T9.2 — Confiança | O front sempre mostra top-3; falta o estado inconclusivo | `assets/data/politica_T6_5/parametros.json` propõe top-1 >= 0,65 e k=3. O documento exige reconferir o limiar no INT8 antes de aplicar no aparelho; não tratar a calibração Keras como validação do INT8 |
| T9.3 — Conteúdo | `frontend/src/data/content.ts` está vazio | `assets/data/dicionario-classes.json` é preliminar; os IDs AGRO não são índices de saída do modelo. Mapear explicitamente as 13 classes para conteúdo revisado, com fonte e data; as chaves de conteúdo ainda aguardam catálogo |
| T9.4 — Offline | Não há service worker nem garantia de abertura/reabertura sem rede | Modelo e runtime executam localmente após carregar, mas há downloads na inicialização. Preparar armazenamento/cache e validar o fluxo completo em modo avião, incluindo conteúdo |

O aceite de seleção de imagem da T9.1 não comprova essas três entregas. Elas podem reutilizar o pipeline existente e ser implementadas depois, com seus critérios próprios.

## 6. Verificações desta análise

- Merge sem entradas não resolvidas e sem erros em `git diff --cached --check`; o conteúdo recebido de `docs/`, `assets/`, `src/` e `tests/` coincide com a `develop` integrada.
- `npm.cmd test`: 9 testes passaram.
- `npm.cmd run build`: preparação dos artefatos, TypeScript e Vite passaram.
- `npm.cmd run test:e2e`: 4 testes passaram em Chromium, incluindo inferência real INT8 e alternativa FP32. Esses testes usam os modelos atualmente empacotados da T5.6; não validam antecipadamente a troca para a T7.3 nem a câmera física.
- Os arquivos locais preexistentes `PLANO_T8_1.md` e `entregas.md` foram preservados fora do commit do merge.

A captura pode avançar com o pipeline atual. A atualização das fontes e referências dos modelos depende da decisão da T8.3; a validação final deve usar o artefato selecionado e registrar câmera e galeria no celular.

## 7. Plano de implementação por arquivo

Os itens abaixo são trabalho proposto, ainda não implementado. A captura pode avançar independentemente da escolha final do modelo; a troca dos artefatos e suas referências deve ocorrer em conjunto depois da T8.3.

| Arquivo | Alteração prevista | Resultado verificável |
| --- | --- | --- |
| `frontend/scripts/prepare-assets.mjs` | Separar origem das classes, do INT8 e do FP32; conferir cada arquivo contra seu contrato oficial; registrar origem, versão e hashes no manifesto web | O build recusa modelo ou classes divergentes; o manifesto identifica exatamente o que será executado |
| `frontend/src/types.ts` | Tipar os metadados de origem que o gerador já publica ou passará a publicar, incluindo `sourceSha256`; manter a compatibilidade das mensagens entre React e worker | O consumidor consegue relacionar o modelo carregado à evidência Python sem metadados omitidos dos tipos |
| `frontend/src/lib/inference.worker.ts` | Preservar execução e pré-processamento atuais; ajustar somente a leitura dos metadados se necessário | Continua carregando uma vez e produzindo 13 scores associados aos mesmos índices |
| `frontend/scripts/generate-reference.py` | Ler a origem selecionada a partir dos metadados gerados, conferindo hashes antes de calcular referências | Gerador Python e build web usam o mesmo arquivo original; não ficam com caminhos independentes para modelos diferentes |
| `frontend/tests/fixtures/reference.json` | Regenerar scores, hash original, hash web e parâmetros de quantização após a troca | Referências rastreáveis ao artefato selecionado; nenhuma expectativa é copiada do modelo anterior |
| `frontend/tests/analysis.spec.ts` | Conferir identidade/hash do modelo contra a referência antes de comparar scores; adaptar os seletores aos dois inputs; exercitar ambas as entradas | Uma referência antiga é identificada como incompatível, mesmo se os scores eventualmente ficarem dentro da tolerância |
| `frontend/src/App.tsx` | Acrescentar entrada de câmera e ação de galeria, ambas encaminhadas para `analyze(File)`; permitir repetir e trocar foto | Câmera e galeria chegam ao mesmo processamento, com os mesmos limites, estados e tratamento de arquivo inválido |
| `frontend/src/App.module.css` | Acomodar as duas ações no painel existente, mantendo uso por toque e teclado e disposição em tela estreita | Os controles continuam acessíveis e não ficam cortados no celular |
| `frontend/README.md` | Atualizar origem dos modelos, instruções de captura e aparelhos efetivamente testados | A documentação descreve o build que foi validado |
| `docs/Projeto.md` | Acrescentar seção T9.1 com contrato, fluxo, rastreabilidade e evidências do aparelho | O critério de aceite fica demonstrável e as pendências mobile permanecem explícitas |

`frontend/src/lib/preprocess.ts` deve permanecer com o contrato atual, salvo se uma divergência real aparecer nos testes. Não aplicar outra normalização do backbone, mudar para recorte central ou alterar a ordem de classes durante essa integração.

### 7.1 Contrato entre empacotamento e referências

Manter no manifesto web a identidade do candidato e acrescentar a identidade específica da conversão. Para cada modelo, registrar caminho de origem relativo à raiz do repositório, caminho do contrato, hash original, nome/hash da cópia web, bytes e especificação dos tensores. Para as classes, registrar também origem e hash.

O gerador Python deve conferir os bytes originais e web com esse manifesto antes de inferir. O teste de navegador deve conferir que `reference.modelSha256` e `reference.webModelSha256` correspondem ao INT8 presente no manifesto servido. Só depois deve comparar os scores. Isso fecha uma lacuna atual: os hashes existem na referência, mas o teste E2E ainda não os compara com o manifesto.

Preservar os arquivos originais e limitar a especialização web às assinaturas de dimensões já tratadas pelo script. A equivalência original/web deve ser reconferida com o modelo escolhido.

### 7.2 Fluxo de captura previsto

1. A tela apresenta as ações de tirar foto e escolher da galeria, habilitadas quando o modelo estiver pronto.
2. A câmera usa um input separado com preferência pela câmera traseira; a galeria mantém o seletor sem preferência de captura.
3. Ao retornar um arquivo, as duas entradas chamam `analyze(File)`. Os handlers limpam o valor do input para permitir selecionar novamente a mesma foto.
4. Enquanto a análise ocorre, ambas as ações ficam indisponíveis. Concluída a análise, é possível remover, trocar ou tirar outra foto.
5. Cancelar o seletor preserva a foto e o resultado atuais. Não exibir erro quando nenhum arquivo for retornado.

A disponibilidade e os erros da câmera controlada pelo seletor nativo precisam ser observados no aparelho. Não prometer uma mensagem específica de permissão negada se o navegador não expuser essa situação à aplicação. Manter a alternativa de galeria disponível.

## 8. Evidências para acompanhar a decisão da T8.3

Os dados abaixo ajudam a revisar a decisão já recomendada na T7.2. Não constituem uma nova seleção feita por este plano.

| Versão | Tamanho (MB decimais) | F1 macro no teste exploratório T8.1 | Acurácia no mesmo teste | p95 local T8.2 (ms) |
| --- | ---: | ---: | ---: | ---: |
| FP32 T7.1 | 13,531 | 0,7329 | 84,78% | 16,03 |
| Float16 T7.2 | 6,834 | 0,7329 | 84,78% | 13,93 |
| Faixa dinâmica T7.2 | 3,753 | 0,7371 | 84,78% | 71,97 |
| INT8 oficial T7.3 | 4,004 | 0,7400 | 84,36% | 10,03 |
| INT8 regenerado T7.2 | 4,004 | 0,7471 | 85,41% | 12,67 |

Fonte de qualidade: `metricas_gerais.csv` na branch `origin/feat/avaliacao-pos-conversao`, commit `528325c`, 473 imagens e 13 classes. Fonte de tamanho/latência: `assets/data/benchmark_T8_2/oficiais_20261106/resumo.csv` na `develop` integrada. São avaliações de aspectos diferentes, não uma única execução.

O relatório da T8.1 declara que o teste já foi consultado em etapas anteriores e não é uma avaliação final independente; ele não fundamenta seleção de modelo nem ajuste de limiar. Portanto, o F1 maior do INT8 regenerado não autoriza substituir automaticamente o INT8 oficial. A T8.3 deve documentar o critério, a evidência de validação, os resultados por classe e as limitações, preservando a distinção entre os arquivos. As latências acima são de notebook e não aprovam desempenho no celular.

## 9. Critérios para encerrar a atualização da T9.1

| Verificação | Evidência necessária | Pode ser feita nesta máquina? |
| --- | --- | --- |
| Modelo e classes corretos | Caminhos/contratos/hashes da decisão T8.3 coincidem com o manifesto servido | Sim, após a decisão |
| Imagem preparada corretamente | Testes contra Python, orientação EXIF e entrada 224 × 224 com proporção/padding preservados | Sim |
| Modelo original e cópia web equivalentes | Gerador Python confere os dois arquivos e suas saídas nas referências | Sim, com o ambiente TensorFlow descrito no README |
| Inferência no navegador | Scores comparados com Python, índices corretos, modelo reutilizado e ausência de envio da foto | Sim, por E2E |
| Câmera e galeria físicas | Captura e seleção em aparelho identificado, com resultado e entrada preparada registrados | Exige acesso ao celular de referência |
| Recuperação e repetição | Cancelar sem apagar resultado, repetir foto, trocar imagem e recuperar falhas | Parte automatizável; seletor/câmera exigem validação física |
| Documentação | Seção T9.1 e README correspondem ao artefato e aos testes realizados | Sim; evidência física depende do teste no celular |

Executar, após as alterações, `npm.cmd run assets`, gerar as referências Python com o modelo selecionado, `npm.cmd test`, `npm.cmd run test:e2e` e `npm.cmd run build`. Registrar os resultados dessa nova execução separadamente dos testes de diagnóstico já aprovados na seção 6.

Sequência de trabalho proposta:

1. Implementar câmera/galeria reaproveitando o fluxo atual, com testes de entrada, cancelamento e repetição.
2. Quando a T8.3 estiver documentada, atualizar empacotamento, metadados, gerador Python e referências como uma única mudança coerente.
3. Executar as verificações locais e corrigir divergências de contrato ou runtime que aparecerem.
4. Validar no aparelho físico e completar a documentação com evidências reais. Até isso acontecer, registrar explicitamente o que foi validado apenas em Chromium automatizado.

Limiar, conteúdo técnico e funcionamento offline continuam com os critérios próprios das T9.2, T9.3 e T9.4.

## 10. Execução do plano — 06/11/2026

- [x] Acrescentar ações separadas de câmera e galeria, com repetição/troca da foto e preservação do resultado ao cancelar.
- [x] Reaproveitar `analyze(File)`, worker e pré-processamento existentes; manter originais, classes e normalização.
- [x] Centralizar fontes em `frontend/model-sources.json`, mantendo os modelos T5.6 e `T8.3_pendente`.
- [x] Registrar origem/contrato/versão/hashes dos modelos e das classes no manifesto web e tipar os metadados.
- [x] Fazer o gerador Python consumir o manifesto e conferir hashes/classes antes de inferir; regenerar as referências com equivalência original/web confirmada.
- [x] Conferir hashes/versão/origem no E2E antes dos scores; adaptar os testes aos dois seletores e acrescentar cancelamento/repetição em viewport móvel.
- [x] Executar 9 testes unitários, 5 E2E e build de produção, todos aprovados. Detector de interface sem achados; revisão visual desktop/móvel sem rolagem horizontal nas capturas verificadas.
- [x] Documentar fluxo, artefatos e pendências em `frontend/README.md` e seção 9.1 de `docs/Projeto.md`.
- [ ] Adotar o artefato final: depende da decisão documentada da T8.3; não foi substituído automaticamente.
- [ ] Validar câmera física, galeria e desempenho no aparelho de referência por HTTPS e anexar as evidências reais.

A implementação, os testes e a documentação foram registrados no commit `0bedece` — `feat(9.1): integre captura e galeria ao pipeline de análise`, a pedido do usuário. Não houve push. Este plano permanece local, fora do commit. Não foi integrada outra branch além da `develop` já incorporada no merge anterior.
