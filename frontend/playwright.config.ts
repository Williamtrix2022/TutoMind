import { defineConfig, devices } from "@playwright/test";

/**
 * Pruebas end-to-end contra el backend REAL (no mocks).
 * Antes de correrlas: base de datos + migraciones + seed + `uvicorn` en el puerto 8000
 * (ver docs/TutoMind_Mvp.md, sección 8). El frontend lo levanta Playwright si no está encendido.
 */
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: { baseURL, locale: "es-CO", trace: "retain-on-failure" },
  projects: [
    { name: "escritorio", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } } },
    { name: "movil", use: { ...devices["Pixel 7"] } },
  ],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : { command: "npm run dev", url: baseURL, reuseExistingServer: true, timeout: 120_000 },
});
