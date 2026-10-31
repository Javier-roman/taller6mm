// Cabeceras y protecciones de S4 contra la build real en workerd (wrangler dev aplica `_headers`).
import { expect, test } from '@playwright/test';

const COMMON = {
  'strict-transport-security': /^max-age=\d{8,}; includeSubDomains$/,
  'x-content-type-options': /^nosniff$/,
  'referrer-policy': /^strict-origin-when-cross-origin$/,
  'permissions-policy': /camera=\(\)/,
  'cross-origin-opener-policy': /^same-origin$/,
  'cross-origin-resource-policy': /^same-origin$/,
  'x-frame-options': /^DENY$/,
  'x-robots-tag': /noindex/, // la build de los e2e es local, nunca producción
} as const;

test.describe('cabeceras de seguridad', () => {
  test('página SSR: comunes + CSP de Astro con frame-ancestors', async ({ request }) => {
    const res = await request.get('/');
    expect(res.status()).toBe(200);
    const headers = res.headers();
    for (const [name, pattern] of Object.entries(COMMON)) expect(headers[name], name).toMatch(pattern);
    const csp = headers['content-security-policy'] ?? '';
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).not.toContain('unsafe-inline');
  });

  test('estáticos (sin pasar por el Worker): las mismas cabeceras por _headers', async ({ request }) => {
    const res = await request.get('/favicon.svg');
    expect(res.status()).toBe(200);
    const headers = res.headers();
    for (const [name, pattern] of Object.entries(COMMON)) expect(headers[name], name).toMatch(pattern);
    expect(headers['content-security-policy']).toContain("frame-ancestors 'none'");
  });

  test('/.well-known/security.txt se sirve como texto', async ({ request }) => {
    const res = await request.get('/.well-known/security.txt');
    expect(res.status()).toBe(200);
    expect(res.headers()['content-type']).toMatch(/^text\/plain/);
    const body = await res.text();
    expect(body).toMatch(/^Contact: https:\/\//m);
    expect(body).toMatch(/^Expires: /m);
  });
});

test.describe('todas las respuestas del Worker llevan las cabeceras (src/worker.ts)', () => {
  test('una sola CSP por respuesta (headersArray no fusiona duplicados)', async ({ request }) => {
    for (const path of ['/', '/no-existe']) {
      const res = await request.get(path);
      const csp = res.headersArray().filter((h) => h.name.toLowerCase() === 'content-security-policy');
      expect(csp, path).toHaveLength(1);
    }
  });

  test('un 404 del Worker también va protegido', async ({ request }) => {
    const res = await request.get('/no-existe');
    expect(res.status()).toBe(404);
    const headers = res.headers();
    for (const [name, pattern] of Object.entries(COMMON)) expect(headers[name], name).toMatch(pattern);
  });
});

test.describe('CSRF (checkOrigin de Astro)', () => {
  for (const contentType of ['application/x-www-form-urlencoded', 'text/plain', 'multipart/form-data; boundary=x']) {
    test(`rechaza un envío desde otro origen (${contentType.split(';')[0]}), con cabeceras`, async ({ request }) => {
      const res = await request.post('/', {
        headers: { origin: 'https://atacante.example', 'content-type': contentType },
        data: contentType.startsWith('multipart') ? '--x--\r\n' : 'a=1',
      });
      expect(res.status()).toBe(403);
      const headers = res.headers();
      for (const [name, pattern] of Object.entries(COMMON)) expect(headers[name], name).toMatch(pattern);
      expect(headers['content-security-policy']).toBe("default-src 'none'; frame-ancestors 'none'");
    });
  }
});
