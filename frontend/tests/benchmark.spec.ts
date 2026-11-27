import { expect, test } from "@playwright/test";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const photo = fileURLToPath(new URL("./fixtures/pattern.png", import.meta.url));

test("coleta 50 análises reais, exclui aquecimentos e exporta identidade e medições", async ({ page }) => {
  await page.goto("/?benchmark=1");
  const panel = page.getByRole("region", { name: "Benchmark no dispositivo" });
  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible();
  await panel.getByLabel("Aparelho", { exact: true }).fill("Chromium automatizado no Mac; não iPhone");
  await panel.getByLabel("Condições", { exact: false }).fill("Automação desktop; validação funcional, não evidência do iPhone.");
  await panel.getByLabel("Imagens para benchmark").setInputFiles(photo);
  await panel.getByRole("button", { name: "Iniciar 50 medições" }).click();
  await expect(panel.getByText("50 medições concluídas. Exporte o JSON.")).toBeVisible();
  const downloading = page.waitForEvent("download");
  await panel.getByRole("button", { name: "Exportar JSON do benchmark" }).click();
  const download = await downloading;
  const output = path.join(test.info().outputDir, "benchmark-desktop-test.json");
  await download.saveAs(output);
  const report = JSON.parse(await readFile(output, "utf8"));
  expect(report.complete).toBe(true);
  expect(report.samples).toHaveLength(53);
  expect(report.samples.filter((sample: { phase: string }) => sample.phase === "warmup")).toHaveLength(3);
  expect(report.summary.inferenceMs.n).toBe(50);
  expect(report.summary.fileToPaintMs.p95).toBeGreaterThan(0);
  expect(report.initialization.model.runtime.version).toBe("2.6.0");
  expect(report.initialization.model.sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(report.images[0].sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(report.initialization.workerToReadyMs).toBeGreaterThan(0);
  expect(report.failure).toBeNull();
});

test("interrompe coleta ao ocultar a página sem completar estatísticas", async ({ page }) => {
  await page.goto("/?benchmark=1");
  const panel = page.getByRole("region", { name: "Benchmark no dispositivo" });
  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible();
  await panel.getByLabel("Condições", { exact: false }).fill("Teste de interrupção.");
  await panel.getByLabel("Imagens para benchmark").setInputFiles(photo);
  await panel.getByRole("button", { name: "Iniciar 50 medições" }).click();
  await expect(panel.getByRole("button", { name: "Interromper coleta" })).toBeVisible();
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", { configurable: true, get: () => "hidden" });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(panel.getByText(/Coleta parcial:/)).toBeVisible();
  const downloading = page.waitForEvent("download");
  await panel.getByRole("button", { name: "Exportar JSON do benchmark" }).click();
  const download = await downloading;
  const report = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(report.complete).toBe(false);
  expect(report.samples.length).toBeLessThan(53);
  expect(report.failure).toContain("interrompida");
});
