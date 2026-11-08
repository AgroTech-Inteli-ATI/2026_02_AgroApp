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
  await expect(page.getByText("Top 3 hipóteses")).toBeVisible();
  // Com a rede desligada, qualquer arquivo fora do cache apareceria como falha.
  expect(network).toEqual([]);
});
