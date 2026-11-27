---
name: AgroApp
description: Identidade visual da interface de reconhecimento de pragas do AgroApp.
colors:
  green: "#00cf89"
  green-dark: "#007f56"
  green-light: "#e9f9f1"
  ink: "#253253"
  muted: "#61716d"
  ground: "#f5f8f6"
  line: "#e3eae5"
  focus: "#00895c"
  white: "#ffffff"
  button-ink: "#133d2e"
  button-hover: "#00bb7c"
typography:
  display:
    fontFamily: "Poppins, sans-serif"
    fontSize: "clamp(32px, 3.1vw, 43px)"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-1.3px"
  title:
    fontFamily: "Poppins, sans-serif"
    fontSize: "14px"
    fontWeight: 500
  body:
    fontFamily: "Poppins, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Poppins, sans-serif"
    fontSize: "12px"
    fontWeight: 500
  action:
    fontFamily: "Poppins, sans-serif"
    fontSize: "12px"
    fontWeight: 600
rounded:
  tag: "4px"
  action: "8px"
  choice: "9px"
  upload: "14px"
  dialog: "20px"
  workspace: "22px"
spacing:
  compact: "8px"
  action-y: "12px"
  action-x: "18px"
  mobile-gutter: "20px"
  section: "24px"
  desktop-gutter: "40px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.button-ink}"
    typography: "{typography.action}"
    rounded: "{rounded.action}"
    padding: "12px 18px"
  button-primary-hover:
    backgroundColor: "{colors.button-hover}"
  button-text:
    textColor: "{colors.green-dark}"
    padding: "8px 0 8px 10px"
  recognition-tag:
    backgroundColor: "{colors.green-light}"
    textColor: "{colors.green-dark}"
    rounded: "{rounded.tag}"
    padding: "3px 7px"
  workspace:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.workspace}"
  prediction:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.choice}"
    padding: "12px 10px"
---

# Design System: AgroApp

## Overview

**Creative North Star: "AgroAPP"**

A identidade vem da apresentação fornecida pelo usuário: marca AgroAPP, Poppins, verde vivo, azul escuro e espaço em branco. A interface mantém esses elementos em controles convencionais de uma aplicação de análise visual.

As superfícies claras separam o trabalho da navegação. O verde sinaliza ação, seleção e disponibilidade; a fotografia e os resultados mantêm prioridade sobre a ornamentação. As folhas originais da apresentação aparecem de forma secundária, com procedência registrada em `frontend/public/brand/PROVENANCE.md`.

**Key Characteristics:**

- Poppins em toda a interface, com pesos distintos para hierarquia.
- Verde para ação e seleção; azul escuro para texto.
- Superfícies claras, bordas discretas e cantos arredondados.
- Ícones Lucide com traços leves e estados acessíveis.

## Colors

### Primary

Verde vivo (`green`) identifica a marca e o botão principal. Verde escuro (`green-dark`) sustenta texto de ação, ícones e scores. Verde claro (`green-light`) marca áreas auxiliares e etiquetas.

### Neutral

Azul escuro (`ink`) é a cor de leitura principal. Cinza esverdeado (`muted`) diferencia texto de apoio. O fundo (`ground`), o branco (`white`) e as linhas (`line`) organizam as superfícies sem grandes sombras. A cor `focus` identifica o foco por teclado.

Erros usam a combinação quente observada nos avisos da aplicação; ela não substitui a identidade principal. Os valores normativos reutilizados estão no frontmatter e em `frontend/src/tokens.css`.

## Typography

Poppins é servida localmente pelo pacote Fontsource, com fallback `sans-serif`. Pesos carregados: regular (400), médio (500), semibold (600) e bold (700).

O título principal usa o papel `display`; no celular, passa a 33 px, com espaçamento de letras de -1 px. Títulos de painel usam o papel `title`. Textos de apoio variam de 9 a 13 px conforme o contexto existente, sem competir com as ações. Nomes científicos aparecem em itálico. Scores, índices e durações usam numerais tabulares.

