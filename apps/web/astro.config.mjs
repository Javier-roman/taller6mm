// Web de Taller6mm: Astro 7 con salida `server` en Cloudflare Workers (ADR-0001 y spike S1).
// - `session: false`: las sesiones las llevará Better Auth en D1 (sin KV).
// - Imágenes en modo `compile`: sin binding de Cloudflare Images.
// - El estado local de D1 se comparte con `wrangler dev` y `pnpm db:*` en <raíz>/.wrangler/state.
import cloudflare from '@astrojs/cloudflare';
import react from '@astrojs/react';
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'server',
  adapter: cloudflare({
    imageService: 'compile',
    persistState: { path: '../../.wrangler/state' },
  }),
  integrations: [react()],
  session: false,
  security: { checkOrigin: true },
  server: { host: '127.0.0.1', port: 4321 },
});
