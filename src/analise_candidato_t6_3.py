"""Publica a análise exploratória dos erros do candidato, sem executar o modelo."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path

from . import matriz_candidato_t6_2 as matriz

SAIDA = matriz.RAIZ / "assets/data/avaliacao_T6_3/candidato_T5_6_20261026_keras"
ANOTACOES = SAIDA / "anotacoes_visuais.json"
ESTAGIOS = {"Adult", "Larva", "Nymph", "Pupa", "Egg", "sem_estagio"}
VISUAIS = {"adulto_aparente", "ninfa_aparente", "larva_aparente", "indeterminado"}
HIPOTESES = {"qualidade_imagem", "semelhanca_visual", "conteudo_multiplos_insetos",
             "rotulo_inconsistente", "variacao_estagio", "cobertura_estagio"}


def csv_texto(linhas: list[dict]) -> str:
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=list(linhas[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(linhas)
    return f.getvalue()


def validar_anotacoes(dados: dict, anotacoes: dict) -> None:
    esperadas = {r["image_id"] for r in dados["erros"]}
    if set(anotacoes["anotacoes"]) != esperadas:
        raise ValueError("anotações devem cobrir exatamente todos os erros do candidato")
    for image_id, a in anotacoes["anotacoes"].items():
        if (len(a) != 4 or a[0] not in VISUAIS or not a[1]
                or not set(a[2]) <= HIPOTESES or not a[3].strip()):
            raise ValueError(f"anotação inválida: {image_id}")


def construir(dados: dict, indice: list[dict], field: dict, agro: dict,
              anotacoes: dict) -> dict[str, str]:
    validar_anotacoes(dados, anotacoes)
    por_id = {r["image_id"]: r for r in indice}
    revisao = []
    for erro in dados["erros"]:
        caminho = erro["caminho_relativo"]
        if caminho.startswith("dataset/field/"):
            if caminho not in field:
                raise ValueError(f"metadado de campo ausente: {caminho}")
            meta = field[caminho]
            origem = "field"
        else:
            if Path(caminho).name not in agro:
                raise ValueError(f"rótulo AgroInsect ausente: {caminho}")
            meta = agro[Path(caminho).name]
            origem = "agroinsect"
        a = anotacoes["anotacoes"][erro["image_id"]]
        revisao.append({**erro, "grupo_particao": por_id[erro["image_id"]]["grupo_particao"],
            "origem": origem, "rotulo_na_fonte": meta["class_name"],
            "inat_obs_id": meta.get("inat_obs_id", ""),
            "observation_url": meta.get("observation_url", ""),
            "life_stage_metadado": meta.get("life_stage", ""),
            "estagio_visual": a[0], "fatores_observados": ";".join(a[1]),
            "hipoteses_de_causa": ";".join(a[2]) or "causa_indeterminada",
            "status_causa": "hipotese" if a[2] else "indeterminada",
            "validacao_taxonomica": "pendente", "observacao": a[3]})

    cobertura = []
    for i, nome in enumerate(dados["nomes"]):
        for particao in ("treino", "validacao", "teste"):
            linhas = [r for r in indice if int(r["indice_modelo"]) == i and r["particao"] == particao]
            campo = [r for r in linhas if r["caminho_relativo"].startswith("dataset/field/")]
            if any(r["caminho_relativo"] not in field for r in campo):
                raise ValueError("metadados de campo incompletos para o índice")
            metadados = [field[r["caminho_relativo"]] for r in campo]
            estagios = Counter(r.get("life_stage") or "sem_estagio" for r in metadados)
            if not set(estagios) <= ESTAGIOS:
                raise ValueError("estágio de metadado inesperado")
            cobertura.append({"indice_classe": i, "classe": nome, "particao": particao,
                "imagens": len(linhas), "grupos_particao": len({r["grupo_particao"] for r in linhas}),
                "imagens_field": len(campo), "imagens_agroinsect": len(linhas) - len(campo),
                "observacoes_inat": len({r["inat_obs_id"] for r in metadados if r["inat_obs_id"]}),
                **{f"field_{e}": estagios[e] for e in sorted(ESTAGIOS)}})
    treino = {r["indice_classe"]: r for r in cobertura if r["particao"] == "treino"}
    pares = []
    for i, j, quantidade, proporcao in dados["pares"]:
        fotos = [r for r in revisao if r["indice_real"] == i and r["indice_previsto"] == j]
        if len(fotos) != quantidade:
            raise ValueError("cobertura por par diverge da matriz")
        hipoteses = {h for r in fotos for h in r["hipoteses_de_causa"].split(";")}
        escassez = "nao_determinada"
        if "cobertura_estagio" in hipoteses:
            escassez = "hipotese_cobertura_estagio;nao_comprovada"
        pares.append({"indice_real": i, "classe_real": dados["nomes"][i],
            "indice_previsto": j, "classe_prevista": dados["nomes"][j],
            "erros": quantidade, "suporte_real": int(dados["suportes"][i]),
            "percentual_da_classe": f"{100*proporcao:.6f}", "principal": "sim" if quantidade >= 2 else "nao",
            "ids": ";".join(r["image_id"] for r in fotos),
            "grupos_particao_nos_erros": len({r["grupo_particao"] for r in fotos}),
            "observacoes_inat_nos_erros": len({r["inat_obs_id"] for r in fotos if r["inat_obs_id"]}),
            "erros_agroinsect": sum(r["origem"] == "agroinsect" for r in fotos),
            "treino_real_imagens": treino[i]["imagens"],
            "treino_real_grupos": treino[i]["grupos_particao"],
            "treino_prevista_imagens": treino[j]["imagens"],
            "treino_prevista_grupos": treino[j]["grupos_particao"],
            "rotulo_inconsistente": "suspeita_visual;validacao_pendente" if "rotulo_inconsistente" in hipoteses else "nao_demonstrado",
            "escassez_de_amostras": escassez,
            "semelhanca_visual_real": "hipotese_visual;nao_comprovada" if "semelhanca_visual" in hipoteses else "nao_demonstrada",
            "hipoteses_adicionais": ";".join(sorted(hipoteses - {"rotulo_inconsistente", "semelhanca_visual", "cobertura_estagio", "causa_indeterminada"})),
            "causa_confirmada": "nenhuma"})

    principais = [r for r in pares if r["principal"] == "sim"]
    suspeitos = [r["image_id"] for r in revisao if "rotulo_inconsistente" in r["hipoteses_de_causa"]]
    detalhes = []
    for i in sorted({r["indice_real"] for r in revisao if "cobertura_estagio" in r["hipoteses_de_causa"]}):
        t = treino[i]
        n = [r for r in revisao if r["indice_real"] == i and r["life_stage_metadado"] == "Nymph"]
        detalhes.append(f"- {dados['nomes'][i]}: treino com {t['imagens']} fotos em {t['grupos_particao']} grupos; "
            f"{t['field_Nymph']} fotos de campo marcadas Nymph e {t['field_sem_estagio']} sem estágio. "
            f"Há {len(n)} erros com metadado Nymph nesta revisão. Isso motiva investigar cobertura; "
            "não prova ausência real de ninfas no treino nem causalidade.")
    detalhes += [f"- {r['image_id']}: {r['observacao']}" for r in revisao if r['image_id'] in suspeitos]
    texto = ["# Análise de erros do candidato Keras FP32 — T6.3", "",
        f"{len(revisao)} erros inspecionados visualmente, distribuídos em {len(pares)} pares direcionais. "
        f"Os {len(principais)} pares com pelo menos dois erros reúnem {sum(r['erros'] for r in principais)} imagens.", "",
        anotacoes["metodo"], "",
        "As contagens vêm das previsões da T6.1 e da matriz da T6.2, sem nova inferência. "
        "Linhas são classes reais e colunas são previstas. Os rótulos reais são os do índice, não uma identificação taxonômica confirmada nesta revisão.", "",
        "## Principais pares e cobertura", "",
        "| Classe real → prevista | Erros / suporte | Observações iNaturalist nos erros | Fotos AgroInsect nos erros | Treino real: fotos / grupos |",
        "| --- | ---: | ---: | ---: | ---: |"]
    texto += [f"| {r['classe_real']} → {r['classe_prevista']} | {r['erros']} / {r['suporte_real']} | "
              f"{r['observacoes_inat_nos_erros']} | {r['erros_agroinsect']} | {r['treino_real_imagens']} / {r['treino_real_grupos']} |" for r in principais]
    texto += ["", "## Evidências que exigem conferência", "", *detalhes]
    texto += ["", "## Leitura dos indicadores", "",
        "- Rótulos: suspeitas visuais para conferência especializada: " + (", ".join(suspeitos) or "nenhuma") + ". Não houve relabelagem ou recálculo seletivo das métricas.",
        "- Escassez: cobertura_classes.csv apresenta as 13 classes em treino, validação e teste. Contagens de fotos e grupos não comprovam a causa de um erro. Metadado de estágio ausente não equivale a adulto, nem demonstra ausência de ninfas ou larvas.",
        "- Semelhança: as hipóteses visuais constam por imagem e por par. Não há confirmação de que semelhança taxonômica real tenha causado os erros.",
        "- Qualidade, estágio e múltiplos sujeitos são registrados separadamente; não são convertidos automaticamente em rótulo errado ou escassez.",
        "- Observações iNaturalist contam apenas a fonte field. Zero nessa coluna não significa ausência de exemplos: fotos AgroInsect não possuem esse identificador. Grupos do particionamento tampouco garantem indivíduos independentes.",
        "- A revisão é assistida por IA e exploratória, em teste consultado historicamente. Nenhuma causa foi confirmada por especialista. A análise do Keras não substitui a do TFLite INT8.", "",
        "## Artefatos", "",
        "- revisao_por_imagem.csv: todas as 72 fotos, caminho, hash, classe, grupo, metadados, observação visual, hipóteses e status.",
        "- analise_por_par.csv: todos os pares, inclusive os de um erro, com as três causas de interesse explicitamente avaliadas como hipótese ou não demonstradas.",
        "- cobertura_classes.csv: cobertura por partição; estágios referem-se apenas a metadados de campo, não a classificação visual automática do acervo.",
        "- anotacoes_visuais.json: registro da inspeção visual de origem; proveniencia.json vincula entradas, código e resultados por hashes.", ""]
    return {"revisao_por_imagem.csv": csv_texto(revisao), "analise_por_par.csv": csv_texto(pares),
            "cobertura_classes.csv": csv_texto(cobertura), "relatorio_erros.md": "\n".join(texto)}


def conferir_imagens(raiz: Path, erros: list[dict]) -> None:
    for r in erros:
        if matriz.hash_arquivo(raiz / r["caminho_relativo"]) != r["sha256_original"]:
            raise ValueError(f"imagem alterada: {r['image_id']}")


def executar(raiz: Path, verificar: bool = False) -> dict:
    prova_matriz = matriz.executar(verificar=True)
    dados = matriz.carregar(matriz.AVALIACAO, matriz.PACOTE, matriz.INDICE)
    conferir_imagens(raiz, dados["erros"])
    field_path, agro_path = raiz / "dataset/field/field_labels.csv", raiz / "dataset/labels.csv"
    field_rows, agro_rows = matriz.ler_csv(field_path), matriz.ler_csv(agro_path)
    field = {"dataset/field/" + r["filename"]: r for r in field_rows}
    agro = {r["filename"]: r for r in agro_rows}
    if len(field) != len(field_rows) or len(agro) != len(agro_rows):
        raise ValueError("caminhos de metadados duplicados")
    arquivos = construir(dados, matriz.ler_csv(matriz.INDICE), field, agro, matriz.ler_json(ANOTACOES))
    prova = {"esquema": "analise_candidato_T6_3_v1", "formato_avaliado": "Keras FP32",
        "modelo_sha256": dados["modelo_sha256"], "execucao_t5_5": dados["execucao_t5_5"],
        "total_erros_revisados": len(dados["erros"]), "metodo": "revisao_visual_assistida_por_IA",
        "validacao_especialista": False, "causas_confirmadas": False, "inferencia_repetida": False,
        "tipo_avaliacao": "exploratoria", "fontes_sha256": {**dados["fontes_sha256"],
            "proveniencia_T6_2": matriz.hash_arquivo(matriz.SAIDA / "proveniencia.json"),
            "field_labels.csv": matriz.hash_arquivo(field_path), "labels.csv": matriz.hash_arquivo(agro_path),
            "anotacoes_visuais.json": matriz.hash_arquivo(ANOTACOES)},
        "codigo_sha256": matriz.hash_arquivo(Path(__file__)),
        "minimo_erros_pares_principais": prova_matriz["minimo_erros_destaque"]}
    for nome, texto in arquivos.items():
        destino = SAIDA / nome
        if verificar:
            if destino.read_text(encoding="utf-8") != texto:
                raise ValueError(f"artefato divergente: {nome}")
        else:
            destino.write_text(texto, encoding="utf-8")
    prova["artefatos_sha256"] = {n: matriz.hash_arquivo(SAIDA / n) for n in arquivos}
    if verificar:
        if matriz.ler_json(SAIDA / "proveniencia.json") != prova:
            raise ValueError("proveniência divergente")
    else:
        (SAIDA / "proveniencia.json").write_text(json.dumps(prova, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return prova


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raiz-imagens", type=Path, required=True, help="raiz contendo dataset/")
    p.add_argument("--verificar", action="store_true")
    a = p.parse_args()
    resultado = executar(a.raiz_imagens, a.verificar)
    print(f"T6.3: {resultado['total_erros_revisados']} erros; "
          f"{'artefatos verificados' if a.verificar else 'análise publicada'}.")


if __name__ == "__main__":
    main()
