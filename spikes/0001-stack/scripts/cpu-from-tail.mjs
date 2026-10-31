// Calcula p50/p95/p99 de CPU y de tiempo de pared por ruta a partir de `wrangler tail --format json`.
// Uso: node scripts/cpu-from-tail.mjs tail.ndjson   (escribe cpu-results.json)
// Acepta la salida tal cual: objetos JSON seguidos (en una o varias líneas), UTF-8 o UTF-16
// (Windows PowerShell 5.1 redirige con `>` en UTF-16LE).
import { readFileSync, writeFileSync } from 'node:fs';

const file = process.argv[2];
if (!file) throw new Error('Uso: node scripts/cpu-from-tail.mjs tail.ndjson');
const buf = readFileSync(file);
const text =
  buf[0] === 0xff && buf[1] === 0xfe
    ? buf.subarray(2).toString('utf16le')
    : buf.toString('utf8').replace(/^﻿/, '');

/** Extrae los objetos JSON de primer nivel aunque vengan formateados en varias líneas. */
function* objects(s) {
  let depth = 0;
  let start = -1;
  let inString = false;
  let escaped = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (c === '\\') escaped = true;
      else if (c === '"') inString = false;
    } else if (c === '"') inString = true;
    else if (c === '{') {
      if (depth++ === 0) start = i;
    } else if (c === '}' && --depth === 0) {
      try {
        yield JSON.parse(s.slice(start, i + 1));
      } catch {
        // Fragmento que no es un evento: se ignora.
      }
    }
  }
}

const byRoute = new Map();
let withoutCpu = 0;
for (const ev of objects(text)) {
  const url = ev?.event?.request?.url;
  if (!url) continue;
  if (typeof ev.cpuTime !== 'number') {
    withoutCpu++;
    continue;
  }
  const route = new URL(url).pathname;
  const entry = byRoute.get(route) ?? { cpu: [], wall: [], outcomes: {} };
  entry.cpu.push(ev.cpuTime);
  if (typeof ev.wallTime === 'number') entry.wall.push(ev.wallTime);
  entry.outcomes[ev.outcome] = (entry.outcomes[ev.outcome] ?? 0) + 1;
  byRoute.set(route, entry);
}

const pct = (arr, p) => {
  const s = [...arr].sort((a, b) => a - b);
  return s.length ? s[Math.min(s.length - 1, Math.ceil((p / 100) * s.length) - 1)] : null;
};
const result = {};
for (const [route, e] of byRoute) {
  result[route] = {
    requests: e.cpu.length,
    cpuMs: { p50: pct(e.cpu, 50), p95: pct(e.cpu, 95), p99: pct(e.cpu, 99), max: Math.max(...e.cpu) },
    wallMs: e.wall.length ? { p50: pct(e.wall, 50), p95: pct(e.wall, 95), p99: pct(e.wall, 99) } : null,
    overFreeLimit10ms: e.cpu.filter((t) => t > 10).length,
    outcomes: e.outcomes,
  };
}
writeFileSync('cpu-results.json', `${JSON.stringify({ source: file, withoutCpu, routes: result }, null, 2)}\n`);
console.table(
  Object.fromEntries(
    Object.entries(result).map(([r, v]) => [r, { n: v.requests, p50: v.cpuMs.p50, p95: v.cpuMs.p95, p99: v.cpuMs.p99, '>10ms': v.overFreeLimit10ms }]),
  ),
);
if (withoutCpu) console.warn(`${withoutCpu} eventos sin cpuTime: usa Workers Logs del panel (campo CPU time) para esos.`);
