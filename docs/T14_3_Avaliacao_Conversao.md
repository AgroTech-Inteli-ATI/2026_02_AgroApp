# T14.3 — Avaliação e conversão LiteRT/TFLite

Autora: Karol · Revisor: Rui · Meta de entrega: a definir.
Documentação implementada em 17/11/2026; revisão de Rui pendente.

## Pré-requisitos e escopo

Use o ambiente, a variável `$python`, o acervo `$imagens` e o checkpoint descritos em [T14.2](T14_2_Pipeline_Treinamento.md). Os comandos são executados na raiz. TFLite é o formato `.tflite` consumido pelo runtime LiteRT; a conversão usa o TensorFlow fixado no repositório. Para preservar evidências, use pastas de saída novas.

## Avaliar um novo treinamento

Defina `$rodada` como a pasta impressa pelo treino, contendo checkpoint, ambiente e métricas de validação:

```powershell
$rodada = "runs/novo_treino/SUBSTITUIR_PELA_PASTA_DA_RODADA"
& $python -m src.avaliacao_t6_1 --rodada $rodada --raiz-imagens $imagens --indice runs/novo_dataset/indice_pipeline.csv --batch 32 --saida runs/avaliacao_nova
```

[avaliacao_t6_1.py](../src/avaliacao_t6_1.py) exige o mesmo hash de índice usado no treinamento, confere classes, IDs, ausência de grupos/hashes compartilhados entre partições e hashes das fotos de teste. Carrega `melhor_modelo.keras`, aplica o mesmo preprocessing e usa argmax dos scores. Gera `metricas_teste.json`, `metricas_por_classe.csv`, `predicoes_teste.csv` e `relatorio_teste.md`. [avaliacao.py](../src/avaliacao.py) define F1 macro, precisão, recall, suporte e matriz de confusão; mantenha sua convenção para classes sem suporte ao comparar execuções.

Selecione hiperparâmetros, modelo e limiar pela validação; consulte o teste independente somente depois de congelar essas decisões. Os resultados históricos T6/T8 usam teste já consultado e são exploratórios. Evidências: [avaliação Keras T6.1](../assets/data/avaliacao_T6_1/candidato_T5_6_20261026_keras/relatorio_teste.md) e [avaliação pós-conversão T8.1](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/relatorio_avaliacao.md).

## Reprodução das conversões históricas

Os CLIs abaixo conferem a seleção T5.6, hashes e ordem das 13 classes; não são exportadores genéricos para qualquer novo checkpoint. O `--rodada` da T7.1 deve apontar para a rodada original T5.1 que originou o candidato, com `melhor_modelo.keras` e `metricas_validacao.json`. O pacote de distribuição usa nomes diferentes (`modelo.keras`, `avaliacao_validacao.json`) e não deve ser passado diretamente como rodada.

```powershell
$rodadaHistorica = "C:\dados\rodadas_T5_6_20261026\20261026-213017_efficientnet_lite0_s42"
& $python -m src.conversao_t7_1 --rodada $rodadaHistorica --pacote assets/modelos/candidato_T5_6_20261026 --saida runs/repro_fp32
& $python -m src.quantizacao_t7_3 converter --raiz-imagens $imagens --conjunto assets/data/calibracao_T7_3 --saida runs/repro_int8
& $python -m src.comparacao_quantizacao_t7_2 --raiz-imagens $imagens --saida runs/repro_comparacao --sem-teste --rodadas 5 --por-rodada 40 --reamostras 2000
```

A T7.1 gera `modelo.tflite`, contrato e relatório sem quantização e com operadores TFLite nativos. `--imagem` é opcional e repetível para smoke test. A T7.3 gera `modelo_int8.tflite`, `contrato_int8.json` e relatório. A T7.2 gera Float16, faixa dinâmica e INT8 regenerado, mais `comparacao.json`, `tabela_comparativa.csv`, `metricas_por_classe.csv`, `predicoes.csv` e relatório. Seus defaults leem o pacote T5.6, o índice T5.2, o conjunto T7.3 e o FP32 publicado em T7.1; o FP32 recém-gerado em `runs/repro_fp32` não é incorporado automaticamente. A reprodução requer também os artefatos publicados de referência.

## Quantização

| Estratégia | Configuração do conversor | Entrada / saída |
| --- | --- | --- |
| FP32 T7.1 | `TFLiteConverter.from_keras_model`, `TFLITE_BUILTINS` | float32 / float32 |
| Float16 T7.2 | `optimizations=[Optimize.DEFAULT]`, `target_spec.supported_types=[tf.float16]` | float32 / float32; pesos float16 |
| INT8 T7.3 | `Optimize.DEFAULT`, `representative_dataset`, `supported_ops=[TFLITE_BUILTINS_INT8]`, `inference_input_type=tf.int8`, `inference_output_type=tf.int8` | int8 / int8 |

