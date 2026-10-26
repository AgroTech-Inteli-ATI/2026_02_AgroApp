"""Avaliação final de uma rodada T5.1 exclusivamente na partição de teste."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from src.avaliacao import calcular_metricas
from src.preprocessamento import preparar_imagem

RAIZ = Path(__file__).resolve().parents[1]
INDICE = RAIZ / "assets/data/pipeline_T4_5/indice_pipeline.csv"


def _hash(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def _carregar_modelo(caminho: Path):
    import keras
    # Registra também as camadas dos backbones KerasHub usados pela T5.1.
    import keras_hub  # noqa: F401
    return keras.models.load_model(caminho, compile=False)


def avaliar(rodada: Path, raiz_imagens: Path, saida: Path, indice: Path = INDICE,
            batch: int = 32, carregador=None) -> dict:
    if isinstance(batch, bool) or not isinstance(batch, int) or batch < 1:
        raise ValueError("batch deve ser inteiro positivo")
    arquivos = ("metricas_teste.json", "metricas_por_classe.csv", "predicoes_teste.csv", "relatorio_teste.md")
    if any((saida / nome).exists() for nome in arquivos):
        raise ValueError("a saída já contém avaliação; escolha outra pasta para preservar os resultados")
    ambiente = json.loads((rodada / "ambiente.json").read_text(encoding="utf-8"))
    anteriores = json.loads((rodada / "metricas_validacao.json").read_text(encoding="utf-8"))
    if anteriores.get("esquema") != "metricas_validacao_T5_1_v1":
        raise ValueError("esquema da rodada não suportado")
    if ambiente["sha256"]["indice_pipeline"] != _hash(indice):
        raise ValueError("índice diverge daquele usado no treinamento")
    classes = anteriores["validacao"]["por_classe"]
    if not classes or [c["indice"] for c in classes] != list(range(len(classes))):
        raise ValueError("ordem de classes inválida na rodada")
    nomes = [c["nome"] for c in classes]
    with indice.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    ids, grupos, hashes = set(), {}, {}
    for linha in linhas:
        if linha["image_id"] in ids:
            raise ValueError("image_id duplicado no índice")
        ids.add(linha["image_id"])
        rotulo = int(linha["indice_modelo"])
        if not 0 <= rotulo < len(nomes) or linha["nome_classe_modelo"] != nomes[rotulo]:
            raise ValueError("classes do índice divergem da saída do modelo")
        if linha["particao"] not in {"treino", "validacao", "teste"}:
            raise ValueError("partição desconhecida")
        for campo, mapa in (("grupo_particao", grupos), ("sha256_original", hashes)):
            valor = linha[campo]
            if not valor:
                raise ValueError(f"{campo} ausente")
            if valor in mapa and mapa[valor] != linha["particao"]:
                raise ValueError(f"{campo} compartilhado entre partições")
            mapa[valor] = linha["particao"]
    teste = [l for l in linhas if l["particao"] == "teste"]
    if not teste:
        raise ValueError("partição de teste vazia")
    tamanho = anteriores["tamanho_entrada"]
    caminho_modelo = rodada / "melhor_modelo.keras"
    hash_modelo = _hash(caminho_modelo)
    modelo = (carregador or _carregar_modelo)(caminho_modelo)
    if tuple(modelo.input_shape[1:]) != (tamanho, tamanho, 3) or tuple(modelo.output_shape[1:]) != (len(nomes),):
        raise ValueError("dimensões do modelo incompatíveis com a rodada")
    previstos = []
    for inicio in range(0, len(teste), batch):
        lote = teste[inicio:inicio + batch]
        imagens = []
        for linha in lote:
            relativo = Path(linha["caminho_relativo"])
            caminho = raiz_imagens / relativo
            if not caminho.is_file() and relativo.parts and relativo.parts[0] == raiz_imagens.name:
                caminho = raiz_imagens.joinpath(*relativo.parts[1:])
            if _hash(caminho) != linha["sha256_original"]:
                raise ValueError(f"hash original divergente: {linha['image_id']}")
            imagens.append(preparar_imagem(caminho, tamanho))
        probabilidades = np.asarray(modelo.predict_on_batch(np.stack(imagens)))
        if (probabilidades.shape != (len(lote), len(nomes)) or not np.isfinite(probabilidades).all()
                or (probabilidades < 0).any() or (probabilidades > 1).any()
                or not np.allclose(probabilidades.sum(axis=1), 1, atol=1e-5)):
            raise ValueError("saída do modelo não é uma distribuição softmax válida")
        previstos.extend(probabilidades.argmax(axis=1).tolist())
    rotulos = np.array([int(l["indice_modelo"]) for l in teste])
    metricas = calcular_metricas(rotulos, np.array(previstos), len(nomes), nomes)
    resultado = {
        "esquema": "metricas_teste_T6_1_v1", "particao": "teste",
        "metrica_principal": "f1_macro", "backbone": anteriores["backbone"],
        "sha256": {"modelo": hash_modelo, "indice_pipeline": _hash(indice)},
        "ambiente_treinamento": ambiente, "batch_avaliacao": batch,
        "augmentation": False, "ponderacao": False, "teste": metricas,
    }
    saida.mkdir(parents=True, exist_ok=True)
    (saida / arquivos[0]).write_text(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (saida / arquivos[1]).open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(metricas["por_classe"][0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(metricas["por_classe"])
    with (saida / arquivos[2]).open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(["image_id", "indice_real", "indice_previsto"])
        escritor.writerows((l["image_id"], int(l["indice_modelo"]), p) for l, p in zip(teste, previstos))
    def numero(valor):
        return "não avaliada" if valor is None else f"{valor:.6f}"
    texto = ["# Avaliação final — T6.1", "", "**Métrica principal: macro F1 no teste = " + numero(metricas["f1_macro"]) + "**", "",
             f"Imagens: {len(teste)}. Classes avaliadas: {metricas['classes_avaliadas']}/{len(nomes)}.",
             "Classes sem suporte permanecem na tabela e não entram na média macro.", "",
             "| Índice | Classe | Precisão | Recall | F1 | Suporte | Status |",
             "| ---: | --- | ---: | ---: | ---: | ---: | --- |"]
    for c in metricas["por_classe"]:
        nome = c["nome"].replace("|", "&#124;").replace("\n", " ")
        texto.append(f"| {c['indice']} | {nome} | {numero(c['precisao'])} | {numero(c['recall'])} | {numero(c['f1'])} | {c['suporte']} | {c['status']} |")
    texto += ["", "Acurácia global (complementar): " + numero(metricas["acuracia"]) + "."]
    (saida / arquivos[3]).write_text("\n".join(texto) + "\n", encoding="utf-8")
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rodada", type=Path, required=True)
    parser.add_argument("--raiz-imagens", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--indice", type=Path, default=INDICE)
    parser.add_argument("--batch", type=int, default=32)
    args = parser.parse_args()
    resultado = avaliar(args.rodada, args.raiz_imagens, args.saida, args.indice, args.batch)
    print(f"Macro F1 no teste: {resultado['teste']['f1_macro']}")


if __name__ == "__main__":
    main()
