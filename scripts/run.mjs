#!/usr/bin/env node
// Ejecuta una tarea del monorepo de forma multiplataforma (Windows, macOS y Linux), sin shell.
//   node scripts/run.mjs <tarea> [argumentos para turbo]
// Desactiva la telemetría de Turborepo, Astro y Wrangler (privacidad por diseño, docs/08 §6.3).
// `lint` y `format` corren Biome sobre todo el repo de una vez; el resto, Turborepo por paquete.
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'package.json'));

export const quietEnv = {
  ...process.env,
  TURBO_TELEMETRY_DISABLED: '1',
  ASTRO_TELEMETRY_DISABLED: '1',
  WRANGLER_SEND_METRICS: 'false',
  DO_NOT_TRACK: '1',
};

/** Ruta del lanzador JS de un binario de node_modules (evita los .cmd de Windows). */
export function bin(pkg, file) {
  return path.join(path.dirname(require.resolve(`${pkg}/package.json`)), file);
}

/** Lanza `node <script> ...args` y devuelve el código de salida. */
export function node(script, args, opts = {}) {
  const r = spawnSync(process.execPath, [script, ...args], { cwd: root, stdio: 'inherit', env: quietEnv, ...opts });
  if (r.error) throw r.error;
  return r.status ?? 1;
}

export const biome = (args) => node(bin('@biomejs/biome', 'bin/biome'), args);
export const turbo = (args) => node(bin('turbo', 'bin/turbo'), args);

const TASKS = {
  lint: (extra) => biome(['ci', '.', ...extra]),
  format: (extra) => biome(['check', '--write', '.', ...extra]),
};

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [task, ...extra] = process.argv.slice(2);
  if (!task) {
    console.error('Uso: node scripts/run.mjs <tarea> [argumentos]');
    process.exit(2);
  }
  process.exit(TASKS[task] ? TASKS[task](extra) : turbo(['run', task, ...extra]));
}
