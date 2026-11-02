# Análise de erros do candidato Keras FP32 — T6.3

72 erros inspecionados visualmente, distribuídos em 35 pares direcionais. Os 16 pares com pelo menos dois erros reúnem 53 imagens.

Inspeção visual assistida por IA das 72 imagens originais em seis pranchas; IMG_02602 também reaberta individualmente. Não é validação taxonômica por especialista.

As contagens vêm das previsões da T6.1 e da matriz da T6.2, sem nova inferência. Linhas são classes reais e colunas são previstas. Os rótulos reais são os do índice, não uma identificação taxonômica confirmada nesta revisão.

## Principais pares e cobertura

| Classe real → prevista | Erros / suporte | Observações iNaturalist nos erros | Fotos AgroInsect nos erros | Treino real: fotos / grupos |
| --- | ---: | ---: | ---: | ---: |
| Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-do-cartucho (Spodoptera frugiperda) | 6 / 12 | 5 | 0 | 55 / 26 |
| Percevejo-asa-preta (Edessa meditabunda) → Percevejo-verde (Nezara viridula) | 5 / 11 | 1 | 0 | 53 / 18 |
| Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Lagarta-do-cartucho (Spodoptera frugiperda) | 5 / 24 | 5 | 0 | 110 / 45 |
| Vaquinha (Diabrotica speciosa) → Astylus variegatus | 5 / 157 | 3 | 1 | 735 / 592 |
| Percevejo-verde (Nezara viridula) → Vaquinha (Diabrotica speciosa) | 4 / 14 | 3 | 0 | 64 / 33 |
| Percevejo-verde (Nezara viridula) → Percevejo-barriga-verde (Dichelops/Diceraeus) | 4 / 14 | 1 | 0 | 64 / 33 |
| Percevejo-do-milho (Leptoglossus zonatus) → Cigarrinha-das-pastagens (Deois flavopicta) | 3 / 12 | 2 | 0 | 55 / 21 |
| Cigarrinha-do-milho (Dalbulus maidis) → Vaquinha (Diabrotica speciosa) | 3 / 29 | 0 | 3 | 135 / 135 |
| Percevejo-barriga-verde (Dichelops/Diceraeus) → Vaquinha (Diabrotica speciosa) | 3 / 42 | 0 | 3 | 198 / 189 |
| Lagarta-do-cartucho (Spodoptera frugiperda) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 3 / 61 | 0 | 3 | 285 / 250 |
| Percevejo-marrom (Euschistus heros) → Percevejo-barriga-verde (Dichelops/Diceraeus) | 2 / 10 | 2 | 0 | 45 / 31 |
| Percevejo-marrom (Euschistus heros) → Percevejo-do-milho (Leptoglossus zonatus) | 2 / 10 | 1 | 0 | 45 / 31 |
| Percevejo-asa-preta (Edessa meditabunda) → Vaquinha (Diabrotica speciosa) | 2 / 11 | 2 | 0 | 53 / 18 |
| Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 2 / 12 | 1 | 0 | 55 / 26 |
| Percevejo-barriga-verde (Dichelops/Diceraeus) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) | 2 / 42 | 0 | 2 | 198 / 189 |
| Vaquinha (Diabrotica speciosa) → Percevejo-barriga-verde (Dichelops/Diceraeus) | 2 / 157 | 1 | 0 | 735 / 592 |

## Evidências que exigem conferência

- Percevejo-asa-preta (Edessa meditabunda): treino com 53 fotos em 18 grupos; 0 fotos de campo marcadas Nymph e 26 sem estágio. Há 7 erros com metadado Nymph nesta revisão. Isso motiva investigar cobertura; não prova ausência real de ninfas no treino nem causalidade.
- IMG_02602: Dois insetos com contorno em escudo, pernas e antenas aparentes sobre folha; aspecto de percevejos, incompatível visualmente com larva ou mariposa. Rótulo de origem também é Spodoptera frugiperda. Suspeita para validação especializada, sem identificação da espécie ou correção automática.

## Leitura dos indicadores

- Rótulos: suspeitas visuais para conferência especializada: IMG_02602. Não houve relabelagem ou recálculo seletivo das métricas.
- Escassez: cobertura_classes.csv apresenta as 13 classes em treino, validação e teste. Contagens de fotos e grupos não comprovam a causa de um erro. Metadado de estágio ausente não equivale a adulto, nem demonstra ausência de ninfas ou larvas.
- Semelhança: as hipóteses visuais constam por imagem e por par. Não há confirmação de que semelhança taxonômica real tenha causado os erros.
- Qualidade, estágio e múltiplos sujeitos são registrados separadamente; não são convertidos automaticamente em rótulo errado ou escassez.
- Observações iNaturalist contam apenas a fonte field. Zero nessa coluna não significa ausência de exemplos: fotos AgroInsect não possuem esse identificador. Grupos do particionamento tampouco garantem indivíduos independentes.
- A revisão é assistida por IA e exploratória, em teste consultado historicamente. Nenhuma causa foi confirmada por especialista. A análise do Keras não substitui a do TFLite INT8.

## Artefatos

- revisao_por_imagem.csv: todas as 72 fotos, caminho, hash, classe, grupo, metadados, observação visual, hipóteses e status.
- analise_por_par.csv: todos os pares, inclusive os de um erro, com as três causas de interesse explicitamente avaliadas como hipótese ou não demonstradas.
- cobertura_classes.csv: cobertura por partição; estágios referem-se apenas a metadados de campo, não a classificação visual automática do acervo.
- anotacoes_visuais.json: registro da inspeção visual de origem; proveniencia.json vincula entradas, código e resultados por hashes.
