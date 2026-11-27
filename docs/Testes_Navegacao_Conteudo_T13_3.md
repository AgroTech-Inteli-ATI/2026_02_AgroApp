# T13.3 — Testes de navegação e apresentação do conteúdo

Autor: Glauco · Revisor: a definir · Executado em: 22/11/2026

**Situação:** 8 testes funcionais automatizados (19 verificações de caso) passaram. Nenhuma informação incorreta foi exibida e nenhum resultado anterior foi reaproveitado. Não foi necessária nenhuma alteração no aplicativo.

## Critério de aceite

> Testes funcionais documentados, sem exibição de informações incorretas ou reutilização indevida de resultados anteriores.

| Exigência | Onde é verificada |
| --- | --- |
| Conteúdo técnico apresentado após uma classificação | CON-01 a CON-04, CAT-01 |
| Diagnóstico inconclusivo | INC-01 a INC-03 |
| Nova imagem | NOV-01 a NOV-04, ERR-01 |
| Ausência de conteúdo disponível | CON-03, CON-04, CAT-01 |
| Nenhuma informação incorreta | Todos: cada caso confere que **só** o conteúdo da classe esperada aparece e que os demais estão ausentes |
| Nenhuma reutilização de resultado anterior | NOV-01 a NOV-04, INC-01, ERR-01, NAV-04 |

## Como os testes funcionam

Os testes estão em [`frontend/tests/conteudo.spec.ts`](../frontend/tests/conteudo.spec.ts) e rodam no Chromium do Playwright sobre o aplicativo real ([`App.tsx`](../frontend/src/App.tsx)), com a política de confiança versionada da [T6.5](../assets/data/politica_T6_5/parametros.json) e os 13 nomes de classe do modelo oficial.

Dois dublês tornam os cenários controláveis:

