#!/usr/bin/env node
// Hornea los pases de DATOS del nivel B con el rasterizador de three.js (albedo, normales y profundidad) a
// 2560 × 1440 en WebP, en assets-src/vistas/armeria/. Los usa la linterna (sobre normales y albedo) y el
// parallax (profundidad). Los pases de luz salen de Cycles (hornear-cycles.mjs).
// Uso: node scripts/armeria/hornear-datos.mjs
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { carpetaVistas, navegador, pausa, servidorHorno } from './comun.mjs';

// Datos: más calidad (el shader los lee tal cual); el albedo es color y aguanta menos.
const PASES = [
  ['albedo', 0.86],
  ['normal', 0.92],
  ['profundidad', 0.92],
];

mkdirSync(carpetaVistas, { recursive: true });
const { base, parar } = await servidorHorno();
const browser = await navegador();
let total = 0;
try {
  const context = await browser.newContext({ viewport: { width: 2560, height: 1440 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errores = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errores.push(m.text());
  });
  await page.goto(`${base}/horno.html`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__horno?.listo === true, null, { timeout: 90_000 });
  // Sin las fuentes de los rótulos, el horneado sale con una sans genérica: mejor fallar.
  const fuentes = await page.evaluate(() =>
    ['700 64px "IBM Plex Sans Condensed"', '500 32px "IBM Plex Mono"', '600 32px "IBM Plex Mono"'].map((f) => [
      f,
      document.fonts.check(f),
    ]),
  );
  const faltan = fuentes.filter(([, ok]) => !ok).map(([f]) => f);
  if (faltan.length) throw new Error(`Fuentes sin cargar: ${faltan.join(', ')}`);
  await pausa(1500);
  for (const [pase, calidad] of PASES) {
    const url = await page.evaluate(([p, q]) => window.__horno.pase(p, q), [pase, calidad]);
    const datos = Buffer.from(url.replace(/^data:image\/webp;base64,/, ''), 'base64');
    writeFileSync(path.join(carpetaVistas, `${pase}.webp`), datos);
    total += datos.length;
    console.log(`✔ ${pase}.webp · ${Math.round(datos.length / 1024)} KB`);
  }
  console.log(`Total: ${Math.round(total / 1024)} KB`);
  for (const e of errores) console.log(`   ✘ ${e}`);
  await context.close();
} finally {
  await browser.close();
  await parar();
}