## Layout

O conteúdo tem largura máxima de 1280 px. O espaçamento lateral é de 40 px no desktop, 28 px na faixa intermediária e 20 px no celular. A navegação superior permanece convencional e ocupa uma segunda linha nas telas menores.

A bancada de análise divide fotografia e resultados na proporção 1,13:1. Até 760 px, os painéis são empilhados e o divisor passa da lateral para a horizontal. O catálogo usa duas colunas no desktop e uma no celular. Os pontos de adaptação observados são 1500, 1000, 760 e 380 px; o documento aceita largura mínima de 320 px.

## Elevation & Depth

A hierarquia depende principalmente de fundos e divisores. A bancada tem sombra ambiente muito discreta (`0 8px 24px -18px #234c3420`). A ajuda usa uma sombra mais ampla (`0 20px 70px #122c3330`) com backdrop escurecido. Os elementos comuns permanecem planos.

## Shapes

Os raios acompanham a escala do componente: etiquetas compactas, botões moderadamente arredondados, áreas de upload maiores e bancada com contorno contínuo. Indicadores de estado e alguns ícones auxiliares usam círculos. Bordas de seleção têm 1 px; o upload vazio usa contorno tracejado.

## Components

### Buttons

O botão principal usa verde vivo, texto verde profundo, raio `action`, espaçamento `action-y`/`action-x` e altura mínima de 45 px. Hover escurece o fundo e desloca o botão 1 px para cima. O estado desabilitado usa fundo e texto dessaturados. Ações auxiliares usam fundo transparente e texto verde escuro.

O foco global usa contorno de 3 px, com afastamento de 4 px. As transições curtas de cor e posição respeitam `prefers-reduced-motion`.

### Navigation

As abas são botões de texto e ícone. O item ativo muda para verde escuro e recebe uma linha inferior verde de 3 px. Esse traço é um indicador de navegação, sem contorno de cartão arredondado. No celular, as abas ocupam uma linha própria.

### Inputs / Fields

A entrada de arquivo é acionada por botão e complementada por uma área de arrastar e soltar. A área usa fundo claro esverdeado, contorno tracejado e raio `upload`. Durante arraste, fundo e borda mudam para verde. O estado de análise exibe a fotografia com uma linha móvel; a remoção fica indisponível durante o processamento.

### Chips / Tags

Etiquetas pequenas usam fundo tonal, pouco espaçamento e texto de apoio. A seleção da visualização original ou preparada usa um grupo segmentado com indicador branco e texto verde escuro.

### Results

As hipóteses são botões alinhados em lista. Nome, nome científico, barra e percentual permanecem agrupados; a seleção usa borda e fundo verdes suaves. As barras representam os scores reais. Avisos e conteúdo indisponível ficam legíveis junto ao contexto, sem diagnóstico inventado.

### Help

A explicação usa um diálogo nativo com título, fechamento explícito e suporte a Escape. No celular, a largura respeita uma margem de 16 px de cada lado. O foco permanece visível.

## Do's and Don'ts

### Do:

- **Do** preservar Poppins, a marca e a relação entre verde, azul escuro e superfícies claras.
- **Do** manter foco visível, estados de carregamento e mensagens de erro no contexto da ação.
- **Do** usar a imagem inteira, com `object-fit: contain`, para permitir conferir a fotografia.
- **Do** respeitar movimento reduzido e o empilhamento dos painéis no celular.

### Don't:

- **Don't** transformar score em afirmação visual de diagnóstico confirmado.
- **Don't** exibir orientações técnicas como validadas enquanto o conteúdo estiver pendente.
- **Don't** substituir a marca e os recursos fornecidos por fotografias com marca d'água.
- **Don't** usar as folhas decorativas como obstáculo aos controles ou à leitura.
