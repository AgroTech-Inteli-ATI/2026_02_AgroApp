# Dataset utilizado pelo modelo do MVP

Ficha consolidada em **18/11/2026**, referente ao recorte `candidato_20261026_indice_28ee6628`. Autor responsável, Rui. Revisor da ficha ainda a definir.

## Identificação e finalidade

O candidato EfficientNet-Lite0 de 26/10/2026 utiliza **3.156 imagens em 13 classes**, distribuídas em **2.209 de treino, 474 de validação e 473 de teste histórico**. O [índice utilizado](../assets/data/treino_T5_2/indice_dataset.csv) identifica cada imagem, seu rótulo e sua partição. Seu SHA-256 é `28ee662885202f0bda3dec9660e44b28f99b8bd183210bcbdd795b103269b2eb`, vinculado ao [manifesto do candidato](../assets/modelos/candidato_T5_6_20261026/manifesto.json).

As versões Float16 T7.2 e INT8 T7.3 selecionadas para o MVP 1.0.0 derivam desse candidato. A [decisão final de seleção](../assets/data/selecao_T8_3/decisao.json) identifica os modelos atuais. O recorte e suas partições continuam históricos, com as limitações de independência registradas nesta ficha.

O alvo é classificação multiclasse de imagens entre as 13 classes de insetos do escopo soja/milho. Cada registro fornece uma classe para a imagem inteira. O treinamento usa as fotografias completas, sem recortar as caixas das anotações YOLO. Essa configuração deve orientar a leitura das métricas e a coleta de novas fotos.

## Origem e composição

| Fonte local | Treino | Validação | Teste | Total no candidato |
| --- | ---: | ---: | ---: | ---: |
| iNaturalist, pasta `dataset/field/` | 1.254 | 269 | 269 | 1.792 |
| AgroInsect, pasta `dataset/image/` | 955 | 205 | 204 | 1.364 |
| **Total** | **2.209** | **474** | **473** | **3.156** |

