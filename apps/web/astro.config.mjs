// Web de Taller6mm: Astro 7 con salida `server` en Cloudflare Workers (ADR-0001 y spike S1).
// - `session: false`: las sesiones las llevará Better Auth en D1 (sin KV).
// - Imágenes en modo `compile`: sin binding de Cloudflare Images.
// - El estado local de D1 se comparte con `wrangler dev` y `pnpm db:*` en <raíz>/.wrangler/state.
// - Seguridad (docs/08 §6.2): CSP de Astro con hashes, comprobación de origen en las mutaciones y
//   cabeceras en src/worker.ts y public/_headers (fuente única: src/lib/security-headers.ts).
import cloudflare from '@astrojs/cloudflare';
import react from '@astrojs/react';
import { defineConfig } from 'astro/config';
import securityHeaders from './integrations/security-headers.ts';
import { CSP_DIRECTIVES } from './src/lib/security-headers.ts';

export default defineConfig({
  output: 'server',
  adapter: cloudflare({
    imageService: 'compile',
    persistState: { path: '../../.wrangler/state' },
  }),
  integrations: [react(), securityHeaders()],
  session: false,
  security: {
    checkOrigin: true,
    csp: { algorithm: 'SHA-256', directives: [...CSP_DIRECTIVES] },
  },
  server: { host: '127.0.0.1', port: 4321 },
});
