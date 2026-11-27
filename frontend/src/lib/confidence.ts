import parametros from "../../../assets/data/politica_T6_5/parametros.json";
import type { Prediction } from "../types";

// A política versionada é empacotada no app; não exige uma chamada de rede.
export const politicaConfianca = Object.freeze({
  limiar: parametros.limiar_confianca,
  numeroHipoteses: parametros.numero_hipoteses,
  mensagem: parametros.abaixo_do_limiar.mensagem,
  orientacao: parametros.abaixo_do_limiar.orientacao_nova_foto,
});

if (
  parametros.regra_limiar !== "top1_maior_ou_igual" ||
  parametros.abaixo_do_limiar.indica_classe !== false ||
  !Number.isFinite(politicaConfianca.limiar) ||
  politicaConfianca.limiar < 0 || politicaConfianca.limiar > 1 ||
  !Number.isInteger(politicaConfianca.numeroHipoteses) ||
  politicaConfianca.numeroHipoteses < 1
) {
  throw new Error("Política de confiança incompatível com o aplicativo.");
}

export type ConfidenceResult =
  | { status: "aceito"; hipoteses: Prediction[] }
  | { status: "inconclusivo"; hipoteses: [] };

export function avaliarConfianca(predictions: readonly Prediction[]): ConfidenceResult {
  // Scores inválidos também ficam sem identificação; não escolher uma classe
  // depois de ignorar silenciosamente parte de uma saída inconsistente.
  if (
    !predictions.length ||
    predictions.some((p) => !Number.isFinite(p.score) || p.score < 0 || p.score > 1) ||
    new Set(predictions.map((p) => p.indice)).size !== predictions.length
  ) {
    return { status: "inconclusivo", hipoteses: [] };
  }
  const ordenadas = [...predictions].sort((a, b) => b.score - a.score || a.indice - b.indice);
  if (ordenadas[0].score < politicaConfianca.limiar) {
    return { status: "inconclusivo", hipoteses: [] };
  }
  // O limiar vale para o top-1, não para cada hipótese individualmente.
  return { status: "aceito", hipoteses: ordenadas.slice(0, politicaConfianca.numeroHipoteses) };
}
