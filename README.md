# AgroApp — Diagnóstico visual de pragas com inferência offline

Projeto desenvolvido pela **AgroTech Inteli** em parceria com o **Agro App**. A solução é um módulo de visão computacional que recebe a foto de um inseto em lavoura de **soja ou milho**, executa o modelo **no próprio aparelho, sem internet**, e apresenta as três hipóteses mais prováveis com o grau de confiança e o conteúdo técnico relacionado.

Este repositório reúne tudo o que foi produzido: dados de treinamento rastreáveis, código do pipeline de treinamento e avaliação, modelos convertidos para uso embarcado, aplicação de demonstração e documentação técnica para continuidade pela equipe do Agro App.

> **Escopo da entrega.** A integração ao aplicativo de produção do Agro App e a publicação nas lojas ficam com a equipe do parceiro, conforme o Termo de Abertura do Projeto. A demonstração foi construída como **aplicação web** (React + LiteRT.js) que roda no navegador do celular e funciona offline após o primeiro acesso.

---

## Sumário

- [Comece por aqui](#comece-por-aqui)
- [O que foi entregue](#o-que-foi-entregue)
- [Resultados em resumo](#resultados-em-resumo)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Rodando a demonstração](#rodando-a-demonstração)
- [Reproduzindo treinamento, avaliação e conversão](#reproduzindo-treinamento-avaliação-e-conversão)
- [Rodando os testes](#rodando-os-testes)
- [Limitações e pendências](#limitações-e-pendências)
- [Convenções do repositório](#convenções-do-repositório)
- [Equipe](#equipe)
- [Uso e licença](#uso-e-licença)

---

## Comece por aqui

Roteiro de leitura sugerido para quem vai receber o projeto:

| Se você quer… | Leia |
| --- | --- |
| Entender o problema, o escopo e as decisões do projeto | [Documentação completa (`docs/Projeto.md`)](docs/Projeto.md), seções 1 e 2 |
| Saber quais dados foram usados e de onde vieram | [Ficha do dataset final (T14.1)](docs/T14_1_Dataset_Final.md) |
| Treinar o modelo novamente | [Pipeline de treinamento (T14.2)](docs/T14_2_Pipeline_Treinamento.md) |
| Avaliar e converter um modelo para TFLite/LiteRT | [Avaliação e conversão (T14.3)](docs/T14_3_Avaliacao_Conversao.md) |
| Entender a aplicação e integrar o modelo | [Arquitetura e integração web (T14.4)](docs/T14_4_Arquitetura_Web.md) e [README do frontend](frontend/README.md) |
| Atualizar o modelo com novas imagens ou voltar à versão anterior | [Guia de retreinamento, atualização e reversão (T14.5)](docs/T14_5_Guia_Retreinamento.md) |
| Ver as métricas finais e os erros do modelo | [Avaliação final (T11.1)](docs/Avaliacao_Final_T11_1.md), [matriz de confusão (T11.2)](docs/Matriz_Erros_T11_2.md) e [limiar de confiança (T11.3)](docs/Avaliacao_Limiar_T11_3.md) |
| Conferir o que está atendido e o que ficou pendente | [Checklist final (T15.1)](docs/T15_1_Checklist_Final.md) e [pacote de entrega (T15.3)](docs/T15_3_Entrega_Parceiro.md) |

O [índice da documentação](docs/README.md) lista todos os documentos, agrupados por assunto.

---

## O que foi entregue

| Entrega | Onde está |
| --- | --- |
| Modelo de classificação de 13 pragas (EfficientNet-Lite0, transfer learning) | [`assets/modelos/candidato_T5_6_20261026/`](assets/modelos/candidato_T5_6_20261026/) |
| Modelos otimizados para o aparelho: **Float16** (principal, 6,8 MB) e **INT8** (contingência, 4,0 MB) | [`frontend/public/models/`](frontend/public/models/) e [manifesto com hashes](frontend/public/models/manifest.json) |
| Aplicação de demonstração offline (foto → top-3 com confiança → conteúdo técnico) | [`frontend/`](frontend/) |
| Pipeline reprodutível de preparação, treinamento, avaliação e conversão | [`src/`](src/) e [`notebooks/`](notebooks/) |
| Testes automatizados do pipeline Python e da aplicação | [`tests/`](tests/) e [`frontend/tests/`](frontend/tests/) |
| Evidências de cada etapa (métricas, matrizes, benchmarks, manifestos) | [`assets/data/`](assets/data/) |
| Documentação técnica e guias de manutenção | [`docs/`](docs/) |

### Classes reconhecidas pelo modelo (versão 1.0.0)

| Índice | Classe | Cultura |
| ---: | --- | --- |
| 0 | Vaquinha (*Diabrotica speciosa*) | Milho/Soja |
| 1 | Cigarrinha-do-milho (*Dalbulus maidis*) | Milho |
| 2 | Percevejo-barriga-verde (*Dichelops/Diceraeus*) | Milho/Soja |
| 3 | Lagarta-do-cartucho (*Spodoptera frugiperda*) | Milho/Soja |
| 4 | Percevejo-marrom (*Euschistus heros*) | Soja |
| 5 | Percevejo-verde (*Nezara viridula*) | Soja |
| 6 | Percevejo-asa-preta (*Edessa meditabunda*) | Soja |
| 7 | Percevejo-do-milho (*Leptoglossus zonatus*) | Milho |
| 8 | Lagarta-falsa-medideira (*Chrysodeixis includens*) | Soja |
| 9 | Lagarta-da-soja (*Anticarsia gemmatalis*) | Soja |
| 10 | Lagarta-das-vagens (*Spodoptera eridania* e *S. cosmioides*) | Soja |
| 11 | *Astylus variegatus* | Milho |
| 12 | Cigarrinha-das-pastagens (*Deois flavopicta*) | Milho |

A lista oficial, com a ordem de saída do modelo, está em [`assets/data/classes-modelo.csv`](assets/data/classes-modelo.csv) e no [dicionário de classes](assets/data/dicionario-classes.json).

---

## Resultados em resumo

Modelo `candidato_T5_6_20261026`, versão **1.0.0**. Números do [relatório T11.1](docs/Avaliacao_Final_T11_1.md) e do [benchmark T12.2](docs/Benchmark_T12_2.md).

| Indicador | Float16 (principal) | INT8 (contingência) |
| --- | ---: | ---: |
| Acurácia no teste histórico (473 imagens) | 0,848 | 0,844 |
| F1 macro no teste histórico | 0,733 | 0,740 |
| Classe correta entre as 3 hipóteses (top-3) | 0,954 | 0,945 |
| Tamanho do arquivo | 6,83 MB | 4,00 MB |
| Inferência no iPhone 13, Chrome (p95) | 13,1 ms | — |

- **Dados:** 3.156 imagens públicas (iNaturalist e AgroInsect), 2.209 de treino, 474 de validação e 473 de teste.
- **Política de confiança:** o app mostra as três hipóteses quando a mais provável atinge **0,65**. Abaixo disso, o resultado é tratado como inconclusivo e o app pede uma nova foto.
- **Atenção:** a avaliação é **exploratória**. O conjunto de teste já havia sido consultado durante o desenvolvimento e tem vínculos com as outras partições ([seção 10.1](docs/Projeto.md#101-independência-dos-conjuntos-de-dados)). Os números não comprovam o desempenho em fotos novas de campo.

---

## Estrutura do projeto

```text
.
├── assets/
│   ├── data/            # Evidências por tarefa (T3.x–T15.x): índices, métricas, matrizes, benchmarks, manifestos
│   ├── modelos/         # Modelos treinados (.keras), convertidos (.tflite) e seus contratos
│   ├── revisão_imagens/ # Amostras usadas na revisão visual e nos testes de preprocessing
│   └── *.png, *.jpg     # Figuras da documentação (canvas, personas, jornadas, matriz de risco)
├── docs/                # Documentação: Projeto.md (completa) e guias/relatórios por tarefa
├── frontend/            # Aplicação de demonstração (React + TypeScript + Vite + LiteRT.js)
│   ├── dist/            # Build pronto da versão 1.0.0, usado nos relatórios de avaliação
│   ├── public/          # Modelos web, runtime WASM e identidade visual servidos pela aplicação
│   ├── scripts/         # Preparação de modelos, empacotamento da demo e service worker
│   ├── src/             # Código da interface, preprocessing, inferência e política de confiança
│   └── tests/           # Testes ponta a ponta (Playwright) e fixtures
├── notebooks/           # Notebooks das etapas de padronização, particionamento e aumento de dados
├── src/                 # Pipeline Python: preparação, treino, avaliação, conversão e análises
├── tests/               # Validações automatizadas do pipeline Python
├── requirements.txt            # Análise de dados e notebooks
├── requirements-treino.txt     # Treinamento e conversão (TensorFlow 2.21, Keras 3.15, KerasHub)
└── requirements-benchmark.txt  # Ambiente mínimo para o benchmark de inferência
```

Os nomes de arquivos e pastas carregam o código da tarefa que os gerou (por exemplo, `T7_3` é a tarefa 7.3, quantização INT8). Assim, cada artefato pode ser localizado na seção de mesmo número em [`docs/Projeto.md`](docs/Projeto.md).

> **As imagens originais não estão no Git.** O repositório guarda os índices, hashes e metadados que identificam cada foto. Para treinar novamente, é preciso obter o acervo e preservar os caminhos relativos descritos na [ficha do dataset](docs/T14_1_Dataset_Final.md).

---

## Pré-requisitos

- [Node.js](https://nodejs.org/) 22.12+ ou 24 LTS e npm, para a aplicação
- [Python](https://www.python.org/) 3.12, para treinamento, avaliação e conversão
- Git
- Acervo de imagens original, somente para treinar ou avaliar novamente

No Windows (PowerShell), use `npm.cmd` no lugar de `npm` se a política de execução bloquear scripts.

---

## Rodando a demonstração

Instale as dependências e inicie o servidor de desenvolvimento:

```bash
cd frontend
npm install
npm run dev
```

Abra `http://127.0.0.1:5173` e envie uma foto. O comando confere os hashes dos modelos, prepara os arquivos web e carrega o modelo no navegador. Nenhuma foto é enviada para servidor.

Para gerar e servir o build de produção, que inclui o funcionamento offline:

```bash
npm run build
npm run preview
```

Para testar no celular, publique a pasta `frontend/dist/` em um host estático com **HTTPS**. Detalhes de hospedagem, modo offline e congelamento do pacote de demonstração estão no [README do frontend](frontend/README.md).

---

## Reproduzindo treinamento, avaliação e conversão

Crie o ambiente na raiz do repositório:

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-treino.txt
export KERAS_BACKEND=tensorflow  # PowerShell: $env:KERAS_BACKEND = "tensorflow"
```

Treinar novamente sobre o mesmo recorte do modelo entregue:

```bash
python -m src.treinamento_t5_1 \
  --config assets/modelos/candidato_T5_6_20261026/configuracao_treino.json \
  --raiz-imagens /caminho/para/o/acervo \
  --indice assets/data/treino_T5_2/indice_dataset.csv \
  --pesos assets/data/treino_T5_2/pesos_dataset.json \
  --saida runs/reproducao
```

A sequência completa, com avaliação, conversão Float16/INT8 e atualização da aplicação, está nos guias [T14.2](docs/T14_2_Pipeline_Treinamento.md), [T14.3](docs/T14_3_Avaliacao_Conversao.md) e [T14.5](docs/T14_5_Guia_Retreinamento.md). Os guias trazem os comandos em PowerShell, o ambiente usado pela equipe.

---

## Rodando os testes

Pipeline Python, na raiz. Cada arquivo em `tests/` valida o código e os artefatos de uma tarefa e pode ser executado sozinho:

```bash
pip install -r requirements-treino.txt
python tests/validar_preprocessamento.py   # exemplo; troque pelo arquivo da tarefa
```

Aplicação, dentro de `frontend/`:

```bash
npm test                          # testes unitários (Vitest)
npx playwright install chromium   # apenas na primeira vez
npm run test:e2e                  # testes ponta a ponta, incluindo o modo offline
```

---

## Limitações e pendências

O [checklist final (T15.1)](docs/T15_1_Checklist_Final.md) traz a situação de cada requisito. Os pontos principais são:

- **Generalização não comprovada:** falta um conjunto de teste independente, coletado depois de congelar o modelo.
- **Acurácia entre os resultados aceitos:** 0,882, abaixo da meta de 0,90 definida na política de confiança (T6.5).
- **Conteúdo técnico:** as 13 fichas exibidas no app foram redigidas pela equipe, com as fontes citadas ([seção 13.1](docs/Projeto.md#131-fichas-técnicas-da-equipe-e-decisão-formal-t131)). Elas são informativas e não têm validação agronômica do Agro App.
- **Testes no aparelho:** faltam a matriz completa de dispositivos (T12.3), a medição de memória e 50 capturas ponta a ponta no aparelho de referência.
- **Limites de tamanho e latência:** os valores usados são propostas da equipe e precisam ser ratificados com o parceiro.
- **Validação com o parceiro:** a apresentação, a ata e o aceite estão registrados como pendentes em [T15.3](docs/T15_3_Entrega_Parceiro.md).

---

## Convenções do repositório

- **Branches:** `main` guarda a versão entregue e `develop` integra o trabalho. Cada tarefa usa uma branch `feat/…`, `docs/…`, `task/…` ou `chore/…` e entra na `develop` por pull request.
- **Commits:** formato `tipo(tarefa): descrição` em português, por exemplo `feat(t7.3): calibra candidato em INT8`.
- **Rastreabilidade:** o código da tarefa (`T4.5`, `T11.1`…) aparece no nome dos scripts em `src/`, das pastas em `assets/data/` e das seções de `docs/Projeto.md`.
- **Integridade:** modelos, índices e builds são conferidos por SHA-256. O `.gitattributes` fixa `eol=lf` para que os hashes coincidam entre sistemas operacionais.

---

## Equipe

Projeto da **AgroTech Inteli**, liga estudantil de tecnologia para o agronegócio do Inteli, 2º semestre de 2026.

- Tobias Viana (Product Owner)
- Ana Célia
- Glauco
- João Fernandes
- Karol Barbosa
- Lucas Cerdeira
- Rui

Contato: agrotech@inteli.edu.br

---

## Uso e licença

O código e a documentação deste repositório estão sob a [licença MIT](LICENSE), com copyright da AgroTech Inteli. O Agro App, ou qualquer pessoa, pode usar, modificar e redistribuir o MVP, desde que mantenha o aviso de copyright e o texto da licença.

A licença MIT não se aplica às imagens de bases públicas, que mantêm as licenças de origem registradas na [ficha do dataset](docs/T14_1_Dataset_Final.md). Antes de usar o acervo ou os modelos treinados com ele, confira essas licenças, principalmente se o uso for comercial.
