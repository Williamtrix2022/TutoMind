import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

export type DemoRole = "teacher" | "student";

/** Usuarios que crea `python -m app.db.seed`. */
export const DEMO_USERS: Record<DemoRole, { email: string; password: string; label: string }> = {
  teacher: { email: "docente@tutomind.demo", password: process.env.E2E_PASSWORD ?? "demo12345", label: "Docente" },
  student: { email: "ana@tutomind.demo", password: process.env.E2E_PASSWORD ?? "demo12345", label: "Estudiante" },
};

/** El aviso de la interfaz; excluye el `role="alert"` interno de Next.js que anuncia cambios de ruta. */
export const alerta = (page: Page) => page.locator('[role="alert"]:not(#__next-route-announcer__)');

/** Fija el tema antes de que cargue la página (el script del layout lo lee de localStorage). */
export async function useTheme(page: Page, theme: "dark" | "light") {
  await page.addInitScript((value) => window.localStorage.setItem("tm-theme", value), theme);
}

/** Entra por el formulario real de login. */
export async function login(page: Page, role: DemoRole) {
  const user = DEMO_USERS[role];
  await page.goto("/login");
  // Con el servidor de desarrollo en frío, enviar antes de hidratar hace un envío nativo del formulario.
  await page.waitForLoadState("networkidle");
  await page.getByRole("radio", { name: user.label }).click();
  await page.getByLabel("Correo").fill(user.email);
  await page.getByLabel("Contraseña", { exact: true }).fill(user.password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).not.toHaveURL(/\/login/, { timeout: 30_000 });
}
