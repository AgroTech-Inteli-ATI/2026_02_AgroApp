"""Busca automática de hiperparâmetros sobre os backbones mais promissores.

Critério de aceite: taxa de aprendizado, tamanho de lote, política de
fine-tuning e estratégia de augmentation avaliados automaticamente sobre os
dois ou três backbones mais promissores.

Reaproveita o protocolo de treinamento e avaliação da T5.1
(src/treinamento_t5_1.py), variando só a configuração. É uma busca aleatória
com orçamento reduzido de épocas por rodada: o objetivo é ranquear
combinações rapidamente, não treinar até convergência. A melhor configuração
de cada backbone deve depois ser retreinada com o orçamento completo via

    python -m src.treinamento_t5_1 --config <config_da_busca> --raiz-imagens ...

Exemplo:

    python -m src.busca_hiperparametros_t5_3 \
        --raiz-imagens <pasta com dataset/, Milho/ e Soja/> \
        --backbones efficientnet_lite0 mobilenet_v3_large \
        --trials-por-backbone 6
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import argparse
import csv
import json

import numpy as np

from src.config_treino import validar_config
from src.dados_treino import INDICE_PADRAO, PESOS_PADRAO

# backbones e treinamento_t5_1 importam keras; adiados para dentro das funções
# que precisam deles, para que a amostragem e a montagem de config (sem
# TensorFlow) continuem testáveis isoladamente, como em dados_treino.py.

RAIZ = Path(__file__).resolve().parents[1]
SAIDA_BUSCA_PADRAO = RAIZ / "runs" / "busca_t5_4"

# Backbones mais promissores: EfficientNet-Lite0 é a recomendação principal do
# projeto (docs/Projeto.md §4), com MobileNetV3-Large como candidata de
# comparação. EfficientNet-Lite2, a terceira recomendação original, não tem
# preset/conversor no Keras 3 nem no KerasHub disponíveis (src/backbones.py),
# então MobileNetV2 entra como terceira candidata leve no lugar dela.
BACKBONES_PADRAO = ("efficientnet_lite0", "mobilenet_v3_large", "mobilenet_v2")

TAXAS_APRENDIZADO = (1e-2, 1e-3, 1e-4)
TAMANHOS_LOTE = (16, 32, 64)
AUGMENTATION = (True, False)

# Política de fine-tuning como fração dos blocos da base, não contagem fixa:
# backbones candidatos têm quantidades de blocos muito diferentes entre si.
# `divisor_taxa` deriva a taxa de aprendizado do fine-tuning a partir da taxa
# da cabeça sorteada no mesmo trial (sempre menor, como exige validar_config).
POLITICAS_FINE_TUNING = {
    "sem_fine_tuning": None,
    "raso": {"fracao_blocos": 0.15, "divisor_taxa": 10, "epocas_max": 8},
    "profundo": {"fracao_blocos": 0.5, "divisor_taxa": 100, "epocas_max": 12},
}


@dataclass(frozen=True)
class Trial:
    backbone: str
    taxa_aprendizado: float
    batch: int
    augmentation: bool
    politica_fine_tuning: str
    semente: int


def contar_blocos(nome_backbone: str) -> int:
    """Constrói a base sem pesos pré-treinados só para contar blocos (rápido, sem dados)."""
    from src import backbones

    backbone = backbones.obter(nome_backbone)
    if not backbone.suporta_fine_tuning:
        return 0
    base = backbone.construir_base(pesos_pre_treinados=False)
    return len(backbone.blocos(base))


def politicas_validas(nome_backbone: str) -> list[str]:
    from src import backbones

    if not backbones.obter(nome_backbone).suporta_fine_tuning:
        return ["sem_fine_tuning"]
    return list(POLITICAS_FINE_TUNING)


def amostrar_trials(
    backbone: str, quantidade: int, rng: np.random.Generator, semente_base: int
) -> list[Trial]:
    """Garante cada valor de cada dimensão e completa com combinações aleatórias."""
    politicas = politicas_validas(backbone)
    dimensoes = (TAXAS_APRENDIZADO, TAMANHOS_LOTE, AUGMENTATION, politicas)
    minimo = max(map(len, dimensoes))
    total = int(np.prod([len(valores) for valores in dimensoes]))
    if not minimo <= quantidade <= total:
        raise ValueError(
            f"trials_por_backbone deve estar entre {minimo} e {total} para {backbone}; "
            "cada valor de cada parâmetro precisa ser avaliado"
        )

    # Permutações independentes cobrem todas as opções já nos primeiros trials.
    embaralhadas = [list(rng.permutation(valores)) for valores in dimensoes]
    obrigatorias = [
        tuple(valores[indice % len(valores)] for valores in embaralhadas)
        for indice in range(minimo)
    ]
    vistos = set(obrigatorias)
    restantes = [combo for combo in product(*dimensoes) if combo not in vistos]
    rng.shuffle(restantes)
    combos = obrigatorias + restantes[:quantidade - minimo]
    rng.shuffle(combos)
    return [Trial(backbone, float(lr), int(lote), bool(aumento), str(politica), semente_base)
            for lr, lote, aumento, politica in combos]


def construir_config(trial: Trial, blocos_base: int, epocas_max_cabeca: int, paciencia: int) -> dict:
    politica = POLITICAS_FINE_TUNING[trial.politica_fine_tuning]
    if politica is None:
        fine_tuning = {
            "ativo": False,
            "blocos_descongelados": 0,
            "taxa_aprendizado": 1e-5,
            "epocas_max": 0,
        }
    else:
        blocos = min(blocos_base, max(1, round(politica["fracao_blocos"] * blocos_base)))
        fine_tuning = {
            "ativo": True,
            "blocos_descongelados": blocos,
            "taxa_aprendizado": trial.taxa_aprendizado / politica["divisor_taxa"],
            "epocas_max": politica["epocas_max"],
        }
    return {
        "backbone": trial.backbone,
        "semente": trial.semente,
        "deterministico": True,
        "otimizador": {"nome": "adam", "taxa_aprendizado": trial.taxa_aprendizado},
        "batch": trial.batch,
        "epocas_max": epocas_max_cabeca,
        "parada": {"monitor": "val_f1_macro", "paciencia": paciencia, "restaurar_melhores_pesos": True},
        "augmentation": {"ativo": trial.augmentation},
        "balanceamento": {"class_weight": True},
        "cabeca": {"dropout": 0.2},
        "fine_tuning": fine_tuning,
    }


CAMPOS_RESULTADOS = [
    "backbone", "trial", "taxa_aprendizado", "batch", "augmentation",
    "politica_fine_tuning", "blocos_descongelados", "blocos_na_base",
    "val_f1_macro", "val_balanced_accuracy", "val_acuracia", "melhor_epoca",
    "epocas_cabeca", "epocas_fine_tuning", "pasta", "erro",
]


def _gravar_resultados(caminho: Path, linhas: list[dict]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RESULTADOS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def _selecionar_melhores(linhas: list[dict]) -> dict:
    melhores: dict[str, dict] = {}
    for linha in linhas:
        if linha["val_f1_macro"] is None:
            continue
        atual = melhores.get(linha["backbone"])
        if atual is None or linha["val_f1_macro"] > atual["val_f1_macro"]:
            melhores[linha["backbone"]] = linha
    ranking = sorted(melhores.values(), key=lambda linha: linha["val_f1_macro"], reverse=True)
    return {"por_backbone": melhores, "ranking_geral": ranking}


def _auditar_cobertura(linhas: list[dict], backbones_candidatos: tuple[str, ...]) -> dict:
    """Confere se cada opção produziu ao menos uma avaliação de validação."""
    dimensoes = {
        "taxa_aprendizado": TAXAS_APRENDIZADO,
        "batch": TAMANHOS_LOTE,
        "augmentation": AUGMENTATION,
    }
    auditoria = {}
    for backbone in backbones_candidatos:
        concluidos = [linha for linha in linhas if linha["backbone"] == backbone
                      and linha["val_f1_macro"] is not None]
        esperados = {**dimensoes, "politica_fine_tuning": politicas_validas(backbone)}
        faltantes = {campo: [valor for valor in valores
                             if not any(linha[campo] == valor for linha in concluidos)]
                     for campo, valores in esperados.items()}
        auditoria[backbone] = {
            "trials_concluidos": len(concluidos),
            "valores_sem_avaliacao": faltantes,
            "cobertura_completa": all(not valores for valores in faltantes.values()),
        }
    return auditoria


def verificar_entradas(raiz_imagens: Path, caminho_indice: Path, caminho_pesos: Path) -> dict:
    """Valida o acervo antes de iniciar uma busca longa, sem depender de Keras."""
    from src.dados_treino import carregar_class_weight, carregar_indice, nomes_classes
    from src.pipeline_preparacao_t4_5 import _resolver_imagem

    indice = carregar_indice(caminho_indice)
    carregar_class_weight(caminho_pesos, len(nomes_classes(indice)))
    contagens = {"treino": 0, "validacao": 0}
    ausentes = []
    for linha in indice:
        particao = linha["particao"]
        if particao not in contagens:
            continue  # a busca não consulta a partição de teste
        contagens[particao] += 1
        if not _resolver_imagem(Path(raiz_imagens), linha["caminho_relativo"]).is_file():
            ausentes.append(linha["caminho_relativo"])
    if not all(contagens.values()):
        raise ValueError(f"índice precisa conter treino e validação: {contagens}")
    if ausentes:
        raise FileNotFoundError(
            f"{len(ausentes)} imagens de treino/validação ausentes em {raiz_imagens}; "
            f"exemplos: {', '.join(ausentes[:3])}"
        )
    return contagens


def executar_busca(
    backbones_candidatos: tuple[str, ...],
    trials_por_backbone: int,
    saida: Path,
    raiz_imagens: Path,
    epocas_max_cabeca: int,
    paciencia: int,
    semente_busca: int,
    caminho_indice: Path = INDICE_PADRAO,
    caminho_pesos: Path = PESOS_PADRAO,
    verbose: int = 2,
) -> Path:
    """Roda a busca e grava resultados.csv (incremental) e melhores_por_backbone.json."""
    if len(backbones_candidatos) not in (2, 3) or len(set(backbones_candidatos)) != len(backbones_candidatos):
        raise ValueError("informe dois ou três backbones distintos")
    if trials_por_backbone < 3:
        raise ValueError("trials_por_backbone deve ser no mínimo 3 para cobrir todos os parâmetros")
    verificar_entradas(raiz_imagens, caminho_indice, caminho_pesos)
    import gc

    import keras

    from src import backbones
    from src.treinamento_t5_1 import treinar

    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(semente_busca)
    linhas: list[dict] = []
    for backbone in backbones_candidatos:
        blocos_base = contar_blocos(backbone)
        trials = amostrar_trials(backbone, trials_por_backbone, rng, semente_busca)
        pasta_backbone = saida / backbone
        for indice, trial in enumerate(trials):
            config = construir_config(trial, blocos_base, epocas_max_cabeca, paciencia)
            validar_config(config, tuple(backbones.REGISTRO))
            linha = {
                "backbone": backbone, "trial": indice,
                "taxa_aprendizado": trial.taxa_aprendizado, "batch": trial.batch,
                "augmentation": trial.augmentation, "politica_fine_tuning": trial.politica_fine_tuning,
                "blocos_descongelados": config["fine_tuning"]["blocos_descongelados"],
                "blocos_na_base": blocos_base,
            }
            try:
                pasta_rodada = treinar(
                    config, raiz_imagens, saida=pasta_backbone,
                    caminho_indice=caminho_indice, caminho_pesos=caminho_pesos,
                    verbose=verbose,
                )
                metricas = json.loads((pasta_rodada / "metricas_validacao.json").read_text(encoding="utf-8"))
                linha.update({
                    "val_f1_macro": metricas["validacao"]["f1_macro"],
                    "val_balanced_accuracy": metricas["validacao"]["balanced_accuracy"],
                    "val_acuracia": metricas["validacao"]["acuracia"],
                    "melhor_epoca": metricas["melhor_epoca"],
                    "epocas_cabeca": metricas["epocas_executadas"]["cabeca"],
                    "epocas_fine_tuning": metricas["epocas_executadas"]["fine_tuning"],
                    "pasta": str(pasta_rodada),
                    "erro": None,
                })
            except Exception as erro:  # mantém a busca viva: um trial ruim não pode derrubar os demais
                linha.update({
                    "val_f1_macro": None, "val_balanced_accuracy": None, "val_acuracia": None,
                    "melhor_epoca": None, "epocas_cabeca": None, "epocas_fine_tuning": None,
                    "pasta": None, "erro": f"{type(erro).__name__}: {erro}",
                })
            linhas.append(linha)
            _gravar_resultados(saida / "resultados.csv", linhas)
            # cada trial constrói um modelo Keras novo; sem isso, o grafo/sessão
            # do trial anterior fica retido e a memória do processo cresce a
            # cada iteração ao longo de uma busca de muitas horas.
            keras.backend.clear_session()
            gc.collect()
    melhores = _selecionar_melhores(linhas)
    melhores["cobertura"] = _auditar_cobertura(linhas, backbones_candidatos)
    (saida / "melhores_por_backbone.json").write_text(
        json.dumps(melhores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not all(item["cobertura_completa"] for item in melhores["cobertura"].values()):
        raise RuntimeError(f"busca incompleta: confira a cobertura e os erros dos trials em {saida}")
    return saida


def main() -> None:
    parser = argparse.ArgumentParser(description="Busca de hiperparâmetros T5.4")
    parser.add_argument("--raiz-imagens", type=Path, required=True, help="Pasta com dataset/, Milho/ e Soja/")
    parser.add_argument("--backbones", nargs="+", default=list(BACKBONES_PADRAO))
    parser.add_argument("--trials-por-backbone", type=int, default=8)
    parser.add_argument("--epocas-max-cabeca", type=int, default=12)
    parser.add_argument("--paciencia", type=int, default=3)
    parser.add_argument("--semente-busca", type=int, default=42)
    parser.add_argument("--saida", type=Path, default=SAIDA_BUSCA_PADRAO)
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO)
    parser.add_argument("--pesos", type=Path, default=PESOS_PADRAO)
    parser.add_argument("--verificar-entradas", action="store_true",
                        help="Confere índice, pesos e imagens sem iniciar o treinamento")
    args = parser.parse_args()
    if args.verificar_entradas:
        print(f"Entradas válidas: {verificar_entradas(args.raiz_imagens, args.indice, args.pesos)}")
        return
    saida = executar_busca(
        tuple(args.backbones), args.trials_por_backbone, Path(args.saida), args.raiz_imagens,
        args.epocas_max_cabeca, args.paciencia, args.semente_busca,
        caminho_indice=args.indice, caminho_pesos=args.pesos,
    )
    melhores = json.loads((saida / "melhores_por_backbone.json").read_text(encoding="utf-8"))
    print(f"Busca gravada em: {saida}")
    for linha in melhores["ranking_geral"]:
        print(f"  {linha['backbone']}: val_f1_macro={linha['val_f1_macro']:.4f} ({linha['pasta']})")


if __name__ == "__main__":
    main()
