# Seleção do modelo para o aplicativo móvel (T8.3)

**Escolhido:** Float16 (T7.2) — `assets/modelos/comparacao_T7_2_candidato_T5_6_20261026/modelo_float16.tflite` (6.833.548 bytes; SHA-256 `c9a26ce13806a2fa26bffbd8cfbdac83ff4c05ffff1009ca9483bb587a5a8fa2`).
**Contingência:** INT8 oficial (T7.3) — `assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite`. Se, no aparelho de referência, o escolhido violar RNF-04 (p95 > 300 ms) ou RNF-07 (memória).

| Versão | MB | Elegível | F1 macro (val.) | IC95 inf. Δ acur. macro (p.p.) | Pior queda de F1 por classe | p95 local (ms) |
| --- | ---: | :---: | ---: | ---: | --- | ---: |
| FP32 (T7.1) | 13,53 | não | 0,7811 | 0,00 | 0,0 p.p. (classe 0, n=157) | 16,03 |
| Faixa dinâmica (T7.2) | 3,75 | sim | 0,7755 | -2,48 | -12,1 p.p. (classe 5, n=14) | 71,97 |
| Float16 (T7.2) | 6,83 | sim | 0,7830 | 0,00 | 0,0 p.p. (classe 0, n=157) | 13,93 |
| INT8 oficial (T7.3) | 4,00 | sim | 0,7767 | -3,26 | -16,7 p.p. (classe 5, n=14) | 10,03 |
| INT8 regenerado (T7.2) | 4,00 | sim | 0,7832 | -2,48 | -10,7 p.p. (classe 5, n=14) | 12,67 |

T8.1: nao_integrada. T8.1 fora da árvore; os números vêm das previsões da T7.2, que ela também usa.
