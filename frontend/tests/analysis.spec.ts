import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import reference from "./fixtures/reference.json" with { type: "json" };

const fixtures = fileURLToPath(new URL("./fixtures/", import.meta.url));

test("executa INT8 real, compara com Python e reutiliza o modelo sem enviar a foto", async ({
  page,
}) => {
  const modelDownloads: string[] = [];
  const uploadRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().endsWith(".tflite")) modelDownloads.push(request.url());
    if (request.method() !== "GET") uploadRequests.push(request.url());
  });
  await page.addInitScript(() => {
    const NativeWorker = window.Worker;
    (window as unknown as { analysisMessages: unknown[] }).analysisMessages =
      [];
    window.Worker = class extends NativeWorker {
      constructor(url: string | URL, options?: WorkerOptions) {
        super(url, options);
        this.addEventListener("message", (event) => {
          if (event.data.type === "result")
            (
              window as unknown as { analysisMessages: unknown[] }
            ).analysisMessages.push(event.data);
        });
      }
    };
  });
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Adicionar foto", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible();
  const downloadsAfterLoad = modelDownloads.length;
  for (const [i, filename] of [
    "pattern.png",
    "orientation.jpg",
    "pattern.png",
  ].entries()) {
    await page
      .locator("input[type=file]")
      .setInputFiles(path.join(fixtures, filename));
    await expect
      .poll(() =>
        page.evaluate(
          () =>
            (window as unknown as { analysisMessages: unknown[] })
              .analysisMessages.length,
        ),
      )
      .toBe(i + 1);
    const predictions = await page.evaluate(() => {
      const messages = (
        window as unknown as {
          analysisMessages: {
            result: {
              predictions: { indice: number; score: number }[];
              width: number;
              height: number;
            };
          }[];
        }
      ).analysisMessages;
      return messages[messages.length - 1].result;
    });
    const expected =
      reference.predictions[filename as keyof typeof reference.predictions];
    for (const item of predictions.predictions)
      expect(Math.abs(item.score - expected[item.indice])).toBeLessThanOrEqual(
        2 / 256,
      );
    expect(predictions.predictions).toHaveLength(13);
    if (filename === "orientation.jpg") {
      expect(predictions.width).toBe(173);
      expect(predictions.height).toBe(391);
    }
    await expect(page.getByText("Top 3 hipóteses")).toBeVisible();
  }
  expect(modelDownloads.length).toBe(downloadsAfterLoad);
  expect(uploadRequests).toEqual([]);
  await page
    .getByRole("button", { name: "Entrada do modelo", exact: true })
    .click();
  await expect(
    page.getByAltText("Foto preparada para o modelo, com preenchimento cinza"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Remover foto", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Adicionar foto", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText("Top 3 hipóteses")).toHaveCount(0);
});

test("trata arquivo inválido, consulta as classes e mantém ajuda acessível", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Adicionar foto", exact: true }),
  ).toBeEnabled();
  await page
    .locator("input[type=file]")
    .setInputFiles({
      name: "arquivo.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("Não é uma foto"),
    });
  await expect(page.getByRole("alert")).toContainText("Formato não aceito");
  await page
    .locator("input[type=file]")
    .setInputFiles({
      name: "quebrada.jpg",
      mimeType: "image/jpeg",
      buffer: Buffer.from("imagem inválida"),
    });
  await expect(page.getByRole("alert")).toContainText(
    "Não foi possível abrir a foto",
  );
  await page
    .getByRole("button", { name: "Classes do modelo", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Cigarrinha-do-milho" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Cigarrinha-das-pastagens" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Como funciona", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
});

test("explica falha ao carregar o modelo e oferece recuperação", async ({
  page,
}) => {
  await page.route("**/models/*.tflite", (route) => route.abort());
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Verifique sua conexão");
  await expect(
    page.getByRole("button", { name: /Recarregar modelo/ }),
  ).toBeVisible();
  await page.unroute("**/models/*.tflite");
  await page.getByRole("button", { name: /Recarregar modelo/ }).click();
  await expect(
    page.getByRole("button", { name: "Adicionar foto", exact: true }),
  ).toBeEnabled();
});

test("executa a alternativa FP32 e identifica a troca de formato", async ({ page }) => {
  await page.route("**/models/manifest.json", async (route) => {
    const response = await route.fetch();
    const manifest = await response.json();
    manifest.models = manifest.models.filter((model: { format: string }) => model.format === "FP32");
    await route.fulfill({ response, json: manifest });
  });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Adicionar foto", exact: true })).toBeEnabled();
  await expect(page.getByText(/Este navegador está usando a versão FP32/)).toBeVisible();
  await page.locator("input[type=file]").setInputFiles(path.join(fixtures, "pattern.png"));
  await expect(page.getByText("Top 3 hipóteses")).toBeVisible();
});
