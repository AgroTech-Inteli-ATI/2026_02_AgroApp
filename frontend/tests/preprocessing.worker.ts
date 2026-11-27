// Harness de teste: usa as mesmas funções e o mesmo runtime do worker publicado.
import { loadLiteRt, loadAndCompile, Tensor, type CompiledModel } from "@litertjs/core";
import { decodeImage, prepareImage, letterbox, normalize, quantize, PREPROCESS_CONTRACT } from "../src/lib/preprocess";
import { avaliarConfianca } from "../src/lib/confidence";
import type { ModelManifest, ModelSpec } from "../src/types";

let model: CompiledModel | undefined;
let spec: ModelSpec;
let manifest: ModelManifest;
const base64 = (bytes: Uint8Array) => {
  let value = "";
  for (let i = 0; i < bytes.length; i += 8192)
    value += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return btoa(value);
};
const digest = async (bytes: Uint8Array) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
  .map((v) => v.toString(16).padStart(2, "0")).join("");

self.onmessage = async ({ data }) => {
  try {
    if (data.action === "init") {
      manifest = await (await fetch(`${data.base}models/manifest.json`)).json();
      spec = manifest.models.find((m) => m.format === data.format)!;
      const bytes = new Uint8Array(await (await fetch(`${data.base}models/${spec.filename}`)).arrayBuffer());
      if (await digest(bytes) !== spec.sha256) throw new Error("Hash do modelo divergente");
      await loadLiteRt(`${data.base}runtime/`);
      model = await loadAndCompile(bytes, { accelerator: "wasm", cpuOptions: { numThreads: 1 } });
      self.postMessage({ spec, contract: PREPROCESS_CONTRACT, runtime: "LiteRT.js 2.6.0 CPU/WASM, 1 thread" });
      return;
    }
    if (data.action === "policy") {
      self.postMessage(data.scores.map((score: number) => avaliarConfianca([
        { indice: 0, nome: "teste", score }, { indice: 1, nome: "outro", score: 1 - score },
      ]).status));
      return;
    }
    const file = data.file as File;
    if (data.action === "legacy") {
      const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
      try {
        const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
        const context = canvas.getContext("2d", { colorSpace: "srgb" })!;
        context.drawImage(bitmap, 0, 0);
        const rgba = context.getImageData(0, 0, bitmap.width, bitmap.height).data;
        const rgb = new Uint8Array(bitmap.width * bitmap.height * 3);
        for (let i = 0, j = 0; i < rgba.length; i += 4, j += 3) rgb.set(rgba.subarray(i, i + 3), j);
        self.postMessage({ pixels: base64(letterbox(rgb, bitmap.width, bitmap.height)) });
      } finally { bitmap.close(); }
      return;
    }
    const { rgb, width, height } = await decodeImage(file);
    const { pixels } = await prepareImage(file);
    const normalized = normalize(pixels);
    let scores: number[] | undefined;
    let tensor: Uint8Array | undefined;
    if (model) {
      const values = spec.input.dtype === "int8" ? quantize(pixels, spec.input.scale!, spec.input.zeroPoint!) : normalized;
      tensor = new Uint8Array(values.buffer, values.byteOffset, values.byteLength);
      const input = new Tensor(values, [1, 224, 224, 3]);
      let outputs: Tensor[] = [];
      try {
        outputs = await model.run(input);
        scores = Array.from(await outputs[0].data(), Number).map((v) =>
          spec.output.dtype === "int8" ? (v - spec.output.zeroPoint!) * spec.output.scale! : v);
      } finally {
        input.delete();
        outputs.forEach((output) => output.delete());
      }
    }
    self.postMessage({
      width, height, decoded: base64(rgb), pixels: base64(pixels),
      normalized: base64(new Uint8Array(normalized.buffer)), tensor: tensor && base64(tensor), scores,
      decision: scores && avaliarConfianca(scores.map((score, indice) => ({ ...manifest.classes[indice], score }))).status,
    });
  } catch (error) {
    self.postMessage({ error: error instanceof Error ? error.message : String(error) });
  }
};
