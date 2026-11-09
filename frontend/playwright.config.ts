import { defineConfig, devices } from "@playwright/test";

const production = process.env.DEMO_PREVIEW === "1";
const port = production ? 4173 : 5173;
// O build + preview só é necessário para o projeto offline (ou para a demo congelada).
const args = process.argv.join(" ");
const onlyChromium = /--project[= ]chromium/.test(args) && !/offline/.test(args);
const preview = production || !onlyChromium;

export default defineConfig({
  testDir: "./tests",
  timeout: 120_000,
  expect: { timeout: 60_000 },
  workers: 1,
  use: { baseURL: `http://127.0.0.1:${port}`, trace: "retain-on-failure" },
  projects: [
    {
      name: "chromium",
      testIgnore: "offline.spec.ts",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      // O service worker só existe no build; por isso este projeto usa o preview.
      name: "offline",
      testMatch: "offline.spec.ts",
      use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:4173" },
    },
  ],
  webServer: [
    ...(production
      ? []
      : [
          {
            command: "npm run dev -- --port 5173 --strictPort",
            url: "http://127.0.0.1:5173",
            reuseExistingServer: !process.env.CI,
            timeout: 120_000,
          },
        ]),
    ...(preview
      ? [
          {
            // Na demo congelada serve o dist existente; senão gera o build com o sw.js.
            command: `${production ? "" : "npm run build && "}npm run preview -- --port 4173 --strictPort`,
            url: "http://127.0.0.1:4173",
            reuseExistingServer: !production && !process.env.CI,
            timeout: 300_000,
          },
        ]
      : []),
  ],
});
