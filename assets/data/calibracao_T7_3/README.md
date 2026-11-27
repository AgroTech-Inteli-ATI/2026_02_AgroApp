# Conjunto representativo — T7.3

200 imagens reais de treino, das 13 classes do candidato `candidato_T5_6_20261026`, selecionadas com semente 42 a partir do acervo já utilizado pela preparação de Dados. A seleção específica desta etapa foi produzida e documentada na T7.3, com autorização para usar esse acervo; não é uma entrega de calibração previamente revisada pela frente de Dados.

Cada classe tem 15 ou 16 imagens. Há 149 fotos de campo e 51 do AgroInsect, em 200 grupos distintos do índice. Nenhuma imagem de validação ou teste foi aberta para a seleção ou fornecida ao conversor. Os rótulos são usados apenas para conferir cobertura; o gerador fornece somente os tensores de imagem. Não há augmentation ou novo treinamento.

## Arquivos

- [manifesto_calibracao.csv](manifesto_calibracao.csv): IDs, caminhos relativos, hashes originais e de entrada float32, classes, grupos, origem e brilho.
- [conjunto.json](conjunto.json): protocolo de seleção, hashes de origem, cobertura das classes e faixas disponíveis/selecionadas.
- [revisao_iluminacao.json](revisao_iluminacao.json): inspeção visual assistida por IA de 49 imagens da seleção, com observações e condições aparentes de luz.

As fotos originais estão no acervo de Dados, nos caminhos relativos ao diretório que contém `dataset/`. Elas não foram duplicadas no Git.

## Brilho e iluminação

O brilho médio considera apenas o conteúdo RGB redimensionado, sem padding: `Y = média(0.2126 R + 0.7152 G + 0.0722 B)`, em [0, 1]. A amostra alterna faixas disponíveis por classe: abaixo de 0,30; de 0,30 a menos de 0,60; a partir de 0,60. Foram selecionadas 46 imagens de baixo brilho, 83 intermediárias e 71 de alto brilho.

Essa estatística é afetada pelo fundo e pela cor do inseto. Um fundo preto pode ter um sujeito muito iluminado. A revisão visual complementa a medida com 37 exemplos de extremos/pontos intermediários por classe/faixa e 12 exemplos adicionais de campo com baixo brilho. As 49 fotos cobrem todas as classes e incluem condições aparentes de sombra/baixa luz, luz suave, realces e iluminação mista. Quatro fotos foram marcadas como iluminação não inferível. As categorias podem coexistir e não são medições fotométricas nem anotações das 200 fotos.

Asa-preta e percevejo-do-milho não possuem imagens abaixo de 0,30 no treino segundo essa medida. A seleção registra essa limitação; não cria exemplos artificiais para preencher a faixa e não afirma cobertura de todas as condições de campo em cada classe.

## Uso e reprodução

Usar uma amostra de treino para calibração é compatível com a [documentação do Google sobre quantização pós-treinamento](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization), que descreve aproximadamente 100–500 exemplos. O objetivo é estimar faixas das ativações para quantização; não medir desempenho diagnóstico.

Com as dependências de `requirements-treino.txt` e as imagens originais:

```bash
python -m src.quantizacao_t7_3 converter --raiz-imagens /caminho/das/fontes --conjunto assets/data/calibracao_T7_3 --saida runs/reproducao_T7_3
```

O comando confere os hashes, as partições, as classes, os grupos, o preprocessamento e a revisão de iluminação antes da conversão. Uma proposta nova pode ser gerada em outra pasta:

```bash
python -m src.quantizacao_t7_3 preparar --raiz-imagens /caminho/das/fontes --saida runs/calibracao_T7_3 --total 200 --semente 42
```

Uma nova seleção precisa de revisão de iluminação correspondente aos seus IDs e hashes. Anotações não devem ser transportadas de outra seleção. As saídas existentes são preservadas.

A conversão executada está em [quantizacao_T7_3_candidato_T5_6_20261026](../../modelos/quantizacao_T7_3_candidato_T5_6_20261026/). Seu contrato registra os 200 IDs efetivamente consumidos. As inferências nas 49 fotos de calibração verificam execução; não substituem avaliação de perda de qualidade em partição própria nem a reconferência da política de confiança.
