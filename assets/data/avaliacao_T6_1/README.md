# Avaliação exploratória do candidato — T6.1

A pasta `candidato_T5_6_20261026_keras/` contém a avaliação do checkpoint
**Keras FP32 EfficientNet-Lite0 selecionado na T5.6**, executada em 27/10/2026
com o avaliador integrado pelo PR #28. Não houve alteração do código do
avaliador, retreino, troca de checkpoint ou ajuste de limiar a partir do teste.

| Indicador no teste | Resultado |
| --- | ---: |
| Macro F1 — métrica principal | 0,732928 |
| Balanced accuracy | 0,712632 |
| Acurácia — complementar | 0,847780 |
| Imagens | 473 |
| Classes avaliadas | 13/13 |

O índice é o recorte `assets/data/treino_T5_2/indice_dataset.csv`, usado no
treinamento do candidato; por isso há 473 fotos, em vez das 474 do índice
completo da T4.5. O hash do modelo corresponde ao `modelo.keras` do pacote
`assets/modelos/candidato_T5_6_20261026/`.

## Artefatos

- `metricas_teste.json`: métricas globais e por classe, matriz de confusão e
  hashes do modelo e do índice.
- `metricas_por_classe.csv`: precisão, recall, F1 e suporte das 13 classes.
- `predicoes_teste.csv`: rótulo real e previsto para cada uma das 473 fotos.
- `relatorio_teste.md`: relatório legível com macro F1 e métricas por classe.
- `proveniencia_avaliacao.json`: vínculo ao pacote T5.6 e à linha da T5.5,
  ambiente da avaliação, hashes dos relatórios e do código e contexto da execução.

As métricas das previsões salvas foram conferidas independentemente com
scikit-learn. O avaliador verificou os hashes das fotos e o isolamento das
partições; somente as imagens de teste foram abertas durante a inferência.

## Reprodução

Usar o ambiente de `requirements-treino.txt`; para executar os testes e a
conferência com scikit-learn, instalar também a versão declarada em
`requirements.txt`. Na raiz do projeto:

```bash
python -m src.avaliacao_t6_1 --rodada assets/modelos/rodadas_T5_6_20261026/20261026-213017_efficientnet_lite0_s42 --raiz-imagens /caminho/das/fontes --indice assets/data/treino_T5_2/indice_dataset.csv --saida runs/reproducao_T6_1_candidato_keras --batch 32
python tests/validar_avaliacao_t6_1.py
```

A raiz deve conter `dataset/`. Usar uma saída nova para preservar os relatórios.
A execução registrada utilizou quatro threads intraop e uma interop do TensorFlow.

## Limites

Estas métricas são **exploratórias**: a partição já foi consultada historicamente
na T5.3. O resultado não é uma avaliação final independente e não deve orientar
nova escolha de candidato ou ajuste de limiar de confiança. Um teste independente
exige novas imagens separadas por origem e a extensão do contrato do avaliador.

O modelo avaliado é o **checkpoint Keras**, não o `modelo_int8.tflite` destinado
ao embarque. As métricas de validação INT8 da T5.6 não são métricas de teste;
uma avaliação do arquivo convertido deve ser identificada separadamente.

Os menores F1 neste teste foram percevejo-verde (0,416667),
lagarta-falsa-medideira (0,470588) e percevejo-asa-preta (0,533333). Esses resultados,
com suportes de 14, 12 e 11 imagens, respectivamente, limitam a interpretação da
média global e devem ser considerados na análise de erros.
