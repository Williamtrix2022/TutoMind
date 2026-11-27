// Genera los PDF de ejemplo del curso de demo en docs/demo/ (usa el Chromium de Playwright).
// Uso: node scripts/generate-demo-pdfs.mjs
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "docs", "demo");

const STYLE = `
  @page { size: A4; margin: 22mm 20mm; }
  body { font-family: Georgia, "Times New Roman", serif; color: #111; line-height: 1.55; font-size: 12.5pt; }
  h1 { font-family: Arial, sans-serif; font-size: 24pt; margin: 0 0 4pt; }
  h2 { font-family: Arial, sans-serif; font-size: 14pt; margin: 18pt 0 4pt; }
  .sub { color: #555; margin: 0 0 14pt; font-family: Arial, sans-serif; font-size: 10.5pt; }
  .formula { font-family: "Cambria Math", "Times New Roman", serif; background: #f2f3f8; padding: 6pt 10pt; border-radius: 4pt; margin: 6pt 0; }
  li { margin: 3pt 0; }
`;

const DOCS = [
  {
    file: "Derivadas.pdf",
    html: `<h1>Derivadas</h1><p class="sub">Cálculo Diferencial · Apuntes de apoyo</p>
<h2>Qué es la derivada</h2>
<p>La derivada de una función en un punto mide qué tan rápido cambia la función en ese punto. Geométricamente es la pendiente de la recta tangente a la gráfica; físicamente es una tasa de cambio instantánea, como la velocidad.</p>
<h2>Definición por límite</h2>
<p class="formula">f'(x) = lím (h → 0) [ f(x + h) − f(x) ] / h</p>
<p>El cociente es la pendiente de una recta secante. Al hacer que h tienda a cero, la secante se convierte en la tangente.</p>
<p><b>Ejemplo.</b> Para f(x) = x²: f(x + h) − f(x) = (x + h)² − x² = 2xh + h². Al dividir entre h queda 2x + h, y cuando h tiende a cero el límite es 2x. Entonces f'(x) = 2x.</p>
<h2>Reglas básicas</h2>
<ul>
<li><b>Constante:</b> la derivada de una constante es 0.</li>
<li><b>Potencia:</b> d/dx (xⁿ) = n · xⁿ⁻¹.</li>
<li><b>Suma:</b> (f + g)' = f' + g'.</li>
<li><b>Producto:</b> (f · g)' = f' · g + f · g'.</li>
<li><b>Cociente:</b> (f / g)' = (f' · g − f · g') / g².</li>
</ul>
<h2>Regla de la cadena</h2>
<p>Se usa cuando una función está dentro de otra, es decir, una función compuesta f(g(x)). Se deriva la función de afuera sin tocar la de adentro y se multiplica por la derivada de la de adentro.</p>
<p class="formula">( f(g(x)) )' = f'(g(x)) · g'(x)</p>
<p><b>Ejemplo.</b> Para y = sen(3x), la función de afuera es el seno y la de adentro es 3x. Entonces y' = cos(3x) · 3 = 3 cos(3x).</p>
<h2>Errores frecuentes</h2>
<ul>
<li>Olvidar multiplicar por la derivada de la función interior en la regla de la cadena.</li>
<li>Derivar un producto como el producto de las derivadas: (f · g)' no es f' · g'.</li>
<li>Confundir la derivada de xⁿ con la de aˣ: son reglas distintas.</li>
</ul>`,
  },
  {
    file: "Integrales.pdf",
    html: `<h1>Integrales</h1><p class="sub">Cálculo Integral · Apuntes de apoyo</p>
<h2>Integral indefinida</h2>
<p>La integral indefinida de f es el conjunto de todas sus antiderivadas: funciones cuya derivada es f. Por eso siempre se suma una constante de integración C.</p>
<ul>
<li>∫ xⁿ dx = xⁿ⁺¹ / (n + 1) + C, siempre que n sea distinto de −1.</li>
<li>∫ 1/x dx = ln|x| + C.</li>
<li>∫ eˣ dx = eˣ + C.</li>
<li>∫ cos x dx = sen x + C.</li>
<li>∫ sen x dx = −cos x + C.</li>
</ul>
<h2>Integral definida y área</h2>
<p>La integral definida de a hasta b mide el área con signo entre la gráfica de f y el eje x. El Teorema Fundamental del Cálculo permite calcularla con una antiderivada F:</p>
<p class="formula">∫ de a hasta b de f(x) dx = F(b) − F(a)</p>
<p><b>Ejemplo.</b> Para ∫ de 0 hasta 2 de x² dx, una antiderivada es x³/3. Entonces el valor es 2³/3 − 0³/3 = 8/3.</p>
<h2>Sustitución</h2>
<p>Sirve cuando dentro de la integral aparece una función y su derivada. Se escribe u = g(x) y du = g'(x) dx. En una integral definida también se cambian los límites: se evalúa u en los valores originales de x.</p>
<p><b>Ejemplo.</b> Para ∫ de 0 hasta 1 de 2x (x² + 1)³ dx, sea u = x² + 1, de modo que du = 2x dx. Cuando x = 0, u = 1; cuando x = 1, u = 2. La integral queda ∫ de 1 hasta 2 de u³ du = [u⁴/4] de 1 a 2 = (16 − 1)/4 = 15/4.</p>
<h2>Errores frecuentes</h2>
<ul>
<li>Olvidar la constante C en una integral indefinida.</li>
<li>No cambiar los límites al sustituir en una integral definida.</li>
<li>Aplicar la regla de la potencia a 1/x: su integral es ln|x|, no x⁰/0.</li>
</ul>`,
  },
  {
    file: "Límites.pdf",
    html: `<h1>Límites</h1><p class="sub">Cálculo Diferencial · Apuntes de apoyo</p>
<h2>Idea de límite</h2>
<p>El límite de f(x) cuando x tiende a a es el valor al que se acerca f(x) cuando x se acerca a a, sin importar lo que pase exactamente en a. Se escribe lím (x → a) f(x) = L.</p>
<p>Un límite existe si los límites laterales, por la izquierda y por la derecha, coinciden.</p>
<h2>Límites indeterminados 0/0</h2>
<p>Cuando al sustituir queda 0/0, se debe simplificar antes de evaluar, por ejemplo factorizando.</p>
<p><b>Ejemplo.</b> lím (x → 2) (x² − 4)/(x − 2). Al sustituir se obtiene 0/0. Como x² − 4 = (x − 2)(x + 2), se cancela (x − 2) y queda lím (x → 2) (x + 2) = 4.</p>
<h2>Límites al infinito</h2>
<p>Describen el comportamiento de la función cuando x crece sin límite. Para un cociente de polinomios se divide numerador y denominador entre la mayor potencia de x.</p>
<ul>
<li>lím (x → ∞) 1/x = 0.</li>
<li><b>Ejemplo.</b> lím (x → ∞) (3x² + 1)/(x² − 5): al dividir entre x² queda (3 + 1/x²)/(1 − 5/x²), que tiende a 3.</li>
<li>Si el grado del numerador es mayor que el del denominador, el límite no es finito.</li>
</ul>
<h2>Continuidad</h2>
<p>Una función es continua en a si el límite en a existe, la función está definida en a y ambos valores coinciden: lím (x → a) f(x) = f(a). Intuitivamente, la gráfica se puede dibujar sin levantar el lápiz.</p>
<h2>Límite notable</h2>
<p class="formula">lím (x → 0) sen(x) / x = 1</p>
<h2>Errores frecuentes</h2>
<ul>
<li>Sustituir directamente y dar por válido un resultado 0/0 sin simplificar.</li>
<li>Pensar que el límite en a depende del valor de f(a).</li>
<li>Olvidar revisar los límites laterales en funciones definidas por tramos.</li>
</ul>`,
  },
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
for (const { file, html } of DOCS) {
  const page = await browser.newPage();
  await page.setContent(`<!doctype html><html lang="es"><meta charset="utf-8"><style>${STYLE}</style><body>${html}</body></html>`);
  await page.pdf({ path: path.join(OUT, file), format: "A4", printBackground: true });
  await page.close();
  console.log("listo", file);
}
await browser.close();
