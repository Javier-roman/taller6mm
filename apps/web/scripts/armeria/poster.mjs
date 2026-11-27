#!/usr/bin/env node
// Póster de La Armería: la composición en reposo de los pases de Cycles (compositor del nivel B) a 1920 × 1080
// y 960 px, sin interfaz, sin intro, sin linterna y sin zona activa: póster, vista ligera y nivel B son la misma
// sala. Sale en WebP a assets-src/vistas/armeria/ en penumbra (poster-*.webp) y en «Más luz» (poster-mas-luz-*.webp).
// Es el primer pintado (LCP) y la vista ligera. Uso: node scripts/armeria/poster.mjs [--calidad 0.82]
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { argumentos, carpetaVistas, navegador, servidorHorno } from './comun.mjs';

const args = argumentos({ calidad: '0.9' });
mkdirSync(carpetaVistas, { recursive: true });
const { base, parar } = await servidorHorno();
const browser = await navegador();
try {
  const context = await browser.newContext({ viewport: { width: 2560, height: 1440 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errores = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errores.push(m.text());
  });
  page.on('pageerror', (e) => errores.push(e.message));
  await page.goto(`${base}/poster.html`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__poster?.listo === true, null, { timeout: 60_000 });
  for (const [luz, nombre] of [
    ['penumbra', 'poster'],
    ['mas-luz', 'poster-mas-luz'],
  ]) {
    const salidas = await page.evaluate(([l, q]) => window.__poster.componer(l, q), [luz, Number(args.calidad)]);
    for (const { ancho, base64 } of salidas) {
      const datos = Buffer.from(base64, 'base64');
      writeFileSync(path.join(carpetaVistas, `${nombre}-${ancho}.webp`), datos);
      console.log(`✔ ${nombre}-${ancho}.webp · ${Math.round(datos.length / 1024)} KB`);
    }
  }
  for (const e of errores) console.log(`   ✘ ${e}`);
  await context.close();
} finally {
  await browser.close();
  await parar();
}
