#!/usr/bin/env node
// Capturas de un prototipo de La Armería (Fase 1) para el informe y para critico-diseno: escritorio
// (1440 × 900) y móvil (390 × 844, DPR 3, táctil), en reposo, con la linterna y una zona activa, con
// una zona abierta, durante la intro, con la variante de luz cálida, con movimiento reducido y con el
// póster (vista ligera). Las capturas salen a escala CSS.
// Uso: node scripts/prototipos/capturas.mjs --ruta /prototipos/armeria-a --prefijo a
//      [--base http://127.0.0.1:4321] [--salida docs/informes/capturas/fase-1-propuestas]
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { argumentos, ESCRITORIO, esperarEscena, MOVIL, navegador, pausa, root, servidor } from './comun.mjs';

const args = argumentos({
  ruta: '/prototipos/armeria-a',
  prefijo: 'a',
  salida: path.join('docs', 'informes', 'capturas', 'fase-1-propuestas'),
});
const salida = path.resolve(root, String(args.salida));
mkdirSync(salida, { recursive: true });
const { base, parar } = await servidor(args, args.ruta);
const browser = await navegador();
let fallos = 0;

async function capturar(nombre, { contexto, query = '?intro=0', reducido = false, escena = true, preparar }) {
  const context = await browser.newContext({ ...contexto, reducedMotion: reducido ? 'reduce' : 'no-preference' });
  const page = await context.newPage();
  const errores = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errores.push(m.text());
  });
  page.on('pageerror', (e) => errores.push(String(e)));
  await page.goto(`${base}${args.ruta}${query}`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (escena) {
    const ok = await esperarEscena(page, 60_000);
    if (!ok) errores.push('La escena no llegó a pintar');
  } else {
    await page.waitForFunction(() => {
      const img = document.querySelector('.armeria-poster__imagen');
      return img instanceof HTMLImageElement && img.complete;
    });
  }
  await pausa(1500);
  if (preparar) await preparar(page);
  const archivo = path.join(salida, `${args.prefijo}-${nombre}.jpg`);
  // JPEG al 88 %: ~5 veces menos que PNG y sin pérdida visible en una escena con grano.
  await page.screenshot({ path: archivo, scale: 'css', type: 'jpeg', quality: 88 });
  console.log(`✔ ${path.relative(root, archivo)}${errores.length ? ` · ${errores.length} errores de consola` : ''}`);
  for (const e of errores) console.log(`   ✘ ${e}`);
  if (errores.length) fallos++;
  await context.close();
}

/** Desliza el carrusel móvil hasta la tarjeta de una zona y espera a que la cámara llegue. */
const irAZona = (id) => async (page) => {
  await page.evaluate((zona) => {
    document.querySelector(`.armeria__zona[href="/${zona}"]`)?.scrollIntoView({ inline: 'center', block: 'nearest' });
  }, id);
  await pausa(1800);
};

try {
  await capturar('escritorio-reposo', { contexto: ESCRITORIO });
  await capturar('escritorio-linterna', {
    contexto: ESCRITORIO,
    preparar: async (page) => {
      // Recorre el armero con la linterna y se queda sobre él (zona activa).
      for (let i = 0; i <= 20; i++) await page.mouse.move(150 + i * 9, 380 + i * 2);
      await pausa(1600);
    },
  });
  await capturar('escritorio-banco-abierto', {
    contexto: ESCRITORIO,
    preparar: async (page) => {
      await page.click('.armeria__zona[href="/banco"]');
      await pausa(1800);
    },
  });
  await capturar('escritorio-intro', {
    contexto: ESCRITORIO,
    query: '?intro=1',
    preparar: async () => {
      // En mitad de la intro: el primer tubo encendido y el segundo arrancando.
    },
  });
  await capturar('escritorio-luz-calida', { contexto: ESCRITORIO, query: '?intro=0&luz=taller' });
  await capturar('escritorio-reducido', { contexto: ESCRITORIO, reducido: true });
  await capturar('escritorio-poster', { contexto: ESCRITORIO, query: '?vista=ligera', escena: false });
  await capturar('movil-reposo', { contexto: MOVIL });
  await capturar('movil-banco', { contexto: MOVIL, preparar: irAZona('banco') });
  await capturar('movil-tablon-abierto', {
    contexto: MOVIL,
    preparar: async (page) => {
      await irAZona('mercado')(page);
      await page.tap('.armeria__zona[href="/mercado"]');
      await pausa(1500);
    },
  });
  await capturar('movil-reducido', { contexto: MOVIL, reducido: true, preparar: irAZona('comunidad') });
  await capturar('movil-poster', { contexto: MOVIL, query: '?vista=ligera', escena: false });
} finally {
  await browser.close();
  parar();
}
process.exit(fallos ? 1 : 0);
