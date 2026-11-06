# T8.2 — Benchmark de inferência

Foram medidas as seis versões TFLite disponíveis nas rodadas T5.6:
EfficientNet-Lite0, MobileNetV3Large e MobileNetV2, em FP32 e INT8.
O candidato versionado é o EfficientNet-Lite0 INT8; sua cópia na pasta
`candidato_T5_6_20261026` não constitui outra versão e não é medida novamente.
Os checkpoints `.keras` são arquivos de treinamento/auditoria e não representam
o pacote de execução móvel comparado aqui.

## Método e reprodução

Executar na raiz do repositório, com `requirements-treino.txt` instalado:

```powershell
.\.venv-treino\Scripts\python.exe -m src.benchmark_t8_2 --saida assets/data/benchmark_T8_2 --threads 1 --aquecimento 20 --repeticoes 100
.\.venv-treino\Scripts\python.exe tests/validar_benchmark_t8_2.py
```

Para repetir, usar uma nova pasta de saída: o comando preserva medições existentes.
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
validade das amostras e recálculo dos percentis publicados.

## Resultados medidos

Medição em 06/11/2026. CPU: `Intel64 Family 6 Model 186 Stepping 3, GenuineIntel`; 12 processadores lógicos.
Sistema: Windows-11-10.0.26300-SP0; Python 3.13.5, TensorFlow 2.21.0 e NumPy 2.4.4.

| Arquitetura | Versão | Bytes | MB | Média (ms) | p50 (ms) | p95 (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| efficientnet_lite0 | FP32 | 13531184 | 13.531 | 310.68 | 385.24 | 419.07 |
| efficientnet_lite0 | INT8 | 4003624 | 4.004 | 1988.00 | 1097.12 | 3494.05 |
| mobilenet_v3_large | FP32 | 11976784 | 11.977 | 67.56 | 65.08 | 82.67 |
| mobilenet_v3_large | INT8 | 3534344 | 3.534 | 594.72 | 589.82 | 626.93 |
| mobilenet_v2 | FP32 | 8955404 | 8.955 | 80.10 | 80.06 | 85.17 |
| mobilenet_v2 | INT8 | 2750824 | 2.751 | 791.95 | 787.06 | 834.41 |

Redução do tamanho de FP32 para INT8, por arquitetura:

- efficientnet_lite0: 70.4%.
- mobilenet_v3_large: 70.5%.
- mobilenet_v2: 69.3%.

Todos os INT8 ficam abaixo do limite proposto de 8 MB; todos os FP32 o excedem.
Nesta sessão, as três versões INT8 apresentaram maior latência que as FP32.
O candidato EfficientNet-Lite0 INT8 ocupa 4,004 MB. Sua latência local reforça a
necessidade de avaliar kernels/delegates no aparelho antes de aprovar o embarque.

## Interpretação para uso móvel

O custo observado contempla armazenamento do modelo e latência de execução na
CPU local. A redução de arquivo INT8 não garante aceleração: o resultado depende
dos kernels, do processador e dos delegates usados na aplicação.
Nenhum modelo é selecionado novamente com base neste benchmark; qualidade de
classificação e escolha do candidato permanecem documentadas na T5.6.

As medições atendem à comparação local de tempos e tamanhos da T8.2. A meta
RNF-04 (p95 ≤ 300 ms) deve ser verificada separadamente no celular de referência,
com o runtime e os delegates da aplicação. Estes números não certificam essa
meta e não permitem estimar bateria, aquecimento, memória máxima ou custo
financeiro. Para concluir a avaliação no aparelho, repetir o protocolo no mesmo
dispositivo, controlar carga concorrente e condições térmicas, registrar versão
do sistema/runtime, threads e delegates, e conservar as amostras. O tempo de
captura, decodificação e preprocessamento deve ser medido separadamente para
avaliar a espera total do usuário. Há uma única sessão por versão; ordem fixa,
carga do sistema e variação térmica podem influenciar os resultados locais.
