# T11.1 — Avaliação final do modelo e métricas por classe

Autor: Glauco · Revisor: Rui · Meta de entrega: a definir

Execução registrada em 20/11/2026 (America/Sao_Paulo). Relatório gerado por [`avaliacao_final_t11_1.py`](../src/avaliacao_final_t11_1.py); dados completos em [`assets/data/avaliacao_final_T11_1`](../assets/data/avaliacao_final_T11_1/metricas.json).

> **Classificação: avaliação exploratória.** Não existe conjunto independente reservado ([T10.1](../assets/data/independencia_T10_1/README.md)). Os números abaixo descrevem o desempenho do build entregue no recorte histórico e **não comprovam generalização** para fotos novas de campo.

## Resumo

| Modelo (papel) | Conjunto | Imagens | Acurácia | IC 95% acurácia | F1 macro | IC 95% F1 macro | Precisão macro | Recall macro | Top-3 |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: |
| Float16 (principal) | teste histórico | 473 | 0,8478 | 0,8161–0,8795 | 0,7329 | 0,6650–0,7907 | 0,8080 | 0,7126 | 0,9535 |
| INT8 (contingência) | teste histórico | 473 | 0,8436 | 0,8118–0,8753 | 0,7400 | 0,6703–0,7939 | 0,7976 | 0,7234 | 0,9450 |
| Float16 (principal) | validação | 474 | 0,8586 | 0,8270–0,8903 | 0,7830 | 0,7245–0,8291 | 0,8337 | 0,7563 | 0,9451 |
| INT8 (contingência) | validação | 474 | 0,8586 | 0,8249–0,8882 | 0,7767 | 0,7140–0,8248 | 0,8185 | 0,7528 | 0,9388 |

O resultado de referência para a entrega é o **Float16 (principal) no teste histórico**. O INT8 só é carregado pelo aplicativo quando o Float16 falha ao compilar ou validar. A validação participou da seleção do checkpoint e do limiar, por isso tende a ser otimista e aparece apenas como complemento. Recall macro é igual à balanced accuracy. Os intervalos são bootstrap percentil por imagem e, por ignorarem a correlação entre fotos do mesmo grupo, tendem a ser estreitos demais.

## Identificação do que foi avaliado

