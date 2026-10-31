// Tests de migraciones dentro de workerd (el runtime de Cloudflare) con D1 en memoria.
import path from 'node:path';
import { cloudflareTest, readD1Migrations } from '@cloudflare/vitest-pool-workers';
import { defineConfig } from 'vitest/config';

const migrations = path.join(import.meta.dirname, 'migrations');

export default defineConfig(async () => ({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: './wrangler.jsonc' },
      miniflare: {
        bindings: {
          CORE_MIGRATIONS: await readD1Migrations(path.join(migrations, 'core')),
          MERCADO_MIGRATIONS: await readD1Migrations(path.join(migrations, 'mercado')),
          BUSQUEDA_MIGRATIONS: await readD1Migrations(path.join(migrations, 'busqueda')),
        },
      },
    }),
  ],
  test: { include: ['test/**/*.test.ts'] },
}));
