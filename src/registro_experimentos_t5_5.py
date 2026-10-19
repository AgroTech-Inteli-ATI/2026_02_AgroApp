"""Consolida rodadas T5.1 sem carregar modelos ou acessar o conjunto de teste."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS = (
    "execucao", "status", "motivo_descarte", "arquitetura", "hiperparametros",
    "f1_macro_validacao", "desempenho_por_classe", "tamanho_modelo_bytes",
    "formato_modelo", "latencia_estimada_ms", "contexto_latencia",
    "proveniencia", "pendencias",
)


def _ler(pasta: Path, nome: str) -> dict:
    caminho = pasta / nome
    if not caminho.exists():
        return {}
    valor = json.loads(caminho.read_text(encoding="utf-8-sig"))
    if not isinstance(valor, dict):
        raise ValueError(f"{caminho}: esperado objeto JSON")
    return valor


def _json(valor: dict | list) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _numero(valor, nome: str, maximo: float | None = None):
    if valor is not None and (
        isinstance(valor, bool) or not isinstance(valor, (int, float))
        or not math.isfinite(valor) or valor < 0
        or (maximo is not None and valor > maximo)
    ):
        raise ValueError(f"{nome}: valor numérico inválido")
    return valor


def consolidar(entrada: Path) -> list[dict]:
    """Uma linha por pasta de rodada, inclusive sem métricas ou descartada."""
    nomes = {"config_usada.json", "metricas_validacao.json", "registro_t5_5.json", "ambiente.json"}
    pastas = sorted({p.parent for p in entrada.rglob("*.json") if p.name in nomes})
    linhas = []
    for pasta in pastas:
        config = _ler(pasta, "config_usada.json")
        metricas = _ler(pasta, "metricas_validacao.json")
        registro = _ler(pasta, "registro_t5_5.json")
        ambiente = _ler(pasta, "ambiente.json")
        status = registro.get("status", "concluida" if metricas else "incompleta")
        if status not in {"concluida", "incompleta", "descartada"}:
            raise ValueError(f"{pasta}: status inválido")
        motivo = registro.get("motivo_descarte", "")
        if not isinstance(motivo, str) or (status == "descartada" and not motivo.strip()):
            raise ValueError(f"{pasta}: descarte exige motivo textual")
        if status != "descartada" and motivo:
            raise ValueError(f"{pasta}: motivo_descarte exige status descartada")
        if metricas and metricas.get("esquema") != "metricas_validacao_T5_1_v1":
            raise ValueError(f"{pasta}: esquema de métricas não suportado")
        if config and metricas and config.get("backbone") != metricas.get("backbone"):
            raise ValueError(f"{pasta}: arquitetura diverge entre configuração e métricas")
        validacao = metricas.get("validacao", {})
        f1 = _numero(validacao.get("f1_macro"), "f1_macro", 1)
        classes = validacao.get("por_classe", [])
        for classe in classes:
            for chave in ("precisao", "recall", "f1"):
                _numero(classe.get(chave), chave, 1)
        latencia = registro.get("latencia", {})
        ms = _numero(latencia.get("estimativa_ms"), "latência")
        contexto = ("dispositivo", "runtime", "precisao", "batch", "metodo", "fonte")
        if ms is not None and any(not latencia.get(c) for c in contexto):
            raise ValueError(f"{pasta}: latência exige dispositivo, runtime, precisão, batch, método e fonte")
        relativo = registro.get("artefato_modelo", "melhor_modelo.keras")
        artefato = (pasta / relativo).resolve()
        if not artefato.is_relative_to(pasta.resolve()):
            raise ValueError(f"{pasta}: artefato deve estar dentro da rodada")
        tamanho = artefato.stat().st_size if artefato.is_file() else None
        pendencias = []
        for falta, nome in ((not config, "hiperparâmetros"), (f1 is None, "macro F1"),
                            (not classes, "desempenho por classe"), (tamanho is None, "modelo"),
                            (ms is None, "latência"), (not ambiente, "proveniência")):
            if falta:
                pendencias.append(nome)
        linhas.append(dict(zip(CAMPOS, (
            pasta.relative_to(entrada).as_posix() or ".", status, motivo,
            config.get("backbone", metricas.get("backbone", "não informado")),
            _json(config), f1, _json(classes), tamanho,
            artefato.suffix if tamanho is not None else "não disponível",
            ms, _json(latencia), _json(ambiente), "; ".join(pendencias),
        ))))
    return linhas


def gerar(entrada: Path, saida: Path) -> list[dict]:
    linhas = consolidar(entrada)
    saida.mkdir(parents=True, exist_ok=True)
    with (saida / "experimentos.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)

    def celula(valor) -> str:
        if valor is None or valor == "":
            return "não informado"
        return str(valor).replace("&", "&amp;").replace("<", "&lt;").replace(
            ">", "&gt;"
        ).replace("|", "&#124;").replace("\r", " ").replace("\n", " ")

    texto = ["# Registro comparativo de experimentos — T5.5", "",
             "Uma linha por execução. Métricas de validação; ausências não representam zero.", "",
             "| " + " | ".join(CAMPOS) + " |",
             "| " + " | ".join("---" for _ in CAMPOS) + " |"]
    texto.extend("| " + " | ".join(celula(linha[c]) for c in CAMPOS) + " |" for linha in linhas)
    if not linhas:
        texto += ["", "Nenhuma execução encontrada. Não há resultados reais para comparar."]
    (saida / "experimentos.md").write_text("\n".join(texto) + "\n", encoding="utf-8")
    return linhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=RAIZ / "runs")
    parser.add_argument("--saida", type=Path, default=RAIZ / "assets/data/experimentos_T5_5")
    args = parser.parse_args()
    print(f"{len(gerar(args.entrada, args.saida))} execuções registradas")


if __name__ == "__main__":
    main()
