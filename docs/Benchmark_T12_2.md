# Benchmark de latência no aparelho — T12.2

Autor: Rui · Revisora: Karol

## Estado da coleta

Instrumentação preparada na branch `feat/t12-2-benchmark-dispositivo`, baseada em `fe33e35` da develop. **Duas coletas automáticas reais recebidas e validadas (Safari e Chrome no iPhone 13), além de três capturas em gravação de tela.** O benchmark literal de p95 de cinquenta capturas completas não foi executado; os limites continuam propostos. Os testes automatizados em computador verificam a instrumentação; não são resultados do iPhone.

Aparelho informado por Rui: **iPhone 13, iOS 26.6.2, Chrome 158.0.8127.35**. Essas versões são declaradas pelo operador e devem ser conferidas nas configurações do aparelho. O relatório também registra o user-agent, sem usá-lo para inferir a versão exata do aplicativo Chrome.

## Instrumentação

O painel só aparece com `?benchmark=1`. Executa o mesmo `analyze`, worker, preprocessing, modelo, política de confiança e renderização da aplicação. Não envia as imagens ao servidor e não altera seleção do modelo ou confiança. Usa 3 aquecimentos adicionais (fora da estatística), seguidos de 50 análises sequenciais; as imagens escolhidas são alternadas ciclicamente. Há também um aquecimento sintético durante a inicialização do runtime.

O JSON exportado identifica os arquivos por nome, tamanho, tipo e SHA-256, sem incluir seus pixels. Guarda amostras brutas, condições declaradas, modelo efetivamente carregado, hashes original/web, runtime, acelerador solicitado, aceleração completa ou parcial e CPU configurada para uma thread. O delegate interno da CPU não é exposto pela API usada: o relatório não presume que seja XNNPACK. Guarda também manifesto, URLs dos scripts e hash do `sw.js` obtido antes da coleta, para rastrear o build servido.

| Medida | Fronteira |
| --- | --- |
| `workerToReadyMs` | Criação do worker → mensagem `ready`; inclui manifesto, download/cache, runtime, compilação, conferência e aquecimento sintético. |
| `navigationToReadyMs` | Origem temporal da navegação → `ready`; inclui carregamento da página, sem alegar inicialização fria do processo do navegador. |
| `preparationMs` | Preparação no worker: decodificação, orientação, resize, normalização/quantização e criação do tensor. |
| `inferenceMs` | `CompiledModel.run()` + espera/leitura de `output.data()`; inclui sincronização, exclui ordenação dos scores e interface. |
| `fileToPaintMs` | Arquivo disponível no início de `analyze` → dois `requestAnimationFrame` após o commit React do resultado; inclui preparação, comunicação, inferência, pós-processamento e atualização da interface. É aproximação da apresentação, sem garantir decodificação da miniatura. |

O navegador não disponibiliza o instante do disparo da câmera nativa. `fileToPaintMs` **exclui câmera, confirmação da foto e seletor de arquivos**; não deve ser publicado como captura → resultado. Para esse intervalo, usar gravação de tela e anotar explicitamente os quadros do disparo e do resultado, conforme protocolo abaixo.

p50/p95 usam interpolação linear na posição `(n-1)*p` das amostras ordenadas, em milissegundos, excluindo os 3 aquecimentos. Uma coleta interrompida mantém amostras parciais e `complete: false`; suas estatísticas não substituem as 50 execuções. Ocultar a aba, bloquear a tela, recarregar o modelo, erro do worker ou timeout de 60 s interrompe a coleta. Os arquivos são identificados antes das medições para não incluir o hashing nos tempos.

## Protocolo no iPhone

