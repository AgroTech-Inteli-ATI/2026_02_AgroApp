import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";
import classes from "../../assets/modelos/candidato_T5_6_20261026/classes.json" with { type: "json" };
import politica from "../../assets/data/politica_T6_5/parametros.json" with { type: "json" };
import { technicalContent, type TechnicalContent } from "../src/data/content";

// T13.3: apresentação do conteúdo técnico após a classificação.
// O worker é um dublê de transporte (como em confidence.spec.ts) para escolher a classe
// e o momento de cada resposta; a inferência real fica em analysis.spec.ts.
// Os casos com conteúdo usam um catálogo fictício entregue no lugar do módulo content.ts pelo
// servidor de desenvolvimento, para não depender do texto das fichas reais (T13.1); o CAT-01
// confere o catálogo versionado.

const foto = fileURLToPath(new URL("./fixtures/pattern.png", import.meta.url));
const nomes = classes.map((c) => c.nome);
const comum = (indice: number) => nomes[indice].split(" (")[0];

const ficha = (indice: number, fonte: string, reviewedAt: string, validated: boolean): TechnicalContent => ({
  title: `TESTE-T13.3 título da classe ${indice}`,
  scientificName: `TESTE-T13.3 nome científico ${indice}`,
  context: null,
  sections: [{
    id: "como_reconhecer",
    title: "Como reconhecer",
    items: [{ text: `TESTE-T13.3 texto da classe ${indice}`, source: `${fonte}, p. 1` }],
  }],
  sources: [`${fonte}, p. 1`],
  references: [`${fonte}. Referência completa fictícia.`],
  author: "Equipe fictícia",
  reviewedAt,
  validated,
});

const catalogoTeste: Record<number, TechnicalContent> = {
  0: ficha(0, "Fonte fictícia A", "2000-01-01", true),
  5: ficha(5, "Fonte fictícia B", "2000-02-02", true),
  // Item presente mas não validado: não pode ser exibido.
  2: ficha(2, "Fonte fictícia C", "2000-03-03", false),
};

// Primeira frase da ficha (o <li> traz também a fonte dela) e linha "Fonte:" como o painel de App.tsx as monta.
const primeiraFrase = (item: TechnicalContent) => item.sections[0].items[0].text;
const rodape = (item: TechnicalContent) =>
  `Fonte: ${item.sources.join("; ")} · Elaborado por ${item.author} · Revisado em ${item.reviewedAt}`;

type Passo = {
  top?: [number, number][];
  erro?: string;
  segurar?: boolean;
  reenviarAnterior?: boolean;
};

async function abrir(page: Page, roteiro: Passo[], catalogo: object | null = catalogoTeste) {
  if (catalogo)
    await page.route(/\/src\/data\/content\.ts(\?.*)?$/, (route) =>
      route.fulfill({
        contentType: "text/javascript",
        body: `export const technicalContent = ${JSON.stringify(catalogo)};`,
      }),
    );
  await page.addInitScript(({ nomes, roteiro }) => {
    const w = window as unknown as { liberar?: () => void };
    let posicao = 0;
    let anterior: { id: number; mensagem: unknown } | undefined;
    class FakeWorker {
      onmessage: ((e: { data: unknown }) => void) | null = null;
      onerror = null;
      terminate() {}
      postMessage(message: { type: string; id: number; file: File }) {
        const enviar = (data: unknown) => queueMicrotask(() => this.onmessage?.({ data }));
        if (message.type === "init") {
          enviar({ type: "ready", info: { id: "fixture", format: "Float16", bytes: 100, accelerator: "CPU", fallback: false } });
          return;
        }
        const passo = roteiro[posicao++];
        // Resposta e erro atrasados de uma análise anterior, já substituída.
        if (passo.reenviarAnterior && anterior) {
          enviar(anterior.mensagem);
          enviar({ type: "error", id: anterior.id, message: "Erro atrasado da análise anterior." });
        }
        if (passo.erro) {
          enviar({ type: "error", id: message.id, message: passo.erro });
          return;
        }
        const top = new Map(passo.top);
        const resto = (1 - [...top.values()].reduce((a, b) => a + b, 0)) / (nomes.length - top.size);
        const mensagem = {
          type: "result",
          id: message.id,
          result: {
            predictions: nomes.map((nome, indice) => ({ indice, nome, score: top.get(indice) ?? resto })),
            preview: message.file, preparationMs: 1, inferenceMs: 2, width: 224, height: 224,
          },
        };
        anterior = { id: message.id, mensagem };
        if (passo.segurar) w.liberar = () => enviar(mensagem);
        else enviar(mensagem);
      }
    }
    window.Worker = FakeWorker as unknown as typeof Worker;
  }, { nomes, roteiro });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Escolher da galeria", exact: true })).toBeEnabled();
  const regiao = page.getByRole("region", { name: "Resultado da análise" });
  return {
    regiao,
    hipoteses: regiao.getByRole("group", { name: "Hipóteses de identificação" }),
    enviar: (arquivo: string | Parameters<Page["setInputFiles"]>[1] = foto) =>
      page.getByLabel("Selecionar foto da galeria", { exact: true }).setInputFiles(arquivo),
  };
}

