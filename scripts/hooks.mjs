#!/usr/bin/env node
// Script `prepare` de la raíz: instala los hooks de git de lefthook (pre-commit con gitleaks y Biome).
// Lo hacemos aquí y no con el postinstall del paquete lefthook, que está bloqueado por `allowBuilds`:
// así ningún script de un tercero se ejecuta al instalar. Nunca hace fallar `pnpm install`.
import { existsSync } from 'node:fs';
import path from 'node:path';
import { bin, node, root } from './run.mjs';

if (process.env.CI) process.exit(0); // en CI no hacen falta hooks
if (!existsSync(path.join(root, '.git'))) process.exit(0); // tarball o copia sin git

try {
  const code = node(bin('lefthook', 'bin/index.js'), ['install']);
  if (code !== 0) console.warn('⚠ No se pudieron instalar los hooks de git: ejecuta `pnpm exec lefthook install`.');
} catch {
  console.warn('⚠ lefthook no está disponible: ejecuta `pnpm install` de nuevo o `pnpm exec lefthook install`.');
}
