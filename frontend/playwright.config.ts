import { defineConfig, devices } from "@playwright/test";

const production = process.env.DEMO_PREVIEW === "1";
const port = production ? 4173 : 5173;

export default defineConfig({
  testDir: "./tests",
  timeout: 120_000,
  expect: { timeout: 60_000 },
  workers: 1,
<<<<<<< HEAD
  use: { baseURL: "http://127.0.0.1:5173", trace: "retain-on-failure" },
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
    {
      command: "npm run dev -- --port 5173",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "npm run build && npm run preview -- --port 4173 --strictPort",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: !process.env.CI,
      timeout: 300_000,
    },
  ],
=======
  use: { baseURL: `http://127.0.0.1:${port}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `npm run ${production ? "preview" : "dev"} -- --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: !production && !process.env.CI,
    timeout: 120_000,
  },
>>>>>>> 5c13d2447fa3751a7c81b5dbcc83a776551268cb
});
