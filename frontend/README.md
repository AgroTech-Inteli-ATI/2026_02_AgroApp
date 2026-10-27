# AgroApp — frontend de análise visual

React + TypeScript + Vite. O EfficientNet-Lite0 é executado no próprio navegador com LiteRT.js. Não há backend, execução de notebooks, envio de fotografias, PWA ou modo offline.

## Executar localmente

Requer Node.js 22.12+ ou 24 LTS e npm. No PowerShell, use `npm.cmd` se a política de execução bloquear `npm.ps1`.

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Abra http://127.0.0.1:5173. Se a porta estiver ocupada, o Vite informa outra porta no terminal.

O comando prepara os recursos automaticamente: verifica os hashes dos modelos e das classes, gera os artefatos web e copia o runtime. O modelo carrega ao abrir a aplicação; o upload é habilitado quando a inicialização e o aquecimento terminam. Cada nova foto reutiliza o modelo carregado.

Para testar em outro dispositivo, prefira publicação estática por HTTPS. O projeto não configura certificados de desenvolvimento; HTTP em um IP de rede não fornece o contexto seguro necessário para Web Crypto e aceleração do navegador. `localhost` e `127.0.0.1` são adequados no próprio computador.

## Build e hospedagem

```powershell
npm.cmd run build
npm.cmd run preview
```

Publique o diretório `dist/` integralmente em hospedagem estática com HTTPS. Sirva `.wasm` com `Content-Type: application/wasm` e preserve os caminhos `models/`, `runtime/`, `brand/` e `assets/`. Não há API a provisionar. Sem service worker; nenhuma promessa de funcionamento offline.

Para hospedagem em subdiretório, defina `VITE_BASE_PATH` com barras inicial e final antes de gerar o build, por exemplo `/agroapp/`. Para atualizar o frontend e o modelo, publique o build completo de forma atômica e faça o host revalidar `models/manifest.json` e `runtime/inference.js`, evitando misturar versões.

O servidor local adiciona COOP/COEP. Esses cabeçalhos permitem isolamento entre origens; a versão atual usa um único thread em WASM e não depende de multithreading. Todos os arquivos e fontes são servidos na mesma origem.

## Modelo e contrato de imagem

- Fonte: `assets/modelos/candidato_T5_6_20261026`, com 13 classes na ordem original.
- INT8 primeiro: 4.003.624 bytes. FP32: 13.531.184 bytes, baixado somente como alternativa quando a execução INT8 é incompatível; a troca é identificada na interface.
- O runtime WASM também é baixado, aproximadamente 11 MB, além do modelo, dos scripts e das fontes. O tamanho do modelo sozinho não representa o download inicial nem o consumo de RAM.
- Entrada RGB `[1,224,224,3]`, normalizada para `[0,1]`. EXIF aplicado uma vez, redimensionamento proporcional bicúbico com antialiasing e arredondamento compatível com Pillow 12.2, preenchimento `(128,128,128)`, sem recorte.
- Quantização e desquantização usam os parâmetros lidos do TFLite, sem repetir a conversão do backbone já incorporada ao grafo.
- JPEG, PNG e WebP de até 10 MiB e 40 megapixels. Imagens com transparência são recusadas para não alterar silenciosamente o contrato RGB.
- Web Worker clássico separado mantém o cálculo fora da interface. O formato clássico é necessário porque o carregador Emscripten do LiteRT usa `importScripts`.
- O INT8 usa CPU/WASM. Para o FP32, WebGPU é tentado quando disponível, com alternativa WASM. Não é usado WebNN experimental.

### Especialização para o navegador

Os arquivos originais têm formas alocadas de batch 1 e assinaturas com batch dinâmico `-1`. O LiteRT.js 2.6 exige tipos de entrada concretos para executar esse grafo. `scripts/prepare-assets.mjs` gera cópias `*_web.tflite`, substituindo somente dimensões dinâmicas nas assinaturas pelas formas já alocadas. Pesos, operadores, quantização e os arquivos originais são preservados. O manifesto web registra os hashes de origem e das cópias e o navegador verifica o hash antes de carregar.

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

Os testes unitários comparam os bytes do processamento com seis referências sintéticas geradas em Python. Os testes de navegador executam o INT8 real, comparam os 13 scores com Python, verificam EXIF, reutilização do modelo, ausência de uploads, navegação, arquivos inválidos e recuperação após falha no download. A tolerância de comparação entre runtimes é de 2/256 por score.

Para regenerar as referências, em ambiente Python separado com TensorFlow 2.21.0, Pillow 12.2.0 e NumPy 2.4.4:

```powershell
python scripts/generate-reference.py
```

Execute `npm.cmd run assets` antes. O gerador também exige resultados idênticos entre o modelo original e a cópia web na execução Python. As imagens de teste são padrões sintéticos, não fotos de usuários.

Validação inicial: Chromium automatizado no Windows; layout desktop e viewport móvel de 390 px. Compatibilidade e desempenho em aparelho Android físico, Safari e Firefox ainda não foram certificados. As medições da tela são da sessão atual e não representam benchmark do celular-alvo.

Ao editar o worker ou o processamento, rode `npm.cmd run assets` novamente e recarregue a página; esses arquivos são compilados separadamente do HMR da interface.
