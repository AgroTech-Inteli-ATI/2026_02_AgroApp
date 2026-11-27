# Índice da documentação

Esta pasta reúne a documentação do projeto AgroApp. O documento principal é o [`Projeto.md`](Projeto.md), organizado nas mesmas fases do projeto (negócio, dados, modelagem, avaliação, conversão, integração e entrega). Os demais arquivos são guias e relatórios de tarefas específicas. O código da tarefa no nome do arquivo (por exemplo, `T11_1`) corresponde à seção de mesmo número no `Projeto.md`.

## 1. Visão geral do projeto

| Documento | Conteúdo |
| --- | --- |
| [Projeto.md](Projeto.md) | Documentação completa: riscos, proposta de valor, personas, governança do acervo, requisitos, dados, modelagem, avaliação, conversão, integração e conteúdo técnico |

## 2. Guias para continuidade pelo Agro App

Leitura recomendada para quem vai manter ou integrar o modelo.

| Documento | Conteúdo |
| --- | --- |
| [T14_1_Dataset_Final.md](T14_1_Dataset_Final.md) | Origem, composição, partições, licenças e limitações das 3.156 imagens usadas |
| [T14_2_Pipeline_Treinamento.md](T14_2_Pipeline_Treinamento.md) | Ambiente, configuração e comandos para treinar o modelo novamente |
| [T14_3_Avaliacao_Conversao.md](T14_3_Avaliacao_Conversao.md) | Avaliação por classe e conversão para TFLite/LiteRT (FP32, Float16 e INT8) |
| [T14_4_Arquitetura_Web.md](T14_4_Arquitetura_Web.md) | Fluxo da foto até o resultado, componentes, contratos de entrada e saída e build |
| [T14_5_Guia_Retreinamento.md](T14_5_Guia_Retreinamento.md) | Receber novas imagens, retreinar, publicar uma nova versão e reverter para a anterior |
| [T14_6_Validacao_Externa.md](T14_6_Validacao_Externa.md) | Protocolo e registro do ensaio do guia de retreinamento por alguém de fora do desenvolvimento |

## 3. Relatórios de avaliação do modelo final

| Documento | Conteúdo |
| --- | --- |
| [Avaliacao_Final_T11_1.md](Avaliacao_Final_T11_1.md) | Métricas gerais e por classe dos modelos Float16 e INT8 entregues |
| [Matriz_Erros_T11_2.md](Matriz_Erros_T11_2.md) | Matriz de confusão e análise dos erros mais frequentes |
| [Avaliacao_Limiar_T11_3.md](Avaliacao_Limiar_T11_3.md) | Comportamento do limiar de confiança de 0,65 e casos inadequados |

## 4. Desempenho e testes no aparelho

| Documento | Conteúdo |
| --- | --- |
| [Validacao_T12_1.md](Validacao_T12_1.md) | Tamanho dos modelos e do pacote web |
| [Benchmark_T12_2.md](Benchmark_T12_2.md) | Latência medida no iPhone 13 (Chrome e Safari) |
| [Testes_Dispositivo_T12_3.md](Testes_Dispositivo_T12_3.md) | Protocolo de testes funcionais do pipeline completo no aparelho |
| [Testes_Navegacao_Conteudo_T13_3.md](Testes_Navegacao_Conteudo_T13_3.md) | Testes de navegação e apresentação do conteúdo técnico |

## 5. Entrega ao parceiro

| Documento | Conteúdo |
| --- | --- |
| [T15_1_Checklist_Final.md](T15_1_Checklist_Final.md) | Situação de cada requisito, evidências e pendências |
| [T15_2_Roteiro_Demonstracao.md](T15_2_Roteiro_Demonstracao.md) | Roteiro e ensaio da demonstração do MVP |
| [T15_3_Entrega_Parceiro.md](T15_3_Entrega_Parceiro.md) | Pacote final, inventário versionado e registro da validação com o Agro App |

## 6. Registros históricos de etapas intermediárias

Mantidos para rastreabilidade. O conteúdo vigente está nas seções correspondentes do `Projeto.md`.

| Documento | Conteúdo |
| --- | --- |
| [MR_T7_1.md](MR_T7_1.md) | Descrição da mudança que implementou a conversão TFLite (T7.1) |
| [Benchmark_T8_2.md](Benchmark_T8_2.md) | Atalho para o benchmark de inferência da seção 8.2 |
| [Benchmark_T8_2_historico_T5_6.md](Benchmark_T8_2_historico_T5_6.md) | Coleta de benchmark anterior, com as seis versões da T5.6 |

## Outros READMEs

- [README do frontend](../frontend/README.md): execução, build, hospedagem, modo offline e contrato de imagem da aplicação.
- READMEs de evidências em `assets/data/`, por exemplo [avaliação T6.1](../assets/data/avaliacao_T6_1/README.md), [calibração T7.3](../assets/data/calibracao_T7_3/README.md) e [independência T10.1](../assets/data/independencia_T10_1/README.md).
