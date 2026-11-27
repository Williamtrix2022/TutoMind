import { expect, test } from "@playwright/test";
import { alerta, login } from "./helpers";

/** Un PDF mínimo pero válido, con texto extraíble. */
function minimalPdf(text: string): Buffer {
  const stream = `BT /F1 12 Tf 72 720 Td (${text}) Tj ET`;
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  let body = "%PDF-1.4\n";
  const offsets: number[] = [];
  objects.forEach((object, index) => {
    offsets.push(body.length);
    body += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xref = body.length;
  body += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const offset of offsets) body += `${String(offset).padStart(10, "0")} 00000 n \n`;
  body += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(body, "latin1");
}

test.describe("Docente", () => {
  test.beforeEach(async ({ page }) => {
    await login(page, "teacher");
  });

  test("el inicio muestra datos reales del curso", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Tu aula, de un vistazo" })).toBeVisible();
    await expect(page.getByText("Requieren atención")).toBeVisible();
    await expect(page.getByText("Termómetro del aula")).toBeVisible();
  });

  test("riesgo: semáforo, lista, filtro y panel XAI", async ({ page }) => {
    await page.goto("/riesgo");
    const list = page.getByRole("list", { name: "Estudiantes por riesgo" });
    await expect(list.getByRole("button")).toHaveCount(5);

    // La lista llega ordenada: lo más urgente primero.
    await expect(list.getByRole("button").first()).toContainText("Riesgo alto");

    // El panel con los factores explícitos.
    await list.getByRole("button").first().click();
    await expect(page.getByRole("heading", { name: "Qué explica este resultado" })).toBeVisible();
    await expect(page.getByText("nota proyectada").first()).toBeVisible();

    // En móvil el panel es una hoja modal: Escape la cierra (en escritorio no hace nada).
    await page.keyboard.press("Escape");

    // Filtrar cambia la lista pero no el semáforo del curso.
    await page.getByRole("radio", { name: "Alto" }).click();
    await expect(list.getByRole("button")).toHaveCount(2);
    await expect(page.getByRole("button", { name: /Riesgo bajo/ })).toContainText("1");
  });

  test("temas: alerta de confusión y preguntas de ejemplo", async ({ page }) => {
    await page.goto("/temas");
    await expect(page.getByRole("heading", { name: "Necesitan atención" })).toBeVisible();
    await expect(page.getByText("Confusión grupal").first()).toBeVisible();
    await page.getByRole("button", { name: /preguntas? de ejemplo/ }).first().click();
    await expect(page.getByText(/«.+»/).first()).toBeVisible();
  });

  test("documentos: sube un PDF y llega a Indexado", async ({ page }) => {
    await page.goto("/documentos");
    const name = `apuntes-e2e-${Date.now()}.pdf`;
    await page.locator('input[type="file"]').setInputFiles({
      name,
      mimeType: "application/pdf",
      buffer: minimalPdf("La integral definida mide el area bajo una curva."),
    });
    const row = page.getByRole("listitem").filter({ hasText: name }).last();
    await expect(row).toContainText("Indexado", { timeout: 40_000 });
  });

  test("un archivo que no es PDF, DOCX o PPTX se rechaza", async ({ page }) => {
    await page.goto("/documentos");
    await page.locator('input[type="file"]').setInputFiles({ name: "virus.exe", mimeType: "application/octet-stream", buffer: Buffer.from("x") });
    await expect(alerta(page)).toBeVisible();
  });
});
