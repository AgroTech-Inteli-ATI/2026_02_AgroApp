# Quantização INT8 — T7.3

Imagens reais consumidas: 200; 13 classes; somente treino, sem augmentation.
Tamanho: 4003624 bytes. SHA-256 INT8: `456caec54fae3c57684f9afd6842cae611a1f6cb6587b40b0c5bd8256aea1340`.

| Tensor | Shape | Tipo | Escala | Zero point |
| --- | --- | --- | --- | --- |
| entrada | [1, 224, 224, 3] | int8 | 0.003921568859368563 | -128 |
| saída | [1, 13] | int8 | 0.00390625 | -128 |

T4.1: EXIF, RGB, proporção e padding cinza; float32 [0,1] sem augmentation; a normalização do backbone já está no modelo
clip(round(x/escala)+zero_point,-128,127); usar escala e zero_point do tensor de entrada
(q-zero_point)*escala; valores não são probabilidades calibradas de acerto

Arquivo reaberto e executado em 49 fotos reais revisadas visualmente, cobrindo as 13 classes.
O grafo foi inspecionado e não contém tensores em ponto flutuante.
Conjunto, IDs, revisão de iluminação, hashes e diferenças por imagem constam no contrato JSON.
execução em imagens da própria calibração; não mede generalização, perda de F1, política de confiança ou latência no aparelho
