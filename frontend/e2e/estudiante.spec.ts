import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test.describe("Estudiante", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, "student");
  });

  test("una pregunta sugerida abre el tutor y recibe respuesta", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "¿Qué repasamos hoy?" })).toBeVisible();
    await page.getByRole("link", { name: "Explícame la derivada por definición" }).click();
    await expect(page).toHaveURL(/\/tutor$/);

    const log = page.getByRole("log", { name: "Conversación con el tutor" });
    await expect(log).toContainText("derivada", { timeout: 30_000 });
    // El tutor termina de escribir: vuelve a poder enviar.
    await expect(page.getByRole("button", { name: /Enviar|Detener/ }).first()).toBeVisible();
  });

  test("al notar frustración, el tutor ofrece ayuda del docente", async ({ page }) => {
    await page.goto("/tutor");
    await page.waitForLoadState("networkidle");
    await page.getByPlaceholder(/Pregunta lo que no te quedó claro/).fill("no entiendo nada, me rindo, esto es imposible");
    await page.keyboard.press("Enter");
    await expect(page.getByText("Este tema está costando, y es normal")).toBeVisible({ timeout: 30_000 });
  });

  test("las secciones de docente están bloqueadas", async ({ page }) => {
    await page.goto("/riesgo");
    await expect(page.getByRole("heading", { name: "Solo para docentes" })).toBeVisible();
  });
});
