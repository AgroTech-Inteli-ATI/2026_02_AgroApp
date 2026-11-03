"""Calcula, para cada par de classes com confusão recorrente da T6.2, indicadores
objetivos sobre as causas candidatas da T6.3: rótulos taxonômicos inconsistentes,
escassez de amostras (poucas observações
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
ESTAGIOS = ["Adult", "Larva", "Nymph", "Pupa", "Egg", "sem_estagio"]
CAUSAS = {"rotulo_inconsistente", "escassez_de_amostras", "semelhanca_visual_real",
          "variacao_estagio_de_vida", "qualidade_imagem", "conteudo_multiplos_insetos",
          "causa_indeterminada"}

# Revisão humana: cada foto abaixo foi aberta manualmente (não inferida das contagens
# agregadas) na revisão original da T6.3. As anotações são hipóteses, não validação
# agronômica. Um adulto pode ter o rótulo de espécie correto mesmo que o nome comum
# mencione a larva. Categorias adicionais evitam forçar qualidade de imagem ou
# variação de estágio a uma suposta inconsistência taxonômica. As 48 fotos geram
# 49 relações foto/par; uma foto pode aparecer em mais de um par.
REVISAO_VISUAL = {
    "IMG_00994": ("semelhanca_visual_real",
                  "Vaquinha adulta nítida sobre pétala rosa; mesma leitura das demais fotos do par — a boa qualidade não permite isolar a causa do erro; semelhança visual é hipótese."),
    "IMG_01012": ("semelhanca_visual_real",
                  "Vaquinha adulta em foco nítido sobre flor amarela; pose e paleta (verde/oliva com manchas amarelas) próximas às de Astylus mesmo sem problema de nitidez."),
    "IMG_01069": ("qualidade_imagem",
                  "Terceira foto da mesma observação (inat185718390): mesmo padrão de inseto minúsculo e distante no quadro."),
    "IMG_01070": ("qualidade_imagem",
                  "Mesma observação iNaturalist do já revisado IMG_01071 (inat185718390): vaquinha pequena e distante sobre folha, sem detalhe suficiente para diferenciar do percevejo-verde."),
    "IMG_01071": ("qualidade_imagem",
                  "Vaquinha adulta pequena e distante sobre folha, pouca saturação de cor visível; sem as manchas alaranjadas nítidas que diferenciam o inseto do percevejo-verde."),
    "IMG_01175": ("conteudo_multiplos_insetos;causa_indeterminada",
                  "Foto da observação iNaturalist 254992883 com mais de um inseto: um besouro na parte inferior e um inseto alado listrado em destaque. A identidade deste último não foi confirmada; não usar a imagem como evidência de um Astylus junto da vaquinha. A presença de mais de um sujeito pode interferir na classificação da foto inteira."),
    "IMG_01176": ("conteudo_multiplos_insetos;causa_indeterminada",
                  "Foto da observação iNaturalist 254992883 com mais de um inseto: um besouro na parte inferior e um inseto alado listrado em destaque. A identidade deste último não foi confirmada; não usar a imagem como evidência de um Astylus junto da vaquinha. A presença de mais de um sujeito pode interferir na classificação da foto inteira."),
    "IMG_01217": ("semelhanca_visual_real",
                  "Vaquinha com coloração alaranjada/listrada (variação de cor da espécie) fotografada de perto; padrão mosqueado se aproxima do de Astylus mesmo em foto nítida."),
    "IMG_01420": ("semelhanca_visual_real",
                  "Vaquinha adulta em foco sobre flor laranja; padrão de manchas e porte semelhantes aos de Astylus mesmo com boa resolução da foto."),
    "IMG_01466": ("qualidade_imagem",
                  "Inseto pequeno e distante no quadro, com pouco detalhe diagnóstico; a dificuldade de enquadramento não comprova semelhança real entre as espécies."),
    "IMG_01485": ("semelhanca_visual_real",
                  "Vaquinha nítida sobre flor roxa, boa iluminação e foco; reforça que a confusão com Astylus não depende de fotos de baixa qualidade."),
    "IMG_01516": ("semelhanca_visual_real",
                  "Vaquinha em foco sobre flor laranja, bem enquadrada; semelhança de porte/padrão com Astylus é hipótese; qualidade não isola outras causas."),
    "IMG_01669": ("semelhanca_visual_real",
                  "Macro muito nítida de vaquinha sobre flor azul, mesma coloração mosqueada que aproxima a classe de Astylus."),
    "IMG_01717": ("semelhanca_visual_real",
                  "Vaquinha nítida sobre folha verde (origem AgroInsect), close-up de boa qualidade; mesma leitura de semelhança visual real com Astylus."),
    "IMG_01741": ("qualidade_imagem",
                  "Inseto minúsculo e distante no quadro (foto de flor, não de close-up); poucos pixels cobrem o inseto, restando pouco detalhe diagnóstico para separar das duas classes."),
    "IMG_01851": ("semelhanca_visual_real",
                  "Foto nítida e bem enquadrada de vaquinha adulta sobre flor azul (origem AgroInsect); o erro com Astylus foi observado apesar da boa qualidade; a causa permanece hipótese."),
    "IMG_01894": ("qualidade_imagem",
                  "Vaquinha pequena fotografada de longe sobre folha grande; mesmo padrão de imagem de baixa qualidade diagnóstica dos demais erros deste par."),
    "IMG_02030": ("qualidade_imagem",
                  "Inseto escuro e pequeno, parcialmente nas sombras entre folhas; pouco detalhe de cor/forma disponível para diferenciar as classes."),
    "IMG_02091": ("escassez_de_amostras",
                  "Dichelops/Diceraeus tem só 14 fotos de campo (2 com life_stage preenchido); instruções.md já sinaliza a classe como fraca por poucas fotos de campo."),
    "IMG_02123": ("semelhanca_visual_real",
                  "Foto registrada como nítida e bem enquadrada de percevejo castanho sobre colmo de milho. Semelhança de porte/cor é hipótese, não identificação taxonômica confirmada nem prova isolada da causa do erro."),
    "IMG_02217": ("qualidade_imagem",
                  "Percevejo castanho parcialmente encoberto por folhas de milho; silhueta pouco visível soma-se à semelhança de porte/cor com Leptoglossus."),
    "IMG_02271": ("semelhanca_visual_real",
                  "Percevejo castanho sobre folha de milho; porte e coloração compatíveis tanto com Dichelops/Diceraeus quanto com Leptoglossus zonatus à distância da foto."),
    "IMG_02312": ("qualidade_imagem",
                  "Foto em close extremo que corta o contorno do inseto, ocultando a silhueta característica que normalmente diferencia os dois percevejos castanhos."),
    "IMG_02546": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02673": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02715": ("variacao_estagio_de_vida;causa_indeterminada",
                  "Adulto da classe Spodoptera frugiperda, fonte AgroInsect. A documentação da fonte declara que suas fotos dessa classe são de adultos; o nome comum 'lagarta-do-cartucho' não define uma classe exclusivamente larval."),
    "IMG_02741": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02814": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02972": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02973": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02974": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_02978": ("variacao_estagio_de_vida;causa_indeterminada",
                  "Mariposa adulta; life_stage ausente no metadado. Observação iNaturalist 10704962, diferente de IMG_03035–IMG_03037 (396445719). Fase adulta não comprova erro no rótulo de espécie."),
    "IMG_03007": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03008": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03035": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03036": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03037": ("variacao_estagio_de_vida;causa_indeterminada",
                  "Mariposa adulta da observação iNaturalist 396445719, compartilhada com IMG_03035 e IMG_03036. IMG_02978 pertence a 10704962, não ao mesmo indivíduo. Fase adulta não comprova erro taxonômico."),
    "IMG_03086": ("escassez_de_amostras;semelhanca_visual_real",
                  "Mesma observação iNaturalist do já revisado IMG_03088 (inat147542055): ninfa de Edessa meditabunda, padrão preto/branco/vermelho típico de ninfas de pentatomídeos."),
    "IMG_03088": ("escassez_de_amostras;semelhanca_visual_real",
                  "Ninfa de Edessa meditabunda (life_stage=Nymph); ninfas de percevejos pentatomídeos convergem num padrão preto/branco/vermelho bem diferente da cor do respectivo adulto, e só 8 das 75 fotos de campo da classe são ninfas."),
    "IMG_03090": ("escassez_de_amostras;semelhanca_visual_real",
                  "Quarta foto da mesma observação (inat147542055): mesma ninfa, reforça que a 'recorrência' é um único espécime fotografado várias vezes."),
    "IMG_03091": ("escassez_de_amostras;semelhanca_visual_real",
                  "Terceira foto da mesma observação (inat147542055): mesma ninfa em outro ângulo."),
    "IMG_03106": ("escassez_de_amostras;semelhanca_visual_real",
                  "Observação iNaturalist diferente (inat198202850): ninfa em estágio mais avançado (pré-asas visíveis), ainda sem a coloração definitiva do adulto que diferenciaria a espécie."),
    "IMG_03304": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03384": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03414": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03424": ("semelhanca_visual_real",
                  "Duas larvas escuras sobre banana. A semelhança visual entre larvas é uma hipótese para o erro; a foto não permite confirmar por si só espécies diferentes nem rótulo incorreto."),
    "IMG_03446": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
    "IMG_03447": ("variacao_estagio_de_vida;causa_indeterminada",
                  "A revisão visual registra uma mariposa adulta nesta foto. A classe identifica a espécie, não apenas a larva; a fase adulta não comprova rótulo taxonômico incorreto. Avaliar cobertura dos estágios e o escopo do MVP com o parceiro."),
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


def gerar_revisao_visual(
    pares: list[dict[str, str]], erros: list[dict[str, str]],
    field_labels: dict[str, dict[str, str]],
) -> str:
    por_id = {linha["image_id"]: linha for linha in erros}
    if len(por_id) != len(erros):
        raise ValueError("ID repetido na fila de erros")
    pares_validos = sorted({(par["classe_real"], par["classe_prevista"]) for par in pares})
    esperadas = {(erro["image_id"], real, prevista) for erro in erros
                 for real, prevista in pares_validos
                 if erro["classe_real"] == real and prevista in erro["previsoes_erradas"]}
    if {i for i, _, _ in esperadas} != set(REVISAO_VISUAL):
        raise ValueError("revisão não cobre exatamente as fotos dos pares recorrentes")
    linhas = []
    for image_id, real, prevista in sorted(esperadas):
        causas, observacao = REVISAO_VISUAL[image_id]
        if not causas or not set(causas.split(";")) <= CAUSAS or not observacao.strip():
            raise ValueError(f"{image_id}: causas ou observação inválidas")
        erro = por_id[image_id]
        metadado = field_labels.get(erro["caminho_relativo"], {})
        linhas.append({
            "image_id": image_id,
            "caminho_relativo": erro["caminho_relativo"],
            "classe_real": real,
            "classe_prevista": prevista,
            "inat_obs_id": metadado.get("inat_obs_id", ""),
            "life_stage_metadado": metadado.get("life_stage", ""),
            "causas_identificadas": causas,
            "status_causa": "indeterminada" if "causa_indeterminada" in causas else "hipotese",
            "observacao_revisao": observacao,
        })
    linhas.sort(key=lambda linha: (linha["classe_real"], linha["classe_prevista"], linha["image_id"]))
    saida = io.StringIO(newline="")
    escritor = csv.DictWriter(
        saida,
        fieldnames=["image_id", "caminho_relativo", "classe_real", "classe_prevista",
                    "inat_obs_id", "life_stage_metadado", "causas_identificadas",
                    "status_causa", "observacao_revisao"],
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
    conteudo_revisao = gerar_revisao_visual(pares, erros, field_labels)
    if not verificar:
        PASTA.mkdir(parents=True, exist_ok=True)
    saidas = {SAIDA: conteudo, SAIDA_REVISAO: conteudo_revisao}
    for caminho, texto in saidas.items():
        if verificar:
            if caminho.read_text(encoding="utf-8") != texto:
                raise ValueError(f"Artefato divergente: {caminho}")
        else:
            caminho.write_text(texto, encoding="utf-8", newline="\n")
    modo = "verificados" if verificar else "gerados"
    relacoes = len(list(csv.DictReader(io.StringIO(conteudo_revisao))))
    print(f"T6.3: {len(linhas)} pares recorrentes, {len(REVISAO_VISUAL)} fotos anotadas, "
          f"{relacoes} relações foto/par; artefatos {modo}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-imagens", type=Path, required=True)
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    executar(args.raiz_imagens, args.verificar)
