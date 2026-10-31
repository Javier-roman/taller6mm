#!/usr/bin/env node
// Tests del pipeline de Python (apps/pipeline) desde Turborepo: uv sync + ruff + pytest.
// Si `uv` no está instalado, se salta con un aviso, salvo en CI, donde falla: el job `verify`
// (Ubuntu y Windows) instala uv y lo ejecuta siempre. Multiplataforma: sin shell.
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { quietEnv, root } from './run.mjs';

const cwd = path.join(root, 'apps', 'pipeline');
const uv = (args) => spawnSync('uv', args, { cwd, stdio: 'inherit', env: quietEnv });

const probe = spawnSync('uv', ['--version'], { cwd, encoding: 'utf8' });
if (probe.error || probe.status !== 0) {
  if (process.env.CI) {
    console.error('✘ uv no está instalado en CI.');
    process.exit(1);
  }
  console.warn(
    '⚠ uv no está instalado: se saltan los tests de apps/pipeline (corren en CI). Windows: winget install --id astral-sh.uv --exact',
  );
  process.exit(0);
}

for (const args of [
  ['sync', '--frozen'],
  ['run', 'ruff', 'check'],
  ['run', 'ruff', 'format', '--check'],
  ['run', 'pytest'],
]) {
  const r = uv(args);
  if (r.status !== 0) process.exit(r.status ?? 1);
}
