"""Executa novas rodadas T5.6, em processos isolados, sem consultar o teste."""

from pathlib import Path
import argparse
import json
import os
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
CANDIDATOS = ("efficientnet_lite0", "mobilenet_v3_large", "mobilenet_v2")
INDICE = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
PESOS = RAIZ / "assets/data/treino_T5_2/pesos_dataset.json"


def executar(raiz_imagens: Path, saida: Path, threads: int = 4) -> None:
    if threads < 1:
        raise ValueError("threads deve ser positivo")
    saida.mkdir(parents=True, exist_ok=True)
    ambiente = {**os.environ, "PYTHONUNBUFFERED": "1",
                "TF_NUM_INTRAOP_THREADS": str(threads), "TF_NUM_INTEROP_THREADS": "1"}
    for nome in CANDIDATOS:
        pasta = saida / nome
        pasta.mkdir(exist_ok=True)
        # A T5.1 só grava o modelo ao terminar. Nunca tomar uma pasta parcial por sucesso.
        completas = [p for p in pasta.glob("*/melhor_modelo.keras")
                     if all((p.parent / n).is_file() for n in
                            ("config_usada.json", "metricas_validacao.json", "ambiente.json", "historico.csv"))]
        if completas:
            if len(completas) != 1:
                raise ValueError(f"mais de uma rodada em {pasta}; separar as execuções")
            print(f"Preservando rodada concluída: {completas[0].parent}", flush=True)
            continue
        config = RAIZ / f"assets/data/retreino_t5_3/config_{nome}.json"
        comando = [sys.executable, "-m", "src.treinamento_t5_1", "--config", str(config),
                   "--raiz-imagens", str(raiz_imagens), "--indice", str(INDICE),
                   "--pesos", str(PESOS), "--saida", str(pasta)]
        log = pasta / "treinamento.log"
        print(f"Iniciando {nome}; log: {log}", flush=True)
        with log.open("a", encoding="utf-8") as arquivo:
            resultado = subprocess.run(comando, cwd=RAIZ, env=ambiente,
                                       stdout=arquivo, stderr=subprocess.STDOUT)
        estado = {"backbone": nome, "comando": comando, "codigo_saida": resultado.returncode,
                  "origem": "nova execução T5.6, não é o checkpoint histórico da T5.4",
                  "threads_intraop": threads, "threads_interop": 1}
        (pasta / "execucao_t5_6.json").write_text(
            json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if resultado.returncode:
            raise RuntimeError(f"{nome} falhou ({resultado.returncode}); consultar {log}")
        print(f"Concluído: {nome}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-imagens", required=True, type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    executar(args.raiz_imagens, args.saida, args.threads)


if __name__ == "__main__":
    main()
