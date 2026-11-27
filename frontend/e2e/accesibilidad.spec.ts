import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { login, useTheme } from "./helpers";
import type { DemoRole } from "./helpers";

/**
 * Auditoría de accesibilidad (WCAG 2.1 A y AA) con axe, en cada pantalla y en los dos temas.
 * Falla ante violaciones graves o críticas; el resto se imprime para revisarlo.
 */
const SCREENS: { role: DemoRole | null; path: string }[] = [
  { role: null, path: "/login" },
  { role: "teacher", path: "/" },
  { role: "teacher", path: "/riesgo" },
  { role: "teacher", path: "/temas" },
  { role: "teacher", path: "/documentos" },
  { role: "student", path: "/" },
  { role: "student", path: "/tutor" },
];

for (const theme of ["dark", "light"] as const) {
  for (const { role, path } of SCREENS) {
    test(`axe ${role ?? "público"} ${path} (${theme})`, async ({ page }) => {
      await useTheme(page, theme);
      if (role) await login(page, role);
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      // Espera a que terminen las animaciones de entrada: axe mide el contraste del color final.
      await page.waitForTimeout(2000);

      const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      const summary = violations.map((v) => `${v.impact} · ${v.id} · ${v.nodes.length} nodos · ${v.nodes[0]?.target.join(" ")}`);
      if (summary.length) console.log(`\n[${theme}] ${path}\n  ${summary.join("\n  ")}`);

      const serious = violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(serious.map((v) => v.id)).toEqual([]);
    });
  }
}