**AgroInsect.** O registro de referência é AGROINSECT, versão 2, DOI `10.17632/4jyp4m9gxj.2`. A publicação descreve 1.510 imagens, anotações YOLO e quatro classes, com aquisição que inclui iNaturalist, GBIF e fotografias de campo. Portanto, os nomes das duas fontes locais não garantem origens independentes. Os metadados locais estão em `dataset/labels.csv`; 1.364 imagens dessa fonte integram o candidato. [Registro original do AgroInsect](https://data.mendeley.com/datasets/4jyp4m9gxj/2)

**iNaturalist.** Os metadados locais `dataset/field/field_labels.csv` descrevem observação, URL da imagem, crédito, licença e estágio quando anotado. A documentação de aquisição informa coleta em 04/10/2026, no Brasil, com filtro `research grade` e licenças `cc0`/`cc-by`. Esses são critérios registrados da coleta. A revisão agronômica integral dos rótulos e estágios permanece pendente. As 1.792 imagens selecionadas correspondem a **928 IDs de observação**. [iNaturalist](https://www.inaturalist.org/)

As fotografias e os metadados originais ficam no acervo de Dados, fora do Git. Para a transferência, devem acompanhar o pacote de dados, preservando os caminhos relativos e os créditos. O [extrato de metadados por imagem](../assets/data/dataset_T14_1/metadados_imagens.csv) versiona a correspondência com os 3.156 IDs, incluindo rótulo de origem, observação, URLs, licença/crédito registrado, estágio e informações do arquivo. Os hashes dos metadados de aquisição estão no [resumo da ficha](../assets/data/dataset_T14_1/resumo.json).

### Diferença entre os totais históricos

| Referência | Quantidade | Interpretação |
| --- | ---: | --- |
| Duas fontes públicas adquiridas | 3.334 | 1.510 AgroInsect e 1.824 iNaturalist, antes da triagem. |
| Recorte dessas fontes marcado para manter | 3.156 | 178 imagens foram excluídas na revisão de qualidade. As decisões estão na planilha revisada. |
| Manifesto anterior T4.2/T4.5 | 3.163 | Incluía sete imagens de outro acervo, posteriormente removidas do candidato. |
| Índice utilizado pelo candidato | **3.156** | Mantém apenas os caminhos iniciados por `dataset/`, com rótulos e partições herdados. |

O histórico ampliado da triagem também contém imagens de outros acervos. As quantidades anteriores de 3.233, 3.262 ou 3.460 descrevem levantamentos e etapas diferentes e devem conservar seus próprios denominadores. As sete exclusões do manifesto de 3.163 estão identificadas em [auditoria_dataset.json](../assets/data/treino_T5_2/auditoria_dataset.json). A retirada ocorreu antes do treinamento do candidato, preservando suas partições remanescentes.

## Dicionário das classes e distribuição

A ordem abaixo é a ordem de saída do modelo em [classes.json](../assets/modelos/candidato_T5_6_20261026/classes.json). `IDs de origem` são os números dos metadados adquiridos e precisam ser mapeados para `Índice do modelo`.

| Índice do modelo | Classe | IDs de origem | Treino | Validação | Teste | Total |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 0 | Vaquinha (*Diabrotica speciosa*) | 0 | 735 | 157 | 157 | 1.049 |
| 1 | Cigarrinha-do-milho (*Dalbulus maidis*) | 1 | 135 | 29 | 29 | 193 |
| 2 | Percevejo-barriga-verde (Dichelops/Diceraeus) | 2 | 198 | 42 | 42 | 282 |
| 3 | Lagarta-do-cartucho (*Spodoptera frugiperda*) | 3 | 285 | 61 | 61 | 407 |
| 4 | Percevejo-marrom (*Euschistus heros*) | 4 | 45 | 10 | 10 | 65 |
| 5 | Percevejo-verde (*Nezara viridula*) | 5 | 64 | 14 | 14 | 92 |
| 6 | Percevejo-asa-preta (*Edessa meditabunda*) | 6 | 53 | 11 | 11 | 75 |
| 7 | Percevejo-do-milho (*Leptoglossus zonatus*) | 7 | 55 | 12 | 12 | 79 |
| 8 | Lagarta-falsa-medideira (*Chrysodeixis includens*) | 8 | 55 | 12 | 12 | 79 |
| 9 | Lagarta-da-soja (*Anticarsia gemmatalis*) | 9 | 28 | 7 | 6 | 41 |
| 10 | Lagarta-das-vagens (*S. eridania* e *S. cosmioides*) | **10 e 11** | 110 | 24 | 24 | 158 |
| 11 | *Astylus variegatus* | **12** | 332 | 71 | 71 | 474 |
| 12 | Cigarrinha-das-pastagens (*Deois flavopicta*) | **13** | 114 | 24 | 24 | 162 |
| **Total** | **13 classes** | **14 IDs de origem** | **2.209** | **474** | **473** | **3.156** |

O agrupamento de *S. eridania* e *S. cosmioides* explica a passagem de 14 IDs de origem para 13 saídas. O [mapeamento histórico](../assets/data/classes-modelo.csv) mantém essa correspondência e as culturas associadas. A aprovação agronômica integral dos rótulos permanece indicada como pendente na auditoria de particionamento. O inventário e os metadados são as referências dos rótulos herdados.

O [CSV de contagens](../assets/data/dataset_T14_1/contagens_por_classe.csv) acrescenta a distribuição por fonte e o número de grupos registrados. A classe 1 possui **193 imagens, todas do AgroInsect**. A classe 2 reúne **268 do AgroInsect e 14 do iNaturalist**. Essa composição limita comparações de desempenho entre fontes.

## Critério de particionamento e duplicidades

O particionamento original foi executado com **semente 42** e proporções-alvo **70%/15%/15%**, usando grupos. O algoritmo preserva grupos, busca cobertura das classes nas três partições e equilibra tamanhos, classes e fontes. As proporções finais são aproximadas por causa do agrupamento e da retirada das sete imagens do outro acervo.

Os grupos são componentes de vínculos de origem, duplicatas exatas, pares visuais confirmados e eventuais vínculos manuais. Para iNaturalist, o ID da observação é uma chave de origem. A rotina aceita vínculos manuais, mas o histórico registra zero vínculos adicionais. O [código de agrupamento](../src/particionamento_t4_2.py) e o [gerador do manifesto](../src/gerar_manifesto_modelo_t4_2.py) descrevem o algoritmo.

O recorte possui **2.292 grupos registrados**, distribuídos em **1.589 de treino, 351 de validação e 352 de teste**. A palavra “grupo” identifica uma unidade registrada no pipeline, com alcance limitado aos vínculos conhecidos. Esses números não quantificam indivíduos biologicamente independentes.

A revisão de qualidade anterior examinou duplicatas exatas e candidatos visuais, conservando suas decisões na [planilha revisada](../assets/data/diagnostico_qualidade_T3_3_revisado.xlsx). A [revisão posterior da independência](../assets/data/independencia_T10_1/README.md) encontrou uma duplicata transformada que havia atravessado a separação.

| Grupo relacionado | Imagens | Situação e tratamento definido |
| --- | --- | --- |
| `REV-IMG_01019` | `IMG_01019` e `IMG_01020`, treino; `IMG_01874`, teste | `IMG_01019`/`IMG_01874` são versões da mesma fotografia. `IMG_01020` pertence à mesma observação `142398716`. Vincular as três em uma próxima partição. |
| `REV-IMG_01752` | `IMG_01752`, validação; `IMG_01835`, teste | Relação suspeita de cena/sequência. Agrupar preventivamente em uma próxima versão até esclarecer a origem. |

Dos 45 pares perceptualmente próximos revisados, um foi confirmado como duplicata, um permanece suspeito e 43 ficaram sem vínculo confirmado. A inspeção foi assistida por IA e a revisão humana permanece pendente no registro versionado. Há zero sobreposições pelas chaves de hash exato, pixels idênticos, grupo e observação conhecidos. O caso confirmado mostra que esses zeros não garantem a independência real.

O índice histórico foi preservado para rastrear os treinamentos e resultados existentes. **Todas as métricas obtidas sobre esse teste histórico são exploratórias**, considerando o vazamento e a consulta repetida ao teste durante o desenvolvimento. Nenhum novo teste com evidência de reserva anterior à avaliação foi identificado na revisão disponível. A [decisão registrada](../assets/data/independencia_T10_1/decisao_avaliacao.json) define o uso dos resultados e o tratamento de uma próxima versão.

## Estrutura dos arquivos e contrato do índice

```text
raiz_das_imagens/
└── dataset/
    ├── image/                 # Imagens adquiridas do AgroInsect
    ├── label/                 # Anotações YOLO de origem
    ├── labels.csv             # Classe e quantidade de caixas por arquivo AgroInsect
    ├── classes_all.txt        # IDs de origem 0–13
    ├── duplicates.txt         # Registro de duplicatas exatas da aquisição
    └── field/
        ├── field_labels.csv   # Observação, licença, crédito e estágio do iNaturalist
        └── <classe_origem>/   # Arquivos das observações
```

O parâmetro `--raiz-imagens` dos comandos aponta para `raiz_das_imagens`, a pasta que contém `dataset/`. Os arquivos versionados no repositório ficam em `assets/data/treino_T5_2/`, `assets/modelos/candidato_T5_6_20261026/` e nos anexos desta ficha. Use os caminhos relativos exatos do índice para localizar cada original.

| Campo de `indice_dataset.csv` | Significado |
| --- | --- |
| `image_id` | Identificador único da fotografia no inventário. |
| `caminho_relativo` | Caminho do arquivo a partir da raiz de imagens. |
| `sha256_original` | SHA-256 dos bytes originais usados na preparação. |
| `indice_modelo`, `nome_classe_modelo` | Índice 0–12 e nome correspondente em `classes.json`. |
| `grupo_particao` | Grupo registrado para separar imagens relacionadas. |
| `particao` | `treino`, `validacao` ou `teste`, herdados da separação histórica. |
| `peso_classe_treino` | Peso atribuído à classe no treino; vazio nas outras partições. |
| `aplicar_augmentation` | Elegibilidade registrada na preparação. A configuração da rodada define se o augmentation é efetivamente ativado. |
| `semente_augmentation` | Quando preenchida, semente determinística por imagem utilizada pelas rotinas de aumento. |
| `sha256_preprocessamento` | Hash do tensor preparado na execução histórica do pipeline. |
| `sha256_augmentation` | Hash da amostra de augmentation produzida na preparação histórica, quando aplicável. |

Os hashes de tensores no índice descrevem sua geração histórica. O hash do arquivo original permanece a referência de integridade das imagens. A implementação atual do preprocessing e seus testes estão documentados na seção 10.2 de [Projeto.md](Projeto.md#102-correspondência-do-preprocessing-python-e-web).

## Transformações, balanceamento e calibração

O processamento usa RGB, orientação EXIF aplicada uma vez, resize proporcional bicúbico para caber em **224 × 224**, preenchimento cinza `(128,128,128)` e normalização float32 para `[0,1]`. Preserva o enquadramento inteiro. O contrato atual explicita a preservação dos códigos RGB8 com ICC ignorado, a recusa de transparência e a comparação com o navegador. A [função de preprocessing](../src/preprocessamento.py) é compartilhada pelo treino e pelos procedimentos Python.

Os pesos seguem `N / (K × n_c)`, calculados apenas sobre as 2.209 imagens de treino. O arquivo [pesos_dataset.json](../assets/data/treino_T5_2/pesos_dataset.json) corresponde a esse recorte. A rodada selecionada manteve **ponderação por classe ativa e augmentation desativado**, conforme sua [configuração](../assets/modelos/candidato_T5_6_20261026/configuracao_treino.json). As marcações de augmentation no índice são registros da preparação.

A calibração INT8 utiliza **200 imagens deste treino**, com origem, grupos e hashes no [manifesto de calibração](../assets/data/calibracao_T7_3/manifesto_calibracao.csv). A calibração integra o subconjunto de treino e deve ser reconhecida ao analisar exposição das imagens. O [guia de treinamento](T14_2_Pipeline_Treinamento.md) e o [guia de avaliação/conversão](T14_3_Avaliacao_Conversao.md) apresentam os comandos associados.

## Qualidade e limitações conhecidas

- **Desbalanceamento.** Vaquinha possui 1.049 imagens e lagarta-da-soja, 41. A razão entre maior e menor classe é aproximadamente 25,6. O teste de algumas classes tem apenas 6 a 14 imagens, com possível correlação entre observações.
- **Estágios de vida.** O campo `life_stage` é disponibilizado pelos metadados iNaturalist e falta em parte dessas fotos. O resumo AgroInsect não traz esse campo. Os estágios foram preservados conforme anotados, sem inferência visual nesta ficha. As classes 8 e 9 têm, respectivamente, 65 e 39 adultos anotados. Há uma larva anotada da classe 8, em validação, e quatro da classe 3, todas em treino. Essas contagens não quantificam todas as larvas do acervo, pois há estágios desconhecidos. O [anexo de estágios](../assets/data/dataset_T14_1/estagios_por_classe.csv) detalha fonte e partição.
- **Rótulos herdados.** Os nomes e agrupamentos vêm da aquisição e do mapeamento interno. A identificação comunitária informada na coleta e a triagem interna devem ser complementadas por revisão agronômica do escopo, estágios e agrupamentos. O [registro de particionamento](../assets/data/particionamento_T4_2/auditoria_modelo.json) conserva essas pendências.
- **Resolução e enquadramento.** Há 18 imagens com lado maior abaixo de 224 pixels. As dimensões dos arquivos variam de 88 a 4.608 pixels de largura e de 100 a 3.468 de altura. O resize pode reduzir o detalhe de insetos pequenos no enquadramento.
- **Formato real dos arquivos.** A conferência dos cabeçalhos encontrou 3.107 JPEG, 23 PNG, 25 WebP e um GIF. `IMG_00020`, em treino, tem extensão `.jpg`, mas seu conteúdo é GIF com oito quadros. O carregamento histórico pelo Pillow utiliza o quadro inicial. Esse registro deve acompanhar uma futura revisão de formatos, e o domínio fotográfico estático aceito pelo frontend deve ser considerado ao montar novos dados.
- **Cor.** 1.762 arquivos possuem perfil ICC incorporado. O contrato atual preserva os códigos RGB8 usados no treinamento. A correspondência demonstrada entre Python e web deve manter a identificação de runtime e do corpus de regressão.
- **Representatividade.** Origem brasileira, cultura associada ao táxon e fotos denominadas `field` são metadados de aquisição. A cobertura de celulares, propriedades, estágios, iluminação e condições reais do parceiro exige avaliação própria. O conjunto é de classificação entre classes conhecidas e não foi preparado como amostra representativa de ausência de inseto ou de todas as entradas inadequadas.

## Licenças, créditos e transferência

O registro publicado do AgroInsect v2 informa **CC BY 4.0**. Essa informação é registrada em nível de conjunto. Para as imagens adquiridas diretamente do iNaturalist, os metadados selecionados registram **320 fotos `cc0` e 1.472 `cc-by`**, com créditos e links individuais preservados no extrato desta ficha. O nome de uma fonte local não substitui a identificação de procedência de cada foto. [Licença no registro do AgroInsect](https://data.mendeley.com/datasets/4jyp4m9gxj/2)

Na transferência do acervo, preservar os arquivos de aquisição, créditos, URLs, códigos de licença e evidências associadas. A conferência desta ficha registra os metadados recebidos e a licença publicada do conjunto. As decisões de uso e distribuição devem observar as condições das fontes e a governança descrita na seção 1.4 de [Projeto.md](Projeto.md#14-governança-do-acervo-de-imagens). As fotografias originais precisam integrar a entrega de dados por meio definido com o parceiro para que o treinamento possa ser reexecutado.

## Integridade e anexos

Na conferência desta ficha, os **3.156 arquivos originais** corresponderam ao SHA-256 do índice. Foram conferidos abertura/cabeçalhos e `Image.verify`, IDs únicos, mapeamento das 14 classes de origem para as 13 saídas e consistência entre grupos e partições. O resumo registra a verificação executada e os hashes dos insumos e dos CSVs gerados.

| Artefato | SHA-256 |
| --- | --- |
| `indice_dataset.csv` | `28ee662885202f0bda3dec9660e44b28f99b8bd183210bcbdd795b103269b2eb` |
| `pesos_dataset.json` | `b342f9a821778840d6a86024ddaef8ccbe6ff18b250b540f0025fadf222046b9` |
| `classes.json` | `1058619e188ffd7fa42bfc6821e2e122356b35d8503af71b987f37ae1e4572f4` |

Os hashes são calculados sobre os bytes dos arquivos. Uma alteração de conteúdo ou de quebras de linha exige conferência antes de atribuir resultados à mesma versão.

- [Resumo e hashes](../assets/data/dataset_T14_1/resumo.json) identificam o snapshot, as fontes e as verificações.
- [Contagens por classe](../assets/data/dataset_T14_1/contagens_por_classe.csv) incluem índices de origem, partições, fontes e grupos registrados.
- [Contagens por fonte e partição](../assets/data/dataset_T14_1/fontes_por_particao.csv) detalham a composição do recorte.
- [Estágios anotados](../assets/data/dataset_T14_1/estagios_por_classe.csv) preservam a ausência de anotação e distinguem fonte e partição.
- [Metadados por imagem](../assets/data/dataset_T14_1/metadados_imagens.csv) vinculam os IDs aos metadados de aquisição e às características dos arquivos. O índice histórico fornece caminhos, partições e SHA-256 originais correspondentes.

Para verificar uma cópia recebida, localizar cada original pelo índice e comparar seu SHA-256 antes de executar treino ou avaliação. A revisão de independência pode ser reproduzida pelo comando abaixo, com saída separada.

```bash
python -m src.independencia_t10_1 --acervo /caminho/que/contem/dataset --saida .work/conferencia_dataset_final
```

O ambiente e os pré-requisitos desse comando estão no [registro da revisão de independência](../assets/data/independencia_T10_1/README.md). A preparação de uma nova versão deve atualizar inventário, vínculos, partições, pesos, hashes e documentação, preservando o snapshot histórico para rastrear os modelos existentes.