1. **Worker de inferência.** Como em `confidence.spec.ts`, só o transporte do worker é substituído. Cada teste define a classe e o score de cada análise e pode segurar uma resposta ou reenviar a resposta anterior, para simular atraso. A inferência real dos modelos Float16 e INT8 continua coberta por `analysis.spec.ts`.
2. **Catálogo de conteúdo.** O catálogo versionado ainda está vazio (0 de 13 classes, ver [T9.3](Projeto.md#93-associação-da-predição-ao-conteúdo-técnico-t93)). Sem dublê, só seria possível testar a ausência de conteúdo. Por isso, os casos CON, NOV, INC, ERR e NAV recebem um catálogo **fictício** no lugar do módulo `src/data/content.ts`, entregue pelo servidor de desenvolvimento:

| Classe | Situação no catálogo de teste |
| --- | --- |
| 0 — Vaquinha | conteúdo validado (`TESTE-T13.3 título da classe 0`, "Fonte fictícia A") |
| 5 — Percevejo-verde | conteúdo validado (`TESTE-T13.3 título da classe 5`, "Fonte fictícia B") |
| 2 — Percevejo-barriga-verde | item presente, mas `validated: false` |
| demais | sem item |

Os textos começam com `TESTE-T13.3` para não serem confundidos com orientação real. O caso CAT-01 usa o catálogo versionado sem dublê e confere que nada do catálogo fictício aparece.

A cada passo, a função `conferirConteudo` verifica o painel "Orientações técnicas" inteiro:

- se a classe tem conteúdo validado, aparecem título, texto, fonte e data dela, e nenhum texto das outras classes;
- se não tem, aparece "Conteúdo técnico ainda indisponível para *nome da classe*.", sem título, texto ou "Fonte:";
- sem resultado aceito, o painel não existe.

## Casos e resultados

| ID | Situação | Passos | Resultado esperado | Resultado |
| --- | --- | --- | --- | --- |
| CON-01 | Hipótese principal com conteúdo | Análise aceita com top-1 = classe 0 | A hipótese 0 abre selecionada e o painel mostra o conteúdo da classe 0 | Passou |
| CON-02 | Troca de hipótese | Clicar na hipótese da classe 5 (2ª posição) e depois voltar à 0 | O conteúdo acompanha o **índice** da classe escolhida, não a posição no ranking; o anterior some | Passou |
| CON-03 | Item não validado | Clicar na hipótese da classe 2 (`validated: false`) | Aviso de indisponível com o nome "Percevejo-barriga-verde"; título e texto do item não aparecem | Passou |
| CON-04 | Classe sem conteúdo | Top-1 = classe 12; depois clicar nas hipóteses 7 e 0 | Aviso com o nome correto de cada classe; ao voltar para a 0, o conteúdo dela aparece | Passou |
| NOV-01 | Nova imagem em análise | Com a classe 5 selecionada e os detalhes de execução abertos, enviar nova foto (resposta retida) | Durante a análise: sem hipóteses, scores, painel de orientações, tempo de inferência ou "Entrada do modelo" do resultado anterior | Passou |
| NOV-02 | Novo resultado | Liberar a resposta (top-1 = classe 12, com a classe 5 em 2º) | Seleciona o top-1 do novo resultado (12), e não a classe 5 escolhida antes; score de 70% | Passou |
| NOV-03 | Terceira imagem | Nova foto com top-1 = classe 5 | Conteúdo da classe 5 e score de 90%; nada da análise anterior | Passou |
| NOV-04 | Resposta atrasada | Durante a nova análise, o worker reenvia o resultado e um erro com o identificador da análise anterior | Ambos descartados: a tela segue em "Observando os detalhes…", sem alerta nem conteúdo antigo; depois exibe só o novo resultado | Passou |
| INC-01 | Aceito → inconclusivo | Com a classe 5 selecionada, nova foto com top-1 = classe 5 logo abaixo de 0,65 | Mensagem e orientação da política; nenhum nome de classe, score, hipótese ou orientação técnica | Passou |
| INC-02 | Entrada do modelo no inconclusivo | Alternar para "Entrada do modelo" | A imagem preparada aparece, sem identificação | Passou |
| INC-03 | Inconclusivo → aceito | Nova foto com top-1 = classe 12 exatamente em 0,65 | Seleção e aviso da classe 12; a visualização volta para a foto original | Passou |
| ERR-01 | Falha ao abrir a nova foto | Após resultado aceito, o worker responde erro para a nova foto | Alerta, estado inicial do painel e nome do novo arquivo; nenhum resultado ou conteúdo anterior | Passou |
| ERR-02 | Arquivo recusado antes da análise | Após resultado aceito, enviar um `.txt` | Alerta "Formato não aceito"; foto, nome do arquivo e conteúdo **continuam sendo os da análise anterior**, coerentes entre si | Passou |
| NAV-01 | Aba "Classes do modelo" | Com a classe 5 selecionada, abrir o catálogo de classes | O catálogo não mostra resultado, hipóteses nem conteúdo técnico | Passou |
| NAV-02 | Voltar à análise | "Analisar uma foto" | Mesma foto, mesma hipótese (5) e mesmo conteúdo | Passou |
| NAV-03 | Ajuda | Abrir "Como funciona" e fechar com Esc | Seleção e conteúdo preservados | Passou |
| NAV-04 | Remover foto e navegar | "Remover foto", ir ao catálogo e voltar | Estado inicial, sem hipóteses nem orientações | Passou |
| NAV-05 | Tela de celular | Viewport de 390 × 900 px com conteúdo aberto | Sem rolagem horizontal | Passou |
| CAT-01 | Catálogo versionado | Top-1 = classe 0; clicar nas hipóteses 0, 1 e 2 | Cada hipótese mostra o conteúdo validado do `content.ts` ou o aviso de indisponível (hoje: aviso nas três); nenhum texto `TESTE-T13.3` | Passou |

O caso CAT-01 compara a tela com o próprio `content.ts`. Assim, continua válido quando o catálogo do parceiro for gerado, sem precisar ser reescrito.

## Sensibilidade dos testes

Para garantir que os testes detectam os defeitos que pretendem cobrir, cinco defeitos foram introduzidos no `App.tsx` servido ao navegador (o arquivo do repositório não foi alterado). Cada defeito fez pelo menos um caso falhar:

| Defeito introduzido | Casos que falharam |
| --- | --- |
| Não limpar o resultado ao iniciar uma nova análise | NOV-01 a NOV-03, NOV-04, ERR-01/02, NAV |
| Aceitar resposta do worker sem conferir o identificador da análise | NOV-04 |
| Exibir item do catálogo mesmo com `validated: false` | CON-01 a CON-03 |
| Manter a hipótese escolhida antes quando ela reaparece na nova foto | NOV-01 a NOV-03 |
| Buscar o conteúdo pela hipótese principal em vez da escolhida | CON, NOV, INC, NAV |

## Execução

Na pasta `frontend`:

```powershell
npm.cmd ci
npx playwright install chromium
npx playwright test --project=chromium tests/conteudo.spec.ts
```

Resultados em 22/11/2026, Windows, Chromium do Playwright:

| Verificação | Resultado |
| --- | --- |
| `tests/conteudo.spec.ts` | 8 passaram |
| `tests/conteudo.spec.ts --repeat-each=5` (estabilidade) | 40 passaram |
| `npx playwright test --project=chromium` (todos os testes de navegador) | 19 passaram, 1 ignorado (`preprocessing.spec.ts`, que só roda com `MODEL_COMPARISON=1`) |
| `npm test` (unitários) | 25 passaram |

## Observações e limites

- **O conteúdo real ainda não existe.** Os testes com conteúdo usam um catálogo fictício. Eles verificam a apresentação, não a correção agronômica dos textos, que depende do catálogo do parceiro e da validação por agrônomo (T9.3).
- **O inconclusivo não sugere conteúdos.** A política da T6.5 tem `conteudos_relacionados_quando_catalogo: true`, mas, conforme a [T9.2](Projeto.md#92-tratamento-do-limiar-de-confiança-t92), o resultado inconclusivo não mostra classe nem conteúdo. O catálogo de classes segue como consulta independente. Quando o conteúdo real chegar, a equipe deve decidir se o inconclusivo passa a indicar conteúdos relacionados; hoje ele não indica, e INC-01 garante isso.
- **Comportamento de ERR-02.** Um arquivo recusado antes da análise não substitui a análise anterior: o alerta aparece e a tela continua mostrando a foto, o nome e o resultado anteriores, que correspondem entre si. Os dados exibidos não são incorretos, mas o usuário vê o alerta junto do resultado antigo.
- **Ambiente.** Os testes rodam no Chromium desktop com worker dublê. Câmera física, aparelho real e inferência no celular ficam na [T12.3](Testes_Dispositivo_T12_3.md). A inferência real no navegador fica em `analysis.spec.ts`.
