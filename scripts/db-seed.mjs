#!/usr/bin/env node
// Genera las semillas SQL del catálogo (is_demo) en packages/db/seeds/<base>/0001_catalogo.sql a partir
// de catalogo/*.json, validando con Zod. Las usa `node scripts/db.mjs seed`. Los .sql no se versionan.
//   node scripts/db-seed.mjs
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { buildCoreSeed, buildSearchSeed } from '../packages/db/src/seed/build.ts';
import { loadCatalog } from '../packages/db/src/seed/load.ts';
import { root } from './run.mjs';

export function generateSeeds() {
  const raw = loadCatalog(path.join(root, 'catalogo'));
  const outputs = [
    ['core', buildCoreSeed(raw)],
    ['busqueda', buildSearchSeed(raw)],
  ];
  for (const [base, seed] of outputs) {
    const dir = path.join(root, 'packages', 'db', 'seeds', base);
    mkdirSync(dir, { recursive: true });
    const header = `-- Generado por scripts/db-seed.mjs desde catalogo/*.json. Todo is_demo = 1. No editar ni versionar.\n`;
    writeFileSync(path.join(dir, '0001_catalogo.sql'), `${header}${seed.statements.join(';\n')};\n`);
    console.log(`Semilla ${base}:`, JSON.stringify(seed.report));
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.join(root, 'scripts', 'db-seed.mjs')) generateSeeds();
