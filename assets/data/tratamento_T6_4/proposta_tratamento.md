# Proposta de tratamento de classes — T6.4

**Autor:** Rui · **Revisora:** Ana Célia · **Data:** 31/10/2026

**Estado:** proposta técnica pronta para revisão. Validação agronômica do parceiro pendente em todos os pares.

## Decisão proposta

Preservar as 13 classes do candidato e apresentar identidades separadas como hipóteses concorrentes, sujeitas ao ranking e à política de confiança. Nenhum novo agrupamento é recomendado nesta rodada: a análise não demonstra indistinguibilidade nem equivalência de conteúdo agronômico.

São 26 pares do candidato, correspondentes às 35 confusões direcionais e aos 72 erros da avaliação Keras FP32. Um par adicional, barriga-verde × percevejo-do-milho, aparece somente nos pares recorrentes históricos. Suas contagens não são atribuídas ao candidato.

O grupo já existente de S. eridania e S. cosmioides em das-vagens é preservado. A proposta não redefine espécies, não muda o modelo e não altera métricas. A partição analisada é exploratória e não demonstra a eficácia de apresentar top-k.

## Exibição no app

Uma hipótese só aparece se estiver no ranking elegível da imagem conforme a política de confiança. Este registro não adiciona automaticamente o par, não soma probabilidades e não propaga relações entre classes. Abaixo do critério aceito, o resultado deve ser inconclusivo e orientar nova foto. Hipóteses não afirmam presença simultânea de várias espécies ou manejo confirmado.

O PR #37 propõe k=3 e limiar top-1 de 0,65 para Keras FP32; permanece separado desta proposta. A T6.4 não fixa esses parâmetros nem comprova que a classe correta estará entre as hipóteses. A política precisa ser reconferida no formato embarcado.

## Decisões por par

A ordem prioriza os pares com mais erros e a suspeita de rótulo. Contagens sempre mantêm o sentido real → previsto; erro zero não significa equivalência ou prova de ausência de confusão futura.

### PAR-03-10 — Lagarta-do-cartucho (Spodoptera frugiperda) × Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)

**Prioridade de validação:** 1 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Lagarta-do-cartucho (Spodoptera frugiperda): 5 erros / 24 imagens reais (20,83%). IDs: IMG_03303, IMG_03384, IMG_03415, IMG_03427, IMG_03447.
- Candidato: Lagarta-do-cartucho (Spodoptera frugiperda) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 3 erros / 61 imagens reais (4,92%). IDs: IMG_02486, IMG_02673, IMG_02748.
- Evidência: O candidato erra nos dois sentidos (cinco das-vagens → cartucho e três cartucho → das-vagens). A revisão registra adultos, uma larva, foto distante e múltiplos sujeitos; não demonstra indistinguibilidade entre as classes.
- Agrupamento em classe única — não recomendado nesta rodada: Não há demonstração de que uma classe única preserve a informação necessária ao parceiro; nem os erros entre adultos nem a inclusão de duas espécies na classe das-vagens estabelecem equivalência com cartucho.
- Hipóteses concorrentes — recomendadas: Preservar cartucho e das-vagens com seus nomes e conteúdos separados, quando retornados pelo ranking aceito, permite representar a ambiguidade sem apagar a identidade de cada classe.
- Impacto agronômico a validar: Confirmar se cultura, órgão observado e estágio exigem conteúdos ou encaminhamentos diferentes para cartucho e para as espécies já reunidas em das-vagens; decidir quais diferenças devem permanecer visíveis.
- Encaminhamento: Conferir espécies e estágios das imagens com especialista; validar os critérios para distinguir as hipóteses e o conteúdo de cada uma.

### PAR-00-11 — Vaquinha (Diabrotica speciosa) × Astylus variegatus

**Prioridade de validação:** 1 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Vaquinha (Diabrotica speciosa) → Astylus variegatus: 5 erros / 157 imagens reais (3,18%). IDs: IMG_00994, IMG_01012, IMG_01175, IMG_01176, IMG_01516.
- Candidato: Astylus variegatus → Vaquinha (Diabrotica speciosa): 1 erro / 71 imagens reais (1,41%). IDs: IMG_00142.
- Evidência: Cinco erros vaquinha → Astylus e um no sentido inverso. Há padrão visual manchado, foto com sujeito pequeno e duas fotos com múltiplos insetos; a identidade do segundo inseto dessas fotos não foi confirmada.
- Agrupamento em classe única — não recomendado nesta rodada: Qualidade e multiplicidade de sujeitos não demonstram que as duas classes sejam indistinguíveis nem que possam compartilhar o mesmo conteúdo técnico.
- Hipóteses concorrentes — recomendadas: Manter vaquinha e Astylus como identidades separadas, sem interpretar a presença de vários insetos como confirmação de ambas as espécies.
- Impacto agronômico a validar: Confirmar se um nome genérico para os dois besouros ocultaria diferenças relevantes à identificação e ao conteúdo do Agro App, por cultura e estágio.
- Encaminhamento: Revisar o sujeito-alvo nas fotos com múltiplos insetos e validar quais caracteres o usuário deve observar para diferenciar as hipóteses.

