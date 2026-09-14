import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:15173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command:
        "../../.venv/bin/uvicorn backend.main:app --app-dir ../.. --host 127.0.0.1 --port 18000",
      url: "http://127.0.0.1:18000/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev -- --port 15173 --strictPort",
      url: "http://127.0.0.1:15173",
      env: { BACKEND_URL: "http://127.0.0.1:18000" },
      reuseExistingServer: !process.env.CI,
    },
  ],
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.01 } },
  snapshotPathTemplate: "{testDir}/baselines/{arg}{ext}",
});
