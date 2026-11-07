import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import reference from "./fixtures/reference.json" with { type: "json" };
import type { ModelManifest } from "../src/types";

const fixtures = fileURLToPath(new URL("./fixtures/", import.meta.url));

test("executa INT8 real, compara com Python e reutiliza o modelo sem enviar a foto", async ({
  page,
}) => {
  const response = await page.request.get("/models/manifest.json");
  expect(response.ok()).toBeTruthy();
  const manifest = (await response.json()) as ModelManifest;
  const int8 = manifest.models.find((model) => model.format === "INT8")!;
  expect(int8.sourceSha256).toBe(reference.modelSha256);
  expect(int8.sha256).toBe(reference.webModelSha256);
  expect(int8.sourcePath).toBe(reference.modelSourcePath);
  expect(int8.version).toBe(reference.modelVersion);
  expect(manifest.classesSource.sha256).toBe(reference.classesSha256);
  expect(reference.webSpecializationVerified).toBe(true);
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
    page.getByRole("button", { name: "Escolher da galeria", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText("Modelo pronto", { exact: true })).toBeVisible();
  const downloadsAfterLoad = modelDownloads.length;
  for (const [i, filename] of [
    "pattern.png",
    "orientation.jpg",
    "pattern.png",
  ].entries()) {
    const choosing = page.waitForEvent("filechooser");
    await page.getByRole("button", {
      name: i === 0 ? "Escolher da galeria" : "Tirar outra foto",
      exact: true,
    }).click();
    const chooser = await choosing;
    expect(await chooser.element().getAttribute("capture")).toBe(i === 0 ? null : "environment");
    await chooser.setFiles(path.join(fixtures, filename));
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
    page.getByRole("button", { name: "Escolher da galeria", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText("Top 3 hipóteses")).toHaveCount(0);
});

test("trata arquivo inválido, consulta as classes e mantém ajuda acessível", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Escolher da galeria", exact: true }),
  ).toBeEnabled();
  await page
    .getByLabel("Selecionar foto da galeria", { exact: true })
    .setInputFiles({
      name: "arquivo.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("Não é uma foto"),
    });
  await expect(page.getByRole("alert")).toContainText("Formato não aceito");
  await page
    .getByLabel("Selecionar foto da galeria", { exact: true })
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
    page.getByRole("button", { name: "Escolher da galeria", exact: true }),
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
  await expect(page.getByRole("button", { name: "Escolher da galeria", exact: true })).toBeEnabled();
  await expect(page.getByText(/Este navegador está usando a versão FP32/)).toBeVisible();
  await page.getByLabel("Selecionar foto da galeria", { exact: true }).setInputFiles(path.join(fixtures, "pattern.png"));
  await expect(page.getByText("Top 3 hipóteses")).toBeVisible();
});

test("mantém a foto ao cancelar e permite repetir a captura em tela móvel", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/");
  const takePhoto = page.getByRole("button", { name: "Tirar foto", exact: true });
  await expect(takePhoto).toBeEnabled();
  const openingCamera = page.waitForEvent("filechooser");
  await takePhoto.click();
  const camera = await openingCamera;
  expect(await camera.element().getAttribute("capture")).toBe("environment");
  await camera.setFiles(path.join(fixtures, "orientation.jpg"));
  await expect(page.getByText("Top 3 hipóteses")).toBeVisible();
  const photo = page.getByAltText("Foto selecionada para análise");
  const originalUrl = await photo.getAttribute("src");
  const resultRegion = page.getByRole("region", { name: "Resultado da análise" });
  const previousResult = await resultRegion.textContent();

  for (const name of ["Tirar outra foto", "Trocar foto"]) {
    const choosing = page.waitForEvent("filechooser");
    await page.getByRole("button", { name, exact: true }).click();
    await (await choosing).setFiles([]);
    await expect(photo).toHaveAttribute("src", originalUrl!);
    await expect(resultRegion).toHaveText(previousResult!);
    await expect(page.getByRole("alert")).toHaveCount(0);
  }

  const choosing = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Tirar outra foto", exact: true }).click();
  await (await choosing).setFiles(path.join(fixtures, "orientation.jpg"));
  await expect(photo).not.toHaveAttribute("src", originalUrl!);
  await expect(page.getByRole("button", { name: "Tirar outra foto", exact: true })).toBeEnabled();
  await expect(page.getByText("Top 3 hipóteses")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});
