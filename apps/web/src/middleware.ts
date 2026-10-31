// Cabeceras de seguridad en todas las respuestas que genera el Worker (docs/08 §6.2).
// Los estáticos no pasan por aquí: llevan las mismas cabeceras por `public/_headers`.
import { defineMiddleware } from 'astro:middleware';
import { env } from 'cloudflare:workers';
import { applySecurityHeaders } from './lib/security-headers';

export const onRequest = defineMiddleware(async (_context, next) => {
  const response = await next();
  try {
    applySecurityHeaders(response.headers, env.ENVIRONMENT);
    return response;
  } catch {
    // Algunas respuestas (p. ej. las que vienen de `fetch`) tienen cabeceras inmutables: se copian.
    const copy = new Response(response.body, response);
    applySecurityHeaders(copy.headers, env.ENVIRONMENT);
    return copy;
  }
});