### PAR-03-08 — Lagarta-do-cartucho (Spodoptera frugiperda) × Lagarta-falsa-medideira (Chrysodeixis includens)

**Prioridade de validação:** 1 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-do-cartucho (Spodoptera frugiperda): 6 erros / 12 imagens reais (50,00%). IDs: IMG_02972, IMG_02973, IMG_02978, IMG_03035, IMG_03040, IMG_03043.
- Evidência: Seis erros falsa-medideira → cartucho em 12 imagens da classe, provenientes de cinco observações; as fotos mostram adultos aparentes. A presença de mariposa sob nome comum iniciado por lagarta não prova rótulo errado.
- Agrupamento em classe única — não recomendado nesta rodada: A confusão nesta amostra não comprova indistinguibilidade nos estágios e condições de uso do MVP; não há validação de equivalência agronômica.
- Hipóteses concorrentes — recomendadas: Manter cartucho e falsa-medideira separados evita estender a dificuldade de identificar adultos a uma fusão de todas as imagens e estágios.
- Impacto agronômico a validar: Confirmar se distinguir cartucho de falsa-medideira é necessário ao conteúdo e ao encaminhamento do MVP, e se o escopo inclui adultos além de larvas.
- Encaminhamento: Validar escopo por estágio e caracteres de diferenciação; não excluir adultos ou relabelar pela interpretação do nome comum.

### PAR-00-02 — Vaquinha (Diabrotica speciosa) × Percevejo-barriga-verde (Dichelops/Diceraeus)

**Prioridade de validação:** 1 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-barriga-verde (Dichelops/Diceraeus) → Vaquinha (Diabrotica speciosa): 3 erros / 42 imagens reais (7,14%). IDs: IMG_02093, IMG_02110, IMG_02321.
- Candidato: Vaquinha (Diabrotica speciosa) → Percevejo-barriga-verde (Dichelops/Diceraeus): 2 erros / 157 imagens reais (1,27%). IDs: IMG_01068, IMG_01070.
- Evidência: Três erros barriga-verde → vaquinha e dois no sentido inverso; várias fotos têm sujeito pequeno. Os dois erros de vaquinha vêm da mesma observação.
- Agrupamento em classe única — não recomendado nesta rodada: O detalhe reduzido na foto não demonstra equivalência entre as classes nem sustenta reuni-las sob um único nome.
- Hipóteses concorrentes — recomendadas: Conservar as duas identidades e solicitar nova foto quando o resultado for inconclusivo; a ambiguidade do enquadramento não deve virar nova classe.
- Impacto agronômico a validar: Confirmar se perder a distinção entre vaquinha e barriga-verde direcionaria o usuário a conteúdo inadequado para a cultura ou o estágio observado.
- Encaminhamento: Validar orientação de enquadramento e o conteúdo de cada hipótese; preservar a separação entre qualidade da imagem e identidade taxonômica.

### PAR-05-06 — Percevejo-verde (Nezara viridula) × Percevejo-asa-preta (Edessa meditabunda)

**Prioridade de validação:** 1 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-asa-preta (Edessa meditabunda) → Percevejo-verde (Nezara viridula): 5 erros / 11 imagens reais (45,45%). IDs: IMG_03086, IMG_03087, IMG_03088, IMG_03089, IMG_03090.
- Evidência: Cinco erros asa-preta → verde, todos da observação 147542055 e com metadado Nymph. Asa-preta não tem ninfas explicitamente identificadas no treino, mas 26 imagens de treino estão sem estágio informado.
- Agrupamento em classe única — não recomendado nesta rodada: Uma observação com ninfa e uma lacuna de metadados não demonstram indistinguibilidade entre as classes em todos os estágios.
- Hipóteses concorrentes — recomendadas: Preservar asa-preta e verde como hipóteses separadas; a cobertura de ninfas deve ser investigada antes de considerar qualquer fusão.
- Impacto agronômico a validar: Confirmar se a identificação separada é necessária para ninfas e adultos, quais informações devem ser apresentadas em cada estágio e se algum agrupamento restrito a estágio seria aceitável.
- Encaminhamento: Validar espécie e estágio com especialista, completar a caracterização do treino e registrar decisão do parceiro sem inferir ausência de ninfas a partir de metadados vazios.

