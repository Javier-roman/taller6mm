import { defineConfig } from 'drizzle-kit';

// Genera el SQL de la base `busqueda`; se aplica con `wrangler d1 migrations apply` (pnpm db:migrate:local).
export default defineConfig({
  dialect: 'sqlite',
  schema: './src/busqueda.ts',
  out: './migrations/busqueda',
});
