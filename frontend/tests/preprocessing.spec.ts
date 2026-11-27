import { expect, test, type Page } from "@playwright/test";
import { build } from "esbuild";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import path from "node:path";
import reference from "./fixtures/preprocessing/reference.json" with { type: "json" };

const fixtures = path.resolve("tests/fixtures/preprocessing");
const sha256 = (bytes: Uint8Array) => createHash("sha256").update(bytes).digest("hex");
const fixturesReferenceSha256 = () => sha256(readFileSync(path.join(fixtures, "reference.json")));
let harness: string;

test.beforeAll(async () => {
  const result = await build({ entryPoints: ["tests/preprocessing.worker.ts"], bundle: true, write: false, format: "iife", platform: "browser" });
  harness = result.outputFiles[0].text;
});

async function start(page: Page) {
  await page.route("**/__preprocessing_test_worker.js", (route) => route.fulfill({
    contentType: "text/javascript", body: harness,
    headers: { "Cross-Origin-Embedder-Policy": "require-corp", "Cross-Origin-Resource-Policy": "same-origin" },
  }));
  await page.goto("/");
  await page.evaluate(() => {
    (window as any).comparisonWorker = new Worker("/runtime/__preprocessing_test_worker.js");
    (window as any).comparisonWorker.onerror = (event: ErrorEvent) => { (window as any).comparisonWorkerError = event.message || "Falha ao carregar worker"; };
    (window as any).compare = (data: unknown) => new Promise((resolve, reject) => {
      const worker = (window as any).comparisonWorker as Worker;
      if ((window as any).comparisonWorkerError) { reject(new Error((window as any).comparisonWorkerError)); return; }
      worker.onmessage = ({ data }) => data.error ? reject(new Error(data.error)) : resolve(data);
      worker.onerror = (event) => reject(new Error(event.message));
      worker.postMessage(data);
    });
  });
}

async function photo(page: Page, filename: string, action = "photo") {
  const bytes = readFileSync(path.join(fixtures, filename)).toString("base64");
  return page.evaluate(async ({ bytes, filename, action }) => {
    const type = filename.endsWith(".jpg") ? "image/jpeg" : filename.endsWith(".webp") ? "image/webp" : "image/png";
    return (window as any).compare({ action, file: new File([Uint8Array.from(atob(bytes), (c) => c.charCodeAt(0))], filename, { type }) });
  }, { bytes, filename, action });
}

function differences(actual: Uint8Array, expected: Uint8Array) {
  expect(actual.length).toBe(expected.length);
  let max = 0, sum = 0, changed = 0;
  for (let i = 0; i < actual.length; i++) {
    const delta = Math.abs(actual[i] - expected[i]);
    max = Math.max(max, delta); sum += delta; changed += Number(delta !== 0);
  }
  return { max, mae: sum / actual.length, changed, total: actual.length };
}

test("compara decodificação, ICC, oito orientações EXIF e normalização em worker real", async ({ page }, testInfo) => {
  await start(page);
  const metrics = [];
  for (const item of reference.cases) {
    expect(sha256(readFileSync(path.join(fixtures, item.file)))).toBe(item.sha256);
    const result = await photo(page, item.file);
    expect([result.width, result.height]).toEqual([item.width, item.height]);
    const stages: Record<string, ReturnType<typeof differences>> = {};
    for (const stage of ["decoded", "pixels"] as const) {
      const expected = gunzipSync(readFileSync(path.join(fixtures, `${item.file}.${stage}.gz`)));
      const delta = differences(Buffer.from(result[stage], "base64"), expected);
      expect(delta.max, `${item.file} / ${stage}`).toBeLessThanOrEqual(item.tolerance.max);
      expect(delta.mae, `${item.file} / ${stage}`).toBeLessThanOrEqual(item.tolerance.mae);
      stages[stage] = delta;
    }
    const pixels = Buffer.from(result.pixels, "base64");
    const expectedFloat = Float32Array.from(pixels, (v) => v / 255);
    expect(Buffer.from(result.normalized, "base64")).toEqual(Buffer.from(expectedFloat.buffer));
    if (stages.pixels.changed === 0)
      expect(sha256(Buffer.from(result.normalized, "base64")), `${item.file}: float32 de referência Python`).toBe(item.normalizedSha256);
    metrics.push({ file: item.file, ...stages });
  }
  await expect(photo(page, "transparent.png")).rejects.toThrow(/transparência/);
  const policies = await page.evaluate(() => (window as any).compare({ action: "policy", scores: [0.6499999999999999, 0.65, 0.6500000000000001, 166 / 256, 167 / 256] }));
  expect(policies).toEqual(["inconclusivo", "aceito", "aceito", "inconclusivo", "aceito"]);
  const legacy = [];
  for (const file of ["display-p3.jpg", "photo-icc.png"]) {
    const result = await photo(page, file, "legacy");
    const expected = gunzipSync(readFileSync(path.join(fixtures, `${file}.pixels.gz`)));
    const delta = differences(Buffer.from(result.pixels, "base64"), expected);
    // Controle negativo: as mesmas fotos revelam a conversão ICC do pipeline antigo.
    expect(delta.max).toBeGreaterThan(3);
    legacy.push({ file, pixels: delta });
  }
  mkdirSync(".work", { recursive: true });
  writeFileSync(".work/preprocessing-metrics.json", JSON.stringify({ browser: page.context().browser()?.version(), contract: reference.contract, fixturesReferenceSha256: fixturesReferenceSha256(), cases: metrics, legacy }, null, 2));
  await testInfo.attach("preprocessing-metrics", { body: JSON.stringify(metrics, null, 2), contentType: "application/json" });
});