### PAR-02-03 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Lagarta-do-cartucho (Spodoptera frugiperda)

**Prioridade de validação:** 1 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-barriga-verde (Dichelops/Diceraeus) → Lagarta-do-cartucho (Spodoptera frugiperda): 1 erro / 42 imagens reais (2,38%). IDs: IMG_02123.
- Candidato: Lagarta-do-cartucho (Spodoptera frugiperda) → Percevejo-barriga-verde (Dichelops/Diceraeus): 1 erro / 61 imagens reais (1,64%). IDs: IMG_02602.
- Evidência: Um erro em cada sentido. IMG_02602 está rotulada como cartucho também na fonte, mas mostra insetos com aspecto de percevejos; a T6.3 registra suspeita de rótulo inconsistente, sem confirmação de espécie.
- Agrupamento em classe única — não recomendado nesta rodada: Uma suspeita de rótulo deve ser investigada na fonte; fundir classes apenas para absorver esse erro esconderia um possível problema de dados.
- Hipóteses concorrentes — recomendadas: Preservar as identidades e encaminhar IMG_02602 para conferência; a manutenção das hipóteses não endossa o rótulo dessa imagem nem a espécie prevista.
- Impacto agronômico a validar: Confirmar a identificação de IMG_02602 e se um grupo comum de cartucho e barriga-verde prejudicaria o conteúdo técnico e a interpretação pelo usuário.
- Encaminhamento: Priorizar revisão taxonômica da imagem e do rótulo de origem. Qualquer correção exige registro e nova versão de dados e avaliação; as métricas atuais permanecem intactas.

### PAR-00-01 — Vaquinha (Diabrotica speciosa) × Cigarrinha-do-milho (Dalbulus maidis)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Cigarrinha-do-milho (Dalbulus maidis) → Vaquinha (Diabrotica speciosa): 3 erros / 29 imagens reais (10,34%). IDs: IMG_00529, IMG_00575, IMG_00675.
- Candidato: Vaquinha (Diabrotica speciosa) → Cigarrinha-do-milho (Dalbulus maidis): 1 erro / 157 imagens reais (0,64%). IDs: IMG_00975.
- Evidência: Três erros cigarrinha-do-milho → vaquinha e um no sentido inverso. A revisão aponta insetos pequenos e, na foto de vaquinha, oclusão parcial.
- Agrupamento em classe única — não recomendado nesta rodada: O erro de imagens com pouco detalhe não sustenta uma classe única nem estabelece equivalência de conteúdo entre as duas identidades.
- Hipóteses concorrentes — recomendadas: Manter cigarrinha-do-milho e vaquinha separadas e tratar falta de detalhe pela orientação de captura ou pelo resultado inconclusivo.
- Impacto agronômico a validar: Confirmar se reunir cigarrinha-do-milho e vaquinha apagaria informação necessária ao conteúdo associado ao milho ou a outras culturas do MVP.
- Encaminhamento: Validar com o parceiro quais detalhes precisam estar visíveis em uma nova foto e manter o conteúdo de cada hipótese identificado.

### PAR-00-05 — Vaquinha (Diabrotica speciosa) × Percevejo-verde (Nezara viridula)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-verde (Nezara viridula) → Vaquinha (Diabrotica speciosa): 4 erros / 14 imagens reais (28,57%). IDs: IMG_03197, IMG_03198, IMG_03216, IMG_03246.
- Evidência: Quatro erros verde → vaquinha em três observações, incluindo duas fotos da mesma observação. Há oclusão e pouco detalhe em parte das fotos; a causa do par segue indeterminada.
- Agrupamento em classe única — não recomendado nesta rodada: Não há evidência de que os rótulos possam ser substituídos por um grupo comum sem perda de informação agronômica.
- Hipóteses concorrentes — recomendadas: Preservar as identidades e seus conteúdos separados, sem converter a causa indeterminada em diagnóstico de semelhança real.
- Impacto agronômico a validar: Confirmar se o conteúdo e o encaminhamento de percevejo-verde e vaquinha precisam permanecer distintos para as culturas e estágios do MVP.
- Encaminhamento: Validar critérios visuais e a orientação para fotos com oclusão; não assumir causa única para as quatro imagens.