1. Gerar o build e servir `frontend/dist` por HTTPS. Abrir o endereço com `?benchmark=1` no Chrome do aparelho. Manter o Mac/servidor acordado caso seja utilizado túnel temporário.
2. Com rede, aguardar **Modelo pronto** e **Cache offline: pronto**. O acesso inicial precisa de rede; não recarregar a página depois de desligá-la. Conferir Float16 principal ou registrar que a contingência INT8 foi realmente carregada.
3. Conferir aparelho, iOS e Chrome. Informar bateria, carregamento, modo de economia, temperatura percebida, outros aplicativos em uso e se é primeiro acesso ou cache já preenchido. Não confundir primeira abertura nessa origem com reinicialização fria do sistema operacional.
4. Escolher, preferencialmente, de 5 a 10 fotos reais representativas do uso, incluindo diferentes dimensões/orientações. Baixar as fotos para o aparelho antes de desligar a rede. Caso só uma imagem seja usada, registrar a menor diversidade como limitação do ensaio. Não inferir qualidade de classificação a partir desta coleta de latência.
5. Ativar modo avião e desligar também o Wi-Fi; retornar ao Chrome e marcar a confirmação manual. `navigator.onLine` é informação complementar, não prova de ausência de rede.
6. Iniciar 50 medições, manter a aba visível e a tela ligada. Não interagir com a análise durante o lote. Não gravar a tela durante esse lote para evitar misturar o custo da gravação.
7. Exportar o JSON, salvar no Arquivos e transferir o arquivo intacto para análise. Registrar os resultados recebidos em `assets/data/benchmark_T12_2/`, mantendo os JSON brutos. Não editar métricas nem metadados do arquivo original.
8. Para inicialização com cache, reabrir com rede e gerar uma nova coleta identificada como cache preenchido. Cada JSON descreve uma inicialização; não calcular p95 de inicialização usando as 50 inferências. Uma inicialização isolada deve ser reportada como observação única.

## Captura → resultado: medição complementar

Fazer uma gravação de tela separada com a versão identificada acima. Executar ao menos três capturas com câmera nativa, mantendo visível a sequência de disparo, confirmação/uso da foto e resultado. Guardar o vídeo e seu SHA-256; anotar por tentativa: imagem/cena, quadro e instante do disparo, quadro e instante em que o resultado ficou visível e diferença. A confirmação humana da foto integra esse intervalo e deve ser explicitada. Se o vídeo não mostrar o disparo, registrar que o intervalo exato não pôde ser medido.

Esse pequeno ensaio descreve a experiência de câmera e não comprova o RNF-03 de 50 execuções/p95; a gravação também pode adicionar custo. Para comprovar esse requisito literalmente, seriam necessárias 50 capturas medidas com o mesmo protocolo, além da validação da fronteira de medição com o parceiro.

## Comparação com requisitos

Os limites da seção 2.1 de `Projeto.md` continuam marcados como propostas pendentes de ratificação:

- RNF-04: p95 ≤ 300 ms de inferência, originalmente com TFLite Benchmark Tool. O resultado LiteRT.js no Chrome é a medição da aplicação web; comparar numericamente, declarar a diferença metodológica e não alegar que o benchmark nativo foi executado.
- RNF-03: p95 ≤ 3 s de captura → resultado, em 50 execuções e modo avião. O lote automatizado cobre apenas arquivo → interface. Mesmo que fique abaixo de 3 s, não comprova sozinho o requisito completo.

As coletas automáticas e o ensaio complementar de câmera estão descritos abaixo; os marcos de câmera são aproximações visuais. Não há aprovação automática nem evidência de RAM/consumo de bateria neste benchmark. Não houve treinamento, recalibração nem consulta ao teste para seleção de modelo.

## Reprodução da instrumentação

```bash
cd frontend
npm ci
npm run build
npm test
npm run preview -- --port 4173 --strictPort
```

Servir esse preview por HTTPS para o telefone. O `build` inclui a versão instalada do `@litertjs/core` no manifesto; o worker devolve a identidade do modelo que carregou e teve seu SHA-256 verificado.

