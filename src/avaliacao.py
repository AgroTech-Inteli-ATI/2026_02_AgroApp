"""Métricas de avaliação fixas para todos os candidatos.

Calculadas em NumPy, sem depender do framework de treino, e usadas tanto no
acompanhamento por época quanto na avaliação final da validação. Classes sem
exemplos na partição avaliada ficam marcadas como "não avaliada" e não entram
nas médias macro (seção 4.3).
"""

from __future__ import annotations

import numpy as np

NAO_AVALIADA = "não avaliada"
AVALIADA = "avaliada"


def matriz_confusao(rotulos: np.ndarray, previstos: np.ndarray, quantidade_classes: int) -> np.ndarray:
    """Linhas são a classe real e colunas a classe prevista."""
    rotulos = np.asarray(rotulos, dtype=np.int64)
    previstos = np.asarray(previstos, dtype=np.int64)
    if rotulos.shape != previstos.shape:
        raise ValueError("rótulos e previsões têm tamanhos diferentes")
    for nome, valores in (("rótulos", rotulos), ("previsões", previstos)):
        if valores.size and (valores.min() < 0 or valores.max() >= quantidade_classes):
            raise ValueError(f"{nome} fora de 0..{quantidade_classes - 1}")
    matriz = np.zeros((quantidade_classes, quantidade_classes), dtype=np.int64)
    np.add.at(matriz, (rotulos, previstos), 1)
    return matriz


def calcular_metricas(
    rotulos: np.ndarray,
    previstos: np.ndarray,
    quantidade_classes: int,
    nomes_classes: list[str] | None = None,
) -> dict:
    """F1 macro, balanced accuracy, métricas por classe e matriz de confusão.

    Precisão de uma classe nunca prevista vale 0, como `zero_division=0` no scikit-learn.
    """
    matriz = matriz_confusao(rotulos, previstos, quantidade_classes)
    acertos = np.diag(matriz).astype(np.float64)
    suporte = matriz.sum(axis=1)
    previstos_por_classe = matriz.sum(axis=0)

    por_classe = []
    f1s, recalls = [], []
    for indice in range(quantidade_classes):
        nome = nomes_classes[indice] if nomes_classes else str(indice)
        if suporte[indice] == 0:
            por_classe.append({
                "indice": indice, "nome": nome, "status": NAO_AVALIADA, "suporte": 0,
                "precisao": None, "recall": None, "f1": None,
            })
            continue
        precisao = acertos[indice] / previstos_por_classe[indice] if previstos_por_classe[indice] else 0.0
        recall = acertos[indice] / suporte[indice]
        f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
        f1s.append(f1)
        recalls.append(recall)
        por_classe.append({
            "indice": indice, "nome": nome, "status": AVALIADA, "suporte": int(suporte[indice]),
            "precisao": float(precisao), "recall": float(recall), "f1": float(f1),
        })

    total = int(suporte.sum())
    return {
        "f1_macro": float(np.mean(f1s)) if f1s else None,
        "balanced_accuracy": float(np.mean(recalls)) if recalls else None,
        "acuracia": float(acertos.sum() / total) if total else None,
        "total_amostras": total,
        "classes_avaliadas": len(f1s),
        "classes_nao_avaliadas": [c["indice"] for c in por_classe if c["status"] == NAO_AVALIADA],
        "por_classe": por_classe,
        "matriz_confusao": matriz.tolist(),
    }