### PAR-02-05 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Percevejo-verde (Nezara viridula)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-verde (Nezara viridula) → Percevejo-barriga-verde (Dichelops/Diceraeus): 4 erros / 14 imagens reais (28,57%). IDs: IMG_03254, IMG_03255, IMG_03257, IMG_03258.
- Evidência: Quatro erros verde → barriga-verde, todos da observação 368128786. A revisão descreve corpo em escudo e variação de distância, sem confirmação taxonômica da causa.
- Agrupamento em classe única — não recomendado nesta rodada: Quatro fotos correlacionadas não demonstram que as classes sejam indistinguíveis em novos exemplares ou agronomicamente intercambiáveis.
- Hipóteses concorrentes — recomendadas: Manter os dois percevejos com nomes separados; semelhança de forma pode ser apresentada como ambiguidade, não como identidade comum.
- Impacto agronômico a validar: Confirmar se um grupo genérico de percevejos perderia distinções necessárias ao conteúdo, ao estágio e à cultura atendida.
- Encaminhamento: Validar a identificação da observação e as diferenças que o conteúdo técnico deve destacar entre as hipóteses.

### PAR-02-10 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-barriga-verde (Dichelops/Diceraeus) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 2 erros / 42 imagens reais (4,76%). IDs: IMG_02198, IMG_02217.
- Candidato: Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Percevejo-barriga-verde (Dichelops/Diceraeus): 1 erro / 24 imagens reais (4,17%). IDs: IMG_03344.
- Evidência: Dois erros barriga-verde → das-vagens e um no sentido inverso. A revisão aponta sujeito pequeno, oclusão por folhas e larva parcialmente encoberta.
- Agrupamento em classe única — não recomendado nesta rodada: Enquadramento e oclusão não demonstram indistinguibilidade entre uma classe de percevejo e a classe das-vagens.
- Hipóteses concorrentes — recomendadas: Preservar as duas classes e orientar nova captura quando o detalhe não sustentar identificação, mantendo as hipóteses sujeitas ao ranking.
- Impacto agronômico a validar: Confirmar se uma categoria que reúna barriga-verde e das-vagens impediria escolher o conteúdo adequado ao sujeito, ao estágio e à cultura da foto.
- Encaminhamento: Validar orientação para sujeito único e imagem sem oclusão; não agrupar para compensar uma condição de captura inadequada.

### PAR-07-12 — Percevejo-do-milho (Leptoglossus zonatus) × Cigarrinha-das-pastagens (Deois flavopicta)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-do-milho (Leptoglossus zonatus) → Cigarrinha-das-pastagens (Deois flavopicta): 3 erros / 12 imagens reais (25,00%). IDs: IMG_00909, IMG_00942, IMG_00943.
- Evidência: Três erros percevejo-do-milho → cigarrinha-das-pastagens em duas observações. O corpo alongado aparece nas três fotos e a causa segue indeterminada.
- Agrupamento em classe única — não recomendado nesta rodada: O destino previsto e o corpo visível não comprovam semelhança indistinguível, equivalência de cultura ou de conteúdo.
- Hipóteses concorrentes — recomendadas: Preservar percevejo-do-milho e cigarrinha-das-pastagens como hipóteses com identidades e conteúdos próprios.
- Impacto agronômico a validar: Confirmar a relevância da distinção entre essas classes nas culturas do MVP; o nome comum de uma classe não deve ser usado sozinho para inferir a cultura da foto.
- Encaminhamento: Pedir ao parceiro os caracteres discriminantes e o contexto agronômico necessário quando a imagem não resolver a identificação.

### PAR-08-10 — Lagarta-falsa-medideira (Chrysodeixis includens) × Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-falsa-medideira (Chrysodeixis includens) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 2 erros / 12 imagens reais (16,67%). IDs: IMG_03036, IMG_03037.
- Candidato: Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Lagarta-falsa-medideira (Chrysodeixis includens): 1 erro / 24 imagens reais (4,17%). IDs: IMG_03304.
- Evidência: Dois erros falsa-medideira → das-vagens e um no sentido inverso. Os dois primeiros pertencem à observação 396445719; as fotos mostram adultos e detalhe reduzido em parte delas.
- Agrupamento em classe única — não recomendado nesta rodada: Fotos correlacionadas de adultos não demonstram que larvas, adultos e conteúdos possam ser tratados como uma classe única.
- Hipóteses concorrentes — recomendadas: Preservar falsa-medideira e das-vagens separadas, mantendo a ambiguidade entre adultos como hipótese de identificação.
- Impacto agronômico a validar: Confirmar se o parceiro precisa distinguir falsa-medideira das espécies da classe das-vagens por cultura e estágio, e quais diferenças devem aparecer no conteúdo.
- Encaminhamento: Validar escopo por estágio e caracteres de diferenciação; não ampliar o agrupamento existente em das-vagens sem nova decisão agronômica.

