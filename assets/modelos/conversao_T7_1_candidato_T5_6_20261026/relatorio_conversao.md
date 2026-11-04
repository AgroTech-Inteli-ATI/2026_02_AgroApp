# Conversão T7.1

Backbone: efficientnet_lite0. Modelo float32, sem quantização.

Pacote selecionado: `assets/modelos/candidato_T5_6_20261026`.
Rodada T5.5: `rodadas_T5_6_20261026/20261026-213017_efficientnet_lite0_s42`.
SHA-256 Keras: `089a8d903a78898badf385f0d57006a4fb556d76e3e8fae719babdaf564aa51a`.
SHA-256 TFLite: `50f7e7a6072c193fadd58d662e1c240acd48806cd5dab2197aaf7677da29da56`.

| Tensor | Nome | Shape alocado | Assinatura | Tipo |
| --- | --- | --- | --- | --- |
| entrada | serving_default_imagem:0 | [1, 224, 224, 3] | [-1, 224, 224, 3] | float32 |
| saida | StatefulPartitionedCall_1:0 | [1, 13] | [-1, 13] | float32 |

T4.1: EXIF, RGB, proporção preservada, padding cinza 128, float32 / 255. Layout NHWC, batch 1; entrada em [0, 1].
Saída: probabilidades softmax; argmax identifica o índice da classe em contrato_tensores.json.

| Índice de saída | Classe |
| ---: | --- |
| 0 | Vaquinha (Diabrotica speciosa) |
| 1 | Cigarrinha-do-milho (Dalbulus maidis) |
| 2 | Percevejo-barriga-verde (Dichelops/Diceraeus) |
| 3 | Lagarta-do-cartucho (Spodoptera frugiperda) |
| 4 | Percevejo-marrom (Euschistus heros) |
| 5 | Percevejo-verde (Nezara viridula) |
| 6 | Percevejo-asa-preta (Edessa meditabunda) |
| 7 | Percevejo-do-milho (Leptoglossus zonatus) |
| 8 | Lagarta-falsa-medideira (Chrysodeixis includens) |
| 9 | Lagarta-da-soja (Anticarsia gemmatalis) |
| 10 | Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) |
| 11 | Astylus variegatus |
| 12 | Cigarrinha-das-pastagens (Deois flavopicta) |

FlatBuffer carregado do disco e executado em 3 amostras.
Comparação Keras/TFLite: atol=1e-5, rtol=1e-4. Detalhes no JSON.
As amostras sintéticas verificam execução e equivalência numérica, sem medir acurácia.
