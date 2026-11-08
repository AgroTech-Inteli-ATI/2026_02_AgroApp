import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";

await mkdir(".work/t9-1", { recursive: true });
const browser = await chromium.launch();
try {
  for (const [name, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 900]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    await page.goto("http://127.0.0.1:5173/");
    await page.getByText("Modelo pronto", { exact: true }).waitFor();
    await page.screenshot({ path: `.work/t9-1/${process.argv[2]}-${name}.png`, fullPage: true });
    console.log(JSON.stringify({ name, overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth) }));
    await page.close();
  }
} finally {
  await browser.close();
}
