# T14.2 — Pipeline de treinamento

Autora: Karol · Revisor: Rui · Meta de entrega: a definir.
Documentação implementada em 17/11/2026; revisão técnica de Rui em 18/11/2026. O alcance das verificações está registrado ao final do guia.

## Escopo e fontes

Este guia descreve o código da `develop` e o candidato que originou o MVP 1.0.0. A [seleção final T8.3](../assets/data/selecao_T8_3/decisao.json) prevalece sobre o campo histórico de embarque do manifesto T5.6. Continue com [avaliação e conversão](T14_3_Avaliacao_Conversao.md) e [integração web](T14_4_Arquitetura_Web.md).

As imagens originais não estão no Git. É necessário obter o acervo e manter os caminhos relativos registrados nos índices. Clonar o repositório permite inspecionar protocolos e resultados, mas não refazer treinamento sem essas imagens. Não há comando que baixe e prepare automaticamente um dataset arbitrário.

## Ambiente

Execute na raiz, com Python 3.12 (registro histórico: 3.12.15). Os comandos abaixo são PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-treino.txt
$env:KERAS_BACKEND = "tensorflow"
$env:PYTHONUTF8 = "1"
$python = ".\.venv\Scripts\python.exe"
$imagens = "C:\dados\agroapp"
```

[requirements-treino.txt](../requirements-treino.txt) fixa TensorFlow 2.21.0, Keras 3.15.1 e KerasHub 0.32.0; inclui [requirements.txt](../requirements.txt), com NumPy 2.4.4, Pillow 12.2.0, pandas 3.0.2, scikit-learn 1.9.1 e ferramentas de análise. O primeiro treinamento precisa de acesso ao preset pré-treinado do KerasHub ou de seu cache local. GPU não é requisito; não se promete tempo de execução. Treino e validação são carregados em RAM como RGB uint8 antes dos lotes; dimensione memória para o acervo, modelo e otimizador.

## Treinar novamente sobre o recorte do candidato

O candidato usa **3.156 imagens**, com 2.209 de treino, 474 de validação e 473 de teste. O índice e os pesos desse recorte devem ser informados explicitamente. O hash do índice está vinculado ao [manifesto do candidato](../assets/modelos/candidato_T5_6_20261026/manifesto.json).

```powershell
$indiceHistorico = "assets/data/treino_T5_2/indice_dataset.csv"
$pesosHistoricos = "assets/data/treino_T5_2/pesos_dataset.json"
& $python -m src.treinamento_t5_1 --config assets/modelos/candidato_T5_6_20261026/configuracao_treino.json --raiz-imagens $imagens --indice $indiceHistorico --pesos $pesosHistoricos --saida runs/reproducao_t14
```

A [preparação histórica T4.5](../src/pipeline_preparacao_t4_5.py) recompõe o manifesto anterior de **3.163 imagens**, incluindo sete imagens de outro acervo que foram excluídas do candidato. Seus arquivos são os defaults do CLI de treino. Para reexecutar essa preparação, obtenha também as sete imagens anteriores e use um checkout dedicado, pois o comando escreve em `assets/data/pipeline_T4_5/`.

```powershell
& $python -m src.pipeline_preparacao_t4_5 --raiz-imagens $imagens --semente 42
```

Esse comando compara o particionamento com os arquivos aprovados em T4.2, confere a referência T4.1 e gera `indice_pipeline.csv`, `pesos_classes.json`, `parametros.json` e `auditoria.json`. Sem `--raiz-imagens`, a verificação se limita aos índices. Para treinar o candidato com suas 3.156 imagens, use os caminhos explícitos do primeiro bloco.

O contrato contém IDs, caminho relativo, classe, partição, grupo, hash original e semente de augmentation. Os pesos seguem `N / (K * n_c)`, calculados apenas no treino. O preprocessing aplica EXIF uma vez, ignora ICC, exige imagem opaca, converte para RGB, redimensiona proporcionalmente com bicúbico/antialiasing, completa com cinza 128 sem recortar e normaliza para `[0,1]`. Consulte [preprocessamento.py](../src/preprocessamento.py). Augmentation, quando habilitado, ocorre apenas no treino; validação e teste ficam sem aumento. O treinamento T5.1 carrega somente treino e validação.

## Arquitetura e configuração selecionadas

Fonte exata: [configuracao_treino.json](../assets/modelos/candidato_T5_6_20261026/configuracao_treino.json), [backbones.py](../src/backbones.py) e [treinamento_t5_1.py](../src/treinamento_t5_1.py).

| Parâmetro | Candidato selecionado |
| --- | --- |
| Backbone | EfficientNet-Lite0, entrada 224 × 224 × 3 |
| Inicialização | KerasHub, pesos timm `efficientnet_lite0.ra_in1k`, ImageNet-1k |
| Cabeça | GlobalAveragePooling2D → Dropout 0,2 → Dense softmax, 13 classes |
| Entrada pública | float32 `[batch,224,224,3]`, RGB em `[0,1]` |
| Conversão interna | Normalização por canal com média/desvio ImageNet, incorporada ao grafo |
| Semente / determinismo | 42 / habilitado |
| Otimizador / loss | Adam / sparse categorical crossentropy |
| Cabeça | batch 64, learning rate 0,01, até 30 épocas |
| Fine-tuning | 2 últimos blocos, learning rate 0,001, até 20 épocas |
| Early stopping | `val_f1_macro`, maximizar, paciência 5, restaurar melhores pesos |
| Balanceamento / augmentation | class weights habilitados / augmentation desabilitado |

A base começa congelada. No fine-tuning, BatchNormalization permanece congelada e a base é chamada com `training=False`. A melhor época é comparada entre as fases; não é obrigatório executar as 50 épocas. Não repetir a normalização ImageNet fora do modelo.

## Treinamento com novos dados

1. Versione um novo inventário com IDs únicos, rótulos revisados, origem, caminhos e SHA-256 dos originais. Preserve a ordem das 13 classes de [classes.json](../assets/modelos/candidato_T5_6_20261026/classes.json) se mantiver o contrato do MVP.
2. Revise cópias transformadas e agrupe imagens da mesma observação, planta ou captura antes da separação. A [revisão da independência](../assets/data/independencia_T10_1/README.md) registra uma duplicata entre treino e teste que passou pelas verificações de hash e grupo anteriores. Congele uma nova versão com os vínculos registrados e preserve a evidência de reserva do novo teste antes da avaliação. O teste histórico permanece exploratório.
3. Produza um novo índice no esquema de [indice_pipeline.csv](../assets/data/pipeline_T4_5/indice_pipeline.csv), incluindo `image_id`, `caminho_relativo`, `indice_modelo`, `nome_classe_modelo`, `particao`, `grupo_particao`, `sha256_original` e `semente_augmentation`. Gere pesos no esquema de [pesos_classes.json](../assets/data/pipeline_T4_5/pesos_classes.json), recalculados somente no treino. Os leitores estão em [dados_treino.py](../src/dados_treino.py).
4. Copie a configuração selecionada para uma nova pasta, registre decisões e execute com caminhos explícitos:

```powershell
& $python -m src.treinamento_t5_1 --config runs/novo_dataset/config.json --raiz-imagens $imagens --indice runs/novo_dataset/indice_pipeline.csv --pesos runs/novo_dataset/pesos_classes.json --saida runs/novo_treino
```

A criação desse inventário/índice exige adaptação e revisão: o CLI T4.5 verifica fontes históricas fixas e não importa novas imagens automaticamente. Não troque apenas a pasta de fotos mantendo índices e hashes antigos. Alterar classes exige revisar cabeça, catálogo, política e frontend. Os scripts de seleção/conversão também conferem a proveniência T5.6; um novo treino não vira o pacote oficial sem atualizar esses contratos.

## Saídas e resultados esperados

Cada execução cria uma subpasta `<data-hora>_<backbone>_s42/` dentro do caminho informado em `--saida`. No exemplo, será `runs/reproducao_t14/<data-hora>_efficientnet_lite0_s42/`, contendo `melhor_modelo.keras`, `config_usada.json`, `ambiente.json` (versões, dispositivos, commit e hashes), `historico.csv` e `metricas_validacao.json` (F1 macro e métricas por classe). Guarde a pasta completa, pois a avaliação depende desses metadados e do checkpoint.

O [registro T5.5](../assets/data/experimentos_T5_5/experimentos.md) registra F1 macro de validação 0,781106 para o EfficientNet-Lite0 selecionado. É referência histórica, sem garantia de obter o mesmo valor com novos dados, hardware ou bibliotecas. Semente e determinismo não garantem checkpoint idêntico entre plataformas. Espere arquivos coerentes, métricas finitas e rastreabilidade; avalie mudanças por classe e não apenas a média. A avaliação final está no próximo guia.

## Alcance da revisão

Foram conferidos os argumentos dos CLIs, a configuração do candidato, o vínculo do índice e os pesos de treino. Os comandos de treinamento são procedimentos documentados para execução posterior. A revisão técnica não incluiu uma nova rodada de treinamento. O ensaio por participante externo será registrado na validação do guia de retreinamento.
