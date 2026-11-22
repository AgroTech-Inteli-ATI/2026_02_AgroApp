import { describe, expect, it } from "vitest";
import { percentile, summarize } from "./benchmark";

describe("estatísticas do benchmark", () => {
  it("calcula p50/p95 por interpolação sem modificar as amostras", () => {
    const values = [40, 10, 30, 20];
    expect(percentile(values, .5)).toBe(25);
    expect(percentile(values, .95)).toBeCloseTo(38.5);
    expect(values).toEqual([40, 10, 30, 20]);
    expect(percentile([17], .95)).toBe(17);
    expect(percentile([0, 10], 0)).toBe(0);
    expect(percentile([0, 10], 1)).toBe(10);
  });
  it("rejeita durações e percentis inválidos", () => {
    for (const values of [[], [NaN], [Infinity], [-1]])
      expect(() => percentile(values, .95)).toThrow();
    for (const p of [-.1, 1.1, NaN]) expect(() => percentile([1], p)).toThrow();
  });
  it("separa preparação, inferência e fluxo; não inventa estatística sem amostras", () => {
    expect(summarize([])).toBeNull();
    const samples = Array.from({ length: 50 }, (_, i) => ({
      preparationMs: i + 1, inferenceMs: (i + 1) * 2, fileToPaintMs: (i + 1) * 3,
    }));
    expect(summarize(samples)).toEqual({
      preparationMs: { n: 50, p50: 25.5, p95: 47.55 },
      inferenceMs: { n: 50, p50: 51, p95: 95.1 },
      fileToPaintMs: { n: 50, p50: 76.5, p95: 142.64999999999998 },
    });
  });
});
