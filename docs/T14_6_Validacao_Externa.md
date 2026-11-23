# Validação externa do guia de retreinamento

Autor responsável pelo ensaio: Rui · Revisora: Karol.

**Estado em 22/11/2026: ciclo completo relatado por Rui; registro aguardando revisão de Karol.** Rui informou que realizou o ensaio com Tobias, em Windows, que funcionou e não houve dúvidas. Ao ser perguntado sobre preparação dos dados, treinamento, avaliação, conversão, atualização e reversão, confirmou a execução de todo o ciclo. O relato é a evidência recebida; comandos, logs e arquivos de saída não foram enviados para conferência técnica.

O objetivo é verificar se alguém que não participou diretamente do desenvolvimento consegue utilizar o [guia de retreinamento](T14_5_Guia_Retreinamento.md), identificar dificuldades e produzir evidências do que realmente fez. O [registro estruturado](../assets/data/validacao_externa_T14_6/registro.json) identifica o guia de referência da preparação, as etapas relatadas, as evidências disponíveis e a conclusão. O hash da cópia utilizada pelo participante não foi informado. O guia só pode ser considerado **operacionalmente validado** após reproduzir os passos essenciais.

## Participante e preparação

1. Identifique uma pessoa que não tenha participado diretamente do desenvolvimento. Registre nome ou identificador acordado, papel e confirmação dessa condição. Não reutilize como validação externa os ensaios de Rui, Karol ou os testes internos automatizados.
2. Entregue o guia e os acessos autorizados ao repositório, imagens, licenças e pacote anterior. Registre a URL/cópia entregue e o SHA-256 do arquivo. O registro inicial identifica a versão da `develop` usada na preparação; não cobre alterações posteriores sem nova identificação.
3. Combine escopo, horário, computador, memória disponível, acesso à rede e canal para registrar evidências. O guia usa PowerShell, Python 3.12 e Node 22.12+; a falta de ferramenta ou permissão é um bloqueio do ensaio, não uma etapa executada.
4. Use um checkout e uma campanha novos, com pastas de saída vazias. Nunca use a produção ou sobrescreva os modelos oficiais para demonstrar atualização ou reversão. A publicação deve ocorrer em ambiente de ensaio autorizado.
5. Garanta que o acervo do ensaio tenha rótulos/grupos revisados, as 13 classes em treino e validação e treino suficiente para a calibração de 200 fotos, com grupos distintos. O conjunto deve vir acompanhado dos direitos de uso. As 39 imagens sintéticas da conferência interna não servem para validar treinamento real ou calibração representativa.

Um treinamento exploratório no acervo histórico pode validar a execução operacional, desde que sua natureza e os vínculos conhecidos sejam registrados. Não demonstra generalização. A auditoria e o preparo dos dados precisam resolver os grupos compartilhados que os validadores recusam; não remova uma proteção para completar o ensaio.

## Instrução para entregar ao participante

> Siga o guia no ambiente de ensaio, começando pela preparação e preservação da versão anterior. Anote cada comando executado, o resultado e qualquer instrução que tenha exigido ajuda. Quando algo impedir o avanço, registre a mensagem de erro e pare nesse ponto. Não altere rótulos, hashes ou critérios apenas para passar um validador. Ao final, relate com suas palavras o que conseguiu fazer, as dificuldades e o que não executou. Não é necessário declarar que o procedimento funcionou se você apenas o leu.

O facilitador pode esclarecer acessos e riscos, mas deve registrar intervenções. Se executar um comando no lugar do participante, atribua essa execução ao facilitador e registre o passo como assistido. Uma explicação oral necessária para avançar deve virar correção no guia ou limitação identificada, não ser omitida do relato.

## Roteiro e evidências

| Etapa | Atividade do participante | Evidência mínima |
| --- | --- | --- |
| 1. Acesso e leitura | Localizar guia, código, dados e compreender o fluxo. | Versão/hash do guia, relato próprio de dúvidas e acessos realmente obtidos. |
| 2. Ambiente | Criar ambiente e conferir dependências/comandos. | Sistema, versões, instalação e log de comandos; falhas de rede/permissão. |
| 3. Dados | Criar e conferir o contrato da nova campanha. | Inventário revisado, hash do índice/pesos/classes, contagens e reserva do teste. |
| 4. Treinamento | Executar a rodada pelo pipeline. | Pasta completa: checkpoint, configuração, ambiente, histórico e métricas de validação; hashes. |
| 5. Decisão | Interpretar validação por classe e congelar a escolha. | Decisão com hashes dos candidatos, critérios e justificativa sem usar o teste. |
| 6. Calibração | Selecionar treino e revisar iluminação. | Manifesto da calibração, grupos/classes, revisão realmente feita e limitações. |
| 7. Conversão | Gerar os formatos e comparar o mesmo checkpoint. | FP32/Float16/INT8, contratos, métricas de validação e hashes; arquivos exatos identificados. |
| 8. Avaliação final | Executar avaliação após a decisão congelada. | Métricas por classe e erros, índice/binário avaliado, classificação independente ou exploratória. |
| 9. Integração | Configurar uma versão de ensaio e testar o frontend. | Proposta/manifesto, referências, logs de testes e modelo efetivamente carregado. |
| 10. Publicação de ensaio | Preparar e abrir o pacote em ambiente autorizado. | Commit, `release.json`, checksum, localização recuperável do pacote e verificações. |
| 11. Reversão | Restaurar o pacote anterior nesse ambiente de ensaio. | Versão antes/depois, verificações de integridade, recarregamento/cache e teste funcional. |

