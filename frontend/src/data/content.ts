// Gerado por `python -m src.associacao_conteudo_t9_3 frontend` (T9.3/T13). Não edite à mão:
// altere associacao_classes.json e base_conteudo.json em assets/data/conteudo_T9_3 e gere de novo.
export interface TechnicalItem {
  text: string;
  source: string;
}

export interface TechnicalSection {
  id: string;
  title: string;
  items: TechnicalItem[];
}

export interface TechnicalContent {
  title: string;
  scientificName: string;
  context: string | null;
  sections: TechnicalSection[];
  sources: string[];
  references: string[];
  author: string;
  reviewedAt: string;
  validated: boolean;
}

// Chaves são os índices de classes.json do modelo versionado.
export const technicalContent: Partial<Record<number, TechnicalContent>> = {
  "0": {
    "title": "Vaquinha",
    "scientificName": "Diabrotica speciosa",
    "context": "Descrição baseada em manual sobre a cultura da soja e em publicações sobre o milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto pequeno, de 5 a 6 mm: corpo verde, três manchas amarelas em cada asa da frente e cabeça avermelhada.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 42"
          },
          {
            "text": "A larva vive no solo. É amarelo-pálida, com cabeça, tórax e pernas pretos, e mede de 10 a 12 mm.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 42"
          },
          {
            "text": "Os ovos são postos em grupos, nas partes da planta que ficam debaixo da terra.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 42"
          },
          {
            "text": "A larva-alfinete é a fase jovem da vaquinha verde e amarela, também chamada de patriota.",
            "source": "EICHOLZ et al., 2024, p. 90"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Os adultos comem folhas e brotos, de preferência os mais tenros, e deixam pequenos furos.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 42"
          },
          {
            "text": "Raramente causam grande desfolha.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 42"
          },
          {
            "text": "No milho, as larvas comem as raízes, e a planta passa a absorver menos água e nutrientes.",
            "source": "VIANA, 2011, p. 22"
          },
          {
            "text": "Com a raiz estragada, o colmo fica curvado: é o sintoma chamado de pescoço-de-ganso.",
            "source": "VIANA, 2011, p. 22"
          },
          {
            "text": "Planta com poucas raízes tomba mais fácil com vento forte e chuva intensa, o que atrapalha a colheita mecânica.",
            "source": "EICHOLZ et al., 2024, p. 90"
          },
          {
            "text": "Mais de 3,5 larvas por planta já bastam para prejudicar as raízes.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 1"
          },
          {
            "text": "No milho, os adultos podem furar folhas de plantas novas e, na polinização, comer os \"cabelos\" da espiga, o que prejudica a fertilização.",
            "source": "VIANA, 2011, p. 23"
          },
          {
            "text": "A fase de maior risco vai da germinação até cerca de 45 dias depois da emergência da planta.",
            "source": "EICHOLZ et al., 2024, p. 90"
          },
          {
            "text": "Os danos mais fortes aparecem em lavouras semeadas tarde ou na safrinha, quando há mais adultos; no Sul, o pico é de fevereiro a março.",
            "source": "WORDELL FILHO et al., 2016, p. 40"
          },
          {
            "text": "Quando a planta cresce, a larva também ataca as raízes adventícias, e a planta lança raízes em nós acima do solo.",
            "source": "WORDELL FILHO et al., 2016, p. 40"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de percevejo-verde, percevejo-barriga-verde ou cigarrinha-do-milho.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 42",
      "EICHOLZ et al., 2024, p. 90",
      "VIANA, 2011, p. 22-23",
      "VIANA; CRUZ; WAQUIL, 2002, p. 1",
      "WORDELL FILHO et al., 2016, p. 40",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "EICHOLZ, E. D. et al. (ed.). Informações técnicas para o cultivo de milho e sorgo na região subtropical do Brasil: safras 2023/24 e 2024/25. Sete Lagoas: Associação Brasileira de Milho e Sorgo, 2024. Cap. 8: Manejo integrado de pragas da cultura do milho e sorgo, p. 89-94. Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1168645/1/MANEJO-INTEGRADO-DE-PRAGAS-DA-CULTURA-DO-MILHO-E-SORGO.pdf. Acesso em: 23 nov. 2026.",
      "VIANA, P. A. (ed.). Principais pragas subterrâneas do milho no Brasil. Sete Lagoas: Embrapa Milho e Sorgo, 2011. 61 p. (Embrapa Milho e Sorgo. Documentos, 129). ISSN 1518-4277. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/914556/1/doc129.pdf. Acesso em: 23 nov. 2026.",
      "VIANA, P. A.; CRUZ, I.; WAQUIL, J. M. Cultivo do milho: pragas iniciais. Sete Lagoas: Embrapa Milho e Sorgo, 2002. (Embrapa Milho e Sorgo. Comunicado Técnico, 59). ISSN 1679-0162. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/487021/1/Com59.pdf. Acesso em: 23 nov. 2026.",
      "WORDELL FILHO, J. A. et al. Pragas e doenças do milho: diagnose, danos e estratégias de manejo. Florianópolis: Epagri, 2016. (Epagri. Boletim Técnico, 170). ISSN 0100-7416. Disponível em: https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "1": {
    "title": "Cigarrinha-do-milho",
    "scientificName": "Dalbulus maidis",
    "context": "Descrição baseada em publicações sobre a cultura do milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto muito pequeno: cerca de 4 mm, cor de palha, com manchas pretas no abdômen e duas manchas pretas na cabeça.",
            "source": "WAQUIL, 2004, p. 1"
          },
          {
            "text": "Os adultos costumam ficar e se alimentar dentro do cartucho do milho.",
            "source": "WAQUIL, 2004, p. 1"
          },
          {
            "text": "As ninfas também têm cor de palha, mas o abdômen é manchado de escuro e os olhos são pretos. Ficam quietas na folha e só andam se forem incomodadas.",
            "source": "WAQUIL, 2004, p. 2"
          },
          {
            "text": "Os ovos são minúsculos (menos de 1 mm), translúcidos e ficam dentro da nervura central da folha.",
            "source": "WAQUIL, 2004, p. 2"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "O principal problema é que ela transmite doenças: os enfezamentos (pálido e vermelho) e o rayado fino.",
            "source": "WAQUIL, 2004, p. 1"
          },
          {
            "text": "Enfezamento pálido: na base das folhas novas surgem listras largas, amareladas ou verde-limão; as folhas mais velhas ficam amareladas ou avermelhadas.",
            "source": "WAQUIL, 2004, p. 3"
          },
          {
            "text": "Enfezamento vermelho: folhas velhas avermelhadas e, depois, a planta toda avermelhada ou amarelada, mais baixa, com aspecto de arbusto e espigas mal granadas.",
            "source": "WAQUIL, 2004, p. 4"
          },
          {
            "text": "Rayado fino: pontinhos amarelados alinhados nas folhas, que se juntam em riscas finas.",
            "source": "WAQUIL, 2004, p. 4"
          },
          {
            "text": "Os sintomas aparecem de cerca de uma a quatro semanas depois da infecção, conforme a doença, e às vezes são leves ou nem aparecem.",
            "source": "WAQUIL, 2004, p. 3-4"
          },
          {
            "text": "Quanto mais cedo a planta é infectada, maior o prejuízo.",
            "source": "WAQUIL, 2004, p. 4"
          },
          {
            "text": "Conforme a idade em que foi infectada, a planta pode ficar com entrenós curtos, espigas pequenas, pendão deformado ou nem formar a espiga.",
            "source": "WAQUIL, 2004, p. 3"
          },
          {
            "text": "Além dos enfezamentos, ela transmite a virose-da-risca e o mosaico-estriado-do-milho.",
            "source": "EICHOLZ et al., 2024, p. 91"
          },
          {
            "text": "As perdas de produtividade podem passar de 90%, conforme o híbrido, o momento da infecção e o clima.",
            "source": "EICHOLZ et al., 2024, p. 91"
          },
          {
            "text": "Nas plantas com enfezamento são comuns planta mais baixa, várias espigas pequenas e espigas e grãos mal formados.",
            "source": "EICHOLZ et al., 2024, p. 92"
          },
          {
            "text": "Virose-da-risca: pontinhos amarelados alinhados e planta menor. Mosaico-estriado: manchas e estrias claras e planta bem mais baixa.",
            "source": "EICHOLZ et al., 2024, p. 92"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "As doenças que ela transmite se parecem e podem ocorrer juntas na mesma planta; só pelo olhar é difícil dizer qual é qual.",
            "source": "EICHOLZ et al., 2024, p. 92"
          }
        ]
      }
    ],
    "sources": [
      "WAQUIL, 2004, p. 1-4",
      "EICHOLZ et al., 2024, p. 91-92"
    ],
    "references": [
      "WAQUIL, J. M. Cigarrinha-do-milho: vetor de molicutes e vírus. Sete Lagoas: Embrapa Milho e Sorgo, 2004. 6 p. (Embrapa Milho e Sorgo. Circular Técnica, 41). ISSN 1518-4269. Disponível em: https://www.embrapa.br/documents/1344498/2767891/cigarrinha-do-milho-vetor-de-molicutes-e-virus.pdf/17d847e1-e4f1-4000-9d4f-7b7a0c720fd0. Acesso em: 20 nov. 2026.",
      "EICHOLZ, E. D. et al. (ed.). Informações técnicas para o cultivo de milho e sorgo na região subtropical do Brasil: safras 2023/24 e 2024/25. Sete Lagoas: Associação Brasileira de Milho e Sorgo, 2024. Cap. 8: Manejo integrado de pragas da cultura do milho e sorgo, p. 89-94. Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1168645/1/MANEJO-INTEGRADO-DE-PRAGAS-DA-CULTURA-DO-MILHO-E-SORGO.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "2": {
    "title": "Percevejo-barriga-verde",
    "scientificName": "Diceraeus spp. (ex-Dichelops)",
    "context": "Descrição baseada em manual sobre a cultura da soja, que usa o nome Dichelops, e em publicações sobre o milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto de 9 a 11 mm, castanho-amarelado a acinzentado, com a barriga verde.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 84"
          },
          {
            "text": "A cabeça termina em duas pontas, e a frente do tórax tem bordas serrilhadas e espinhos nas laterais.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 84"
          },
          {
            "text": "As ninfas são castanhas, com a barriga mais clara e pontinhos escuros. Logo depois de nascer ficam juntas sobre os ovos e depois se espalham.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 84"
          },
          {
            "text": "Os ovos são verde-claros, postos em grupos de cerca de 14, nas folhas ou nas vagens.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 84"
          },
          {
            "text": "O D. melacanthus mede cerca de 9 mm, tem o dorso pardo e a barriga verde-clara, e o espinho de cada lado do tórax tem a ponta marrom-escura.",
            "source": "WORDELL FILHO et al., 2016, p. 34"
          },
          {
            "text": "As ninfas têm a barriga esverdeada e o dorso pardo, com manchas arroxeadas na cabeça e no tórax e avermelhadas no abdome.",
            "source": "WORDELL FILHO et al., 2016, p. 34"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Ninfas e adultos sugam as vagens e estragam os grãos, o que reduz a produtividade e a qualidade da soja.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 84"
          },
          {
            "text": "Também ocorre em milho e trigo, com danos sérios principalmente em plantas jovens de milho.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 84"
          },
          {
            "text": "No milho, adultos e ninfas sugam a base das plantas novas, logo depois da emergência; ao abrirem, as folhas mostram furos simétricos com halos amarelados.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 4-5"
          },
          {
            "text": "A planta atacada pode ficar deformada, soltar perfilhos que não produzem e até morrer.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 5"
          },
          {
            "text": "As folhas ficam retorcidas, com furos perpendiculares às nervuras; a planta cresce devagar e pode dar espigas pequenas.",
            "source": "EICHOLZ et al., 2024, p. 91"
          },
          {
            "text": "Quando o sintoma aparece, o dano já aconteceu e não tem volta.",
            "source": "EICHOLZ et al., 2024, p. 91"
          },
          {
            "text": "Plantas com mais de 5 folhas abertas, ou com colmo de mais de 1 cm de espessura, sofrem pouco; quanto menor a planta, maior o estrago.",
            "source": "EICHOLZ et al., 2024, p. 91"
          },
          {
            "text": "É praga típica da soja, mas passou a atacar o milho plantado em sucessão ou rotação com ela, logo após a emergência.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 4"
          },
          {
            "text": "Um único percevejo pode estragar até seis plantas vizinhas.",
            "source": "WORDELL FILHO et al., 2016, p. 34"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de percevejo-verde.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 84",
      "WORDELL FILHO et al., 2016, p. 34",
      "VIANA; CRUZ; WAQUIL, 2002, p. 4-5",
      "EICHOLZ et al., 2024, p. 91",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "WORDELL FILHO, J. A. et al. Pragas e doenças do milho: diagnose, danos e estratégias de manejo. Florianópolis: Epagri, 2016. (Epagri. Boletim Técnico, 170). ISSN 0100-7416. Disponível em: https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf. Acesso em: 23 nov. 2026.",
      "VIANA, P. A.; CRUZ, I.; WAQUIL, J. M. Cultivo do milho: pragas iniciais. Sete Lagoas: Embrapa Milho e Sorgo, 2002. (Embrapa Milho e Sorgo. Comunicado Técnico, 59). ISSN 1679-0162. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/487021/1/Com59.pdf. Acesso em: 23 nov. 2026.",
      "EICHOLZ, E. D. et al. (ed.). Informações técnicas para o cultivo de milho e sorgo na região subtropical do Brasil: safras 2023/24 e 2024/25. Sete Lagoas: Associação Brasileira de Milho e Sorgo, 2024. Cap. 8: Manejo integrado de pragas da cultura do milho e sorgo, p. 89-94. Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1168645/1/MANEJO-INTEGRADO-DE-PRAGAS-DA-CULTURA-DO-MILHO-E-SORGO.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "3": {
    "title": "Lagarta-do-cartucho",
    "scientificName": "Spodoptera frugiperda",
    "context": "Descrição baseada em manual sobre a cultura da soja, que usa o título lagarta-das-vagens, e em publicações sobre o milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Lagarta crescida: de 35 a 40 mm, com pontos pretos em pares dos dois lados de cada segmento do corpo, cada ponto com um pelo longo.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 74"
          },
          {
            "text": "No último segmento do corpo há quatro pontos pretos, dispostos como os cantos de um quadrado.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 74"
          },
          {
            "text": "A cabeça tem um desenho de épsilon invertido, mas só isso não basta para confirmar a espécie.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 74"
          },
          {
            "text": "O adulto é uma mariposa de 32 a 38 mm com as asas abertas: asas da frente cinza-amarronzadas (mais escuras nos machos) e asas de trás branco-prateadas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 74"
          },
          {
            "text": "Os ovos são quase redondos, postos em camadas e cobertos por escamas do abdômen da fêmea.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 74"
          },
          {
            "text": "A lagarta recém-nascida tem a cabeça preta e o corpo claro; escurece a partir dos 3 dias de vida.",
            "source": "VALICENTE, 2015, p. 5"
          },
          {
            "text": "A pupa fica no solo, é marrom-avermelhada e mede de 14 a 18 mm.",
            "source": "VALICENTE, 2015, p. 5"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Na soja, pode atacar as vagens.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 74"
          },
          {
            "text": "É uma das principais pragas do milho: sem controle, pode reduzir a produção em 34% a 52%.",
            "source": "VALICENTE, 2015, p. 4"
          },
          {
            "text": "Lagartas novas raspam só um lado da folha; depois do 2º ou 3º estágio passam a furá-la.",
            "source": "VALICENTE, 2015, p. 5"
          },
          {
            "text": "Comendo no cartucho, deixam uma fileira de furos nas folhas, e o cartucho pode ficar totalmente destruído.",
            "source": "VALICENTE, 2015, p. 5-6"
          },
          {
            "text": "Dentro do cartucho aparecem também os excrementos da lagarta.",
            "source": "EICHOLZ et al., 2024, p. 92"
          },
          {
            "text": "Em plantas novas pode matar a planta, principalmente quando o milho é semeado logo depois da dessecação, no plantio direto.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 6"
          },
          {
            "text": "O estrago é maior quando o ataque acontece em plantas com até 8 a 10 folhas abertas.",
            "source": "EICHOLZ et al., 2024, p. 92"
          },
          {
            "text": "Também ataca a espiga, entrando pela base, pela ponta ou pelo meio.",
            "source": "VALICENTE, 2015, p. 5"
          },
          {
            "text": "No milho, pode cortar a planta rente ao solo, como a lagarta-rosca, e reduzir o número de plantas na lavoura.",
            "source": "EICHOLZ et al., 2024, p. 90"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Lagarta-rosca: nas plantas novas de milho os sintomas podem ser parecidos, com a planta cortada rente ao solo.",
            "source": "VALICENTE, 2015, p. 5"
          },
          {
            "text": "As lagartas do gênero Spodoptera se parecem muito, e é difícil diferenciar as espécies.",
            "source": "TEODORO et al., 2013, p. 2"
          },
          {
            "text": "Na espiga, a lagarta rasga a palha ao sair para virar pupa, e isso a diferencia da lagarta-da-espiga.",
            "source": "EICHOLZ et al., 2024, p. 92"
          },
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de lagarta-falsa-medideira ou de lagarta-das-vagens.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 74",
      "VALICENTE, 2015, p. 4-6",
      "EICHOLZ et al., 2024, p. 90-92",
      "VIANA; CRUZ; WAQUIL, 2002, p. 6",
      "TEODORO et al., 2013, p. 2",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "VALICENTE, F. H. Manejo integrado de pragas na cultura do milho. Sete Lagoas: Embrapa Milho e Sorgo, 2015. (Embrapa Milho e Sorgo. Circular Técnica, 208). ISSN 1679-1150. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1017489/1/circ208.pdf. Acesso em: 23 nov. 2026.",
      "EICHOLZ, E. D. et al. (ed.). Informações técnicas para o cultivo de milho e sorgo na região subtropical do Brasil: safras 2023/24 e 2024/25. Sete Lagoas: Associação Brasileira de Milho e Sorgo, 2024. Cap. 8: Manejo integrado de pragas da cultura do milho e sorgo, p. 89-94. Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1168645/1/MANEJO-INTEGRADO-DE-PRAGAS-DA-CULTURA-DO-MILHO-E-SORGO.pdf. Acesso em: 23 nov. 2026.",
      "VIANA, P. A.; CRUZ, I.; WAQUIL, J. M. Cultivo do milho: pragas iniciais. Sete Lagoas: Embrapa Milho e Sorgo, 2002. (Embrapa Milho e Sorgo. Comunicado Técnico, 59). ISSN 1679-0162. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/487021/1/Com59.pdf. Acesso em: 23 nov. 2026.",
      "TEODORO, A. V. et al. Spodoptera cosmioides (Walker) e Spodoptera eridania (Cramer) (Lepidoptera: Noctuidae): novas pragas de cultivos da Região Nordeste. Aracaju: Embrapa Tabuleiros Costeiros, 2013. (Embrapa Tabuleiros Costeiros. Comunicado Técnico, 131). ISSN 1679-1937. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/977975/1/cot131.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "4": {
    "title": "Percevejo-marrom",
    "scientificName": "Euschistus heros",
    "context": "Descrição baseada em manual e circular sobre a cultura da soja e em publicação sobre o milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto marrom-escuro, com dois pequenos espinhos nas laterais, perto da cabeça.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 78"
          },
          {
            "text": "A ninfa recém-nascida tem cerca de 1 mm, corpo alaranjado e cabeça preta. Passa por cinco fases e, nas maiores, a cor varia do cinza ao marrom.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 78"
          },
          {
            "text": "Os ovos são amarelados, postos nas folhas em pequenos grupos de 5 a 7; perto de nascer, ganham uma mancha rosada.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 78"
          },
          {
            "text": "O adulto mede cerca de 11 mm e tem uma mancha branca em forma de meia-lua na ponta de trás do escudo (escutelo).",
            "source": "EICHOLZ et al., 2024, p. 91"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Adultos e ninfas sugam vagens e grãos, o que reduz a produtividade e piora a qualidade da semente.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 78"
          },
          {
            "text": "Provoca menos sintomas de retenção foliar do que o percevejo-verde e o percevejo-verde-pequeno.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 78"
          },
          {
            "text": "Ninfas do 3º ao 5º estágio também estragam os grãos da soja.",
            "source": "HOFFMANN-CAMPO et al., 2000, p. 24"
          },
          {
            "text": "Em milho safrinha, plantado depois da soja, pode aparecer em grande número; sintomas e fase crítica são parecidos com os do barriga-verde.",
            "source": "EICHOLZ et al., 2024, p. 91"
          },
          {
            "text": "No milho ele também pesa, sobretudo onde o clima é mais quente.",
            "source": "WORDELL FILHO et al., 2016, p. 36"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 78",
      "EICHOLZ et al., 2024, p. 91",
      "HOFFMANN-CAMPO et al., 2000, p. 24",
      "WORDELL FILHO et al., 2016, p. 36"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "EICHOLZ, E. D. et al. (ed.). Informações técnicas para o cultivo de milho e sorgo na região subtropical do Brasil: safras 2023/24 e 2024/25. Sete Lagoas: Associação Brasileira de Milho e Sorgo, 2024. Cap. 8: Manejo integrado de pragas da cultura do milho e sorgo, p. 89-94. Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1168645/1/MANEJO-INTEGRADO-DE-PRAGAS-DA-CULTURA-DO-MILHO-E-SORGO.pdf. Acesso em: 23 nov. 2026.",
      "HOFFMANN-CAMPO, C. B. et al. Pragas da soja no Brasil e seu manejo integrado. Londrina: Embrapa Soja, 2000. 70 p. (Embrapa Soja. Circular Técnica, 30). ISSN 1516-7860. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/449719/1/ID6173.pdf. Acesso em: 23 nov. 2026.",
      "WORDELL FILHO, J. A. et al. Pragas e doenças do milho: diagnose, danos e estratégias de manejo. Florianópolis: Epagri, 2016. (Epagri. Boletim Técnico, 170). ISSN 0100-7416. Disponível em: https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "5": {
    "title": "Percevejo-verde",
    "scientificName": "Nezara viridula",
    "context": "Descrição baseada em manual e circular sobre a cultura da soja e em publicação sobre o milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto totalmente verde, de 12 a 15 mm; solta mau cheiro quando incomodado (por isso, \"maria-fedida\" ou \"fede-fede\").",
            "source": "SOSA-GÓMEZ et al., 2014, p. 82"
          },
          {
            "text": "A ninfa é verde ou preta, com manchas redondas brancas e pontinhos pretos pelo corpo; passa por cinco fases e se desenvolve em cerca de 25 dias.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 82"
          },
          {
            "text": "Os ovos são amarelados, postos de preferência na face de baixo das folhas, em massas regulares de 50 a 100, parecidas com favos de colmeia.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 82"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Ninfas e adultos causam dano parecido com o dos outros percevejos da soja.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 82"
          },
          {
            "text": "A capacidade de provocar haste verde é maior que a do percevejo-marrom e menor que a do percevejo-verde-pequeno.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 82"
          },
          {
            "text": "As ninfas só começam a comer os grãos de soja a partir do 3º estágio, e o estrago cresce até o 5º, o último.",
            "source": "HOFFMANN-CAMPO et al., 2000, p. 22"
          },
          {
            "text": "Também ataca o milho novo semeado depois da soja, junto com o percevejo-barriga-verde.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 4"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de percevejo-asa-preta.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 82",
      "HOFFMANN-CAMPO et al., 2000, p. 22",
      "VIANA; CRUZ; WAQUIL, 2002, p. 4",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "HOFFMANN-CAMPO, C. B. et al. Pragas da soja no Brasil e seu manejo integrado. Londrina: Embrapa Soja, 2000. 70 p. (Embrapa Soja. Circular Técnica, 30). ISSN 1516-7860. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/449719/1/ID6173.pdf. Acesso em: 23 nov. 2026.",
      "VIANA, P. A.; CRUZ, I.; WAQUIL, J. M. Cultivo do milho: pragas iniciais. Sete Lagoas: Embrapa Milho e Sorgo, 2002. (Embrapa Milho e Sorgo. Comunicado Técnico, 59). ISSN 1679-0162. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/487021/1/Com59.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "6": {
    "title": "Percevejo-asa-preta",
    "scientificName": "Edessa meditabunda",
    "context": "Descrição baseada em manual e circular sobre a cultura da soja, que chamam a espécie de percevejo-edessa, e em resumo da Embrapa Soja.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto de 13 mm, de corpo oval, com a cabeça e parte do tórax verdes e as asas marrom-escuras.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 86"
          },
          {
            "text": "A ninfa é verde-amarelada, com antenas e pernas da mesma cor; a barriga é amarelo-escura e brilhante.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 86"
          },
          {
            "text": "Os ovos são verde-claros, em geral nas folhas, em massas de 14 ovos dispostos em duas fileiras.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 86"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Os danos são parecidos com os dos outros percevejos que sugam sementes, mas a capacidade de dano é menor.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 86"
          },
          {
            "text": "Também pode sugar caules e causar lesões escuras.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 86"
          },
          {
            "text": "Em geral, as populações não são elevadas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 86"
          },
          {
            "text": "Sozinha, a espécie costuma não formar populações que ameacem a produtividade, mas o dano dela se soma ao dos percevejos principais.",
            "source": "HOFFMANN-CAMPO et al., 2000, p. 25"
          },
          {
            "text": "É um percevejo secundário da soja, que ataca só de vez em quando.",
            "source": "CANTONE et al., [2011?], p. 16"
          },
          {
            "text": "O bico é mais curto que o dos principais percevejos da soja; por isso, as ninfas não completam o desenvolvimento só com vagens e precisam comer folhas também.",
            "source": "CANTONE et al., [2011?], p. 16"
          },
          {
            "text": "As ninfas ficam agrupadas e comem com frequência, o que pode causar danos importantes à planta.",
            "source": "CANTONE et al., [2011?], p. 16"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 86",
      "HOFFMANN-CAMPO et al., 2000, p. 25",
      "CANTONE et al., [2011?], p. 16"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "HOFFMANN-CAMPO, C. B. et al. Pragas da soja no Brasil e seu manejo integrado. Londrina: Embrapa Soja, 2000. 70 p. (Embrapa Soja. Circular Técnica, 30). ISSN 1516-7860. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/449719/1/ID6173.pdf. Acesso em: 23 nov. 2026.",
      "CANTONE, W. et al. Danos de percevejos em sementes de soja. In: JORNADA ACADÊMICA DA EMBRAPA SOJA, 6., [2011?], Londrina. Resumos expandidos. Londrina: Embrapa Soja, [2011?]. p. 16-20. (Embrapa Soja. Documentos, 328). Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/909203/1/danos.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "7": {
    "title": "Percevejo-do-milho",
    "scientificName": "Leptoglossus zonatus",
    "context": "Descrição baseada em textos sobre a cultura do milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto com cerca de 20 mm, marrom-escuro, com duas manchas amarelas redondas na frente do tórax.",
            "source": "ÁVILA; PAPA, s.d., seção “Percevejo-do-milho”"
          },
          {
            "text": "Nas asas da frente há uma faixa amarela em zigue-zague, e as pernas de trás têm um alargamento em forma de folha.",
            "source": "ÁVILA; PAPA, s.d., seção “Percevejo-do-milho”"
          },
          {
            "text": "As fêmeas costumam ser maiores que os machos.",
            "source": "MATRANGOLO; WAQUIL, 1994, p. 421"
          },
          {
            "text": "Os ovos são postos enfileirados, grudados na superfície; são esverdeados no início e ficam marrons em algumas horas.",
            "source": "MATRANGOLO; WAQUIL, 1994, p. 421"
          },
          {
            "text": "As ninfas ficam agrupadas até o fim do 2º estágio e depois se espalham. Em milho, a maioria foi encontrada nas folhas.",
            "source": "MATRANGOLO; WAQUIL, 1994, p. 421-422"
          },
          {
            "text": "As ninfas são alaranjadas e, no começo da vida, ficam agrupadas.",
            "source": "WORDELL FILHO et al., 2016, p. 38"
          },
          {
            "text": "Do ovo ao adulto o ciclo dura de 40 a 60 dias.",
            "source": "WORDELL FILHO et al., 2016, p. 38"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Adultos e ninfas sugam os grãos do milho. Os adultos ficam sobre as espigas e furam a palha para chegar aos grãos.",
            "source": "MATRANGOLO; WAQUIL, 1994, p. 422"
          },
          {
            "text": "O furo da picada deixa entrar fungos. O resultado é espiga com falhas e grãos murchos e podres.",
            "source": "ÁVILA; PAPA, s.d., seção “Percevejo-do-milho”"
          },
          {
            "text": "Há relatos de grãos contaminados por fungos, entre eles Fusarium moniliforme, Penicillium e Cephalosporium.",
            "source": "MATRANGOLO; WAQUIL, 1994, p. 420"
          },
          {
            "text": "Prefere espigas de palha aberta, em que as sementes ficam mais expostas.",
            "source": "ÁVILA; PAPA, s.d., seção “Percevejo-do-milho”"
          },
          {
            "text": "Também é citado em sorgo, laranja e tomate.",
            "source": "MATRANGOLO; WAQUIL, 1994, p. 420"
          },
          {
            "text": "No milho, o ataque pode reduzir a produtividade em cerca de 15%.",
            "source": "WORDELL FILHO et al., 2016, p. 38"
          },
          {
            "text": "Ninfas e adultos sugam as espigas, sobretudo na fase de enchimento dos grãos, e causam murcha e manchas que impedem o uso do milho verde em conserva.",
            "source": "WORDELL FILHO et al., 2016, p. 38"
          },
          {
            "text": "Espigas atacadas têm mais grãos ardidos, o que piora a qualidade da ração e prejudica a produção de sementes.",
            "source": "WORDELL FILHO et al., 2016, p. 38"
          },
          {
            "text": "Costuma chegar às plantas de milho a partir do aparecimento dos \"cabelos\" (estilos) da espiga.",
            "source": "WORDELL FILHO et al., 2016, p. 38"
          }
        ]
      }
    ],
    "sources": [
      "ÁVILA; PAPA, s.d., seção “Percevejo-do-milho”",
      "MATRANGOLO; WAQUIL, 1994, p. 420-422",
      "WORDELL FILHO et al., 2016, p. 38"
    ],
    "references": [
      "ÁVILA, C. J.; PAPA, G. Manejo de pragas da parte aérea do milho. Cultivar Grandes Culturas, n. 199, [s. d.]. Disponível em: https://revistacultivar.com.br/artigos/manejo-de-pragas-da-parte-aerea-do-milho. Acesso em: 20 nov. 2026.",
      "MATRANGOLO, W. J. R.; WAQUIL, J. M. Biologia de Leptoglossus zonatus (Dallas) (Hemiptera: Coreidae) alimentados com milho e sorgo. Anais da Sociedade Entomológica do Brasil, Jaboticabal, v. 23, n. 3, p. 419-423, 1994. Disponível em: http://www.alice.cnptia.embrapa.br/alice/handle/doc/474805. Acesso em: 20 nov. 2026.",
      "WORDELL FILHO, J. A. et al. Pragas e doenças do milho: diagnose, danos e estratégias de manejo. Florianópolis: Epagri, 2016. (Epagri. Boletim Técnico, 170). ISSN 0100-7416. Disponível em: https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "8": {
    "title": "Lagarta-falsa-medideira",
    "scientificName": "Chrysodeixis includens",
    "context": "Descrição baseada em manual e circulares sobre a cultura da soja.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "A lagarta é verde-clara, com listras brancas ao longo do corpo e pontinhos pretos; anda \"medindo palmos\" (arqueando o corpo).",
            "source": "SOSA-GÓMEZ et al., 2014, p. 36"
          },
          {
            "text": "No último estágio chega a 40 ou 45 mm e vira pupa sob uma teia, em geral na face de baixo das folhas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 36"
          },
          {
            "text": "O adulto é uma mariposa que mantém as asas inclinadas; logo depois de sair da pupa, mostra manchas prateadas brilhantes no meio das asas da frente.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 36"
          },
          {
            "text": "A lagarta tem três pares de patas na frente, dois pares de falsas pernas no abdome e um par na ponta; por isso o corpo se arqueia ao andar.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 4"
          },
          {
            "text": "Os ovos são postos um a um, em geral na face de baixo das folhas; são cremes e brilhantes no começo e ficam marrom-claros perto de nascer.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 4"
          },
          {
            "text": "A mariposa mede cerca de 35 mm com as asas abertas; as asas da frente são escuras, com duas manchas prateadas no centro, e as de trás são marrons.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 8"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "A lagarta come o tecido da folha e deixa as nervuras, o que dá aos folíolos um aspecto rendilhado.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 36"
          },
          {
            "text": "Cada lagarta come de 64 a 200 cm² de folha de soja, o que pode reduzir bastante a área que a planta usa para fazer fotossíntese.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 7"
          },
          {
            "text": "Até o 3º estágio as lagartas só raspam a folha; do 4º em diante furam e comem grandes áreas.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 7"
          },
          {
            "text": "Ela costuma ficar na parte de baixo das plantas de soja, onde fica mais protegida.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 3"
          },
          {
            "text": "Quando aparece junto com a lagarta-da-soja, ou depois dela, a desfolha da lavoura aumenta.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 2"
          },
          {
            "text": "Come mais de 170 espécies de plantas, mas prefere a soja.",
            "source": "BOTELHO; SILVA; ÁVILA, 2019, p. 2"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Rachiplusia nu, mais frequente no Sul do Brasil; só um detalhe das mandíbulas ajuda a separar as duas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 36"
          },
          {
            "text": "Enquanto pequenas, as lagartas da lagarta-da-soja são fáceis de trocar pelas da falsa-medideira.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 34-36",
      "BOTELHO; SILVA; ÁVILA, 2019, p. 2-8"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "BOTELHO, A. B. R. Z.; SILVA, I. F. da; ÁVILA, C. J. Aspectos biológicos da lagarta-falsa-medideira e sua criação em laboratório com dieta artificial. Dourados: Embrapa Agropecuária Oeste, 2019. (Embrapa Agropecuária Oeste. Circular Técnica, 47). ISSN 1679-0464. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1118272/1/36927.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "9": {
    "title": "Lagarta-da-soja",
    "scientificName": "Anticarsia gemmatalis",
    "context": "Descrição baseada em manual e circular sobre a cultura da soja.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Lagarta pequena (até 10 mm), em geral verde, com quatro pares de pernas falsas no abdômen, duas delas reduzidas; por isso anda \"medindo palmos\".",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "Lagartas maiores que 15 mm podem ser verdes ou escuras e têm três linhas brancas no dorso.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "O adulto é uma mariposa cinza-clara a marrom-escura, sempre com uma linha diagonal marrom-canela ligando as pontas das asas da frente.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "Os ovos são verde-claros, postos um a um, principalmente na face de baixo das folhas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "Os ovos mudam de cor: de verde-claro passam a acinzentados e, perto de nascer, a marrom-escuros.",
            "source": "HOFFMANN-CAMPO et al., 2000, p. 13"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "A partir do 3º estágio a lagarta fura as folhas, mas deixa as nervuras.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "Do 4º ao 6º estágio ela consome mais de 95% de toda a folha que come ao longo da vida.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "Em populações altas pode causar desfolha acima de 30% e perda de produtividade.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          },
          {
            "text": "Em toda a vida, uma lagarta pode consumir de 100 a 150 cm² de folha.",
            "source": "HOFFMANN-CAMPO et al., 2000, p. 13"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Enquanto pequenas, as lagartas são fáceis de trocar pelas da falsa-medideira.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 34"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 34",
      "HOFFMANN-CAMPO et al., 2000, p. 13"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "HOFFMANN-CAMPO, C. B. et al. Pragas da soja no Brasil e seu manejo integrado. Londrina: Embrapa Soja, 2000. 70 p. (Embrapa Soja. Circular Técnica, 30). ISSN 1516-7860. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/449719/1/ID6173.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "10": {
    "title": "Lagarta-das-vagens",
    "scientificName": "Spodoptera eridania e S. cosmioides",
    "context": "Descrição baseada em manual sobre a cultura da soja e em comunicado técnico da Embrapa.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "A classe junta duas espécies, Spodoptera cosmioides e S. eridania, que o manual trata em fichas separadas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 70-72"
          },
          {
            "text": "As lagartas variam de amarelo-claro a preto, com listras no corpo, e podem chegar a 50 mm no último estágio (S. cosmioides).",
            "source": "SOSA-GÓMEZ et al., 2014, p. 70"
          },
          {
            "text": "No dorso há manchas triangulares pretas: em S. cosmioides as do 7º e 8º segmentos do abdômen são maiores que as dos primeiros; em S. eridania, do 1º ao 8º, são grandes e de tamanho parecido.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 70-72"
          },
          {
            "text": "Os adultos de S. cosmioides são mariposas de 16 a 20 mm; as fêmeas põem os ovos em massas sobre as folhas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 70"
          },
          {
            "text": "S. cosmioides: lagarta cinza-clara, castanha ou, mais comum, preta; no começo tem uma região escura entre o tórax e o abdômen e uma faixa laranja nas laterais.",
            "source": "TEODORO et al., 2013, p. 2"
          },
          {
            "text": "S. eridania: lagarta marrom, de até 35 mm, com uma faixa esbranquiçada nas laterais, interrompida por uma mancha escura no tórax.",
            "source": "TEODORO et al., 2013, p. 3"
          },
          {
            "text": "As lagartas de S. eridania costumam ficar na parte de baixo da planta e são mais ativas à noite.",
            "source": "TEODORO et al., 2013, p. 3"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "As lagartas atacam as vagens.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 70-72"
          },
          {
            "text": "S. eridania também desfolha soja e algodão.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 72"
          },
          {
            "text": "Podem atacar logo depois da emergência, diminuir o número de plantas e até exigir replantio.",
            "source": "TEODORO et al., 2013, p. 1"
          },
          {
            "text": "Ao longo do ciclo causam desfolha forte e também furam as vagens.",
            "source": "TEODORO et al., 2013, p. 1"
          },
          {
            "text": "São muito vorazes e atacam muitas culturas, como milho, algodão, amendoim e girassol; S. cosmioides come mais que S. eridania.",
            "source": "TEODORO et al., 2013, p. 2-3"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Spodoptera albula (fora das classes do app): o manual compara as duas espécies com ela. S. eridania tem tom bronzeado nas asas da frente.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 70-72"
          },
          {
            "text": "S. frugiperda e S. albula também são comuns nas lavouras e muito parecidas; diferenciar as espécies do gênero é difícil.",
            "source": "TEODORO et al., 2013, p. 2"
          },
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de lagarta-do-cartucho.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 70-72",
      "TEODORO et al., 2013, p. 1-3",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "TEODORO, A. V. et al. Spodoptera cosmioides (Walker) e Spodoptera eridania (Cramer) (Lepidoptera: Noctuidae): novas pragas de cultivos da Região Nordeste. Aracaju: Embrapa Tabuleiros Costeiros, 2013. (Embrapa Tabuleiros Costeiros. Comunicado Técnico, 131). ISSN 1679-1937. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/977975/1/cot131.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "11": {
    "title": "Astylus variegatus",
    "scientificName": "Astylus variegatus",
    "context": "Descrição baseada em manual sobre a cultura da soja e em publicação sobre pragas do milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto com cerca de 8 mm, asas amarelas com pintas pretas.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 98"
          },
          {
            "text": "A larva vive no solo, é marrom-escura e tem pelos esparsos.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 98"
          },
          {
            "text": "Os adultos comem pólen e podem aparecer em grande número na lavoura, principalmente perto da floração.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 98"
          },
          {
            "text": "A fase de larva é longa e pode durar até um ano.",
            "source": "VIANA, 2011, p. 59"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Os adultos não causam danos; as larvas podem, de vez em quando, comer raízes.",
            "source": "SOSA-GÓMEZ et al., 2014, p. 98"
          },
          {
            "text": "No milho é praga secundária: só populações altas causam prejuízo, pois o milho é semeado com poucas sementes por área.",
            "source": "VIANA, 2011, p. 58"
          },
          {
            "text": "As larvas comem sobretudo as sementes depois do plantio e as raízes, o que reduz a germinação e o número de plantas.",
            "source": "VIANA, 2011, p. 58"
          },
          {
            "text": "É praga ocasional no início do milho: pode danificar as sementes e as raízes e prejudicar a formação da lavoura.",
            "source": "WORDELL FILHO et al., 2016, p. 42"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de vaquinha.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SOSA-GÓMEZ et al., 2014, p. 98",
      "VIANA, 2011, p. 58-59",
      "WORDELL FILHO et al., 2016, p. 42",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SOSA-GÓMEZ, D. R. et al. Manual de identificação de insetos e outros invertebrados da cultura da soja. 3. ed. Londrina: Embrapa Soja, 2014. (Embrapa Soja. Documentos, 269). ISSN 1516-781X. Disponível em: https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/991685/manual-de-identificacao-de-insetos-e-outros-invertebrados-da-cultura-da-soja. Acesso em: 8 nov. 2026.",
      "VIANA, P. A. (ed.). Principais pragas subterrâneas do milho no Brasil. Sete Lagoas: Embrapa Milho e Sorgo, 2011. 61 p. (Embrapa Milho e Sorgo. Documentos, 129). ISSN 1518-4277. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/914556/1/doc129.pdf. Acesso em: 23 nov. 2026.",
      "WORDELL FILHO, J. A. et al. Pragas e doenças do milho: diagnose, danos e estratégias de manejo. Florianópolis: Epagri, 2016. (Epagri. Boletim Técnico, 170). ISSN 0100-7416. Disponível em: https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  },
  "12": {
    "title": "Cigarrinha-das-pastagens",
    "scientificName": "Deois flavopicta",
    "context": "Descrição baseada em material sobre pastagens e em publicações sobre o milho.",
    "sections": [
      {
        "id": "como_reconhecer",
        "title": "Como reconhecer",
        "items": [
          {
            "text": "Adulto de cerca de 10 mm, preto, com duas faixas amarelas atravessadas nas asas; abdômen e pernas vermelhos.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          },
          {
            "text": "Os adultos vivem na parte de cima das gramíneas; as ninfas ficam na base das plantas, protegidas por uma espuma branca.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          }
        ]
      },
      {
        "id": "danos",
        "title": "Danos ou sintomas",
        "items": [
          {
            "text": "Suga a seiva e, ao picar, injeta toxinas na planta.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          },
          {
            "text": "Essas toxinas amarelam, secam e matam as folhas, efeito conhecido como \"queima\" do pasto.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          },
          {
            "text": "Ataca principalmente em épocas de muita umidade.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          },
          {
            "text": "No milho só os adultos atacam; as ninfas não vivem na lavoura.",
            "source": "CRUZ et al., 2010, p. 2"
          },
          {
            "text": "Os adultos vêm de pastos vizinhos, principalmente de braquiária, porque o milho não permite à cigarrinha completar o ciclo.",
            "source": "VIANA; CRUZ; WAQUIL, 2002, p. 6"
          },
          {
            "text": "Eles sugam a seiva: as folhas amarelam e secam, e a planta nova pode morrer.",
            "source": "CRUZ et al., 2010, p. 2"
          },
          {
            "text": "O amarelo aparece em estrias nas folhas e nos colmos.",
            "source": "EICHOLZ et al., 2024, p. 93"
          },
          {
            "text": "As plantas mais novas, até uns 20 dias, são as mais sensíveis: chegaram a secar com 3 a 4 cigarrinhas por planta.",
            "source": "EICHOLZ et al., 2024, p. 93"
          },
          {
            "text": "Em teste da Embrapa, milho novo (fase V2) com 2 adultos por planta ficou amarelado em mais de 70% das folhas em 8 dias.",
            "source": "CRUZ et al., 2010, p. 1"
          }
        ]
      },
      {
        "id": "confusao",
        "title": "Pode ser confundido com",
        "items": [
          {
            "text": "Deois schach: também tem cerca de 10 mm e abdômen e pernas vermelhos, mas é preta-esverdeada e tem uma faixa laranja perto da ponta da asa.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          },
          {
            "text": "Zulia entreriana: menor (cerca de 7 mm), preta e brilhante, com uma faixa branco-amarelada perto da ponta da asa.",
            "source": "SANTOS; BALSALOBRE, 2002, p. 1"
          },
          {
            "text": "No milho também aparecem outras cigarrinhas-das-pastagens, como as do gênero Mahanarva e a Deois flexuosa, com danos parecidos.",
            "source": "WORDELL FILHO et al., 2016, p. 44"
          },
          {
            "text": "Em testes, o app às vezes indicou esta praga quando a foto era de percevejo-do-milho.",
            "source": "Análise de erros do modelo (seção 6.4 do Projeto.md)"
          }
        ]
      }
    ],
    "sources": [
      "SANTOS; BALSALOBRE, 2002, p. 1",
      "CRUZ et al., 2010, p. 1-2",
      "VIANA; CRUZ; WAQUIL, 2002, p. 6",
      "EICHOLZ et al., 2024, p. 93",
      "WORDELL FILHO et al., 2016, p. 44",
      "Análise de erros do modelo (seção 6.4 do Projeto.md)"
    ],
    "references": [
      "SANTOS, P. M.; BALSALOBRE, M. A. A. Cigarrinha das pastagens. 1. Caracterização. MilkPoint, 2002. 3 p. Disponível em: http://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/46239. Acesso em: 20 nov. 2026.",
      "CRUZ, I.; FIGUEIREDO, M. de L. C.; GONTIJO NETO, M. M.; SILVA, R. B. da. Danos da cigarrinha-das-pastagens, Deois flavopicta Stal (Homoptera: Cercopidae) em milho consorciado com braquiárias. Sete Lagoas: Embrapa Milho e Sorgo, 2010. (Embrapa Milho e Sorgo. Circular Técnica, 144). ISSN 1679-1150. Disponível em: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/880841/1/circ144.pdf. Acesso em: 23 nov. 2026.",
      "VIANA, P. A.; CRUZ, I.; WAQUIL, J. M. Cultivo do milho: pragas iniciais. Sete Lagoas: Embrapa Milho e Sorgo, 2002. (Embrapa Milho e Sorgo. Comunicado Técnico, 59). ISSN 1679-0162. Disponível em: https://www.infoteca.cnptia.embrapa.br/bitstream/doc/487021/1/Com59.pdf. Acesso em: 23 nov. 2026.",
      "EICHOLZ, E. D. et al. (ed.). Informações técnicas para o cultivo de milho e sorgo na região subtropical do Brasil: safras 2023/24 e 2024/25. Sete Lagoas: Associação Brasileira de Milho e Sorgo, 2024. Cap. 8: Manejo integrado de pragas da cultura do milho e sorgo, p. 89-94. Disponível em: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1168645/1/MANEJO-INTEGRADO-DE-PRAGAS-DA-CULTURA-DO-MILHO-E-SORGO.pdf. Acesso em: 23 nov. 2026.",
      "WORDELL FILHO, J. A. et al. Pragas e doenças do milho: diagnose, danos e estratégias de manejo. Florianópolis: Epagri, 2016. (Epagri. Boletim Técnico, 170). ISSN 0100-7416. Disponível em: https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf. Acesso em: 23 nov. 2026."
    ],
    "author": "Equipe do projeto AgroApp (Inteli)",
    "reviewedAt": "2026-11-23",
    "validated": true
  }
};
