# AgroApp — frontend de análise visual

React + TypeScript + Vite. O EfficientNet-Lite0 é executado no próprio navegador com LiteRT.js. Não há backend, execução de notebooks nem envio de fotografias. No build de produção, um service worker guarda o app para funcionar offline (T9.4).

## Executar localmente

Requer Node.js 22.12+ ou 24 LTS e npm. No PowerShell, use `npm.cmd` se a política de execução bloquear `npm.ps1`.

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Abra http://127.0.0.1:5173. Se a porta estiver ocupada, o Vite informa outra porta no terminal.

O comando prepara os recursos automaticamente: verifica os hashes dos modelos e das classes, gera os artefatos web e copia o runtime. O modelo carrega ao abrir a aplicação; o upload é habilitado quando a inicialização e o aquecimento terminam. Cada nova foto reutiliza o modelo carregado.

## Capturar ou selecionar uma foto

Use **Tirar foto** para abrir o seletor do dispositivo com preferência pela câmera traseira ou **Escolher da galeria** para selecionar um arquivo. A disponibilidade da câmera depende do aparelho e do navegador; no computador, o sistema pode abrir um seletor de arquivos. As duas entradas usam o mesmo processamento e inferência local. Arrastar e soltar continua disponível.

Depois da análise, use **Tirar outra foto** ou **Trocar foto**. Cancelar o seletor preserva a foto e o resultado atuais; selecionar a mesma foto novamente executa uma nova análise. Durante o processamento, as duas ações ficam desabilitadas. Os formatos aceitos são JPEG, PNG e WebP, sem transparência, até 10 MiB e 40 megapixels.

Para testar em outro dispositivo, prefira publicação estática por HTTPS. O projeto não configura certificados de desenvolvimento; HTTP em um IP de rede não fornece o contexto seguro necessário para Web Crypto e aceleração do navegador. `localhost` e `127.0.0.1` são adequados no próprio computador.

## Build e hospedagem

```powershell
npm.cmd run build
npm.cmd run preview
```

Publique o diretório `dist/` integralmente em hospedagem estática com HTTPS. Sirva `.wasm` com `Content-Type: application/wasm` e preserve os caminhos `models/`, `runtime/`, `brand/` e `assets/`. Não há API a provisionar. Sirva `sw.js` sem cache longo, para que o navegador detecte versões novas.

Para hospedagem em subdiretório, defina `VITE_BASE_PATH` com barras inicial e final antes de gerar o build, por exemplo `/agroapp/`. Para atualizar o frontend e o modelo, publique o build completo de forma atômica e faça o host revalidar `models/manifest.json` e `runtime/inference.js`, evitando misturar versões.

O servidor local adiciona COOP/COEP. Esses cabeçalhos permitem isolamento entre origens; a versão atual usa um único thread em WASM e não depende de multithreading. Todos os arquivos e fontes são servidos na mesma origem.

## Funcionamento offline (T9.4)

O build gera `dist/sw.js` (modelo em `scripts/sw.js`, lista de arquivos montada em `vite.config.ts`). Na primeira visita com rede, ele baixa e guarda de uma vez o app, as fontes, `models/manifest.json`, os dois `.tflite` do manifesto e as quatro variantes do runtime WASM (cerca de 60 MB). Quando termina, o status mostra **disponível offline**. A partir daí o app abre e classifica sem rede. Cada build novo troca o nome do cache e apaga o anterior. No `npm run dev` o service worker não é registrado.

`npx playwright test --project=offline` gera o build, abre o preview, espera o cache, desliga a rede, recarrega e classifica uma foto sem nenhuma requisição falha.

Demonstração no celular (critério da T9.4):

1. Abra a URL HTTPS com rede e espere **Modelo pronto · disponível offline**.
2. Ative o modo avião e feche a aba.
3. Abra a URL de novo, tire uma foto com **Tirar foto** e confira as hipóteses e o conteúdo técnico.
4. Registre aparelho, Android, navegador, URL e o hash do build (nome do cache em DevTools → Application → Cache Storage).

O conteúdo técnico vai embutido no bundle JS (`src/data/content.ts`), então também fica disponível offline assim que for preenchido.

## Modelo e contrato de imagem

