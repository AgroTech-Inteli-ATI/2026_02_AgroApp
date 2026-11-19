import type { ModelInfo } from "../types";

export interface BenchmarkSample {
  preparationMs: number;
  inferenceMs: number;
  fileToPaintMs: number;
}
export interface InitializationMeasurement {
  workerToReadyMs: number;
  navigationToReadyMs: number;
  model: ModelInfo;
}

// Interpolação linear: posição (n - 1) * p, compatível com numpy.quantile padrão.
export function percentile(values: number[], p: number): number {
  if (!values.length || values.some((n) => !Number.isFinite(n) || n < 0)
      || !Number.isFinite(p) || p < 0 || p > 1)
    throw new Error("Amostras ou percentil inválidos.");
  const sorted = [...values].sort((a, b) => a - b);
  const position = (sorted.length - 1) * p;
  const lower = Math.floor(position);
  return sorted[lower] + (sorted[Math.ceil(position)] - sorted[lower]) * (position - lower);
}
export function summarize(samples: BenchmarkSample[]) {
  if (!samples.length) return null;
  return Object.fromEntries(
    (["preparationMs", "inferenceMs", "fileToPaintMs"] as const).map((key) => {
      const values = samples.map((sample) => sample[key]);
      return [key, { n: values.length, p50: percentile(values, 0.5), p95: percentile(values, 0.95) }];
    }),
  );
}
export async function sha256(bytes: ArrayBuffer): Promise<string> {
  return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
    .map((n) => n.toString(16).padStart(2, "0")).join("");
}
