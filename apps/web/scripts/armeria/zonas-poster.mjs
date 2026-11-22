#!/usr/bin/env node
// Genera src/components/armeria/zonas-poster.css: la posición de cada zona clicable sobre el póster (y sobre
// los pases del nivel B), calculada con la misma proyección que la cámara. Va en CSS y no en atributos
// `style` porque la CSP no admite estilos en línea. Uso: pnpm --filter @taller6mm/web zonas:css
// (Node 26 ejecuta TypeScript sin compilar: solo usa camara.ts y zonas.ts, que no llevan JSX.)
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ASPECTO_POSTER, ENCUADRE_POSTER, rectZona } from '../../src/components/armeria/camara.ts';
import { ZONAS } from '../../src/components/armeria/zonas.ts';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const destino = path.resolve(aqui, '../../src/components/armeria/zonas-poster.css');
const pc = (n) => `${(n * 100).toFixed(3)}%`;

const reglas = ZONAS.map((zona) => {
  const r = rectZona(zona, ENCUADRE_POSTER, ASPECTO_POSTER);
  return `.armeria-poster__zona[data-zona="${zona.id}"] {\n  left: ${pc(r.x)};\n  top: ${pc(r.y)};\n  width: ${pc(r.ancho)};\n  height: ${pc(r.alto)};\n}`;
});

writeFileSync(
  destino,
  `/* GENERADO por scripts/armeria/zonas-poster.mjs: no editar a mano (lo comprueba un test). */\n${reglas.join('\n\n')}\n`,
);
console.log(`✔ ${path.relative(process.cwd(), destino)}`);