Os testes de `tests/benchmark.spec.ts` verificam exportação de 53 amostras (3 + 50), identidade do modelo/runtime e interrupção por página oculta. `src/lib/benchmark.test.ts` verifica percentis, fronteiras estatísticas e rejeição de valores inválidos. Os testes de inferência Float16/INT8 e offline verificam regressões da aplicação; resultados de automação não são publicados como medições do aparelho físico.

## Primeira coleta real — Safari no iPhone 13

Coleta em **19/11/2026, 15:32:17–15:32:23 (America/Sao_Paulo)**. [JSON original](../assets/data/benchmark_T12_2/iphone13_20261119_183217.json), preservado byte a byte; SHA-256 `3903453d0d92c9dff4ee31149e79768358a611ea4ec83bc4ce92cb84bd3e9ec4`. A [validação](../assets/data/benchmark_T12_2/validacao_iphone13_20261119.json) registra conferências, percentis recalculados e correção dos metadados. O [inventário do build](../assets/data/benchmark_T12_2/build.json) registra os arquivos servidos.

**Correção de navegador:** o campo `browser` do JSON foi preenchido como Chrome, mas Rui confirmou neste chat que abriu o link no **Safari**. O user-agent registra Safari/Version 26.6.1. O original não foi editado; essa rodada deve ser identificada como Safari, sem atribuir seus números ao Chrome. O iOS 26.6.2 permanece informação declarada pelo operador; o user-agent não confirma a versão exata do sistema.

Condições: bateria 71%, economia de energia desativada, temperatura percebida normal. Modo avião declarado, `navigator.onLine: false` no início e fim, cache offline pronto. Rui informou que já havia aberto/recarregado o endereço; não foi isolado se cada recurso da inicialização veio do cache. Não se trata de uma medição controlada de primeiro acesso nem de inicialização fria do processo.

Modelo **Float16 principal, EfficientNet-Lite0**, 6.833.548 bytes, com **LiteRT.js 2.6.0 e WebGPU totalmente acelerado**, sem uso da contingência. A opção de CPU é uma thread, mas o processamento efetivo registrado foi WebGPU. Os hashes original/web e do service worker conferem com o manifesto e o build preparado. Foram escolhidas **5 imagens distintas (4 PNG, incluindo capturas de tela, e 1 JPEG)**, identificadas por SHA-256; cada uma recebeu 10 medições. Essa seleção avalia latência, sem representar cobertura agronômica das 13 classes.

| Medida | n | p50 | p95 | Máximo |
| --- | ---: | ---: | ---: | ---: |
| Preparação | 50 | 43,93 ms | 134,35 ms | 138,74 ms |
| Inferência | 50 | 10,01 ms | 13,38 ms | 20,48 ms |
| Arquivo → apresentação aproximada | 50 | 83,44 ms | 166,88 ms | 183,40 ms |

Inicialização observada uma vez: **19.762,64 ms do worker até pronto**, e **20.152,80 ms da origem da navegação até pronto**. Esses tempos incluem carregamento/cache, compilação e aquecimento; não são percentis e não devem ser misturados aos tempos das análises com modelo já carregado. A fonte da demora não foi isolada.

Foram conferidas as 53 amostras (3 aquecimentos + 50 medidas), 10 medidas por imagem, durações finitas e não negativas, identidade do manifesto/modelo, hash do service worker, presença do script no inventário e p50/p95 recalculados independentemente em Python. Não houve falha no lote. Os arquivos de imagem não foram recebidos: seus hashes são os declarados pelo coletor no aparelho, não uma conferência independente de seus pixels.

**Interpretação:** a inferência fica numericamente abaixo da proposta de 300 ms neste aparelho, navegador e backend, sob a metodologia LiteRT.js descrita. Arquivo → apresentação também fica abaixo de 3 s, mas exclui a câmera e não fecha o RNF-03. Não comprova qualidade de classificação, outros aparelhos, fallback INT8, primeiro acesso rápido nem estabilidade térmica em sessão prolongada. A rodada no Chrome está descrita a seguir; os lotes foram mantidos separados por navegador e backend.

