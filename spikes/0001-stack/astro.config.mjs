// Spike S1 (ADR-0001). Configuración mínima que reproduce la decisión 13 del plan de la Fase 0:
// salida `server`, sin sesiones de Astro (las lleva Better Auth en D1, así no hace falta KV)
// e imágenes en modo `compile` (sin binding de Cloudflare Images).
import cloudflare from '@astrojs/cloudflare';
import react from '@astrojs/react';
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'server',
  adapter: cloudflare({ imageService: 'compile' }),
  integrations: [react()],
  session: false,
  security: { checkOrigin: true },
  server: { host: '127.0.0.1', port: 4321 },
});
