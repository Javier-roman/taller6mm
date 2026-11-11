#!/usr/bin/env node
// Recortes del prototipo B para el móvil (recortes.ts), después de hornearlos (hornear-b-cycles.mjs --conjunto):
// 1. Variante reducida de cada pase (-2x, a 2/3): la que piden los móviles de 2× o menos, como un srcset.
// 2. Póster de cada conjunto (public/prototipos/armeria/movil/<conjunto>.webp y -2x): la composición en
//    reposo del propio compositor del B, para que el póster y la escena del móvil sean la misma imagen.
// Uso: node scripts/prototipos/recortes-movil.mjs [--base http://127.0.0.1:4321] [--calidad 0.86]
//      [--solo variantes|posteres]
// Los pósteres necesitan la build servida con los pases ya horneados (y sus variantes).
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import {
  CONJUNTOS_MOVIL,
  PASES_RECORTE,
  paseHorneado,
  VARIANTES_RECORTE,
} from '../../src/components/armeria/recortes.ts';
import { argumentos, esperarEscena, MOVIL, navegador, pausa, servidor, webDir } from './comun.mjs';

const args = argumentos({ ruta: '/prototipos/armeria-b', calidad: '0.86' });
const pases = path.join(webDir, 'public', 'prototipos', 'armeria-b', 'movil');
const posteres = path.join(webDir, 'public', 'prototipos', 'armeria', 'movil');
const kb = (archivo) => `${Math.round(statSync(archivo).size / 1024)} KB`;
const guardar = (archivo, url) => {
  writeFileSync(archivo, Buffer.from(url.replace(/^data:image\/webp;base64,/, ''), 'base64'));
  console.log(`✔ ${path.relative(webDir, archivo)} · ${kb(archivo)}`);
};
const reducidas = VARIANTES_RECORTE.filter((v) => v.escala < 1);
const browser = await navegador();
let parar = () => undefined;
try {
  if (args.solo !== 'posteres') {
    const page = await (await browser.newContext()).newPage();
    for (const conjunto of CONJUNTOS_MOVIL) {
      for (const pase of PASES_RECORTE) {
        const nombre = paseHorneado(conjunto, pase);
        const origen = nombre ? path.join(pases, conjunto.id, `${nombre}.webp`) : null;
        if (!origen || !existsSync(origen)) continue;
        for (const { sufijo, escala } of reducidas) {
          const url = await page.evaluate(
            async ([b64, factor, calidad]) => {
              const img = new Image();
              img.src = `data:image/webp;base64,${b64}`;
              await img.decode();
              const c = document.createElement('canvas');
              c.width = Math.round(img.naturalWidth * factor);
              c.height = Math.round(img.naturalHeight * factor);
              const ctx = c.getContext('2d');
              ctx.imageSmoothingQuality = 'high';
              ctx.drawImage(img, 0, 0, c.width, c.height);
              return c.toDataURL('image/webp', calidad);
            },
            [readFileSync(origen).toString('base64'), escala, Number(args.calidad)],
          );
          guardar(path.join(pases, conjunto.id, `${nombre}${sufijo}.webp`), url);
        }
      }
    }
  }
  if (args.solo !== 'variantes') {
    mkdirSync(posteres, { recursive: true });
    const s = await servidor(args, args.ruta);
    parar = s.parar;
    // El móvil de las capturas (390 × 844 a 3×) pide los pases enteros.
    const page = await (await browser.newContext(MOVIL)).newPage();
    await page.goto(`${s.base}${args.ruta}?intro=0&medir`, { waitUntil: 'load' });
    if (!(await esperarEscena(page, 90_000))) throw new Error('La escena no llegó a pintar');
    await pausa(2500);
    for (const conjunto of CONJUNTOS_MOVIL) {
      const salidas = await page.evaluate((id) => window.__armeria.componer(id), conjunto.id);
      if (!salidas) {
        console.log(`✘ ${conjunto.id}: sin recorte (¿falta hornearlo?)`);
        process.exitCode = 1;
        continue;
      }
      for (const { sufijo, url } of salidas) guardar(path.join(posteres, `${conjunto.id}${sufijo}.webp`), url);
    }
  }
} finally {
  await browser.close();
  parar();
}
