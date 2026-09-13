import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/visual",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:15174",
    locale: "en-GB",
    timezoneId: "UTC",
    colorScheme: "dark",
    reducedMotion: "reduce",
  },
  webServer: {
    command: "npm run dev -- --port 15174 --strictPort",
    url: "http://127.0.0.1:15174",
  },
  snapshotPathTemplate: "{testDir}/baselines/{arg}{ext}",
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.001 } },
});