// A comparação com modelos é opt-in, após gerar .work/model-comparison-python.json.
test("compara tensores e inferências dos modelos finais Float16 e INT8", async ({ page }, testInfo) => {
  test.skip(process.env.MODEL_COMPARISON !== "1", "Executar com MODEL_COMPARISON=1 após a referência Python");
  test.setTimeout(300_000);
  const python = JSON.parse(readFileSync(".work/model-comparison-python.json", "utf8"));
  expect(python.contract).toBe(reference.contract);
  expect(python.fixturesReferenceSha256).toBe(fixturesReferenceSha256());
  expect(python.policySha256).toBe(sha256(readFileSync("../assets/data/politica_T6_5/parametros.json")));
  const codeSha256: Record<string, string> = {};
  for (const [name, expected] of Object.entries(python.codeSha256)) {
    codeSha256[name] = sha256(readFileSync(path.resolve("..", name)));
    expect(codeSha256[name], `${name}: referência Python desatualizada`).toBe(expected);
  }
  const models = [];
  for (const format of ["Float16", "INT8"]) {
    await start(page);
    const init = await page.evaluate((format) => (window as any).compare({ action: "init", base: new URL("/", location.href).href, format }), format);
    expect(init.spec.sha256).toBe(python.models[format].spec.sha256);
    expect(init.spec.sourceSha256).toBe(python.models[format].spec.sourceSha256);
    expect(init.contract).toBe(python.contract);
    const cases = [];
    for (const item of python.cases) {
      expect(sha256(readFileSync(path.join(fixtures, item.file)))).toBe(item.sha256);
      const result = await photo(page, item.file);
      expect([result.width, result.height]).toEqual([item.width, item.height]);
      if (sha256(Buffer.from(result.pixels, "base64")) === item.pixelsSha256)
        expect(sha256(Buffer.from(result.tensor, "base64")), `${format}/${item.file}: tensor de referência Python`).toBe(python.models[format].cases[item.file].tensorSha256);
      // O relatório posterior também executa Python sobre estes mesmos tensores.
      expect(result.scores).toHaveLength(13);
      expect(result.scores.every((score: number) => Number.isFinite(score) && score >= 0 && score <= 1)).toBe(true);
      const expected = python.models[format].cases[item.file];
      const maxError = Math.max(...result.scores.map((score: number, i: number) => Math.abs(score - expected.scores[i])));
      if (format === "Float16") expect(maxError, `${format}/${item.file}: 13 scores Python × web`).toBeLessThanOrEqual(1e-5);
      const defaultError = Math.max(...result.scores.map((score: number, i: number) => Math.abs(score - expected.defaultDelegateScores[i])));
      expect(defaultError, `${format}/${item.file}: Python XNNPACK × web`).toBeLessThanOrEqual(format === "INT8" ? 0 : 1e-5);
      expect(result.decision).toBe(expected.defaultDelegate.decision);
      expect(result.scores.indexOf(Math.max(...result.scores))).toBe(expected.defaultDelegate.class);
      // A decisão deve ser estável quando o erro medido não alcança o limiar.
      if (Math.abs(expected.margin) > maxError) expect(result.decision).toBe(expected.decision);
      const sorted = [...expected.scores].sort((a: number, b: number) => b - a);
      if (sorted[0] - sorted[1] > 2 * maxError)
        expect(result.scores.indexOf(Math.max(...result.scores))).toBe(expected.class);
      cases.push({ file: item.file, ...result, decoded: undefined, normalized: undefined,
        maxScoreDifference: maxError, maxScoreDifferenceDefaultDelegate: defaultError, exceedsHistoricalTolerance: maxError > 2 / 256 });
    }
    models.push({ format, ...init, cases });
    await page.evaluate(() => (window as any).comparisonWorker.terminate());
  }
  const output = { browser: page.context().browser()?.version(), platform: process.platform, contract: reference.contract,
    codeSha256, fixturesReferenceSha256: fixturesReferenceSha256(), models };
  writeFileSync(".work/model-comparison-web.json", JSON.stringify(output, null, 2));
  await testInfo.attach("model-comparison-web", { body: JSON.stringify(output), contentType: "application/json" });
});
