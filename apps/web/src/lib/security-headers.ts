// Cabeceras de seguridad de Taller6mm (docs/08 §6.2), en un solo sitio:
//   - el middleware las pone en las respuestas que genera el Worker (SSR, API);
//   - `public/_headers` las repite para los estáticos, que no pasan por el Worker (un test comprueba
//     que coinciden con `staticHeaders('production')`);
//   - la integración `security-headers` añade X-Robots-Tag a `_headers` fuera de producción.
// La CSP con hashes la genera Astro (`security.csp`): en SSR como cabecera y en las páginas
// prerenderizadas como <meta>. Lo que una <meta> no admite (frame-ancestors) va siempre por cabecera.

/** Directivas de la CSP que gestiona Astro (todas válidas también en <meta>). */
export const CSP_DIRECTIVES = [
  "default-src 'self'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  "manifest-src 'self'",
  "worker-src 'self'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'self'",
] as const;

/** Solo por cabecera: los navegadores la ignoran (con aviso en consola) si llega en una <meta>. */
export const HEADER_ONLY_CSP = "frame-ancestors 'none'";

/** CSP para respuestas que no son HTML (JSON, errores): no cargan nada. */
export const NON_HTML_CSP = `default-src 'none'; ${HEADER_ONLY_CSP}`;

export type Environment = 'local' | 'preview' | 'production' | (string & {});

/** Cabeceras comunes a todas las respuestas (sin la CSP de Astro). */
export function baseHeaders(environment: Environment): Record<string, string> {
  const headers: Record<string, string> = {
    // Dos años; `preload` cuando el dominio definitivo esté listo (docs/08 §6.2).
    'strict-transport-security': 'max-age=63072000; includeSubDomains',
    'x-content-type-options': 'nosniff',
    'referrer-policy': 'strict-origin-when-cross-origin',
    // Mínima: solo los sensores de movimiento para el parallax opcional de La Armería (docs/02 §3.3).
    'permissions-policy':
      'accelerometer=(self), gyroscope=(self), magnetometer=(), camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()',
    'cross-origin-opener-policy': 'same-origin',
    'cross-origin-resource-policy': 'same-origin',
    'x-frame-options': 'DENY',
  };
  // Las previews y el entorno local nunca se indexan; producción sí.
  if (environment !== 'production') headers['x-robots-tag'] = 'noindex, nofollow';
  return headers;
}

/** Cabeceras de los estáticos (`_headers`): las comunes más `frame-ancestors`. */
export function staticHeaders(environment: Environment): Record<string, string> {
  return { ...baseHeaders(environment), 'content-security-policy': HEADER_ONLY_CSP };
}

/** Añade `frame-ancestors` a la CSP de Astro o, si no hay (no es HTML), pone una CSP cerrada. */
export function mergeCsp(existing: string | null): string {
  if (!existing) return NON_HTML_CSP;
  if (/(?:^|;)\s*frame-ancestors\b/.test(existing)) return existing;
  return `${existing.replace(/;\s*$/, '')}; ${HEADER_ONLY_CSP}`;
}

/** Aplica todas las cabeceras a una respuesta del Worker (las cabeceras deben ser mutables). */
export function applySecurityHeaders(headers: Headers, environment: Environment): void {
  for (const [name, value] of Object.entries(baseHeaders(environment))) headers.set(name, value);
  headers.set('content-security-policy', mergeCsp(headers.get('content-security-policy')));
}

/** Bloque de `_headers` (formato de Cloudflare) para la ruta indicada. */
export function toHeadersFile(path: string, headers: Record<string, string>): string {
  const lines = Object.entries(headers).map(([name, value]) => `  ${canonical(name)}: ${value}`);
  return `${path}\n${lines.join('\n')}\n`;
}

const canonical = (name: string) =>
  name
    .split('-')
    .map((part) => (part === 'x' ? 'X' : part.charAt(0).toUpperCase() + part.slice(1)))
    .join('-');
