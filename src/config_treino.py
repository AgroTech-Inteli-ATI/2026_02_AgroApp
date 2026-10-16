"""Leitura e validação da configuração de treinamento.

A configuração reúne tudo o que pode variar entre rodadas. O tamanho de entrada
não aparece aqui: ele vem do backbone escolhido (src/backbones.py).
"""

from __future__ import annotations

from pathlib import Path
import json

MONITORES = {"val_f1_macro": "max", "val_loss": "min"}
OTIMIZADORES = ("adam", "adamw", "sgd", "rmsprop")

ESQUEMA = {
    "backbone": str,
    "semente": int,
    "deterministico": bool,
    "otimizador": {"nome": str, "taxa_aprendizado": float},
    "batch": int,
    "epocas_max": int,
    "parada": {"monitor": str, "paciencia": int, "restaurar_melhores_pesos": bool},
    "augmentation": {"ativo": bool},
    "balanceamento": {"class_weight": bool},
    "cabeca": {"dropout": float},
    "fine_tuning": {
        "ativo": bool,
        "blocos_descongelados": int,
        "taxa_aprendizado": float,
        "epocas_max": int,
    },
}


def _conferir_tipos(valores: dict, esquema: dict, prefixo: str = "") -> None:
    faltando = set(esquema) - set(valores)
    sobrando = set(valores) - set(esquema)
    if faltando or sobrando:
        raise ValueError(
            f"config{prefixo}: chaves faltando {sorted(faltando)}, desconhecidas {sorted(sobrando)}"
        )
    for chave, tipo in esquema.items():
        valor = valores[chave]
        caminho = f"{prefixo}.{chave}"
        if isinstance(tipo, dict):
            if not isinstance(valor, dict):
                raise ValueError(f"config{caminho} deve ser um objeto")
            _conferir_tipos(valor, tipo, caminho)
        elif tipo is float:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValueError(f"config{caminho} deve ser numérico")
        elif tipo is int:
            if isinstance(valor, bool) or not isinstance(valor, int):
                raise ValueError(f"config{caminho} deve ser inteiro")
        elif not isinstance(valor, tipo):
            raise ValueError(f"config{caminho} deve ser {tipo.__name__}")


def validar_config(config: dict, backbones_disponiveis: tuple[str, ...] | None = None) -> dict:
    """Confere chaves, tipos e faixas; devolve a própria config."""
    _conferir_tipos(config, ESQUEMA)
    if backbones_disponiveis is not None and config["backbone"] not in backbones_disponiveis:
        raise ValueError(
            f"backbone '{config['backbone']}' não registrado; opções: {', '.join(backbones_disponiveis)}"
        )
    if config["otimizador"]["nome"] not in OTIMIZADORES:
        raise ValueError(f"otimizador deve ser um de {OTIMIZADORES}")
    if config["parada"]["monitor"] not in MONITORES:
        raise ValueError(f"parada.monitor deve ser um de {tuple(MONITORES)}")
    positivos = {
        "batch": config["batch"],
        "epocas_max": config["epocas_max"],
        "parada.paciencia": config["parada"]["paciencia"],
        "otimizador.taxa_aprendizado": config["otimizador"]["taxa_aprendizado"],
    }
    if config["fine_tuning"]["ativo"]:
        positivos.update({
            "fine_tuning.blocos_descongelados": config["fine_tuning"]["blocos_descongelados"],
            "fine_tuning.taxa_aprendizado": config["fine_tuning"]["taxa_aprendizado"],
            "fine_tuning.epocas_max": config["fine_tuning"]["epocas_max"],
        })
        if config["fine_tuning"]["taxa_aprendizado"] >= config["otimizador"]["taxa_aprendizado"]:
            raise ValueError("fine_tuning.taxa_aprendizado deve ser menor que a da cabeça")
    for nome, valor in positivos.items():
        if valor <= 0:
            raise ValueError(f"config.{nome} deve ser positivo")
    if not 0 <= config["cabeca"]["dropout"] < 1:
        raise ValueError("config.cabeca.dropout deve estar em [0, 1)")
    return config


def carregar_config(caminho: Path, backbones_disponiveis: tuple[str, ...] | None = None) -> dict:
    config = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return validar_config(config, backbones_disponiveis)
