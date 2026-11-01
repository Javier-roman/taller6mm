// Web de Taller6mm: Astro 7 con salida `server` en Cloudflare Workers (ADR-0001 y spike S1).
// - `session: false`: las sesiones las llevará Better Auth en D1 (sin KV).
// - Imágenes en modo `compile`: sin binding de Cloudflare Images.
// - El estado local de D1 se comparte con `wrangler dev` y `pnpm db:*` en <raíz>/.wrangler/state.
// - Seguridad (docs/08 §6.2): CSP de Astro con hashes, comprobación de origen en las mutaciones y
//   cabeceras en src/worker.ts y public/_headers (fuente única: src/lib/security-headers.ts).
import cloudflare from '@astrojs/cloudflare';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';
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
  // Páginas prerenderizadas como `sistema.html`, sin barra final: Cloudflare sirve /sistema con 200 en
  // vez de redirigir a /sistema/ (una ida y vuelta menos; auditor-rendimiento, S5).
  build: { format: 'file' },
  trailingSlash: 'never',
  security: {
    checkOrigin: true,
    csp: { algorithm: 'SHA-256', directives: [...CSP_DIRECTIVES] },
  },
  server: { host: '127.0.0.1', port: 4321 },
  // Tailwind v4 sobre los tokens de @taller6mm/ui (src/styles/global.css).
  vite: {
    plugins: [tailwindcss()],
    // Vite incrusta en base64 los archivos de < 4 KB, incluidos subconjuntos pequeños de Fontsource.
    // La CSP solo admite `font-src 'self'`, así que las fuentes nunca se incrustan (sin `data:` en la CSP).
    build: { assetsInlineLimit: (file) => (/\.(?:woff2?|ttf|otf)$/i.test(file) ? false : undefined) },
  },
});
