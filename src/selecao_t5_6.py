"""Auditoria e publicação de um candidato rastreável; nunca acessa imagens de teste."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import csv
import json
import math
import shutil

from src.registro_experimentos_t5_5 import gerar

ARQUIVOS_RODADA = ("melhor_modelo.keras", "config_usada.json", "historico.csv",
                   "ambiente.json", "metricas_validacao.json")
CANDIDATOS = {"efficientnet_lite0", "mobilenet_v3_large", "mobilenet_v2"}
LIMITE_BYTES = 8_000_000


def hash_arquivo(caminho: Path) -> str:
    return sha256(caminho.read_bytes()).hexdigest()


def ler(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8-sig"))


def gravar(caminho: Path, dados) -> None:
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                       encoding="utf-8")


def validar_rodada(pasta: Path, indice: Path, pesos: Path) -> dict:
    faltando = [n for n in ARQUIVOS_RODADA if not (pasta / n).is_file()]
    if faltando:
        raise ValueError(f"rodada incompleta em {pasta}: {', '.join(faltando)}")
    config = ler(pasta / "config_usada.json")
    ambiente = ler(pasta / "ambiente.json")
    metricas = ler(pasta / "metricas_validacao.json")
    if metricas.get("esquema") != "metricas_validacao_T5_1_v1":
        raise ValueError("esquema da rodada incompatível")
    if config["backbone"] != metricas["backbone"] or config["semente"] != metricas["semente"]:
        raise ValueError("configuração e métricas divergem")
    hashes = ambiente.get("sha256", {})
    for chave, caminho in (("indice_pipeline", indice), ("pesos_classes", pesos)):
        if hashes.get(chave) != hash_arquivo(caminho):
            raise ValueError(f"evidência de outra rodada: hash de {chave} divergente")
    # A T5.1 registra o hash do JSON original, mas reserializa config_usada.json
    # (0.00001 e 1e-05 representam o mesmo valor). Conferir também a fonte original.
    if hashes.get("config") != hash_arquivo(pasta / "config_usada.json"):
        raiz = Path(__file__).resolve().parents[1]
        origem = (raiz / "assets/data/treino_T5_2/config_baseline.json"
                  if config["backbone"] == "cnn_baseline" else
                  raiz / f"assets/data/retreino_t5_3/config_{config['backbone']}.json")
        if not origem.is_file() or hash_arquivo(origem) != hashes.get("config") or ler(origem) != config:
            raise ValueError("evidência de outra rodada: hash de config divergente")
    with indice.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    nomes = {}
    ids = set()
    grupos, hashes_imagens = {}, {}
    for linha in linhas:
        if linha["image_id"] in ids:
            raise ValueError("ID de imagem repetido")
        ids.add(linha["image_id"])
        i = int(linha["indice_modelo"])
        nome = linha["nome_classe_modelo"]
        if i in nomes and nomes[i] != nome:
            raise ValueError("nomes de classes inconsistentes")
        nomes[i] = nome
        if linha["particao"] not in {"treino", "validacao", "teste"}:
            raise ValueError("partição desconhecida")
        for campo, mapa in (("grupo_particao", grupos), ("sha256_original", hashes_imagens)):
            valor = linha[campo]
            if not valor or (valor in mapa and mapa[valor] != linha["particao"]):
                raise ValueError("origem compartilhada entre partições")
            mapa[valor] = linha["particao"]
    if sorted(nomes) != list(range(13)):
        raise ValueError("o candidato deve preservar as 13 classes")
    classes = metricas["validacao"]["por_classe"]
    if [(c["indice"], c["nome"]) for c in classes] != list(sorted(nomes.items())):
        raise ValueError("ordem das classes incompatível com o índice")
    suporte = Counter(int(r["indice_modelo"]) for r in linhas if r["particao"] == "validacao")
    if any(c["suporte"] != suporte[c["indice"]] for c in classes):
        raise ValueError("suporte de validação divergente")
    for particao in ("treino", "validacao"):
        if metricas["imagens"][particao] != sum(r["particao"] == particao for r in linhas):
            raise ValueError("contagens de imagens divergentes")
    f1 = metricas["validacao"]["f1_macro"]
    if not isinstance(f1, (float, int)) or not math.isfinite(f1) or not 0 <= f1 <= 1:
        raise ValueError("F1 macro inválida")
    if not math.isclose(f1, sum(c["f1"] for c in classes) / len(classes), abs_tol=1e-12):
        raise ValueError("F1 macro diverge das métricas por classe")
    with (pasta / "historico.csv").open(encoding="utf-8", newline="") as f:
        historico = list(csv.DictReader(f))
    if not historico or metricas["pesos_finais"] != "melhor época":
        raise ValueError("histórico ou restauração dos melhores pesos ausente")
    melhor = max(float(l["val_f1_macro"]) for l in historico)
    if config["parada"]["monitor"] != "val_f1_macro" or not math.isclose(f1, melhor, abs_tol=1e-7):
        raise ValueError("checkpoint não corresponde ao melhor F1 registrado")
    return {"pasta": pasta, "arquitetura": config["backbone"], "config": config,
            "metricas": metricas, "f1_macro": f1,
            "balanced_accuracy": metricas["validacao"]["balanced_accuracy"],
            "classes": [{"indice": i, "nome": n} for i, n in sorted(nomes.items())],
            "sha256": {n: hash_arquivo(pasta / n) for n in ARQUIVOS_RODADA}}


def comparar(pastas: list[Path], indice: Path, pesos: Path) -> list[dict]:
    rodadas = [validar_rodada(p, indice, pesos) for p in pastas]
    if len(rodadas) != 3 or {r["arquitetura"] for r in rodadas} != CANDIDATOS:
        raise ValueError("necessária exatamente uma rodada de cada um dos três candidatos")
    orcamentos = [(r["config"]["epocas_max"], r["config"]["parada"],
                   r["config"]["fine_tuning"]["epocas_max"], r["config"]["semente"])
                  for r in rodadas]
    if any(o != orcamentos[0] for o in orcamentos):
        raise ValueError("orçamento, parada ou semente distintos entre candidatos")
    return sorted(rodadas, key=lambda r: (-r["f1_macro"], -r["balanced_accuracy"], r["arquitetura"]))


def publicar(rodada: Path, conversao: Path, indice: Path, pesos: Path,
             saida: Path, modelos: Path, comparativo: Path, data: str) -> dict:
    """Publica somente após conferir origem, métrica, conversão e linha da T5.5."""
    r = validar_rodada(rodada, indice, pesos)
    evidencia = ler(conversao / "conversao.json")
    if (evidencia.get("teste_acessado") is not False
            or evidencia.get("particao_avaliacao") != "validacao"
            or evidencia.get("pesos_sha256") != hash_arquivo(pesos)):
        raise ValueError("protocolo de conversão incompatível")
    if evidencia["modelo_origem_sha256"] != r["sha256"]["melhor_modelo.keras"]:
        raise ValueError("conversão pertence a outro checkpoint")
    if evidencia["indice_sha256"] != hash_arquivo(indice):
        raise ValueError("conversão usa outro recorte")
    modelo_tflite = conversao / "modelo_int8.tflite"
    if hash_arquivo(modelo_tflite) != evidencia["int8_sha256"]:
        raise ValueError("modelo convertido diverge da evidência")
    if not 0 < modelo_tflite.stat().st_size <= LIMITE_BYTES:
        raise ValueError("candidato não atende ao limite de 8 MB")
    if hash_arquivo(conversao / "modelo_fp32.tflite") != evidencia["fp32_sha256"]:
        raise ValueError("modelo FP32 diverge da evidência")
    # Uma chamada isolada não pode publicar um candidato arbitrário como vencedor.
    # As rodadas da mesma campanha ficam juntas; versões anteriores não entram
    # novamente no ranking nem impedem a publicação de uma nova data.
    pastas = [p.parent for p in rodada.parent.rglob("metricas_validacao.json")
              if ler(p).get("backbone") in CANDIDATOS]
    ranking = comparar(pastas, indice, pesos)
    elegiveis = []
    for candidato in ranking:
        pasta_conversao = candidato["pasta"] / "conversao_t5_6"
        prova = ler(pasta_conversao / "conversao.json")
        arquivo = pasta_conversao / "modelo_int8.tflite"
        if (prova["modelo_origem_sha256"] != candidato["sha256"]["melhor_modelo.keras"]
                or prova["int8_sha256"] != hash_arquivo(arquivo)
                or prova["indice_sha256"] != hash_arquivo(indice)):
            raise ValueError("conversão de candidato inconsistente")
        if 0 < arquivo.stat().st_size <= LIMITE_BYTES:
            elegiveis.append(candidato)
    if not elegiveis or elegiveis[0]["pasta"].resolve() != rodada.resolve():
        raise ValueError("candidato não é o vencedor elegível da comparação")
    if saida.exists():
        raise ValueError("pacote já existe; preservar a versão e escolher outra saída")
    linhas = gerar(modelos, comparativo)
    id_execucao = rodada.resolve().relative_to(modelos.resolve()).as_posix()
    linha = next((l for l in linhas if l["execucao"] == id_execucao), None)
    if linha is None or linha["f1_macro_validacao"] != r["f1_macro"]:
        raise ValueError("rodada não corresponde à linha T5.5")
    saida.mkdir(parents=True)
    destinos = {"melhor_modelo.keras": "modelo.keras", "config_usada.json": "configuracao_treino.json",
                "historico.csv": "historico.csv", "ambiente.json": "ambiente_treino.json",
                "metricas_validacao.json": "avaliacao_validacao.json"}
    for origem, destino in destinos.items():
        shutil.copy2(rodada / origem, saida / destino)
    for nome in ("modelo_int8.tflite", "modelo_fp32.tflite", "conversao.json"):
        shutil.copy2(conversao / nome, saida / nome)
    shutil.copy2(comparativo / "experimentos.csv", saida / "registro_t5_5.csv")
    gravar(saida / "classes.json", r["classes"])
    manifesto = {
        "esquema": "selecao_T5_6_v1", "data": data,
        "status": "candidato_versionado_benchmark_celular_pendente",
        "origem": "nova rodada T5.6 com configurações da T5.4",
        "artefato_para_embarque": "modelo_int8.tflite",
        "demais_modelos": "checkpoint Keras e TFLite FP32 preservados para auditoria; não são o pacote móvel",
        "arquitetura": r["arquitetura"], "execucao_t5_5": id_execucao,
        "criterio": "maior F1 macro de validação entre as novas rodadas comparáveis que cabem em 8 MB; empate exato por balanced accuracy e nome",
        "f1_macro_validacao_keras": r["f1_macro"], "tamanho_int8_bytes": modelo_tflite.stat().st_size,
        "comparacao": [{"execucao": c["pasta"].resolve().relative_to(modelos.resolve()).as_posix(),
                        "arquitetura": c["arquitetura"], "f1_macro_validacao": c["f1_macro"],
                        "balanced_accuracy": c["balanced_accuracy"],
                        "modelo_keras_sha256": c["sha256"]["melhor_modelo.keras"],
                        "int8_bytes": (c["pasta"] / "conversao_t5_6/modelo_int8.tflite").stat().st_size}
                       for c in ranking],
        "limite_modelo_bytes_proposto": LIMITE_BYTES,
        "latencia_celular": {"status": "pendente", "limite_p95_ms_proposto": 300},
        "aprovacao_parceiro": "pendente", "teste_utilizado_na_selecao": False,
        "indice_sha256": hash_arquivo(indice), "pesos_sha256": hash_arquivo(pesos),
        "registro_comparativo_sha256": hash_arquivo(comparativo / "experimentos.csv"),
        "codigo_sha256": {p.name: hash_arquivo(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "sha256": {p.name: hash_arquivo(p) for p in sorted(saida.iterdir())},
    }
    gravar(saida / "manifesto.json", manifesto)
    return manifesto


def verificar_pacote(pacote: Path, comparativo: Path) -> dict:
    manifesto = ler(pacote / "manifesto.json")
    if manifesto.get("esquema") != "selecao_T5_6_v1":
        raise ValueError("esquema de pacote incompatível")
    for nome, hash_esperado in manifesto["sha256"].items():
        if Path(nome).name != nome or hash_arquivo(pacote / nome) != hash_esperado:
            raise ValueError(f"artefato alterado: {nome}")
    if hash_arquivo(pacote / "registro_t5_5.csv") != manifesto["registro_comparativo_sha256"]:
        raise ValueError("snapshot do registro alterado")
    linhas = []
    for caminho in (pacote / "registro_t5_5.csv", comparativo / "experimentos.csv"):
        with caminho.open(encoding="utf-8", newline="") as f:
            matches = [r for r in csv.DictReader(f) if r["execucao"] == manifesto["execucao_t5_5"]]
        if len(matches) != 1:
            raise ValueError("vínculo com a T5.5 ausente ou ambíguo")
        linhas.append(matches[0])
    if linhas[0] != linhas[1] or float(linhas[0]["f1_macro_validacao"]) != manifesto["f1_macro_validacao_keras"]:
        raise ValueError("linha da T5.5 diverge do pacote")
    metricas = ler(pacote / "avaliacao_validacao.json")
    esperado = [{"indice": c["indice"], "nome": c["nome"]}
                for c in metricas["validacao"]["por_classe"]]
    if ler(pacote / "classes.json") != esperado:
        raise ValueError("classes do pacote incompatíveis")
    conversao = ler(pacote / "conversao.json")
    if conversao["modelo_origem_sha256"] != hash_arquivo(pacote / "modelo.keras"):
        raise ValueError("conversão não corresponde ao checkpoint")
    return manifesto


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", type=Path, help="Audita um pacote já publicado, sem reescrevê-lo")
    parser.add_argument("--rodada", type=Path)
    parser.add_argument("--conversao", type=Path)
    parser.add_argument("--indice", type=Path)
    parser.add_argument("--pesos", type=Path)
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--modelos", type=Path, default=Path("assets/modelos"))
    parser.add_argument("--comparativo", type=Path, default=Path("assets/data/experimentos_T5_5"))
    parser.add_argument("--data")
    args = parser.parse_args()
    if args.verificar:
        manifesto = verificar_pacote(args.verificar, args.comparativo)
        print(f"Pacote verificado: {manifesto['arquitetura']}; benchmark no celular: pendente")
        return
    if any(getattr(args, k) is None for k in ("rodada", "conversao", "indice", "pesos", "saida", "data")):
        parser.error("publicação exige --rodada, --conversao, --indice, --pesos, --saida e --data")
    print(json.dumps(publicar(args.rodada, args.conversao, args.indice, args.pesos,
                              args.saida, args.modelos, args.comparativo, args.data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
