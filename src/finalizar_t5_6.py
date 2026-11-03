"""Converte as novas rodadas, atualiza a T5.5 e publica o candidato elegível."""

from datetime import datetime
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

from src.selecao_t5_6 import (
    ARQUIVOS_RODADA, CANDIDATOS, LIMITE_BYTES, comparar, gravar,
    hash_arquivo, ler, publicar,
)

RAIZ = Path(__file__).resolve().parents[1]


def finalizar(treinos: Path, raiz_imagens: Path, data: str):
    datetime.strptime(data, "%Y-%m-%d")
    indice = RAIZ / "assets/data/treino_T5_2/indice_dataset.csv"
    pesos = RAIZ / "assets/data/treino_T5_2/pesos_dataset.json"
    modelos = RAIZ / "assets/modelos"
    origem = []
    for nome in sorted(CANDIDATOS):
        pastas = list((treinos / nome).glob("*/melhor_modelo.keras"))
        if len(pastas) != 1:
            raise ValueError(f"esperada uma rodada concluída de {nome}; encontradas {len(pastas)}")
        origem.append(pastas[0].parent)
    comparar(origem, indice, pesos)
    pasta_rodadas = modelos / f"rodadas_T5_6_{data.replace('-', '')}"
    pastas = []
    env = {**os.environ, "TF_NUM_INTRAOP_THREADS": "4", "TF_NUM_INTEROP_THREADS": "1",
           "PYTHONUNBUFFERED": "1"}
    for original in origem:
        destino = pasta_rodadas / original.name
        if destino.exists():
            if any(hash_arquivo(destino / n) != hash_arquivo(original / n) for n in ARQUIVOS_RODADA):
                raise ValueError("rodada já arquivada diverge da original")
        else:
            shutil.copytree(original, destino)
        shutil.copy2(original.parent / "execucao_t5_6.json", destino / "execucao_t5_6.json")
        pastas.append(destino)
        conversao = destino / "conversao_t5_6"
        if not (conversao / "conversao.json").is_file():
            if conversao.exists():
                conversao.rename(destino / f"conversao_incompleta_{datetime.now():%Y%m%d%H%M%S}")
            comando = [sys.executable, "-m", "src.converter_t5_6", "--rodada", str(destino),
                       "--raiz-imagens", str(raiz_imagens), "--indice", str(indice),
                       "--pesos", str(pesos), "--saida", str(conversao)]
            print(f"Convertendo {destino.name}", flush=True)
            with (destino / "conversao.log").open("a", encoding="utf-8") as log:
                subprocess.run(comando, cwd=RAIZ, env=env, stdout=log,
                               stderr=subprocess.STDOUT, check=True)
        print(f"Conversão concluída: {destino.name}", flush=True)
    ranking = comparar(pastas, indice, pesos)
    elegiveis = [r for r in ranking
                 if 0 < (r["pasta"] / "conversao_t5_6/modelo_int8.tflite").stat().st_size <= LIMITE_BYTES]
    if not elegiveis:
        raise ValueError("nenhum candidato atende ao limite de 8 MB")
    escolhido = elegiveis[0]
    resumo = []
    for r in ranking:
        venceu = r["pasta"] == escolhido["pasta"]
        motivo = "" if venceu else ("modelo INT8 excede 8 MB" if r not in elegiveis else
                                    "não selecionada: F1 macro de validação inferior ou desempate declarado")
        gravar(r["pasta"] / "registro_t5_5.json", {
            "status": "concluida" if venceu else "descartada", "motivo_descarte": motivo,
            "origem": "nova rodada T5.6; hiperparâmetros fixos da T5.4; recorte dataset-only"})
        resumo.append({"execucao": r["pasta"].relative_to(modelos).as_posix(),
                       "arquitetura": r["arquitetura"], "f1_macro_validacao": r["f1_macro"],
                       "balanced_accuracy": r["balanced_accuracy"], "selecionada": venceu,
                       "motivo_descarte": motivo, "metricas": r["metricas"]["validacao"],
                       "conversao": ler(r["pasta"] / "conversao_t5_6/conversao.json")})
    registro = RAIZ / "assets/data/experimentos_T5_5"
    pacote = modelos / f"candidato_T5_6_{data.replace('-', '')}"
    manifesto = publicar(escolhido["pasta"], escolhido["pasta"] / "conversao_t5_6",
                         indice, pesos, pacote, modelos, registro, data)
    relatorios = RAIZ / "assets/data/selecao_T5_6"
    relatorios.mkdir(parents=True, exist_ok=True)
    gravar(relatorios / "comparacao.json", {"data": data, "teste_utilizado": False,
           "origem": "novas execuções; não substituem os resultados históricos da T5.4",
           "indice_sha256": hash_arquivo(indice), "candidatos": resumo,
           "pacote": pacote.relative_to(RAIZ).as_posix()})
    print(f"Candidato publicado: {manifesto['arquitetura']} em {pacote}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--treinos", required=True, type=Path)
    p.add_argument("--raiz-imagens", required=True, type=Path)
    p.add_argument("--data", required=True)
    a = p.parse_args()
    finalizar(a.treinos, a.raiz_imagens, a.data)


if __name__ == "__main__":
    main()