- As 13 classes mantêm a ordem de `assets/modelos/candidato_T5_6_20261026/classes.json`.
- `model-sources.json` separa as origens das classes e de cada modelo, com caminho do contrato e chave do hash esperado. A integração segue a decisão T8.3 fornecida para esta entrega; a seção e o script da seleção não são acrescentados por esta alteração. O estado `T8.3_integrada_pendente_celular_e_parceiro` mantém explícitas as validações externas pendentes.
- **Principal:** Float16 T7.2, `comparacao_T7_2_candidato_T5_6_20261026/modelo_float16.tflite`, 6.833.548 bytes, com entrada e saída float32. **Contingência:** INT8 oficial T7.3, `quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite`, 4.003.624 bytes. O INT8 antigo da T5.6 e o FP32 não são empacotados.
- O carregador tenta o Float16 primeiro e baixa o INT8 somente se o principal não puder ser compilado, validar seus tensores ou executar o aquecimento. A troca é identificada na interface. Falhas de download ou hash são informadas e permitem recarregar; não causam troca silenciosa. A contingência por limites de latência ou memória depende da medição no aparelho e de uma decisão de configuração; não se aplica um limite automático a uma inferência isolada.
- O runtime WASM também é baixado, aproximadamente 11 MB, além do modelo, dos scripts e das fontes. O tamanho do modelo sozinho não representa o download inicial nem o consumo de RAM.
- Entrada RGB `[1,224,224,3]`, normalizada para `[0,1]`. EXIF aplicado uma vez, redimensionamento proporcional bicúbico com antialiasing e arredondamento compatível com Pillow 12.2, preenchimento `(128,128,128)`, sem recorte.
- Quantização e desquantização usam os parâmetros lidos do TFLite, sem repetir a conversão do backbone já incorporada ao grafo.
- JPEG, PNG e WebP de até 10 MiB e 40 megapixels. Imagens com transparência são recusadas para não alterar silenciosamente o contrato RGB.
- Web Worker clássico separado mantém o cálculo fora da interface. O formato clássico é necessário porque o carregador Emscripten do LiteRT usa `importScripts`.
- O INT8 usa CPU/WASM. Para o Float16, WebGPU é tentado quando disponível, com alternativa WASM. Não é usado WebNN experimental.

### Especialização para o navegador

Os arquivos originais têm formas alocadas de batch 1 e assinaturas com batch dinâmico `-1`. O LiteRT.js 2.6 exige tipos de entrada concretos para executar esse grafo. `scripts/prepare-assets.mjs` gera cópias `*_web.tflite`, substituindo somente dimensões dinâmicas nas assinaturas pelas formas já alocadas. Pesos, operadores, quantização e os arquivos originais são preservados. O manifesto web registra os hashes de origem e das cópias e o navegador verifica o hash antes de carregar.

O manifesto também registra versão da conversão, caminhos relativos de origem/contrato, origem/hash das classes e situação da seleção. O empacotamento verifica o vínculo das classes ao contrato de cada modelo, as dimensões e os tipos dos tensores. O gerador Python lê as origens desse mesmo manifesto e confere os hashes antes de inferir, evitando uma configuração independente para os testes.

O Float16 é conferido contra `comparacao.json` → `estrategias.float16.sha256`; o INT8 T7.3, contra `contrato_int8.json` → `modelo_int8_sha256`. Ao atualizar um artefato, rode `npm.cmd run assets`, regenere as referências Python dos dois modelos e repita os testes. O empacotador preserva a ordem Float16 principal, INT8 de contingência.

## Resultados e conteúdo técnico

Os três maiores scores são apresentados como hipóteses. Não se aplica limiar arbitrário e um score alto não confirma diagnóstico nem detecta automaticamente fotos fora das 13 classes.

O catálogo de conteúdo técnico fica em `src/data/content.ts`, indexado pelo índice exato da classe do modelo. Preencha somente com texto, fonte e data de revisão aprovados, marcando `validated: true` após validação. Enquanto isso, a interface mostra conteúdo indisponível. Não existem recomendações de manejo ou links oficiais inventados.

A identidade visual usa cores, tipografia e elementos da apresentação fornecida pelo usuário; a origem dos rasters está registrada em `public/brand/PROVENANCE.md`.

## Verificações

```powershell
npm.cmd test
npx.cmd playwright install chromium
npm.cmd run test:e2e
npm.cmd run build
```

Os 9 testes unitários comparam os bytes do processamento com seis referências sintéticas geradas em Python, incluindo quantização e arredondamento. Os 6 testes de navegador executam o Float16 principal e o INT8 oficial real após incompatibilidade simulada do principal. Conferem os hashes do manifesto contra as referências, comparam os 13 scores e a classe de maior score com Python e verificam EXIF, reutilização do modelo, ausência de uploads, navegação, arquivos inválidos, recuperação após falha no download e recusa de modelo alterado. Também exercitam os dois seletores, cancelamento e repetição da mesma foto em viewport móvel. A tolerância de comparação entre runtimes é de 2/256 por score.

Para regenerar as referências, em ambiente Python separado com TensorFlow 2.21.0, Pillow 12.2.0 e NumPy 2.4.4:

```powershell
python scripts/generate-reference.py
```

Execute `npm.cmd run assets` antes. Para cada um dos dois modelos, o gerador exige resultados idênticos entre o original e a cópia web na execução Python e registra seus hashes, versão, caminho original, scores e parâmetros de quantização em `reference.json` → `models`. O hash das classes e as referências de processamento são comuns. As imagens de teste são padrões sintéticos, não fotos de usuários.

Validação inicial: Chromium automatizado no Windows; layout desktop e viewport móvel de 390 px. Compatibilidade e desempenho em aparelho Android físico, Safari e Firefox ainda não foram certificados. As medições da tela são da sessão atual e não representam benchmark do celular-alvo.

A seleção automatizada de um arquivo no input de captura não comprova a abertura da câmera física nem suas permissões. Para fechar a validação mobile da T9.1, registrar em aparelho real: modelo/hash, aparelho, SO, navegador, URL HTTPS, captura e galeria, cancelamento, repetição, orientação e classificação, usando o Float16 escolhido e verificando também a contingência oficial.

Ao editar o worker ou o processamento, rode `npm.cmd run assets` novamente e recarregue a página; esses arquivos são compilados separadamente do HMR da interface.