### PAR-00-06 — Vaquinha (Diabrotica speciosa) × Percevejo-asa-preta (Edessa meditabunda)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-asa-preta (Edessa meditabunda) → Vaquinha (Diabrotica speciosa): 2 erros / 11 imagens reais (18,18%). IDs: IMG_03091, IMG_03104.
- Evidência: Dois erros asa-preta → vaquinha em duas observações, ambas com metadado Nymph. A causa específica do destino vaquinha não foi isolada.
- Agrupamento em classe única — não recomendado nesta rodada: Uma lacuna de cobertura por estágio não demonstra equivalência entre asa-preta e vaquinha, nem justifica reunir as classes.
- Hipóteses concorrentes — recomendadas: Conservar as identidades e investigar a cobertura de ninfas, sem transformar uma dificuldade de estágio em fusão taxonômica.
- Impacto agronômico a validar: Confirmar quais conteúdos devem distinguir ninfas de asa-preta de vaquinha e se a interface precisa explicitar a incerteza de estágio.
- Encaminhamento: Validar ninfas com especialista e revisar a caracterização de estágios do treino antes de decidir sobre alteração de escopo.

### PAR-02-04 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Percevejo-marrom (Euschistus heros)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-marrom (Euschistus heros) → Percevejo-barriga-verde (Dichelops/Diceraeus): 2 erros / 10 imagens reais (20,00%). IDs: IMG_03160, IMG_03187.
- Evidência: Dois erros marrom → barriga-verde, em duas observações com insetos castanhos em escudo e corpo visível. Semelhança visual é hipótese, sem confirmação de espécie.
- Agrupamento em classe única — não recomendado nesta rodada: Forma e cor parecidas nas duas fotos não comprovam indistinguibilidade agronômica ou taxonômica.
- Hipóteses concorrentes — recomendadas: Preservar marrom e barriga-verde como classes separadas com informações de diferenciação validadas pelo parceiro.
- Impacto agronômico a validar: Confirmar se a distinção entre os dois percevejos é necessária ao conteúdo do MVP por cultura, estágio ou contexto observado.
- Encaminhamento: Validar caracteres discriminantes e esclarecer o que o usuário deve observar antes de escolher entre as hipóteses.

### PAR-02-09 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Lagarta-da-soja (Anticarsia gemmatalis)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-da-soja (Anticarsia gemmatalis) → Percevejo-barriga-verde (Dichelops/Diceraeus): 1 erro / 6 imagens reais (16,67%). IDs: IMG_02949.
- Candidato: Percevejo-barriga-verde (Dichelops/Diceraeus) → Lagarta-da-soja (Anticarsia gemmatalis): 1 erro / 42 imagens reais (2,38%). IDs: IMG_02159.
- Evidência: Um erro em cada sentido; a revisão não isolou a causa. Há inseto em escudo no rótulo barriga-verde e mariposa no rótulo lagarta-da-soja.
- Agrupamento em classe única — não recomendado nesta rodada: Dois erros isolados sem causa demonstrada não sustentam fusão de classes ou equivalência de conteúdo.
- Hipóteses concorrentes — recomendadas: Preservar barriga-verde e lagarta-da-soja, sem atribuir identidade comum a partir da previsão errada.
- Impacto agronômico a validar: Confirmar se reunir esses rótulos faria o usuário consultar conteúdo inadequado para o sujeito e o estágio observado, inclusive no escopo soja.
- Encaminhamento: Conferir identidades e escopo por estágio com o parceiro; manter a causa como indeterminada até haver evidência.

### PAR-04-07 — Percevejo-marrom (Euschistus heros) × Percevejo-do-milho (Leptoglossus zonatus)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-marrom (Euschistus heros) → Percevejo-do-milho (Leptoglossus zonatus): 2 erros / 10 imagens reais (20,00%). IDs: IMG_03154, IMG_03155.
- Evidência: Dois erros marrom → percevejo-do-milho, ambos da observação 19890644; as fotos contêm múltiplos insetos de aspectos distintos.
- Agrupamento em classe única — não recomendado nesta rodada: Ambiguidade de sujeito em uma observação não prova equivalência entre as classes e não pode ser resolvida por fusão automática.
- Hipóteses concorrentes — recomendadas: Preservar marrom e percevejo-do-milho com conteúdo próprio; orientar nova foto de um sujeito quando a cena for ambígua.
- Impacto agronômico a validar: Confirmar qual sujeito deve ser identificado em uma foto com vários insetos e se os conteúdos de marrom e percevejo-do-milho precisam permanecer separados.
- Encaminhamento: Validar identificação dos sujeitos e protocolo de captura; não usar a cena como confirmação simultânea das espécies.

