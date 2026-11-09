// Gerado por `python -m src.associacao_conteudo_t9_3 frontend` (T9.3). Não edite à mão:
// altere associacao_classes.json e base_conteudo.json em assets/data/conteudo_T9_3 e gere de novo.
export interface TechnicalContent {
  title: string;
  text: string;
  source: string;
  reviewedAt: string;
  validated: boolean;
}

// Chaves são os índices de classes.json do modelo versionado.
export const technicalContent: Partial<Record<number, TechnicalContent>> = {};
