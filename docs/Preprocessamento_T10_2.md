# Contrato de preprocessing T10.2

Identificador: `T10.2-rgb8-sem-conversao-icc-v1`.
Implementações: [`preprocessamento.py`](../src/preprocessamento.py) e
[`preprocess.ts`](../frontend/src/lib/preprocess.ts). Treino, calibração e avaliação
Python continuam usando `preparar_imagem`; a inferência web usa `prepareImage`,
`normalize` e `quantize` no worker.

## Etapas e regras

| Etapa | Contrato |
|---|---|
| Decodificação | JPEG, PNG e WebP estáticos de fotografias RGB8 opacas. Pillow no Python; `createImageBitmap` no navegador, sem redimensionamento na decodificação. Cinza de 8 bits é expandido para RGB; PNG com paleta/alpha totalmente opaco pode ser convertido. |
| ICC e cor | **Preservar os códigos RGB8, ignorando o ICC e a correção de gama de metadados.** Não converter Display P3/Adobe RGB para sRGB. No Python, `convert('RGB')` sem `ImageCms`; na web, `colorSpaceConversion: 'none'`, `premultiplyAlpha: 'none'` e canvas/leitura explicitamente `srgb`. Esses códigos são tratados como sRGB para leitura e preview. |
| EXIF | Aplicar a orientação 1–8 exatamente uma vez antes de calcular as dimensões: rotações e espelhamentos. Python: `ImageOps.exif_transpose`; web: `imageOrientation: 'from-image'`. As dimensões devolvidas são as orientadas. |
| Transparência | Recusar qualquer pixel com alpha < 255, inclusive transparência de paleta. Não compor sobre branco/cinza nem descartar alpha silenciosamente. |
| Dimensões | Limite de 40 milhões de pixels. A interface web também limita o arquivo a 10 MiB. O limite de pixels é verificado após a abertura do cabeçalho no Python e após a criação do bitmap na web; não é uma garantia de limite de memória de decodificação. |
| Geometria | Escala = `224 / max(largura, altura)`. Cada dimensão = `max(1, round_even(dimensão * escala))`. Preservar proporção e ampliar imagens pequenas. |
| Reamostragem | Bicúbica separável Pillow 12.2, com antialiasing na redução e arredondamento/clipping para RGB8 entre os passes. A web reproduz os coeficientes de precisão 22 bits. Não usar o resize nativo do canvas. |
| Preenchimento | RGB8 `(128,128,128)`, quadro 224×224; deslocamento `floor((224 - dimensão) / 2)`. Sobra ímpar fica à direita/embaixo. Sem recorte. |
| Float | HWC RGB contíguo, `float32(pixel / 255)` em [0,1]; adicionar batch para `[1,224,224,3]`. O Float16 final tem entrada float32. Não repetir a normalização do backbone embutida no modelo. |
| INT8 | A partir do float32, `clip(round_even(x / scale + zero_point), -128,127)`. Escala e zero point vêm do modelo final. A equivalência é verificada para todos os 256 níveis RGB com a escala oficial T7.3. |
| Preview | Gerado dos próprios RGB8 224×224 usados no tensor, sem segunda decodificação ou conversão ICC. |

A política de ICC preserva o comportamento histórico de entrada do treino T4.1;
a correção principal elimina a conversão automática que existia só na web.
Isso estabelece correspondência numérica, sem prometer fidelidade colorimétrica
entre perfis distintos. Uma migração para sRGB colorimétrico exige outro contrato,
novas referências e reavaliação dos modelos.

O domínio certificado é o descrito acima. CMYK/YCCK, HDR, canais de 16 bits,
imagens animadas, perfis de cor inválidos e outros formatos não têm equivalência
certificada por esta entrega. Não extrapolar os resultados para essas entradas.

## Evidência e tolerâncias

Os arquivos em [`fixtures/preprocessing`](../frontend/tests/fixtures/preprocessing/)
contêm três fotografias originais intactas (sem perfil, sRGB e Display P3),
variantes lossless da foto sem perfil com/sem ICC, WebP, oito orientações EXIF
controladas e quatro casos de fronteira de confiança. EXIF e brilho das variantes
são metadados/transformações de teste sobre fotos reais, não registros originais
de câmera. `reference.json` registra proveniência, hashes, dimensões, perfil,
orientação e versões Python. `boundary-provenance.json` descreve o brilho e o
modelo usados na procura deliberada dos casos críticos.

As referências `.decoded.gz` e `.pixels.gz` armazenam RGB8 do Python, antes e
depois da geometria. PNG/WebP lossless exigem igualdade exata. Para os JPEGs
deste corpus, o teto de regressão é máximo 3/255 e MAE 0,35/255 por canal, em
ambas as etapas, para acomodar diferenças entre decodificadores. Esses limites
foram definidos para o corpus e não constituem garantia para qualquer JPEG.
**Na execução registrada, todos os 18 casos tiveram diferença zero.**

A normalização/quantização exige igualdade exata quando os RGB8 são iguais.
Os hashes float32 e dos tensores são conferidos diretamente contra as referências
Python. A comparação recusa referências desatualizadas de código, dependências,
política ou imagens, para não misturar evidências de execuções diferentes.
Os seis padrões sintéticos existentes continuam exigindo os hashes exatos do
Pillow, cobrindo ampliação, redução, dimensões estreitas e empate no arredondamento.
O controle negativo usa a conversão ICC automática antiga nas mesmas fotos e
demonstra que os testes detectam o defeito corrigido.

```powershell
# Na raiz; Pillow 12.2.0 / NumPy 2.4.4, sem TensorFlow para estes testes
python frontend/scripts/generate-preprocessing-reference.py
python tests/validar_preprocessamento.py
python tests/validar_preprocessamento_t10_2.py
cd frontend
npm.cmd test
npx.cmd playwright test tests/preprocessing.spec.ts --project=chromium
npm.cmd run build
```

O teste de inferência é opt-in e requer as referências Python dos modelos:
consulte o [relatório comparativo](Comparacao_preprocessamento_T10_2.md).
O teste de inferência exige correspondência com Python usando XNNPACK (scores
INT8 exatos neste corpus; tolerância 1e-5 para Float16). As diferenças contra
Python sem delegates são registradas explicitamente, incluindo mudanças de decisão.

## Compatibilidade com os resultados históricos

Fotos RGB8 opacas mantêm os pixels de entrada Python anteriores, inclusive
quando têm ICC. A recusa de transparência é uma restrição nova no Python, alinhada
ao navegador. Nenhum modelo ou resultado histórico foi retreinado/recalculado.
Os manifestos e hashes históricos de código continuam identificando as execuções
originais; não devem ser substituídos para simular uma nova calibração. Uma nova
execução de etapas que conferem proveniência deve gerar sua própria evidência.

Referências das APIs: [WHATWG, ImageBitmap](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html)
define a decodificação sem conversão com `none`; [Pillow, ImageCms](https://pillow.readthedocs.io/en/stable/reference/ImageCms.html)
documenta a transformação colorimétrica explícita, que este contrato não aplica.