### PAR-10-11 — Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) × Astylus variegatus

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) → Astylus variegatus: 1 erro / 24 imagens reais (4,17%). IDs: IMG_03315.
- Candidato: Astylus variegatus → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 1 erro / 71 imagens reais (1,41%). IDs: IMG_00233.
- Evidência: Um erro das-vagens → Astylus e um no sentido inverso. Há sujeito pequeno em uma foto e vários insetos na outra.
- Agrupamento em classe única — não recomendado nesta rodada: Qualidade e múltiplos sujeitos não demonstram uma categoria agronômica comum entre as duas classes.
- Hipóteses concorrentes — recomendadas: Manter das-vagens e Astylus separados; hipótese concorrente não significa afirmar que ambos estão presentes na foto.
- Impacto agronômico a validar: Confirmar se uma identificação única para das-vagens e Astylus apagaria informação relevante ao conteúdo, à cultura e ao estágio atendidos.
- Encaminhamento: Validar sujeito-alvo e orientação de captura; investigar cada erro antes de inferir semelhança real entre as classes.

### PAR-02-07 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Percevejo-do-milho (Leptoglossus zonatus)

**Prioridade de validação:** 2 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: nenhum erro em ambos os sentidos; par retido por evidência histórica.
- Evidência: Não há erros entre essas classes na matriz do candidato. O par barriga-verde → percevejo-do-milho é recorrente nos quatro modelos FP32 históricos; a análise antiga aponta baixa cobertura de campo, oclusão e semelhança como hipóteses.
- Agrupamento em classe única — não recomendado nesta rodada: A evidência histórica não comprova equivalência agronômica, e não deve ser atribuída ao candidato atual ou usada para agrupá-lo retroativamente.
- Hipóteses concorrentes — recomendadas: Preservar barriga-verde e percevejo-do-milho como classes separadas; reter a proposta para o caso de ambas surgirem no ranking de uma nova imagem.
- Impacto agronômico a validar: Confirmar se a distinção entre esses percevejos precisa permanecer visível no conteúdo e no encaminhamento ao usuário, por cultura e estágio.
- Encaminhamento: Validar a interpretação histórica com o parceiro, mantendo suas contagens separadas das do candidato atual.

### PAR-00-10 — Vaquinha (Diabrotica speciosa) × Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Vaquinha (Diabrotica speciosa) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 1 erro / 157 imagens reais (0,64%). IDs: IMG_01855.
- Evidência: Um erro vaquinha → das-vagens; IMG_01855 mostra inseto pequeno no dedo, com mão e ambiente dominando o quadro.
- Agrupamento em classe única — não recomendado nesta rodada: Um único erro com sujeito pequeno não demonstra indistinguibilidade das classes nem equivalência de conteúdo.
- Hipóteses concorrentes — recomendadas: Preservar vaquinha e das-vagens e tratar a captura insuficiente pela política de resultado inconclusivo.
- Impacto agronômico a validar: Confirmar se os conteúdos de vaquinha e das-vagens devem permanecer distintos por cultura e estágio; nenhuma equivalência é presumida.
- Encaminhamento: Validar orientação para aproximar o sujeito e manter o caso como evidência isolada.

### PAR-00-12 — Vaquinha (Diabrotica speciosa) × Cigarrinha-das-pastagens (Deois flavopicta)

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Vaquinha (Diabrotica speciosa) → Cigarrinha-das-pastagens (Deois flavopicta): 1 erro / 157 imagens reais (0,64%). IDs: IMG_01303.
- Evidência: Um erro vaquinha → cigarrinha-das-pastagens em foto junto de régua, com vista parcial e detalhe limitado.
- Agrupamento em classe única — não recomendado nesta rodada: A dificuldade de uma foto não demonstra que as classes sejam indistinguíveis ou que possam compartilhar uma identificação.
- Hipóteses concorrentes — recomendadas: Preservar os dois rótulos e seus conteúdos quando elegíveis pelo ranking, sem inferir cultura apenas pelo nome comum.
- Impacto agronômico a validar: Confirmar se reunir vaquinha e cigarrinha-das-pastagens ocultaria distinções relevantes às culturas e ao conteúdo do MVP.
- Encaminhamento: Validar enquadramento necessário e caracteres discriminantes, sem generalizar a partir de um erro.

