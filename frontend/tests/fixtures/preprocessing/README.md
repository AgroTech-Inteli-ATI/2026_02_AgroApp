# Fotografias de regressão T10.2

- `display-p3.jpg`: original `IMG_01540`, SHA-256 `d406d8d95579816063eec80212bc864d171196af73b798f759ef1f8fbfb30400`.
- `srgb.jpg`: original `IMG_01812`, SHA-256 `5afc5e8cc8ac06ee4e8cef5e8e2be7bdb94fc77ebed686f05bc74e3ef7fbef94`.
- Ambos são os originais auditados na [revisão T8.1](../../../../assets/data/avaliacao_T8_1/candidato_T5_6_20261026/aprofundamento/revisao_visual.csv), sem reencodificação.
- `no-profile.jpg`: cópia de `assets/revisão_imagens/IMG_0125.jpg`, sem ICC.
- `photo*`, `exif-*` e `transparent.png`: derivados da foto sem perfil. O ICC Display P3 é extraído do original `display-p3.jpg`. Os tags EXIF 1–8 foram adicionados deliberadamente.
- `boundary-*`: fotos derivadas de `IMG_0021.jpg`, com brilho e hashes documentados em `boundary-provenance.json`. Procuradas nos modelos finais para exercitar decisões de confiança; não são amostras de avaliação independentes.

`generate-preprocessing-reference.py` regenera as variantes e os RGB8 compactados
com gzip determinístico. Os JPEGs originais são entradas fixas. A busca de
fronteiras requer `python -m src.comparacao_preprocessamento_t10_2 referencia`.

Consulte [o contrato](../../../../docs/Preprocessamento_T10_2.md) para tolerâncias
e [o relatório](../../../../docs/Comparacao_preprocessamento_T10_2.md) para
divergências dos runtimes. O corpus é de regressão de preprocessing, sem alegação
de acurácia, calibração ou independência estatística.
