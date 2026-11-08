import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import politica from "../../assets/data/politica_T6_5/parametros.json" with { type: "json" };

const foto = fileURLToPath(new URL("./fixtures/pattern.png", import.meta.url));

for (const format of ["Float16", "INT8"]) {
  test(`trata limiar, transições e nova foto na interface com ${format}`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    // Dublê apenas do transporte do worker: testa as fronteiras exatas da UI.
    // analysis.spec.ts mantém a inferência real dos dois arquivos TFLite.
    await page.addInitScript(({ format, limiar }) => {
      let posicao = 0;
      const scores = [.9, limiar - .000001, limiar, .4];
      class FakeWorker {
        onmessage: ((e: { data: unknown }) => void) | null = null;
        onerror = null;
        terminate() {}
        postMessage(message: { type: string; id?: number; file?: File }) {
          if (message.type === "init") {
            queueMicrotask(() => this.onmessage?.({ data: {
              type: "ready", info: { id: "fixture", format, bytes: 100, accelerator: "CPU", fallback: format === "INT8" },
            } }));
          } else {
            const top = scores[posicao++];
            const predictions = Array.from({ length: 13 }, (_, indice) => ({
              indice, nome: `Classe de teste ${indice}`, score: indice === 0 ? top : (1-top)/12,
            }));
            queueMicrotask(() => this.onmessage?.({ data: { type: "result", id: message.id, result: {
              predictions, preview: message.file, preparationMs: 1, inferenceMs: 2, width: 224, height: 224,
            } } }));
          }
        }
      }
      window.Worker = FakeWorker as unknown as typeof Worker;
    }, { format, limiar: politica.limiar_confianca });
    await page.goto("/");
    const input = page.getByLabel("Selecionar foto da galeria", { exact: true });
    await expect(page.getByRole("button", { name: "Escolher da galeria", exact: true })).toBeEnabled();
    const region = page.getByRole("region", { name: "Resultado da análise" });
    const hipoteses = region.getByRole("group", { name: "Hipóteses de identificação" });

    // Aceito: hipóteses secundárias também aparecem, ainda que tenham score baixo.
    await input.setInputFiles(foto);
    await expect(hipoteses.getByRole("button")).toHaveCount(politica.numero_hipoteses);
    await expect(region.getByText("Classe de teste 0", { exact: true })).toBeVisible();
    await hipoteses.getByRole("button").nth(1).click();

    // O resultado anterior e a classe selecionada não podem vazar para o inconclusivo.
    await input.setInputFiles(foto);
    await expect(region.getByText(politica.abaixo_do_limiar.mensagem, { exact: true })).toBeVisible();
    await expect(region.getByText(politica.abaixo_do_limiar.orientacao_nova_foto, { exact: true })).toBeVisible();
    await expect(hipoteses).toHaveCount(0);
    await expect(region.getByRole("heading", { name: "Orientações técnicas" })).toHaveCount(0);
    await expect(region.getByText(/Classe de teste/)).toHaveCount(0);

    // Cancelar a tentativa mantém o estado inconclusivo.
    const choosing = page.waitForEvent("filechooser");
    await region.getByRole("button", { name: "Tentar outra foto", exact: true }).click();
    const chooser = await choosing;
    expect(await chooser.element().getAttribute("capture")).toBe("environment");
    await chooser.setFiles([]);
    await expect(region.getByText(politica.abaixo_do_limiar.mensagem, { exact: true })).toBeVisible();

    // Igualdade aceita (sem arredondar antes da decisão).
    await input.setInputFiles(foto);
    await expect(hipoteses.getByRole("button")).toHaveCount(politica.numero_hipoteses);
    await expect(region.getByRole("heading", { name: "Identificação inconclusiva" })).toHaveCount(0);
    await expect(region.getByText("Classe de teste 0", { exact: true })).toBeVisible();

    // Nova tentativa abaixo do limite e remoção limpam a identificação novamente.
    await input.setInputFiles(foto);
    await expect(region.getByRole("heading", { name: "Identificação inconclusiva" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
    await page.screenshot({ path: path.join(test.info().outputDir, `inconclusivo-${format}.png`), fullPage: true });
    await region.screenshot({ path: path.join(test.info().outputDir, `painel-inconclusivo-${format}.png`) });
    await page.getByRole("button", { name: "Remover foto", exact: true }).click();
    await expect(region.getByRole("heading", { name: "O que a sua foto revela?" })).toBeVisible();
    await expect(hipoteses).toHaveCount(0);
  });
}
