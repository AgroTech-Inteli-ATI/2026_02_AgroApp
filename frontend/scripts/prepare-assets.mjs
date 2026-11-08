import { createHash } from "node:crypto";
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { build } from "esbuild";

const root = fileURLToPath(new URL("../../", import.meta.url));
const app = path.join(root, "frontend");
const destination = path.join(app, "public/models");
const sources = JSON.parse(
  await readFile(path.join(app, "model-sources.json"), "utf8"),
);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");

async function checkedSource(source) {
  const contract = JSON.parse(await readFile(path.join(root, source.contractPath), "utf8"));
  const bytes = await readFile(path.join(root, source.sourcePath));
  const sha256 = digest(bytes);
  const expected = source.sha256Key.reduce((value, key) => value?.[key], contract);
  if (sha256 !== expected) throw new Error(`Hash divergente: ${source.sourcePath}`);
  return { bytes, sha256, contract };
}

const classSource = await checkedSource(sources.classes);
const classes = JSON.parse(classSource.bytes.toString("utf8"));
if (classes.length !== 13 || classes.some((item, i) => item.indice !== i))
  throw new Error("Ordem de classes inválida.");
if (sources.models.map((model) => model.format).join() !== "Float16,INT8")
  throw new Error("Esperados Float16 principal e INT8 de contingência, nessa ordem.");

// Lê do esquema oficial do TFLite os tensores de entrada e saída do modelo.
// Assim, o contrato e os parâmetros de quantização vêm do próprio arquivo.
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
    // O LiteRT.js 2.6 exige dimensões concretas. O exportador Python mantém
    // shape_signature[0] = -1 mesmo com shape[0] = 1. Ajustamos só os metadados:
    // operadores, dados, pesos, quantização e arquivos originais não são alterados.
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

// Estas pastas contêm somente saídas geradas. Não carregar modelos ou runtimes
// de uma preparação anterior para o próximo build.
await rm(destination, { recursive: true, force: true });
await rm(path.join(app, "public/runtime"), { recursive: true, force: true });
await mkdir(destination, { recursive: true });
// Retira apenas as antigas cópias FP32 geradas por este empacotador.
for (const filename of ["modelo_fp32.tflite", "modelo_fp32_web.tflite"])
  await rm(path.join(destination, filename), { force: true });
const models = [];
for (const source of sources.models) {
  const { format, version, sourcePath, contractPath } = source;
  const { bytes, sha256: sourceSha256, contract: provenance } = await checkedSource(source);
  const classesSha256 = provenance.origem_selecao?.classes_sha256 ?? provenance.sha256?.["classes.json"];
  if (classesSha256 !== classSource.sha256 ||
      (provenance.classes && JSON.stringify(provenance.classes) !== JSON.stringify(classes)))
    throw new Error(`Classes incompatíveis: ${contractPath}`);
  const contract = tensorContract(bytes, true);
  const sha256 = digest(bytes);
  if (
    contract.input.shape.join() !== "1,224,224,3" ||
    contract.output.shape.join() !== "1,13"
  ) {
    throw new Error("Dimensões diferentes do contrato do candidato.");
  }
  const expectedDtype = format === "INT8" ? "int8" : "float32";
  if (contract.input.dtype !== expectedDtype || contract.output.dtype !== expectedDtype)
    throw new Error(`Tipo de tensor incompatível: ${sourcePath}`);
  const filename = `modelo_${format.toLowerCase()}.tflite`;
  const webFilename = filename.replace(".tflite", "_web.tflite");
  await writeFile(path.join(destination, webFilename), bytes);
  // Remove cópias geradas antigas deste script, se existirem.
  await rm(path.join(destination, filename), { force: true });
  models.push({
    format,
    filename: webFilename,
    bytes: bytes.length,
    sha256,
    sourceSha256,
    sourcePath,
    contractPath,
    version,
    ...contract,
  });
}
await writeFile(
  path.join(destination, "manifest.json"),
  JSON.stringify(
    {
      id: sources.id,
      architecture: classSource.contract.arquitetura,
      selectionStatus: sources.selectionStatus,
      classes,
      classesSource: {
        sourcePath: sources.classes.sourcePath,
        contractPath: sources.classes.contractPath,
        sha256: classSource.sha256,
      },
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
// O carregador Emscripten do LiteRT usa importScripts(), que exige um worker clássico.
// Geramos o pacote separado para servir o mesmo arquivo no Vite e na produção.
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
  `Recursos preparados: ${classes.length} classes, Float16 T7.2 e INT8 T7.3 com hashes verificados, LiteRT.js local.`,
);
