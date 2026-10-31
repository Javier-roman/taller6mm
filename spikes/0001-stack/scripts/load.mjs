// Genera carga moderada contra el spike desplegado para medir la CPU con `wrangler tail`.
// Uso (Windows, macOS o Linux):
//   node scripts/load.mjs --base https://taller6mm-spike.<tu-subdominio>.workers.dev --n 200 \
//     --path / --path /api/auth/get-session [--cookie "better-auth.session_token=..."]
// Hace n peticiones por ruta con 4 en paralelo como máximo (muy por debajo de cualquier límite).
import { parseArgs } from 'node:util';

const { values } = parseArgs({
  options: {
    base: { type: 'string' },
    n: { type: 'string', default: '200' },
    path: { type: 'string', multiple: true, default: ['/', '/api/auth/get-session'] },
    cookie: { type: 'string' },
    concurrency: { type: 'string', default: '4' },
  },
});
if (!values.base?.startsWith('https://') && !values.base?.startsWith('http://127.0.0.1')) {
  throw new Error('Indica --base con la URL del Worker (https://…workers.dev) o http://127.0.0.1:…');
}
const n = Number(values.n);
const concurrency = Math.min(Number(values.concurrency), 8);
const headers = values.cookie ? { cookie: values.cookie } : {};

for (const route of values.path) {
  const url = new URL(route, values.base).toString();
  const times = [];
  const statuses = {};
  let next = 0;
  const worker = async () => {
    while (next < n) {
      next++;
      const t0 = performance.now();
      const res = await fetch(url, { headers, redirect: 'manual' });
      await res.arrayBuffer();
      times.push(performance.now() - t0);
      statuses[res.status] = (statuses[res.status] ?? 0) + 1;
    }
  };
  await Promise.all(Array.from({ length: concurrency }, worker));
  times.sort((a, b) => a - b);
  const q = (p) => Math.round(times[Math.min(times.length - 1, Math.floor((p / 100) * times.length))]);
  console.log(`${route}: ${times.length} peticiones, estados ${JSON.stringify(statuses)}, latencia cliente p50 ${q(50)} ms, p95 ${q(95)} ms`);
}
console.log('Ahora corta `wrangler tail` (Ctrl+C) y ejecuta: node scripts/cpu-from-tail.mjs tail.ndjson');
