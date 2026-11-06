# Avaliação pós-conversão — T8.1

**473 imagens de teste; 13 classes; referência principal: Keras original.**

Métricas recalculadas a partir das previsões salvas da T7.2, pareadas por image_id e conferidas com a T6.1. Nenhum modelo foi executado novamente nesta etapa. Valores abaixo arredondados a quatro casas; deltas calculados antes do arredondamento.

## Métricas gerais

| Versão | F1 macro | Balanced accuracy | Acurácia | Δ F1 vs Keras (p.p.) | Δ balanced accuracy vs Keras (p.p.) | Δ acurácia vs Keras (p.p.) | Acertos perdidos / ganhos vs Keras |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Keras original (T5.6/T6.1) | 0,7329 | 0,7126 | 0,8478 | +0,0000 | +0,0000 | +0,0000 | 0 / 0 |
| TFLite FP32 (T7.1) | 0,7329 | 0,7126 | 0,8478 | +0,0000 | +0,0000 | +0,0000 | 0 / 0 |
| Faixa dinâmica (T7.2) | 0,7371 | 0,7127 | 0,8478 | +0,4128 | +0,0050 | +0,0000 | 2 / 2 |
| Float16 (T7.2) | 0,7329 | 0,7126 | 0,8478 | +0,0000 | +0,0000 | +0,0000 | 0 / 0 |
| INT8 oficial (T7.3) | 0,7400 | 0,7234 | 0,8436 | +0,7091 | +1,0755 | -0,4228 | 7 / 5 |
| INT8 regenerado (T7.2) | 0,7471 | 0,7270 | 0,8541 | +1,4212 | +1,4392 | +0,6342 | 4 / 7 |

## Perdas por classe

Todas as classes, inclusive as sem queda, estão em comparacao_por_classe.csv. Para cada conversão, a tabela destaca a maior queda de F1 e a maior queda de recall frente ao Keras; empates são preservados.

| Versão | Métrica | Classe | Suporte | Keras | Convertido | Δ (p.p.) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| TFLite FP32 (T7.1) | f1 | Sem queda observada | — | — | — | — |
| TFLite FP32 (T7.1) | recall | Sem queda observada | — | — | — | — |
| Faixa dinâmica (T7.2) | f1 | Lagarta-do-cartucho (Spodoptera frugiperda) | 61 | 0,8594 | 0,8308 | -2,8606 |
| Faixa dinâmica (T7.2) | recall | Percevejo-barriga-verde (Dichelops/Diceraeus) | 42 | 0,8095 | 0,7857 | -2,3810 |
| Float16 (T7.2) | f1 | Sem queda observada | — | — | — | — |
| Float16 (T7.2) | recall | Sem queda observada | — | — | — | — |
| INT8 oficial (T7.3) | f1 | Lagarta-falsa-medideira (Chrysodeixis includens) | 12 | 0,4706 | 0,4444 | -2,6144 |
| INT8 oficial (T7.3) | recall | Percevejo-barriga-verde (Dichelops/Diceraeus) | 42 | 0,8095 | 0,7857 | -2,3810 |
| INT8 regenerado (T7.2) | f1 | Lagarta-falsa-medideira (Chrysodeixis includens) | 12 | 0,4706 | 0,4444 | -2,6144 |
| INT8 regenerado (T7.2) | recall | Percevejo-barriga-verde (Dichelops/Diceraeus) | 42 | 0,8095 | 0,7857 | -2,3810 |

## Protocolo e interpretação

- A referência principal é o checkpoint selecionado na T5.6, avaliado na T6.1. As previsões Keras da T7.2 coincidem por ID com as da T6.1.
- O CSV geral e o CSV por classe incluem deltas contra Keras e contra TFLite FP32. Deltas negativos indicam perda. Balanced accuracy é a média dos recalls e não é F1 macro.
- O protocolo de inferência herdado da T7.2 usa T4.1, sem augmentation, ponderação ou limiar de confiança. Não há mudança de pesos, calibração ou pré-processamento nesta consolidação.
- As matrizes mantêm a ordem das classes do candidato: linhas reais, colunas previstas. Os suportes são iguais entre as versões.
- mudancas_por_imagem.csv lista toda troca de argmax frente ao Keras, distinguindo acerto perdido, acerto ganho e erro alterado. Não descreve alterações de scores que preservam o argmax.
- Melhor média global pode coexistir com perdas por classe. Suportes pequenos limitam a interpretação; não se atribuem causas visuais sem revisar fotos.
- INT8 oficial T7.3 e INT8 regenerado T7.2 são artefatos distintos. Esta análise não substitui o oficial pelo modelo de maior F1 no teste.
- Esta etapa não calcula novos testes estatísticos. McNemar e os ICs da T7.2 têm FP32 como referência e não são usados como prova de equivalência ao Keras ou entre os dois INT8.

Teste exploratório, consultado em etapas anteriores; não é avaliação final independente. Não fundamenta seleção de modelo, ajuste de pesos ou limiares. Deltas descrevem esta amostra e não comprovam equivalência estatística nem atendimento definitivo ao RNF-06. Não houve nova inferência ou revisão visual.

Tamanho e latência estão na seção 7.2 de docs/Projeto.md; benchmark no aparelho pertence à T8.2 e seleção à T8.3.

## Artefatos

metricas_gerais.csv; comparacao_por_classe.csv; predicoes_teste.csv; mudancas_por_imagem.csv; matrizes/<versao>.csv; proveniencia.json.

## Reprodução

```bash
python -m src.avaliacao_pos_conversao_t8_1 --saida runs/reproducao_T8_1
python tests/validar_avaliacao_pos_conversao_t8_1.py
```
