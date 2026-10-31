// Genera carga moderada contra el spike desplegado para medir la CPU con `wrangler tail`.
// Cada escenario lleva `?m=<nombre>`: el middleware lo registra junto al isolate y al número de
// petición, y scripts/cpu-from-tail.mjs separa frío (n = 1) y caliente por escenario.
// Uso (Windows, macOS o Linux):
//   node scripts/load.mjs --base https://taller6mm-spike.<subdominio>.workers.dev --n 200 \
//     [--cookie "better-auth.session_token=…; better-auth.session_data=…"]
// Con --cookie añade los escenarios con sesión (cópiala del navegador tras iniciar sesión).
import { parseArgs } from 'node:util';

const { values } = parseArgs({
  options: {
    base: { type: 'string' },
    n: { type: 'string', default: '200' },
    warmup: { type: 'string', default: '5' },
    cookie: { type: 'string' },
    concurrency: { type: 'string', default: '4' },
  },
});
const base = values.base ?? '';
if (!base.startsWith('https://') && !base.startsWith('http://127.0.0.1')) {
  throw new Error('Indica --base con la URL del Worker (https://…workers.dev) o http://127.0.0.1:…');
}
const n = Number(values.n);
const warmup = Number(values.warmup);
const concurrency = Math.min(Number(values.concurrency), 8);
const cookie = values.cookie;
const tokenOnly = cookie
  ?.split(';')
  .find((c) => c.includes('session_token'))
  ?.trim();

/** @type {Array<{ m: string, path: string, init?: RequestInit, count?: number }>} */
const scenarios = [
  { m: 'inicio-anonimo', path: '/' },
  { m: 'sesion-anonima', path: '/api/auth/get-session' },
];
if (cookie && tokenOnly) {
  scenarios.push(
    { m: 'inicio-cookie', path: '/', init: { headers: { cookie } } },
    { m: 'inicio-token', path: '/', init: { headers: { cookie: tokenOnly } } },
    { m: 'sesion-cookie', path: '/api/auth/get-session', init: { headers: { cookie } } },
    { m: 'sesion-token', path: '/api/auth/get-session', init: { headers: { cookie: tokenOnly } } },
  );
}
// Pide enlaces mágicos de verdad (escribe en D1): pocas peticiones.
scenarios.push({
  m: 'enlace-alta',
  path: '/api/auth/sign-in/magic-link',
  count: Math.min(n, 20),
  init: {
    method: 'POST',
    headers: { 'content-type': 'application/json', origin: new URL(base).origin },
    body: JSON.stringify({ email: 'carga@example.test', callbackURL: '/' }),
  },
});

/** Percentil por rango más cercano (el mismo método que cpu-from-tail.mjs). */
const percentile = (sorted, p) => sorted[Math.max(0, Math.ceil((p / 100) * sorted.length) - 1)];

for (const s of scenarios) {
  const url = new URL(s.path, base);
  url.searchParams.set('m', s.m);
  const total = (s.count ?? n) + warmup;
  const times = [];
  const statuses = {};
  let next = 0;
  const worker = async () => {
    while (next < total) {
      const i = next++;
      const t0 = performance.now();
      const res = await fetch(url, { redirect: 'manual', ...s.init });
      await res.arrayBuffer();
      if (i >= warmup) times.push(performance.now() - t0);
      statuses[res.status] = (statuses[res.status] ?? 0) + 1;
    }
  };
  await Promise.all(Array.from({ length: concurrency }, worker));
  times.sort((a, b) => a - b);
  console.log(
    `${s.m}: ${total} peticiones (${warmup} de calentamiento), estados ${JSON.stringify(statuses)}, ` +
      `latencia cliente p50 ${Math.round(percentile(times, 50))} ms, p95 ${Math.round(percentile(times, 95))} ms`,
  );
}
console.log('Ahora corta `wrangler tail` (Ctrl+C) y ejecuta: node scripts/cpu-from-tail.mjs tail.ndjson');
