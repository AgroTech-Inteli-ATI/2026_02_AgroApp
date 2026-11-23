# T11.3 — Avaliação do limiar de confiança e casos inadequados

Autor: Lucas · Revisor: Glauco · Meta de entrega: a definir

Relatório gerado por [`limiar_t11_3.py`](../src/limiar_t11_3.py) a partir das predições da [T11.1](Avaliacao_Final_T11_1.md) e das inferências feitas no próprio aplicativo (LiteRT.js no Chromium) com o modelo do build; artefatos em [`assets/data/limiar_T11_3`](../assets/data/limiar_T11_3/resultados.json).

> **Classificação: exploratória.** O teste histórico já foi consultado no desenvolvimento e não é independente ([T10.1](../assets/data/independencia_T10_1/README.md)). Esta avaliação **não recalibra** o limiar e **não apresenta nenhum score como probabilidade de acerto**: o valor mostrado é o softmax do modelo, sem calibração.

## Resumo

- Regra testada: top-1 **≥ 0,65** (igualdade aceita) mostra as três hipóteses; abaixo disso, resultado inconclusivo, sem indicar classe.
- Float16 no teste histórico (473 imagens): 441 aceitas (93,2%), com acerto de 88,2% entre elas; **52 erros foram aceitos** e 12 acertos ficaram inconclusivos.
- **Erros com score alto:** 27 dos 72 erros têm score ≥ 0,90; a classe real aparece entre as três hipóteses em 38 dos 52 erros aceitos.
- **O score não é probabilidade calibrada:** o erro de calibração esperado (ECE) do Float16 no teste é 0,094, e 7 das 8 faixas de score têm score médio acima do acerto observado.
- **Fora do recorte:** das 77 imagens sem o inseto ou sem relação com as 13 classes, o app **aceitou e indicou uma classe em 24** (31,2%) com o Float16. O limiar não funciona como detector de imagem fora do escopo.
- **Interface:** em 397 imagens, a tela mostrou as hipóteses exatamente quando o score atingiu o limiar (nenhuma divergência).

## Cenários do conjunto histórico

Cada imagem cai em um de quatro cenários, conforme o top-1 esteja certo e atinja ou não o limiar. Float16 e INT8, teste histórico e validação (a validação participou da seleção do checkpoint e do limiar; é otimista).

| Modelo | Conjunto | Imagens | Acerto aceito | Acerto inconclusivo | Erro aceito | Erro inconclusivo | Cobertura | Acerto entre aceitas |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Float16 | teste histórico | 473 | 389 | 12 | 52 | 20 | 93,2% | 88,2% |
| Float16 | validação | 474 | 390 | 17 | 40 | 27 | 90,7% | 90,7% |
| INT8 | teste histórico | 473 | 385 | 14 | 55 | 19 | 93,0% | 87,5% |
| INT8 | validação | 474 | 391 | 16 | 42 | 25 | 91,4% | 90,3% |

- **Acerto aceito:** o caso desejado; o usuário vê a classe certa entre as hipóteses.
- **Acerto inconclusivo:** o modelo acertou, mas o score ficou abaixo do limiar; o usuário recebe a mensagem de resultado inconclusivo (custo de cobertura).
- **Erro aceito:** o caso mais sensível; o app mostra uma classe errada como hipótese principal, e o score pode ser alto.
- **Erro inconclusivo:** o limiar evitou mostrar uma classe errada. No Float16 do teste, 62,5% das imagens inconclusivas eram erros.

### Quando o app mostra uma classe, quanto ela acerta (Float16, teste)

| Classe mostrada como principal | Vezes mostrada | Acerto quando mostrada | Cobertura da classe real | Recall no limiar |
| --- | ---: | ---: | ---: | ---: |
| 0 · Vaquinha | 155 | 94,2% | 98,1% | 93,0% |
| 1 · Cigarrinha-do-milho | 25 | 100,0% | 93,1% | 86,2% |
| 2 · Percevejo-barriga-verde | 38 | 78,9% | 83,3% | 71,4% |
| 3 · Lagarta-do-cartucho | 63 | 85,7% | 93,4% | 88,5% |
| 4 · Percevejo-marrom | 5 | 100,0% | 100,0% | 50,0% |
| 5 · Percevejo-verde | 9 | 55,6% | 71,4% | 35,7% |
| 6 · Percevejo-asa-preta | 4 | 100,0% | 81,8% | 36,4% |
| 7 · Percevejo-do-milho | 12 | 75,0% | 91,7% | 75,0% |
| 8 · Lagarta-falsa-medideira | 4 | 100,0% | 91,7% | 33,3% |
| 9 · Lagarta-da-soja | 6 | 83,3% | 100,0% | 83,3% |
| 10 · Lagarta-das-vagens | 23 | 69,6% | 87,5% | 66,7% |
| 11 · Astylus variegatus | 71 | 88,7% | 93,0% | 88,7% |
| 12 · Cigarrinha-das-pastagens | 26 | 88,5% | 100,0% | 95,8% |

