import { describe, expect, it } from "vitest";
import { avaliarConfianca, politicaConfianca } from "./confidence";
import type { Prediction } from "../types";

const previsoes = (scores: number[]): Prediction[] => scores.map((score, indice) => ({
  indice, nome: `Classe ${indice}`, score,
}));

describe("tratamento do limiar de confiança", () => {
  it("recusa o maior score abaixo do limiar sem devolver classes", () => {
    const p = previsoes([.10, politicaConfianca.limiar - .000001, .25]);
    expect(avaliarConfianca(p)).toEqual({ status: "inconclusivo", hipoteses: [] });
  });

  it("aceita a igualdade exata e preserva hipóteses secundárias abaixo do limiar", () => {
    const p = previsoes([.20, politicaConfianca.limiar, .10, .05]);
    const resultado = avaliarConfianca(p);
    expect(resultado.status).toBe("aceito");
    expect(resultado.hipoteses.map((r) => r.indice)).toEqual([1, 0, 2]);
  });

  it("aceita score acima do limiar e limita a lista ao k da política", () => {
    const resultado = avaliarConfianca(previsoes([.01, .02, .9, .03, .04]));
    expect(resultado.status).toBe("aceito");
    expect(resultado.hipoteses).toHaveLength(politicaConfianca.numeroHipoteses);
    expect(resultado.hipoteses.map((r) => r.indice)).toEqual([2, 4, 3]);
  });

  it("desempata pelo índice e não muda o vetor original", () => {
    const p = previsoes([.8, .1, .1]);
    p.reverse();
    const antes = p.map((r) => ({ ...r }));
    expect(avaliarConfianca(p).hipoteses.map((r) => r.indice)).toEqual([0, 1, 2]);
    expect(p).toEqual(antes);
  });

  it("não exige soma exata de scores desquantizados INT8", () => {
    const p = previsoes([.69921875, .19921875, .09765625]);
    expect(avaliarConfianca(p).status).toBe("aceito");
  });

  it.each([NaN, Infinity, -.01, 1.01])("recusa saída contendo score inválido %s", (valor) => {
    expect(avaliarConfianca(previsoes([.9, valor]))).toEqual({ status: "inconclusivo", hipoteses: [] });
  });

  it("não escolhe classe de vetor vazio ou com índices repetidos", () => {
    expect(avaliarConfianca([]).status).toBe("inconclusivo");
    const p = previsoes([.9, .1]);
    p[1].indice = 0;
    expect(avaliarConfianca(p).hipoteses).toEqual([]);
  });
});
