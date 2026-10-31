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

// Sin variables TURBO_* heredadas: TURBO_API, TURBO_TOKEN o TURBO_REMOTE_* podrían activar una caché
// remota y subir `dist/` (con copias de .dev.vars) a un servidor ajeno.
const inherited = Object.fromEntries(Object.entries(process.env).filter(([name]) => !/^TURBO_/i.test(name)));

export const quietEnv = {
  ...inherited,
  TURBO_TELEMETRY_DISABLED: '1',
  ASTRO_TELEMETRY_DISABLED: '1',
  WRANGLER_SEND_METRICS: 'false',
  DO_NOT_TRACK: '1',
};

// Argumentos admitidos desde la línea de comandos (las reglas `pnpm test *` de .claude/settings.json
// no piden permiso): solo filtrar paquetes y saltarse la caché local. Nada de --api, --token,
// --cache, --cwd, --graph ni opciones de Biome que escriban archivos.
const FILTER = /^--filter=[@\w./-]+(?:\.\.\.)?$/;
const TASKS_WITHOUT_ARGS = new Set(['lint', 'format']);

/** Devuelve los argumentos no admitidos para la tarea (lista vacía si todo es correcto). */
export function checkArgs(task, extra) {
  if (TASKS_WITHOUT_ARGS.has(task)) return [...extra];
  return extra.filter((a) => !(a === '--force' || FILTER.test(a)));
}

/**
 * Ruta del lanzador JS de un binario de node_modules (evita los .cmd de Windows), resuelto desde el
 * paquete que declara la dependencia (`from`, la raíz por defecto).
 */
export function bin(pkg, file, from = root) {
  const require = createRequire(path.join(from, 'package.json'));
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
  if (!task || !/^[a-z][a-z0-9:-]*$/.test(task)) {
    console.error('Uso: node scripts/run.mjs <tarea> [--filter=<paquete>] [--force]');
    process.exit(2);
  }
  const bad = checkArgs(task, extra);
  if (bad.length) {
    console.error(`Argumentos no admitidos: ${bad.join(' ')}`);
    console.error('Solo --filter=<paquete> y --force (lint y format no admiten ninguno).');
    process.exit(2);
  }
  process.exit(TASKS[task] ? TASKS[task](extra) : turbo(['run', task, ...extra]));
}
