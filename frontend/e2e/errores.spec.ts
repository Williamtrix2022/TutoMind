import { expect, test } from "@playwright/test";
import { alerta } from "./helpers";

test.describe("Errores", () => {
  test("contraseña incorrecta muestra un aviso y no entra", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.getByLabel("Correo").fill("ana@tutomind.demo");
    await page.getByLabel("Contraseña", { exact: true }).fill("contraseña-incorrecta");
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(alerta(page)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("con el backend caído se explica en español, sin «Failed to fetch»", async ({ page }) => {
    await page.route("**/api/v1/auth/login", (route) => route.abort("connectionrefused"));
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.getByLabel("Correo").fill("ana@tutomind.demo");
    await page.getByLabel("Contraseña", { exact: true }).fill("demo12345");
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(alerta(page)).toContainText("No pudimos conectar con el servidor");
    await expect(page.getByText("Failed to fetch")).toHaveCount(0);
  });

  test("sin sesión, entrar a una sección privada lleva al login", async ({ page }) => {
    await page.goto("/riesgo");
    await expect(page).toHaveURL(/\/login/);
  });
});