// Confere o painel de orientações: só o conteúdo da classe esperada, ou o aviso de indisponível.
async function conferirConteudo(page: Page, indice: number | null) {
  const regiao = page.getByRole("region", { name: "Resultado da análise" });
  const item = indice === null ? undefined : catalogoTeste[indice];
  const mostrado = item?.validated ? item : undefined;
  for (const item of Object.values(catalogoTeste))
    if (item !== mostrado) {
      await expect(regiao.getByText(item.title)).toHaveCount(0);
      await expect(regiao.getByText(primeiraFrase(item))).toHaveCount(0);
    }
  if (indice === null) {
    await expect(regiao.getByRole("heading", { name: "Orientações técnicas" })).toHaveCount(0);
    await expect(regiao.getByText(/Conteúdo técnico ainda indisponível|Fonte:/)).toHaveCount(0);
  } else if (mostrado) {
    await expect(regiao.getByText(mostrado.title, { exact: true })).toBeVisible();
    await expect(regiao.getByRole("listitem").filter({ hasText: primeiraFrase(mostrado) })).toBeVisible();
    await expect(regiao.getByText(rodape(mostrado), { exact: true })).toBeVisible();
    await expect(regiao.getByText(/Conteúdo técnico ainda indisponível/)).toHaveCount(0);
  } else {
    await expect(regiao.getByText(`Conteúdo técnico ainda indisponível para ${comum(indice)}.`, { exact: true })).toBeVisible();
    await expect(regiao.getByText(/Fonte:/)).toHaveCount(0);
  }
}

const selecionada = (hipoteses: ReturnType<Page["locator"]>) =>
  hipoteses.locator("button[aria-pressed='true']");

test("CON-01 a CON-03: mostra o conteúdo da hipótese escolhida e trata item ausente ou não validado", async ({ page }) => {
  const { hipoteses, enviar } = await abrir(page, [{ top: [[0, .8], [5, .1], [2, .05]] }]);
  await enviar();
  await expect(hipoteses.getByRole("button")).toHaveCount(politica.numero_hipoteses);
  // A hipótese principal abre já selecionada, com o conteúdo do índice dela.
  await expect(selecionada(hipoteses)).toHaveCount(1);
  await expect(selecionada(hipoteses)).toContainText(comum(0));
  await conferirConteudo(page, 0);
  // O conteúdo segue o índice da classe, não a posição no ranking.
  await hipoteses.getByRole("button", { name: new RegExp(comum(5)) }).click();
  await expect(selecionada(hipoteses)).toContainText(comum(5));
  await conferirConteudo(page, 5);
  // Item do catálogo com validated=false é tratado como ausente.
  await hipoteses.getByRole("button", { name: new RegExp(comum(2)) }).click();
  await conferirConteudo(page, 2);
  await hipoteses.getByRole("button", { name: new RegExp(comum(0)) }).click();
  await conferirConteudo(page, 0);
});

test("CON-04: classe sem conteúdo informa a ausência com o nome correto", async ({ page }) => {
  const { hipoteses, enviar } = await abrir(page, [{ top: [[12, .7], [7, .2], [0, .05]] }]);
  await enviar();
  await expect(selecionada(hipoteses)).toContainText(comum(12));
  await conferirConteudo(page, 12);
  await hipoteses.getByRole("button", { name: new RegExp(comum(7)) }).click();
  await conferirConteudo(page, 7);
  await hipoteses.getByRole("button", { name: new RegExp(comum(0)) }).click();
  await conferirConteudo(page, 0);
});