## Coleta de referência — Chrome no iPhone 13

Coleta em **19/11/2026, 15:38:37–15:38:43 (America/Sao_Paulo)**. [JSON original](../assets/data/benchmark_T12_2/iphone13_chrome_20261119_183837.json), preservado byte a byte; SHA-256 `6c8e4102abd74e2d3d75cd03eee924bae943644733e9e96d4c28b269da58cc9d`. A [validação independente](../assets/data/benchmark_T12_2/validacao_iphone13_chrome_20261119.json) confirma contagem, estatísticas recalculadas e rastreabilidade.

O user-agent contém **CriOS/158.0.8127.35** e **iPhone OS 26_6_2**, coerentes com Chrome 158.0.8127.35 e iOS 26.6.2 informados. O aparelho iPhone 13 permanece declarado pelo operador. Bateria 70%, temperatura percebida normal, modo avião declarado e `navigator.onLine: false` no início e no fim, cache offline pronto. O campo de condições escreveu “economia de rede: nao”; isso não confirma o modo de economia de energia, e o original foi preservado sem corrigir por inferência. O estado do cache durante a inicialização não foi isolado.

São **as mesmas cinco imagens por SHA-256**, o mesmo build, modelo Float16 e backend WebGPU totalmente acelerado da rodada Safari. A ordem de seleção mudou; cada imagem recebeu dez medições em ambos os lotes. As coletas são sequenciais, não um experimento controlado para atribuir diferenças ao navegador. Não foram agrupadas numa distribuição única.

| Medida | n | p50 | p95 | Máximo |
| --- | ---: | ---: | ---: | ---: |
| Preparação | 50 | 45,44 ms | 136,20 ms | 138,78 ms |
| Inferência | 50 | 10,16 ms | 13,10 ms | 13,18 ms |
| Arquivo → apresentação aproximada | 50 | 83,41 ms | 166,87 ms | 183,70 ms |

Inicialização observada uma vez: **20.479,76 ms do worker até pronto**, e **21.112,78 ms da origem da navegação até pronto**. A inicialização é medida separadamente e não entra nos percentis das análises. Seu custo não foi decomposto entre rede/cache, carregamento, compilação e aquecimento.

### Comparação descritiva das duas coletas

| Navegador | Preparação p95 | Inferência p95 | Arquivo → apresentação p95 | Inicialização do worker (1 observação) |
| --- | ---: | ---: | ---: | ---: |
| Safari | 134,35 ms | 13,38 ms | 166,88 ms | 19,76 s |
| Chrome | 136,20 ms | 13,10 ms | 166,87 ms | 20,48 s |

Os números são próximos nesses dois lotes, sem evidência suficiente para declarar um navegador superior. No Chrome, inferência p95 de 13,10 ms fica numericamente abaixo da proposta de 300 ms, sob a metodologia LiteRT.js, e arquivo → apresentação p95 de 166,87 ms também é inferior a 3 s. A segunda comparação é parcial: **não mede o intervalo do disparo da câmera ao resultado e não comprova RNF-03**. A coleta é específica do iPhone 13/WebGPU e não valida contingência INT8, outros aparelhos, estabilidade térmica prolongada ou qualidade de classificação.

**Ensaio complementar recebido:** a gravação abaixo documenta três capturas no Chrome com modelo já pronto. Os marcos visuais aproximam a captura e não substituem cinquenta capturas medidas para certificar literalmente p95 do intervalo completo.

## Ensaio complementar de câmera — gravação de tela

Arquivo fornecido por Rui: `ScreenRecording_11-19-2026 15-43-54_1.MP4`, **186.527.307 bytes**, duração **108,325 s**, resolução **1170 × 2532**. SHA-256 `5dfe5997a0b0307bb682aa6d3e9496c08f775694143e08135cb1f7856e6ce740`. O original permanece no acervo do operador; não foi incorporado ao Git pelo tamanho. Foram preservados [quadros com hashes e observações](../assets/data/benchmark_T12_2/camera_20261119/observacoes.json) e a [tabela de tempos](../assets/data/benchmark_T12_2/camera_20261119/tempos.csv).

