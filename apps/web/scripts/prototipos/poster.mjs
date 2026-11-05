#!/usr/bin/env node
// Póster de La Armería: la composición en reposo del prototipo B (pases de Cycles) a 1920 × 1080, sin
// interfaz, sin intro, sin linterna y sin zona activa. Así el póster, la vista ligera y el B son la misma
// sala (critico-diseno, 05-11-2026: antes salía de A y parecía otra). Sale en WebP a 1920 y 960 px a
// public/prototipos/armeria/. Es el primer pintado (LCP) de A y B y la vista ligera de los dos.
// Uso: node scripts/prototipos/poster.mjs [--base http://127.0.0.1:4321] [--calidad 0.82]
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { argumentos, esperarEscena, navegador, pausa, servidor, webDir } from './comun.mjs';

const args = argumentos({ ruta: '/prototipos/armeria-b', calidad: '0.82' });
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
  // Sin la capa de interfaz: solo el lienzo del compositor.
  // (La CSP estricta impide inyectar una hoja de estilos: se oculta por el DOM.)
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('.armeria__capa')) el.style.visibility = 'hidden';
  });
  await pausa(300);
  const png = await page.locator('canvas').first().screenshot({ type: 'png' });
  const imagenes = await page.evaluate(
    async ([b64, calidad]) => {
      const img = new Image();
      img.src = `data:image/png;base64,${b64}`;
      await img.decode();
      return [1920, 960].map((ancho) => {
        const c = document.createElement('canvas');
        c.width = ancho;
        c.height = Math.round((ancho * 9) / 16);
        c.getContext('2d')?.drawImage(img, 0, 0, c.width, c.height);
        return c.toDataURL('image/webp', calidad);
      });
    },
    [png.toString('base64'), Number(args.calidad)],
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
