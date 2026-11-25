import { expect, test, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import type { ModelManifest } from "../src/types";
import politica from "../../assets/data/politica_T6_5/parametros.json" with { type: "json" };

// T11.3: mede a política de confiança no aplicativo real, com o modelo do build, para imagens fora do recorte e
// inadequadas. Opt-in: precisa das imagens geradas por `python -m src.limiar_t11_3 preparar` (pasta em T11_3_IMAGENS).
// Grava assets/data/limiar_T11_3/inferencias_web.json com os 13 scores e a decisão mostrada na tela, por imagem.
const manifestoCaminho = path.resolve("../assets/data/limiar_T11_3/manifesto.json");
const saidaCaminho = path.resolve("../assets/data/limiar_T11_3/inferencias_web.json");
const sha256 = (dados: Buffer) => createHash("sha256").update(dados).digest("hex");

interface Item { id: string; cenario: string; arquivo: string }

async function medir(page: Page, formato: "Float16" | "INT8", itens: Item[], pasta: string) {
  if (formato === "INT8") {
    // Como em analysis.spec.ts: o contrato do Float16 é recusado e o app carrega a contingência oficial.
    await page.route("**/models/manifest.json", async (route) => {
      const response = await route.fetch();
      const manifest = (await response.json()) as ModelManifest;
      manifest.models[0].input.shape = [1, 225, 224, 3];
      await route.fulfill({ response, json: manifest });
    });
  }
  await page.addInitScript(() => {
    const NativeWorker = window.Worker;
    const w = window as unknown as { saidasWorker: { type: string; info?: unknown; result?: unknown }[] };
    w.saidasWorker = [];
    window.Worker = class extends NativeWorker {
      constructor(url: string | URL, options?: WorkerOptions) {
        super(url, options);
        this.addEventListener("message", (event) => {
          if (event.data.type === "result") w.saidasWorker.push({ type: "result", result: event.data.result });
          if (event.data.type === "ready") w.saidasWorker.push({ type: "ready", info: event.data.info });
        });
      }
    };
  });
  await page.goto("/");
  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible({ timeout: 120_000 });
  await expect(page.locator("span[class*='modelFormat']")).toHaveText(formato);
  const info = await page.evaluate(() => (window as any).saidasWorker.find((m: any) => m.type === "ready")?.info);
  const entrada = page.getByLabel("Selecionar foto da galeria", { exact: true });
  const region = page.getByRole("region", { name: "Resultado da análise" });
  const hipoteses = region.getByRole("group", { name: "Hipóteses de identificação" });
  const resultados: unknown[] = [];
  let esperados = 0;
  for (const item of itens) {
    const arquivo = path.join(pasta, item.arquivo);
    esperados += 1;
    try {
      await entrada.setInputFiles(arquivo);
      await expect.poll(
        () => page.evaluate(() => (window as any).saidasWorker.filter((m: any) => m.type === "result").length),
        { timeout: 60_000 },
      ).toBe(esperados);
      const previsoes = await page.evaluate(() => {
        const r = (window as any).saidasWorker.filter((m: any) => m.type === "result");
        return r[r.length - 1].result.predictions as { indice: number; nome: string; score: number }[];
      });
      await page.waitForTimeout(120);
      const scores = new Array(13).fill(0);
      for (const p of previsoes) scores[p.indice] = p.score;
      const topo = [...previsoes].sort((a, b) => b.score - a.score || a.indice - b.indice)[0];
      const aceitoNaTela = (await hipoteses.count()) > 0;
      let primeira = "";
      if (aceitoNaTela) primeira = (await hipoteses.getByRole("button").first().innerText()).replace(/\s+/g, " ");
      const inconclusivoNaTela = await region.getByRole("heading", { name: "Identificação inconclusiva" }).count();
      resultados.push({
        id: item.id, scores, top_nome: topo.nome, ui_decisao: aceitoNaTela ? "aceito" : inconclusivoNaTela ? "inconclusivo" : "indeterminado",
        ui_primeira_hipotese: primeira,
      });
    } catch (erro) {
      resultados.push({ id: item.id, erro: String(erro).slice(0, 200) });
      throw erro;
    }
  }
  return { info, resultados };
}

test("limiar de confiança no app: imagens fora do recorte e inadequadas (Float16 e INT8)", async ({ browser }) => {
  test.skip(!process.env.T11_3_IMAGENS, "Defina T11_3_IMAGENS com a pasta gerada por `python -m src.limiar_t11_3 preparar`");
  test.setTimeout(3_600_000);
  const pasta = process.env.T11_3_IMAGENS!;
  const manifestoBytes = readFileSync(manifestoCaminho);
  const manifesto = JSON.parse(manifestoBytes.toString("utf8")) as { imagens: (Item & { sha256: string })[] };
  for (const item of manifesto.imagens) {
    expect(sha256(readFileSync(path.join(pasta, item.arquivo))), `${item.id}: arquivo diferente do manifesto`).toBe(item.sha256);
  }
  const formatos: Record<string, unknown[]> = {};
  const infos: Record<string, unknown> = {};
  for (const formato of ["Float16", "INT8"] as const) {
    const context = await browser.newContext({ viewport: { width: 900, height: 1000 } });
    const page = await context.newPage();
    const { info, resultados } = await medir(page, formato, manifesto.imagens, pasta);
    formatos[formato] = resultados;
    infos[formato] = info;
    await context.close();
  }
  writeFileSync(saidaCaminho, JSON.stringify({
    esquema: "inferencias_web_T11_3_v1",
    manifesto_sha256: sha256(manifestoBytes),
    limiar_politica: politica.limiar_confianca,
    navegador: `Chromium ${browser.version()}`,
    runtime: "LiteRT.js 2.6.0",
    modelo: infos,
    formatos,
  }, null, 2) + "\n");
});
