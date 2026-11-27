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

  test("el docente es la última instancia: se ofrece si la frustración persiste y solo se registra al aceptar", async ({
    page,
  }) => {
    await page.goto("/tutor");
    await page.waitForLoadState("networkidle");
    const box = page.getByPlaceholder(/Pregunta lo que no te quedó claro/);
    const log = page.getByRole("log", { name: "Conversación con el tutor" });
    const offer = page.getByText("¿Quieres que le envíe esta consulta y nuestro historial al profesor");

    // Una sola frase frustrada solo suaviza el tono: todavía no se ofrece el docente.
    await box.fill("no entiendo nada, me rindo");
    await page.keyboard.press("Enter");
    await expect(log).toContainText("Te entiendo", { timeout: 30_000 });
    await expect(offer).toHaveCount(0);

    // Si la frustración persiste, el tutor ofrece enviar la duda y la conversación al docente.
    await box.fill("sigo sin entender, esto es imposible, me rindo");
    await page.keyboard.press("Enter");
    await expect(offer).toBeVisible({ timeout: 30_000 });

    // Nada se registra hasta que el estudiante acepta.
    await page.getByRole("button", { name: "Sí, enviarla al profesor" }).click();
    await expect(page.getByText("Listo, tu docente ya tiene tu consulta")).toBeVisible({ timeout: 30_000 });
  });

  test("las secciones de docente están bloqueadas", async ({ page }) => {
    await page.goto("/riesgo");
    await expect(page.getByRole("heading", { name: "Solo para docentes" })).toBeVisible();
  });
});