test("NOV-01 a NOV-03: nova imagem não reaproveita resultado, seleção nem conteúdo anteriores", async ({ page }) => {
  const { regiao, hipoteses, enviar } = await abrir(page, [
    { top: [[0, .8], [5, .1], [2, .05]] },
    { top: [[12, .7], [5, .2], [0, .05]], segurar: true },
    { top: [[5, .9], [0, .05], [1, .01]] },
  ]);
  await enviar();
  await hipoteses.getByRole("button", { name: new RegExp(comum(5)) }).click();
  await conferirConteudo(page, 5);
  await page.getByText("Detalhes do modelo e da execução").click();
  await expect(page.getByText("Inferência", { exact: true })).toBeVisible();

  // Enquanto a nova foto é analisada, nada do resultado anterior permanece na tela.
  await enviar();
  await expect(regiao.getByRole("heading", { name: "Observando os detalhes…" })).toBeVisible();
  await expect(hipoteses).toHaveCount(0);
  await conferirConteudo(page, null);
  await expect(regiao.getByText(/%/)).toHaveCount(0);
  await expect(page.getByText("Inferência", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Entrada do modelo", exact: true })).toHaveCount(0);

  // O novo resultado seleciona o próprio top-1, mesmo contendo a classe antes escolhida.
  await page.evaluate(() => (window as unknown as { liberar: () => void }).liberar());
  await expect(selecionada(hipoteses)).toContainText(comum(12));
  await conferirConteudo(page, 12);
  await expect(regiao.getByText("70%", { exact: true })).toBeVisible();

  await enviar();
  await expect(selecionada(hipoteses)).toContainText(comum(5));
  await conferirConteudo(page, 5);
  await expect(regiao.getByText("90%", { exact: true })).toBeVisible();
});

test("NOV-04: resposta ou erro atrasado da análise anterior é descartado", async ({ page }) => {
  const { regiao, hipoteses, enviar } = await abrir(page, [
    { top: [[0, .8], [5, .1], [2, .05]] },
    { top: [[5, .7], [12, .2], [1, .05]], segurar: true, reenviarAnterior: true },
  ]);
  await enviar();
  await conferirConteudo(page, 0);
  await enviar();
  // O worker devolveu de novo o resultado antigo e um erro antigo: a tela segue aguardando.
  await expect(regiao.getByRole("heading", { name: "Observando os detalhes…" })).toBeVisible();
  await expect(hipoteses).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await conferirConteudo(page, null);
  await page.evaluate(() => (window as unknown as { liberar: () => void }).liberar());
  await expect(selecionada(hipoteses)).toContainText(comum(5));
  await conferirConteudo(page, 5);
});

test("INC-01 a INC-03: inconclusivo não exibe classe nem conteúdo, e o aceito seguinte exibe o próprio", async ({ page }) => {
  const abaixo = politica.limiar_confianca - 0.000001;
  const { regiao, hipoteses, enviar } = await abrir(page, [
    { top: [[0, .8], [5, .1], [2, .05]] },
    { top: [[5, abaixo], [0, .2]] },
    { top: [[12, politica.limiar_confianca], [0, .2]] },
  ]);
  await enviar();
  await hipoteses.getByRole("button", { name: new RegExp(comum(5)) }).click();
  await conferirConteudo(page, 5);

  // Mesmo com a classe 5 no topo (abaixo do limiar), nada dela é mostrado.
  await enviar();
  await expect(regiao.getByRole("heading", { name: "Identificação inconclusiva" })).toBeVisible();
  await expect(regiao.getByText(politica.abaixo_do_limiar.mensagem, { exact: true })).toBeVisible();
  await expect(regiao.getByText(politica.abaixo_do_limiar.orientacao_nova_foto, { exact: true })).toBeVisible();
  await expect(hipoteses).toHaveCount(0);
  await conferirConteudo(page, null);
  for (const indice of [0, 5, 12]) await expect(regiao.getByText(comum(indice))).toHaveCount(0);
  await expect(regiao.getByText(/%/)).toHaveCount(0);

  // A entrada do modelo segue consultável e não traz identificação junto.
  await page.getByRole("button", { name: "Entrada do modelo", exact: true }).click();
  await expect(page.getByAltText("Foto preparada para o modelo, com preenchimento cinza")).toBeVisible();
  await expect(hipoteses).toHaveCount(0);

  await enviar();
  await expect(selecionada(hipoteses)).toContainText(comum(12));
  await conferirConteudo(page, 12);
  await expect(page.getByAltText("Foto selecionada para análise")).toBeVisible();
});

test("ERR-01 e ERR-02: falha na nova foto limpa o resultado; arquivo recusado mantém foto e resultado coerentes", async ({ page }) => {
  const { regiao, hipoteses, enviar } = await abrir(page, [
    { top: [[0, .8], [5, .1], [2, .05]] },
    { erro: "Não foi possível abrir a foto. Escolha outra imagem." },
  ]);
  await enviar();
  await conferirConteudo(page, 0);

  // Arquivo recusado antes da análise: a foto, o nome e o resultado exibidos continuam sendo os da análise anterior.
  await enviar({ name: "documento.txt", mimeType: "text/plain", buffer: Buffer.from("texto") });
  await expect(page.getByRole("alert")).toContainText("Formato não aceito");
  await expect(page.getByTitle("pattern.png")).toBeVisible();
  await expect(page.getByTitle("documento.txt")).toHaveCount(0);
  await conferirConteudo(page, 0);

  // Falha durante a análise da nova foto: nenhum resultado anterior fica associado a ela.
  await enviar({ name: "quebrada.jpg", mimeType: "image/jpeg", buffer: Buffer.from("x") });
  await expect(page.getByRole("alert")).toContainText("Não foi possível abrir a foto");
  await expect(page.getByTitle("quebrada.jpg")).toBeVisible();
  await expect(regiao.getByRole("heading", { name: "O que a sua foto revela?" })).toBeVisible();
  await expect(hipoteses).toHaveCount(0);
  await conferirConteudo(page, null);
});

test("NAV-01 a NAV-05: abas, ajuda e remoção preservam ou limpam o conteúdo sem misturar resultados", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  const { regiao, hipoteses, enviar } = await abrir(page, [{ top: [[0, .8], [5, .1], [2, .05]] }]);
  await enviar();
  await hipoteses.getByRole("button", { name: new RegExp(comum(5)) }).click();
  await conferirConteudo(page, 5);
  const foto = await page.getByAltText("Foto selecionada para análise").getAttribute("src");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);

  // O catálogo de classes é consulta independente: não mostra o conteúdo nem a identificação.
  await page.getByRole("button", { name: "Classes do modelo", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Catálogo de reconhecimento" })).toBeVisible();
  await expect(regiao).toHaveCount(0);
  for (const item of Object.values(catalogoTeste)) await expect(page.getByText(item.title)).toHaveCount(0);
  await expect(page.getByText(/Conteúdo técnico|Orientações técnicas/)).toHaveCount(0);

  // Voltar mantém a mesma foto, a mesma hipótese escolhida e o conteúdo dela.
  await page.getByRole("button", { name: "Analisar uma foto" }).click();
  await expect(page.getByAltText("Foto selecionada para análise")).toHaveAttribute("src", foto!);
  await expect(selecionada(hipoteses)).toContainText(comum(5));
  await conferirConteudo(page, 5);

  await page.getByRole("button", { name: "Como funciona", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(selecionada(hipoteses)).toContainText(comum(5));
  await conferirConteudo(page, 5);

  await page.getByRole("button", { name: "Remover foto", exact: true }).click();
  await expect(regiao.getByRole("heading", { name: "O que a sua foto revela?" })).toBeVisible();
  await conferirConteudo(page, null);
  await page.getByRole("button", { name: "Classes do modelo", exact: true }).click();
  await page.getByRole("button", { name: "Analisar foto", exact: true }).click();
  await expect(regiao.getByRole("heading", { name: "O que a sua foto revela?" })).toBeVisible();
  await expect(hipoteses).toHaveCount(0);
  await conferirConteudo(page, null);
});

test("CAT-01: com o catálogo versionado, cada hipótese mostra o conteúdo validado ou a ausência dele", async ({ page }) => {
  const { regiao, hipoteses, enviar } = await abrir(page, [{ top: [[0, .7], [1, .1], [2, .05]] }], null);
  await enviar();
  for (const indice of [0, 1, 2]) {
    await hipoteses.getByRole("button", { name: new RegExp(comum(indice)) }).click();
    const item = technicalContent[indice];
    if (item?.validated) {
      // O título real repete o nome comum do botão da hipótese; a frase e o rodapé são únicos do painel.
      await expect(regiao.getByRole("listitem").filter({ hasText: primeiraFrase(item) })).toBeVisible();
      await expect(regiao.getByText(rodape(item), { exact: true })).toBeVisible();
    } else {
      await expect(regiao.getByText(`Conteúdo técnico ainda indisponível para ${comum(indice)}.`, { exact: true })).toBeVisible();
      await expect(regiao.getByText(/Fonte:/)).toHaveCount(0);
    }
  }
  // Nenhum texto fictício do teste pode vazar para o catálogo real.
  await expect(page.getByText(/TESTE-T13\.3/)).toHaveCount(0);
});
