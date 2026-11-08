import { defineConfig, devices } from "@playwright/test";

const production = process.env.DEMO_PREVIEW === "1";
const port = production ? 4173 : 5173;

export default defineConfig({
  testDir: "./tests",
  timeout: 120_000,
  expect: { timeout: 60_000 },
  workers: 1,
  use: { baseURL: `http://127.0.0.1:${port}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `npm run ${production ? "preview" : "dev"} -- --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: !production && !process.env.CI,
    timeout: 120_000,
  },
});
