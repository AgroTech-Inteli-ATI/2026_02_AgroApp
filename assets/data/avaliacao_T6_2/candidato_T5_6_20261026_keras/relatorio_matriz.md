# Matriz do candidato Keras FP32 — T6.2

Teste exploratório: 473 imagens, 13 classes, 401 acertos e 72 erros.

Linhas: classe real. Colunas: classe prevista. Cores: fração da classe real.
Destaque descritivo: pares direcionais com pelo menos 2 erros nesta amostra.
Não demonstra confusão sistemática em dados novos, independência entre fotos ou causa do erro.

| Classe real → prevista | Erros | Suporte real | Parcela da classe |
| --- | ---: | ---: | ---: |
| Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-do-cartucho (Spodoptera frugiperda) | 6 | 12 | 50.0% |
| Percevejo-asa-preta (Edessa meditabunda) → Percevejo-verde (Nezara viridula) | 5 | 11 | 45.5% |
| Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Lagarta-do-cartucho (Spodoptera frugiperda) | 5 | 24 | 20.8% |
| Vaquinha (Diabrotica speciosa) → Astylus variegatus | 5 | 157 | 3.2% |
| Percevejo-verde (Nezara viridula) → Vaquinha (Diabrotica speciosa) | 4 | 14 | 28.6% |
| Percevejo-verde (Nezara viridula) → Percevejo-barriga-verde (Dichelops/Diceraeus) | 4 | 14 | 28.6% |
| Percevejo-do-milho (Leptoglossus zonatus) → Cigarrinha-das-pastagens (Deois flavopicta) | 3 | 12 | 25.0% |
| Cigarrinha-do-milho (Dalbulus maidis) → Vaquinha (Diabrotica speciosa) | 3 | 29 | 10.3% |
| Percevejo-barriga-verde (Dichelops/Diceraeus) → Vaquinha (Diabrotica speciosa) | 3 | 42 | 7.1% |
| Lagarta-do-cartucho (Spodoptera frugiperda) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 3 | 61 | 4.9% |
| Percevejo-marrom (Euschistus heros) → Percevejo-barriga-verde (Dichelops/Diceraeus) | 2 | 10 | 20.0% |
| Percevejo-marrom (Euschistus heros) → Percevejo-do-milho (Leptoglossus zonatus) | 2 | 10 | 20.0% |
| Percevejo-asa-preta (Edessa meditabunda) → Vaquinha (Diabrotica speciosa) | 2 | 11 | 18.2% |
| Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 2 | 12 | 16.7% |
| Percevejo-barriga-verde (Dichelops/Diceraeus) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 2 | 42 | 4.8% |
| Vaquinha (Diabrotica speciosa) → Percevejo-barriga-verde (Dichelops/Diceraeus) | 2 | 157 | 1.3% |

Todos os pares, inclusive os de um único erro, estão em pares_confundidos.csv.
Os IDs e caminhos das fotos erradas estão em erros_por_imagem.csv; não há revisão visual ou causa atribuída nesse arquivo.
Não houve nova inferência, treinamento, mudança de pesos ou ajuste de limiar.
O resultado corresponde ao checkpoint Keras, não ao TFLite INT8.
A partição foi consultada historicamente; esta publicação não é avaliação final independente.
