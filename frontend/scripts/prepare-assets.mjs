import { createHash } from "node:crypto";
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { build } from "esbuild";

const root = fileURLToPath(new URL("../../", import.meta.url));
const app = path.join(root, "frontend");
const source = path.join(root, "assets/modelos/candidato_T5_6_20261026");
const destination = path.join(app, "public/models");
const manifest = JSON.parse(
  await readFile(path.join(source, "manifesto.json"), "utf8"),
);

// Read the small part of the official TFLite FlatBuffer schema that describes
// the graph's boundary tensors. Never duplicate quantization constants by hand.
function tensorContract(buffer, specialize = false) {
  if (buffer.toString("ascii", 4, 8) !== "TFL3")
    throw new Error("Arquivo TFLite inválido.");
  const field = (table, index) => {
    const vtable = table - buffer.readInt32LE(table);
    return 4 + index * 2 < buffer.readUInt16LE(vtable)
      ? buffer.readUInt16LE(vtable + 4 + index * 2)
      : 0;
  };
  const pointer = (position) => position + buffer.readUInt32LE(position);
  const vector = (table, index, bytes, read) => {
    const offset = field(table, index);
    if (!offset) return [];
    const start = pointer(table + offset);
    return Array.from({ length: buffer.readUInt32LE(start) }, (_, i) =>
      read(start + 4 + bytes * i),
    );
  };
  const ints = (table, index) =>
    vector(table, index, 4, (p) => buffer.readInt32LE(p));
  const tables = (table, index) => vector(table, index, 4, pointer);
  const graph = tables(buffer.readUInt32LE(0), 2)[0];
  const tensors = tables(graph, 0);
  if (specialize) {
    // LiteRT.js 2.6 requires matching concrete types. The Python exporter keeps
    // shape_signature[0] = -1 despite shape[0] = 1. Specialize metadata only:
    // no operator, tensor data, weight, quantization or original file is changed.
    for (const table of tensors) {
      const shape = ints(table, 0);
      vector(table, 7, 4, (position) => position).forEach((position, i) => {
        if (buffer.readInt32LE(position) === -1) {
          if (!(shape[i] > 0))
            throw new Error("Dimensão dinâmica sem forma concreta.");
          buffer.writeInt32LE(shape[i], position);
        }
      });
    }
  }
  const readTensor = (index) => {
    const table = tensors[index];
    const typeField = field(table, 1);
    const type = typeField ? buffer.readUInt8(table + typeField) : 0;
    const dtype = { 0: "float32", 9: "int8" }[type];
    if (!dtype) throw new Error(`Tipo de tensor não suportado: ${type}`);
    const quantField = field(table, 4);
    const quant = quantField ? pointer(table + quantField) : 0;
    const scale = quant
      ? vector(quant, 2, 4, (p) => buffer.readFloatLE(p))[0]
      : undefined;
    const zeroPoint = quant
      ? vector(quant, 3, 8, (p) => Number(buffer.readBigInt64LE(p)))[0]
      : undefined;
    return {
      shape: ints(table, 0),
      dtype,
      ...(scale ? { scale, zeroPoint } : {}),
    };
  };
  const inputs = ints(graph, 1),
    outputs = ints(graph, 2);
  if (inputs.length !== 1 || outputs.length !== 1)
    throw new Error("Esperada uma entrada e uma saída.");
  return { input: readTensor(inputs[0]), output: readTensor(outputs[0]) };
}

await mkdir(destination, { recursive: true });
const models = [];
for (const [format, filename] of [
  ["INT8", "modelo_int8.tflite"],
  ["FP32", "modelo_fp32.tflite"],
]) {
  const bytes = await readFile(path.join(source, filename));
  const sourceSha256 = createHash("sha256").update(bytes).digest("hex");
  if (sourceSha256 !== manifest.sha256[filename])
    throw new Error(`Hash divergente: ${filename}`);
  const contract = tensorContract(bytes, true);
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  if (
    contract.input.shape.join() !== "1,224,224,3" ||
    contract.output.shape.join() !== "1,13"
  ) {
    throw new Error("Dimensões diferentes do contrato do candidato.");
  }
  const webFilename = filename.replace(".tflite", "_web.tflite");
  await writeFile(path.join(destination, webFilename), bytes);
  // Remove only this script's obsolete generated copies from earlier builds.
  await rm(path.join(destination, filename), { force: true });
  models.push({
    format,
    filename: webFilename,
    bytes: bytes.length,
    sha256,
    sourceSha256,
    ...contract,
  });
}
const classesBytes = await readFile(path.join(source, "classes.json"));
if (
  createHash("sha256").update(classesBytes).digest("hex") !==
  manifest.sha256["classes.json"]
) {
  throw new Error("Hash divergente: classes.json");
}
const classes = JSON.parse(classesBytes.toString("utf8"));
if (classes.length !== 13 || classes.some((item, i) => item.indice !== i))
  throw new Error("Ordem de classes inválida.");
await writeFile(
  path.join(destination, "manifest.json"),
  JSON.stringify(
    {
      id: "candidato_T5_6_20261026",
      architecture: manifest.arquitetura,
      classes,
      models,
    },
    null,
    2,
  ) + "\n",
);
await cp(
  path.join(app, "node_modules/@litertjs/core/wasm"),
  path.join(app, "public/runtime"),
  { recursive: true },
);
// LiteRT's Emscripten loader uses importScripts(), which needs a classic worker.
// Bundle separately so both Vite dev and production serve the same classic IIFE.
await build({
  entryPoints: [path.join(app, "src/lib/inference.worker.ts")],
  outfile: path.join(app, "public/runtime/inference.js"),
  bundle: true,
  format: "iife",
  platform: "browser",
  target: "es2022",
  minify: true,
});
console.log(
  `Recursos preparados: ${classes.length} classes, INT8 e FP32 com hashes verificados, LiteRT.js local.`,
);
