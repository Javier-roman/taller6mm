#!/usr/bin/env node
// Bases D1 locales (core, mercado y busqueda), compartidas por `astro dev`, `wrangler dev` y los e2e
// en <raíz>/.wrangler/state. Solo local: lo remoto se hace a mano y con permiso (CLAUDE.md).
//   node scripts/db.mjs migrate   → aplica las migraciones de packages/db/migrations/<base>
//   node scripts/db.mjs seed      → aplica packages/db/seeds/<base>/*.sql (datos is_demo)
//   node scripts/db.mjs reset     → borra el estado local de D1, migra y siembra
import { existsSync, readdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { bin, node, root } from './run.mjs';

const BASES = [
  ['core', 'CORE'],
  ['mercado', 'MERCADO'],
  ['busqueda', 'BUSQUEDA'],
];
export const persistTo = path.join(root, '.wrangler', 'state');
const webDir = path.join(root, 'apps', 'web');
const wrangler = (args) =>
  node(bin('wrangler', 'bin/wrangler.js', webDir), [...args, '--local', '--persist-to', persistTo], {
    cwd: webDir,
    env: { ...process.env, CI: 'true', WRANGLER_SEND_METRICS: 'false' },
  });

export function migrate() {
  for (const [base, binding] of BASES) {
    console.log(`\n▶ Migraciones de ${base}`);
    if (wrangler(['d1', 'migrations', 'apply', binding]) !== 0) return 1;
  }
  return 0;
}

export function seed() {
  let applied = 0;
  for (const [base, binding] of BASES) {
    const dir = path.join(root, 'packages', 'db', 'seeds', base);
    if (!existsSync(dir)) continue;
    for (const file of readdirSync(dir)
      .filter((f) => f.endsWith('.sql'))
      .sort()) {
      console.log(`\n▶ Semilla ${base}/${file}`);
      if (wrangler(['d1', 'execute', binding, '--file', path.join(dir, file)]) !== 0) return 1;
      applied++;
    }
  }
  if (applied === 0) console.log('No hay semillas todavía: el catálogo de demostración (is_demo) llega en la Fase 2.');
  return 0;
}

export function reset() {
  const d1State = path.join(persistTo, 'v3', 'd1');
  console.log(`Borrando el estado local de D1 en ${path.relative(root, d1State)}`);
  rmSync(d1State, { recursive: true, force: true });
  return migrate() || seed();
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.join(root, 'scripts', 'db.mjs')) {
  const commands = { migrate, seed, reset };
  const command = commands[process.argv[2]];
  if (!command) {
    console.error('Uso: node scripts/db.mjs <migrate|seed|reset>');
    process.exit(2);
  }
  process.exit(command());
}