O acerto quando a classe é mostrada varia bastante entre classes com o mesmo limiar: um limiar único não dá a mesma garantia a todas.

## Erros com score elevado

No Float16, teste histórico, 27 erros têm score ≥ 0,90 e seriam apresentados com aparência de alta confiança. Faixas de score do top-1:

| Faixa de score | Imagens | Acertos | Erros | Acerto | Score médio |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,00 a 0,50 | 15 | 6 | 9 | 40,0% | 0,42 |
| 0,50 a 0,65 | 17 | 6 | 11 | 35,3% | 0,58 |
| 0,65 a 0,80 | 31 | 16 | 15 | 51,6% | 0,74 |
| 0,80 a 0,90 | 25 | 15 | 10 | 60,0% | 0,85 |
| 0,90 a 0,95 | 19 | 14 | 5 | 73,7% | 0,93 |
| 0,95 a 0,99 | 58 | 43 | 15 | 74,1% | 0,98 |
| 0,99 a 1,00 | 308 | 301 | 7 | 97,7% | 1,00 |

Erros com score ≥ 0,90 (Float16, teste):

| Imagem | Real → Prevista | Score | Classe real entre as 3 hipóteses |
| --- | --- | ---: | --- |
| IMG_03197 | Percevejo-verde → Vaquinha | 1,000 | sim |
| IMG_03447 | Lagarta-das-vagens → Lagarta-do-cartucho | 0,999 | sim |
| IMG_03091 | Percevejo-asa-preta → Vaquinha | 0,999 | sim |
| IMG_03037 | Lagarta-falsa-medideira → Lagarta-das-vagens | 0,998 | não |
| IMG_02973 | Lagarta-falsa-medideira → Lagarta-do-cartucho | 0,998 | sim |
| IMG_03089 | Percevejo-asa-preta → Percevejo-verde | 0,995 | sim |
| IMG_03384 | Lagarta-das-vagens → Lagarta-do-cartucho | 0,995 | sim |
| IMG_01012 | Vaquinha → Astylus variegatus | 0,988 | sim |
| IMG_02972 | Lagarta-falsa-medideira → Lagarta-do-cartucho | 0,988 | sim |
| IMG_00142 | Astylus variegatus → Vaquinha | 0,985 | sim |
| IMG_03198 | Percevejo-verde → Vaquinha | 0,981 | sim |
| IMG_03086 | Percevejo-asa-preta → Percevejo-verde | 0,978 | não |
| IMG_03187 | Percevejo-marrom → Percevejo-barriga-verde | 0,977 | sim |
| IMG_03088 | Percevejo-asa-preta → Percevejo-verde | 0,977 | sim |
| IMG_03156 | Percevejo-marrom → Astylus variegatus | 0,974 | não |
| IMG_02978 | Lagarta-falsa-medideira → Lagarta-do-cartucho | 0,974 | sim |
| IMG_03427 | Lagarta-das-vagens → Lagarta-do-cartucho | 0,973 | sim |
| IMG_00529 | Cigarrinha-do-milho → Vaquinha | 0,971 | sim |
| IMG_03254 | Percevejo-verde → Percevejo-barriga-verde | 0,966 | não |
| IMG_02123 | Percevejo-barriga-verde → Lagarta-do-cartucho | 0,966 | sim |
| IMG_03154 | Percevejo-marrom → Percevejo-do-milho | 0,965 | não |
| IMG_00909 | Percevejo-do-milho → Cigarrinha-das-pastagens | 0,958 | não |
| IMG_03160 | Percevejo-marrom → Percevejo-barriga-verde | 0,949 | sim |
| IMG_03036 | Lagarta-falsa-medideira → Lagarta-das-vagens | 0,949 | não |
| IMG_01175 | Vaquinha → Astylus variegatus | 0,931 | sim |
| IMG_01855 | Vaquinha → Lagarta-das-vagens | 0,927 | sim |
| IMG_03258 | Percevejo-verde → Percevejo-barriga-verde | 0,909 | não |

## O score não é probabilidade de acerto

