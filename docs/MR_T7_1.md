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

## Dependência para concluir o aceite

O repositório contém o pipeline de treinamento, mas não contém a rodada final
treinada nem as imagens originais para produzi-la. É necessário disponibilizar
`melhor_modelo.keras` e `metricas_validacao.json` da rodada selecionada e executar
a conversão para concluir o aceite experimental. Modelos sintéticos usados nos
testes não representam um classificador agrícola treinado.

Este MR deve permanecer como **rascunho** até essa execução. A implementação
do fluxo e a validação de integração podem ser revisadas independentemente.

## Validação executada em 03/11/2026

- T7.1: sete testes passaram, sem testes pulados. Incluem conversão real,
  carregamento e inferência de um Keras sintético e da MobileNetV3Small do
  pipeline T5.1 com pesos aleatórios, além de casos de recusa e preservação.
- T6.1: sete testes passaram.
- T4.1: formato, faixa, proporção, EXIF, modos de cor e determinismo passaram.
- `pip check`: nenhuma dependência incompatível.
- `git diff --check`: sem erros.

Ambiente da conversão: Windows, Python 3.13.5, TensorFlow 2.21.0,
Keras 3.15.1 e KerasHub 0.32.0. Os modelos usados na integração são temporários
e não são entregues como modelo final.
