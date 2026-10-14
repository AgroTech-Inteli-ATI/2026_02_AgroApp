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

- [Entendimento dos dados](#entendimento-dos-dados)
- [T3.4 — Dicionário de classes](#dicionário-de-classes-t34)

</details>

<details>
<summary><strong>3. Entendimento dos dados</strong></summary>

- [3.1 Inventário do acervo](#31-inventário-do-acervo)
- [3.2 Análise exploratória visual](#32-análise-exploratória-visual)
- [3.3 Diagnóstico de qualidade do acervo](#33-diagnóstico-de-qualidade-do-acervo)

</details>

<details>
<summary><strong>4. Preparação dos dados</strong></summary>

- [4.1 Padronização das imagens (T4.1)](#41-padronização-das-imagens)
- [4.2 Particionamento por grupo (T4.2)](#42-particionamento-por-grupo-t42)
- [4.4 Rotinas de aumento de dados (T4.4)](#44-rotinas-de-aumento-de-dados)
- [4.5 Pipeline reprodutível (T4.5)](#45-pipeline-reprodutível-t45)

</details>

<details>
<summary><strong>4. Preparação dos dados</strong></summary>

- [4.3 Estratégia de balanceamento (T4.3)](#43-estratégia-de-balanceamento-t43)

</details>

---

# 1. Entendimento de Negócio

## 1.1 Matriz de riscos

A matriz de riscos identifica os eventos que podem comprometer o desenvolvimento e os resultados do Módulo de Identificação de Pragas por Reconhecimento Visual integrado ao Agro App, avaliando cada um por probabilidade e impacto para priorizar as ações de mitigação. Foram levantados 12 riscos, dos quais 6 vêm do Termo de Abertura do Projeto (TAP) e 6 derivam dos requisitos do módulo, como nível mínimo de confiança, qualidade da imagem e rastreabilidade.

### Matriz de probabilidade e impacto

A Figura 1 mostra onde cada risco se posiciona ao cruzar probabilidade (eixo vertical) e impacto (eixo horizontal). Quanto mais próximo do canto superior direito, maior a prioridade de tratamento.

<div align="center">
  <p><strong>Figura 1 — Matriz de probabilidade e impacto</strong></p>
  <img src="../assets/matriz-de-risco.jpg" alt="Matriz de risco cruzando probabilidade e impacto, com os riscos R01 a R12 posicionados por nível">
  <p><em>Fonte: feito pela própria equipe, 2026.</em></p>
</div>

### Critérios de classificação

Cada risco recebeu uma nota de 1 a 3 em probabilidade e em impacto. A probabilidade indica a chance de o risco ocorrer ao longo do projeto, e o impacto indica o quanto ele compromete a qualidade do modelo, o cronograma ou a entrega do MVP.

| Nota | Probabilidade | Impacto |
| --- | --- | --- |
| 1 | **Baixa:** ocorrência improvável ao longo do projeto | **Baixo:** efeito pequeno, absorvido na própria sprint |
| 2 | **Média:** pode ocorrer, dependendo de decisões ou condições em aberto | **Médio:** atrasa etapas ou reduz a qualidade de parte da solução, mas o MVP continua viável |
| 3 | **Alta:** ocorrência provável ou já esperada, dadas as características dos dados e do contexto de uso | **Alto:** compromete o desempenho do modelo, o cronograma ou os critérios de sucesso do MVP |

O nível de risco é o produto entre as duas notas:

| Produto | Nível de risco | Tratamento |
| --- | --- | --- |
| 1 a 2 | Baixo | Acompanhamento simples, sem ação imediata |
| 3 a 4 | Médio | Monitoramento e manutenção da mitigação planejada |
| 6 | Alto | Mitigação ativa, revisada a cada sprint |
| 9 | Crítico | Prioridade máxima, tratado desde as primeiras fases |

### Riscos identificados

A tabela apresenta os riscos ordenados por nível.

| Risco | Probabilidade | Impacto | Nível | Mitigação | Responsável |
| --- | --- | --- | --- | --- | --- |
| **R01.** Número insuficiente de imagens por classe, principalmente para pragas e doenças menos frequentes | Alta (3) | Alto (3) | 9 (Crítico) | Priorizar no MVP as classes com mais imagens, usar aumento de dados e complementar com bases públicas validadas pelo parceiro | Equipe de dados e Agro App |
| **R04.** Sintomas visualmente semelhantes entre agentes causais distintos geram confusão sistemática entre classes | Alta (3) | Alto (3) | 9 (Crítico) | Retornar as hipóteses mais prováveis com grau de confiança, em vez de diagnóstico único, e agrupar classes indistinguíveis quando validado pelo parceiro | Equipe de modelagem |
| **R02.** Desbalanceamento entre classes faz o modelo favorecer as mais representadas | Alta (3) | Médio (2) | 6 (Alto) | Balanceamento e ponderação de classes, avaliando por métricas por classe e não pela acurácia global | Equipe de modelagem |
| **R06.** Fotos de baixa qualidade tiradas em campo (sol forte, sombra, tremor) prejudicam a análise | Alta (3) | Médio (2) | 6 (Alto) | Definir padrão mínimo de nitidez, validar a foto antes da análise e pedir nova foto explicando o problema | Equipe de desenvolvimento |
| **R03.** Modelo excede o tamanho ou o tempo de resposta aceitáveis no aparelho | Média (2) | Alto (3) | 6 (Alto) | Arquiteturas leves desde o início, quantização e limites de tamanho e latência definidos com o parceiro | Equipe de modelagem |
| **R07.** Limiar mínimo de confiança mal calibrado: muito baixo gera diagnósticos errados, muito alto faz o modelo recusar quase tudo | Média (2) | Alto (3) | 6 (Alto) | Definir o limiar com base no conjunto de validação e em referências de mercado, e pedir nova foto ou mais informações quando não for atingido | Equipe de modelagem |
| **R09.** Diferença entre as imagens do acervo e as fotos reais de campo faz o modelo ir bem no teste e mal em uso | Média (2) | Alto (3) | 6 (Alto) | Aumento de dados com variações de luz, ângulo e fundo, e testes com fotos tiradas por celular em condições reais | Equipe de modelagem |
| **R11.** O produtor trata a hipótese como conclusão definitiva e decide o manejo com base nela | Média (2) | Alto (3) | 6 (Alto) | Apresentar hipóteses com confiança, permitir esclarecer dúvidas antes da conclusão e deixar claro que a dosagem não faz parte do módulo | Equipe de UX e produto |
| **R05.** Curva de aprendizado da equipe em visão computacional maior que a prevista | Média (2) | Médio (2) | 4 (Médio) | Bibliotecas e modelos pré-treinados de alto nível, acompanhamento da diretoria de tecnologia e divisão de tarefas por frente de trabalho | Diretoria de tecnologia |
| **R08.** Acervo do parceiro chega atrasado, sem rótulos ou em formato inadequado | Média (2) | Médio (2) | 4 (Médio) | Confirmar volume, rotulagem e formato na Fase 1 e reservar a rotulagem manual no cronograma da Fase 2 | Gestão do projeto |
| **R12.** Aumento de escopo por funcionalidades ainda não detalhadas no TAP, como diálogo com o usuário e logs de rastreabilidade | Média (2) | Médio (2) | 4 (Médio) | Definir com o parceiro o que entra no MVP e o que fica para ciclos posteriores, com registro formal da decisão | Gestão do projeto |
| **R10.** Diagnóstico direciona a um conteúdo técnico errado ou inexistente na base do Agro App | Baixa (1) | Alto (3) | 3 (Médio) | Mapeamento classe-conteúdo validado pelo parceiro, testes em todas as classes do MVP e sugestão de conteúdos relacionados quando não houver validação | Equipe de desenvolvimento e Agro App |

### Análise da distribuição dos riscos

Dos 12 riscos, 2 são críticos, 6 são altos e 4 são médios, e nenhum ficou no nível baixo. Os críticos (R01 e R04) decorrem das características dos dados, que são o volume de imagens por classe e a semelhança visual entre sintomas, e por isso suas mitigações devem orientar já as Fases 1 e 2 do cronograma. Os altos se concentram no desempenho e no uso do módulo, como qualidade das fotos, limites de tamanho e latência, limiar de confiança, diferença entre o acervo e o campo e interpretação do resultado, e vários dependem de decisões ainda em aberto com o parceiro. Os médios estão ligados à equipe, ao parceiro e ao escopo. O R10 tem baixa probabilidade porque o Agro App já organiza o conteúdo por cultura e praga, mas alto impacto, pois um direcionamento errado comprometeria a recomendação de manejo.

---

## 1.2 Canvas de proposta de valor


<p align="center">
  <img src="../assets/canvas.png" alt="Canvas de Proposta de Valor" width="700">
</p>

### 1. Contextualização

O Canvas de Proposta de Valor foi desenvolvido com o objetivo de compreender as principais necessidades do usuário do AgroApp durante a identificação de problemas em uma cultura e relacioná-las à solução proposta.

O problema analisado ocorre principalmente no contexto de campo, no qual o usuário pode observar alterações na cultura sem possuir conhecimento técnico suficiente para identificar sua causa. Além disso, a disponibilidade de conexão com a internet pode ser limitada, dificultando o acesso imediato a especialistas ou a informações que auxiliem na tomada de decisão.

A partir desse cenário, o Canvas foi dividido entre o **Segmento de Clientes**, que representa as tarefas, dores e ganhos esperados pelo usuário, e a **Proposta de Valor**, que apresenta como a solução busca responder a essas necessidades.

### 2. Segmento de Clientes

### 2.1 Tarefas do Cliente

As tarefas representam aquilo que o usuário procura realizar ao perceber um possível problema em sua cultura, independentemente da solução proposta.

A primeira tarefa é **identificar o que está causando o problema observado na cultura**. O usuário percebe algum sintoma ou alteração visual, mas precisa compreender sua possível origem.

Após a identificação, existe a necessidade de **encontrar informações técnicas sobre o problema**, de forma a compreender melhor suas características e consequências.

Por fim, o usuário precisa **entender como manejar ou tratar o problema identificado**, utilizando as informações obtidas para decidir como agir de maneira adequada.

Dessa forma, as tarefas estão relacionadas a três momentos principais: identificar o problema, compreender suas características e encontrar uma forma apropriada de manejo.

### 2.2 Dores

As dores representam os obstáculos, dificuldades e riscos encontrados pelo usuário durante a realização dessas tarefas.

Uma das principais dificuldades é **não conseguir identificar rapidamente o problema enquanto está em campo**. Essa dificuldade é ampliada quando o usuário não possui conhecimento técnico suficiente para reconhecer visualmente pragas ou doenças.

Mesmo utilizando o AgroApp, pode existir uma barreira para encontrar o conteúdo correto, já que o usuário pode não saber previamente qual termo, praga ou doença deve procurar.

Outro fator relevante é a **falta de conexão com a internet no campo**. No processo atual, o usuário pode precisar fotografar o problema, esperar até conseguir conexão, enviar a imagem e posteriormente aguardar a análise de um agrônomo. Esse fluxo aumenta o tempo entre a percepção do problema e o acesso a uma orientação.

Também existe uma incerteza relacionada à **qualidade da fotografia capturada**, já que o usuário pode não saber se a imagem possui condições adequadas para análise.

Por fim, uma identificação incorreta pode gerar uma decisão de manejo inadequada, criando um risco adicional para o usuário.

### 3. Ganhos esperados pelo cliente

Os ganhos representam os resultados desejados pelo usuário ao realizar essas tarefas.

O principal ganho esperado é **conseguir identificar rapidamente o possível problema e possuir confiança na informação recebida**. A rapidez é especialmente importante porque o usuário pode precisar tomar uma decisão enquanto ainda está no campo.

Também é desejável obter a informação **no momento em que ela é necessária**, sem precisar esperar por conexão ou pelo retorno imediato de um especialista.

Além da identificação, o usuário espera compreender **como agir de forma mais segura**, diminuindo a incerteza durante a tomada de decisão.

Consequentemente, espera-se também uma **economia de tempo e uma redução da dependência de assistência imediata de um especialista**, sem necessariamente substituir a atuação profissional em situações que exijam análise especializada.

### 4. Proposta de Valor

### 4.1 Produto e serviço

A solução proposta consiste em um **módulo de visão computacional capaz de analisar uma fotografia diretamente no dispositivo do usuário**, buscando identificar possíveis pragas, doenças, deficiências nutricionais ou plantas daninhas.

A partir da análise, o módulo apresenta ao usuário as informações técnicas e as recomendações de manejo correspondentes.

O objetivo, portanto, não é apenas apresentar uma classificação visual, mas reduzir o caminho entre a observação de um problema na cultura e o acesso à informação necessária para compreendê-lo e decidir como agir.

### 4.2 Aliviadores de dores

A proposta busca reduzir as principais dificuldades identificadas no segmento de clientes.

O funcionamento **offline** permite que a análise seja realizada mesmo em regiões sem conexão com a internet, eliminando uma das principais barreiras do contexto de uso.

A utilização da imagem como ponto de partida também reduz a necessidade de o usuário **conhecer previamente o nome da praga, doença ou outro problema** para encontrar a informação desejada.

A solução busca ainda **reduzir o tempo de espera por uma primeira identificação**, oferecendo uma análise diretamente no dispositivo.

Para lidar com as limitações e incertezas inerentes ao modelo, são apresentadas **hipóteses acompanhadas de grau de confiança**, evitando tratar toda previsão como uma identificação absoluta.

Por fim, a solução direciona o usuário ao **conteúdo técnico correspondente**, reduzindo o esforço necessário para localizar manualmente a informação relevante dentro da plataforma.

### 4.3 Criadores de ganhos

Além de reduzir dificuldades existentes, a proposta busca gerar novos benefícios para o usuário.

Um dos principais é a **entrega do resultado em poucos segundos**, diminuindo o intervalo entre a captura da imagem e a obtenção da informação.

O módulo também facilita o **acesso à informação relevante**, tornando o processo mais direto para usuários que não possuem conhecimento técnico aprofundado.

Outro ganho é a criação de um fluxo integrado entre **identificação do possível problema e recomendação de manejo**, evitando que o usuário tenha que realizar diferentes buscas após receber o resultado.

Por funcionar diretamente no dispositivo, a solução permite ainda que o usuário **acesse a informação no próprio campo e no momento em que surge a necessidade**.

### 5. Relação entre o Segmento de Clientes e a Proposta de Valor

O encaixe entre as duas partes do Canvas ocorre porque as características da solução respondem diretamente às necessidades levantadas no segmento de clientes.

A dificuldade de identificar um problema é atendida pela análise da fotografia por visão computacional. A ausência de internet é tratada pelo funcionamento offline. A necessidade de conhecer previamente a nomenclatura do problema é reduzida porque a interação começa por uma imagem. A demora por uma primeira análise é reduzida pela inferência realizada diretamente no dispositivo. Já a necessidade de compreender como agir é atendida pela apresentação das informações técnicas e recomendações de manejo relacionadas ao resultado.

Da mesma forma, os criadores de ganhos estão relacionados aos resultados esperados pelo usuário: a resposta em poucos segundos atende à necessidade de rapidez; o acesso facilitado à informação contribui para uma decisão mais segura; e o funcionamento em campo possibilita que essa informação esteja disponível justamente no momento em que é necessária.

### 6. Síntese da proposta de valor

A proposta de valor pode ser sintetizada como a possibilidade de **reduzir o caminho entre a identificação visual de uma anormalidade na cultura e o acesso à informação necessária para compreender e manejar o possível problema**.

Em vez de depender inicialmente do conhecimento técnico do usuário, de conexão com a internet ou da espera por uma primeira análise externa, o módulo utiliza uma fotografia como ponto de partida e busca disponibilizar rapidamente informações relevantes diretamente no dispositivo.

A proposta, portanto, concentra-se principalmente em três atributos: **rapidez, disponibilidade em campo e facilidade de acesso à informação técnica**.

---

## 1.3 Persona e jornada do usuário

Uma persona é uma representação fictícia de um usuário, criada com base nas características, nos objetivos, nas necessidades e nas dificuldades do público que se pretende atender. Em nosso projeto, as personas funcionam como uma forma de validar se a solução proposta está realmente alinhada aos problemas e às expectativas de seus futuros usuários. Elas orientam as decisões da equipe ao longo do desenvolvimento, ajudando a avaliar funcionalidades, formas de interação e situações de uso do Módulo de Identificação de Pragas por Reconhecimento Visual integrado ao Agro App. Foram definidas duas personas para o projeto, e Vitória Lima, apresentada a seguir, é uma delas.

### Persona 1 — Rafael Mendes

<div align="center">
  <p><strong>Figura 2 — Persona Rafael Mendes</strong></p>
  <img src="../assets/persona_agronomo.png" alt="Persona Rafael Mendes, produtor rural e engenheiro agrônomo">
  <p><em>Fonte: feito pela própria equipe, 2026.</em></p>
</div>

Rafael Mendes tem 38 anos, é engenheiro agrônomo e produtor rural em Rio Verde, Goiás. Ele cuida da própria lavoura e, durante as rondas nos talhões, fotografa plantas com sintomas para descobrir o que está acontecendo e como tratar. Ele busca identificar rapidamente pragas, doenças e deficiências nutricionais, encontrar a recomendação de manejo adequada e evitar a aplicação de defensivo errado, mas encontra dificuldades para diferenciar sintomas visualmente semelhantes, nem sempre tem um consultor por perto e nem sempre conta com internet na lavoura. Por isso, precisa de um módulo que apresente as hipóteses mais prováveis, informe o grau de confiança do resultado, permita esclarecer dúvidas antes de uma conclusão e leve do diagnóstico ao manejo, inclusive offline.

### Jornada do usuário — Rafael Mendes

A jornada do usuário representa as etapas percorridas por uma pessoa ao interagir com uma solução, considerando suas ações, seus pensamentos, suas emoções e as dificuldades encontradas durante a experiência. No projeto, esse mapeamento permite compreender como Rafael utilizaria o módulo em uma situação real e identificar pontos de fricção e oportunidades de melhoria.

<div align="center">
  <p><strong>Figura 3 — Mapa da jornada do usuário de Rafael Mendes</strong></p>
  <img src="../assets/jornada_agronomo.png" alt="Mapa da jornada do usuário de Rafael Mendes">
  <p><em>Fonte: feito pela própria equipe, 2026.</em></p>
</div>

Na jornada mapeada, Rafael percebe plantas com aspecto diferente durante a ronda no talhão e fotografa a área afetada pelo módulo integrado ao Agro App. A análise é feita no próprio aparelho, mesmo sem conexão, e ele recebe as hipóteses com seus respectivos níveis de confiança. Caso a confiança fique abaixo do mínimo, o módulo não afirma o diagnóstico e pede uma nova foto ou mais informações. Em seguida, Rafael compara as hipóteses, esclarece suas dúvidas, consulta o conteúdo técnico relacionado e usa a recomendação de manejo para decidir o que fazer na lavoura.

O mapa evidencia necessidades importantes para o módulo, como validar a qualidade da imagem antes da análise, indicar o andamento do processamento, explicar o grau de confiança dos resultados, sugerir conteúdos do aplicativo quando não houver validação e conduzir do diagnóstico direto ao manejo. Como o custo de uma decisão equivocada recai sobre a própria safra, esses elementos aumentam a segurança de Rafael ao decidir e tornam o uso do módulo mais útil no dia a dia da lavoura.

### Persona 2 — Vitória Lima

<div align="center">
  <p><strong>Figura 4 — Persona Vitória Lima</strong></p>
  <img src="../assets/persona_estudante.png" alt="Persona Vitória Lima, estudante e pesquisadora de Agronomia">
  <p><em>Fonte: feito pela própria equipe, 2026.</em></p>
</div>

Vitória Lima tem 22 anos, cursa Agronomia e atua como pesquisadora em Piracicaba, São Paulo. Durante atividades de campo, fotografa sintomas em folhas e frutos para comparar possíveis doenças, pragas e deficiências nutricionais. Ela busca desenvolver experiência prática em diagnóstico vegetal e consultar referências técnicas confiáveis, mas encontra dificuldades para diferenciar sintomas visualmente semelhantes, avaliar hipóteses com segurança e acessar a internet em campo. Por isso, precisa de um módulo que apresente as hipóteses mais prováveis, informe o grau de confiança do resultado e permita acesso offline a conteúdos técnicos relacionados.

### Jornada do usuário — Vitória Lima

A jornada do usuário representa as etapas percorridas por uma pessoa ao interagir com uma solução, considerando suas ações, seus pensamentos, suas emoções e as dificuldades encontradas durante a experiência. No projeto, esse mapeamento permite compreender como Vitória utilizaria o módulo em uma situação real e identificar pontos de fricção e oportunidades de melhoria.

<div align="center">
  <p><strong>Figura 5 — Mapa da jornada do usuário de Vitória Lima</strong></p>
  <img src="../assets/jornada_estudante.png" alt="Mapa da jornada do usuário de Vitória Lima">
  <p><em>Fonte: feito pela própria equipe, 2026.</em></p>
</div>

Na jornada mapeada, Vitória encontra uma alteração em uma planta durante uma aula de campo e registra uma fotografia pelo módulo integrado ao Agro App. Caso esteja sem conexão, a imagem permanece salva no dispositivo até que possa ser enviada e processada. Em seguida, ela consulta as hipóteses apresentadas e seus respectivos níveis de confiança, compara os sinais com o conteúdo técnico disponível e registra as informações necessárias para discutir o resultado e o próximo passo com o professor.

O mapa evidencia necessidades importantes para o módulo, como orientar a captura de imagens com qualidade, informar claramente o estado do envio e do processamento, explicar o grau de confiança dos resultados e manter um histórico com fotos, análises e anotações. Esses elementos reduzem dúvidas ao longo da experiência e tornam seu uso mais seguro e útil em atividades de campo.

---

## 1.4 Governança do acervo de imagens

### 1. Objetivo

Estabelecer como as imagens usadas no desenvolvimento do diagnóstico visual serão recebidas, catalogadas, protegidas e descartadas. A governança permite verificar a procedência e a permissão de uso de cada imagem, manter a rastreabilidade do dataset e reduzir riscos de exposição indevida.

### 2. Origem das imagens

- **Acervo principal:** fornecido pelo Agro App para treinamento e avaliação do modelo. Pode conter imagens de pragas, doenças, deficiências nutricionais, plantas daninhas e culturas agrícolas.
- **Bases públicas complementares:** podem reforçar classes com poucas amostras, desde que sua utilização seja validada pelo parceiro e as condições de uso sejam verificadas.
- **Outras origens:** caso sejam incorporadas, deverão passar pelo mesmo registro de procedência e pela verificação das permissões antes do uso.

A origem de cada conjunto e, quando possível, de cada imagem deve ser registrada antes de sua inclusão no dataset.

### 3. Propriedade e permissão de uso

Para cada origem, deve-se identificar o titular dos direitos ou responsável pelo fornecimento, a autorização ou licença aplicável e suas limitações. O registro deve distinguir a permissão para **treinamento, validação, teste, documentação e apresentação**, além de eventuais restrições de compartilhamento, redistribuição ou publicação. O fornecimento de uma imagem, por si só, não comprova autorização para todos esses usos.

Até que a titularidade, as autorizações e as restrições do acervo principal sejam documentadas, as imagens não devem ser usadas fora das finalidades expressamente comprovadas. Isso inclui a publicação em documentos e apresentações. Imagens sem permissão identificada devem ficar fora dos conjuntos de uso até que a situação seja esclarecida.

### 4. Catalogação e rastreabilidade

**Proposta da equipe:** manter um registro por imagem ou por conjunto homogêneo, conforme a granularidade disponível, com os seguintes campos mínimos:

| Campo | Informação a registrar |
| --- | --- |
| Identificador | Código único da imagem ou do conjunto. |
| Origem e fornecimento | Fonte, referência de obtenção e responsável pelo fornecimento. |
| Conteúdo | Classe ou rótulo, cultura associada e observações relevantes, quando aplicáveis. |
| Direito de uso | Titular ou responsável, autorização ou licença, evidência e restrições conhecidas. |
| Histórico | Data de inclusão, alterações de rótulo e motivo de exclusão, quando ocorrer. |
| Uso no dataset | Partição de treino, validação ou teste e identificação de eventuais derivados. |

O identificador deve permitir localizar a imagem, sua origem e a evidência da permissão sem depender apenas do nome do arquivo.

### 5. Armazenamento e controle de acesso

**Proposta da equipe:** manter o acervo em local de acesso restrito, organizado por origem e etapa de tratamento. Preservar os arquivos brutos separadamente das versões processadas e registrar a ligação entre eles. Conceder acesso somente às pessoas que precisam das imagens para suas atividades, revisar esses acessos quando a participação mudar e evitar links públicos ou a inclusão acidental do acervo em repositórios públicos. Quando houver cópias de segurança, elas devem seguir as mesmas regras de acesso e o ciclo de retenção definido para os originais.

O local de armazenamento, a lista de pessoas autorizadas e as regras de cópia de segurança precisam ser definidos antes do recebimento do acervo. A escolha da ferramenta deve respeitar essas regras; esta seção não pressupõe uma solução específica.

### 6. Dados pessoais e LGPD

Embora o objetivo seja fotografar plantas, uma imagem pode incluir pessoas ao fundo, rostos, placas de veículos, localização em metadados EXIF ou elementos de uma propriedade rural que, em determinado contexto, permitam identificar uma pessoa natural. A presença desses elementos deve ser avaliada também nas bases públicas. A [ANPD define dado pessoal pela possibilidade de identificar uma pessoa natural direta ou indiretamente](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados); a avaliação de cada imagem depende do contexto.

**Proposta da equipe:** inspecionar as imagens e seus metadados antes de incluí-las no dataset; coletar e conservar somente o necessário para a finalidade definida; restringir o acesso; e remover metadados ou ocultar elementos identificadores quando não forem necessários à análise agronômica. Se a identificação for necessária ou a remoção não for suficiente, o uso deve passar por avaliação específica da finalidade, da base legal e das responsabilidades das partes, com apoio jurídico quando necessário. Essas medidas seguem os princípios de finalidade, necessidade e segurança da [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm); sua aplicação concreta depende dos dados e do papel de cada parte.

Também é necessário verificar se o acervo inclui fotografias enviadas por usuários do aplicativo, quais informações lhes foram fornecidas e se existe política interna de privacidade aplicável. A definição dos responsáveis pelo tratamento de eventuais dados pessoais depende dessa análise.

### 7. Uso de bases públicas complementares

Uma base pública somente deve ser incorporada após registrar sua origem, versão ou endereço de referência, licença e condições de uso; verificar a compatibilidade dessas condições com as finalidades do projeto; avaliar adequação às culturas e classes do MVP, qualidade das imagens e presença de dados pessoais; e identificar duplicatas relevantes em relação ao acervo existente. A procedência e o resultado dessa avaliação devem acompanhar as imagens importadas.

Além da licença, a inclusão de cada base complementar depende de aprovação para o projeto. Essa aprovação deve registrar os limites de uso, redistribuição e publicação das imagens importadas.

### 8. Retenção e descarte

**Proposta da equipe:** conservar imagens de desenvolvimento enquanto forem necessárias às atividades autorizadas; identificar quais imagens integram o dataset final e sob qual responsabilidade permanecerão; e revisar periodicamente cópias temporárias, duplicatas e imagens rejeitadas para descarte quando não houver finalidade ou obrigação de conservação. O descarte deve abranger originais, derivados e cópias acessíveis, conforme o ambiente de armazenamento, com registro do que foi excluído, quando e por quem. Cópias de segurança devem seguir o procedimento de expiração aplicável. A [ANPD observa que não há prazo único de tratamento aplicável a todos os casos](https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes); o prazo depende da finalidade e das circunstâncias.

Os prazos de retenção por categoria, o destino do dataset final e o procedimento de exclusão após o projeto ainda precisam ser definidos. Até lá, a equipe deve evitar cópias desnecessárias e manter identificáveis as imagens que deverão ser revisadas para descarte.

### 9. Responsabilidades

| Parte | Responsabilidade |
| --- | --- |
| Agro App | Fornecer o acervo principal e esclarecer sua origem, permissões, restrições de uso e políticas aplicáveis. |
| Equipe do projeto | Organizar e preparar o dataset, aplicar os controles definidos e registrar o uso e o descarte das imagens. |
| Responsáveis técnicos/agronômicos | Apoiar a revisão da adequação agronômica das imagens, culturas, classes e rótulos. |
| Responsáveis pela governança do dataset | Manter o catálogo, as evidências de permissão, o histórico de alterações e a revisão de acessos e retenção. As pessoas que exercerão essa função ainda precisam ser designadas. |

As responsabilidades operacionais da tabela não definem, por si só, os papéis legais de controlador e operador previstos na LGPD. Caso haja tratamento de dados pessoais, esses papéis devem ser avaliados conforme as decisões efetivamente tomadas por cada parte sobre finalidade e meios do tratamento, considerando as [definições da ANPD para agentes de tratamento](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados).

### 10. Riscos e medidas de mitigação

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Imagem sem origem comprovada | Perda de rastreabilidade e dificuldade de justificar seu uso. | Registrar procedência e impedir a inclusão até esclarecimento. |
| Ausência de autorização de uso | Uso fora das condições permitidas. | Guardar evidência da permissão e verificar cada finalidade antes do uso. |
| Dados pessoais na imagem ou nos metadados | Exposição indevida de pessoas identificáveis. | Inspecionar imagens e metadados, minimizar dados e restringir acesso. |
| Vazamento do dataset | Divulgação não autorizada do acervo. | Restringir acessos, evitar exposição pública e aplicar controles ao armazenamento e às cópias. |
| Uso indevido de base pública | Violação de licença ou incorporação de dados inadequados. | Verificar licença, procedência, qualidade e aprovação antes da importação. |
| Imagens duplicadas | Distorção na composição e na avaliação do dataset. | Identificar duplicatas e revisar sua distribuição entre treino, validação e teste. |
| Rótulos incorretos | Treinamento e avaliação comprometidos. | Submeter rótulos duvidosos à revisão técnica e registrar correções. |
| Perda de rastreabilidade | Impossibilidade de reconstruir a origem e o uso das imagens. | Manter identificadores, catálogo, evidências e histórico de alterações. |

### 11. Definições necessárias para uso do acervo

| Definição | Por que é necessária |
| --- | --- |
| Direitos e autorizações do acervo principal para treinamento, validação e teste. | Delimitar as finalidades permitidas e documentar sua evidência. |
| Origem de fotografias enviadas por usuários e informações fornecidas a eles. | Avaliar permissões de uso e eventual tratamento de dados pessoais. |
| Ambiente de armazenamento, pessoas autorizadas e regras de segurança. | Proteger o acervo desde seu recebimento. |
| Uso em documentação, apresentações, compartilhamento e publicação. | Evitar divulgação além das permissões existentes. |
| Bases públicas complementares aprovadas e respectivas condições. | Verificar licença, adequação e limites de uso antes da importação. |
| Prazos de retenção por categoria, destino do dataset final e responsáveis pelo descarte. | Planejar a conservação e a exclusão de originais, derivados e cópias. |
| Políticas internas aplicáveis e papéis relativos a dados pessoais. | Alinhar os controles do projeto às regras existentes e às responsabilidades de cada parte. |

Essas definições devem ser registradas com a decisão tomada, o responsável e a evidência correspondente antes da etapa do projeto que dependa delas.

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

Consolidação dos requisitos não funcionais levantados para o módulo de diagnóstico visual, em formato verificável. Valores marcados com ⧗ dependem de resposta do parceiro e estão preenchidos com proposta da equipe.

| ID | Requisito | Métrica | Valor | Verificação |
| --- | --- | --- | --- | --- |
| RNF-01 | Tamanho do modelo embarcado | MB do .tflite | ≤ 8 MB ⧗ | Medição do arquivo gerado |
| RNF-02 | Acréscimo total ao pacote | MB | ≤ 9 MB ⧗ | Modelo + rótulos + índice |
| RNF-03 | Latência fim a fim | p95, device de referência | ≤ 3 s ⧗ | 50 execuções, modo avião |
| RNF-04 | Latência de inferência isolada | p95 | ≤ 300 ms ⧗ | TFLite Benchmark Tool |
| RNF-05 | Operação offline | Chamadas de rede no fluxo | 0 | Modo avião + inspeção de tráfego |
| RNF-06 | Perda por quantização | Δ acurácia macro float → int8 | ≤ 2 p.p. ⧗ | Avaliação no conjunto de teste |
| RNF-07 | Pico de memória na inferência | MB de RAM | ⧗ (RQ-C07) | Profiler no device de referência |
| RNF-08 | Resolução de rota do diagnóstico | % de classes que resolvem para conteúdo válido | 100% | Teste automatizado sobre o índice |
| RNF-09 | Degradação sem aceleração | Funcionamento com XNNPACK/CPU apenas | Obrigatório | Execução com delegates desativados |

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


# 3. Entendimento dos dados

Para consultar o código e as etapas de geração dos arquivos desta seção, acesse o [notebook do AgroApp no Google Colab](https://colab.research.google.com/drive/18igL8eeSBvpOwm9mstFra3c0GXk4uCVB).

## 3.1 Inventário do acervo

Esta seção registra inicialmente o inventário produzido a partir do primeiro acervo
recebido pelo projeto. A atualização referente à base ampliada disponibilizada pelo
parceiro é apresentada na sequência.

### Inventário inicial

#### Objetivo

Realizar a contagem das imagens do Agro App por cultura,
classe e ocorrência, consolidando os dados para análise
do conjunto recebido.

#### Metodologia

O inventário foi realizado automaticamente com Python
no Google Colab, percorrendo a estrutura de diretórios
do conjunto de dados armazenado no Google Drive.

[Link do Colab](https://colab.research.google.com/drive/18igL8eeSBvpOwm9mstFra3c0GXk4uCVB)

Estrutura considerada:

```text
Agro App/
├── Soja/
│   ├── Doencas/
│   └── Pragas/
└── Milho/
    └── Pragas/
```

Cada subpasta de ocorrência foi identificada e a quantidade
de imagens presente nela foi contabilizada.

#### Resultados

| Cultura | Classe | Quantidade de imagens |
|---------|---------|----------------------:|
| Soja | Doenças | 97 |
| Soja | Pragas | 13 |
| Milho | Pragas | 16 |
| **Total** | | **126** |

Foram identificadas 126 imagens distribuídas em 55
ocorrências.

A relação completa das imagens por cultura, classe e ocorrência está disponível em:

[Inventário do Agro App](https://docs.google.com/spreadsheets/d/1VAnspzW3pkyijLxPsg4IY85lJJX28dmgtZ5hci610FI/edit?usp=sharing)

Além disso, a planilha do inventário também está versionada no repositório em:

`assets/data/inventario-acervo.xlsx`

#### Observação

A associação formal entre os nomes das ocorrências e seus
respectivos agentes causais será complementada a partir do
dicionário de classes desenvolvido na T3.4.

### Atualização do inventário com o novo dataset

Após a elaboração do inventário inicial, o parceiro disponibilizou um novo dataset,
maior e mais estruturado, voltado à identificação de pragas das culturas de soja e
milho. Para atender ao objetivo da T3.1 com a base ampliada, foi realizada uma nova
consolidação das imagens por classe, cultura e agente causal.

#### Metodologia da atualização

O dataset atualizado reúne duas fontes:

- **AgroInsect:** 1.510 imagens de 4 classes, com metadados disponíveis em
  `labels.csv`;
- **iNaturalist / field:** 1.824 imagens de 13 classes, com metadados disponíveis
  em `field/field_labels.csv`.

Os metadados das duas fontes foram consolidados por `class_id` e associados a uma
taxonomia unificada de 14 classes. Para cada classe, foram registrados o nome
padronizado, o agente causal, o nome comum, a cultura relacionada e a quantidade
de imagens em cada fonte. O total de cada classe corresponde à soma das colunas
`agroinsect_imagens` e `field_imagens`.

Quando a coluna `cultura` apresenta `milho/soja`, a classe está relacionada às duas
culturas. Essa indicação não representa uma divisão das imagens entre elas, pois
as contagens disponibilizadas estão agregadas por classe e fonte.

#### Resultados da atualização

O acervo atualizado contém **3.334 imagens**, distribuídas em **14 classes**:
**1.510 imagens do AgroInsect** e **1.824 imagens do iNaturalist / field**.

| class_id | class_name | agente_causal | nome_comum | cultura | agroinsect_imagens | field_imagens | total_imagens |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 0 | diabrotica_speciosa | Diabrotica speciosa | vaquinha | milho/soja | 631 | 486 | 1.117 |
| 1 | dalbulus_maidis | Dalbulus maidis | cigarrinha-do-milho | milho | 217 | 0 | 217 |
| 2 | dichelops_sp | Diceraeus spp. | percevejo-barriga-verde | milho/soja | 279 | 14 | 293 |
| 3 | spodoptera_frugiperda | Spodoptera frugiperda | lagarta-do-cartucho | milho/soja | 383 | 79 | 462 |
| 4 | euschistus_heros | Euschistus heros | percevejo-marrom | soja | 0 | 65 | 65 |
| 5 | nezara_viridula | Nezara viridula | percevejo-verde | soja | 0 | 95 | 95 |
| 6 | edessa_meditabunda | Edessa meditabunda | percevejo-asa-preta | soja | 0 | 75 | 75 |
| 7 | leptoglossus_zonatus | Leptoglossus zonatus | percevejo-do-milho | milho | 0 | 79 | 79 |
| 8 | chrysodeixis_includens | Chrysodeixis includens | lagarta-falsa-medideira | soja | 0 | 82 | 82 |
| 9 | anticarsia_gemmatalis | Anticarsia gemmatalis | lagarta-da-soja | soja | 0 | 41 | 41 |
| 10 | spodoptera_eridania | Spodoptera eridania | lagarta-das-vagens | soja | 0 | 99 | 99 |
| 11 | spodoptera_cosmioides | Spodoptera cosmioides | lagarta-das-vagens | soja | 0 | 60 | 60 |
| 12 | astylus_variegatus | Astylus variegatus | larva-angorá | milho | 0 | 481 | 481 |
| 13 | deois_flavopicta | Deois flavopicta | cigarrinha-das-pastagens | milho | 0 | 168 | 168 |
| **Total** | **14 classes** |  |  | **soja e milho** | **1.510** | **1.824** | **3.334** |

#### Conclusão

O inventário atualizado consolida 3.334 imagens distribuídas em 14 classes de pragas associadas às culturas de soja e milho. A base combina imagens do AgroInsect e do iNaturalist, permitindo visualizar a distribuição das amostras por classe e fonte. Esses dados servirão de base para as etapas seguintes de análise de qualidade, definição das classes do MVP e preparação do dataset.

## 3.2 Análise exploratória visual

### Objetivo

Analisar amostras representativas de cada classe do acervo (Milho e Soja) e registrar
as principais características visuais que ajudam a diferenciar classes semelhantes,
identificando os pares e clusters de classes com maior risco de confusão para o modelo
e o que, na prática, permite distingui-los (cor, formato da lesão, textura, parte da
planta afetada).

### Metodologia


Etapas:

1. Observação em bloco. As imagens de cada classe foram reunidas em folhas de
   contato por bloco — Milho/Pragas, Soja/Pragas e Soja/Doenças —
   para permitir uma primeira varredura comparativa entre classes vizinhas.
2. Levantamento de pares candidatos. A partir da varredura e da semelhança de
   nomenclatura entre classes (ex.: várias classes com "podridão", "mancha" ou
   "nematóide" no nome), foram levantados pares e clusters candidatos a confusão.
3. Validação Cada par candidato só foi considerado
   efetivamente confuso após a checagem individual das imagens, pares com nomes parecidos mas distintas nessa
   checagem foram descartados (ver [Pares avaliados e descartados](#pares-avaliados-e-descartados)).

4. Registro. Para cada par/cluster confirmado, foi registrado o que efetivamente
   causa a confusão e o que permite diferenciar as classes, consolidado nas pranchas comparativas desta seção.

Como o acervo ainda é pequeno, todas as imagens disponíveis foram observadas, não
apenas uma amostra de 5 a 10 por classe.

### Resultados

#### Classes e imagens observadas

| Cultura | Bloco | Classes | Imagens observadas |
| --- | --- | --- | --- |
| Milho | Pragas | 4 | 16  |
| Soja | Pragas | 10 | 13  |
| Soja | Doenças | 41 | 97  |
| **Total** | | **55** | **126** |

#### Características visuais por classe

**Milho — Pragas**

| Classe | Característica visual predominante |
| --- | --- |
| Percevejo-do-milho | corpo em escudo, marrom-escuro/preto com faixa clara e pernas com pontas laranja; ninfas em cluster avermelhado; ovos em fileira |
| Pulgão-do-milho | sempre em colônia densa (nunca inseto isolado), concentrada no cartucho/base do pendão; textura granulada verde-escura/cinza com pontos brancos |
| Coró-do-milho | larva em "C", branco-acinzentada/azulada, cabeça marrom-alaranjada, sempre em ambiente de solo |
| Cigarrinha do milho | inseto adulto minúsculo, alongado, amarelo-pálido (raro nas fotos); maioria das imagens mostra o sintoma indireto — estrias cloróticas ou avermelhamento da folha |

**Soja — Pragas**

| Classe | Característica visual predominante |
| --- | --- |
| Percevejo da Soja | inseto escudo verde-acinzentado, adulto, sobre vagem |
| Broca-das-axilas-da-soja | lagarta verde-clara, corpo mole segmentado, dentro de broto/folha enrolada |
| Broca das vagens | mesma lagarta verde-clara, dentro da vagem |
| Lagarta-da-soja | lagarta listrada verde/preta, borda da folha consumida |
| Cascudinho-da-soja | besouro pequeno marrom-acinzentado, corpo oval compacto |
| Gorgulho-da-soja, Tamanduá-da-soja | besouro preto pequeno com marca clara em cruz/X sobre os élitros |
| Tamanduá-da-soja | mesmo padrão de besouro preto com marca clara em cruz/X |
| Coró da soja / Coró-da-soja, bicho-bolo / Coró-da-soja-do-cerrado | larva branca em "C", cabeça marrom, corpo translúcido, sobre terra |

**Soja — Doenças (agrupadas por padrão visual)**

| Grupo | Classes | Característica visual predominante |
| --- | --- | --- |
| Podridões de raiz/colo/haste | Podridão-de-raízes; Podridão-preta-das-raízes/Podridão-cinzenta-do-caule; Podridão-radicular; Estiolamento/Tombamento-de-mudas; Cancro-da-haste; Macrophomina; Podridão radicular de Phytophthora; Murcha-de-fusarium; Podridão-vermelha-da-raiz; Fusariose | raiz ou caule escurecido/apodrecido; variações vão de fibras enegrecidas a lesão roxo-avermelhada no colo |
| Manchas foliares | Mancha-aureolada; Mancha-parda/Septoriose; Crestamento bacteriano; Mancha alvo; Mancha-olho-de-rã; Pústula bacteriana; Clodosporiose/Verrugose; Oídio; Mela ou requeima; Ferrugem asiática; Míldio | folha verde/amarelada com manchas ou pontuações escuras; diferenciadores no detalhe, halo, formato circular, tamanho e densidade dos pontos |
| Nematoides | Nematóide-reniforme; nematóide de cisto da soja (NCS); Nematóide-espiralado; Nematóide de galhas; Nematóide das lesões; Nematóide de cisto | sintoma indireto (reboleira, planta atrofiada) ou sinal direto na raiz |
| Sementes/grãos e vagens armazenados | Fungo-de-armazenamento; Fungo de pós colheita; Tombamento; Fungo-de-pós-colheita/Podridão-dos-grãos-armazenados; Phomopsis-da-semente; Antracnose; Podridão da semente/Podridão de Fusarium; Seca da haste e da vagem |  semente/vagem coberta por esporos, cor e textura do mofo variam  |
| Sistêmicas / murcha / vírus | Mofo-branco/Podridão-de-sclerotinia; Murcha-de-Sclerotium; Damping-off/Podridão-aquosa; Nematoide-da-haste verde/Ponta Branca; Mosaico comum da soja | planta murcha ou com micélio branco visível no colo; mosaico é a única com padrão de mosqueado na folha e no grão |

#### Pares e clusters de classes visualmente confundíveis

| # | Classes | O que causa a confusão | O que diferencia | Prancha |
| --- | --- | --- | --- | --- |
| 1 | Coró da soja × Coró-da-soja, bicho-bolo × Coró-da-soja-do-cerrado | mesma larva branca em "C", cabeça marrom, sobre terra | sem escala de referência ou o besouro adulto ao lado, a foto isolada não identifica a espécie | Figura 1 |
| 2 | Tombamento × Fungo-de-pós-colheita, Podridão-dos-grãos-armazenados | textura granular idêntica (esporulação dourada/marrom cobrindo a semente) | praticamente nenhuma, pelo visual isolado, diferenciação depende do estágio/local relatado, não da imagem | Figura 1 |
| 3 | Ferrugem asiática × Míldio | folha verde/amarelada com pequenos pontos marrom-avermelhados espalhados entre nervuras | diferença real (pústula com esporulação × halo anguloso) só aparece de perto, na face inferior da folha | Figura 1 |
| 4 | Podridão-vermelha-da-raiz × Fusariose, Podridão vermelha da raiz | mesma lesão — estria roxo-avermelhada sobre caule bege, na altura da raiz | nenhuma diferença visual identificada; ver [duplicidades de rótulo](#possíveis-duplicidades-de-rótulo) | Figura 1 |
| 5 | Tamanduá-da-soja × Gorgulho-da-soja, Tamanduá-da-soja | mesmo besouro preto pequeno com marca clara em cruz/X sobre os élitros | não identificado no material disponível | Figura 2 |
| 6 | Broca das vagens × Broca-das-axilas-da-soja | mesma lagarta verde-clara, corpo mole segmentado, cabeça marrom | local da foto (dentro da vagem × dentro do broto/axila), sem esse contexto, a lagarta isolada é praticamente idêntica | Figura 2 |
| 7 | Podridão-preta-das-raízes/Podridão-cinzenta-do-caule × Podridão-cinzenta-do-caule/Podridão-preta-das-raízes | mesmo nome invertido; mesma imagem de caule acinzentado com casca descascando | nenhuma diferença visual identificada; ver [duplicidades de rótulo](#possíveis-duplicidades-de-rótulo) | Figura 3 |
| 8 | Mancha-parda/Septoriose × Crestamento bacteriano × Clodosporiose/Verrugose × Mancha alvo × Pústula bacteriana | folha verde/amarelada coberta de pequenas manchas escuras — padrão geral confunde à primeira vista | Mancha alvo: anéis concêntricos nítidos (único padrão "alvo"). Crestamento bacteriano: manchas angulares, delimitadas pelas nervuras. Pústula bacteriana: pontos muito menores e mais numerosos. Clodosporiose/Verrugose: manchas redondas maiores, levemente ásperas. Mancha-parda/Septoriose: manchas irregulares, mais escuras e densas, sem halo definido | Figura 4 |



#### Possíveis duplicidades de rótulo

Alguns pares acima não parecem ser apenas visualmente parecidos, mas sim a mesma
doença cadastrada duas vezes no acervo:

- **Podridão-vermelha-da-raiz** × **Fusariose, Podridão vermelha da raiz**, nomes já
  se sobrepõem; imagens mostram a mesma lesão.
- **Podridão-preta-das-raízes, Podridão-cinzenta-do-caule** × **Podridão-cinzenta-do-caule,
  Podridão-preta-das-raízes** , mesmo nome, apenas invertido.
- **nematóide de cisto da soja (NCS)** × **Nematóide de cisto**, mesmo padrão visual,
  raízes com pequenos cistos esféricos aderidos.


#### Pranchas comparativas

<div align="center">
  <p><strong>Figura 1 — Prancha comparativa, Soja (clusters de doenças e pragas)</strong></p>
  <img src="../assets/prancha-soja-clusters-1.png" alt="Prancha comparativa dos clusters confusos da Soja: corós, mofo granular, Ferrugem asiática x Míldio, Podridão-vermelha-da-raiz x Fusariose">
  <p><em>Fonte: Próprios autores (2026).</em></p>
</div>

<div align="center">
  <p><strong>Figura 2 — Prancha comparativa, Soja (pragas, continuação)</strong></p>
  <img src="../assets/prancha-soja-pragas-2.png" alt="Prancha comparativa: Tamanduá-da-soja x Gorgulho-da-soja e Broca das vagens x Broca-das-axilas-da-soja">
  <p><em>Fonte: Próprios autores (2026).</em></p>
</div>

<div align="center">
  <p><strong>Figura 3 — Prancha comparativa, Soja (duplicidade de rótulo — caule/raiz)</strong></p>
  <img src="../assets/prancha-soja-duplicidade-caule.png" alt="Prancha comparativa entre as classes 03 e 16, com nomes invertidos e mesma imagem de caule">
  <p><em>Fonte: Próprios autores (2026).</em></p>
</div>

<div align="center">
  <p><strong>Figura 4 — Prancha comparativa, Soja (cluster de manchas foliares)</strong></p>
  <img src="../assets/prancha-soja-manchas-foliares.png" alt="Prancha comparativa das cinco doencas foliares de folha manchada: Mancha-parda, Crestamento bacteriano, Clodosporiose, Mancha alvo e Pustula bacteriana">
  <p><em>Fonte: Próprios autores (2026).</em></p>
</div>

### Observação

Boa parte das classes de Soja/Doenças tem hoje apenas 1 a 3 imagens, abaixo do volume
desejável de 5 a 10 indicado como objetivo mínimo para avaliação visual, a análise foi feita com
todo o material disponível, mas os pares e clusters aqui identificados devem ser
revisados quando o acervo for complementado pelo parceiro ou por bases públicas

validadas (Seção 1.4, item 7). A associação formal entre os pares/clusters aqui
levantados e a decisão de unificar ou manter classes separadas será complementada a
partir do dicionário de classes desenvolvido na T3.4.

---

# 4. Preparação dos dados

## 4.3 Estratégia de balanceamento (T4.3)

### Objetivo e decisão

Adotar **ponderação de classes na função de perda**, com amostragem natural das imagens de treino, como estratégia inicial para reduzir a preferência do modelo pelas classes mais frequentes. A reamostragem será avaliada em um experimento separado caso a ponderação não ofereça recuperação adequada das classes minoritárias. Não aplicar as duas correções simultaneamente na configuração inicial.

Esta é uma decisão de preparação para o treinamento, ainda sem resultados experimentais. O repositório já contém um [particionamento das 13 classes do modelo](../assets/data/particionamento_T4_2/manifesto_modelo.csv), que aguarda revisão; não há modelo treinado. Os pesos para os experimentos deverão ser calculados a partir das contagens de treino dessa versão após a revisão. A estratégia atende à mitigação do risco R02 e deve ser reavaliada quando o acervo for ampliado.

### Diagnóstico do acervo

As tabelas abaixo registram o **inventário inicial** do acervo, obtido do [inventário versionado](../assets/data/inventario-acervo.xlsx). Suas 55 ocorrências foram tratadas como rótulos candidatos, não como classes do modelo atual. O particionamento provisório posterior reuniu **64 rótulos candidatos** dos acervos antigo e novo; a [T3.5](#35-classes-do-mvp) selecionou **13 classes de saída**. O [resumo do particionamento do modelo](../assets/data/particionamento_T4_2/resumo_modelo.csv) registra 2.214 imagens de treino nessas 13 classes, de 30 a 735 por classe. É essa distribuição de treino que deve orientar os pesos dos experimentos, após a revisão do manifesto.

| Cultura e categoria | Ocorrências | Imagens | Menor / maior contagem por ocorrência |
| --- | ---: | ---: | ---: |
| Milho — Pragas | 4 | 16 | 2 / 5 |
| Soja — Pragas | 10 | 13 | 1 / 2 |
| Soja — Doenças | 41 | 97 | 1 / 5 |
| **Total** | **55** | **126** | **1 / 5** |

| Imagens por ocorrência | Quantidade de ocorrências | Total de imagens |
| ---: | ---: | ---: |
| 1 | 15 | 15 |
| 2 | 21 | 42 |
| 3 | 10 | 30 |
| 4 | 6 | 24 |
| 5 | 3 | 15 |
| **Total** | **55** | **126** |

A razão entre a maior e a menor ocorrência **nesse inventário inicial** é **5:1**, e **36 de 55 ocorrências (65,5%)** possuem no máximo duas imagens. Soja/doenças reúne 97 de 126 imagens (77,0%), distribuídas entre 41 ocorrências. Esses dados justificaram a análise inicial de balanceamento, mas não descrevem a distribuição das 13 classes selecionadas. Se houver modelos separados por cultura, as frequências e os pesos serão calculados separadamente para cada modelo.

A limitação principal combina desbalanceamento e escassez de exemplos independentes. Nenhuma técnica de balanceamento substitui a coleta de imagens novas, a revisão de rótulos ambíguos ou a definição de classes visualmente distinguíveis.

### Comparação das abordagens

| Abordagem | Benefício | Limitação no acervo atual | Decisão |
| --- | --- | --- | --- |
| Ponderação de classes | Aumenta a contribuição das classes raras na perda e conserva todas as imagens disponíveis. | Também aumenta a influência de erros de rótulo e pode favorecer memorização de classes com poucos exemplos. | Estratégia inicial, após revisão dos rótulos. |
| Sobreamostragem | Faz as classes raras aparecerem mais vezes nos lotes de treino. | Repete os mesmos exemplares; não acrescenta diversidade independente e pode causar sobreajuste. | Alternativa a comparar, sem pesos inversos simultâneos. |
| Subamostragem | Reduz a participação das classes mais frequentes. | Descartaria imagens úteis das classes majoritárias sem acrescentar diversidade às minoritárias. | Não adotar inicialmente. |
| Ponderação + sobreamostragem | Permite ajustar frequência e contribuição na perda separadamente. | Aplicar ambas integralmente sobrecorrige as classes raras e dificulta atribuir a origem de um ganho. | Não adotar inicialmente; exige novo experimento com pesos ajustados à distribuição efetivamente amostrada. |

A [documentação do TensorFlow sobre dados desbalanceados](https://www.tensorflow.org/tutorials/structured_data/imbalanced_data) apresenta ponderação e sobreamostragem e discute suas diferenças na atualização por lotes. Essa referência trata de classificação binária; a comparação experimental aqui será multiclasse, no acervo do Agro App, sem assumir transferência dos resultados do tutorial.

### Cálculo e aplicação dos pesos

Para cada classe aprovada `c`, calcular:

```text
N = número de imagens originais no conjunto de treino do modelo
K = número de classes aprovadas para esse modelo
n_c = número de imagens originais da classe c no treino
w_c = N / (K × n_c)
```

Essa é a regra de ponderação balanceada descrita pelo [scikit-learn em `compute_class_weight`](https://scikit-learn.org/stable/modules/generated/sklearn.utils.class_weight.compute_class_weight.html). Com amostragem natural, a contribuição potencial de cada classe passa a ser `n_c × w_c = N/K`. A média dos pesos sobre as imagens de treino é 1, preservando a escala média da ponderação.

No treinamento multiclasse, multiplicar a entropia cruzada de cada exemplo pelo peso de sua classe antes de calcular a média do lote. No fluxo Keras previsto para os experimentos, fornecer o mapa de índices de saída para pesos por meio de `class_weight`; não aplicar simultaneamente o mesmo peso via `sample_weight`. O mapa de índices deve corresponder exatamente ao manifesto de classes do modelo.

Como exemplo **ilustrativo**, usando todo o inventário como se fosse treino (`N = 126`, `K = 55`), uma ocorrência com uma imagem receberia peso `2,291`, enquanto uma com cinco receberia `0,458`. Esses valores demonstram a regra, mas **não são os pesos finais**: o inventário completo inclui imagens que poderão pertencer à validação ou ao teste e rótulos ainda em revisão.

Recalcular os pesos em cada partição de treinamento, inclusive em cada rodada de validação cruzada. Não utilizar as frequências de validação ou teste, nem contar versões aumentadas como novas imagens originais. Uma classe com `n_c = 0` torna a configuração inválida: revisar a partição ou o escopo antes de treinar, sem substituir a divisão por zero por um peso arbitrário.

### Partições, classes escassas e aumento de dados

1. Revisar rótulos e duplicatas antes de definir as classes e contar os exemplos. Registrar as decisões de fusão ou exclusão com rastreabilidade até o inventário.
2. Separar treino, validação e teste por grupos de origem: imagens idênticas, versões derivadas e fotos correlacionadas da mesma planta ou captura devem permanecer na mesma partição. Preservar as proporções de classes quando houver grupos suficientes; a separação por grupos tem prioridade sobre a estratificação. A [documentação do scikit-learn sobre validação cruzada](https://scikit-learn.org/stable/modules/cross_validation.html) descreve a combinação de grupos e estratificação.
3. Conferir a presença de exemplos independentes de cada classe nas partições. Uma única imagem não permite avaliar a mesma classe em treino e em uma partição independente. Duas imagens ou grupos não permitem representá-la simultaneamente em treino, validação e teste. Não forçar uma divisão percentual fixa quando a integridade dos grupos exigir outra distribuição.
4. Priorizar a complementação das classes insuficientes. Até que haja grupos independentes para treinamento, seleção e avaliação, tratá-las como exploratórias e não declarar desempenho validado para elas. Se for necessário restringir o MVP, registrar o escopo efetivamente avaliado; agrupamentos só podem decorrer de decisão agronômica, não da necessidade de aumentar contagens.
5. Aplicar aumento de dados somente depois da divisão, durante o treino, preservando o ID e a partição do original. Usar transformações moderadas e agronomicamente plausíveis, que não removam lesões nem alterem cores diagnósticas. As transformações deverão ser inspecionadas por amostra; não fixar parâmetros sem observar as imagens.

Validação e teste manterão suas imagens originais, com apenas o pré-processamento determinístico exigido pelo modelo, sem sobreamostragem, subamostragem ou pesos de balanceamento nas métricas. O conjunto de teste será reservado para avaliação final. Quando se usar validação cruzada para selecionar a estratégia, verificar previamente se cada classe possui grupos suficientes para as rodadas escolhidas e manter o teste separado.

### Plano de comparação e seleção

Comparar as configurações abaixo no mesmo escopo de classes avaliáveis e nas mesmas partições. Manter arquitetura, inicialização, transformações, orçamento de atualizações do otimizador e regra de parada equivalentes; registrar as sementes. Quando viável, usar três sementes por configuração e apresentar média e dispersão dos resultados.

| Experimento | Amostragem de treino | Peso na perda | Finalidade |
| --- | --- | --- | --- |
| E0 — Referência | Natural, embaralhada | 1 para todas as classes | Medir o comportamento sem correção. |
| E1 — Estratégia inicial | Natural, embaralhada | `N / (K × n_c)` | Medir o efeito da ponderação. |
| E2 — Alternativa | Selecionar a classe uniformemente e depois uma imagem dessa classe, com reposição | 1 para todas as classes | Medir o efeito da sobreamostragem sem dupla correção. |

Em E2, realizar exatamente o mesmo número de atualizações que nos demais experimentos e gerar transformações de treino a cada apresentação da imagem. A repetição não será registrada como aumento do número de imagens independentes. Não usar a quantidade de épocas isoladamente para igualar o orçamento se o tamanho lógico do conjunto amostrado mudar.

Selecionar a configuração pela **F1 macro na validação**, reportando também precisão, recall, F1 e suporte por classe, balanced accuracy (média do recall das classes) e matriz de confusão. A acurácia global será complementar. Classes sem exemplos em uma partição devem ser indicadas como não avaliadas, com a cobertura explicitada; não omitir silenciosamente essas classes nem interpretar métricas sem suporte como desempenho observado.

Verificar especialmente as classes minoritárias e os pares confundíveis apontados na análise visual. Se a correção elevar recall às custas de muitas identificações incorretas, investigar a matriz de confusão e a precisão por classe antes de adotá-la. Em caso de resultados próximos à variação entre sementes, preferir a configuração mais simples; se E1 não apresentar benefício demonstrável frente a E0, registrar o resultado e rever a decisão inicial. Não escolher a estratégia a partir do teste final.

Depois da seleção, ajustar a política de confiança usando somente dados de validação independentes: o balanceamento pode mudar a distribuição das saídas do modelo. Confirmar o desempenho e o comportamento inconclusivo no teste final, inclusive após a quantização. Não interpretar a confiança bruta como probabilidade calibrada sem avaliação.

### Registros e critérios de conclusão

O experimento deverá guardar versão do dataset, classes aprovadas e respectivos índices, IDs e grupos de cada partição, contagens originais de treino por classe, pesos aplicados, configuração de amostragem, transformações, sementes, orçamento de treinamento e métricas por classe. Esses registros permitem reproduzir o cálculo e identificar alterações após a ampliação do acervo.

A **definição da T4.3** fica consolidada nesta seção: ponderação como escolha inicial, justificativa baseada no inventário, comparação das alternativas e protocolo de avaliação. A **validação experimental** ficará concluída após a revisão do particionamento das 13 classes, execução de E0/E1 (e E2 se necessário), registro das métricas e justificativa da configuração selecionada. Até lá, não há evidência para afirmar melhora de desempenho ou generalização nas classes do modelo.

validadas (Seção 1.4, item 7). O [dicionário de classes da T3.4](#dicionário-de-classes-t34)
registra as relações entre os rótulos candidatos a duplicidade. A decisão de unificar
ou manter classes separadas depende de validação agronômica e do conteúdo técnico do parceiro.

## 3.3 Diagnóstico de qualidade do acervo

### Objetivo

Avaliar resolução, enquadramento, presença de duplicatas e proporção de imagens de campo e de catálogo no acervo de soja e milho. O diagnóstico registra como esses fatores podem afetar a generalização do modelo de reconhecimento visual.

**Fonte das imagens analisadas:** imagens disponibilizadas pela equipe do Agro APP.

### Metodologia

A análise reúne **3.460 imagens** de três fontes: **3.334** da pasta `dataset` e **126** dos acervos de Milho e Soja. As planilhas registram, para cada imagem, a cultura, a categoria, a ocorrência, o caminho do arquivo, as dimensões, a legibilidade, o hash SHA-256, o hash perceptual, os alertas de qualidade e a decisão de seleção. A verificação seguiu estas etapas:

1. **Resolução e leitura:** conferir se o arquivo era legível, registrar largura e altura e sinalizar imagens cuja menor dimensão fosse inferior à referência de 224 pixels.
2. **Duplicatas:** comparar hashes SHA-256 para localizar arquivos idênticos e examinar os pares sugeridos pelo hash perceptual para identificar versões da mesma fotografia, inclusive quando aparecem em classes diferentes.
3. **Revisão por imagem:** conferir o enquadramento, a visibilidade do problema, o formato da imagem, a duplicidade e a coerência do rótulo; registrar a decisão (**manter**, **revisar** ou **excluir**) e sua justificativa. As 379 pendências foram examinadas visualmente. Outras 2.953 imagens de `dataset` conservam decisões de triagem automática, ainda sem inspeção visual individual.
4. **Consolidação:** agrupar os registros por fonte e classe, contar os alertas de qualidade e as decisões, e calcular as proporções de imagens de campo e de catálogo. Os alertas de resolução, desfoque e exposição podem se sobrepor e não determinam, isoladamente, a exclusão.

A unidade de contagem é o **registro de imagem**. Se uma mesma fotografia aparece em duas classes, ela contribui com um registro para cada classe. As abas de revisão e os resumos da planilha de decisões permitem rastrear os totais até cada imagem.

### Planilhas de diagnóstico e revisão

| Arquivo | Conteúdo e função |
| --- | --- |
| [Diagnóstico das três fontes](../assets/data/diagnostico_qualidade_T3_3_tres_fontes.xlsx) | Relatório de diagnóstico das 3.460 imagens de `dataset`, Milho e Soja, com indicadores de qualidade, resumos por classe e candidatos a duplicata. |
| [Planilha de decisões](../assets/data/diagnostico_qualidade_T3_3_revisado.xlsx) | Decisão **manter**, **excluir** ou **revisar** e justificativa por registro, além dos resumos e da conclusão dos pares de duplicatas visuais. |

 <p><em>Fonte: Próprios autores (2026).</em></p>

As abas de revisão preservam `largura`, `altura`, `menor_dimensao`, `megapixels`, `arquivo_legivel`, os alertas de nitidez e exposição, a decisão e a justificativa de cada foto. O **Resumo por classe** reúne os indicadores e as decisões por cultura, ocorrência e fonte. Megapixels medem o tamanho total da imagem, enquanto a menor dimensão e o enquadramento ajudam a verificar se o sinal relevante terá detalhe suficiente na entrada do modelo.

### Resultados

#### Visão geral

| Indicador | Resultado |
| --- | ---: |
| Imagens avaliadas | 3.460 |
| Ocorrências distintas registradas | 69 |
| Imagens legíveis | 3.460 |
| Imagens com menor dimensão abaixo de 224 pixels | 129 (3,7%) |
| Imagens possivelmente borradas | 29 (0,8%) |
| Imagens com exposição inadequada | 75 (2,2%) |
| Imagens de campo | 1.900 (54,9%) |
| Imagens de catálogo | 1.560 (45,1%) |
| Imagens marcadas para manter | 3.262 |
| Imagens marcadas para revisar | 0 |
| Imagens marcadas para excluir | 198 |

*Fonte: diagnóstico das três fontes e planilha de decisões (2026).*

Os **3.460 registros** incluem **1.824** fotos de campo e **1.510** imagens de catálogo de `dataset`, além de **16** imagens do acervo de Milho e **110** do acervo de Soja. Na pasta `dataset`, as decisões são **3.156 manter** e **178 excluir**. Das **379** pendências encontradas no conjunto, a inspeção visual indicou **214 manter** e **165 excluir**. Uma imagem adicional, anteriormente marcada para manter, foi excluída por repetir uma fotografia com rótulo conflitante. As justificativas individuais constam da planilha de decisões.

O limite de **224 pixels na menor dimensão** sinaliza imagens pequenas, mas não prova que sejam inutilizáveis; o detalhe relevante precisa ser conferido após o redimensionamento usado pelo modelo. O enquadramento manual foi registrado nas **126 imagens** dos acervos anteriores: **seis** receberam a marcação *distante*. Esse indicador não foi medido manualmente para as outras 3.334 imagens e, por isso, não aparece como total geral no quadro.

#### Duplicatas: critério essencial

Nas três fontes, foram encontrados **15 grupos de duplicatas exatas**, com **30 registros**, e **99 pares candidatos a duplicata visual** pelo hash perceptual. A inspeção dos 99 pares identificou **4 falsos positivos**, **2 pares da mesma foto com rótulos conflitantes** e **93 pares da mesma foto ou cena com versões redundantes**. Pares podem compartilhar imagens e não representam, necessariamente, 99 exclusões adicionais. Entre os 15 grupos exatos, **12** conservaram uma cópia; em **dois**, ambas foram excluídas por rótulos conflitantes; no grupo restante, foi selecionada uma versão equivalente fora do par exato. Os 30 registros desses grupos somam **12 manter** e **18 excluir**.

O quadro abaixo detalha **dois pares do acervo de Soja** que atravessam classes diferentes: um par exato, confirmado pelo SHA-256, e outro formado por versões da mesma fotografia. Esses casos exemplificam o risco de rótulos conflitantes preservado na análise visual:

| Classe de soja/doenças | Duplicatas exatas na classe | Versões quase iguais na classe | Imagem | Repetida de |
| --- | ---: | ---: | --- | --- |
| Estiolamento, Podridão-de-raízes, Tombamento-de-mudas | 1 | 0 | IMG_0030 | IMG_0098 |
| Podridão-de-raízes | 1 | 0 | IMG_0098 | IMG_0030 |
| Phomopsis-da-semente | 0 | 1 | IMG_0090 | IMG_0108 |
| Seca da haste e da vagem, Phomopsis-da-semente | 0 | 1 | IMG_0108 | IMG_0090 |

 <p><em>Fonte: Próprios autores (2026).</em></p>

IMG_0030 e IMG_0098 formam o par exato; IMG_0090 e IMG_0108 são versões da mesma foto. Os quatro registros foram excluídos da seleção para treinamento até que seus rótulos sejam conferidos e corrigidos. Antes de separar dados de treino e teste, deve-se manter versões da mesma fotografia no mesmo conjunto ou remover a redundância. Caso contrário, o modelo pode memorizar a imagem e a avaliação aparentar um desempenho maior do que teria em fotos novas. Rótulos conflitantes também podem ensinar associações contraditórias. A conclusão de cada par candidato está na aba **Duplicatas visuais** da planilha de decisões.

#### Campo e catálogo: critério essencial

**Campo** representa a imagem no contexto da lavoura. **Catálogo** representa uma imagem de referência, frequentemente isolada ou com apresentação controlada. É uma classificação do tipo de foto, não uma decisão automática de descarte.

| Fonte | Campo | Catálogo | Total |
| --- | ---: | ---: | ---: |
| `dataset` | 1.824 | 1.510 | 3.334 |
| Milho | 14 | 2 | 16 |
| Soja | 62 | 48 | 110 |
| **Total** | **1.900** | **1.560** | **3.460** |

 <p><em>Fonte: Próprios autores (2026).</em></p>

Em `dataset`, **54,7%** das imagens são de campo e **45,3%** de catálogo. Na avaliação manual dos acervos anteriores, **15 classes** tinham apenas imagens de catálogo, **18** apenas imagens de campo e **22** apresentavam os dois tipos. Se o uso real do AgroApp for fotografar plantas em campo, um modelo treinado em excesso com imagens de catálogo pode aprender fundos, iluminação ou enquadramentos que não representam esse uso. Isso pode reduzir sua capacidade de reconhecer a mesma ocorrência em fotos reais. Recomenda-se avaliar o modelo em fotos de campo separadas por fotografia de origem e acompanhar o desempenho por tipo de imagem e por classe. Este diagnóstico aponta um risco de generalização; ele não quantifica uma queda de desempenho.

#### Resolução e enquadramento: critério desejável

No conjunto das três fontes, **129 imagens** têm menor dimensão abaixo de 224 pixels, **29** foram sinalizadas como possivelmente borradas e **75** apresentam exposição inadequada. Esses alertas podem se sobrepor. Entre as **12 imagens pequenas** dos acervos anteriores, **5** foram excluídas e **7** mantidas após inspeção visual; as **6** com enquadramento distante foram excluídas. O limite de 224 pixels funciona como alerta, não como critério isolado de exclusão. As imagens abaixo preservam exemplos das decisões e justificativas da inspeção.

##### Imagens pequenas mantidas

| Imagem | Classe | Dimensões | Decisão |
| --- | --- | ---: | --- |
| IMG_0017 | Antracnose | 216 × 322 pixels | Manter |
| IMG_0018 | Antracnose | 322 × 211 pixels | Manter |
| IMG_0045 | Mancha-aureolada | 259 × 194 pixels | Manter |
| IMG_0099 | Podridão-preta-das-raízes, Podridão-cinzenta-do-caule | 259 × 195 pixels | Manter |
| IMG_0119 | Coró-da-soja-do-cerrado | 279 × 181 pixels | Manter |
| IMG_0121 | Coró-da-soja, bicho-bolo | 200 × 190 pixels | Manter |
| IMG_0122 | Gorgulho-da-soja, Tamanduá-da-soja | 287 × 220 pixels | Manter |

*Fonte: imagens disponibilizadas pela equipe do Agro APP.*

A decisão de manter essas imagens não elimina o alerta de resolução. A qualidade do sinal deve continuar sendo acompanhada após o redimensionamento do fluxo de treinamento.

##### Imagens pequenas excluídas

As cinco imagens abaixo foram retiradas da seleção para treinamento porque sua resolução é inferior à referência de 224 pixels na menor dimensão e o detalhe útil foi considerado insuficiente na revisão. A planilha preserva cada arquivo e registra **excluir** na coluna `decisao`, com a justificativa individual.

| Foto | Classe e dimensões | Por que excluir |
| --- | --- | --- |
| ![IMG_0021: três folhas com manchas escuras em imagem pequena](../assets/revisão_imagens/IMG_0021.jpg) | **IMG_0021** — Clodosporiose, Verrugose; 300 × 214 pixels | As lesões perdem detalhe com a baixa resolução.Além da imagem possuir outra imagem sobreposta. |
| ![IMG_0055: detalhe de folha com pequenos sinais claros em imagem pequena](../assets/revisão_imagens/IMG_0055.jpg) | **IMG_0055** — Míldio; 340 × 210 pixels | O detalhe do sintoma fica limitado pelo tamanho do arquivo. |
| ![IMG_0087: elemento claro muito pequeno sobre haste em imagem pequena](../assets/revisão_imagens/IMG_0087.jpg) | **IMG_0087** — Nematóide-reniforme; 251 × 200 pixels | O elemento observado dispõe de poucos pixels para reconhecimento junto a imagem ser de microcóspio. |
| ![IMG_0117: dois insetos em fotografia pequena](../assets/revisão_imagens/IMG_0117.jpg) | **IMG_0117** — Cascudinho-da-soja; 274 × 184 pixels | Os insetos têm detalhe insuficiente para uma entrada de treinamento confiável. |
| ![IMG_0125: percevejo em fotografia de resolução muito baixa](../assets/revisão_imagens/IMG_0125.jpg) | **IMG_0125** — Percevejo da Soja; 121 × 136 pixels | A resolução é muito baixa e limita fortemente a identificação do inseto. |

*Fonte: imagens disponibilizadas pela equipe do Agro APP.*

##### Imagens com enquadramento distante excluídas

Foram marcadas como **excluir** as imagens **IMG_0014**, **IMG_0029**, **IMG_0042**, **IMG_0072**, **IMG_0073** e **IMG_0078**. Nelas, a infestação, a muda ou os sinais associados à classe aparecem pequenos demais ou não são visíveis. Mesmo quando o arquivo tem dimensões grandes, a informação necessária para reconhecer a ocorrência ocupa poucos pixels. Por isso, essas fotos não são adequadas para treinar o reconhecimento da ocorrência específica. Os exemplos abaixo preservam as justificativas dessa inspeção visual.

| Foto | Classe e motivo da exclusão |
| --- | --- |
| ![IMG_0042: vista ampla de lavoura de soja, sem detalhe de lesões individuais](../assets/revisão_imagens/IMG_0042.jpg) | **IMG_0042 — Macrophomina.** A fotografia mostra a lavoura à distância. O sinal específico da classe não pode ser distinguido na imagem. |
| ![IMG_0078: vista panorâmica de lavoura de soja, sem raízes ou cistos visíveis](../assets/revisão_imagens/IMG_0078.jpg) | **IMG_0078 — Nematóide de cisto.** A fotografia mostra as linhas da lavoura, mas não as raízes ou os cistos necessários para identificar a ocorrência. |

*Fonte: imagens disponibilizadas pela equipe do Agro APP.*

As fotos acima são exemplos de um problema de **escala do objeto na cena**, não de tamanho do arquivo. Fotos distantes podem levar o modelo a aprender características gerais da lavoura ou do fundo em vez dos sinais da classe, prejudicando a generalização para novas capturas.

#### Imagem incompatível com o rótulo

A **IMG_0067** também foi marcada como **excluir**. Ela está na pasta `Soja/Doencas/21 - Murcha-de-fusarium, Murcha`, mas mostra plantas com **frutos vermelhos** e tem baixa qualidade visual. O conteúdo não corresponde de forma confiável à cultura e à ocorrência registradas. Não deve ser usada no treinamento do modelo; o rótulo precisa de validação técnica antes de qualquer reaproveitamento.

![IMG_0067: plantas com frutos vermelhos; imagem de baixa qualidade, incompatível com a classe de soja registrada](../assets/revisão_imagens/IMG_0067.jpg)

*Fonte: imagens disponibilizadas pela equipe do Agro APP.*

Imagens com conteúdo incompatível com a classe, cultura não confirmada ou qualidade visual insuficiente devem ser retiradas da seleção de treinamento. Caso se deseje reaproveitá-las em outro conjunto, é necessário validar a origem e o rótulo antes.



#### Imagens em formato técnico ou de montagem

As imagens **IMG_0031**, **IMG_0036** e **IMG_0070** também foram marcadas como **excluir**. A [persona e sua jornada](#13-persona-e-jornada-do-usuário) descrevem uma estudante que fotografa plantas durante atividades de campo com o AgroApp. A entrada esperada para o modelo é, portanto, uma fotografia única capturada nessa situação. Uma imagem de microscópio ou uma montagem preparada apresenta enquadramento e pistas visuais diferentes dos que o aplicativo receberá. Incluí-las no treinamento pode fazer o modelo aprender características do material técnico, como bordas, margens e divisão da imagem, em vez dos sinais da ocorrência.

| Foto | Classe e justificativa da exclusão |
| --- | --- |
| ![IMG_0031: detalhe microscópico com campo circular e bordas escuras](../assets/revisão_imagens/IMG_0031.jpg) | **IMG_0031 — Ferrugem asiática.** O campo circular indica uma captura microscópica de laboratório, que não corresponde à fotografia da planta feita pela persona em campo. |
| ![IMG_0036: montagem de duas imagens de sementes sobre fundo branco amplo](../assets/revisão_imagens/IMG_0036.jpg) | **IMG_0036 — Fungo-de-armazenamento.** Duas imagens pequenas foram reunidas em uma apresentação técnica com margens amplas; o arquivo não representa uma captura única no aplicativo. |
| ![IMG_0070: montagem lado a lado de duas cenas de plantas](../assets/revisão_imagens/IMG_0070.jpg) | **IMG_0070 — Nematoide-da-haste verde, Ponta Branca.** A montagem compara duas cenas em um único arquivo. Embora as cenas mostrem plantas, esse formato preparado não corresponde à foto única que a persona enviará. |

*Fonte: imagens disponibilizadas pela equipe do Agro APP.*

Essas exclusões se referem ao treinamento do modelo de reconhecimento por fotos capturadas no uso previsto. Os arquivos originais continuam preservados como material técnico de referência.

### Observação

**Nenhuma imagem permanece em revisar** na planilha de decisões. A inspeção visual cobriu as **126 imagens** dos acervos anteriores e **381 imagens distintas de `dataset`**, incluindo as pendências e amostras adicionais. Outras **2.953 imagens de `dataset`** conservam decisões de triagem automática e ainda precisam de inspeção individual antes da definição do conjunto final de treinamento. A marcação **excluir** retira a imagem da seleção de treinamento; os arquivos originais foram preservados. Não foram feitos testes de desempenho do modelo para quantificar o efeito das exclusões.
## Dicionário de classes (T3.4)

O dicionário relaciona as **55 ocorrências e 126 imagens** do inventário às culturas, aos agentes causais de referência e ao vínculo de conteúdo técnico. Cobre 4 ocorrências de milho/pragas (16 imagens), 10 de soja/pragas (13 imagens) e 41 de soja/doenças (97 imagens). Não inclui classes de plantas daninhas, deficiências ou plantas sadias, pois não há registros dessas categorias no inventário recebido.

O arquivo [dicionario-classes.json](../assets/data/dicionario-classes.json) é a fonte estruturada desta entrega. A origem dos rótulos e das contagens é o [inventário versionado](../assets/data/inventario-acervo.xlsx). Os agentes são referências bibliográficas para revisão agronômica, não diagnósticos confirmados das imagens. A confirmação da identidade de cada ocorrência depende do parceiro.

### Campos e convenções

| Campo JSON | Significado e regra |
| --- | --- |
| `id` | Identificador único e estável, de `AGRO-001` a `AGRO-055`. A ordem inicial acompanha as linhas preenchidas do inventário. Não reutilizar IDs nem renumerar após revisão. Não representa o índice de saída do modelo. |
| `cultura` | Soja ou Milho; faz parte da identidade da ocorrência. |
| `categoria` | Pragas ou Doenças; o campo `classe` da planilha representa esta categoria, não uma classe individual de treinamento. |
| `rotulo_origem` | Texto exato da planilha, inclusive acentos decompostos, grafias e separadores. Permite rastrear a ocorrência. |
| `nome_comum` | Rótulo convertido para Unicode NFC para exibição, preservando a nomenclatura recebida. Correções de nomes exigem revisão, mantendo o rótulo de origem. |
| `quantidade_imagens` | Contagem registrada no inventário. |
| `agente_causal` | Táxon ou conjunto de táxons de referência; `null` quando o rótulo não permite associação suficientemente segura. Gênero seguido de `spp.` não identifica uma espécie. |
| `status_agente` | `referencia_a_validar` ou `indeterminado`; nenhuma imagem foi confirmada agronomicamente nesta entrega. |
| `fontes` | Códigos de referências bibliográficas definidos no objeto `fontes` do JSON. Lista vazia para agentes indeterminados. |
| `chave_conteudo` | Chave **oficial** do conteúdo técnico do Agro App. Atualmente `null` em todos os registros: o catálogo oficial não está no repositório. |
| `chave_conteudo_proposta` | Chave local única em ASCII (`cultura.ocorrencia.agro-NNN`) para organizar a futura integração. Não é uma URL, rota ou identificador existente do aplicativo. |
| `status_conteudo` | `aguardando_catalogo_agroapp`; mudar para `validado` somente após confirmar a chave oficial e a abertura do conteúdo correto. |
| `relacoes` | IDs de ocorrências candidatas a duplicidade ou revisão de identidade. Não autoriza união de classes. |

### Catálogo

Todas as chaves abaixo são **propostas locais**, ainda sem correspondência oficial validada. “Indeterminado” é uma pendência explícita, não uma nova classe do modelo.

<!-- tabela:inicio -->
| ID | Cultura | Categoria | Rótulo no inventário / nome comum | Agente causal de referência | Chave proposta |
| --- | --- | --- | --- | --- | --- |
| AGRO-001 | Milho | Pragas | Cigarrinha do milho | Dalbulus maidis | `milho.ocorrencia.agro-001` |
| AGRO-002 | Milho | Pragas | Coró-do-milho | Indeterminado — revisão necessária | `milho.ocorrencia.agro-002` |
| AGRO-003 | Milho | Pragas | Percevejo-do-milho | Indeterminado — revisão necessária | `milho.ocorrencia.agro-003` |
| AGRO-004 | Milho | Pragas | Pulgão-do-milho | Rhopalosiphum maidis | `milho.ocorrencia.agro-004` |
| AGRO-005 | Soja | Doenças | Antracnose | Colletotrichum truncatum | `soja.ocorrencia.agro-005` |
| AGRO-006 | Soja | Doenças | Cancro-da-haste | Diaporthe aspalathi; Diaporthe caulivora | `soja.ocorrencia.agro-006` |
| AGRO-007 | Soja | Doenças | Clodosporiose, Verrugose | Indeterminado — revisão necessária | `soja.ocorrencia.agro-007` |
| AGRO-008 | Soja | Doenças | Crestamento bacteriano | Pseudomonas savastanoi pv. glycinea | `soja.ocorrencia.agro-008` |
| AGRO-009 | Soja | Doenças | Damping-off, Podridão-aquosa, Tombamento | Indeterminado — revisão necessária | `soja.ocorrencia.agro-009` |
| AGRO-010 | Soja | Doenças | Estiolamento, Podridão-de-raízes, Tombamento-de-mudas | Indeterminado — revisão necessária | `soja.ocorrencia.agro-010` |
| AGRO-011 | Soja | Doenças | Ferrugem asiática | Phakopsora pachyrhizi | `soja.ocorrencia.agro-011` |
| AGRO-012 | Soja | Doenças | Fungo de pós colheita | Indeterminado — revisão necessária | `soja.ocorrencia.agro-012` |
| AGRO-013 | Soja | Doenças | Fungo-de-armazenamento | Indeterminado — revisão necessária | `soja.ocorrencia.agro-013` |
| AGRO-014 | Soja | Doenças | Fungo-de-pós-colheita, Podridão-dos-grãos-armazenados | Indeterminado — revisão necessária | `soja.ocorrencia.agro-014` |
| AGRO-015 | Soja | Doenças | Fusariose, Podridão vermelha da raiz | Fusarium spp. (complexo de podridão vermelha da raiz) | `soja.ocorrencia.agro-015` |
| AGRO-016 | Soja | Doenças | Macrophomina | Macrophomina phaseolina | `soja.ocorrencia.agro-016` |
| AGRO-017 | Soja | Doenças | Mancha alvo | Corynespora cassiicola | `soja.ocorrencia.agro-017` |
| AGRO-018 | Soja | Doenças | Mancha-aureolada | Indeterminado — revisão necessária | `soja.ocorrencia.agro-018` |
| AGRO-019 | Soja | Doenças | Mancha-olho-de-rã | Cercospora sojina | `soja.ocorrencia.agro-019` |
| AGRO-020 | Soja | Doenças | Mancha-parda, Septoriose | Septoria glycines | `soja.ocorrencia.agro-020` |
| AGRO-021 | Soja | Doenças | Mela ou requeima | Rhizoctonia solani AG1 | `soja.ocorrencia.agro-021` |
| AGRO-022 | Soja | Doenças | Míldio | Peronospora manshurica | `soja.ocorrencia.agro-022` |
| AGRO-023 | Soja | Doenças | Mofo-branco, Podridão-de-sclerotinia | Sclerotinia sclerotiorum | `soja.ocorrencia.agro-023` |
| AGRO-024 | Soja | Doenças | Mosaico comum da soja | Soybean mosaic virus (SMV) | `soja.ocorrencia.agro-024` |
| AGRO-025 | Soja | Doenças | Murcha-de-Sclerotium | Sclerotium rolfsii | `soja.ocorrencia.agro-025` |
| AGRO-026 | Soja | Doenças | Murcha-de-fusarium, Murcha | Fusarium spp. | `soja.ocorrencia.agro-026` |
| AGRO-027 | Soja | Doenças | Nematoide-da-haste verde, Ponta Branca | Aphelenchoides besseyi | `soja.ocorrencia.agro-027` |
| AGRO-028 | Soja | Doenças | Nematóide das lesões | Pratylenchus spp. | `soja.ocorrencia.agro-028` |
| AGRO-029 | Soja | Doenças | Nematóide de cisto | Heterodera glycines | `soja.ocorrencia.agro-029` |
| AGRO-030 | Soja | Doenças | Nematóide de galhas | Meloidogyne spp. | `soja.ocorrencia.agro-030` |
| AGRO-031 | Soja | Doenças | Nematóide-espiralado, Nematóide | Helicotylenchus spp. | `soja.ocorrencia.agro-031` |
| AGRO-032 | Soja | Doenças | Nematóide-reniforme | Rotylenchulus reniformis | `soja.ocorrencia.agro-032` |
| AGRO-033 | Soja | Doenças | Oídio | Microsphaera diffusa (sinônimo: Erysiphe diffusa) | `soja.ocorrencia.agro-033` |
| AGRO-034 | Soja | Doenças | Phomopsis-da-semente | Diaporthe spp. (Phomopsis spp.) | `soja.ocorrencia.agro-034` |
| AGRO-035 | Soja | Doenças | Podridão da semente, Podridão de Fusarium | Fusarium spp. | `soja.ocorrencia.agro-035` |
| AGRO-036 | Soja | Doenças | Podridão radicular de Phytophthora | Phytophthora sojae | `soja.ocorrencia.agro-036` |
| AGRO-037 | Soja | Doenças | Podridão-cinzenta-do-caule, Podridão-preta-das-raízes | Macrophomina phaseolina | `soja.ocorrencia.agro-037` |
| AGRO-038 | Soja | Doenças | Podridão-de-raízes | Indeterminado — revisão necessária | `soja.ocorrencia.agro-038` |
| AGRO-039 | Soja | Doenças | Podridão-preta-das-raízes, Podridão-cinzenta-do-caule | Macrophomina phaseolina | `soja.ocorrencia.agro-039` |
| AGRO-040 | Soja | Doenças | Podridão-radicular | Indeterminado — revisão necessária | `soja.ocorrencia.agro-040` |
| AGRO-041 | Soja | Doenças | Podridão-vermelha-da-raiz | Fusarium spp. (complexo de podridão vermelha da raiz) | `soja.ocorrencia.agro-041` |
| AGRO-042 | Soja | Doenças | Pústula bacteriana | Xanthomonas axonopodis pv. glycines | `soja.ocorrencia.agro-042` |
| AGRO-043 | Soja | Doenças | Seca da haste e da vagem, Phomopsis-da-semente | Diaporthe spp. (Phomopsis spp.) | `soja.ocorrencia.agro-043` |
| AGRO-044 | Soja | Doenças | Tombamento | Indeterminado — revisão necessária | `soja.ocorrencia.agro-044` |
| AGRO-045 | Soja | Doenças | nematóide de cisto da soja (NCS) | Heterodera glycines | `soja.ocorrencia.agro-045` |
| AGRO-046 | Soja | Pragas | Broca das vagens - Soja | Indeterminado — revisão necessária | `soja.ocorrencia.agro-046` |
| AGRO-047 | Soja | Pragas | Broca-das-axilas-da-soja | Crocidosema aporema | `soja.ocorrencia.agro-047` |
| AGRO-048 | Soja | Pragas | Cascudinho-da-soja | Myochrous armatus | `soja.ocorrencia.agro-048` |
| AGRO-049 | Soja | Pragas | Coró da soja | Indeterminado — revisão necessária | `soja.ocorrencia.agro-049` |
| AGRO-050 | Soja | Pragas | Coró-da-soja-do-cerrado | Phyllophaga capillata | `soja.ocorrencia.agro-050` |
| AGRO-051 | Soja | Pragas | Coró-da-soja_ bicho-bolo | Indeterminado — revisão necessária | `soja.ocorrencia.agro-051` |
| AGRO-052 | Soja | Pragas | Gorgulho-da-soja_ Tamanduá-da-soja | Sternechus subsignatus | `soja.ocorrencia.agro-052` |
| AGRO-053 | Soja | Pragas | Lagarta-da-soja | Anticarsia gemmatalis | `soja.ocorrencia.agro-053` |
| AGRO-054 | Soja | Pragas | Percevejo da Soja | Indeterminado — revisão necessária | `soja.ocorrencia.agro-054` |
| AGRO-055 | Soja | Pragas | Tamanduá-da-soja | Sternechus subsignatus | `soja.ocorrencia.agro-055` |
<!-- tabela:fim -->

### Ambiguidades e duplicidades

- **AGRO-015 / AGRO-041:** fusariose e podridão vermelha da raiz; revisar a identidade e o complexo de espécies antes de unificar.
- **AGRO-016 / AGRO-037 / AGRO-039:** Macrophomina e os nomes invertidos de podridão cinzenta/preta; verificar se representam o mesmo conteúdo e a mesma classe.
- **AGRO-029 / AGRO-045:** nematoide de cisto, com agente de referência comum; preservar os registros até confirmação.
- **AGRO-052 / AGRO-055:** gorgulho/tamanduá; possível duplicidade de nomenclatura.
- **AGRO-049 / AGRO-050 / AGRO-051:** os nomes de corós não justificam atribuir a mesma espécie a todos. A referência de AGRO-050 é específica ao coró-do-cerrado; os demais permanecem indeterminados.
- **AGRO-046 / AGRO-047:** broca das vagens e broca das axilas requerem revisão de espécie e do local de ataque. Semelhança visual não confirma igualdade de agente.
- **AGRO-012 / AGRO-013 / AGRO-014 / AGRO-044:** fungos pós-colheita, armazenamento e tombamento são rótulos abrangentes. Não atribuir Aspergillus, Penicillium ou outro agente apenas pela aparência das sementes.
- **AGRO-002 / AGRO-003 / AGRO-054:** coró e percevejos podem representar diferentes espécies; o rótulo disponível não resolve essa escolha.
- **AGRO-007 / AGRO-018:** manter “Clodosporiose” e “Mancha-aureolada” como recebidos, aguardando correção ou confirmação agronômica.
- **AGRO-009 / AGRO-010 / AGRO-038 / AGRO-040:** tombamentos e podridões genéricos admitem causas distintas; não completar o agente por inferência do nome.

As relações registradas não modificam as 55 ocorrências do inventário. A seleção das classes do MVP e qualquer fusão devem registrar os IDs de origem, a justificativa e a evidência da decisão. O modelo deverá ter um manifesto próprio que associe cada índice de saída ao ID aprovado, sem depender da posição no JSON.

### Vinculação ao conteúdo técnico

1. Receber do Agro App o catálogo com chaves oficiais, cultura, título e mecanismo de acesso ao conteúdo.
2. Conferir, para cada ocorrência, cultura, agente e nome comum; obter confirmação agronômica nos casos ambíguos.
3. Preencher `chave_conteudo` com a chave real, mantendo a chave proposta apenas como referência local. Mais de uma ocorrência pode apontar ao mesmo conteúdo após aprovação.
4. Registrar a evidência e o responsável pela validação em novo campo `validacao_conteudo` (responsável, data e evidência) e mudar `status_conteudo` para `validado`.
5. Verificar a abertura do conteúdo correto, inclusive offline, para todas as classes selecionadas para o MVP, conforme RF-07, RF-08 e RNF-08.

Enquanto `chave_conteudo` for `null` ou o status não for `validado`, a integração não deve tentar navegar usando a chave proposta. Tratar a associação como indisponível. A entrega organiza o mapeamento, mas a resolução de 100% das rotas permanece dependente do catálogo oficial.

### Referências e manutenção

As associações usam como referência os [manuais de doenças de soja da Embrapa](https://www.embrapa.br/en/web/soja/busca-de-publicacoes/-/publicacao/991687/manual-de-identificacao-de-doencas-de-soja) e de [insetos e outros invertebrados da soja](https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja). As referências complementares estão identificadas no JSON por registro. Essa bibliografia não comprova a identidade dos exemplares do acervo nem substitui o catálogo técnico do parceiro.

Para atualizar a tabela após editar o JSON: `python assets/data/gerar_dicionario.py`. Para verificar cobertura do inventário, contagens, unicidade e integridade das relações: `python tests/validar_dicionario.py`. Os comandos usam somente a biblioteca padrão do Python.

## 3.5. Classes do MVP

### Objetivo

Definir quais classes de pragas e doenças entram e quais ficam de fora do MVP, com a justificativa de cada decisão.

### Metodologia

A definição partiu do [Inventário do acervo](#inventário-do-acervo) do Agro App, complementado por fotos de campo do iNaturalist e pelas imagens do AgroInsect. Os dados foram tratados como uma base única, desconsiderando imagens repetidas e figuras que não são fotografias. Classes com mais de uma pasta ou nome na base foram reunidas em uma só (por exemplo, os corós e as duas espécies da lagarta-das-vagens).

A decisão considerou dois pontos: o **volume de imagens**, principal critério, porque um volume maior dá melhores condições de treinar e avaliar o modelo, e a **qualidade das imagens**, isto é, se o inseto ou o sintoma aparece com nitidez. Entram as classes com maior volume e imagens adequadas; ficam de fora as que têm poucas imagens.

**Fontes e créditos.** Acervo do Agro App; fotos do iNaturalist, observações do Brasil com identificação confirmada pela comunidade, sob licenças CC0 e CC BY, em que o crédito de cada autor deve acompanhar o uso das fotos; e o conjunto AgroInsect, sob licença CC BY 4.0.

### Decisões

- **Base do primeiro modelo:** as 14 espécies do novo dataset (13 classes, pelo agrupamento abaixo), com as imagens do acervo das três pragas que também estão no novo dataset (Cigarrinha-do-milho, Percevejo-do-milho e Lagarta-da-soja). As demais classes do acervo anterior ficam fora.
- **Spodoptera eridania e S. cosmioides:** agrupadas na classe Lagarta-das-vagens (IDs 10 e 11). Têm o mesmo nome comum no dataset, as larvas são visualmente muito parecidas e juntas somam 159 imagens. A Spodoptera frugiperda (ID 3) continua separada.

### Resultados

#### Resumo

| Grupo | Status | Classes | Imagens |
| --- | --- | --- | --- |
| Pragas | Entra | 13 | 3.233 |
| Pragas | Fora do MVP | 7 | 18 |
| Doenças | Entra | 0 | 0 |
| Doenças | Fora do MVP | 36 | 95 |
| **Total** | | **56** | **3.346** |

#### Lista definitiva de classes do modelo

| Índice | Classe | Cultura | ID e nome no inventário | Imagens | Justificativa |
| --- | --- | --- | --- | --- | --- |
| 0 | **Vaquinha (Diabrotica speciosa)** | Milho/Soja | 0 · diabrotica_speciosa | 1.055 | Maior volume da base, com o inseto nítido e um padrão verde com manchas alaranjadas inconfundível. |
| 1 | **Cigarrinha-do-milho (Dalbulus maidis)** | Milho | 1 · dalbulus_maidis; AGRO-001 | 212 | Alto volume, com a cigarrinha em posições variadas; as imagens do acervo mostram também o sintoma na folha. |
| 2 | **Percevejo-barriga-verde (Dichelops/Diceraeus)** | Milho/Soja | 2 · dichelops_sp | 283 | Alto volume, com o percevejo em diferentes plantas e posições. |
| 3 | **Lagarta-do-cartucho (Spodoptera frugiperda)** | Milho/Soja | 3 · spodoptera_frugiperda | 434 | Alto volume, com o inseto bem visível em fundos e posições variadas. |
| 4 | **Percevejo-marrom (Euschistus heros)** | Soja | 4 · euschistus_heros | 65 | Volume adequado, com o inseto bem visível e a mancha clara característica no dorso. |
| 5 | **Percevejo-verde (Nezara viridula)** | Soja | 5 · nezara_viridula | 94 | Bom volume, com adultos e ninfas de cores diferentes. |
| 6 | **Percevejo-asa-preta (Edessa meditabunda)** | Soja | 6 · edessa_meditabunda | 75 | Bom volume e padrão de cor verde e marrom bem distinto. |
| 7 | **Percevejo-do-milho (Leptoglossus zonatus)** | Milho | 7 · leptoglossus_zonatus; AGRO-003 | 83 | Bom volume, com adultos, ninfas e ovos; as pernas dilatadas ficam bem visíveis. |
| 8 | **Lagarta-falsa-medideira (Chrysodeixis includens)** | Soja | 8 · chrysodeixis_includens | 82 | Bom volume, com a mariposa nítida e as marcas prateadas nas asas. |
| 9 | **Lagarta-da-soja (Anticarsia gemmatalis)** | Soja | 9 · anticarsia_gemmatalis; AGRO-053 | 43 | Menor volume entre as pragas que entram, mas ainda com dezenas de imagens e a mariposa bem visível. |
| 10 | **Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)** | Soja | 10 · spodoptera_eridania; 11 · spodoptera_cosmioides | 159 | Bom volume e a maior presença de lagartas (larvas) entre as classes de lagartas. |
| 11 | **Astylus variegatus** | Milho | 12 · astylus_variegatus | 480 | Alto volume, com o besouro nítido e o padrão preto e amarelo marcante. |
| 12 | **Cigarrinha-das-pastagens (Deois flavopicta)** | Milho | 13 · deois_flavopicta | 168 | Bom volume, com o inseto nítido e o padrão preto e amarelo característico. |

O índice é a posição da classe na saída do modelo, e não o ID do inventário, as classes seguem a ordem do `class_id`. As imagens são as aproveitáveis, sem repetidas nem figuras, as contagens do inventário estão em `assets/data/classes-modelo.csv`.

#### Classes fora do MVP

| Grupo | Classes | Imagens por classe | Justificativa |
| --- | --- | --- | --- |
| Pragas | Pulgão-do-milho; Coró-da-soja; Brocas-da-soja (vagens + axilas); Coró-do-milho; Tamanduá-da-soja; Cascudinho-da-soja; Percevejo da Soja (sem espécie definida) | 1 a 5 | Poucas imagens por classe, o que não permite ao modelo aprender e ser avaliado de forma confiável. |
| Doenças | Nematóide de cisto; Podridão-cinzenta-do-caule (Macrophomina); Nematóide das lesões; Ferrugem asiática; Mancha-olho-de-rã; Mosaico comum da soja; Míldio; Phomopsis / Seca da haste e da vagem; Podridão-vermelha-da-raiz | 4 a 6 | Poucas imagens por classe. |
| Doenças | Damping-off, Podridão-aquosa, Tombamento; Estiolamento, Podridão-de-raízes, Tombamento-de-mudas; Mancha-aureolada; Murcha-de-Sclerotium; Murcha-de-fusarium; Nematóide de galhas; Nematóide-espiralado, Nematóide; Antracnose; Cancro-da-haste; Crestamento bacteriano; Mancha alvo; Mancha-parda / Septoriose; Nematoide-da-haste verde, Ponta Branca; Nematóide-reniforme; Oídio; Podridão radicular de Phytophthora; Podridão-de-raízes; Podridão-radicular; Pústula bacteriana; Tombamento | 2 a 3 | Muito poucas imagens por classe. |
| Doenças | Clodosporiose, Verrugose; Fungo de pós colheita; Fungo-de-armazenamento; Fungo-de-pós-colheita, Podridão-dos-grãos-armazenados; Mela ou requeima; Mofo-branco, Podridão-de-sclerotinia; Podridão da semente, Podridão de Fusarium | 1 | Uma única imagem por classe. |

### Observação

As classes que ficaram de fora podem entrar à medida que o acervo for complementado. Nas classes de lagartas, parte das imagens mostra o inseto adulto; complementar com fotos de lagartas e do dano na planta deixa a base mais próxima do uso em campo.

### Referências

ALMEIDA, G.; NAZARIO, L.; TEIXEIRA, M.; STIRLE, J.; FRANCA, H.; OLIVEIRA, M.; OLIVEIRA, R.; NOVAK, S.; BAILÃO, A.; GONTIJO, P. **AGROINSECT: A dataset for identifying agricultural insects and pests of interest**. Versão 2. Mendeley Data, 2026. DOI: 10.17632/4jyp4m9gxj.2.

INATURALIST. **Observações de pragas de soja e milho no Brasil**. Disponível em: https://www.inaturalist.org. Acesso em: 4 out. 2026. Os créditos individuais das fotos acompanham os metadados da base.

# 4. Preparação dos dados

## 4.1 Padronização das imagens

### Objetivo e entradas

Definir um único processamento de entrada para o modelo, aplicado da mesma forma no treinamento e na inferência, para que as fotos dos acervos e as fotos tiradas em campo cheguem ao modelo no mesmo formato. O [notebook da T4.1](../notebooks/T4_1_padronizacao_imagens.ipynb) usa como entrada o [manifesto das 13 classes da T4.2](../assets/data/particionamento_T4_2/manifesto_modelo.csv), com **3.163 imagens**. A lógica fica em [`src/preprocessamento.py`](../src/preprocessamento.py), para que o notebook e o restante do código usem a mesma função.

### Método

A função `preparar_imagem` executa, nesta ordem:

1. **Orientação EXIF:** aplica a rotação gravada pelo celular, para que fotos tiradas em retrato não cheguem deitadas ao modelo.
2. **Conversão para RGB:** imagens em escala de cinza ou com canal alfa passam a ter três canais.
3. **Redimensionamento proporcional para 224 × 224 px:** a maior dimensão é ajustada a 224 px e a proporção é preservada, com reamostragem bicúbica.
4. **Preenchimento neutro:** o restante do quadro recebe cinza `(128, 128, 128)`. Não há recorte, para não remover lesões nas bordas da foto.
5. **Normalização:** os valores de pixel são convertidos para `float32` no intervalo [0, 1].

As decisões e o motivo de cada uma estão registradas no notebook. O tamanho de 224 px segue a referência do diagnóstico da T3.3 e do candidato EfficientNet-Lite0, mas é um parâmetro, porque a arquitetura final ainda não foi escolhida.

**Verificação automatizada.** O script [`tests/validar_preprocessamento.py`](../tests/validar_preprocessamento.py) usa imagens sintéticas para checar o contrato da função: formato e faixa de valores, preservação da proporção com faixas de preenchimento, ampliação de imagens menores que 224 px, conversão de modos de cor, aplicação da orientação EXIF e determinismo. Para executar, use `python tests/validar_preprocessamento.py`.

### Resultado e atualização da entrada

O notebook agora lê o manifesto das 13 classes. O arquivo [`referencia_entrada.csv`](../assets/data/padronizacao_T4_1/referencia_entrada.csv) foi reduzido às **3.163 imagens** desse manifesto e recebeu as partições atuais. Os hashes de entrada foram preservados da execução anterior para as mesmas imagens, pois o pré-processamento não depende da partição. A inspeção visual e o recálculo dos hashes com os arquivos originais ainda precisam ser repetidos. O arquivo de [parâmetros](../assets/data/padronizacao_T4_1/parametros.json) registra tamanho, cor de preenchimento, normalização, EXIF e versão do Pillow da execução anterior.

### Limites e próximos passos

- A normalização em [0, 1] é uma escolha simples. Antes do treinamento, a faixa exigida pelo backbone escolhido deve ser confirmada, e a normalização ajustada se necessário.
- Os hashes foram gerados em um ambiente específico. Se outro ambiente usar outra versão do Pillow ou outra implementação de reamostragem, os valores podem diferir e a referência deve ser regenerada.
- A inspeção visual foi feita por uma amostra fixa de 8 imagens, e não por revisão individual do conjunto.
- A padronização trata a geometria e a cor de entrada. Ela não corrige a qualidade da foto; essa validação precisa ser tratada na etapa de validação da imagem.

## 4.2 Particionamento por grupo

### Escopo

O particionamento atual distribui **3.163 imagens das 13 classes do primeiro modelo** entre treino, validação e teste. As classes e seus índices vêm da [lista T3.5](../assets/data/classes-modelo.csv); as decisões de qualidade por imagem vêm da [T3.3](../assets/data/diagnostico_qualidade_T3_3_revisado.xlsx), e os IDs do acervo anterior vêm do [dicionário T3.4](../assets/data/dicionario-classes.json).

As imagens `AGRO-001` e `AGRO-053` complementam classes já existentes. `DATASET-10` e `DATASET-11` compartilham a classe de índice 10 (*Spodoptera eridania* e *S. cosmioides*). As quatro imagens `AGRO-003` não entram enquanto a espécie estiver indeterminada; a classe *Leptoglossus zonatus* permanece no modelo com as imagens `DATASET-07`. Outras **95 imagens** mantidas na triagem ficam fora do escopo das 13 classes.

### Método

1. **Selecionar as imagens:** manter apenas registros aprovados na triagem que correspondem às 13 classes e aplicar seus índices de saída.
2. **Formar grupos indivisíveis:** unir registros com o mesmo `grupo_origem`, duplicatas exatas e pares visuais confirmados. Vínculos adicionais da mesma planta ou sessão podem ser registrados em `assets/data/vinculos_mesma_planta.csv`.
3. **Distribuir os grupos:** usar a semente **42** e metas de **70% treino, 15% validação e 15% teste**, equilibrando classes e fontes. A integridade dos grupos tem prioridade sobre as proporções.
4. **Auditar:** verificar se nenhum grupo de origem, grupo de partição ou hash SHA-256 aparece em mais de uma partição e se cada classe avaliável tem exemplos nas três.

### Resultado

| Partição | Grupos | Imagens |
| --- | ---: | ---: |
| Treino | 1.594 | 2.214 |
| Validação | 352 | 475 |
| Teste | 353 | 474 |
| **Total** | **2.299** | **3.163** |

Todas as **13 classes** têm grupos em treino, validação e teste. Nenhuma ficou exploratória por falta de grupos. A auditoria não encontrou cruzamento entre os grupos de origem, grupos de partição ou hashes exatos registrados. As **99 imagens mantidas na triagem mas fora do modelo** estão resumidas em [fora_modelo.csv](../assets/data/particionamento_T4_2/fora_modelo.csv).

Os resultados estão no [manifesto do modelo](../assets/data/particionamento_T4_2/manifesto_modelo.csv), no [resumo por classe](../assets/data/particionamento_T4_2/resumo_modelo.csv) e na [auditoria reproduzível](../assets/data/particionamento_T4_2/auditoria_modelo.json). O código está em [`src/gerar_manifesto_modelo_t4_2.py`](../src/gerar_manifesto_modelo_t4_2.py) e [`src/particionamento_t4_2.py`](../src/particionamento_t4_2.py). Para refazer a separação, execute `python -m src.gerar_manifesto_modelo_t4_2` na raiz do repositório.

### Limites e próximos passos

O CSV T3.5 informa **3.233 imagens aproveitáveis**, enquanto o manifesto contém **3.163**. A [auditoria](../assets/data/particionamento_T4_2/auditoria_modelo.json) detalha a diferença por classe; as contagens ainda precisam ser conciliadas. A revisão de Glauco e a aprovação interna dos rótulos também estão pendentes.

Parte das imagens de `dataset` manteve decisões de triagem automática sem inspeção visual individual. Não foram fornecidos vínculos manuais adicionais da mesma planta; em parte do catálogo, `grupo_origem` identifica apenas o arquivo. A auditoria confirma ausência de vazamento **identificável pelos metadados e pares revisados**, sem comprovar independência completa das plantas. Se a revisão visual, os rótulos ou os vínculos mudarem, a divisão deve ser refeita e o teste mantido reservado para avaliação final.

## 4.4 Rotinas de aumento de dados

### Objetivo e entradas

Ampliar a diversidade das imagens de treino com variações que aparecem na captura em campo, como luz do sol, sombra, balanço de branco do celular, ângulo da folha, tremor e ruído do sensor. O aumento responde ao risco **R09** (diferença entre o acervo e as fotos reais de campo) e ajuda a mitigar o **R01** (poucas imagens por classe). O [notebook da T4.4](../notebooks/T4_4_aumento_dados.ipynb) usa como entrada o [manifesto das 13 classes da T4.2](../assets/data/particionamento_T4_2/manifesto_modelo.csv) e a saída de `preparar_imagem` da T4.1. A lógica fica em [`src/aumento.py`](../src/aumento.py).

### Método

A função `aplicar_aumento` recebe a imagem já padronizada (224 × 224 px, float32 em [0, 1]) e a partição de origem. Cada uma das cinco transformações é sorteada de forma independente, com probabilidade de 50%:

1. **Brilho e contraste:** simula sol forte e sombra, com contraste entre 0,8 e 1,2 e brilho entre 0,75 e 1,25.
2. **Balanço de branco:** ganho de ±5% em cada canal de cor, para representar celulares com correções de cor diferentes.
3. **Ângulo de captura:** rotação de 0°, 90°, 180° ou 270°, com espelhamento horizontal em metade dos casos. Não há rotação arbitrária, para não criar bordas de interpolação.
4. **Tremor ou foco leve:** desfoque gaussiano com raio entre 0,5 e 1,5 px.
5. **Ruído do sensor:** ruído gaussiano com desvio-padrão entre 0,005 e 0,03.

**Aplicação restrita ao treino.** A função recusa qualquer partição diferente de `treino` com `ValueError`. Assim, validação e teste nunca recebem uma variação aumentada, nem por engano de quem chama a função.

**Sem recorte.** Como na T4.1, o aumento não corta a imagem, para não remover lesões nas bordas.

**Preenchimento preservado.** As faixas de cinza adicionadas pela T4.1 são artificiais e não representam a cena fotografada. Por isso, brilho, balanço de branco, desfoque e ruído são aplicados somente ao conteúdo da imagem. Em rotações e espelhamentos, a máscara do preenchimento acompanha a transformação e as faixas permanecem no cinza neutro original.

A função recebe um gerador de números aleatórios com semente explícita (o notebook usa a semente 42), e os parâmetros são gravados em [`parametros.json`](../assets/data/aumento_T4_4/parametros.json) para permitir a reprodução.

### Resultado da execução

- **Aplicação:** das **3.163 imagens** do manifesto atual, **2.214** são de treino e aceitam aumento. As **949** de validação e teste foram recusadas no teste automatizado.
- **Inspeção visual:** o notebook gera uma grade com quatro imagens de treino, cada uma com a entrada original e três variações sorteadas. A inspeção precisa ser repetida com as imagens do manifesto atual.
- **Verificação automatizada:** o script [`tests/validar_aumento.py`](../tests/validar_aumento.py) confirma formato e faixa de valores, entrada não alterada, determinismo com semente fixa, preservação do preenchimento neutro, variação real (menos de 10% das saídas iguais à entrada) e bloqueio fora do treino em todas as linhas do manifesto.

### Limites e próximos passos

- **Imagens sem variação suficiente:** classes com 1 ou 2 imagens no treino continuam com pouca diversidade. Aumentar uma única foto gera variações parecidas, então essas classes seguem como exploratórias, sem ganho real de generalização.
- **Cor como sinal diagnóstico:** o balanço de branco foi limitado a ±5% porque a cor pode indicar sintomas como amarelamento. Uma faixa maior precisa ser validada com o parceiro.
- **Fundo e condições reais:** o aumento não simula fundos de campo nem chuva ou poeira. Esses casos dependem de fotos reais, previstas nos testes com celular da fase de validação.
- **Balanceamento:** esta task não equilibra as classes. Essa decisão pertence à T4.3, que trata da estratégia de balanceamento.
- **Probabilidade fixa:** a probabilidade de 50% por transformação ainda não foi comparada com outras opções. Ela pode ser ajustada depois de um primeiro treino.

## 4.5 Pipeline reprodutível (T4.5)

### Objetivo e entradas

Executar a preparação dos dados por um único ponto de entrada, preservando os
contratos definidos nas etapas anteriores. O pipeline usa a lista das **13 classes**
da T3.5, recompõe o particionamento da T4.2, incorpora os parâmetros de
padronização da T4.1, calcula os pesos da T4.3 e associa o augmentation da T4.4
exclusivamente às amostras de treino.

As entradas versionadas são:

- `assets/data/classes-modelo.csv`;
- `assets/data/diagnostico_qualidade_T3_3_revisado.xlsx`;
- `assets/data/dicionario-classes.json`;
- parâmetros de T4.1 e T4.4;
- manifesto aprovado da T4.2, usado como referência de reprodução.

### Execução

O ponto de entrada é [`src/pipeline_preparacao_t4_5.py`](../src/pipeline_preparacao_t4_5.py):

```bash
python -m src.pipeline_preparacao_t4_5
```

Esse modo não precisa das imagens originais: ele recompõe e compara as partições,
calcula os pesos e gera o índice consumido pelo treinamento. Quando todas as fontes
de imagem estiverem disponíveis em uma pasta que contenha `dataset/`, `Milho/` e
`Soja/`, a mesma execução também pode abrir e processar todas as entradas:

```bash
python -m src.pipeline_preparacao_t4_5 --raiz-imagens /caminho/para/as/fontes
```

### Reprodutibilidade e isolamento

- A semente global é **42**.
- A T4.2 é executada novamente em uma pasta temporária; seus quatro artefatos devem
  ser idênticos aos arquivos aprovados antes que o pipeline continue.
- Cada imagem de treino recebe uma semente estável derivada de `semente + image_id`.
- Os pesos seguem `N / (K × n_c)` e usam somente as imagens originais de treino.
- Validação e teste não recebem peso de treino nem augmentation.
- As imagens não são copiadas para o repositório; o pipeline versiona somente
  índices, parâmetros, pesos e hashes de auditoria.

### Saídas

Os artefatos ficam em `assets/data/pipeline_T4_5/`:

| Arquivo | Conteúdo |
| --- | --- |
| `indice_pipeline.csv` | Classe, grupo, partição, peso e decisão de augmentation por imagem. |
| `pesos_classes.json` | Contagens de treino e peso calculado para cada uma das 13 classes. |
| `parametros.json` | Semente e parâmetros consolidados de T4.1, T4.3 e T4.4. |
| `auditoria.json` | Prova de reprodução da T4.2, contagens e regras de isolamento. |

### Verificação automatizada

O teste [`tests/validar_pipeline_t4_5.py`](../tests/validar_pipeline_t4_5.py) executa
o pipeline duas vezes em pastas vazias e exige saídas idênticas. Ele também confirma
as 3.163 imagens, as 13 classes, as partições 2.214/475/474, a média ponderada dos
pesos igual a 1 e a ausência de augmentation em validação e teste.

```bash
python tests/validar_pipeline_t4_5.py
```

### Limites

A execução sem `--raiz-imagens` valida integralmente os índices e as decisões do
pipeline, mas não reabre as fotografias. A validação dos hashes de preprocessamento
e das variações aumentadas exige acesso às três fontes externas, que não são
versionadas neste repositório.


