# Product

<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
React, TypeScript e Vite. Inferência local com LiteRT.js, sem backend.

## Users
Equipe do AgroApp, testando fotografias no computador e no celular.

## Product Purpose
Receber uma fotografia, prepará-la conforme o treinamento e apresentar as três classes mais prováveis do modelo de reconhecimento de pragas.

## Capabilities and Constraints
- Candidato EfficientNet-Lite0, 13 classes, versão oficial 1.0.0: Float16 T7.2 como principal e INT8 T7.3 como contingência (decisão T8.3, consolidada na T10.4).
- Análise real no navegador; sem execução de notebooks, envio da foto, login ou persistência de histórico.
- Conexão necessária para carregar a aplicação. Modo offline e PWA fora do escopo.
- Conteúdo técnico depende de revisão e catálogo oficial; não inventar manejo nem limiares de confiança.
- Preservar a fotografia inteira no processamento 224 × 224, preenchendo com cinza.

## Brand Commitments
Usar a apresentação fornecida pelo usuário como referência visual: verde #00cf89, azul #253253, branco, Poppins e a marca AgroAPP. A referência não altera a decisão explícita de excluir modo offline.

## Evidence on Hand
Classes e manifesto em assets/modelos/candidato_T5_6_20261026 (o modelo_int8.tflite dessa pasta é o pacote histórico da T5.6, não o embarcado). Modelo principal em assets/modelos/comparacao_T7_2_candidato_T5_6_20261026/modelo_float16.tflite; contingência em assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite; decisão em assets/data/selecao_T8_3/decisao.json. Pré-processamento Python em src/preprocessamento.py. Catálogo de recomendações oficial ausente.

## Accessibility & Inclusion
Português brasileiro, navegação por teclado, mensagens acessíveis de estado e interface responsiva.
