#!/usr/bin/env node
// Póster de La Armería: render de la escena del prototipo A a 1920 × 1080 (el encuadre fijo 16:9 de
// camara.ts) en reposo, sin intro, sin linterna y sin zona activa. Sale en WebP a 1920 y 960 px a
// public/prototipos/armeria/. Es el primer pintado (LCP) de A y B y la vista ligera de los dos.
// Uso: node scripts/prototipos/poster.mjs [--base http://127.0.0.1:4321] [--calidad 0.82]
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { argumentos, esperarEscena, navegador, pausa, servidor, webDir } from './comun.mjs';

const args = argumentos({ ruta: '/prototipos/armeria-a', calidad: '0.82' });
const destino = path.join(webDir, 'public', 'prototipos', 'armeria');
mkdirSync(destino, { recursive: true });
const { base, parar } = await servidor(args, args.ruta);
const browser = await navegador();
try {
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  await page.goto(`${base}${args.ruta}?intro=0&medir&calidad=alta`, { waitUntil: 'load' });
  if (!(await esperarEscena(page, 60_000))) throw new Error('La escena no llegó a pintar');
  // Que las luces lleguen al reposo y las sombras se asienten.
  await pausa(3500);
  const imagenes = await page.evaluate(
    (calidad) => window.__armeria.capturar([1920, 960], Number(calidad)),
    args.calidad,
  );
  for (const [i, ancho] of [1920, 960].entries()) {
    const datos = imagenes[i].replace(/^data:image\/webp;base64,/, '');
    const archivo = path.join(destino, `poster-${ancho}.webp`);
    writeFileSync(archivo, Buffer.from(datos, 'base64'));
    console.log(`✔ ${path.relative(webDir, archivo)} · ${Math.round(Buffer.byteLength(datos, 'base64') / 1024)} KB`);
  }
  await context.close();
} finally {
  await browser.close();
  parar();
}