### PAR-02-11 — Percevejo-barriga-verde (Dichelops/Diceraeus) × Astylus variegatus

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-barriga-verde (Dichelops/Diceraeus) → Astylus variegatus: 1 erro / 42 imagens reais (2,38%). IDs: IMG_02172.
- Evidência: Um erro barriga-verde → Astylus; a foto contém dois insetos de aspectos diferentes sobre a mão.
- Agrupamento em classe única — não recomendado nesta rodada: Uma cena com mais de um sujeito não estabelece semelhança entre espécies nem identidade agronômica comum.
- Hipóteses concorrentes — recomendadas: Preservar barriga-verde e Astylus; a previsão não confirma a identidade dos dois sujeitos presentes na cena.
- Impacto agronômico a validar: Confirmar o sujeito de interesse na foto e se a perda da distinção entre as classes afetaria a consulta ao conteúdo técnico.
- Encaminhamento: Validar a identificação dos sujeitos e a orientação para nova foto de um inseto por vez.

### PAR-03-07 — Lagarta-do-cartucho (Spodoptera frugiperda) × Percevejo-do-milho (Leptoglossus zonatus)

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-do-cartucho (Spodoptera frugiperda) → Percevejo-do-milho (Leptoglossus zonatus): 1 erro / 61 imagens reais (1,64%). IDs: IMG_02814.
- Evidência: Um erro cartucho → percevejo-do-milho em foto de mariposa com corpo visível; a causa não foi isolada.
- Agrupamento em classe única — não recomendado nesta rodada: Nome comum ligado ao milho e um erro isolado não demonstram equivalência entre as classes.
- Hipóteses concorrentes — recomendadas: Preservar cartucho e percevejo-do-milho separados, sem confundir contexto de cultura com identidade do sujeito.
- Impacto agronômico a validar: Confirmar quais diferenças de conteúdo devem permanecer visíveis quando as duas classes forem candidatas no contexto do milho, inclusive por estágio.
- Encaminhamento: Conferir a identificação e registrar que a causa permanece indeterminada.

### PAR-03-09 — Lagarta-do-cartucho (Spodoptera frugiperda) × Lagarta-da-soja (Anticarsia gemmatalis)

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Lagarta-do-cartucho (Spodoptera frugiperda) → Lagarta-da-soja (Anticarsia gemmatalis): 1 erro / 61 imagens reais (1,64%). IDs: IMG_02743.
- Evidência: Um erro cartucho → lagarta-da-soja em foto de mariposa de asas abertas; semelhança e variação de estágio são hipóteses, não erro taxonômico confirmado.
- Agrupamento em classe única — não recomendado nesta rodada: Uma confusão entre adultos não demonstra indistinguibilidade em todos os estágios ou equivalência de conteúdo.
- Hipóteses concorrentes — recomendadas: Preservar cartucho e lagarta-da-soja como identidades separadas e explicitar a incerteza do resultado.
- Impacto agronômico a validar: Confirmar se a diferenciação é necessária nas culturas e estágios atendidos pelo MVP e se o conteúdo de adultos e larvas exige apresentação distinta.
- Encaminhamento: Validar espécie e escopo por estágio antes de qualquer alteração de classes.

### PAR-04-11 — Percevejo-marrom (Euschistus heros) × Astylus variegatus

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-marrom (Euschistus heros) → Astylus variegatus: 1 erro / 10 imagens reais (10,00%). IDs: IMG_03156.
- Evidência: Um erro marrom → Astylus na observação 19890644, também presente no par marrom × percevejo-do-milho; a imagem contém múltiplos insetos.
- Agrupamento em classe única — não recomendado nesta rodada: A mesma cena confusa produzir destinos diferentes não demonstra que essas classes devam formar um grupo, nem autoriza agrupamento transitivo.
- Hipóteses concorrentes — recomendadas: Preservar marrom e Astylus e tratar a ambiguidade do sujeito, sem acrescentar automaticamente todas as classes ligadas pela mesma observação.
- Impacto agronômico a validar: Confirmar o sujeito-alvo e se o conteúdo de marrom e Astylus deve permanecer separado para evitar atribuir a um inseto a informação de outro.
- Encaminhamento: Conferir os sujeitos e solicitar captura individual quando necessário; avaliar a cena junto com os demais erros da observação.

### PAR-05-10 — Percevejo-verde (Nezara viridula) × Lagarta-das-vagens (Spodoptera eridania e S. cosmioides)

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Percevejo-verde (Nezara viridula) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 1 erro / 14 imagens reais (7,14%). IDs: IMG_03256.
- Evidência: Um erro verde → das-vagens na observação 368128786; o inseto aparece parcialmente escondido atrás de vagem seca.
- Agrupamento em classe única — não recomendado nesta rodada: A presença de uma vagem na cena e a oclusão não demonstram identidade comum entre as classes.
- Hipóteses concorrentes — recomendadas: Preservar verde e das-vagens, sem usar o objeto de fundo ou o nome da classe como identificação do sujeito.
- Impacto agronômico a validar: Confirmar como o conteúdo deve distinguir o sujeito observado de danos ou estruturas da planta, mantendo os dois rótulos separados.
- Encaminhamento: Validar captura sem oclusão e considerar o caso junto dos demais erros da observação, sem inferir causalidade do fundo.

