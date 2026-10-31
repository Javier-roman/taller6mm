// p50/p95/p99 de CPU y de tiempo de pared por escenario, separando frío (1.ª petición del isolate) y
// caliente, a partir de `wrangler tail --format json`. Uso: node scripts/cpu-from-tail.mjs tail.ndjson
// Acepta la salida tal cual: objetos JSON seguidos (en una o varias líneas), UTF-8 o UTF-16
// (Windows PowerShell 5.1 redirige con `>` en UTF-16LE). Escribe cpu-results.json.
import { readFileSync, writeFileSync } from 'node:fs';

const file = process.argv[2];
if (!file) throw new Error('Uso: node scripts/cpu-from-tail.mjs tail.ndjson');
const WARMUP = Number(process.env.WARMUP ?? 5); // peticiones en caliente que se descartan por escenario
const buf = readFileSync(file);
const text =
  buf[0] === 0xff && buf[1] === 0xfe ? buf.subarray(2).toString('utf16le') : buf.toString('utf8').replace(/^﻿/, '');

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

/** La línea que escribe src/middleware.ts: { spike: 'req', iso, n, m }. */
function tagOf(ev) {
  for (const log of ev.logs ?? []) {
    for (const part of [log.message].flat()) {
      if (typeof part !== 'string' || !part.includes('"spike":"req"')) continue;
      try {
        return JSON.parse(part);
      } catch {
        // Línea cortada: se ignora.
      }
    }
  }
  return null;
}

const groups = new Map();
let events = 0;
let withoutCpu = 0;
let withoutTag = 0;
for (const ev of objects(text)) {
  if (!ev?.event?.request?.url) continue;
  events++;
  if (typeof ev.cpuTime !== 'number') {
    withoutCpu++;
    continue;
  }
  const tag = tagOf(ev);
  if (!tag) withoutTag++;
  const scenario = tag?.m ?? new URL(ev.event.request.url).pathname;
  const g = groups.get(scenario) ?? { cold: [], warm: [], wall: [], outcomes: {} };
  if (tag?.n === 1) g.cold.push(ev.cpuTime);
  else g.warm.push({ t: ev.eventTimestamp ?? 0, cpu: ev.cpuTime, wall: ev.wallTime });
  g.outcomes[ev.outcome] = (g.outcomes[ev.outcome] ?? 0) + 1;
  groups.set(scenario, g);
}

/** Percentil por rango más cercano (el mismo método que load.mjs). */
const pct = (values, p) => {
  const s = [...values].sort((a, b) => a - b);
  return s.length ? s[Math.max(0, Math.ceil((p / 100) * s.length) - 1)] : null;
};
const result = {};
for (const [scenario, g] of groups) {
  const warm = g.warm.sort((a, b) => a.t - b.t).slice(WARMUP);
  const cpu = warm.map((w) => w.cpu);
  const wall = warm.map((w) => w.wall).filter((v) => typeof v === 'number');
  result[scenario] = {
    calientes: cpu.length,
    cpuMs: { p50: pct(cpu, 50), p95: pct(cpu, 95), p99: pct(cpu, 99), max: cpu.length ? Math.max(...cpu) : null },
    paredMs: wall.length ? { p50: pct(wall, 50), p95: pct(wall, 95), p99: pct(wall, 99) } : null,
    frias: g.cold.length,
    cpuFriaMs: g.cold.length ? { p50: pct(g.cold, 50), max: Math.max(...g.cold) } : null,
    porEncimaDe10ms: cpu.filter((t) => t > 10).length + g.cold.filter((t) => t > 10).length,
    resultados: g.outcomes,
  };
}
writeFileSync(
  'cpu-results.json',
  `${JSON.stringify({ source: file, events, withoutCpu, withoutTag, warmupDiscarded: WARMUP, scenarios: result }, null, 2)}\n`,
);
console.table(
  Object.fromEntries(
    Object.entries(result).map(([m, v]) => [
      m,
      {
        n: v.calientes,
        p50: v.cpuMs.p50,
        p95: v.cpuMs.p95,
        p99: v.cpuMs.p99,
        frías: v.frias,
        'fría p50': v.cpuFriaMs?.p50 ?? '-',
        '>10ms': v.porEncimaDe10ms,
      },
    ]),
  ),
);
console.log(`${events} eventos leídos; compáralo con las peticiones que envió load.mjs (tail puede muestrear).`);
if (withoutCpu) console.warn(`${withoutCpu} eventos sin cpuTime: usa Workers Logs del panel (campo «CPU time»).`);
if (withoutTag)
  console.warn(`${withoutTag} eventos sin la etiqueta del middleware: no se pueden separar frío y caliente.`);