Se o score fosse uma probabilidade calibrada, as imagens com score médio próximo de 0,9 acertariam cerca de 90% das vezes. A tabela compara o score médio de cada faixa com o acerto observado (Float16, teste histórico):

| Faixa | Imagens | Score médio | Acerto observado | Diferença |
| --- | ---: | ---: | ---: | ---: |
| 0,20 a 0,30 | 1 | 0,28 | 0,0% | -0,28 |
| 0,30 a 0,40 | 4 | 0,36 | 75,0% | 0,39 |
| 0,40 a 0,50 | 10 | 0,46 | 30,0% | -0,16 |
| 0,50 a 0,60 | 12 | 0,56 | 25,0% | -0,31 |
| 0,60 a 0,70 | 11 | 0,66 | 54,5% | -0,11 |
| 0,70 a 0,80 | 25 | 0,75 | 52,0% | -0,23 |
| 0,80 a 0,90 | 25 | 0,85 | 60,0% | -0,25 |
| 0,90 a 1,00 | 385 | 0,99 | 93,0% | -0,06 |

ECE: 0,094 no teste e 0,077 na validação (Float16). O texto do aplicativo e os documentos devem chamar o valor de *score do modelo*, nunca de chance ou probabilidade de acerto; a política T6.5 já determina isso.

## Sensibilidade ao limiar

Não é uma recalibração: o teste histórico já foi consultado. Serve para mostrar o que o limiar de 0,65 troca entre cobertura e erros aceitos (Float16).

| Limiar | Teste: cobertura | Teste: acerto entre aceitas | Teste: erros aceitos | Validação: cobertura | Validação: acerto entre aceitas | Validação: erros aceitos |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0,50 | 96,8% | 86,2% | 63 | 96,6% | 87,1% | 59 |
| 0,55 | 95,6% | 87,2% | 58 | 94,5% | 88,4% | 52 |
| 0,60 | 94,3% | 87,9% | 54 | 93,0% | 89,3% | 47 |
| **0,65** | 93,2% | 88,2% | 52 | 90,7% | 90,7% | 40 |
| 0,70 | 92,0% | 88,7% | 49 | 88,6% | 91,4% | 36 |
| 0,75 | 90,1% | 89,9% | 43 | 87,6% | 92,0% | 33 |
| 0,80 | 86,7% | 91,0% | 37 | 85,4% | 93,3% | 27 |
| 0,85 | 83,9% | 92,7% | 29 | 84,6% | 93,5% | 26 |
| 0,90 | 81,4% | 93,0% | 27 | 82,1% | 94,6% | 21 |
| 0,95 | 77,4% | 94,0% | 22 | 76,8% | 95,9% | 15 |

Subir o limiar reduz erros aceitos, mas também aceita menos fotos; mesmo em 0,95 ainda há erros aceitos. A meta de 0,90 de acerto entre aceitas foi definida na validação (T6.5).

## Imagens fora do recorte e inadequadas (inferência no aplicativo)

As imagens foram enviadas ao aplicativo real (Playwright, Chromium 156.0.8078.4, LiteRT.js 2.6.0), com o modelo do build e a política de 0,65; o resultado foi lido da saída do worker e da tela. O manifesto (`manifesto.json`) lista cada imagem, o cenário, a origem e o hash do arquivo.

### Float16

| Cenário | Imagens | Aceitas (app indica classe) | Score mediano | Score máximo | Classe mais mostrada |
| --- | ---: | ---: | ---: | ---: | --- |
| Controles sintéticos sem inseto | 17 | 3 (17,6%) | 0,39 | 0,81 | Vaquinha (3) |
| Fotos reais sem o inseto (recorte do fundo) | 60 | 21 (35,0%) | 0,51 | 0,99 | Vaquinha (9) |
| Foto original (referência dos pares) | 40 | 39 (97,5%) | 1,00 | 1,00 | Vaquinha (17) |
| Desfoque forte | 40 | 14 (35,0%) | 0,59 | 1,00 | Vaquinha (8) |
| Foto escura | 40 | 33 (82,5%) | 0,99 | 1,00 | Vaquinha (14) |
| Foto superexposta | 40 | 34 (85,0%) | 0,99 | 1,00 | Vaquinha (16) |
| Escala de cinza | 40 | 29 (72,5%) | 0,89 | 1,00 | Lagarta-do-cartucho (9) |
| Ruído forte | 40 | 37 (92,5%) | 0,97 | 1,00 | Vaquinha (15) |
| Compressão JPEG q=10 | 40 | 37 (92,5%) | 1,00 | 1,00 | Vaquinha (17) |
| Sujeito pequeno e distante | 40 | 30 (75,0%) | 0,84 | 1,00 | Vaquinha (12) |

