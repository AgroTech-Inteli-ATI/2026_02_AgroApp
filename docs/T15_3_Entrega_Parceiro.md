# T15.3 — Pacote final e validação com o Agro App

Responsável pela atividade: Karol · Pacote preparado em 22/11/2026

## Pacote versionado para entrega

| Item | Identificação e localização |
| --- | --- |
| Build web | `agroapp-demo-2026-11-22T17-58-58-271Z-42c280dd`, 27 arquivos verificados. [Inventário release.json](../assets/data/ensaio_T15_2/release.json). |
| Código | Commit `42c280ddc0fe5df4e81a737083347388b66f512f` da develop. O manifesto registra a atualização de `frontend/tsconfig.tsbuildinfo`, cache incremental gerado pela compilação. |
| Modelos | Versão web 1.0.0, Float16 T7.2 principal e INT8 T7.3 contingência, EfficientNet-Lite0, LiteRT.js 2.6.0 e política top 3 com limiar 0,65. [Manifesto web](../frontend/dist/models/manifest.json). |
| Documentação | [Dataset](T14_1_Dataset_Final.md), [treinamento](T14_2_Pipeline_Treinamento.md), [avaliação e conversão](T14_3_Avaliacao_Conversao.md), [arquitetura web](T14_4_Arquitetura_Web.md), [retreinamento e reversão](T14_5_Guia_Retreinamento.md). |
| Relatórios | [Avaliação histórica](Avaliacao_Final_T11_1.md), [tamanho](Validacao_T12_1.md), [benchmark](Benchmark_T12_2.md), [protocolo funcional no aparelho](Testes_Dispositivo_T12_3.md), [checklist](T15_1_Checklist_Final.md) e [ensaio](T15_2_Roteiro_Demonstracao.md). |

O arquivo local está em `frontend/.work/demo/agroapp-demo-2026-11-22T17-58-58-271Z-42c280dd.tar.gz`, com SHA-256 `ad2d812de8edd1850254591e7cd2eee228b1004f58983370c91c7eff69c77a51`. O arquivo inclui o site completo, os dois modelos web, o manifesto de integridade e as instruções de uso. Código, relatórios e documentação acompanham a entrega por referência aos commits do repositório.

### Reprodução

Em um checkout do commit de código acima, use Node.js 22 e execute na pasta `frontend`:

```powershell
npm.cmd ci
npm.cmd run demo:package
npm.cmd run demo:verify -- .work/demo/<identificador-gerado>/site
```

O empacotador atribui um novo identificador pelo instante de geração. Compare os hashes dos arquivos publicados com o inventário registrado para identificar diferenças. Para abrir o pacote congelado, sirva a pasta `site` completa via HTTP local no computador ou via HTTPS no celular. Exemplo após extrair o arquivo e entrar na pasta do pacote:

```powershell
python -m http.server 4173 --bind 127.0.0.1 --directory site
```

Abra `http://127.0.0.1:4173` e siga o roteiro T15.2. Para reproduzir as medições e a avaliação, use os protocolos dos respectivos relatórios. O acesso ao acervo de origem pode requerer as permissões e os caminhos descritos na ficha do dataset.

## Registro da validação com o parceiro

**Estado:** pacote preparado e ensaiado localmente. Apresentação, feedback, ajustes acordados e aceite seguem pendentes de registro com o Agro App.

| Campo da ata | Registro |
| --- | --- |
| Data, participantes e canal | Pendente |
| Identificador, URL e hash do build efetivamente apresentado | Pendente |
| Casos executados na sessão e evidências | Pendente |
| Feedback do Agro App e decisão de aceite | Pendente |
| Ajustes acordados, responsável, prazo e aceite | Pendente |
| Commit ou novo build por ajuste implementado | Pendente |

## Pendências para a sessão

| Tema | Registro esperado |
| --- | --- |
| TAP e escopo web | Conferir o TAP integral e documentar os critérios aplicáveis, o aparelho de referência, o que conta no tamanho do pacote e os limites ratificados. |
| Conteúdo técnico | Validar as 13 classes, nomes, hipóteses concorrentes, chaves e destinos oficiais do catálogo. |
| Modelo | Discutir o limiar, a meta de acurácia entre aceitas e a coleta independente para avaliar generalização e perda por quantização. |
| Dispositivo | Concluir captura, galeria, uso offline com inspeção de tráfego, 50 capturas fim a fim e medição de memória no aparelho acordado. |

Após a sessão, registrar cada ajuste com evidência, responsável, prazo e estado. Se um ajuste alterar o site, publicar um novo manifesto e vincular o novo build à ata.
