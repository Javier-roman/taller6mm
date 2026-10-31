import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import {
  applySecurityHeaders,
  baseHeaders,
  CSP_DIRECTIVES,
  HEADER_ONLY_CSP,
  mergeCsp,
  NON_HTML_CSP,
  staticHeaders,
} from './security-headers.ts';

/** Lee un bloque de `_headers` (formato de Cloudflare) como objeto con nombres en minúscula. */
function parseHeadersFile(text: string, path: string): Record<string, string> {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() && !l.trim().startsWith('#'));
  const start = lines.indexOf(path);
  const out: Record<string, string> = {};
  for (const line of lines.slice(start + 1)) {
    if (!/^\s/.test(line)) break;
    const [name, ...value] = line.trim().split(':');
    out[(name ?? '').toLowerCase()] = value.join(':').trim();
  }
  return out;
}

describe('cabeceras de seguridad (docs/08 §6.2)', () => {
  test('producción: todas las cabeceras y sin noindex', () => {
    const h = baseHeaders('production');
    expect(h['strict-transport-security']).toMatch(/^max-age=\d{8,}; includeSubDomains$/);
    expect(h['x-content-type-options']).toBe('nosniff');
    expect(h['referrer-policy']).toBe('strict-origin-when-cross-origin');
    expect(h['cross-origin-opener-policy']).toBe('same-origin');
    expect(h['cross-origin-resource-policy']).toBe('same-origin');
    expect(h['x-frame-options']).toBe('DENY');
    expect(h['x-robots-tag']).toBeUndefined();
  });

  test('fuera de producción nunca se indexa', () => {
    expect(baseHeaders('preview')['x-robots-tag']).toBe('noindex, nofollow');
    expect(baseHeaders('local')['x-robots-tag']).toBe('noindex, nofollow');
  });

  test('Permissions-Policy mínima: solo los sensores de movimiento para el propio sitio', () => {
    const policy = baseHeaders('production')['permissions-policy'] ?? '';
    const allowed = policy.split(', ').filter((p) => !p.endsWith('=()'));
    expect(allowed.sort()).toEqual(['accelerometer=(self)', 'gyroscope=(self)']);
    for (const feature of ['camera', 'microphone', 'geolocation', 'payment']) expect(policy).toContain(`${feature}=()`);
  });

  test('la CSP de Astro no abre inline ni eval y no lleva directivas que una <meta> no admite', () => {
    const csp = CSP_DIRECTIVES.join('; ');
    expect(csp).not.toMatch(/unsafe-inline|unsafe-eval|\*/);
    expect(csp).not.toMatch(/frame-ancestors|report-uri|sandbox/);
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("base-uri 'none'");
  });

  test('mergeCsp añade frame-ancestors una sola vez y cierra lo que no es HTML', () => {
    expect(mergeCsp("default-src 'self'")).toBe(`default-src 'self'; ${HEADER_ONLY_CSP}`);
    expect(mergeCsp(`default-src 'self'; ${HEADER_ONLY_CSP}`)).toBe(`default-src 'self'; ${HEADER_ONLY_CSP}`);
    expect(mergeCsp("default-src 'self';")).toBe(`default-src 'self'; ${HEADER_ONLY_CSP}`);
    expect(mergeCsp(null)).toBe(NON_HTML_CSP);
  });

  test('applySecurityHeaders deja la respuesta completa', () => {
    const headers = new Headers({ 'content-security-policy': "default-src 'self'" });
    applySecurityHeaders(headers, 'preview');
    expect(headers.get('content-security-policy')).toContain(HEADER_ONLY_CSP);
    expect(headers.get('x-robots-tag')).toBe('noindex, nofollow');
    expect(headers.get('x-frame-options')).toBe('DENY');
  });

  test('public/_headers coincide con staticHeaders("production")', () => {
    const file = readFileSync(new URL('../../public/_headers', import.meta.url), 'utf8');
    expect(parseHeadersFile(file, '/*')).toEqual(staticHeaders('production'));
  });
});

describe('/.well-known/security.txt (RFC 9116)', () => {
  const text = readFileSync(new URL('../../public/.well-known/security.txt', import.meta.url), 'utf8');
  const field = (name: string) =>
    text
      .split(/\r?\n/)
      .find((l) => l.toLowerCase().startsWith(`${name.toLowerCase()}:`))
      ?.slice(name.length + 1)
      .trim();

  test('tiene Contact por https y una política', () => {
    expect(field('Contact')).toMatch(/^https:\/\//);
    expect(field('Policy')).toMatch(/^https:\/\//);
  });

  test('Expires no caduca en menos de 30 días ni pasa de un año (renovarlo antes)', () => {
    const expires = Date.parse(field('Expires') ?? '');
    const days = (expires - Date.now()) / 86_400_000;
    expect(Number.isNaN(expires)).toBe(false);
    expect(days, 'security.txt caduca en menos de 30 días: actualiza Expires').toBeGreaterThan(30);
    expect(days, 'RFC 9116 recomienda que Expires no pase de un año').toBeLessThanOrEqual(366);
  });
});

describe('integración security-headers', () => {
  test('X-Robots-Tag va dentro del único bloque /* (con dos bloques, Cloudflare aplica solo uno)', async () => {
    const { withNoIndex, ROBOTS_LINE } = await import('../../integrations/security-headers.ts');
    const file = '/_astro/*\n  Cache-Control: public\n\n/*\n  X-Frame-Options: DENY\n';
    const out = withNoIndex(file);
    expect(out.split('\n').filter((l) => l.trim() === '/*')).toHaveLength(1);
    expect(out.split('\n').indexOf(ROBOTS_LINE)).toBe(out.split('\n').indexOf('/*') + 1);
    expect(withNoIndex(out)).toBe(out);
    expect(() => withNoIndex('/_astro/*\n  Cache-Control: public\n')).toThrow();
  });
});
