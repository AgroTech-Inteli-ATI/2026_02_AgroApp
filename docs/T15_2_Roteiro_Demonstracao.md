# T15.2 — Roteiro e ensaio da demonstração do MVP

Responsável pela atividade: Karol · Ensaio em 22/11/2026

## Roteiro da apresentação

1. **Contexto, 1 min.** Apresentar o MVP web de apoio à identificação visual em soja e milho. Mostrar a câmera, a galeria e o indicador de modelo pronto. Explicar que a classificação roda no navegador e que o acesso offline exige a carga inicial.
2. **Acerto, 1 min.** Selecionar `IMG_02004.jpg`. Comparar a primeira hipótese com o rótulo histórico Vaquinha (*Diabrotica speciosa*). Mostrar o score e explicar que ele orienta a leitura da lista e carece de calibração como probabilidade de acerto.
3. **Hipóteses concorrentes, 1 min.** Selecionar `IMG_02637.jpg`. Mostrar Lagarta-do-cartucho e Lagarta-falsa-medideira, abrir a segunda hipótese e indicar quais orientações locais estão disponíveis. Explicar que a regra aceita o top 1 a partir de 0,65 e então mostra as três hipóteses em ordem.
4. **Inconclusivo, 1 min.** Selecionar `orientation.jpg`. Mostrar o aviso e a opção de tentar outra foto. Abaixo do limiar, a aplicação oculta hipóteses, scores e orientações específicas.
5. **Erro de classificação e recuperação, 2 min.** Mostrar a execução de contingência do mesmo `IMG_02004.jpg`: INT8 apontou Cigarrinha-das-pastagens acima do limiar, enquanto o rótulo histórico é Vaquinha. Explicar que a troca do modelo foi provocada para o ensaio e que a inferência INT8 é real. Em seguida, demonstrar arquivo inválido e retomar a análise com uma imagem válida.
6. **Resultados e decisão, 2 min.** Mostrar 473 imagens no teste histórico, 93,2% de cobertura e 88,21% de acurácia entre aceitas no Float16. Apresentar as limitações da avaliação, os resultados de latência web e as pendências de conteúdo, teste independente e aparelho. Registrar o retorno do parceiro na [ficha T15.3](T15_3_Entrega_Parceiro.md).

## Exemplos e resultado observado

Os arquivos `IMG_*` vêm da [revisão visual histórica T8.1](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/aprofundamento/relatorio_visual.md). Já foram consultados e ficam reservados para demonstração e regressão. `orientation.jpg` é uma fixture técnica do frontend. Uma futura avaliação independente deve usar novas imagens e grupos de captura, separados desses arquivos e do acervo histórico.

| Caso | Arquivo | Resultado observado |
| --- | --- | --- |
| Acerto, Float16 | [IMG_02004](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/aprofundamento/fotos/IMG_02004.jpg) | Vaquinha 81,88%, em acordo com o rótulo histórico. |
| Hipóteses concorrentes, Float16 | [IMG_02637](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/aprofundamento/fotos/IMG_02637.jpg) | Lagarta-do-cartucho 69,82%, Lagarta-falsa-medideira 29,71% e Cigarrinha-das-pastagens 0,39%. |
| Inconclusivo, Float16 | [orientation.jpg](../frontend/tests/fixtures/orientation.jpg) | Maior score interno 35,38%. A interface mostrou o aviso sem hipóteses. |
| Erro de classificação, INT8 | [IMG_02004](../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/aprofundamento/fotos/IMG_02004.jpg) | Cigarrinha-das-pastagens 71,88%, com Vaquinha em segundo lugar a 25,00%. A classificação aceita divergiu do rótulo histórico. |
| Erro de entrada | `quebrada.jpg`, arquivo gerado com bytes UTF-8 de `imagem inválida` | Aviso de foto inválida e nova análise concluída com a fixture `orientation.jpg`. |

Os registros [Float16](../assets/data/ensaio_T15_2/float16.json) e [INT8](../assets/data/ensaio_T15_2/int8.json) contêm os hashes das imagens e dos modelos e os scores brutos. O ensaio usou o build congelado [identificado na T15.3](T15_3_Entrega_Parceiro.md), com Chrome 158.0.8127.36 no Windows em uma janela de 390 × 900. A execução usou o seletor de arquivos e o worker real, em Float16 T7.2/WebGPU e INT8 T7.3/CPU WebAssembly. A câmera nativa e a sessão com o parceiro exigem evidências próprias.

Para reproduzir, sirva o pacote local e siga os quatro primeiros passos. Para o caso INT8 em ensaio automatizado, use o padrão de [analysis.spec.ts](../frontend/tests/analysis.spec.ts): crie uma sessão com service worker bloqueado e altere somente a resposta local do manifesto para que o contrato Float16 seja incompatível. Confira a indicação de contingência e use `IMG_02004.jpg`. Em apresentação sem automação, use o registro do ensaio INT8 e mostre explicitamente a condição de contingência. Scores podem variar por navegador e acelerador.
