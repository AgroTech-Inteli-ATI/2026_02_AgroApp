# T12.3 — Testes funcionais do pipeline completo no dispositivo

Autor: Glauco · Revisora: Karol · Meta de entrega: a definir · Entregue em: pendente

**Situação:** protocolo, ferramentas e verificações automatizadas prontos. **A execução no aparelho real está pendente** e é registrada nas tabelas de resultado abaixo. Os testes automatizados não substituem essa execução.

## Escopo

A T12.3 valida no navegador do celular:

- captura pela câmera e seleção pela galeria;
- preprocessing (EXIF) e execução do modelo;
- apresentação das hipóteses e tratamento de erros, incluindo cancelamento e repetição.

Também comprova que, depois do carregamento inicial, a classificação acontece no próprio aparelho, sem envio da fotografia, inclusive sem conexão. Para isso são usados:

| Recurso | Para quê |
| --- | --- |
| [`frontend/scripts/device-kit.py`](../frontend/scripts/device-kit.py) | Gera o kit de imagens para a galeria do celular, com hashes e resultado esperado em `kit.json`. |
| [`frontend/scripts/verify-har.mjs`](../frontend/scripts/verify-har.mjs) | Confere o log de rede (HAR) exportado do DevTools: nenhum envio de dados, nenhuma origem externa e, no diagnóstico, nenhuma requisição. |
| [`frontend/tests/sessao-local.spec.ts`](../frontend/tests/sessao-local.spec.ts) | Ensaio automatizado da sessão local no build de produção com emulação de Pixel 7. |

## Evidências automatizadas (já executadas)

Executadas em 20/11/2026 no Windows, Chromium do Playwright, com o build de produção (`npm run build` + preview):

| Verificação | Resultado |
| --- | --- |
| `sessao-local.spec.ts`: após "Modelo pronto · disponível offline", rede desligada sem recarregar e duas análises (Tirar foto e Trocar foto) | **Passou.** Nenhuma requisição de rede após a carga, inclusive do worker e do service worker. Só houve leituras `blob:` da própria foto na memória do navegador, para a pré-visualização. O HAR da sessão foi aprovado pelo verificador. |
| Carga inicial medida no mesmo HAR | 41 requisições, ≈ 67,0 MB transferidos, todas `GET` à origem do app. |
| Kit do dispositivo aplicado ao app no Chromium desktop | 15/15 arquivos com o resultado esperado: as 6 mensagens de erro exatas e as 9 fotos válidas com Vaquinha aceita. |
| Testes unitários (`npm test`) | 22 passaram, incluindo os 3 do verificador de HAR. |
| `npx playwright test --project=offline` | 3 passaram: reabertura offline (T9.4), aviso de pré-cache e sessão local (T12.3). |

Esses testes não abrem a câmera física, não pedem permissões do Android e não medem o desempenho do aparelho.

## Necessidade de conexão para o carregamento inicial

- **O primeiro acesso exige conexão.** O app, o runtime LiteRT e o modelo vêm do servidor. Sem rede e sem visita anterior, o navegador nem abre o app (caso ERR-07).
- **Volume:** na primeira visita, o service worker baixa de uma vez o app, os dois modelos (Float16 e INT8) e as quatro variantes do runtime WASM. O ensaio automatizado mediu **≈ 67 MB transferidos em 41 requisições**, com a compressão do servidor de preview. O pacote publicado soma 58,26 MB sem compressão ([T12.1](Validacao_T12_1.md)). O número real no celular é registrado em NET-01.
- **Depois de "Modelo pronto · disponível offline"**, a classificação não usa rede, com a página aberta (OFF-01) ou reaberta (OFF-02, T9.4).
- **Com "modo offline indisponível"** (falha de cota ou de rede no pré-cache), a sessão aberta continua classificando, mas reabrir sem rede falha.
- **Novas versões** do app ou do modelo exigem conexão. O navegador pode apagar o cache se faltar espaço no aparelho; nesse caso, volta a ser preciso conectar.

