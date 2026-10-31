// Punto de entrada del Worker `web` (wrangler.jsonc → main): el handler del adaptador de Astro más
// las cabeceras de seguridad en TODAS las respuestas. Va aquí y no en un middleware porque Astro
// genera algunas respuestas fuera de los middlewares: el 403 de checkOrigin, los 500 por excepción
// y los 404 con página de error prerenderizada (revisión de seguridad de S4, hallazgo B1).
// Los estáticos no pasan por aquí: llevan las mismas cabeceras por `public/_headers`.
import { handle } from '@astrojs/cloudflare/handler';
import { applySecurityHeaders } from './lib/security-headers';

const internalError = () =>
  new Response('Error interno. Inténtalo de nuevo en unos minutos.', {
    status: 500,
    headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' },
  });

export default {
  async fetch(request, env, ctx) {
    let response: Response;
    try {
      response = await handle(request, env, ctx);
    } catch (error) {
      // Sin detalles en la respuesta ni datos personales en el log (docs/08 §6.3).
      console.error('web: excepción no controlada', error instanceof Error ? error.name : typeof error);
      response = internalError();
    }
    // Un WebSocket aceptado (101) no admite cambiar la respuesta.
    if (response.status === 101) return response;
    const secured = new Response(response.body, response);
    applySecurityHeaders(secured.headers, env.ENVIRONMENT);
    return secured;
  },
} satisfies ExportedHandler<Env>;
