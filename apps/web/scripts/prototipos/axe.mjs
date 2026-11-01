#!/usr/bin/env node
// axe (WCAG 2.2 AA) sobre los prototipos de La Armería, en escritorio y móvil, con la escena pintada,
// con una zona abierta y con el póster. Uso: node scripts/prototipos/axe.mjs [--base URL]
//   [--rutas /prototipos/armeria-a,/prototipos/armeria-b] [--salida archivo.json]
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import AxeBuilder from '@axe-core/playwright';
import { argumentos, ESCRITORIO, esperarEscena, MOVIL, navegador, pausa, root, servidor } from './comun.mjs';

const args = argumentos({ rutas: '/prototipos/armeria-a,/prototipos/armeria-b' });
const rutas = String(args.rutas).split(',');
const { base, parar } = await servidor(args, rutas[0]);
const browser = await navegador();
const resultados = [];
try {
  for (const ruta of rutas) {
    for (const [nombre, contexto] of [
      ['escritorio', ESCRITORIO],
      ['movil', MOVIL],
    ]) {
      for (const caso of ['escena', 'zona-abierta', 'poster']) {
        const context = await browser.newContext(contexto);
        const page = await context.newPage();
        await page.goto(`${base}${ruta}?intro=0${caso === 'poster' ? '&vista=ligera' : ''}`, { waitUntil: 'load' });
        if (caso !== 'poster') await esperarEscena(page, 60_000);
        if (caso === 'zona-abierta') {
          await page.locator('.armeria__zona[href="/banco"]').click();
          await pausa(800);
        }
        await pausa(600);
        const r = await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
          .analyze();
        const fallos = r.violations.map((v) => ({ id: v.id, impacto: v.impact, nodos: v.nodes.length, ayuda: v.help }));
        resultados.push({ ruta, pantalla: nombre, caso, fallos });
        console.log(
          `${fallos.length ? '✘' : '✔'} ${ruta} · ${nombre} · ${caso}${fallos.length ? `: ${fallos.map((f) => `${f.id} (${f.nodos})`).join(', ')}` : ''}`,
        );
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
  parar();
}
if (args.salida) writeFileSync(path.resolve(root, String(args.salida)), `${JSON.stringify(resultados, null, 2)}\n`);
process.exit(resultados.some((r) => r.fallos.length) ? 1 : 0);