Imagens fora do recorte que o Float16 **aceitou** (as 10 de maior score, de 24):

| Imagem | Cenário | Classe indicada | Score |
| --- | --- | --- | ---: |
| fundo_IMG_01779 | Fotos reais sem o inseto (recorte do fundo) | Vaquinha | 0,989 |
| fundo_IMG_00498 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,984 |
| fundo_IMG_01794 | Fotos reais sem o inseto (recorte do fundo) | Vaquinha | 0,982 |
| fundo_IMG_02701 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,981 |
| fundo_IMG_02236 | Fotos reais sem o inseto (recorte do fundo) | Percevejo-barriga-verde | 0,967 |
| fundo_IMG_00635 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,960 |
| fundo_IMG_01580 | Fotos reais sem o inseto (recorte do fundo) | Vaquinha | 0,860 |
| fundo_IMG_00529 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,848 |
| fundo_IMG_01855 | Fotos reais sem o inseto (recorte do fundo) | Lagarta-das-vagens | 0,839 |
| fundo_IMG_01641 | Fotos reais sem o inseto (recorte do fundo) | Vaquinha | 0,826 |

**Mesma foto, degradada** (comparação com a foto original, Float16):

| Degradação | Pares | Decisão mudou | Aceito → inconclusivo | Inconclusivo → aceito | Classe mudou | Erros aceitos | Erros aceitos novos | Queda média do score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Desfoque forte | 40 | 27 | 26 | 1 | 16 | 5 | 5 | 0,34 |
| Foto escura | 40 | 8 | 7 | 1 | 6 | 2 | 2 | 0,09 |
| Foto superexposta | 40 | 7 | 6 | 1 | 7 | 2 | 1 | 0,06 |
| Escala de cinza | 40 | 12 | 11 | 1 | 12 | 8 | 6 | 0,15 |
| Ruído forte | 40 | 4 | 3 | 1 | 7 | 3 | 2 | 0,06 |
| Compressão JPEG q=10 | 40 | 4 | 3 | 1 | 3 | 4 | 1 | 0,02 |
| Sujeito pequeno e distante | 40 | 9 | 9 | 0 | 21 | 13 | 11 | 0,17 |

As fotos originais dos pares: 39/40 aceitas, com 89,7% de acerto entre elas.

**Consistência da interface:** 397 imagens; a tela mostrou as hipóteses quando e somente quando o top-1 atingiu o limiar (0 divergências).

### INT8

| Cenário | Imagens | Aceitas (app indica classe) | Score mediano | Score máximo | Classe mais mostrada |
| --- | ---: | ---: | ---: | ---: | --- |
| Controles sintéticos sem inseto | 17 | 3 (17,6%) | 0,41 | 0,91 | Vaquinha (3) |
| Fotos reais sem o inseto (recorte do fundo) | 60 | 18 (30,0%) | 0,49 | 0,99 | Vaquinha (8) |
| Foto original (referência dos pares) | 40 | 37 (92,5%) | 1,00 | 1,00 | Vaquinha (16) |
| Desfoque forte | 40 | 14 (35,0%) | 0,49 | 1,00 | Lagarta-das-vagens (5) |
| Foto escura | 40 | 36 (90,0%) | 0,97 | 1,00 | Vaquinha (13) |
| Foto superexposta | 40 | 37 (92,5%) | 0,99 | 1,00 | Vaquinha (17) |
| Escala de cinza | 40 | 32 (80,0%) | 0,89 | 1,00 | Lagarta-do-cartucho (9) |
| Ruído forte | 40 | 35 (87,5%) | 0,96 | 1,00 | Vaquinha (13) |
| Compressão JPEG q=10 | 40 | 38 (95,0%) | 0,99 | 1,00 | Vaquinha (17) |
| Sujeito pequeno e distante | 40 | 30 (75,0%) | 0,81 | 1,00 | Vaquinha (12) |

Imagens fora do recorte que o INT8 **aceitou** (as 10 de maior score, de 21):

