import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { cp, mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const app = fileURLToPath(new URL("../", import.meta.url));
const root = path.dirname(app);
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const json = async (file) => JSON.parse(await readFile(file, "utf8"));
const run = (command, args, cwd = app) =>
  execFileSync(command, args, { cwd, encoding: "utf8" });

async function inventory(directory, relative = "") {
  const files = {};
  for (const entry of (await readdir(path.join(directory, relative), { withFileTypes: true }))
    .sort((a, b) => a.name.localeCompare(b.name))) {
    const name = relative ? `${relative}/${entry.name}` : entry.name;
    if (entry.isDirectory()) Object.assign(files, await inventory(directory, name));
    else if (entry.isFile() && name !== "release.json") {
      const bytes = await readFile(path.join(directory, name));
      files[name] = { bytes: bytes.length, sha256: hash(bytes) };
    } else if (!entry.isFile()) throw new Error(`Tipo de arquivo não permitido: ${name}`);
  }
  return files;
}

async function verify(directory) {
  const release = await json(path.join(directory, "release.json"));
  const actual = await inventory(directory);
  if (JSON.stringify(actual) !== JSON.stringify(release.files))
    throw new Error("Pacote alterado: arquivos ausentes, adicionais ou com hash divergente.");
  const models = await json(path.join(directory, "models/manifest.json"));
  if (models.models.map((model) => `${model.format}:${model.version}`).join() !== "Float16:T7.2,INT8:T7.3")
    throw new Error("Seleção de modelos inesperada.");
  for (const model of models.models) {
    if (actual[`models/${model.filename}`]?.sha256 !== model.sha256)
      throw new Error(`Modelo divergente do manifesto: ${model.filename}`);
  }
  console.log(`Pacote verificado: ${release.id}, ${Object.keys(actual).length} arquivos.`);
}

if (process.argv[2] === "--verify") {
  if (!process.argv[3]) throw new Error("Informe a pasta site do pacote congelado.");
  await verify(path.resolve(process.argv[3]));
} else {
  // npm executa prebuild: modelos, contratos, classes e worker são regenerados.
  if (!process.env.npm_execpath) throw new Error("Execute com npm run demo:package.");
  execFileSync(process.execPath, [process.env.npm_execpath, "run", "build"], { cwd: app, stdio: "inherit" });
  const createdAt = new Date().toISOString();
  const commit = run("git", ["rev-parse", "HEAD"], root).trim();
  const id = `agroapp-demo-${createdAt.replace(/[:.]/g, "-")}-${commit.slice(0, 8)}`;
  const output = path.join(app, ".work/demo", id);
  const site = path.join(output, "site");
  await mkdir(output, { recursive: true });
  await cp(path.join(app, "dist"), site, { recursive: true });
  const sourcePaths = [
    "frontend/package-lock.json", "frontend/model-sources.json",
    "frontend/src/lib/preprocess.ts", "frontend/src/lib/confidence.ts",
    "frontend/src/lib/inference.worker.ts", "frontend/src/data/content.ts",
    "assets/data/politica_T6_5/parametros.json",
  ];
  const sources = {};
  for (const filename of sourcePaths) sources[filename] = hash(await readFile(path.join(root, filename)));
  const release = {
    id, createdAt, commit,
    workingTreeStatus: run("git", ["status", "--porcelain", "--untracked-files=normal"], root),
    node: process.version,
    dependencies: (await json(path.join(app, "package-lock.json"))).packages[""],
    sources,
    modelManifest: await json(path.join(site, "models/manifest.json")),
    confidencePolicy: await json(path.join(root, "assets/data/politica_T6_5/parametros.json")),
    limitations: [
      "Protótipo experimental de 13 classes; score não é probabilidade calibrada de acerto.",
      "T10.2: preprocessing validado no corpus fotográfico; scores INT8 dependem da configuração do delegate (ver relatório comparativo).",
      "Avaliação histórica exploratória; independência dos dados comprometida.",
      "Conteúdo técnico e validação em aparelho físico permanecem pendentes.",
    ],
    files: await inventory(site),
  };
  await writeFile(path.join(site, "release.json"), JSON.stringify(release, null, 2) + "\n");
  await verify(site);
  await writeFile(path.join(output, "LEIA-ME.txt"), [
    `Versão congelada: ${id}`,
    "Sirva/publice a pasta site inteira em HTTPS. Não misture arquivos de outro build.",
    "Para ensaio no próprio computador: python3 -m http.server 4173 --bind 127.0.0.1 --directory site",
    "Abra http://127.0.0.1:4173. Para celular, use hospedagem HTTPS; localhost é do próprio aparelho.",
    "release.json identifica código, modelos, política e hashes. Consulte também suas limitações.",
    "Verifique: npm run demo:verify -- <caminho-da-pasta-site> (a partir de frontend).",
    "Este pacote não certifica câmera física, latência móvel, offline ou generalização.",
    "",
  ].join("\n"));
  const archive = `${output}.tar.gz`;
  run("tar", ["-czf", archive, "-C", path.dirname(output), id]);
  await writeFile(`${archive}.sha256`, `${hash(await readFile(archive))}  ${path.basename(archive)}\n`);
  console.log(`Demo congelada: ${output}\nArquivo: ${archive}\nSHA-256: ${archive}.sha256`);
}
