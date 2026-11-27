// Tests de migraciones dentro de workerd (el runtime de Cloudflare) con D1 en memoria.
import path from 'node:path';
import { cloudflareTest, readD1Migrations } from '@cloudflare/vitest-pool-workers';
import { defineConfig } from 'vitest/config';
import { buildCoreSeed, buildSearchSeed } from './src/seed/build.ts';
import { loadCatalog } from './src/seed/load.ts';

const migrations = path.join(import.meta.dirname, 'migrations');
// Semillas del catálogo, construidas en Node (los tests corren en workerd y no leen disco).
const catalog = loadCatalog(path.join(import.meta.dirname, '..', '..', 'catalogo'));

export default defineConfig(async () => ({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: './wrangler.jsonc' },
      miniflare: {
        bindings: {
          CORE_MIGRATIONS: await readD1Migrations(path.join(migrations, 'core')),
          MERCADO_MIGRATIONS: await readD1Migrations(path.join(migrations, 'mercado')),
          BUSQUEDA_MIGRATIONS: await readD1Migrations(path.join(migrations, 'busqueda')),
          CORE_SEED: buildCoreSeed(catalog).statements,
          BUSQUEDA_SEED: buildSearchSeed(catalog).statements,
        },
      },
    }),
  ],
  test: { include: ['test/**/*.test.ts'] },
}));