| Imagem | Cenário | Classe indicada | Score |
| --- | --- | --- | ---: |
| fundo_IMG_00498 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,988 |
| fundo_IMG_01779 | Fotos reais sem o inseto (recorte do fundo) | Vaquinha | 0,988 |
| fundo_IMG_02701 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,977 |
| fundo_IMG_00635 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,965 |
| fundo_IMG_01794 | Fotos reais sem o inseto (recorte do fundo) | Vaquinha | 0,961 |
| fundo_IMG_02236 | Fotos reais sem o inseto (recorte do fundo) | Percevejo-barriga-verde | 0,930 |
| sintetico_circulos_concentricos | Controles sintéticos sem inseto | Vaquinha | 0,910 |
| fundo_IMG_01855 | Fotos reais sem o inseto (recorte do fundo) | Lagarta-das-vagens | 0,895 |
| fundo_IMG_01852 | Fotos reais sem o inseto (recorte do fundo) | Percevejo-barriga-verde | 0,852 |
| fundo_IMG_02271 | Fotos reais sem o inseto (recorte do fundo) | Cigarrinha-do-milho | 0,840 |

**Mesma foto, degradada** (comparação com a foto original, INT8):

| Degradação | Pares | Decisão mudou | Aceito → inconclusivo | Inconclusivo → aceito | Classe mudou | Erros aceitos | Erros aceitos novos | Queda média do score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Desfoque forte | 40 | 25 | 24 | 1 | 20 | 6 | 6 | 0,40 |
| Foto escura | 40 | 7 | 4 | 3 | 6 | 6 | 5 | 0,08 |
| Foto superexposta | 40 | 4 | 2 | 2 | 4 | 4 | 2 | 0,05 |
| Escala de cinza | 40 | 11 | 8 | 3 | 13 | 11 | 9 | 0,15 |
| Ruído forte | 40 | 8 | 5 | 3 | 7 | 3 | 2 | 0,07 |
| Compressão JPEG q=10 | 40 | 5 | 2 | 3 | 0 | 4 | 1 | 0,01 |
| Sujeito pequeno e distante | 40 | 9 | 8 | 1 | 20 | 13 | 11 | 0,17 |

As fotos originais dos pares: 37/40 aceitas, com 89,2% de acerto entre elas.

**Consistência da interface:** 397 imagens; a tela mostrou as hipóteses quando e somente quando o top-1 atingiu o limiar (0 divergências).

## Limitações das previsões

1. **Sem conjunto independente.** O teste histórico já foi consultado; os números descrevem o build nesse recorte e não estimam o desempenho em fotos novas de campo.
2. **O limiar não detecta imagem fora do escopo.** O modelo escolhe sempre uma das 13 classes; fotos sem inseto, de outras pragas, de doenças ou de plantas sadias podem receber score alto. As medições acima usam controles sintéticos e recortes de fundo, não doenças, outras culturas ou insetos de outras espécies; para esses casos reais, incluir fotos da equipe (opção `--pasta-extras`) e repetir a avaliação.
3. **Score ≠ probabilidade.** É um softmax não calibrado (T6.5); o limiar de 0,65 foi escolhido na validação em Keras FP32 e não foi recalibrado para o Float16 nem para o INT8.
4. **Classes pequenas.** Suportes de 6 a 157 imagens tornam instáveis os percentuais por classe; não há intervalo de confiança por classe.
5. **Fotos do AgroInsect e do iNaturalist.** As degradações e os recortes usam fotos do AgroInsect (com caixas YOLO); a origem iNaturalist não foi reprocessada no navegador. Os recortes de fundo não foram revisados um a um: são regiões fora das caixas anotadas, e um recorte pode conter um inseto pequeno não anotado (por exemplo, há uma formiga minúscula em `fundo_IMG_01779`). A degradação sintética não substitui fotos reais com problemas de captura no campo.
6. **Runtime.** O Chromium desktop com LiteRT.js CPU/WASM representa o app, mas não WebGPU, Safari, Firefox ou aparelhos físicos.

## Reprodução

```powershell
python -m src.limiar_t11_3 preparar --raiz-imagens "C:\caminho\agroapp - imagens" --saida-imagens "C:\tmp\t11_3" [--pasta-extras "C:\caminho\fotos"]
cd frontend
$env:T11_3_IMAGENS = "C:\tmp\t11_3"; npx playwright test tests/limiar-t11-3.spec.ts --project=chromium
cd ..
python -m src.limiar_t11_3 analisar
python -m src.limiar_t11_3 --verificar
python tests/validar_limiar_t11_3.py
```

O passo do navegador grava `assets/data/limiar_T11_3/inferencias_web.json` (scores das 13 classes e decisão exibida por imagem, para o Float16 e o INT8). A análise e os testes usam apenas arquivos versionados, sem modelo, imagens ou rede.
