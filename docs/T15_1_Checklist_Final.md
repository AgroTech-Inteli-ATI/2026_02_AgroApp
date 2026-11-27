# T15.1 — Checklist final de critérios e evidências

Responsável pela atividade: Karol · Revisão em 22/11/2026

A cobertura abaixo usa os [requisitos da seção 2.1](Projeto.md#21-requisitos-e-restrições-técnicas), a política T6.5 e os resultados da Sprint 5. O escopo considerado é o MVP web para soja e milho, com inferência no navegador e opção offline depois da carga inicial. O TAP integral e o registro formal das condições de aceite do parceiro não estão no material consultado. A correspondência integral com o TAP fica pendente até sua conferência.

**Versão de referência:** web `1.0.0`, código `42c280dd`, Float16 T7.2 principal, INT8 T7.3 contingência, LiteRT.js 2.6.0. As medições anteriores estão identificadas por relatório e devem ser comparadas com os manifestos de cada execução. Os status registram a evidência técnica disponível e as lacunas de aceite.

| Critério | Status | Evidência e versão | Pendência |
| --- | --- | --- | --- |
| RF-01 — Captura e galeria | Parcialmente atendido | Web 1.0.0: galeria no ensaio A15 e três capturas registradas em [T12.2](Benchmark_T12_2.md). | Concluir a matriz de dispositivos T12.3. |
| RF-02 — Preparação da foto | Atendido | Web 1.0.0: contrato de entrada, EXIF, redimensionamento e comparação fotográfica em [T14.4](T14_4_Arquitetura_Web.md). | — |
| RF-03 — Catálogo e confiança | Atendido | Web 1.0.0: 13 classes, scores dos dois modelos em [T11.1](Avaliacao_Final_T11_1.md) e ensaio A15. | Qualidade em campo avaliada separadamente. |
| RF-04 — Hipóteses ordenadas | Atendido | Web 1.0.0: top 3 e desempate documentados em [T14.4](T14_4_Arquitetura_Web.md), ensaio A15. | — |
| RF-05 — Confiança por hipótese | Atendido | Web 1.0.0: scores individuais exibidos na tela e top 3 registrados no ensaio A15. | — |
| RF-06 — Identificação inconclusiva | Atendido | Web 1.0.0: top 1 abaixo de 0,65, aviso, nova foto e ausência de hipóteses no ensaio A15. | Ratificar política com o parceiro. |
| RF-07 — Associação ao conteúdo oficial | Parcialmente atendido | Web 1.0.0: índice e referências locais da [T9.3](Projeto.md#93-associação-da-predição-ao-conteúdo-técnico-t93). | Receber e validar catálogo oficial, conteúdo e chaves. |
| RF-08 — Acesso à orientação relacionada | Parcialmente atendido | Web 1.0.0: seleção de hipóteses e orientações locais descritas em [T14.4](T14_4_Arquitetura_Web.md). | Validar destino e conteúdo oficial por classe. |
| RNF-01 — Modelo ≤ 8 MB propostos | Parcialmente atendido | T12.1: Float16 6,834 MB e INT8 4,004 MB individualmente. | Ratificar limite e unidade em [T12.1](Validacao_T12_1.md). |
| RNF-02 — Acréscimo ≤ 9 MB propostos | Parcialmente atendido | T12.1: os dois modelos e manifesto somam 10,841 MB e o site medido soma 58,261 MB. | Definir baseline e quais arquivos entram no limite web. |
| RNF-03 — Captura até resultado p95 ≤ 3 s propostos | Parcialmente atendido | T12.2: iPhone 13, Float16 web, Chrome, 166,87 ms p95 de arquivo até interface. Três capturas observadas. | Ratificar início e fim e medir 50 capturas no aparelho de referência. |
| RNF-04 — Inferência p95 ≤ 300 ms propostos | Parcialmente atendido | T12.2: 13,10 ms no Chrome e 13,38 ms no Safari, Float16/LiteRT.js WebGPU. | Ratificar metodologia web, aparelho e configuração de referência. |
| RNF-05 — Operação offline e zero chamadas no diagnóstico | Parcialmente atendido | Web 1.0.0: service worker e verificações automatizadas em [T14.4](T14_4_Arquitetura_Web.md). | Concluir [T12.3](Testes_Dispositivo_T12_3.md) em aparelho físico, com inspeção de rede e reabertura do cache. |
| RNF-06 — Perda por quantização ≤ 2 p.p. propostos | Parcialmente atendido | [T11.1](Avaliacao_Final_T11_1.md): teste histórico, acurácia balanceada (recall macro) 0,7126 Float16 e 0,7234 INT8. T11.1 compara os dois arquivos web e T7.2 registra comparações com FP32. | Reavaliar contra FP32 em conjunto independente e confirmar métrica e limite. |
| RNF-07 — Pico de memória | Não atendido | T12.1 mede armazenamento e T12.2 mede tempos no iPhone 13. | Definir orçamento e medir RAM com profiler no aparelho de referência. |
| RNF-08 — Conteúdo válido em 100% das classes | Parcialmente atendido | Web 1.0.0: o índice local representa as classes e explicita lacunas de conteúdo. [T14.4](T14_4_Arquitetura_Web.md). | Validar 13/13 destinos oficiais com o Agro App. |
| RNF-09 — Operação sem aceleração | Parcialmente atendido | T7.2 executou os modelos em CPU sem delegates e T14.4 documenta o fallback web. | Confirmar modo CPU no navegador e aparelho selecionados pelo parceiro. |
| T6.5 — Acurácia entre aceitas ≥ 0,90 | Não atendido | T11.1, Float16 web: 0,8821 de acurácia entre aceitas e 93,2% de cobertura no teste histórico. | Investigar erros, validar política e repetir em conjunto independente. |
| Independência do teste final | Não atendido | T10.1 e T11.1 documentam consulta prévia e vínculos entre partições. | Obter coleta nova e bloquear seu uso antes de congelar o modelo. |
| Documentação e reprodução | Parcialmente atendido | T14.1 a T14.5 cobrem dados, treinamento, avaliação, web e retreinamento. O [registro da T14.6, PR #62](https://github.com/AgroTech-Inteli-ATI/2026_02_AgroApp/pull/62) documenta o ciclo completo relatado por Rui com Tobias em Windows, sem dúvidas. | Revisar o registro e o alcance da evidência: comandos, logs e arquivos do participante não foram recebidos para conferência técnica. Execução relatada não equivale a reprodução técnica conferida. |
| Pacote final recuperável | Parcialmente atendido | [T15.3](T15_3_Entrega_Parceiro.md): inventário dos 27 arquivos e commit do build versionados; arquivo compactado identificado por caminho local e checksum. | Disponibilizar o pacote congelado em local autorizado, recuperável pelo destinatário, e registrar acesso e conferência do checksum. O caminho `.work` não acompanha o clone. |
| Demonstração e validação com o parceiro | Parcialmente atendido | Roteiro e ensaio local em [T15.2](T15_2_Roteiro_Demonstracao.md), ficha de entrega em [T15.3](T15_3_Entrega_Parceiro.md). | Apresentação externa, ata, ajustes e aceite. |
