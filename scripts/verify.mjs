#!/usr/bin/env node
// `pnpm verify`: la puerta de calidad local y de CI, en este orden y parando en el primer fallo:
//   1. Biome (lint + formato) sobre todo el repo
//   2. Typecheck, tests y build de cada paquete (Turborepo, en paralelo y con caché)
//   3. Tests de la configuración de Claude Code (hooks y lanzador del MCP)
// Multiplataforma: solo Node, sin sintaxis de shell.
import path from 'node:path';
import { biome, node, root, turbo } from './run.mjs';

const steps = [
  ['Biome (lint y formato)', () => biome(['ci', '.'])],
  ['Typecheck, tests y build', () => turbo(['run', 'typecheck', 'test', 'build'])],
  [
    'Tests de .claude (hooks y MCP)',
    () => node('--test', [path.posix.join('.claude', '**', '*.test.mjs')], { cwd: root }),
  ],
];

for (const [name, run] of steps) {
  console.log(`\n▶ ${name}`);
  const t0 = Date.now();
  const code = run();
  if (code !== 0) {
    console.error(`\n✘ ${name} falló (código ${code}).`);
    process.exit(code);
  }
  console.log(`✔ ${name} (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
}
console.log('\n✔ verify en verde');