## Preparação

### 1. Build e kit

Na raiz do repositório:

```powershell
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
python frontend/scripts/device-kit.py
```

Copie todo o conteúdo de `frontend/.work/kit-dispositivo/` para a galeria do celular, por exemplo pela pasta `Pictures/` via USB. Mantenha `kit.json` no computador para consultar os resultados esperados.

### 2. Servir o app ao celular

**Opção recomendada: USB, com o mesmo cabo para monitorar a rede.**

1. No celular, ative **Opções do desenvolvedor → Depuração USB** e conecte o cabo.
2. No computador: `cd frontend` e depois `npm.cmd run preview -- --port 4173`.
3. No Chrome do computador, abra `chrome://inspect/#devices` → **Port forwarding** → `4173` → `localhost:4173` → marque **Enable port forwarding**.
4. No Chrome do celular, abra `http://localhost:4173`. Por ser `localhost`, o navegador trata a página como contexto seguro: service worker, Web Crypto e câmera funcionam sem certificado.

**Alternativa:** publicar `frontend/dist` em hospedagem estática HTTPS, como descrito no [README do frontend](../frontend/README.md#build-e-hospedagem). É o cenário mais próximo da produção. O monitoramento continua por `chrome://inspect` via USB.

Em `chrome://inspect`, clique em **inspect** na aba do app para abrir o DevTools do celular no computador.

### 3. Identificação da execução

| Campo | Valor |
| --- | --- |
| Data e responsável | |
| Aparelho (modelo) | |
| Versão do Android | |
| Versão do Chrome | |
| Forma de acesso (USB `localhost` ou URL HTTPS) | |
| Commit do build (`git rev-parse HEAD`) | |
| SHA-256 de `frontend/dist/models/manifest.json` | |
| Nome do cache (DevTools → Application → Cache Storage) | |
| Modelo em uso e acelerador (rodapé do app: Float16/INT8, WebGPU ou CPU/WebAssembly) | |

## Monitoramento de rede

No DevTools do celular, aba **Network**, marque **Preserve log** e deixe **Disable cache** desmarcado.

1. **Carga (NET-01):** no celular, limpe os dados do site (Chrome → Configurações do site → Armazenamento) para simular o primeiro acesso. Abra o app e espere **Modelo pronto · disponível offline**. Exporte o log pelo ícone **Export HAR** como `carga.har`.
2. Clique em **Clear network log** (🚫).
3. **Diagnóstico (NET-02):** execute os casos CAP, GAL, EXIF, CAN, REP e ERR. Depois exporte `diagnostico.har` e tire uma captura de tela do painel Network.
4. No computador, em `frontend/`:

```powershell
node scripts/verify-har.mjs caminho\carga.har --fase carga > carga-resumo.json
node scripts/verify-har.mjs caminho\diagnostico.har --fase diagnostico > diagnostico-resumo.json
```

O comando termina com código 0 quando aprovado e lista os problemas encontrados. Na carga, reprova qualquer método diferente de `GET`/`HEAD`, requisição com corpo, query string longa ou origem externa ao app. No diagnóstico, também reprova **qualquer** requisição de rede. URLs `blob:` e `data:` são locais e não contam.

Guarde `carga-resumo.json`, `diagnostico-resumo.json` e as capturas de tela em `assets/data/testes_dispositivo_T12_3/`. Os HARs brutos são grandes e podem conter cabeçalhos do aparelho; guarde-os fora do Git e registre o SHA-256 deles.

## Casos de teste e registro de resultados

Preencha **Resultado** com `Passou`, `Falhou` ou `N/A`, e **Observação/evidência** com o que foi visto: score, tempo, mensagem ou nome da captura. Os scores esperados são do Float16 em CPU. Em WebGPU ou INT8, aceite diferença de até 0,02 no score, desde que a classe e a decisão não mudem.

### Captura pela câmera

| ID | Passos | Esperado | Resultado | Observação/evidência |
| --- | --- | --- | --- | --- |
| CAP-01 | Tocar **Tirar foto** | Abre a câmera do aparelho (traseira, `capture="environment"`) | Pendente | |
| CAP-02 | Fotografar `referencia.jpg` aberta em outra tela ou impressa, com o celular **em pé** | Análise conclui; hipóteses ou "Identificação inconclusiva"; em **Entrada do modelo** a foto aparece em pé, com faixas cinza | Pendente | |
| CAP-03 | Repetir CAP-02 com o celular **deitado** (paisagem) | Mesma classe; Entrada do modelo na orientação correta | Pendente | |
| CAP-04 | Fotografar um inseto ou cena real fora das 13 classes | Resultado coerente com a política: inconclusivo ou hipóteses com score; sem travar | Pendente | |
| CAP-05 | Primeiro uso: negar a permissão de câmera, se o Android pedir | Volta ao app sem foto e sem erro; nova tentativa pede a permissão de novo ou orienta pelas configurações | Pendente | |

### Galeria e EXIF

| ID | Arquivo | Esperado | Resultado | Observação/evidência |
| --- | --- | --- | --- | --- |
| GAL-01 | `referencia.jpg` | Vaquinha, aceito, top-1 ≈ 0,978 | Pendente | |
| GAL-02 | Foto tirada antes pela câmera do próprio celular | Análise conclui; orientação correta em Entrada do modelo | Pendente | |
| EXIF-01 | `exif-1.jpg` | Vaquinha, aceito, ≈ 0,978; inseto em pé em Entrada do modelo | Pendente | |
| EXIF-02 | `exif-2.jpg` | Vaquinha, aceito, ≈ 0,978; em pé | Pendente | |
| EXIF-03 | `exif-3.jpg` | Vaquinha, aceito, ≈ 0,980; em pé | Pendente | |
| EXIF-04 | `exif-4.jpg` | Vaquinha, aceito, ≈ 0,979; em pé | Pendente | |
| EXIF-05 | `exif-5.jpg` | Vaquinha, aceito, ≈ 0,978; em pé | Pendente | |
| EXIF-06 | `exif-6.jpg` | Vaquinha, aceito, ≈ 0,979; em pé | Pendente | |
| EXIF-07 | `exif-7.jpg` | Vaquinha, aceito, ≈ 0,980; em pé | Pendente | |
| EXIF-08 | `exif-8.jpg` | Vaquinha, aceito, ≈ 0,979; em pé | Pendente | |

As oito fotos EXIF têm pixels girados ou espelhados de formas diferentes. Se a orientação for aplicada corretamente, todas aparecem iguais e com a mesma classe. Uma foto deitada ou espelhada em Entrada do modelo indica falha.

### Cancelamento e repetição

| ID | Passos | Esperado | Resultado | Observação/evidência |
| --- | --- | --- | --- | --- |
| CAN-01 | Com um resultado na tela, **Tirar outra foto** → voltar sem fotografar | Foto e resultado anteriores mantidos; sem mensagem de erro | Pendente | |
| CAN-02 | **Trocar foto** → fechar a galeria sem escolher | Igual a CAN-01 | Pendente | |
| CAN-03 | Sem foto, **Escolher da galeria** → cancelar | Volta ao estado inicial, sem erro | Pendente | |
| REP-01 | Escolher a mesma foto duas vezes seguidas | Nova análise a cada escolha (o tempo exibido muda) | Pendente | |
| REP-02 | Fazer 5 análises seguidas, alternando câmera e galeria | Sem travar e sem recarregar o modelo; o app continua responsivo | Pendente | |
| REP-03 | Durante uma análise, tocar de novo nos botões | Botões desabilitados até concluir | Pendente | |
| REP-04 | **Remover foto** | Volta ao estado inicial | Pendente | |

### Situações de erro

| ID | Passos | Mensagem esperada | Resultado | Observação/evidência |
| --- | --- | --- | --- | --- |
| ERR-01 | Galeria: `transparente.png` | "A imagem tem transparência. Escolha um JPEG ou uma imagem sem transparência." | Pendente | |
| ERR-02 | Galeria: `acima-40mp.jpg` | "A foto é grande demais. Reduza para até 40 megapixels e tente novamente." | Pendente | |
| ERR-03 | Galeria: `acima-10mb.png` | "Escolha uma foto válida com até 10 MB." | Pendente | |
| ERR-04 | Galeria (app Arquivos): `vazia.jpg` | "Escolha uma foto válida com até 10 MB." ou o seletor não oferece o arquivo | Pendente | |
| ERR-05 | Galeria (app Arquivos): `corrompida.jpg` | "Não foi possível abrir a foto. Escolha um JPEG, PNG ou WebP válido." ou o seletor não oferece o arquivo | Pendente | |
| ERR-06 | Galeria: `animacao.gif` | "Formato não aceito. Escolha uma foto JPEG, PNG ou WebP." ou o seletor não oferece o arquivo | Pendente | |
| ERR-07 | Limpar dados do site, ativar modo avião e abrir o app | O navegador indica que não há conexão; o app não abre. Documenta a necessidade de conexão inicial | Pendente | |
| ERR-08 | Limpar dados do site e ativar modo avião enquanto aparece "Carregando o modelo…" | Mensagem pedindo para verificar a conexão, com **Recarregar modelo**; com a rede de volta, o botão conclui a carga | Pendente | |

Após cada erro, confirme que uma foto válida em seguida é analisada normalmente.

### Rede e funcionamento sem conexão

| ID | Passos | Esperado | Resultado | Observação/evidência |
| --- | --- | --- | --- | --- |
| NET-01 | Carga monitorada (seção anterior) e `verify-har.mjs --fase carga` | Aprovado; registrar requisições e MB transferidos | Pendente | |
| NET-02 | Diagnósticos monitorados e `verify-har.mjs --fase diagnostico` | Aprovado: **0 requisições de rede**; nenhum upload da foto | Pendente | |
| OFF-01 | Com "Modelo pronto · disponível offline", ativar **modo avião** e desligar o Wi-Fi. No acesso via USB, desmarcar também o *port forwarding*. **Sem recarregar**, analisar uma foto da câmera e uma da galeria | Hipóteses ou inconclusivo exibidos normalmente; o Network do DevTools continua vazio. A depuração USB segue ativa no modo avião | Pendente | |
| OFF-02 | Ainda sem rede, fechar a aba, reabrir o app e analisar uma foto (T9.4) | O app abre do cache e classifica | Pendente | |

## Conclusão da execução

| Grupo | Passou | Falhou | N/A |
| --- | ---: | ---: | ---: |
| Captura (CAP) | | | |
| Galeria e EXIF (GAL, EXIF) | | | |
| Cancelamento e repetição (CAN, REP) | | | |
| Erros (ERR) | | | |
| Rede e offline (NET, OFF) | | | |

Registre cada falha com passos, captura e versão. Uma correção no app exige um novo build, um novo `kit.json` (se os modelos mudarem) e a repetição dos casos afetados.

## Limites

- Um aparelho e um navegador comprovam o fluxo nessas condições. Safari/iOS, Firefox e outros aparelhos Android não ficam certificados.
- O acesso por USB (`localhost`) não reproduz latência de rede nem HTTPS de produção; a hospedagem HTTPS cobre essa diferença.
- O kit usa uma foto de referência do acervo, que não é independente do treinamento ([T10.1](../assets/data/independencia_T10_1/README.md)). Ele verifica o funcionamento do pipeline, não a acurácia em campo.
- Latência e memória no aparelho de referência são registradas à parte (RNF-03/04/07, pendentes na T8.3).
