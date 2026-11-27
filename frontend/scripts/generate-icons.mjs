// Genera los iconos de la PWA a partir del logo de TutoMind (la «T neuronal»).
// Uso: node scripts/generate-icons.mjs   (usa el Chromium que instala Playwright)
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "public", "icons");

const GRADIENT = `<linearGradient id="g" x1="4" y1="2" x2="44" y2="46" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#8e97fd"/><stop offset="1" stop-color="#d9a5b3"/></linearGradient>`;

/** Trazos y nodos del logo, en un viewBox de 48. */
const GLYPH = `
  <g fill="none" stroke="#03174c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 18.5Q24 8 36 18.5"/><path d="M24 13.2V35"/></g>
  <g fill="#03174c"><circle cx="12" cy="18.5" r="3"/><circle cx="36" cy="18.5" r="3"/><circle cx="24" cy="36" r="3.4"/></g>
  <circle cx="24" cy="13.2" r="4" fill="#ffcf86" stroke="#03174c" stroke-width="2.2"/>`;

const SHINE = `<path d="M15 1h18a14 14 0 0 1 14 14v1C36 8 12 8 1 16v-1A14 14 0 0 1 15 1Z" fill="#fff" opacity="0.16"/>`;

/** `any`: la pieza redondeada, con transparencia en las esquinas. */
const rounded = `<rect x="1" y="1" width="46" height="46" rx="14" fill="url(#g)"/>${SHINE}${GLYPH}`;

/** Cuadrado a sangre (maskable y Apple): el sistema lo recorta; el logo queda dentro de la zona segura (80 %). */
const bleed = `<rect width="48" height="48" fill="url(#g)"/>
  <g transform="translate(24 24) scale(0.62) translate(-24 -24)">${GLYPH}</g>`;

const ICONS = [
  { file: "icon-192.png", size: 192, body: rounded, transparent: true },
  { file: "icon-512.png", size: 512, body: rounded, transparent: true },
  { file: "icon-maskable-512.png", size: 512, body: bleed, transparent: false },
  { file: "apple-touch-icon.png", size: 180, body: bleed, transparent: false },
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
for (const { file, size, body, transparent } of ICONS) {
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  await page.setContent(
    `<style>html,body{margin:0;background:transparent}svg{display:block}</style>
     <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="${size}" height="${size}"><defs>${GRADIENT}</defs>${body}</svg>`,
  );
  await page.screenshot({ path: path.join(OUT, file), omitBackground: transparent });
  await page.close();
  console.log("listo", file);
}
await browser.close();