| Item | Valor |
| --- | --- |
| Modelo | `candidato_T5_6_20261026` · versão **1.0.0** · efficientnet_lite0 · seleção `concluida_versao_oficial_mvp` |
| Arquivo Float16 (principal, T7.2) | `frontend/dist/models/modelo_float16_web.tflite` · 6.833.548 bytes · SHA-256 `9c18f0a2ca4a4e2eb0d84dd415046f0bd35385ede8c47e14463d3a0f134647ec` (origem `c9a26ce13806a2fa…`) |
| Arquivo INT8 (contingência, T7.3) | `frontend/dist/models/modelo_int8_web.tflite` · 4.003.624 bytes · SHA-256 `df2f5d4fe22b4d3f76c4b8f6dab6e0100231c83d606122999ed15ceb72c05978` (origem `456caec54fae3c57…`) |
| Build | `frontend/dist` · manifesto SHA-256 `0d171afdf46918bc378388497c597d29c4789434730b88d6ded7b3158c1bb31b` · commit `fe33e353671fa9ea8bea905654af7b8b6f62566a` |
| Runtime | TFLite `tf.lite.Interpreter` 2.22.0-rc0, delegate padrão (XNNPACK), 1 thread · Python 3.14.4, NumPy 2.4.4, Pillow 12.2.0 |
| Preprocessing | contrato `T10.2-rgb8-sem-conversao-icc-v1` ([seção 10.2](Projeto.md#102-correspondência-do-preprocessing-python-e-web)) |
| Índice | `assets/data/treino_T5_2/indice_dataset.csv` · SHA-256 `28ee662885202f0bda3dec9660e44b28f99b8bd183210bcbdd795b103269b2eb` (o mesmo auditado na T10.1) |
| Classes | 13, ordem do manifesto · SHA-256 `1058619e188ffd7fa42bfc6821e2e122356b35d8503af71b987f37ae1e4572f4` |
| Política de confiança | top-1 ≥ 0,65 ([T6.5](../assets/data/politica_T6_5/parametros.json)) |
| Conjuntos | teste histórico (473 imagens) e validação (474 imagens); treino não avaliado |

### Equivalência com o runtime do navegador

O avaliador lê os `.tflite` do build, verifica tamanho e SHA-256 contra o manifesto servido e recusa divergências. Antes da avaliação, reexecuta os 18 casos fotográficos da T10.2 e compara os scores com os registrados no navegador (tolerância `1e-05`, sem mudança de classe ou decisão):

| Modelo | Runtime web de referência | Casos | Diferença máxima de score | Mudanças de classe/decisão |
| --- | --- | ---: | ---: | ---: |
| Float16 | LiteRT.js 2.6.0 CPU/WASM, 1 thread (Chromium 156.0.8078.4) | 18 | `1.19e-07` | 0 |
| INT8 | LiteRT.js 2.6.0 CPU/WASM, 1 thread (Chromium 156.0.8078.4) | 18 | `0` | 0 |

## Métricas por classe

Acurácia por classe é calculada um-contra-todos: `(VP + VN) / N`. Como VN domina com 13 classes, ela fica sempre alta; o recall mostra a taxa de acerto das imagens da própria classe. Precisão de classe nunca prevista vale 0.

### Float16 (principal) — teste histórico

| Índice | Classe | Acurácia (OvR) | Precisão | Recall | F1 | Suporte |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Vaquinha (Diabrotica speciosa) | 0,9514 | 0,9187 | 0,9363 | 0,9274 | 157 |
| 1 | Cigarrinha-do-milho (Dalbulus maidis) | 0,9915 | 0,9630 | 0,8966 | 0,9286 | 29 |
| 2 | Percevejo-barriga-verde (Dichelops/Diceraeus) | 0,9598 | 0,7556 | 0,8095 | 0,7816 | 42 |
| 3 | Lagarta-do-cartucho (Spodoptera frugiperda) | 0,9619 | 0,8209 | 0,9016 | 0,8594 | 61 |
| 4 | Percevejo-marrom (Euschistus heros) | 0,9894 | 1,0000 | 0,5000 | 0,6667 | 10 |
| 5 | Percevejo-verde (Nezara viridula) | 0,9704 | 0,5000 | 0,3571 | 0,4167 | 14 |
| 6 | Percevejo-asa-preta (Edessa meditabunda) | 0,9852 | 1,0000 | 0,3636 | 0,5333 | 11 |
| 7 | Percevejo-do-milho (Leptoglossus zonatus) | 0,9852 | 0,6923 | 0,7500 | 0,7200 | 12 |
| 8 | Lagarta-falsa-medideira (Chrysodeixis includens) | 0,9810 | 0,8000 | 0,3333 | 0,4706 | 12 |
| 9 | Lagarta-da-soja (Anticarsia gemmatalis) | 0,9937 | 0,7143 | 0,8333 | 0,7692 | 6 |
| 10 | Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 0,9598 | 0,5926 | 0,6667 | 0,6275 | 24 |
| 11 | Astylus variegatus | 0,9767 | 0,8947 | 0,9577 | 0,9252 | 71 |
| 12 | Cigarrinha-das-pastagens (Deois flavopicta) | 0,9894 | 0,8519 | 0,9583 | 0,9020 | 24 |
| | **Total / macro** | **0,8478** (global) | | **0,7126** | **0,7329** | **473** |

### INT8 (contingência) — teste histórico

| Índice | Classe | Acurácia (OvR) | Precisão | Recall | F1 | Suporte |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Vaquinha (Diabrotica speciosa) | 0,9471 | 0,9231 | 0,9172 | 0,9201 | 157 |
| 1 | Cigarrinha-do-milho (Dalbulus maidis) | 0,9937 | 0,9643 | 0,9310 | 0,9474 | 29 |
| 2 | Percevejo-barriga-verde (Dichelops/Diceraeus) | 0,9598 | 0,7674 | 0,7857 | 0,7765 | 42 |
| 3 | Lagarta-do-cartucho (Spodoptera frugiperda) | 0,9619 | 0,8209 | 0,9016 | 0,8594 | 61 |
| 4 | Percevejo-marrom (Euschistus heros) | 0,9894 | 1,0000 | 0,5000 | 0,6667 | 10 |
| 5 | Percevejo-verde (Nezara viridula) | 0,9725 | 0,5455 | 0,4286 | 0,4800 | 14 |
| 6 | Percevejo-asa-preta (Edessa meditabunda) | 0,9873 | 1,0000 | 0,4545 | 0,6250 | 11 |
| 7 | Percevejo-do-milho (Leptoglossus zonatus) | 0,9852 | 0,6923 | 0,7500 | 0,7200 | 12 |
| 8 | Lagarta-falsa-medideira (Chrysodeixis includens) | 0,9789 | 0,6667 | 0,3333 | 0,4444 | 12 |
| 9 | Lagarta-da-soja (Anticarsia gemmatalis) | 0,9937 | 0,7143 | 0,8333 | 0,7692 | 6 |
| 10 | Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 0,9577 | 0,5714 | 0,6667 | 0,6154 | 24 |
| 11 | Astylus variegatus | 0,9725 | 0,8816 | 0,9437 | 0,9116 | 71 |
| 12 | Cigarrinha-das-pastagens (Deois flavopicta) | 0,9873 | 0,8214 | 0,9583 | 0,8846 | 24 |
| | **Total / macro** | **0,8436** (global) | | **0,7234** | **0,7400** | **473** |

### Float16 (principal) — validação

| Índice | Classe | Acurácia (OvR) | Precisão | Recall | F1 | Suporte |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Vaquinha (Diabrotica speciosa) | 0,9536 | 0,9141 | 0,9490 | 0,9313 | 157 |
| 1 | Cigarrinha-do-milho (Dalbulus maidis) | 0,9937 | 0,9643 | 0,9310 | 0,9474 | 29 |
| 2 | Percevejo-barriga-verde (Dichelops/Diceraeus) | 0,9599 | 0,7170 | 0,9048 | 0,8000 | 42 |
| 3 | Lagarta-do-cartucho (Spodoptera frugiperda) | 0,9620 | 0,8525 | 0,8525 | 0,8525 | 61 |
| 4 | Percevejo-marrom (Euschistus heros) | 0,9937 | 1,0000 | 0,7000 | 0,8235 | 10 |
| 5 | Percevejo-verde (Nezara viridula) | 0,9831 | 0,8000 | 0,5714 | 0,6667 | 14 |
| 6 | Percevejo-asa-preta (Edessa meditabunda) | 0,9895 | 0,8750 | 0,6364 | 0,7368 | 11 |
| 7 | Percevejo-do-milho (Leptoglossus zonatus) | 0,9958 | 1,0000 | 0,8333 | 0,9091 | 12 |
| 8 | Lagarta-falsa-medideira (Chrysodeixis includens) | 0,9747 | 0,5000 | 0,2500 | 0,3333 | 12 |
| 9 | Lagarta-da-soja (Anticarsia gemmatalis) | 0,9937 | 0,7500 | 0,8571 | 0,8000 | 7 |
| 10 | Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 0,9662 | 0,7500 | 0,5000 | 0,6000 | 24 |
| 11 | Astylus variegatus | 0,9620 | 0,8354 | 0,9296 | 0,8800 | 71 |
| 12 | Cigarrinha-das-pastagens (Deois flavopicta) | 0,9895 | 0,8800 | 0,9167 | 0,8980 | 24 |
| | **Total / macro** | **0,8586** (global) | | **0,7563** | **0,7830** | **474** |

### INT8 (contingência) — validação

| Índice | Classe | Acurácia (OvR) | Precisão | Recall | F1 | Suporte |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Vaquinha (Diabrotica speciosa) | 0,9557 | 0,9146 | 0,9554 | 0,9346 | 157 |
| 1 | Cigarrinha-do-milho (Dalbulus maidis) | 0,9916 | 0,9310 | 0,9310 | 0,9310 | 29 |
| 2 | Percevejo-barriga-verde (Dichelops/Diceraeus) | 0,9620 | 0,7500 | 0,8571 | 0,8000 | 42 |
| 3 | Lagarta-do-cartucho (Spodoptera frugiperda) | 0,9620 | 0,8525 | 0,8525 | 0,8525 | 61 |
| 4 | Percevejo-marrom (Euschistus heros) | 0,9937 | 1,0000 | 0,7000 | 0,8235 | 10 |
| 5 | Percevejo-verde (Nezara viridula) | 0,9747 | 0,6000 | 0,4286 | 0,5000 | 14 |
| 6 | Percevejo-asa-preta (Edessa meditabunda) | 0,9873 | 0,7778 | 0,6364 | 0,7000 | 11 |
| 7 | Percevejo-do-milho (Leptoglossus zonatus) | 0,9958 | 1,0000 | 0,8333 | 0,9091 | 12 |
| 8 | Lagarta-falsa-medideira (Chrysodeixis includens) | 0,9768 | 0,5714 | 0,3333 | 0,4211 | 12 |
| 9 | Lagarta-da-soja (Anticarsia gemmatalis) | 0,9937 | 0,7500 | 0,8571 | 0,8000 | 7 |
| 10 | Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 0,9684 | 0,7647 | 0,5417 | 0,6341 | 24 |
| 11 | Astylus variegatus | 0,9662 | 0,8481 | 0,9437 | 0,8933 | 71 |
| 12 | Cigarrinha-das-pastagens (Deois flavopicta) | 0,9895 | 0,8800 | 0,9167 | 0,8980 | 24 |
| | **Total / macro** | **0,8586** (global) | | **0,7528** | **0,7767** | **474** |

### Leitura dos resultados (Float16, teste histórico)

A diferença entre acurácia global (0,8478) e F1 macro (0,7329) vem do desbalanceamento: as classes com mais imagens (Vaquinha, Astylus, Lagarta-do-cartucho) têm F1 alto e dominam a acurácia, enquanto o F1 macro pesa igualmente as classes pequenas. Classes com F1 abaixo de 0,60: Percevejo-verde (Nezara viridula) (F1 0,42, recall 0,36, suporte 14); Percevejo-asa-preta (Edessa meditabunda) (F1 0,53, recall 0,36, suporte 11); Lagarta-falsa-medideira (Chrysodeixis includens) (F1 0,47, recall 0,33, suporte 12). Principais confusões (real → prevista): Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-do-cartucho (Spodoptera frugiperda) (6); Vaquinha (Diabrotica speciosa) → Astylus variegatus (5); Percevejo-asa-preta (Edessa meditabunda) → Percevejo-verde (Nezara viridula) (5); Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Lagarta-do-cartucho (Spodoptera frugiperda) (5); Percevejo-verde (Nezara viridula) → Vaquinha (Diabrotica speciosa) (4).

### Matriz de confusão — Float16, teste histórico

Linhas: classe real; colunas: classe prevista (índices da tabela acima).

| Real \ Prevista | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **0** | **147** | 1 | 2 | · | · | · | · | · | · | · | 1 | 5 | 1 |
| **1** | 3 | **26** | · | · | · | · | · | · | · | · | · | · | · |
| **2** | 3 | · | **34** | 1 | · | · | · | · | · | 1 | 2 | 1 | · |
| **3** | · | · | 1 | **55** | · | · | · | 1 | · | 1 | 3 | · | · |
| **4** | · | · | 2 | · | **5** | · | · | 2 | · | · | · | 1 | · |
| **5** | 4 | · | 4 | · | · | **5** | · | · | · | · | 1 | · | · |
| **6** | 2 | · | · | · | · | 5 | **4** | · | · | · | · | · | · |
| **7** | · | · | · | · | · | · | · | **9** | · | · | · | · | 3 |
| **8** | · | · | · | 6 | · | · | · | · | **4** | · | 2 | · | · |
| **9** | · | · | 1 | · | · | · | · | · | · | **5** | · | · | · |
| **10** | · | · | 1 | 5 | · | · | · | · | 1 | · | **16** | 1 | · |
| **11** | 1 | · | · | · | · | · | · | 1 | · | · | 1 | **68** | · |
| **12** | · | · | · | · | · | · | · | · | · | · | 1 | · | **23** |

## Política de confiança no aplicativo

O aplicativo só indica a classe quando o top-1 atinge o limiar; abaixo dele, mostra resultado inconclusivo. O limiar foi calibrado em Keras FP32 na validação e não foi recalibrado para os arquivos entregues.

| Modelo | Conjunto | Cobertura (aceitos) | Acurácia nos aceitos | Erros aceitos | Acertos tornados inconclusivos |
| --- | --- | ---: | ---: | ---: | ---: |
| Float16 | teste histórico | 441/473 (93,2%) | 0,8821 | 52 | 12 |
| INT8 | teste histórico | 440/473 (93,0%) | 0,8750 | 55 | 14 |
| Float16 | validação | 430/474 (90,7%) | 0,9070 | 40 | 17 |
| INT8 | validação | 433/474 (91,4%) | 0,9030 | 42 | 16 |

A meta de acerto nos aceitos definida na T6.5 é 0,90, medida na validação em Keras FP32.

## Análise de sensibilidade (retrospectiva)

Regra: excluir da partição avaliada as imagens com vínculo registrado na T10.1 a imagens de partições usadas antes dela (treino e validação, no caso do teste). IDs removidos do teste: `IMG_01835`, `IMG_01874`. Na validação nenhuma imagem atende à regra. A exclusão não restaura a independência; serve só para dimensionar o efeito.

| Modelo | Recorte | Imagens | Acurácia | F1 macro | Precisão macro | Recall macro |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Float16 | integral | 473 | 0,8478 | 0,7329 | 0,8080 | 0,7126 |
| Float16 | sem vínculos | 471 | 0,8471 | 0,7329 | 0,8079 | 0,7126 |
| INT8 | integral | 473 | 0,8436 | 0,7400 | 0,7976 | 0,7234 |
| INT8 | sem vínculos | 471 | 0,8429 | 0,7399 | 0,7975 | 0,7233 |

Os suportes por classe do recorte reduzido estão em `metricas_por_classe.csv` (`recorte = sem_vinculos`).

## Consistência com avaliações anteriores

Classe prevista no teste histórico comparada às predições da [T8.1](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/relatorio_avaliacao.md), que usou os arquivos de origem dos mesmos modelos:

| Modelo | Coluna T8.1 | Predições iguais |
| --- | --- | ---: |
| Float16 | `previsto_float16` | 473/473 |
| INT8 | `previsto_int8_t7_3` | 473/473 |

## Limitações metodológicas

1. **Sem conjunto independente.** O teste histórico já foi consultado durante o desenvolvimento (T6/T8). Todas as métricas são exploratórias e servem para comparação descritiva, regressão e análise de erros, não como estimativa de generalização.
2. **Vazamento conhecido e vínculos desconhecidos.** Há uma fotografia repetida entre treino e teste (`IMG_01019`/`IMG_01874`) e uma relação suspeita entre validação e teste (`IMG_01752`/`IMG_01835`). A busca perceptual da T10.1 não é exaustiva. O efeito real sobre as métricas é desconhecido; a análise de sensibilidade cobre só os casos registrados.
3. **Validação usada na seleção.** Checkpoint, formato final e limiar de confiança foram escolhidos na validação, cujo resultado é otimista.
4. **Suporte pequeno e desbalanceado.** No teste, o suporte vai de 6 a 157 imagens por classe, e 9 das 13 classes têm menos de 30. Uma única imagem altera o recall da menor classe em 16,7 pontos percentuais. As métricas dessas classes são instáveis. Os intervalos de confiança globais tratam as imagens como independentes e subestimam a incerteza; não foram calculados intervalos por classe.
5. **Domínio das imagens.** O acervo combina iNaturalist e AgroInsect, com enquadramento e qualidade diferentes das fotos que um produtor tira no campo com o celular. Classes, estágios e condições de captura não foram validados com o parceiro.
6. **Runtime representado.** A inferência roda em Python com TFLite + XNNPACK, configuração que reproduziu o LiteRT.js CPU/WASM do Chromium desktop nos 18 casos da T10.2. WebGPU (tentado primeiro para o Float16 quando disponível), Safari, Firefox e Android físico não foram reavaliados; o TensorFlow desta execução pode diferir do usado na T10.2.
7. **Limiar não recalibrado.** A política de confiança foi definida em Keras FP32. Cobertura e acurácia nos aceitos descrevem o comportamento atual, sem ajuste do limiar no teste.

## Reprodução

Na raiz do repositório, com o build já gerado em `frontend/dist` e o acervo de imagens contendo `dataset/`:

```powershell
python -m src.avaliacao_final_t11_1 --raiz-imagens "C:\caminho\para\Agro App"
python -m unittest tests/validar_avaliacao_final_t11_1.py
```

O comando recusa build com modelo ou classes divergentes do manifesto, índice diferente do auditado na T10.1, imagem com hash divergente e runtime que não reproduza os scores do navegador. Não altera modelos, build nem índice. Saídas: este relatório, `metricas.json` (métricas, matrizes e proveniência), `metricas_por_classe.csv` e `predicoes.csv` (13 scores por imagem e modelo).