Fontes: [conversao_t7_1.py](../src/conversao_t7_1.py), [comparacao_quantizacao_t7_2.py](../src/comparacao_quantizacao_t7_2.py) e [quantizacao_t7_3.py](../src/quantizacao_t7_3.py). Float16 não exige calibração. No INT8, o gerador fornece somente imagens float32 `[1,224,224,3]` em `[0,1]`, sem augmentation, antes da conversão interna do backbone.

O [conjunto T7.3](../assets/data/calibracao_T7_3/README.md) contém 200 imagens reais exclusivamente de treino, semente 42, 15 ou 16 por classe, grupos distintos, hashes e revisão de iluminação. Não usar validação ou teste para estimar faixas. Para propor outra seleção histórica:

```powershell
& $python -m src.quantizacao_t7_3 preparar --raiz-imagens $imagens --saida runs/nova_calibracao --total 200 --semente 42
```

Complete a revisão de iluminação correspondente aos novos IDs/hashes antes de converter com `--conjunto runs/nova_calibracao`. O comando de preparação não substitui essa revisão. Para um dataset novo, atualize também índice, pacote e contratos de proveniência: os validadores recusam hashes incompatíveis com T5.6. Preserve a versão oficial e registre uma nova versão; não contorne as verificações.

Leia escala e zero point de cada tensor do arquivo convertido. Use `q = clip(round(x / escala) + zero_point, -128, 127)` e `x = (q - zero_point) * escala`. No [contrato oficial INT8](../assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026/contrato_int8.json), a entrada tem escala aproximadamente `1/255` e zero point `-128`; a saída tem seus próprios parâmetros. Não aplique parâmetros de outro modelo.

## Comparação e critérios

Compare os mesmos IDs, preprocessing, ordem das classes e checkpoint em FP32, Float16 e INT8. Registre SHA-256, bytes, tipos, escala/zero point, versões, delegates, threads e hardware. Compare F1 macro, precisão/recall/F1 por classe, matriz, argmax e erro absoluto dos scores. A T7.2 usa validação para decisão, bootstrap pareado com 2.000 reamostragens e latência em 5 rodadas de 40 inferências, com XNNPACK (1/2/4 threads) e sem delegate (1/4). Execute ligado à tomada; `--permitir-bateria` altera essa condição e precisa ser registrado.

Os critérios versionados são modelo até 8.000.000 bytes, p95 abaixo de 300 ms no aparelho de referência, perda de acurácia macro até 2 pontos percentuais e execução sem delegate. Estimativa pontual e intervalo de confiança são evidências diferentes; a T8.3 registra ambas. Resultados locais x86 não certificam Android nem RAM. Reavalie a política de confiança após quantizar: ela foi calibrada originalmente em Keras FP32.

A consolidação histórica não faz nova inferência; confere tabelas/predições existentes:

```powershell
& $python -m src.avaliacao_pos_conversao_t8_1 --saida runs/consolidacao_t8_1
```

Para consolidar novos resultados, passe explicitamente `--comparacao`, `--original`, `--pacote`, `--indice`, `--fp32` e `--int8` compatíveis; não combine defaults históricos com uma nova rodada. A saída inclui métricas gerais/por classe, predições, mudanças por imagem, matrizes e `proveniencia.json`.

## Arquivos finais e valores de referência

Fonte decisória: [decisao.json T8.3](../assets/data/selecao_T8_3/decisao.json).

| Artefato | Bytes | F1 macro validação | F1 macro teste exploratório |
| --- | --- | --- | --- |
| [FP32 T7.1](../assets/modelos/conversao_T7_1_candidato_T5_6_20261026/modelo.tflite) | 13.531.184 | 0,781106 | 0,732928 |
| [Float16 principal T7.2](../assets/modelos/comparacao_T7_2_candidato_T5_6_20261026/modelo_float16.tflite) | 6.833.548 | 0,782961 | 0,732928 |
| [INT8 contingência T7.3](../assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite) | 4.003.624 | 0,776707 | 0,740019 |

O hash Float16 vem de [comparacao.json](../assets/modelos/comparacao_T7_2_candidato_T5_6_20261026/comparacao.json), chave `estrategias.float16.sha256`; o INT8 vem de `contrato_int8.json`, chave `modelo_int8_sha256`. O INT8 regenerado T7.2 e o antigo T5.6 têm outros hashes e não são a contingência oficial. Novas conversões podem divergir em bytes e scores; exija nova comparação e versionamento. Veja [T14.4](T14_4_Arquitetura_Web.md) para empacotar e conferir a execução no navegador.
