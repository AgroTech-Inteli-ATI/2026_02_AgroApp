# Comparação das estratégias de quantização — T7.2

Candidato: EfficientNet-Lite0 do pacote `candidato_T5_6_20261026` (Keras `089a8d903a78…`).

INT8 regenerada nesta etapa com o conjunto de calibração da T7.3: difere em bytes do artefato T7.3 (ambos avaliados abaixo).

## Tamanho (RNF-01: até 8 MB)

| Estratégia | Entrada/saída | Tamanho (bytes) | Redução vs FP32 | Até 8 MB |
| --- | --- | ---: | ---: | --- |
| FP32 (referência, T7.1) | float32/float32 | 13.531.184 | 0,0% | **não** |
| Faixa dinâmica | float32/float32 | 3.753.152 | 72,3% | sim |
| Float16 | float32/float32 | 6.833.548 | 49,5% | sim |
| INT8 inteira (regenerada na T7.2) | int8/int8 | 4.003.624 | 70,4% | sim |
| INT8 inteira (artefato T7.3) | int8/int8 | 4.003.624 | 70,4% | sim |

## Latência no CPU local — mediana / p95 (ms)

| Estratégia | xnnpack 1t | xnnpack 2t | xnnpack 4t | sem delegate 1t | sem delegate 4t |
| --- | ---: | ---: | ---: | ---: | ---: |
| FP32 (referência, T7.1) | 8,12 / 9,86 | 7,00 / 12,54 | 6,31 / 7,24 | 58,99 / 140,81 | 51,88 / 126,64 |
| Faixa dinâmica | 38,74 / 43,05 | 57,90 / 110,59 | 107,10 / 157,24 | 477,41 / 1020,15 | 264,56 / 356,24 |
| Float16 | 8,34 / 10,46 | 9,86 / 13,29 | 5,68 / 6,83 | 102,82 / 148,64 | 70,48 / 124,68 |
| INT8 inteira (regenerada na T7.2) | 5,90 / 7,38 | 6,25 / 8,78 | 3,98 / 4,67 | 905,69 / 1197,11 | 308,82 / 410,21 |
| INT8 inteira (artefato T7.3) | 5,67 / 7,34 | 5,43 / 7,86 | 4,05 / 4,77 | 542,62 / 1180,87 | 293,01 / 348,73 |

## Desempenho — validação (partição principal), 474 imagens

| Estratégia | F1 macro | Δ F1 vs FP32 | IC 95% Δ F1 | Acurácia macro | Δ acurácia macro (p.p.) | IC 95% Δ (p.p.) | RNF-06 (≥ −2 p.p.) | Acurácia | Divergências top-1 | McNemar p | Maior queda de F1 por classe |
| --- | ---: | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |
| FP32 (referência, T7.1) | 0,7811 | +0,0000 | — | 0,7550 | +0,00 | — | — | 0,8565 | 0 | — | — |
| Faixa dinâmica | 0,7755 | -0,0056 | [-0,0296; 0,0169] | 0,7517 | -0,33 | [-2,48; 1,98] | sim (IC: **não**) | 0,8565 | 9 | 1,000 | Percevejo-verde (Nezara viridula) (-0,121) |
| Float16 | 0,7830 | +0,0019 | [0,0000; 0,0062] | 0,7563 | +0,13 | [0,00; 0,40] | sim (IC: sim) | 0,8587 | 1 | 1,000 | — |
| INT8 inteira (regenerada na T7.2) | 0,7832 | +0,0021 | [-0,0259; 0,0317] | 0,7578 | +0,28 | [-2,48; 3,20] | sim (IC: **não**) | 0,8587 | 14 | 1,000 | Percevejo-verde (Nezara viridula) (-0,107) |
| INT8 inteira (artefato T7.3) | 0,7767 | -0,0044 | [-0,0373; 0,0293] | 0,7528 | -0,22 | [-3,26; 2,93] | sim (IC: **não**) | 0,8587 | 15 | 1,000 | Percevejo-verde (Nezara viridula) (-0,167) |

F1 macro do checkpoint Keras na mesma partição: 0,7811.

## Desempenho — teste (exploratório, já consultado), 473 imagens

| Estratégia | F1 macro | Δ F1 vs FP32 | IC 95% Δ F1 | Acurácia macro | Δ acurácia macro (p.p.) | IC 95% Δ (p.p.) | RNF-06 (≥ −2 p.p.) | Acurácia | Divergências top-1 | McNemar p | Maior queda de F1 por classe |
| --- | ---: | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |
| FP32 (referência, T7.1) | 0,7329 | +0,0000 | — | 0,7126 | +0,00 | — | — | 0,8478 | 0 | — | — |
| Faixa dinâmica | 0,7371 | +0,0041 | [-0,0063; 0,0188] | 0,7127 | +0,01 | [-0,65; 0,76] | sim (IC: sim) | 0,8478 | 7 | 1,000 | Lagarta-do-cartucho (Spodoptera frugiperda) (-0,029) |
| Float16 | 0,7329 | +0,0000 | [0,0000; 0,0000] | 0,7126 | +0,00 | [0,00; 0,00] | sim (IC: sim) | 0,8478 | 0 | 1,000 | — |
| INT8 inteira (regenerada na T7.2) | 0,7471 | +0,0142 | [-0,0052; 0,0387] | 0,7270 | +1,44 | [-0,24; 3,52] | sim (IC: sim) | 0,8541 | 14 | 0,549 | Lagarta-falsa-medideira (Chrysodeixis includens) (-0,026) |
| INT8 inteira (artefato T7.3) | 0,7400 | +0,0071 | [-0,0121; 0,0315] | 0,7234 | +1,08 | [-0,57; 3,18] | sim (IC: sim) | 0,8436 | 15 | 0,774 | Lagarta-falsa-medideira (Chrysodeixis includens) (-0,026) |

F1 macro do checkpoint Keras na mesma partição: 0,7329.

## Execução sem delegates (RNF-09)

| Estratégia | Executou com saídas válidas | Top-1 igual ao XNNPACK | Erro abs. máx. vs XNNPACK |
| --- | --- | ---: | ---: |
| FP32 (referência, T7.1) | sim | 100,0% | 0,000004 |
| Faixa dinâmica | sim | 92,3% | 0,121471 |
| Float16 | sim | 100,0% | 0,000004 |
| INT8 inteira (regenerada na T7.2) | sim | 92,3% | 0,089844 |
| INT8 inteira (artefato T7.3) | sim | 100,0% | 0,121094 |

## Ambiente e limites

Windows-11-10.0.26200-SP0; Intel(R) Core(TM) Ultra 5 235U; alimentação: tomada; Python 3.12.10; TensorFlow 2.21.0.
tempo de set_tensor + invoke + get_tensor (inclui (des)quantização INT8) em uma imagem real 1x224x224x3, tf.lite.Interpreter.
latência medida no CPU x86 de desenvolvimento, não no celular de referência; serve para comparar estratégias entre si e não aprova o RNF-04. O teste já foi consultado em etapas anteriores e é apenas exploratório; nenhuma estratégia foi escolhida por ele. Intervalos por bootstrap de imagens não consideram a dependência entre fotos do mesmo grupo. Scores não são probabilidades calibradas.
