#!/usr/bin/env node
// Hornea los pases del prototipo B (2,5D re-iluminable) desde la sala del prototipo A: un pase por
// grupo de luz (base, tres filas de tubos, cálidas y rótulos), más albedo, normales y profundidad,
// a 1920 × 1080 en WebP, en public/prototipos/armeria-b/. Los pases de luz se suman en el shader.
// Sustituye a Blender (no instalado: pide permisos de administrador) con el rasterizador de three.js.
// Uso: node scripts/prototipos/hornear-b.mjs [--base http://127.0.0.1:4321]
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { argumentos, navegador, pausa, servidor, webDir } from './comun.mjs';

const PASES = [
  ['base', 0.86],
  ['tubo-izquierda', 0.86],
  ['tubo-centro', 0.86],
  ['tubo-derecha', 0.86],
  ['calidas', 0.86],
  ['rotulos', 0.86],
  ['albedo', 0.86],
  // Datos: más calidad, el shader los usa para la linterna y el parallax.
  ['normal', 0.92],
  ['profundidad', 0.92],
];

const args = argumentos({ ruta: '/prototipos/hornear' });
const destino = path.join(webDir, 'public', 'prototipos', 'armeria-b');
mkdirSync(destino, { recursive: true });
const { base, parar } = await servidor(args, args.ruta);
const browser = await navegador();
let total = 0;
try {
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errores = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errores.push(m.text());
  });
  await page.goto(`${base}${args.ruta}`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__horno?.listo === true, null, { timeout: 60_000 });
  await pausa(1500);
  for (const [pase, calidad] of PASES) {
    const url = await page.evaluate(([p, q]) => window.__horno.pase(p, q), [pase, calidad]);
    const datos = Buffer.from(url.replace(/^data:image\/webp;base64,/, ''), 'base64');
    writeFileSync(path.join(destino, `${pase}.webp`), datos);
    total += datos.length;
    console.log(`✔ ${pase}.webp · ${Math.round(datos.length / 1024)} KB`);
  }
  console.log(`Total: ${Math.round(total / 1024)} KB`);
  for (const e of errores) console.log(`   ✘ ${e}`);
  await context.close();
} finally {
  await browser.close();
  parar();
}
