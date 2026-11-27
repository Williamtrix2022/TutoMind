import AxeBuilder from "@axe-core/playwright";
import { test } from "@playwright/test";
import { login, useTheme } from "./helpers";
import type { DemoRole } from "./helpers";

// Herramienta de diagnóstico: imprime colores y razones de contraste de cada nodo. No se corre en `npm run e2e`.
const CASES: { role: DemoRole; path: string; theme: "dark" | "light" }[] = [
  { role: "teacher", path: "/", theme: "light" },
  { role: "teacher", path: "/riesgo", theme: "light" },
  { role: "teacher", path: "/temas", theme: "light" },
  { role: "teacher", path: "/documentos", theme: "dark" },
  { role: "student", path: "/", theme: "dark" },
];

for (const { role, path, theme } of CASES) {
  test(`debug-axe ${role} ${path} ${theme}`, async ({ page }) => {
    await useTheme(page, theme);
    await login(page, role);
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);
    const { violations } = await new AxeBuilder({ page }).withRules(["color-contrast"]).analyze();
    for (const v of violations) {
      for (const n of v.nodes) {
        const d = n.any[0]?.data as { fgColor?: string; bgColor?: string; contrastRatio?: number; expectedContrastRatio?: string } | undefined;
        const text = await page.locator(n.target.join(" ")).first().innerText().catch(() => "?");
        console.log(`[${theme}] ${path} | "${text.replace(/\s+/g, " ").slice(0, 40)}" fg=${d?.fgColor} bg=${d?.bgColor} ratio=${d?.contrastRatio} need=${d?.expectedContrastRatio}`);
      }
    }
  });
}
