"""Calcula, para cada par de classes com confusão recorrente da T6.2, indicadores
objetivos sobre as três causas candidatas da T6.3: rótulos inconsistentes (estágio de
vida fora do esperado pelo nome da classe), escassez de amostras (poucas observações
independentes por trás das imagens de erro) e semelhança visual real entre os agentes
causais. Não decide sozinho a causa — isso exige abrir as fotos e está registrado em
`revisao_visual_pares.csv` — mas reduz o palpite ao fornecer contagens reprodutíveis.

Uso:
    python -m src.analise_erros_t6_3 --raiz-imagens "CAMINHO/Agro App" [--verificar]

Requer `dataset/field/field_labels.csv` dentro de `--raiz-imagens`, que não é
versionado neste repositório (ver `assets/data/avaliacao_T6_2` para os CSVs já
publicados que este script consome).
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

from .analise_confusao_t6_2 import PASTA as PASTA_T6_2, ler_classes

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "assets/data/avaliacao_T6_3"
PARES = PASTA_T6_2 / "pares_recorrentes_fp32.csv"
ERROS = PASTA_T6_2 / "erros_por_imagem_keras_3_modelos.csv"
SAIDA = PASTA / "estatisticas_por_par.csv"
SAIDA_REVISAO = PASTA / "revisao_visual_pares.csv"
ESTAGIOS = ["Adult", "Larva", "Nymph", "Pupa", "sem_estagio"]

# Revisão humana: cada foto abaixo foi aberta manualmente (não inferida das contagens
# agregadas) para a T6.3. "causas" usa o vocabulário fixo do critério de aceite:
# rotulo_inconsistente | escassez_de_amostras | semelhanca_visual_real (uma foto pode
# ter mais de uma, nessa ordem). Ver a seção 6.3 de docs/Projeto.md para a leitura
# completa por par.
REVISAO_VISUAL = {
    "IMG_01175": ("semelhanca_visual_real",
                  "Vaquinha adulta e Astylus variegatus de referência são besouros pequenos, de coloração "
                  "mosqueada amarelo/preto, fotografados sobre flor; silhueta e paleta muito próximas."),
    "IMG_01741": ("semelhanca_visual_real",
                  "Inseto minúsculo e distante no quadro (foto de flor, não de close-up); poucos pixels "
                  "cobrem o inseto, restando pouco detalhe diagnóstico para separar das duas classes."),
    "IMG_02978": ("rotulo_inconsistente",
                  "Classe 'Lagarta-falsa-medideira' (lagarta = larva), mas a foto mostra uma mariposa "
                  "adulta. life_stage vazio em field_labels.csv, confirmado visualmente como Adult."),
    "IMG_03037": ("rotulo_inconsistente",
                  "Mesma observação iNaturalist (inat396445719) do par IMG_02978; mariposa adulta sob o "
                  "rótulo de classe nomeada pela larva."),
    "IMG_02715": ("rotulo_inconsistente",
                  "Imagem do AgroInsect (classe 'spodoptera_frugiperda'), cuja documentação do dataset "
                  "(instruções.md) registra que essa classe contém só mariposas adultas, nunca lagartas."),
    "IMG_03384": ("rotulo_inconsistente;semelhanca_visual_real",
                  "Mariposa adulta de Spodoptera eridania segurada na mão; visualmente quase idêntica à "
                  "mariposa de Chrysodeixis includens (IMG_03037): corpo pardo/acinzentado, pouso triangular."),
    "IMG_02091": ("escassez_de_amostras",
                  "Dichelops/Diceraeus tem só 14 fotos de campo (2 com life_stage preenchido); "
                  "instruções.md já sinaliza a classe como fraca por poucas fotos de campo."),
    "IMG_02271": ("semelhanca_visual_real",
                  "Percevejo castanho sobre folha de milho; porte e coloração compatíveis tanto com "
                  "Dichelops/Diceraeus quanto com Leptoglossus zonatus à distância da foto."),
    "IMG_01071": ("semelhanca_visual_real",
                  "Vaquinha adulta pequena e distante sobre folha, pouca saturação de cor visível; "
                  "sem as manchas alaranjadas nítidas que diferenciam o inseto do percevejo-verde."),
    "IMG_03088": ("escassez_de_amostras;semelhanca_visual_real",
                  "Ninfa de Edessa meditabunda (life_stage=Nymph); ninfas de percevejos pentatomídeos "
                  "convergem num padrão preto/branco/vermelho bem diferente da cor do respectivo adulto, "
                  "e só 8 das 75 fotos de campo da classe são ninfas."),
}


def ler_pares() -> list[dict[str, str]]:
    with PARES.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))
    if not linhas:
        raise ValueError("pares_recorrentes_fp32.csv vazio")
    return linhas


def ler_erros() -> list[dict[str, str]]:
    with ERROS.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    if len(linhas) != 177:
        raise ValueError("erros_por_imagem_keras_3_modelos.csv deveria ter 177 fotos")
    return linhas


def ler_field_labels(raiz_imagens: Path) -> dict[str, dict[str, str]]:
    caminho = raiz_imagens / "dataset/field/field_labels.csv"
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    por_caminho = {f"dataset/field/{linha['filename']}": linha for linha in linhas}
    if len(por_caminho) != len(linhas):
        raise ValueError("field_labels.csv tem caminhos duplicados")
    return por_caminho


def histograma_estagio(classe: str, field_labels: dict[str, dict[str, str]]) -> dict[str, int]:
    contagem = {estagio: 0 for estagio in ESTAGIOS}
    for linha in field_labels.values():
        if linha["class_name"] != classe:
            continue
        estagio = linha.get("life_stage") or "sem_estagio"
        if estagio not in contagem:
            raise ValueError(f"estágio de vida inesperado: {estagio}")
        contagem[estagio] += 1
    return contagem


def pastas_da_classe(classe_com_nome_comum: str, classes_modelo: list[str], pastas: list[list[str]]) -> list[str]:
    indice = classes_modelo.index(classe_com_nome_comum)
    return pastas[indice]


def histograma_estagio_classe(
    pastas: list[str], field_labels: dict[str, dict[str, str]]
) -> dict[str, int]:
    total = {estagio: 0 for estagio in ESTAGIOS}
    for pasta in pastas:
        parcial = histograma_estagio(pasta, field_labels)
        for estagio, quantidade in parcial.items():
            total[estagio] += quantidade
    return total


def calcular_par(
    par: dict[str, str], erros: list[dict[str, str]], field_labels: dict[str, dict[str, str]],
    classes_modelo: list[str], pastas_por_classe: list[list[str]],
) -> dict[str, object]:
    real, prevista = par["classe_real"], par["classe_prevista"]
    na_fila = [linha for linha in erros if linha["classe_real"] == real and prevista in linha["previsoes_erradas"]]
    origem_field = [linha for linha in na_fila if linha["caminho_relativo"] in field_labels]
    observacoes = {field_labels[linha["caminho_relativo"]]["inat_obs_id"] for linha in origem_field}
    linha = {
        "classe_real": real, "classe_prevista": prevista,
        "suporte_real": int(par["suporte_real"]),
        "imagens_na_fila_de_erro": len(na_fila),
        "imagens_na_fila_origem_field": len(origem_field),
        "imagens_na_fila_origem_agroinsect": len(na_fila) - len(origem_field),
        "observacoes_inat_distintas_na_fila": len(observacoes),
    }
    pastas_real = pastas_da_classe(real, classes_modelo, pastas_por_classe)
    pastas_prevista = pastas_da_classe(prevista, classes_modelo, pastas_por_classe)
    for prefixo, pastas in (("real", pastas_real), ("prevista", pastas_prevista)):
        for estagio, quantidade in histograma_estagio_classe(pastas, field_labels).items():
            linha[f"{prefixo}_{estagio.lower()}"] = quantidade
    return linha


def gerar_revisao_visual(pares: list[dict[str, str]], erros: list[dict[str, str]]) -> str:
    por_id = {linha["image_id"]: linha for linha in erros}
    pares_validos = {(par["classe_real"], par["classe_prevista"]) for par in pares}
    linhas = []
    for image_id, (causas, observacao) in REVISAO_VISUAL.items():
        if image_id not in por_id:
            raise ValueError(f"{image_id} não está na fila de erros da T6.2")
        erro = por_id[image_id]
        par_imagem = next(
            ((real, prevista) for real, prevista in pares_validos
             if erro["classe_real"] == real and prevista in erro["previsoes_erradas"]),
            None,
        )
        if par_imagem is None:
            raise ValueError(f"{image_id} não corresponde a nenhum par recorrente da T6.2")
        linhas.append({
            "image_id": image_id,
            "caminho_relativo": erro["caminho_relativo"],
            "classe_real": par_imagem[0],
            "classe_prevista": par_imagem[1],
            "causas_identificadas": causas,
            "observacao_revisao": observacao,
        })
    linhas.sort(key=lambda linha: (linha["classe_real"], linha["classe_prevista"], linha["image_id"]))
    saida = io.StringIO(newline="")
    escritor = csv.DictWriter(
        saida,
        fieldnames=["image_id", "caminho_relativo", "classe_real", "classe_prevista",
                    "causas_identificadas", "observacao_revisao"],
        lineterminator="\n",
    )
    escritor.writeheader()
    escritor.writerows(linhas)
    return saida.getvalue()


def gerar_csv(linhas: list[dict[str, object]]) -> str:
    colunas: list[str] = []
    for linha in linhas:
        for chave in linha:
            if chave not in colunas:
                colunas.append(chave)
    saida = io.StringIO(newline="")
    escritor = csv.DictWriter(saida, fieldnames=colunas, restval=0, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(linhas)
    return saida.getvalue()


def executar(raiz_imagens: Path, verificar: bool = False) -> None:
    classes_modelo = ler_classes()
    with (RAIZ / "assets/data/classes-modelo.csv").open(encoding="utf-8-sig", newline="") as arquivo:
        resumo = list(csv.DictReader(arquivo, delimiter=";"))
    if [int(linha["indice_modelo"]) for linha in resumo] != list(range(len(classes_modelo))):
        raise ValueError("classes-modelo.csv fora de ordem")
    pastas_por_classe = [linha["nomes_inventario"].split(";") for linha in resumo]
    pares = ler_pares()
    erros = ler_erros()
    field_labels = ler_field_labels(raiz_imagens)
    linhas = [calcular_par(par, erros, field_labels, classes_modelo, pastas_por_classe) for par in pares]
    conteudo = gerar_csv(linhas)
    conteudo_revisao = gerar_revisao_visual(pares, erros)
    PASTA.mkdir(parents=True, exist_ok=True)
    saidas = {SAIDA: conteudo, SAIDA_REVISAO: conteudo_revisao}
    for caminho, texto in saidas.items():
        if verificar:
            if caminho.read_text(encoding="utf-8") != texto:
                raise ValueError(f"Artefato divergente: {caminho}")
        else:
            caminho.write_text(texto, encoding="utf-8", newline="\n")
    modo = "verificados" if verificar else "gerados"
    print(f"T6.3: {len(linhas)} pares recorrentes, {len(REVISAO_VISUAL)} fotos revisadas; artefatos {modo}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-imagens", type=Path, required=True)
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    executar(args.raiz_imagens, args.verificar)
