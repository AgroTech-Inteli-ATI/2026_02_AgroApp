# T7.1 — Conversão e validação de modelos TFLite

## Descrição

Adiciona um comando para converter o checkpoint Keras da rodada selecionada
em `modelo.tflite`, usando `tf.lite.TFLiteConverter`. O comando carrega o
FlatBuffer do disco, executa inferências e compara numericamente as saídas
com o modelo Keras antes de gravar os artefatos definitivos.

Gera o contrato de entrada e saída a partir do interpretador, com shapes,
assinaturas, tipos, ordem das classes, preprocessamento, hashes e erros por
amostra. Preserva conversões existentes e aceita fotos adicionais pela opção
`--imagem`. A conversão usa float32 e operadores TFLite nativos.

## Como executar

```bash
python -m pip install -r requirements-treino.txt
python -m src.conversao_t7_1 --rodada runs/<rodada_selecionada> --saida runs/<rodada_selecionada>/tflite
python tests/validar_conversao_t7_1.py
```

## Origem e classes

O comando confere o checkpoint e o arquivo de métricas contra o manifesto do
pacote selecionado na T5.6. Os nomes e índices precisam coincidir com o
`classes.json` auditado. Trocar nomes mantendo os índices sequenciais, substituir
o checkpoint, misturar métricas de outra rodada ou alterar o pacote interrompe
a conversão antes de qualquer saída. O contrato registra os hashes da seleção.

## Entrega do candidato oficial — 04/11/2026

A conversão real foi executada com
`assets/modelos/rodadas_T5_6_20261026/20261026-213017_efficientnet_lite0_s42/`,
cujo checkpoint corresponde ao pacote `candidato_T5_6_20261026`.

Os três arquivos estão em
[`assets/modelos/conversao_T7_1_candidato_T5_6_20261026/`](../assets/modelos/conversao_T7_1_candidato_T5_6_20261026/):

- `modelo.tflite`, FP32, com 13.531.184 bytes.
- `contrato_tensores.json`, com evidência de carregamento, execução e comparação Keras/TFLite.
- `relatorio_conversao.md`, com formatos, classes, preprocessamento e hashes.

Entrada real `[1, 224, 224, 3]` e saída `[1, 13]`, ambas float32. A inferência
nas três entradas sintéticas passou nas tolerâncias `atol=1e-5`, `rtol=1e-4`.
Isso verifica funcionamento da conversão; não mede qualidade diagnóstica ou
latência no celular. A conversão FP32 não substitui o artefato INT8 da T5.6.

Para reproduzir em uma saída nova:

```bash
python -m src.conversao_t7_1 --rodada assets/modelos/rodadas_T5_6_20261026/20261026-213017_efficientnet_lite0_s42 --pacote assets/modelos/candidato_T5_6_20261026 --saida runs/reproducao_T7_1
```

## Validação

- T7.1: 11 testes passaram, sem testes pulados, incluindo os casos de troca de
  nomes, checkpoint substituído, métricas de outra rodada e pacote alterado.
- Conversão, carregamento e execução do candidato agrícola selecionado concluídos.
- `git diff --check`: sem erros.

Ambiente: macOS arm64, Python 3.12.15, TensorFlow 2.21.0, Keras 3.15.1,
KerasHub 0.32.0 e NumPy 2.4.4. Modelos sintéticos permanecem restritos aos testes.
