# T8.2 — Coleta histórica T5.6

Este registro descreve a coleta anterior. A revisão atual e os comandos vigentes estão no [relatório principal](Benchmark_T8_2.md). Os JSON e CSV históricos foram preservados.

Foram medidas seis versões TFLite das rodadas T5.6:
EfficientNet-Lite0, MobileNetV3Large e MobileNetV2, em FP32 e INT8.
O INT8 do pacote `candidato_T5_6_20261026` é uma cópia do artefato T5.6 medido,
conforme o hash, e não foi contado novamente.

**Esta coleta não mediu o INT8 oficial da T7.3 nem o FP32 da T7.1.** Embora
tenham os mesmos tamanhos dos arquivos T5.6 correspondentes, seus hashes são
diferentes. Também não foram medidas a faixa dinâmica, o float16 e a versão
INT8 regenerada na T7.2. O resultado descreve as rodadas T5.6 e não substitui
o benchmark das conversões previstas nas dependências da T8.2.

## Método e resultados da coleta histórica

Os modelos são executados sequencialmente, no mesmo processo e runtime, CPU,
uma thread, sem delegates, batch 1 e entrada RGB 224 × 224. Cada versão recebe
os mesmos pixels sintéticos uniformes em [0,1], semente 42, convertidos ao dtype
de entrada conforme os parâmetros de quantização do próprio modelo.
São descartadas 20 inferências de aquecimento antes das 100 cronometradas.

O relógio `perf_counter_ns` mede `set_tensor + invoke + get_tensor`.
Leitura de arquivo, criação do interpretador, alocação, geração e quantização da
entrada ficam fora desse tempo. A alocação é registrada separadamente no JSON;
não é uma medida completa de inicialização. O tamanho é o número exato de bytes
do `.tflite` em disco; MB = 1.000.000 bytes. Não representa RAM de execução.

O [JSON com evidências](../assets/data/benchmark_T8_2/resultados.json) registra
hardware, sistema, versões, parâmetros, hashes SHA-256 e todas as durações.
O [CSV](../assets/data/benchmark_T8_2/resumo.csv) facilita novas comparações.
O teste confere cobertura das seis versões, hashes, tamanhos, quantidade e
validade das amostras e recálculo dos percentis publicados. Ele não executa
inferências nem verifica a estabilidade das condições durante a coleta.

## Resultados medidos

Medição em 06/11/2026. CPU: `Intel64 Family 6 Model 186 Stepping 3, GenuineIntel`; 12 processadores lógicos.
Sistema: Windows-11-10.0.26300-SP0; Python 3.13.5, TensorFlow 2.21.0 e NumPy 2.4.4.

| Arquitetura | Versão | Bytes | MB | Média (ms) | p50 (ms) | p95 (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| EfficientNet-Lite0 | FP32 | 13.531.184 | 13,531 | 310,68 | 385,24 | 419,07 |
| EfficientNet-Lite0 | INT8 | 4.003.624 | 4,004 | 1.988,00 | 1.097,12 | 3.494,05 |
| MobileNetV3-Large | FP32 | 11.976.784 | 11,977 | 67,56 | 65,08 | 82,67 |
| MobileNetV3-Large | INT8 | 3.534.344 | 3,534 | 594,72 | 589,82 | 626,93 |
| MobileNetV2 | FP32 | 8.955.404 | 8,955 | 80,10 | 80,06 | 85,17 |
| MobileNetV2 | INT8 | 2.750.824 | 2,751 | 791,95 | 787,06 | 834,41 |

Redução do tamanho de FP32 para INT8, por arquitetura:

- EfficientNet-Lite0: 70,4%.
- MobileNetV3-Large: 70,5%.
- MobileNetV2: 69,3%.

Todos os INT8 ficam abaixo do limite proposto de 8 MB; todos os FP32 o excedem.
Nesta sessão, as três versões INT8 apresentaram maior latência que as FP32.
O EfficientNet-Lite0 INT8 **da T5.6** ocupa 4,004 MB. Essa medição não corresponde
ao arquivo INT8 oficial exportado na T7.3.

### Variação durante a coleta

Os tempos do Lite0 variaram ao longo das 100 execuções. No FP32, a mediana das
primeiras 25 foi **393,65 ms**, contra **115,75 ms** nas últimas 25. No INT8,
as amostras variaram de **954,05 a 3.642,91 ms**. As estatísticas da tabela
conferem com essas amostras, mas não demonstram execução em condições estáveis.

O registro não informa alimentação por bateria/tomada, temperatura ou carga
concorrente. Não é possível atribuir a variação a uma causa específica.
A coleta deve ser repetida em sessões independentes, alternando a ordem dos
modelos e registrando essas condições antes de comparar seu desempenho.

Os valores também não são diretamente comparáveis aos da T7.2: mudam o
hardware, os artefatos e a configuração de execução. A T7.2 inclui
(des)quantização no tempo do INT8; esta coleta deixa a quantização da entrada
fora do intervalo e lê a saída sem desquantizá-la.

## Interpretação para uso móvel

O custo observado contempla armazenamento do modelo e latência de execução na
CPU local. A redução de arquivo INT8 não garante aceleração: o resultado depende
dos kernels, do processador e dos delegates usados na aplicação.
Nenhum modelo é selecionado novamente com base neste benchmark; qualidade de
classificação e escolha do candidato permanecem documentadas na T5.6.

Os arquivos documentam tempos e tamanhos das seis versões T5.6 nesta sessão.
Permanecem pendentes a medição das conversões T7.1–T7.3 e a repetição da coleta
sob condições estáveis. A meta RNF-04 (p95 ≤ 300 ms) deve ser verificada
separadamente no celular de referência, com a
[ferramenta de benchmark do LiteRT](https://developers.google.com/edge/litert/models/measurement),
com o runtime e os delegates da aplicação. Estes números não certificam essa
meta e não permitem estimar bateria, aquecimento, memória máxima ou custo
financeiro. Para concluir a avaliação no aparelho, repetir o protocolo no mesmo
dispositivo, controlar carga concorrente e condições térmicas, registrar versão
do sistema/runtime, threads e delegates, e conservar as amostras. O tempo de
captura, decodificação e preprocessamento deve ser medido separadamente para
avaliar a espera total do usuário. Há uma única sessão por versão; ordem fixa,
carga do sistema e variação térmica podem influenciar os resultados locais.
