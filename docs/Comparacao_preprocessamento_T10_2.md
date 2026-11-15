# Comparação Python × web após T10.2

**Resultado: correspondencia_com_XNNPACK_divergencia_INT8_sem_delegate.** O preprocessing e o efeito do delegate são quantificados separadamente abaixo. A configuração do runtime precisa acompanhar a versão do modelo nas validações.

Contrato: `T10.2-rgb8-sem-conversao-icc-v1`. Limiar: 0.65 (top-1 ≥ limiar).

Python 3.13.14, Pillow 12.2.0, NumPy 2.4.4, TensorFlow 2.21.0; CPU, 1 thread, sem delegates padrão.
Chromium 156.0.8078.4; LiteRT.js 2.6.0 CPU/WASM, 1 thread. Windows; execução desktop automatizada.

As fotos não formam uma amostra independente de acurácia. Variantes EXIF e brilho são casos de regressão derivados de fotos reais; os quatro casos de fronteira foram procurados deliberadamente nos modelos finais.

## Identidade dos modelos

- **Float16 T7.2**: `assets/modelos/comparacao_T7_2_candidato_T5_6_20261026/modelo_float16.tflite`; SHA-256 original `c9a26ce13806a2fa26bffbd8cfbdac83ff4c05ffff1009ca9483bb587a5a8fa2`; cópia web `9c18f0a2ca4a4e2eb0d84dd415046f0bd35385ede8c47e14463d3a0f134647ec`.
- **INT8 T7.3**: `assets/modelos/quantizacao_T7_3_candidato_T5_6_20261026/modelo_int8.tflite`; SHA-256 original `456caec54fae3c57684f9afd6842cae611a1f6cb6587b40b0c5bd8256aea1340`; cópia web `df2f5d4fe22b4d3f76c4b8f6dab6e0100231c83d606122999ed15ceb72c05978`.

Originais e cópias web produziram os mesmos 13 scores no Python em todos os casos. Classes, política, arquivos de entrada e código têm hashes no JSON anexo.

## Python sem delegates × web CPU/WASM

Esta configuração explicita o caminho de kernels sem delegates usado pelo helper de benchmark. O ensaio com delegates padrão, também usado pela avaliação T8.1 e pelo gerador de referência do frontend, aparece em seguida.

| Modelo | Casos | Δ pixel máx. (0–255) | Δ tensor máx. | Δ score máx. | MAE scores | Classes diferentes | Decisões diferentes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Float16 | 18 | 0 | 0 | 4.61935997e-06 | 1.85546319e-07 | 0 | 0 |
| INT8 | 18 | 0 | 0 | 0.11328125 | 0.00300480769 | 0 | 2 |

A tolerância de scores de 2/256 dos testes sintéticos históricos é usada como sinal de investigação, sem generalizá-la como garantia para fotos reais. Float16: 0 casos acima dessa referência; INT8: 6 casos acima dessa referência.

Controle negativo do pipeline antigo (conversão ICC automática):

- `display-p3.jpg`: Δ pixel máximo 9; MAE 0.572691. Após a correção, Δ=0 em todos os casos medidos.
- `photo-icc.png`: Δ pixel máximo 13; MAE 1.254883. Após a correção, Δ=0 em todos os casos medidos.

Diferenças de tensor usam a unidade de cada entrada: float32 em [0,1] para Float16, inteiros [-128,127] para INT8. Cada elemento normalizado/quantizado da web foi comparado exatamente com Python usando os mesmos RGB8 da web.

A decomposição executa Python com o tensor produzido na web: Δ preprocessing = Python(tensor web) − Python(tensor Python); Δ runtime = web(tensor web) − Python(tensor web). Os máximos não são somáveis, pois podem ocorrer em classes diferentes.

- Float16: Δ score máx. atribuído ao preprocessing 0; ao runtime 4.61935997e-06; web contra Python com delegate padrão 1.1920929e-07.
- INT8: Δ score máx. atribuído ao preprocessing 0; ao runtime 0.11328125; web contra Python com delegate padrão 0.

O ensaio adicional habilita o delegate padrão do TFLite Python (XNNPACK nesta execução), mantendo o tensor web. Isso testa a influência do caminho otimizado sem alterar os modelos. A proximidade dos resultados apoia uma hipótese sobre os kernels; não identifica sozinha o operador causador.

## Python com XNNPACK × web CPU/WASM

| Modelo | Δ score máx. | Classes diferentes | Decisões diferentes |
|---|---:|---:|---:|
| Float16 | 1.1920929e-07 | 0 | 0 |
| INT8 | 0 | 0 | 0 |

A referência Python com delegates padrão corresponde à configuração documentada em `src/avaliacao_pos_conversao_t8_1.py` (T8.1 usou 4 threads; este ensaio usa 1). A igualdade observada no INT8 com XNNPACK é evidência deste corpus, sem garantir que todos os operadores/builds de runtimes sejam intercambiáveis.

## Casos próximos ao limiar e divergências

A tabela abaixo usa Python **sem delegates**. Com XNNPACK no Python, não houve mudanças de classe/decisão em nenhum desses casos.