Extração com AVFoundation do macOS, respeitando a orientação e usando o timestamp de apresentação (PTS) devolvido pelo decodificador. As imagens de evidência foram reduzidas para largura máxima de 440 px. O vídeo tem taxa nominal informada de 38,39 fps; não se presumiu intervalo constante entre quadros. Foram inspecionados quadros a cada 0,05 s nas transições de captura e a cada 0,2 s nos demais marcos. Os números abaixo são aproximações arredondadas a 0,1 s, não medições instrumentadas do sensor ou do toque.

O marco de captura é a animação/alteração visual da câmera, usada como **proxy**: o instante físico do disparo não está disponível. O marco de retorno é o primeiro quadro amostrado de fechamento da câmera/retorno ao navegador, não o instante exato do toque em “Use Photo”. O fim do processamento é a mudança do indicador de análise, que antecede a leitura das hipóteses ou do inconclusivo por estarem abaixo da área visível. O marco de decisão legível é um quadro após a rolagem com o resultado identificável. Não são necessariamente os primeiros quadros possíveis de cada evento.

| Tentativa | Captura: proxy no vídeo | Retorno ao navegador | Indicador finalizado | Decisão legível após rolagem | Proxy → decisão legível | Retorno → indicador finalizado |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 23,425 s | 25,790 s | 26,958 s | 30,995 s | ≈ 7,6 s | ≈ 1,2 s |
| 2 | 51,892 s | 56,995 s | 58,197 s | 60,198 s | ≈ 8,3 s | ≈ 1,2 s |
| 3 | 84,492 s | 86,392 s | 87,393 s | 88,595 s | ≈ 4,1 s | ≈ 1,0 s |

Resultados visíveis: primeira tentativa com hipótese principal **Percevejo-barriga-verde**, score **96,9%**; segunda **inconclusiva**, sem afirmar diagnóstico; terceira com hipótese principal **Astylus variegatus**, score **99,9%**. Scores não são probabilidades de acerto calibradas. Não há rótulo independente das fotos neste ensaio para declarar acurácia.

As três tentativas usam a câmera para fotografar imagens em um monitor, com confirmação manual da foto. O fluxo completa os três ciclos sem erro visível e permite repetir a captura depois de um inconclusivo. A identidade de modelo/runtime provém das coletas JSON associadas à mesma versão servida; o vídeo sozinho não fornece nova verificação criptográfica do modelo. O painel final mostra modo avião e Wi-Fi habilitado: **o vídeo não comprova ausência de rede**, diferentemente dos indicadores declarados/registrados dos lotes automáticos.

**Interpretação:** o intervalo até a decisão legível inclui câmera nativa, espera/confirmação humana, retorno ao navegador, processamento e rolagem. Não deve ser atribuído à inferência. A página já indica análise finalizada antes de a decisão entrar na área visível; isso é uma observação de usabilidade relevante para a demonstração. O intervalo de cerca de 1,0–1,2 s após o retorno também não é inferência isolada: inclui entrega/decodificação da foto e atualização da interface. Fotos de câmera e gravação ativa têm condições distintas das cinco imagens do lote automático.

Os três intervalos observados até a decisão legível superam 3 s, mas não demonstram reprovação estatística nem aprovação de RNF-03: usam fronteira com interação humana/rolagem, proxy visual de captura e apenas três observações. Não se calculou p95 para apresentar essa amostra como comprovação de cinquenta capturas. A inferência do Chrome permanece numericamente abaixo de 300 ms no lote automático; a validação literal do intervalo completo em cinquenta execuções e a ratificação da fronteira/limite pelo parceiro continuam abertas.
