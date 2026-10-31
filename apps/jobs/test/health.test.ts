// Se ejecuta dentro de workerd con el Worker real (`main` de wrangler.jsonc).
import { exports } from 'cloudflare:workers';
import { describe, expect, test } from 'vitest';

describe('GET /health', () => {
  test('responde ok, en JSON y sin caché', async () => {
    const res = await exports.default.fetch('https://jobs.test/health');
    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toContain('application/json');
    expect(res.headers.get('cache-control')).toBe('no-store');
    const body = await res.json<{ status: string; service: string; checkedAt: string }>();
    expect(body.status).toBe('ok');
    expect(body.service).toBe('taller6mm-jobs');
    expect(new Date(body.checkedAt).toISOString()).toBe(body.checkedAt); // ISO 8601 en UTC
  });

  test('las rutas desconocidas dan 404 sin detalles internos', async () => {
    const res = await exports.default.fetch('https://jobs.test/internal/no-existe');
    expect(res.status).toBe(404);
    expect(await res.json()).toEqual({ error: 'not_found' });
  });

  test('solo GET', async () => {
    const res = await exports.default.fetch('https://jobs.test/health', { method: 'POST' });
    expect(res.status).toBe(404);
  });
});
