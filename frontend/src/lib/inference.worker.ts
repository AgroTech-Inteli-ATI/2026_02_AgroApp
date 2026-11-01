/// <reference lib="webworker" />
import {
  loadLiteRt,
  loadAndCompile,
  Tensor,
  type CompiledModel,
} from "@litertjs/core";
import { prepareImage, quantize } from "./preprocess";
import type {
  ModelInfo,
  ModelManifest,
  ModelSpec,
  WorkerRequest,
  WorkerResponse,
} from "../types";

const scope = self as unknown as DedicatedWorkerGlobalScope;
const send = (message: WorkerResponse) => scope.postMessage(message);
let compiled: CompiledModel | undefined;
let spec: ModelSpec;
let manifest: ModelManifest;
let initialization: Promise<void> | undefined;
let busy = false;

async function checkedBytes(url: string, hash: string) {
  const response = await fetch(url);
  if (!response.ok)
    throw new Error(`Não foi possível baixar o modelo (${response.status}).`);
  const bytes = await response.arrayBuffer();
  const digest = [
    ...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
  ]
    .map((n) => n.toString(16).padStart(2, "0"))
    .join("");
  if (digest !== hash)
    throw new Error(
      "O arquivo do modelo está incompleto ou foi alterado. Recarregue a página.",
    );
  return new Uint8Array(bytes);
}

async function init(base: string) {
  // O worker baixa o manifesto e o modelo; a inferência acontece no navegador.
  send({ type: "status", message: "Carregando o modelo…" });
  const response = await fetch(`${base}models/manifest.json`);
  if (!response.ok)
    throw new Error(
      "O modelo não está disponível no site. Recarregue a página ou avise a equipe responsável.",
    );
  manifest = (await response.json()) as ModelManifest;
  if (
    manifest.classes.length !== 13 ||
    manifest.classes.some((c, i) => c.indice !== i)
  )
    throw new Error("Catálogo de classes incompatível com o modelo.");
  await loadLiteRt(`${base}runtime/`);
  let lastError: unknown;
  for (const candidate of manifest.models) {
    const bytes = await checkedBytes(
      `${base}models/${candidate.filename}`,
      candidate.sha256,
    );
    // O modelo INT8 roda na CPU; para FP32, tentamos WebGPU e depois CPU.
    const accelerators: ("wasm" | "webgpu")[] =
      candidate.format === "FP32" && "gpu" in navigator
        ? ["webgpu", "wasm"]
        : ["wasm"];
    for (const accelerator of accelerators) {
      try {
        send({ type: "status", message: `Preparando ${candidate.format}…` });
        const model = await loadAndCompile(bytes, {
          accelerator,
          cpuOptions: { numThreads: 1 },
        });
        try {
          const input = model.getInputDetails()[0],
            output = model.getOutputDetails()[0];
          // Confere se as dimensões e os tipos do arquivo correspondem ao manifesto.
          const shapeMatches = (actual: Int32Array, expected: number[]) =>
            actual.length === expected.length &&
            expected.every((size, i) => actual[i] === size);
          if (
            !shapeMatches(input.shape, candidate.input.shape) ||
            !shapeMatches(output.shape, candidate.output.shape) ||
            input.dtype !== candidate.input.dtype ||
            output.dtype !== candidate.output.dtype
          )
            throw new Error("Entrada ou saída incompatível.");
          // Uma execução de aquecimento confirma que o modelo também consegue inferir.
          const warmup = new Tensor(
            candidate.input.dtype === "int8"
              ? quantize(
                  new Uint8Array(224 * 224 * 3).fill(128),
                  candidate.input.scale!,
                  candidate.input.zeroPoint!,
                )
              : new Float32Array(224 * 224 * 3).fill(128 / 255),
            [1, 224, 224, 3],
          );
          let outputs: Tensor[] = [];
          try {
            outputs = await model.run(warmup);
            const values = await outputs[0].data();
            if (
              values.length !== 13 ||
              !Array.from(values, Number).every(Number.isFinite)
            )
              throw new Error("O modelo não retornou 13 scores válidos.");
          } finally {
            warmup.delete();
            outputs.forEach((tensor) => tensor.delete());
          }
        } catch (error) {
          model.delete();
          throw error;
        }
        compiled = model;
        spec = candidate;
        const info: ModelInfo = {
          id: manifest.id,
          format: candidate.format,
          bytes: candidate.bytes,
          accelerator:
            accelerator === "webgpu" && model.isFullyAccelerated
              ? "WebGPU"
              : "CPU / WebAssembly",
          fallback: candidate.format !== "INT8",
        };
        send({ type: "ready", info });
        return;
      } catch (error) {
        lastError = error;
      }
    }
  }
  console.error("Falha de compatibilidade LiteRT:", lastError);
  throw new Error(
    "Não foi possível executar o modelo neste navegador. Tente Chrome ou Edge atualizado e recarregue a página.",
  );
}

async function analyze(id: number, file: File) {
  if (busy) {
    send({ type: "error", id, message: "Aguarde a análise atual terminar." });
    return;
  }
  busy = true;
  try {
    await initialization;
    if (!compiled)
      throw new Error("O modelo ainda não está pronto. Recarregue a página.");
    const start = performance.now();
    // A imagem é preparada e redimensionada antes de ser enviada ao modelo.
    const { pixels, width, height, preview } = await prepareImage(file);
    const data =
      spec.input.dtype === "int8"
        ? quantize(pixels, spec.input.scale!, spec.input.zeroPoint!)
        : Float32Array.from(pixels, (value) => value / 255);
    const input = new Tensor(data, [1, 224, 224, 3]);
    const preparationMs = performance.now() - start;
    let outputs: Tensor[] = [];
    try {
      const inferenceStart = performance.now();
      outputs = await compiled.run(input);
      const raw = await outputs[0].data();
      const numeric = Array.from(raw as ArrayLike<number | bigint>, Number);
      const scores = numeric.map((value) =>
        spec.output.dtype === "int8"
          ? (value - spec.output.zeroPoint!) * spec.output.scale!
          : value,
      );
      if (
        scores.length !== 13 ||
        scores.some((n) => !Number.isFinite(n) || n < 0 || n > 1)
      )
        throw new Error(
          "O modelo retornou scores inválidos. Tente outra foto.",
        );
      // Cada score é associado à classe pelo índice definido no manifesto.
      const predictions = manifest.classes
        .map((label, i) => ({ ...label, score: scores[i] }))
        .sort((a, b) => b.score - a.score || a.indice - b.indice);
      // Envia previsões e tempos à interface React, sem enviar a foto a um servidor.
      send({
        type: "result",
        id,
        result: {
          predictions,
          width,
          height,
          preview,
          preparationMs,
          inferenceMs: performance.now() - inferenceStart,
        },
      });
    } finally {
      input.delete();
      outputs.forEach((tensor) => tensor.delete());
    }
  } catch (error) {
    send({
      type: "error",
      id,
      message:
        error instanceof Error
          ? error.message
          : "Não foi possível analisar a foto. Tente novamente.",
    });
  } finally {
    busy = false;
  }
}

scope.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const message = event.data;
  if (message.type === "init") {
    initialization ??= init(message.base);
    void initialization.catch((error) => {
      console.error("Falha ao carregar o modelo:", error);
      send({
        type: "error",
        message:
          error instanceof TypeError
            ? "Não foi possível baixar os arquivos da análise. Verifique sua conexão e tente novamente."
            : error instanceof Error
              ? error.message
              : "Falha ao carregar o modelo. Recarregue a página.",
      });
    });
  } else {
    void analyze(message.id, message.file);
  }
};
