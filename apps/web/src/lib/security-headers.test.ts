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
    expect(mergeCsp(null, 'application/json')).toBe(NON_HTML_CSP);
    expect(mergeCsp(null, 'text/plain;charset=UTF-8')).toBe(NON_HTML_CSP);
  });

  test('HTML sin CSP en cabecera (trae su <meta>): solo frame-ancestors, para no intersecar', () => {
    expect(mergeCsp(null, 'text/html; charset=utf-8')).toBe(HEADER_ONLY_CSP);
    expect(mergeCsp(null, 'TEXT/HTML')).toBe(HEADER_ONLY_CSP);
  });

  test('applySecurityHeaders deja la respuesta completa', () => {
    const headers = new Headers({ 'content-security-policy': "default-src 'self'" });
    applySecurityHeaders(headers, 'preview');
    expect(headers.get('content-security-policy')).toContain(HEADER_ONLY_CSP);
    expect(headers.get('x-robots-tag')).toBe('noindex, nofollow');
    expect(headers.get('x-frame-options')).toBe('DENY');
  });

  test('public/_headers coincide con staticHeaders("production") y tiene un único bloque /*', () => {
    const file = readFileSync(new URL('../../public/_headers', import.meta.url), 'utf8');
    // Wrangler indexa las reglas por ruta: un segundo bloque /* anularía el primero.
    expect(file.split(/\r?\n/).filter((l) => l.trim() === '/*')).toHaveLength(1);
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

  test('Expires aparece una vez, en RFC 3339 (UTC), sin caducar y a menos de un año', () => {
    const lines = text.split(/\r?\n/).filter((l) => /^expires:/i.test(l));
    expect(lines).toHaveLength(1);
    const value = field('Expires') ?? '';
    expect(value).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/);
    const days = (Date.parse(value) - Date.now()) / 86_400_000;
    // Caducado, el archivo deja de ser válido (RFC 9116 §2.5.5): ese fallo es legítimo.
    expect(days, 'security.txt ha caducado: actualiza Expires').toBeGreaterThan(0);
    expect(days, 'RFC 9116 recomienda que Expires no pase de un año').toBeLessThanOrEqual(366);
    // Aviso (no fallo) para no bloquear PR urgentes el último mes.
    if (days < 30) console.warn(`security.txt caduca en ${Math.floor(days)} días: renueva Expires.`);
  });
});

describe('integración security-headers', () => {
  test('el entorno sale del wrangler.json de la build; si falta o no se entiende, «desconocido»', async () => {
    const { buildEnvironment } = await import('../../integrations/security-headers.ts');
    const { mkdtempSync, mkdirSync, writeFileSync } = await import('node:fs');
    const { tmpdir } = await import('node:os');
    const { join } = await import('node:path');
    const { pathToFileURL } = await import('node:url');
    const root = mkdtempSync(join(tmpdir(), 't6m-build-'));
    mkdirSync(join(root, 'client'));
    mkdirSync(join(root, 'server'));
    const client = pathToFileURL(`${join(root, 'client')}/`);
    expect(await buildEnvironment(client)).toBe('desconocido');
    writeFileSync(join(root, 'server', 'wrangler.json'), JSON.stringify({ vars: { ENVIRONMENT: 'production' } }));
    expect(await buildEnvironment(client)).toBe('production');
    writeFileSync(join(root, 'server', 'wrangler.json'), '{ no es json');
    expect(await buildEnvironment(client)).toBe('desconocido');
  });

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
