import { expect, test, devices } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { verificarHar } from "../scripts/verify-har.mjs";

const fixtures = fileURLToPath(new URL("./fixtures/", import.meta.url));
const { defaultBrowserType: _, ...pixel } = devices["Pixel 7"];
test.use(pixel);

// T12.3: depois do carregamento inicial, a classificação acontece no aparelho, sem rede e sem upload.
test("classifica na sessão carregada sem conexão e sem enviar a foto", async ({ browser }, testInfo) => {
  const har = testInfo.outputPath("sessao.har");
  const context = await browser.newContext({ ...pixel, recordHar: { path: har, content: "omit" } });
  const page = await context.newPage();
  const depoisDaCarga: string[] = [];
  const locais: string[] = [];
  let carregado = false;
  // No contexto: inclui as requisições do worker e do service worker.
  // blob: é a foto lida da memória do próprio navegador para a pré-visualização, sem rede.
  context.on("request", (request) => {
    if (!carregado) return;
    (request.url().startsWith("blob:") ? locais : depoisDaCarga).push(`${request.method()} ${request.url()}`);
  });

  await page.goto("/");
  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible();
  await expect(page.getByText(/disponível offline/)).toBeVisible();
  carregado = true;
  await context.setOffline(true);

  const region = page.getByRole("region", { name: "Resultado da análise" });
  const resultado = region
    .getByRole("heading", { name: "Identificação inconclusiva" })
    .or(region.getByRole("group", { name: "Hipóteses de identificação" }));
  for (const [botao, arquivo] of [
    ["Tirar foto", "orientation.jpg"],
    ["Trocar foto", "pattern.png"],
  ]) {
    const choosing = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: botao, exact: true }).click();
    await (await choosing).setFiles(path.join(fixtures, arquivo));
    await expect(page.getByAltText("Foto selecionada para análise")).toBeVisible();
    await expect(resultado).toBeVisible();
  }
  expect(depoisDaCarga).toEqual([]);
  expect(locais.every((r) => r.startsWith("GET blob:"))).toBe(true);
  await context.close();

  const resumo = verificarHar(JSON.parse(readFileSync(har, "utf8")), "carga");
  expect(resumo.problemas).toEqual([]);
  expect(resumo.requisicoes).toBeGreaterThan(0);
  await testInfo.attach("resumo-carga.json", { body: JSON.stringify(resumo, null, 2), contentType: "application/json" });
});