Na ficha, cada etapa aceita: `nao_informado` (alcance ainda não detalhado), `execucao_relatada` (execução informada sem conferência dos artefatos), `nao_executado`, `lido_apenas`, `executado_com_ajuda`, `executado_sem_ajuda` ou `bloqueado`. O estado da etapa deve refletir a atividade real; a presença de arquivos de exemplo no repositório não significa que o participante os produziu. Registre tempo observado sem estimar o que não foi medido.

Uma sessão pode terminar bloqueada ou cobrir só parte do fluxo. Preserve o resultado e programe a retomada se necessário; não avance o status da validação porque a documentação já foi integrada.

## Como preencher o registro

O arquivo `registro.json` começa com dados da preparação e campos vazios para a sessão. Depois do ensaio:

- Preencha participante, declaração de independência, datas, sistema e versões com as informações confirmadas.
- Em cada etapa, registre comandos, estado, dúvidas, assistência, arquivos/links e SHA-256 das evidências. Guarde stdout/stderr e o relato original do participante em local autorizado e recuperável, sem credenciais ou dados pessoais desnecessários.
- Registre cada problema com etapa, mensagem/comportamento observado, impacto e correção proposta. Vincule correções do guia a commit/PR; se a mudança afetar a execução, repita o passo com a nova versão do guia e registre seu hash.
- Peça ao participante que confirme o relato. A confirmação é parte da evidência, não um campo que o autor preenche presumindo concordância.
- Registre o alcance: leitura, execução parcial ou reprodução dos passos essenciais. Identifique precisamente o que ficou sem executar, inclusive quando o impedimento é falta de dados, tempo, hardware ou acesso de publicação.

Não substitua silenciosamente uma sessão encerrada por outro ensaio. Preserve os resultados em arquivos separados por identificador/data ou mantenha o registro inicial como template e crie uma cópia para cada participante. A conclusão deve apontar para as sessões que a sustentam.

## Critério de conclusão

| Evidência obtida | Conclusão permitida |
| --- | --- |
| Apenas este protocolo, sem participante e sem relato | Preparado; validação externa não realizada. |
| Ciclo completo confirmado por relato, sem conferência dos arquivos | Execução completa relatada, com fonte identificada e limites; aguarda revisão técnica do registro. |
| Leitura/percurso real por participante externo, com dúvidas e limitações documentadas | Ensaio externo de leitura; não valida operacionalmente o guia. |
| Parte dos procedimentos executados, com bloqueios/ajuda registrados | Validação externa parcial, limitada às etapas e versão do guia identificadas. |
| Passos essenciais de dados, treinamento, avaliação, conversão, atualização e reversão reproduzidos, evidências conferidas e relato confirmado | Guia operacionalmente validado para esse ambiente, dados e versão; limitações restantes explícitas. |

A T14.6 pede execução ou ensaio externo documentado. Um percurso de leitura pode produzir esse registro, mas não autoriza declarar que a equipe do Agro App já consegue operar o ciclo completo. Se etapas essenciais não forem reproduzidas, preserve `guia_operacionalmente_validado: false`, mesmo depois de um ensaio parcial ou da aprovação da documentação.

## Entregáveis da sessão

O conjunto final reúne identificação/hash do guia, ficha preenchida, relato confirmado do participante, logs e hashes dos arquivos gerados, problemas/correções e conclusão com limites. A revisão de Karol deve conferir se os resultados são sustentados por essas evidências, inclusive quando a conclusão é parcial ou bloqueada.

O [checklist final da entrega](https://github.com/AgroTech-Inteli-ATI/2026_02_AgroApp/pull/61) deve tratar reprodução como parcial enquanto esse conjunto não sustentar a execução operacional. Esta preparação não muda o estado do modelo, dos testes de dispositivo ou do aceite do parceiro.

## Relato recebido em 22/11/2026

| Informação | Registro recebido |
| --- | --- |
| Participante | Tobias, informado por Rui. |
| Ambiente | Windows; versão e demais ferramentas não informadas. |
| Acompanhamento | Rui informou que fez o ensaio com Tobias; tipo de ajuda não detalhado. |
| Resultado | “Funcionou”, segundo Rui. |
| Dúvidas | Rui informou que não houve dúvidas. |
| Etapas executadas | Ciclo completo, incluindo preparação, treinamento, avaliação, conversão, atualização e reversão, conforme confirmação de Rui. |
| Versão do guia executada | Hash da sessão não informado; a ficha identifica o guia de referência da preparação. |
| Evidências recebidas | Relato neste chat; sem logs ou arquivos de saída enviados. |

Relato original de Rui: “funcionou aqui. fiz com o tobias. ele usou windows. nao teve duvidas”. Ao ser perguntado se o ciclo completo havia sido executado, incluindo treinamento, conversão, atualização e reversão, respondeu “todo”. A data acima é a de recebimento, não uma data de execução confirmada. As etapas ficam como `execucao_relatada`, sustentadas pela confirmação de Rui, sem inventar comandos ou resultados de arquivos que não foram enviados.

**Conclusão do registro:** o ciclo completo foi informado como realizado com sucesso por Tobias em Windows, acompanhado por Rui, sem dúvidas relatadas. Não há correção decorrente de dúvida registrada nesse retorno. A conferência independente dos artefatos e a revisão de Karol permanecem distintas dessa confirmação: `etapas_essenciais_reproduzidas: true` registra o relato de execução, enquanto `reproducao_tecnica_conferida: false` e `guia_operacionalmente_validado: false` evitam apresentar uma auditoria técnica ou aceite formal que ainda não ocorreram. Isso não nega o resultado informado; identifica a fonte e o alcance da evidência disponível.
