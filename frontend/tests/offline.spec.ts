import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const fixtures = fileURLToPath(new URL("./fixtures/", import.meta.url));

// T9.4: depois de uma visita com rede, o app reabre e classifica sem nenhuma conexão.
test("reabre e classifica sem rede depois da primeira visita", async ({ page, context }) => {
  await page.goto("/");
  await expect(page.getByText(/disponível offline/)).toBeVisible();

  await context.setOffline(true);
  const network: string[] = [];
  page.on("requestfailed", (request) => network.push(request.url()));
  await page.reload();

  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible();
  const choosing = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Escolher da galeria", exact: true }).click();
  await (await choosing).setFiles(path.join(fixtures, "pattern.png"));
  // A foto sintética fica abaixo do limiar (T9.2); qualquer um dos dois estados prova a inferência offline.
  const region = page.getByRole("region", { name: "Resultado da análise" });
  await expect(
    region
      .getByRole("heading", { name: "Identificação inconclusiva" })
      .or(region.getByRole("group", { name: "Hipóteses de identificação" })),
  ).toBeVisible();

  // Painel técnico: dublê só do worker (como no confidence.spec.ts) para forçar um resultado aceito.
  await page.addInitScript(() => {
    class FakeWorker {
      onmessage: ((e: { data: unknown }) => void) | null = null;
      onerror = null;
      terminate() {}
      postMessage(message: { type: string; id?: number; file?: File }) {
        const data =
          message.type === "init"
            ? { type: "ready", info: { id: "fixture", format: "Float16", bytes: 100, accelerator: "CPU", fallback: false } }
            : {
                type: "result",
                id: message.id,
                result: {
                  predictions: Array.from({ length: 13 }, (_, indice) => ({
                    indice, nome: `Classe de teste ${indice}`, score: indice === 0 ? 0.9 : 0.1 / 12,
                  })),
                  preview: message.file, preparationMs: 1, inferenceMs: 2, width: 224, height: 224,
                },
              };
        queueMicrotask(() => this.onmessage?.({ data }));
      }
    }
    window.Worker = FakeWorker as unknown as typeof Worker;
  });
  await page.reload();
  await page.getByLabel("Selecionar foto da galeria", { exact: true }).setInputFiles(path.join(fixtures, "pattern.png"));
  await expect(region.getByRole("heading", { name: "Orientações técnicas" })).toBeVisible();
  // Hoje "indisponível"; quando o content.ts for preenchido, o painel passa a mostrar a fonte.
  await expect(region.getByText(/Conteúdo técnico ainda indisponível|Fonte:/)).toBeVisible();
  // Com a rede desligada, qualquer arquivo fora do cache apareceria como falha.
  expect(network).toEqual([]);
});

test("avisa quando o pré-cache falha", async ({ page }) => {
  // Simula queda de rede/cota no pré-cache de um modelo; o app em si carrega normalmente.
  await page.context().route(/\.tflite$/, (route) =>
    route.request().serviceWorker() ? route.abort() : route.continue(),
  );
  await page.goto("/");
  await expect(page.getByText(/modo offline indisponível/)).toBeVisible();
});