### PAR-07-11 — Percevejo-do-milho (Leptoglossus zonatus) × Astylus variegatus

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Astylus variegatus → Percevejo-do-milho (Leptoglossus zonatus): 1 erro / 71 imagens reais (1,41%). IDs: IMG_00008.
- Evidência: Um erro Astylus → percevejo-do-milho; o sujeito é pequeno e folhas e fundo ocupam a maior parte da imagem.
- Agrupamento em classe única — não recomendado nesta rodada: Um erro com pouco detalhe não comprova indistinguibilidade nem equivalência de conteúdo das classes.
- Hipóteses concorrentes — recomendadas: Manter Astylus e percevejo-do-milho separados, com nova captura quando a política indicar resultado inconclusivo.
- Impacto agronômico a validar: Confirmar se um nome conjunto apagaria diferenças necessárias à consulta ao conteúdo técnico por cultura ou estágio.
- Encaminhamento: Validar quais características devem ser visíveis em nova foto; não ampliar o agrupamento com base neste caso isolado.

### PAR-10-12 — Lagarta-das-vagens (Spodoptera eridania e S. cosmioides) × Cigarrinha-das-pastagens (Deois flavopicta)

**Prioridade de validação:** 3 · **Decisão proposta:** hipóteses concorrentes · **Validação do parceiro:** pendente.

- Candidato: Cigarrinha-das-pastagens (Deois flavopicta) → Lagarta-das-vagens (Spodoptera eridania e S. cosmioides): 1 erro / 24 imagens reais (4,17%). IDs: IMG_00843.
- Evidência: Um erro cigarrinha-das-pastagens → das-vagens em foto com corpo visível junto de régua; a causa segue indeterminada.
- Agrupamento em classe única — não recomendado nesta rodada: Um erro isolado e sem causa demonstrada não estabelece equivalência taxonômica ou agronômica.
- Hipóteses concorrentes — recomendadas: Preservar cigarrinha-das-pastagens e das-vagens com identidades e conteúdos separados.
- Impacto agronômico a validar: Confirmar se a distinção entre essas classes é necessária ao conteúdo nas culturas e estágios previstos, sem inferir cultura pelo nome comum.
- Encaminhamento: Validar identificação do sujeito e caracteres discriminantes; manter a causa indeterminada até haver evidência.

## Validação a registrar

Ana Célia revisa cobertura, justificativas e distinção entre evidência e hipótese. O parceiro confirma se manter as identidades separadas e seus conteúdos atende ao uso previsto; para cada par, deve registrar concordância ou alteração, impacto agronômico, responsável, data e evidência (ata, mensagem ou documento). Uma aprovação em bloco pode referenciar explicitamente todos os IDs e a versão deste registro.

A validação deve se concentrar no que o usuário pode entender e em qual conteúdo será associado a cada classe, considerando culturas e estágios do escopo do MVP.

Os campos de validação por par e a revisão técnica estão em [proposta_tratamento.json](proposta_tratamento.json), inicialmente pendentes e sem responsáveis ou datas inventados. Uma alteração de decisão exige registrar o novo fundamento, sem reescrever as evidências dos modelos anteriores.

Se houver opção por agrupamento, explicitar o nome e o conjunto completo de classes, culturas e estágios abrangidos, exceções e conteúdo associado. Depois, versionar a mudança de contrato, dados ou pós-processamento conforme a implementação escolhida e reavaliar métricas e confiança. A aprovação de um par não autoriza fusão transitiva com outros.

## Base e rastreabilidade

TAP, seção 12, pp. 5–6: a mitigação da confusão prevê hipóteses com confiança e permite agrupar classes indistinguíveis mediante validação técnica do parceiro. O original fornecido pelo parceiro não foi adicionado ao Git; seu hash está no registro estruturado.

- [Matriz do candidato e pares direcionais](../avaliacao_T6_2/candidato_T5_6_20261026_keras/pares_confundidos.csv).
- [Análise de causas do candidato](../avaliacao_T6_3/candidato_T5_6_20261026_keras/analise_por_par.csv).
- [Revisão por imagem](../avaliacao_T6_3/candidato_T5_6_20261026_keras/revisao_por_imagem.csv).
- [Pares históricos](../avaliacao_T6_2/pares_recorrentes_fp32.csv).
- [Rastreabilidade dos arquivos desta proposta](rastreabilidade.json).