| Modelo / foto | Classe Python → web (índice) | Top-1 Python | Top-1 web | Decisão Python → web | Δ score máx. |
|---|---|---:|---:|---|---:|
| Float16 / exif-2.png | 5 → 5 | 0.633357346 | 0.633359075 | inconclusivo → inconclusivo | 1.7285347e-06 |
| Float16 / exif-6.png | 2 → 2 | 0.662924349 | 0.662928939 | aceito → aceito | 4.61935997e-06 |
| Float16 / boundary-float16-above.png | 0 → 0 | 0.650361896 | 0.650360882 | aceito → aceito | 1.29640102e-06 |
| Float16 / boundary-float16-below.png | 0 → 0 | 0.637463629 | 0.637463927 | inconclusivo → inconclusivo | 2.98023224e-07 |
| Float16 / boundary-int8-above.png | 0 → 0 | 0.825945675 | 0.825945318 | aceito → aceito | 5.51342964e-07 |
| Float16 / boundary-int8-below.png | 0 → 0 | 0.783723712 | 0.783722281 | aceito → aceito | 1.49011612e-06 |
| INT8 / display-p3.jpg | 12 → 12 | 0.664062500 | 0.664062500 | aceito → aceito | 0.00390625 |
| INT8 / srgb.jpg | 5 → 5 | 0.562500000 | 0.609375000 | inconclusivo → inconclusivo | 0.046875 |
| INT8 / exif-2.png | 5 → 5 | 0.628906250 | 0.628906250 | inconclusivo → inconclusivo | 0 |
| INT8 / exif-5.png | 2 → 2 | 0.953125000 | 0.964843750 | aceito → aceito | 0.01171875 |
| INT8 / exif-6.png | 2 → 2 | 0.585937500 | 0.667968750 | inconclusivo → aceito | 0.0859375 |
| INT8 / boundary-float16-above.png | 5 → 5 | 0.585937500 | 0.625000000 | inconclusivo → inconclusivo | 0.0390625 |
| INT8 / boundary-float16-below.png | 5 → 5 | 0.632812500 | 0.585937500 | inconclusivo → inconclusivo | 0.046875 |
| INT8 / boundary-int8-above.png | 0 → 0 | 0.761718750 | 0.648437500 | aceito → inconclusivo | 0.11328125 |
| INT8 / boundary-int8-below.png | 0 → 0 | 0.648437500 | 0.648437500 | inconclusivo → inconclusivo | 0 |

## Diferenças entre os modelos finais

Os índices e nomes completos das 13 classes estão no JSON anexo. Divergências entre Float16 e INT8 não são divergências Python × web:

| Foto | Float16 Python: classe / score / decisão | INT8 Python: classe / score / decisão |
|---|---|---|
| display-p3.jpg | 0 / 0.824377 / aceito | 12 / 0.664062 / aceito |
| srgb.jpg | 0 / 0.726886 / aceito | 5 / 0.562500 / inconclusivo |
| exif-6.png | 2 / 0.662924 / aceito | 2 / 0.585938 / inconclusivo |
| boundary-float16-above.png | 0 / 0.650362 / aceito | 5 / 0.585938 / inconclusivo |
| boundary-float16-below.png | 0 / 0.637464 / inconclusivo | 5 / 0.632812 / inconclusivo |
| boundary-int8-below.png | 0 / 0.783724 / aceito | 0 / 0.648438 / inconclusivo |

## Pontos para análise

- **Prioridade: padronizar a configuração de referência do INT8.** Com XNNPACK no Python os scores coincidiram com a web; sem delegates houve diferenças de até 0,11328125 e duas mudanças de decisão. Registrar delegate, threads e build junto ao hash do modelo. Caso seja necessário sustentar equivalência também sem delegates, reduzir os casos críticos e localizar o primeiro operador divergente. Os tensores de entrada são idênticos.
- Scores muito próximos de 0,65 podem mudar a decisão mesmo com a classe preservada e erro numérico pequeno. Não ampliar a tolerância do limiar nem arredondar scores para ocultar o efeito; qualquer margem de abstenção exige decisão de produto e validação/calibração própria.
- Float16 × INT8 no Python: 4 diferenças de classe e 4 diferenças de decisão. Na web: 4 e 4, respectivamente. São modelos numericamente distintos; não atribuir essas diferenças automaticamente ao preprocessing.
- A política de ignorar ICC preserva os valores usados no treino. Uma futura migração para conversão colorimétrica sRGB precisa versionar o contrato e reavaliar treino, calibração e métricas, sobretudo para Display P3.
- CPU/WASM foi medido aqui. WebGPU, Safari/Firefox e aparelho Android físico exigem execução equivalente antes de generalizar a correspondência.
- O limiar 0,65 foi calibrado anteriormente em Keras FP32; estes testes não demonstram calibração estatística do Float16 ou INT8.
- Os pares de fronteira foram obtidos por busca binária no brilho de uma foto. RGB8 e quantização tornam a função descontínua; o arquivo `boundary-int8-above.png` fica mais distante de 0,65 no Python e cruza para baixo na web. Não interpretar o par como estimativa da frequência de erro em fotos naturais.

## Reprodução e evidência

Na raiz, em ambiente com TensorFlow 2.21.0, Pillow 12.2.0 e NumPy 2.4.4:

```powershell
cd frontend
npm.cmd run assets
cd ..
python -m src.comparacao_preprocessamento_t10_2 referencia
cd frontend
$env:MODEL_COMPARISON='1'
npx.cmd playwright test tests/preprocessing.spec.ts --project=chromium
Remove-Item Env:MODEL_COMPARISON
cd ..
python -m src.comparacao_preprocessamento_t10_2 relatorio
```

[Dados completos](../assets/data/comparacao_preprocessamento_T10_2/comparacao.json): 13 scores de cada execução, hashes dos tensores, erros por etapa, decisões, margens e proveniência dos casos. Arquivos intermediários com os tensores completos ficam em `frontend/.work/model-comparison-*.json` e podem ser regenerados.
