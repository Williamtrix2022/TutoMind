import { test } from "@playwright/test";
import { login, useTheme } from "./helpers";
import type { DemoRole } from "./helpers";

/**
 * No comprueba nada: recorre las pantallas y guarda capturas en `e2e/screenshots/`
 * para revisar el diseño a ojo (claro, oscuro, escritorio y móvil).
 * Correr con: npm run e2e:capturas
 */
const STEPS: { role: DemoRole; routes: { path: string; name: string }[] }[] = [
  {
    role: "teacher",
    routes: [
      { path: "/", name: "docente-inicio" },
      { path: "/riesgo", name: "docente-riesgo" },
      { path: "/temas", name: "docente-temas" },
      { path: "/documentos", name: "docente-documentos" },
    ],
  },
  {
    role: "student",
    routes: [
      { path: "/", name: "estudiante-inicio" },
      { path: "/tutor", name: "estudiante-tutor" },
    ],
  },
];

for (const theme of ["dark", "light"] as const) {
  for (const { role, routes } of STEPS) {
    test(`capturas ${role} (${theme})`, async ({ page }, info) => {
      await useTheme(page, theme);
      await page.goto("/login");
      await page.screenshot({ path: `e2e/screenshots/${info.project.name}-${theme}-login.png`, fullPage: true });
      await login(page, role);
      for (const { path, name } of routes) {
        await page.goto(path);
        await page.waitForLoadState("networkidle");
        // Deja terminar las animaciones de entrada (anillos, barras, contadores).
        await page.waitForTimeout(1800);
        await page.screenshot({ path: `e2e/screenshots/${info.project.name}-${theme}-${name}.png`, fullPage: true });
      }
    });
  }
}
