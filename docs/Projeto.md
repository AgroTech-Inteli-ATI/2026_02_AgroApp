# Documentação do Projeto — AgroApp

## Sumário

<details>
<summary><strong>1. Entendimento de Negócio</strong></summary>

- [1.1 Matriz de riscos](#11-matriz-de-riscos)
- [1.2 Canvas de proposta de valor](#12-canvas-de-proposta-de-valor)
- [1.3 Persona e jornada do usuário](#13-persona-e-jornada-do-usuário)
- [1.4 Governança do acervo de imagens](#14-governança-do-acervo-de-imagens)

</details>

<details>
<summary><strong>2. Especificação Técnica e Arquitetura</strong></summary>

- [2.1 Requisitos e restrições técnicas](#21-requisitos-e-restrições-técnicas)
- [2.2 Glossário técnico do projeto](#22-glossário-técnico-do-projeto)
- [2.3 Levantamento de arquiteturas viáveis](#23-levantamento-de-arquiteturas-viáveis)
- [2.4 Diagrama da arquitetura da solução](#24-diagrama-da-arquitetura-da-solução)
- [2.5 Consolidação técnica](#25-consolidação-técnica)

</details>

---

# 1. Entendimento de Negócio

## 1.1 Matriz de riscos

Levantar e classificar os riscos da Seção 12 do TAP por probabilidade e impacto, iniciando a definição das mitigações.

**Documentação — a preencher**

| Risco | Probabilidade | Impacto | Mitigação | Responsável |
| --- | --- | --- | --- | --- |
| A preencher | A definir | A definir | A preencher | A definir |

**Critérios de classificação:** a preencher.

**Referências:** a preencher.

---

## 1.2 Canvas de proposta de valor

Mapear as dores e ganhos do produtor, diferenciando o que o Agro App já resolve do que será acrescentado pelo diagnóstico visual.

**Documentação — a preencher**

| Dores do produtor | Ganhos esperados | Solução atual do Agro App | Contribuição do diagnóstico visual |
| --- | --- | --- | --- |
| A preencher | A preencher | A preencher | A preencher |

**Canvas:** inserir a imagem ou o link do artefato aqui.

**Referências:** a preencher.

---

## 1.3 Persona e jornada do usuário

Construir a persona e estruturar a jornada do usuário desde a observação do sintoma em campo até a decisão de manejo.

**Documentação — a preencher**

**Persona:** descrever perfil, contexto de trabalho, objetivos, dificuldades e familiaridade com tecnologia.

| Etapa da jornada | Ação do usuário | Dificuldade | Oportunidade de melhoria |
| --- | --- | --- | --- |
| Observação do sintoma em campo | A preencher | A preencher | A preencher |
| Captura da imagem | A preencher | A preencher | A preencher |
| Consulta ao diagnóstico | A preencher | A preencher | A preencher |
| Decisão de manejo | A preencher | A preencher | A preencher |

**Referências:** a preencher.

---

## 1.4 Governança do acervo de imagens

Documentar origem, propriedade, permissão de uso, armazenamento e descarte das imagens, considerando também possíveis dados pessoais e a LGPD.

**Documentação — a preencher**

| Acervo | Origem | Propriedade | Permissão de uso | Armazenamento e acesso | Retenção e descarte |
| --- | --- | --- | --- | --- | --- |
| A preencher | A preencher | A validar | A validar | A definir | A definir |

**Possíveis dados pessoais e tratamento previsto:** a avaliar e documentar.

**Evidências das permissões e referências:** inserir links aqui.

---

# 2. Especificação Técnica e Arquitetura

## 2.1 Requisitos e restrições técnicas

Esta seção reúne os requisitos do módulo de diagnóstico visual previstos na Seção 17 do TAP. Os requisitos funcionais descrevem o fluxo desde a escolha da fotografia até o acesso ao conteúdo técnico do Agro App. As restrições técnicas tratam da execução do modelo no dispositivo, incluindo limites de tamanho, tempo de resposta e recursos necessários para a inferência. A definição conjunta desses pontos orienta o desenvolvimento e a validação do MVP.

### Requisitos funcionais do diagnóstico visual (MVP)

| ID | Requisito Funcional | Descrição | Entrada | Comportamento esperado | Critério de aceitação |
| --- | --- | --- | --- | --- | --- |
| RF-01 | O sistema deve permitir que o usuário capture ou selecione uma fotografia para diagnóstico. | Disponibiliza as duas formas de fornecer uma imagem ao módulo. | Fotografia capturada pela câmera ou selecionada no dispositivo. | Recebe a fotografia escolhida e inicia o fluxo de análise. | Uma fotografia capturada e uma fotografia selecionada podem, cada uma, iniciar a análise. |
| RF-02 | O sistema deve preparar a fotografia para a entrada do modelo de classificação. | Aplica à imagem os ajustes exigidos pelo modelo embarcado. | Fotografia recebida no RF-01. | Produz uma imagem no formato de entrada definido para o modelo. | Para cada fotografia aceita, a saída da preparação atende às especificações de entrada do modelo utilizado no MVP. |
| RF-03 | O sistema deve classificar a imagem nas classes definidas para o MVP. | Identifica possíveis pragas, doenças, deficiências nutricionais ou plantas daninhas nas culturas contempladas. | Imagem preparada no RF-02. | Retorna uma classe e um grau de confiança para cada hipótese produzida. | Todas as classes retornadas pertencem ao catálogo de classes do MVP; cada hipótese possui um grau de confiança associado. O escopo inicial de culturas é soja e milho, conforme o glossário. |
| RF-04 | O sistema deve apresentar as hipóteses mais prováveis em ordem decrescente de confiança. | Exibe as identificações candidatas resultantes da análise. | Hipóteses retornadas no RF-03. | Apresenta o nome de cada hipótese selecionada para exibição, começando pela de maior confiança. | As hipóteses exibidas pertencem ao resultado da análise e aparecem em ordem decrescente de confiança. |
| RF-05 | O sistema deve apresentar o grau de confiança de cada hipótese exibida. | Permite consultar a confiança atribuída a cada identificação candidata. | Hipóteses e graus de confiança retornados no RF-03. | Mostra o grau de confiança junto à hipótese correspondente. | Cada hipótese exibida possui um valor visível que corresponde ao grau de confiança retornado para ela. |
| RF-06 | O sistema deve informar quando nenhuma hipótese atingir o limiar mínimo de confiança. | Trata o resultado inconclusivo da análise. | Hipóteses retornadas no RF-03 e limiar mínimo adotado no MVP. | Apresenta uma mensagem de identificação inconclusiva, sem indicar uma classe como diagnóstico obtido. | Se todos os graus de confiança forem inferiores ao limiar, a mensagem é exibida e nenhuma classe é indicada como identificação obtida. |
| RF-07 | O sistema deve associar as classes do MVP ao conteúdo técnico correspondente do Agro App. | Relaciona cada classe reconhecível às informações técnicas existentes no aplicativo. | Classe pertencente ao catálogo do MVP. | Identifica o conteúdo técnico vinculado à classe. | Para cada classe do catálogo do MVP, a associação aponta para um conteúdo técnico correspondente e acessível no Agro App. |
| RF-08 | O sistema deve permitir que o usuário acesse as informações e recomendações de manejo relacionadas à hipótese apresentada. | Oferece a navegação do resultado para o conteúdo técnico associado. | Hipótese exibida com conteúdo associado no RF-07. | Ao selecionar a hipótese, abre o conteúdo correspondente no Agro App. | A seleção de cada hipótese exibida abre o conteúdo técnico associado à sua classe. |


### Requisitos não funcionais e restrições técnicas

**Documentação — a preencher**

| ID | Requisito ou restrição | Tipo | Valor ou limite | Critério de aceitação | Fonte |
| --- | --- | --- | --- | --- | --- |
| A definir | A preencher | A definir | A definir | A preencher | A preencher |

**Ambiente de execução:** a definir.

---

## 2.2 Glossário técnico do projeto

### Glossário Técnico

Este glossário tem como objetivo estabelecer um vocabulário comum entre a equipe de desenvolvimento e o parceiro ao longo das dez semanas de projeto. A padronização dos termos busca reduzir ambiguidades durante discussões técnicas, definição de requisitos, preparação dos dados, treinamento e avaliação do modelo, análise dos resultados e validação do MVP.

Os conceitos apresentados estão relacionados às principais etapas da solução, desde a organização do dataset e treinamento do modelo até sua execução local no dispositivo, avaliação da qualidade da imagem, tratamento de situações de baixa confiança e associação dos resultados ao conteúdo técnico disponível no AgroApp.

Para o MVP, o escopo agronômico inicial contempla as culturas de **soja e milho**. As classes específicas de problemas que serão reconhecidas dentro dessas culturas serão definidas conforme a estrutura e a disponibilidade das imagens do dataset.

| Termo | Definição no contexto do projeto |
|---|---|
| **Dataset** | Conjunto organizado de imagens utilizado para desenvolver e avaliar o modelo. Será composto principalmente pelo acervo disponibilizado pelo AgroApp, podendo ser complementado por bases públicas quando necessário. |
| **Amostra** | Uma unidade individual do dataset. No projeto, corresponde normalmente a uma imagem utilizada em alguma etapa de treinamento, validação ou teste do modelo. |
| **Cultura** | Espécie agrícola à qual a imagem ou o problema analisado está relacionado. No MVP, as culturas contempladas serão **soja e milho**. |
| **Classe** | Categoria que o modelo deverá distinguir durante a classificação. No MVP, o conjunto de classes será composto por problemas associados às culturas de soja e milho, conforme a estrutura e a rotulagem definidas para o dataset. |
| **Rótulo (Label)** | Informação associada a uma amostra que indica sua classe considerada correta. É utilizada como referência durante o treinamento e a avaliação do modelo. |
| **Anotação / Rotulagem** | Processo de associar às imagens as informações necessárias para sua utilização no dataset, principalmente a classe correspondente a cada amostra. |
| **Partição do Dataset** | Divisão do dataset em conjuntos com funções distintas, normalmente treino, validação e teste, evitando que a avaliação final seja realizada sobre as mesmas imagens utilizadas para o aprendizado do modelo. |
| **Conjunto de Treino** | Parte do dataset utilizada para que o modelo ajuste seus parâmetros e aprenda os padrões relacionados às diferentes classes. |
| **Conjunto de Validação** | Parte do dataset utilizada durante o desenvolvimento para acompanhar o desempenho do modelo e auxiliar na comparação entre configurações e experimentos. |
| **Conjunto de Teste** | Parte separada do dataset utilizada para avaliar o desempenho final do modelo sobre imagens que não participaram de seu treinamento. |
| **Transfer Learning** | Estratégia em que um modelo previamente treinado é adaptado ao problema específico do projeto, evitando a necessidade de desenvolver e treinar uma arquitetura completamente do zero. |
| **Aumento de Dados (Data Augmentation)** | Aplicação de transformações sobre as imagens de treinamento para aumentar sua diversidade e reduzir problemas relacionados à quantidade limitada ou à pouca variedade de amostras. |
| **Inferência** | Processo em que o modelo já treinado recebe uma nova imagem e gera uma previsão sobre a classe à qual ela provavelmente pertence. |
| **Inferência Local** | Execução da inferência diretamente no dispositivo do usuário, sem depender de uma conexão com servidores externos, preservando o funcionamento offline do AgroApp. |
| **Quantização** | Técnica de otimização utilizada para reduzir o tamanho do modelo e seu consumo de memória e recursos computacionais, buscando viabilizar sua execução em dispositivos móveis. |
| **Validação da Imagem** | Etapa anterior à classificação responsável por verificar se a fotografia apresenta condições mínimas para análise, considerando fatores como nitidez e qualidade visual suficiente. Caso esses critérios não sejam atendidos, o sistema deverá solicitar uma nova imagem antes de realizar a análise. |
| **Classe Predita** | Classe indicada pelo modelo como resultado da análise de uma nova imagem. Ela representa a categoria considerada mais compatível com os padrões identificados pelo modelo. |
| **Hipótese Diagnóstica** | Possível identificação do problema apresentada ao usuário a partir da análise da imagem. O termo é utilizado para indicar que o resultado do modelo deve ser tratado considerando seu grau de confiança e possíveis ambiguidades, e não necessariamente como uma conclusão definitiva. |
| **Grau de Confiança** | Valor associado à previsão do modelo que representa o nível de confiança atribuído a determinada hipótese. Esse valor auxilia o sistema a decidir como apresentar o resultado ao usuário, mas não deve ser interpretado isoladamente como garantia de que a classificação está correta. |
| **Limiar de Confiança** | Valor mínimo estabelecido para que uma hipótese possa ser apresentada como suficientemente confiável. Esse limite deverá ser definido com base nos experimentos do projeto e em referências adequadas. Caso nenhuma hipótese alcance o limiar estabelecido, o sistema deverá adotar um comportamento alternativo. |
| **Fallback** | Comportamento adotado quando o sistema não possui informações ou confiança suficientes para apresentar uma hipótese adequada. Pode incluir solicitar uma nova fotografia, pedir informações adicionais ou direcionar o usuário para conteúdos relacionados disponíveis no AgroApp. |
| **Base de Conteúdo** | Conjunto de informações técnicas já existentes no AgroApp que será associado às classes reconhecidas pelo modelo, permitindo direcionar o usuário para informações e recomendações relacionadas ao problema analisado. |
| **Latência** | Tempo decorrido entre o início do processamento da imagem e a disponibilização do resultado ao usuário. Como a inferência será executada localmente, esse indicador será utilizado para avaliar a velocidade da solução em dispositivos móveis. |
| **Métricas de Avaliação** | Indicadores utilizados para analisar o desempenho do modelo. Entre as métricas previstas estão acurácia, precisão e recall, que devem ser avaliadas também individualmente por classe e não apenas de forma global. |
| **Matriz de Confusão** | Estrutura que compara as classes reais das imagens com as classes preditas pelo modelo, permitindo identificar quais categorias estão sendo classificadas corretamente e quais estão sendo confundidas entre si. |
| **Log** | Registro de eventos relevantes ocorridos durante a execução da solução. Pode armazenar informações como resultado obtido, nível de confiança, ocorrência de falhas, conteúdo recomendado e ações realizadas pelo usuário. |
| **Rastreabilidade** | Capacidade de reconstruir e analisar o comportamento da solução a partir dos registros gerados. No projeto, poderá permitir verificar se o sistema encontrou uma resposta, qual foi seu grau de confiança, quais conteúdos foram sugeridos e se o usuário acessou as informações recomendadas. |

### Evolução do Glossário

Este glossário representa uma versão inicial do vocabulário técnico compartilhado do projeto e não deve ser considerado uma lista definitiva. A tabela poderá ser expandida, revisada ou refinada ao longo das dez semanas conforme novos conceitos passem a fazer parte das decisões técnicas, das reuniões com o parceiro, dos experimentos realizados ou da documentação da solução.

Algumas definições também poderão se tornar mais específicas conforme decisões ainda em aberto forem tomadas. Isso se aplica principalmente à composição das **classes do modelo**, aos critérios mínimos utilizados na **validação da imagem**, ao valor adotado como **limiar de confiança** e às informações efetivamente armazenadas para fins de **rastreabilidade**.

Embora o MVP tenha sido delimitado inicialmente às culturas de **soja e milho**, ainda será necessário definir quais problemas e classes associados a essas culturas serão contemplados, considerando principalmente a disponibilidade, qualidade e distribuição das imagens fornecidas para treinamento.

Recomenda-se que o glossário seja atualizado sempre que um termo técnico passar a ser utilizado de maneira recorrente ou quando houver possibilidade de interpretações diferentes entre a equipe e o parceiro. Dessa forma, o documento permanece conciso e atua como uma referência compartilhada para comunicação, tomada de decisão e documentação técnica ao longo do projeto.

---

## 2.3 Levantamento de arquiteturas viáveis

Pesquisar arquiteturas compatíveis com execução embarcada e comparar número de parâmetros, tamanho e acurácia de referência com os limites levantados no T2.1.

| Arquitetura | Parâmetros | Tamanho | Acurácia de referência | Dataset e condições de avaliação | Compatibilidade com T2.1 | Fonte |
| --- | --- | --- | --- | --- | --- | --- |
| EfficientNet-Lite0 | 4,7M | ≈ 4,7 MB (INT8, estimado) | 75,1% FP32 / 74,4% INT8 (top-1) | ImageNet-1k, 224×224. Latência INT8 de 6,5 ms em CPU do Pixel 4, com 4 threads e batch 1. | Provável: suporte nativo a INT8, menor tamanho da família. | [1] |
| EfficientNet-Lite1 | 5,4M | ≈ 5,4 MB (INT8, estimado) | 76,7% FP32 / 75,9% INT8 (top-1) | ImageNet-1k, 240×240. Latência INT8 de 9,1 ms em CPU do Pixel 4, com 4 threads e batch 1. | Provável. | [1] |
| EfficientNet-Lite2 | 6,1M | ≈ 6,1 MB (INT8, estimado) | 77,6% FP32 / 77,0% INT8 (top-1) | ImageNet-1k, 260×260. Latência INT8 de 12 ms em CPU do Pixel 4, com 4 threads e batch 1. | Provável, dependendo do limite final de tamanho. | [1] |
| EfficientNet-Lite3 | 8,2M | ≈ 8,2 MB (INT8, estimado) | 79,8% FP32 / 79,0% INT8 (top-1) | ImageNet-1k, 280×280. Latência INT8 de 18 ms em CPU do Pixel 4, com 4 threads e batch 1. | Depende do limite final de tamanho. | [1] |
| EfficientNet-Lite4 | 13,0M | ≈ 13 MB (INT8, estimado) | 81,5% FP32 / 80,2% INT8 (top-1) | ImageNet-1k, 300×300. Latência INT8 de 30 ms em CPU do Pixel 4, com 4 threads e batch 1. | Improvável: maior opção da lista, adequada apenas se o limite permitir. | [1] |
| MobileNetV3-Small (1.0) | 2,9M | ≈ 2,9 MB (INT8, estimado) | 68,1% top-1 (float) | ImageNet-1k, 224×224. 66M MACs e 15,8 ms em CPU do Pixel 1 (float). | Provável em tamanho e latência, mas com acurácia de base mais baixa. | [2] |
| MobileNetV3-Large (1.0) | 5,4M | ≈ 5,4 MB (INT8, estimado) | 75,6% top-1 (float) | ImageNet-1k, 224×224. 217M MACs e 51,2 ms em CPU do Pixel 1 (float). | Provável, mas falta validar a queda de acurácia após quantização. | [2] |
| MobileNetV3-Large (0.75) | 4,0M | ≈ 4,0 MB (INT8, estimado) | 73,3% top-1 (float) | ImageNet-1k, 224×224. 155M MACs e 39,8 ms em CPU do Pixel 1 (float). | Provável; representa um meio-termo entre tamanho, custo computacional e acurácia. | [2] |
| MobileNetV2 (referência) | 3,5M | 14 MB (Keras, FP32) | 71,3% top-1 | ImageNet-1k, 224×224, pesos Keras. | Fora do escopo do TAP; usado apenas como comparação. | [3] |
| EfficientNet-B0 (referência) | 5,3M | 29 MB (Keras, FP32) | 77,1% top-1 | ImageNet-1k, 224×224, pesos Keras. | Descartada: não foi desenhada para INT8 e apresenta risco maior de perda na quantização. | [3], [4] |

Como as fontes consultadas não publicam o tamanho dos arquivos `.tflite` das variantes candidatas, os valores em MB para modelos INT8 foram estimados usando a regra aproximada de 1 byte por parâmetro. Os valores em MB de MobileNetV2 e EfficientNet-B0 são referentes aos arquivos Keras em FP32 e, portanto, não são diretamente comparáveis com as estimativas INT8.

### Análise comparativa e limitações

Dentro das duas famílias previstas no TAP, o EfficientNet-Lite oferece a escala de acurácia mais previsível: de 74,4% (Lite0) a 80,2% (Lite4) em INT8, com custo crescente de parâmetros e latência. O MobileNetV3-Large tem acurácia float próxima à do Lite0 (75,6% contra 75,1%) com número de parâmetros semelhante, enquanto o MobileNetV3-Small é a opção de menor custo, mas apresenta acurácia de base sensivelmente inferior (68,1%).

O diferencial técnico está na quantização. O EfficientNet-Lite foi adaptado para execução embarcada, removendo squeeze-and-excite e trocando swish por ReLU6 para facilitar a quantização pós-treino. Segundo o blog do TensorFlow, a quantização pós-treino do EfficientNet original derrubou o top-1 de 75% para 46% em um teste inicial. Por isso, o EfficientNet-B0 padrão foi descartado como arquitetura principal. O MobileNetV3 usa hard-swish e squeeze-and-excite; a documentação também indica que a variante minimalistic, sem esses blocos, é menos eficiente em CPU, embora possa ser mais performática em GPU/DSP.

O tamanho tende a ser o critério mais restritivo, já que o TAP limita o modelo ao espaço que o Agro App aceita no pacote. A latência dificilmente deve ser o gargalo inicial, pois todos os candidatos avaliados ficam na casa de dezenas de milissegundos nos benchmarks publicados. Ainda assim, essa leitura deve ser validada com o dispositivo-alvo definido no T2.1.

As principais limitações do levantamento são:

- A acurácia de referência vem do ImageNet-1k, com objetos genéricos, e não representa diretamente o desempenho em folhas, pragas e deficiências fotografadas em campo.
- As latências vêm de aparelhos diferentes (Pixel 4 para EfficientNet-Lite e Pixel 1 para MobileNetV3) e de precisões diferentes (INT8 e float), servindo apenas como ordem de grandeza.
- Não foi encontrada nas fontes consultadas a acurácia INT8 do MobileNetV3, então ela precisa ser medida no projeto.
- Os benchmarks foram feitos em celulares Google, enquanto o aparelho-alvo dos produtores rurais pode ser mais modesto.
- O tamanho em MB foi estimado considerando a cabeça de 1000 classes; o modelo final, com menos classes, pode ser menor.
- Os candidatos foram limitados às famílias previstas no TAP; outras arquiteturas recentes não foram levantadas nesta etapa.

### Arquitetura recomendada e justificativa

Recomenda-se preliminarmente adotar o **EfficientNet-Lite0** como arquitetura principal do MVP, com **EfficientNet-Lite2** e **MobileNetV3-Large (1.0)** como candidatas para comparação no fine-tuning.

O EfficientNet-Lite0 apresenta o menor tamanho entre as variantes com acurácia INT8 publicada (74,4%), o que reduz o risco em relação à restrição de espaço do TAP. Além disso, foi desenhado para quantização, diminuindo a chance de perda significativa de acurácia na conversão para TensorFlow Lite/LiteRT prevista no escopo do projeto.

O EfficientNet-Lite2 deve ser considerado como alternativa se o limite de tamanho permitir e o Lite0 ficar aquém no dataset real, pois ganha cerca de 2,6 pontos de top-1 INT8 em relação ao Lite0 (77,0% contra 74,4%). O MobileNetV3-Large entra como comparação por ser citado no TAP e estar disponível diretamente no Keras, mas precisa ser testado quanto à perda pós-quantização.

A escolha final deve sair de um experimento de fine-tuning no dataset do Agro App, medindo F1 por classe, tamanho do arquivo `.tflite` e latência no aparelho-alvo.

**Referências:**

[1] [Repositório oficial EfficientNet-Lite (tensorflow/tpu)](https://github.com/tensorflow/tpu/blob/master/models/official/efficientnet/lite/README.md)  
[2] [Documentação Keras: MobileNet e MobileNetV3](https://keras.io/api/applications/mobilenet/)  
[3] [Documentação Keras Applications](https://keras.io/api/applications/)  
[4] [TensorFlow Blog: Higher accuracy on vision models with EfficientNet-Lite](https://blog.tensorflow.org/2020/03/higher-accuracy-on-vision-models-with-efficientnet-lite.html)

---

## 2.4 Diagrama da arquitetura da solução

Construir e finalizar o diagrama com captura da imagem, preprocessing, inferência local, política de confiança e associação ao conteúdo técnico.

**Documentação — a preencher**

**Diagrama:** inserir a imagem, o link ou um bloco Mermaid aqui.

| Componente | Responsabilidade | Entrada | Saída |
| --- | --- | --- | --- |
| Captura da imagem | A preencher | A preencher | A preencher |
| Pré-processamento | A preencher | A preencher | A preencher |
| Inferência local | A preencher | A preencher | A preencher |
| Política de confiança | A preencher | A preencher | A preencher |
| Associação ao conteúdo técnico | A preencher | A preencher | A preencher |

**Decisões de arquitetura e justificativas:** a preencher.

---

## 2.5 Consolidação técnica

Finalizar os requisitos e restrições técnicas com os valores acordados com o parceiro e revisar o glossário técnico do projeto.

**Documentação — a preencher**

| Item validado | Valor ou decisão acordada | Data | Participantes da validação | Evidência |
| --- | --- | --- | --- | --- |
| A preencher | A validar | A preencher | A preencher | A preencher |

