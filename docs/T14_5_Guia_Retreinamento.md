# Guia de retreinamento e atualização do modelo

Autor: Rui · Revisora: Karol.

Este guia reúne o procedimento de manutenção para a equipe do Agro App: receber novas imagens, congelar dados, treinar, avaliar, converter, integrar e reverter a aplicação. O fluxo mantém **as mesmas 13 classes e entrada RGB 224 × 224**. Alterar classes, formato de entrada ou política exige uma revisão de contrato, catálogo, testes e conteúdo, fora deste procedimento.

**Não houve novo treinamento nem publicação de modelo nesta entrega.** Os exemplos de campanha são caminhos novos, não resultados já produzidos. A conferência técnica dos comandos não substitui a execução por participante externo prevista na validação do guia. O modelo oficial permanece o candidato `candidato_T5_6_20261026`, versão 1.0.0, Float16 principal e INT8 de contingência.

## 1. Preparar ambiente e preservar a versão anterior

Use um checkout dedicado, Git, PowerShell (versão 7 em macOS/Linux), Python 3.12, Node.js 22.12+ e npm, conforme [ambiente e dependências](T14_2_Pipeline_Treinamento.md#ambiente). Execute os blocos Python abaixo **na raiz do repositório**. Em Windows, os comandos usam `py`; em macOS/Linux, crie o ambiente com `python3.12 -m venv .venv` e ajuste `$python` para `.venv/bin/python`. O restante usa PowerShell em ambos os casos. Se qualquer comando terminar com erro ou código de saída diferente de zero, pare e resolva a causa antes do próximo passo; não publique saídas parciais.

```powershell
git status --short
# Continue em um checkout limpo; preserve/commite seu trabalho antes de atualizar.
git switch develop
git pull --ff-only
git switch -c manutencao/modelo-1-1-0
py -3.12 -m venv .venv
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install -r requirements-treino.txt
$env:KERAS_BACKEND = "tensorflow"
$env:PYTHONUTF8 = "1"
$imagens = "C:\dados\agroapp"
$campanha = "assets/modelos/retreinamento_1_1_0"
New-Item -ItemType Directory -Path $campanha
```

`1.1.0` é exemplo de **nova** versão; escolha outro identificador se a pasta já existir. Guarde commit, ambiente, comandos executados e decisões na campanha. As imagens ficam fora do Git, com seus caminhos relativos preservados no acervo entregue separadamente. O primeiro uso dos pesos ImageNet exige internet ou cache do KerasHub. O treino carrega treino e validação em RAM: confirme recursos antes de iniciar.

Preserve o pacote **realmente publicado** anterior: pasta `site` inteira, `release.json`, arquivo compactado e checksum, junto com a URL/caminho de publicação e o commit correspondente. Não substitua essa evidência por um build novo. Se ainda não há pacote congelado, no checkout da versão vigente:

```powershell
Push-Location frontend
npm.cmd ci
npm.cmd run demo:package
# Substitua pelo caminho impresso pelo comando anterior:
npm.cmd run demo:verify -- .work/demo/IDENTIFICADOR_GERADO/site
Pop-Location
```

Copie o pacote para o armazenamento de entregas da equipe, fora de `.work` e do computador de uma única pessoa. `demo:verify` verifica integridade; não atesta aprovação agronômica ou latência. O empacotador aceita os papéis Float16/INT8 e os identificadores de protocolo T7.2/T7.3; esses campos não são a versão comercial do novo modelo.

## 2. Receber, revisar e congelar os dados

Antes de criar o índice:

- Obtenha as imagens originais, rótulos revisados, origem, autor/crédito, licença e autorização de uso. Preserve o arquivo recebido; não use a extensão como prova de formato. O acervo histórico inclui um GIF com extensão `.jpg`.
- Mantenha os índices 0–12 e os nomes de [classes.json](../assets/modelos/candidato_T5_6_20261026/classes.json). Imagens sem rótulo confiável ou fora dessas classes ficam em quarentena, fora do treino.
- Identifique fotos da mesma observação, planta/cena e suas cópias recortadas ou alteradas. Elas precisam do mesmo `grupo_particao`, mesmo com hashes diferentes. Hash não detecta sozinho cópias transformadas. Use a [auditoria de independência](../assets/data/independencia_T10_1/README.md) como referência; seus grupos históricos não auditam automaticamente o novo acervo.
- Atribua **o grupo inteiro** a `treino`, `validacao` ou `teste`. Busque proporção próxima de 70/15/15 sem quebrar grupos, registrando o critério e a semente usada na atribuição. Treino e validação precisam das 13 classes neste fluxo: o comparador executa uma foto de validação por classe. Registre classes com pouco ou nenhum suporte no teste; se faltar uma classe na validação, obtenha dados antes de usar esse comparador.
- Um teste independente deve conter grupos novos, reservados antes do treino e sem uso na escolha de modelo, hiperparâmetros ou limiar. Redistribuir o teste histórico ou retirar duas duplicatas não restaura independência. Sem dados novos reservados, declare a avaliação exploratória.

A ficha [T14.1, PR #56](https://github.com/AgroTech-Inteli-ATI/2026_02_AgroApp/pull/56) documenta o recorte histórico de **3.156 imagens: 2.209/474/473**. A T14.2 explica por que os defaults antigos recompõem **3.163**. Não rode T4.5 para importar fotos novas nem altere o índice histórico para acomodá-las.

Crie `$campanha/inventario_revisado.csv` em UTF-8, uma linha por imagem aprovada, com estas colunas:

| Coluna | Preenchimento |
| --- | --- |
| `image_id` | Identificador único, estável, sem reciclar IDs para outros arquivos. |
| `caminho_relativo` | Caminho a partir de `$imagens`, usando `/`; sem caminho absoluto ou `..`. |
| `indice_modelo`, `nome_classe_modelo` | Índice e nome exatos do catálogo. |
| `grupo_particao`, `particao` | Grupo revisado e uma das três partições. |
| `origem`, `licenca`, `credito` | Proveniência real e autorização/crédito documentados; não inferir licença pelo download. |

Inclua na campanha um registro de revisão de rótulos/grupos, responsável, data, exclusões e reserva do teste. Não preencha aprovação que ainda não ocorreu. O bloco abaixo **não decide rótulos, grupos ou partições**: valida o CSV revisado, confere originais, calcula hashes/pesos e cria o contrato para o treino. Recusa saída existente.

```powershell
@'
import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path
from src.preprocessamento import preparar_imagem

raiz, campanha = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
out = campanha / "dados"
if out.exists():
    raise ValueError("dados já existem; use outra campanha")
classes = json.loads(Path("assets/modelos/candidato_T5_6_20261026/classes.json").read_text(encoding="utf-8"))
config = json.loads(Path("assets/modelos/candidato_T5_6_20261026/configuracao_treino.json").read_text(encoding="utf-8"))
with (campanha / "inventario_revisado.csv").open(encoding="utf-8-sig", newline="") as f:
    linhas = list(csv.DictReader(f))
if not linhas:
    raise ValueError("inventário vazio")
ids, hashes, grupos, indice = set(), set(), {}, []
for r in linhas:
    i = int(r["indice_modelo"])
    if not 0 <= i < 13 or r["nome_classe_modelo"] != classes[i]["nome"]:
        raise ValueError("rótulo incompatível: " + r["image_id"])
    if not all(r[k].strip() for k in ("image_id", "grupo_particao", "origem", "licenca", "credito")):
        raise ValueError("faltam identificação ou proveniência")
    p = (raiz / r["caminho_relativo"]).resolve()
    if not p.is_relative_to(raiz) or Path(r["caminho_relativo"]).is_absolute() or ".." in Path(r["caminho_relativo"]).parts:
        raise ValueError("caminho fora do acervo")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    preparar_imagem(p)  # EXIF, imagem opaca, RGB e contrato T10.2; não altera o original.
    grupo, part = r["grupo_particao"], r["particao"]
    if part not in {"treino", "validacao", "teste"} or grupos.get(grupo, part) != part:
        raise ValueError("partição inválida ou grupo compartilhado")
    if r["image_id"] in ids or h in hashes:
        raise ValueError("ID ou fotografia byte a byte repetida")
    ids.add(r["image_id"]); hashes.add(h); grupos[grupo] = part
    indice.append({k: r[k] for k in ("image_id", "caminho_relativo", "indice_modelo", "nome_classe_modelo", "grupo_particao", "particao")})
    indice[-1].update(sha256_original=h, semente_augmentation=str(int(h[:16], 16)) if part == "treino" else "")
contagem = Counter(int(r["indice_modelo"]) for r in indice if r["particao"] == "treino")
classes_val = {int(r["indice_modelo"]) for r in indice if r["particao"] == "validacao"}
if set(contagem) != set(range(13)) or classes_val != set(range(13)) or not any(r["particao"] == "teste" for r in indice):
    raise ValueError("exigidos treino/validação com 13 classes e teste não vazio")
out.mkdir()
with (out / "indice.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(indice[0]), lineterminator="\n"); w.writeheader(); w.writerows(indice)
pesos = {"formula": "N / (K * n_c)", "total_treino": sum(contagem.values()), "quantidade_classes": 13,
         "classes": {str(i): {"nome_classe": classes[i]["nome"], "imagens_treino": contagem[i],
                              "peso": sum(contagem.values()) / (13 * contagem[i])} for i in range(13)}}
for nome, valor in (("pesos.json", pesos), ("classes.json", classes), ("config.json", config)):
    (out / nome).write_text(json.dumps(valor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("Contrato criado:", out, Counter(r["particao"] for r in indice))
'@ | & $python - $imagens $campanha
```

Revise as contagens por classe, fonte e partição, o suporte minoritário e a reserva do teste antes de continuar. A semente por imagem não cria partições nem garante igualdade entre plataformas. O preprocessing não usa augmentation; durante o treino, augmentation é controlado pela configuração e nunca aplicado à validação/teste. A configuração copiada mantém EfficientNet-Lite0, semente 42, class weights e augmentation desabilitado, como no candidato. Registre qualquer mudança antes da rodada.

Congele e versione inventário, índice, classes, pesos, configuração e registro de revisão **antes de treinar**. Calcule seus SHA-256 com `Get-FileHash -Algorithm SHA256 CAMINHO`. Não altere arquivos de uma campanha já executada: uma mudança de rótulo, arquivo ou partição origina outra versão.

## 3. Treinar e escolher o checkpoint pela validação

```powershell
& $python -m src.treinamento_t5_1 --config "$campanha/dados/config.json" --raiz-imagens $imagens --indice "$campanha/dados/indice.csv" --pesos "$campanha/dados/pesos.json" --saida "$campanha/rodadas"
# Copie o caminho exato impresso pelo treinamento, não a pasta-pai:
$rodada = "$campanha/rodadas/SUBSTITUIR_PELA_RODADA_GERADA"
```

Exija a pasta completa: `melhor_modelo.keras`, `config_usada.json`, `ambiente.json`, `historico.csv` e `metricas_validacao.json`. O treino só carrega treino/validação; o teste permanece reservado. Confira hashes de índice e pesos no ambiente, curvas por época, melhor época, F1 macro, recall/F1 das classes minoritárias e diferença treino/validação. Métricas altas no treino e queda persistente na validação são sinal para investigação, não prova isolada de overfitting. O comando não gera uma análise automática desse fenômeno.

Compare rodadas da **mesma versão dos dados**, incluindo tentativas descartadas, usando [registro T5.5](../src/registro_experimentos_t5_5.py), com saídas próprias:

```powershell
& $python -m src.registro_experimentos_t5_5 --entrada "$campanha/rodadas" --saida "$campanha/registro"
```

Escolha pelo desempenho de validação, por classe, tamanho e medições no aparelho; não pelo teste. Não existe obrigação de refazer a varredura histórica de três arquiteturas para toda atualização. Registre em `$campanha/decisao_checkpoint.md` a rodada escolhida, alternativas/descartes, seus hashes e justificativa. Se os resultados forem insuficientes, conserve a versão vigente.

Crie um **pacote de candidato novo**, usando o esquema aceito pelos conversores. O nome de esquema é um contrato técnico legado, não uma declaração de que a nova rodada foi a vencedora histórica T5.6. O bloco exige o vínculo entre rodada e novo índice/pesos, preserva os cinco artefatos e registra hashes; a decisão humana permanece no arquivo anterior.

```powershell
@'
import hashlib, json, shutil, sys
from pathlib import Path
campanha, rodada = map(Path, sys.argv[1:3])
ler = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pacote = campanha / "pacote"
if pacote.exists(): raise ValueError("pacote já existe")
if not (campanha / "decisao_checkpoint.md").is_file(): raise ValueError("registre a escolha pela validação")
ambiente, metricas = ler(rodada / "ambiente.json"), ler(rodada / "metricas_validacao.json")
classes = ler(campanha / "dados/classes.json")
assert ambiente["sha256"]["indice_pipeline"] == h(campanha / "dados/indice.csv")
assert ambiente["sha256"]["pesos_classes"] == h(campanha / "dados/pesos.json")
assert [{"indice": c["indice"], "nome": c["nome"]} for c in metricas["validacao"]["por_classe"]] == classes
pacote.mkdir()
for origem, destino in (("melhor_modelo.keras", "modelo.keras"), ("config_usada.json", "configuracao_treino.json"),
                        ("ambiente.json", "ambiente_treino.json"), ("historico.csv", "historico.csv"),
                        ("metricas_validacao.json", "avaliacao_validacao.json")):
    shutil.copy2(rodada / origem, pacote / destino)
shutil.copy2(campanha / "dados/classes.json", pacote / "classes.json")
manifesto = {"esquema": "selecao_T5_6_v1", "status": "candidato_em_validacao", "arquitetura": metricas["backbone"],
             "execucao_t5_5": rodada.resolve().relative_to((campanha / "rodadas").resolve()).as_posix(),
             "indice_sha256": ambiente["sha256"]["indice_pipeline"], "pesos_sha256": ambiente["sha256"]["pesos_classes"],
             "decisao_checkpoint_sha256": h(campanha / "decisao_checkpoint.md"),
             "sha256": {p.name: h(p) for p in pacote.iterdir()}}
(pacote / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("Candidato preparado:", pacote)
'@ | & $python - $campanha $rodada
```

## 4. Converter e comparar sem consultar o teste

Passe **todos** os caminhos da campanha. Não use os defaults dos conversores, da T8.3 ou da T11.1 para um modelo/dataset novo: eles apontam para a versão histórica. A T11.1 recusa índices que não sejam o auditado na T10.1. A publicação T5.6 também impõe sua comparação de três arquiteturas; não é o procedimento genérico de atualização.

```powershell
& $python -m src.conversao_t7_1 --rodada $rodada --pacote "$campanha/pacote" --saida "$campanha/fp32"
& $python -m src.quantizacao_t7_3 preparar --raiz-imagens $imagens --indice "$campanha/dados/indice.csv" --pacote "$campanha/pacote" --saida "$campanha/calibracao" --total 200 --semente 42
```

A calibração usa **somente treino**, sem augmentation, 13 classes e grupos/hashes distintos. É necessário dispor de treino suficiente; o programa recusa uma seleção impossível. Revise as 200 escolhas. O campo `origem` gerado pela T7.3 distingue caminhos iniciados por `dataset/field/` dos demais; para novas fontes ele é uma **heurística de pasta**, não prova de que a foto veio do AgroInsect. Preserve a origem real no inventário e registre essa limitação no conjunto, sem adulterar os hashes do manifesto.

Crie `$campanha/calibracao/revisao_iluminacao.json` após inspeção visual dos novos IDs. Use o [registro histórico](../assets/data/calibracao_T7_3/revisao_iluminacao.json) como **esquema**, sem copiar observações, IDs ou alegar que a inspeção já ocorreu. Estrutura:

```json
{
  "esquema": "revisao_iluminacao_T7_3_v1",
  "data": "AAAA-MM-DD",
  "metodo": "Responsável e método da inspeção realmente feita",
  "limites": "Amostragem, condições ausentes e incertezas",
  "imagens": [
    {
      "image_id": "ID_DO_NOVO_MANIFESTO",
      "sha256_original": "HASH_DO_MESMO_ARQUIVO",
      "condicoes": ["luz_difusa"],
      "observacao": "Observação visual específica da foto"
    }
  ]
}
```

Inclua imagens revisadas das 13 classes e exemplos aparentes de `sombra_ou_baixa_luz`, `luz_difusa` e `luz_direta_ou_realces`; também são aceitas `iluminacao_mista` e `nao_inferivel`. Não confunda brilho médio do fundo com iluminação do sujeito. Se o acervo não sustenta essa cobertura, registre a falta e obtenha amostras adequadas; não invente rótulos de iluminação para passar o validador. O exemplo de uma linha acima não é uma revisão completa.

```powershell
& $python -m src.quantizacao_t7_3 converter --raiz-imagens $imagens --indice "$campanha/dados/indice.csv" --pacote "$campanha/pacote" --conjunto "$campanha/calibracao" --saida "$campanha/int8"
```

Para gerar Float16 e comparar os formatos, use a função existente com **FP32 e INT8 explícitos**. O CLI T7.2 não expõe esses dois argumentos e, sozinho, continuaria lendo artefatos antigos. Conecte o computador à tomada. O bloco abaixo avalia **somente validação**:

```powershell
@'
import sys
from pathlib import Path
from src.comparacao_quantizacao_t7_2 import comparar
campanha, imagens = map(Path, sys.argv[1:3])
comparar(raiz=imagens, saida=campanha / "comparacao_validacao", indice=campanha / "dados/indice.csv",
         pacote=campanha / "pacote", fp32=campanha / "fp32", int8=campanha / "int8", conjunto=campanha / "calibracao",
         particoes=("validacao",), rodadas=5, por_rodada=40, reamostras=2000)
'@ | & $python - $campanha $imagens
```

Examine `comparacao.json`, `metricas_por_classe.csv`, `predicoes.csv` e o relatório: F1 macro e recall das minoritárias, mudanças de classe/scores, bytes, tensores e latência por runtime. A política de confiança precisa de uma análise separada dos scores máximos; não é calculada automaticamente pelo comparador. A comparação gera um INT8 regenerado, que pode diferir do arquivo `$campanha/int8/modelo_int8.tflite`; são artefatos diferentes. No passo de integração usamos explicitamente **Float16 da comparação e INT8 da conversão T7.3**, com seus próprios hashes. Não atribua resultado do INT8 regenerado ao outro arquivo. Se não forem idênticos, o comparador inclui a estratégia `int8_t7_3` para o arquivo preservado.

Float16 usa pesos reduzidos com entrada/saída float32. INT8 usa escala/zero point lidos de cada tensor; nunca copie parâmetros antigos nem normalize ImageNet outra vez fora do grafo. Ambos precisam funcionar com o contrato do frontend. Latência local não aprova o celular.

## 5. Congelar a decisão e avaliar o teste uma vez

Antes de abrir o teste, registre `$campanha/decisao_final.md`: hashes exatos de checkpoint/índice/pesos/Float16/INT8, versão, resultados de validação por classe, política de confiança, limites aplicáveis, hardware e limitações. Registre quem revisou a decisão e o que continua em validação; essa revisão não equivale à aprovação do parceiro. Se Float16/INT8 não forem adequados, não avance com essa composição: mudar formatos exige revisar o contrato web.

A proposta histórica é modelo ≤ 8.000.000 bytes e inferência p95 ≤ 300 ms no aparelho; o perímetro do pacote e os limites ainda precisam de ratificação. Confira a [T12.1](Validacao_T12_1.md). A política atual é top-1 ≥ 0,65 para exibir até três hipóteses; scores não são probabilidades calibradas. Avalie-a **na validação** após converter, com exemplos corretos, errados, inconclusivos e fora do escopo; ajuste/versione a política antes do teste se necessário. O comparador não faz detecção automática de imagens fora das classes nem substitui esse ensaio.

Com decisão congelada, avalie o checkpoint no teste do novo índice:

```powershell
& $python -m src.avaliacao_t6_1 --rodada $rodada --raiz-imagens $imagens --indice "$campanha/dados/indice.csv" --saida "$campanha/teste_keras" --batch 32
```

Para avaliar também os formatos convertidos, execute a mesma função anterior mudando apenas `saida=campanha / "comparacao_final"` e `particoes=("validacao", "teste")`. Isso gera **novas conversões**: confira que o SHA-256 de `comparacao_final/modelo_float16.tflite` coincide com o congelado da comparação de validação e que o INT8 T7.3 consumido é o mesmo. Se não coincidir, não associe as métricas ao binário anterior: investigue a reprodutibilidade e avalie o arquivo exato antes de publicar. Preserve as duas pastas.

Reporte acurácia, F1 macro, precisão/recall/F1/suporte das 13 classes, matriz e erros. No `predicoes.csv`, use `score_float16`/`previsto_float16` para o principal e `score_int8_t7_3`/`previsto_int8_t7_3` para a contingência (se a regeneração for idêntica, use `score_int8`/`previsto_int8`). Compare `previsto_*` a `indice_real` e `score_*` ao limiar congelado para contar acertos/erros aceitos e inconclusivos. Os scores desse CSV são arredondados a seis casas: se um deles coincide com o limiar, reavalie a imagem no arquivo exato usando a precisão original antes de determinar a decisão. Identifique versão dos dados, grupos relacionados, condições de captura e se existe independência. Não mude a seleção ou limiar depois de ler o teste; uma iteração motivada pelo teste transforma esse resultado em desenvolvimento e exige outra avaliação reservada para sustentar generalização.

## 6. Preparar a integração da nova versão

Use uma decisão de integração própria. **Não sobrescreva** a decisão histórica T8.3, seus modelos, classes ou contratos. O bloco cria dois arquivos de proposta na campanha; não altera a configuração ativa. Todos os caminhos precisam estar dentro do repositório para o pacote ser reproduzível pelo destinatário.

```powershell
@'
import hashlib, json, sys
from pathlib import Path
campanha = Path(sys.argv[1]).resolve(); raiz = Path.cwd().resolve()
versao = sys.argv[2]
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
rel = lambda p: p.relative_to(raiz).as_posix()
if not (campanha / "decisao_final.md").is_file(): raise ValueError("falta decisão registrada")
fp16 = campanha / "comparacao_validacao/modelo_float16.tflite"
int8 = campanha / "int8/modelo_int8.tflite"
if any(not 0 < p.stat().st_size <= 8_000_000 for p in (fp16, int8)):
    raise ValueError("modelo fora da proposta de tamanho")
decisao = {"status": "candidato_em_validacao", "versao": versao,
           "decisao_sha256": h(campanha / "decisao_final.md"),
           "escolhido": {"arquivo": rel(fp16), "sha256": h(fp16)},
           "contingencia": {"arquivo": rel(int8), "sha256": h(int8)}}
fontes = {"id": campanha.name, "version": versao, "selectionStatus": "candidato_em_validacao",
          "selection": {"sourcePath": rel(campanha / "decisao_integracao.json")},
          "classes": {"sourcePath": rel(campanha / "pacote/classes.json"),
                      "contractPath": rel(campanha / "pacote/manifesto.json"), "sha256Key": ["sha256", "classes.json"]},
          "models": [
              {"format": "Float16", "role": "principal", "version": "T7.2", "sourcePath": rel(fp16),
               "contractPath": rel(campanha / "comparacao_validacao/comparacao.json"), "sha256Key": ["estrategias", "float16", "sha256"]},
              {"format": "INT8", "role": "contingencia", "version": "T7.3", "sourcePath": rel(int8),
               "contractPath": rel(campanha / "int8/contrato_int8.json"), "sha256Key": ["modelo_int8_sha256"]}]}
for nome, valor in (("decisao_integracao.json", decisao), ("model-sources.proposto.json", fontes)):
    p = campanha / nome
    if p.exists(): raise ValueError("proposta já existe: " + str(p))
    p.write_text(json.dumps(valor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("Proposta criada; não é autorização de publicação.")
'@ | & $python - $campanha "1.1.0"
```

Os valores `models[].version = T7.2/T7.3` identificam os protocolos esperados pelo empacotador legado. A **nova versão global** está em `version`, junto com os novos caminhos e hashes. Não reutilize o ID do candidato antigo. `candidato_em_validacao` permanece explícito até a conclusão das verificações; não use uma string de aprovação para contornar teste histórico que espere estado oficial.

Em checkout de integração, após revisar a proposta:

```powershell
Copy-Item frontend/model-sources.json "$campanha/model-sources.anterior.json"
Copy-Item "$campanha/model-sources.proposto.json" frontend/model-sources.json
Push-Location frontend
npm.cmd ci
npm.cmd run assets
Pop-Location
& $python frontend/scripts/generate-reference.py
```

O gerador acima usa o manifesto novo e compara os originais aos modelos web nas referências sintéticas. O empacotador especializa dimensões dinâmicas para batch 1 sem modificar os originais; por isso o hash web difere do arquivo convertido. Não edite manualmente os `.tflite` em `public/models` ou `dist/models`.

**Antes dos testes completos:** `frontend/tests/analysis.spec.ts` ainda exige o estado histórico `T8.3_concluida_versao_oficial_mvp`. Atualize essa expectativa para a decisão da nova versão, mantendo a verificação de estado, origem, hashes, 13 classes e contingência; não remova a asserção apenas para deixar o teste verde. Algumas regressões Python e os relatórios T6/T8/T11 são históricos e verificam o candidato antigo: conserve-os como históricos e registre validações da nova campanha separadamente. Não atribua seus resultados à versão nova.

O `package-demo.mjs` também contém textos de limitações históricas. Na integração futura, atualize-os com as evidências reais da campanha antes do pacote definitivo; não remova uma limitação que ainda exista.

Para a comparação fotográfica Python/web, execute a sequência completa do [guia de integração](T14_4_Arquitetura_Web.md#execução-e-verificação), em checkout dedicado: `comparacao_preprocessamento_t10_2 referencia`, teste com `MODEL_COMPARISON=1` e consolidação. Guarde os resultados atuais na nova campanha, com hashes e ambiente. O gerador atual escreve nas pastas históricas; preserve as evidências anteriores antes de rodá-lo. Compare os dois modelos e decisões próximas ao limiar. Um corpus de regressão não comprova qualidade em campo, e equivalência CPU/WASM não certifica WebGPU.

```powershell
Push-Location frontend
npm.cmd test
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
npm.cmd run demo:package
npm.cmd run demo:verify -- .work/demo/IDENTIFICADOR_NOVO/site
Pop-Location
```

Verifique no dispositivo-alvo: câmera, galeria, EXIF, cancelamento, repetição, hipóteses, inconclusivo, erro, ausência de conteúdo e contingência. Monitore rede para confirmar ausência de upload e teste classificação após carregar os recursos e desligar a conexão. O primeiro acesso exige rede. Registre latência de inicialização, inferência e captura → resultado, tamanho total e, se disponível, memória: não transfira os números da versão anterior para o novo modelo. O benchmark de T12.2 do PR #57 é referência de método e limitações, não evidência de latência desta campanha.

## 7. Publicar e reverter

Só publique após revisão técnica e decisão de aceite/limitações registradas com a equipe do Agro App. Guarde modelo selecionado, fallback, checkpoint, índice/hash e revisão dos dados, calibração e inspeção, avaliações, referências web, ambiente, código/commit, política, decisão e pacote completo. O `release.json` identifica o código e os arquivos do site; verifique também que o checkout não tinha alterações de integração não registradas. Faça commit dos artefatos e configuração aprovados e gere o pacote definitivo a partir desse commit, registrando seu checksum. Não execute o gerador de referência nem troque modelo depois desse congelamento sem criar outra versão.

Publique **a pasta `site` inteira em HTTPS**, por troca atômica de versão ou rota versionada do ambiente de hospedagem. O repositório não fornece um comando universal de deploy: registre o serviço, responsável e procedimento realmente usado. Não envie apenas o `.tflite`: interface, catálogo, política, runtime, manifesto e cache formam um conjunto. Confirme pela URL publicada o hash/versão do manifesto e o modelo carregado; aguarde a instalação do novo service worker e faça nova navegação/recarregamento. Abas abertas podem continuar com o worker/modelo anterior em memória.

Se houver regressão de classe, falha de carregamento, decisão insegura ou incompatibilidade no aparelho:

1. Interrompa a disponibilização da nova versão e registre motivo, versão, hashes e evidências do problema.
2. Verifique com `demo:verify` a pasta `site` anterior preservada no passo 1 e **republique esse pacote inteiro** na rota de produção. Não troque só modelo/manifesto nem rode treino/conversão durante a reversão.
3. Reabra/recarregue a aplicação após a atualização do service worker; confira o manifesto, modelo carregado, galeria/câmera, inconclusivo e offline. Registre que abas antigas precisam ser recarregadas.
4. Em uma branch de correção, restaure também a configuração, contratos, política e referências do commit anterior aprovado. Preserve a campanha rejeitada para auditoria. Não use `reset --hard` ou force-push como procedimento de deploy.

Se não existe pacote anterior íntegro ou o canal de publicação não permite restaurá-lo, a reversão ainda não está preparada: resolva isso **antes** de trocar a versão em uso. Guarde onde obter os originais e licenças; um clone do Git não contém o acervo nem garante acesso futuro aos pesos pré-treinados.

## 8. Critérios de conclusão e validação externa

| Etapa | Evidência necessária para avançar |
| --- | --- |
| Dados | Inventário revisado, grupos/partições congelados, originais e hashes conferidos, classes/contagens e limitações. |
| Treino | Rodada completa, hashes de entrada, configuração/ambiente, curvas e métricas por classe de validação. |
| Conversão | Mesmo checkpoint/classes/índice, calibração só de treino revisada, contratos e resultados de cada binário. |
| Avaliação | Decisão congelada antes do teste, métricas por classe, matriz/erros e natureza independente ou exploratória declarada. |
| Integração | Manifesto/decisão/contratos coerentes, referências da nova versão, testes e aparelho identificado. |
| Publicação | Revisão registrada, commit/pacote íntegros, canal de publicação e pacote anterior recuperável. |
| Transferência | Destinatário com acesso a código, ambiente, originais autorizados e evidências; ensaio externo registrado. |

Para a validação externa, entregue este guia e os acessos necessários a alguém que não participou do desenvolvimento. Peça para percorrer as etapas e, quando houver ambiente/dados, executar os passos essenciais. Registre participante, data, sistema, comandos, entradas/saídas e hashes, o que realmente executou, dúvidas, bloqueios e correções. Leitura de comandos, teste sintético e execução interna **não** equivalem a retreinamento operacional validado. Se não houver novo treino/conversão/deploy/reversão reproduzidos, mantenha esses itens explicitamente não validados; não preencha uma declaração fictícia de conclusão.

## Fontes e alcance desta entrega

As fontes executáveis são [treinamento](../src/treinamento_t5_1.py), [dados](../src/dados_treino.py), [avaliação Keras](../src/avaliacao_t6_1.py), [conversão FP32](../src/conversao_t7_1.py), [calibração/INT8](../src/quantizacao_t7_3.py), [comparação](../src/comparacao_quantizacao_t7_2.py), [preparação web](../frontend/scripts/prepare-assets.mjs) e [pacote/reversão](../frontend/scripts/package-demo.mjs). Consulte os guias [T14.2](T14_2_Pipeline_Treinamento.md), [T14.3](T14_3_Avaliacao_Conversao.md) e [T14.4](T14_4_Arquitetura_Web.md) para detalhes. Os scripts históricos não foram generalizados nem a versão oficial foi substituída nesta documentação.

### Verificação interna em 20/11/2026

- Os quatro blocos Python foram extraídos deste guia e tiveram a sintaxe conferida. Foram executados os exemplos de índice, pacote e proposta; a chamada de comparação teve assinatura, caminhos explícitos e uso apenas da validação conferidos com o executor substituído por um dublê.
- Um acervo **sintético de 39 imagens** (13 por partição) exercitou a preparação. O índice foi aceito pelo leitor existente, com pesos de treino iguais a 1 nesse caso equilibrado. Foram confirmadas as recusas de ID repetido, grupo entre partições, caminho externo, classe ausente na validação e saída existente. Isso não audita dados reais.
- O pacote de metadados foi aceito pelo validador de proveniência. O checkpoint usado nesse ensaio era uma fixture, sem carregar modelo nem produzir métricas.
- A proposta foi aceita por `prepare-assets.mjs` em um checkout temporário com os binários históricos reais, sem alterar `frontend/model-sources.json` ativo. Foram conferidos hashes, catálogo, tipos/formas e estado pendente. Isso verifica o contrato de integração, não a origem de um novo treinamento.
- Os argumentos dos seis CLIs de treino, avaliação, FP32, preparação/calibração INT8 e registro foram conferidos com `--help`; links locais e `git diff --check` também foram conferidos.

Não foram executados novo treinamento, conversão de novo checkpoint, teste reservado, publicação/reversão em hospedagem ou ensaio por participante externo. PowerShell não estava instalado no ambiente desta conferência: foram executados os blocos Python extraídos e os CLIs, não uma sessão PowerShell ponta a ponta. Essas etapas continuam dependentes do ambiente/acervo da equipe e do ensaio externo.
