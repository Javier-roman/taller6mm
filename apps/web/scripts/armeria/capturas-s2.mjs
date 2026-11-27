#!/usr/bin/env node
// Capturas de La Armería a 1440 px (el móvil está aparcado) contra un servidor ya en marcha
// (`astro dev` o la build en workerd). Salida: docs/informes/capturas/fase-1-s2/.
// Uso: node scripts/armeria/capturas-s2.mjs <base-url> <prefijo> [--luz mas-luz] [--reducido] [--abrir <zona>]
//        [--tecla Tab,ArrowRight,Enter] [--zoom 2] [--ancho 1440] [--alto 900] [--completa]
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const salida = path.resolve(aqui, '..', '..', '..', '..', 'docs', 'informes', 'capturas', 'fase-1-s2');
const args = process.argv.slice(2);
const [base, prefijo] = args;
const opcion = (nombre) => {
  const i = args.indexOf(`--${nombre}`);
  return i === -1 ? null : (args[i + 1] ?? true);
};
const bandera = (nombre) => args.includes(`--${nombre}`);

const ancho = Number(opcion('ancho') ?? 1440);
const alto = Number(opcion('alto') ?? 900);
const luz = opcion('luz') ?? 'penumbra';
const abrir = opcion('abrir');
const teclas = (opcion('tecla') ?? '').split(',').filter(Boolean);
const zoom = Number(opcion('zoom') ?? 1);

mkdirSync(salida, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: ancho, height: alto },
  deviceScaleFactor: zoom,
  reducedMotion: bandera('reducido') ? 'reduce' : 'no-preference',
  colorScheme: 'dark',
});
const page = await context.newPage();
const errores = [];
page.on('console', (m) => m.type() === 'error' && errores.push(m.text()));
page.on('pageerror', (e) => errores.push(e.message));
await page.goto(`${base}/?luz=${luz}`, { waitUntil: 'networkidle' });
await page.waitForSelector('.armeria[data-hidratado="true"]');
await page.evaluate(() => document.fonts.ready);
// La barra de herramientas de `astro dev` (solo en desarrollo) tapa la navegación y no es parte de la página.
await page.addStyleTag({ content: 'astro-dev-toolbar { display: none !important; }' });
if (abrir) {
  await page.locator(`.armeria__nav a[href="/${abrir}"]`).click();
  await page.waitForSelector('[role="dialog"]');
}
for (const t of teclas) await page.keyboard.press(t);
await page.mouse.move(ancho - 4, 4);
await page.waitForTimeout(700);
const archivo = path.join(salida, `${prefijo}.png`);
await page.screenshot({ path: archivo, fullPage: bandera('completa') });
console.log(archivo, errores.length ? `ERRORES: ${errores.join(' | ')}` : 'sin errores de consola');
await browser.close();
