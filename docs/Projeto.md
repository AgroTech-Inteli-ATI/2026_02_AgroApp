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

Uma persona é uma representação fictícia de um usuário, criada com base nas características, nos objetivos, nas necessidades e nas dificuldades do público que se pretende atender. Em nosso projeto, as personas funcionam como uma forma de validar se a solução proposta está realmente alinhada aos problemas e às expectativas de seus futuros usuários. Elas orientam as decisões da equipe ao longo do desenvolvimento, ajudando a avaliar funcionalidades, formas de interação e situações de uso do Módulo de Identificação de Pragas por Reconhecimento Visual integrado ao Agro App. Foram definidas duas personas para o projeto, e Vitória Lima, apresentada a seguir, é uma delas.

### Persona 2 — Vitória Lima

<div align="center">
  <p><strong>Figura 1 — Persona Vitória Lima</strong></p>
  <img src="../assets/persona_estudante.png" alt="Persona Vitória Lima, estudante e pesquisadora de Agronomia">
  <p><em>Fonte: feito pela própria equipe, 2026.</em></p>
</div>

Vitória Lima tem 22 anos, cursa Agronomia e atua como pesquisadora em Piracicaba, São Paulo. Durante atividades de campo, fotografa sintomas em folhas e frutos para comparar possíveis doenças, pragas e deficiências nutricionais. Ela busca desenvolver experiência prática em diagnóstico vegetal e consultar referências técnicas confiáveis, mas encontra dificuldades para diferenciar sintomas visualmente semelhantes, avaliar hipóteses com segurança e acessar a internet em campo. Por isso, precisa de um módulo que apresente as hipóteses mais prováveis, informe o grau de confiança do resultado e permita acesso offline a conteúdos técnicos relacionados.



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

Levantar os requisitos da Seção 17 do TAP e identificar as principais restrições de tamanho, latência e execução embarcada.

**Documentação — a preencher**

| ID | Requisito ou restrição | Tipo | Valor ou limite | Critério de aceitação | Fonte |
| --- | --- | --- | --- | --- | --- |
| A definir | A preencher | A definir | A validar | A preencher | A preencher |

**Ambiente de execução:** a definir.

**Pendências de validação com o parceiro:** a preencher.

---

## 2.2 Glossário técnico do projeto

Construir a primeira versão do glossário com os principais termos técnicos utilizados no projeto.

**Documentação — a preencher**

| Termo ou sigla | Definição | Aplicação no projeto | Referência |
| --- | --- | --- | --- |
| A preencher | A preencher | A preencher | A preencher |

---

## 2.3 Levantamento de arquiteturas viáveis

Pesquisar arquiteturas compatíveis com execução embarcada e comparar número de parâmetros, tamanho e acurácia de referência com os limites levantados no T2.1.

**Documentação — a preencher**

| Arquitetura | Parâmetros | Tamanho | Acurácia de referência | Dataset e condições de avaliação | Compatibilidade com T2.1 | Fonte |
| --- | --- | --- | --- | --- | --- | --- |
| A pesquisar | A verificar | A verificar | A verificar | A verificar | A avaliar | A preencher |

**Análise comparativa e limitações:** a preencher.

**Arquitetura recomendada e justificativa:** a definir após a análise.

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

