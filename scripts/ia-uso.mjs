#!/usr/bin/env node
// pnpm ia:uso — tokens por modelo y día de las sesiones de Claude Code de este proyecto (docs/ia/modelos.md).
// Lee los registros locales (~/.claude/projects/C--dev-taller6mm*, y los antiguos C--dev-bancada*),
// incluidos los subagentes. Solo suma contadores (tokens, peticiones): nunca lee ni muestra contenido.
// Las llamadas al asesor (advisor) se cuentan aparte, con el prefijo «asesor:».
// El formato de esos registros es interno de Claude Code y puede cambiar: si deja de cuadrar, revisa aquí.
//
// Uso: pnpm ia:uso [--desde 2026-11-01] [--hasta 2026-11-30] [--json]
import { createReadStream, existsSync, readdirSync, statSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';

const PROYECTO = /^C--dev-(?:taller6mm|bancada)(?:-|$)/i;
const CAMPOS = ['peticiones', 'entrada', 'cache_escrita', 'cache_leida', 'salida'];

/** Contadores de una línea del registro, o null si no es una respuesta del modelo. Nunca toca el contenido. */
export function contadores(linea) {
  let o;
  try {
    o = JSON.parse(linea);
  } catch {
    return null;
  }
  const m = o?.message;
  const u = m?.usage;
  if (o?.type !== 'assistant' || !u || typeof m.model !== 'string' || m.model.startsWith('<')) return null;
  const n = (x) => (Number.isFinite(x) ? x : 0);
  const filas = [
    {
      modelo: m.model,
      entrada: n(u.input_tokens),
      cache_escrita: n(u.cache_creation_input_tokens),
      cache_leida: n(u.cache_read_input_tokens),
      salida: n(u.output_tokens),
    },
  ];
  // Las consultas al asesor llegan como iteraciones de otro tipo dentro de la misma respuesta.
  for (const it of Array.isArray(u.iterations) ? u.iterations : []) {
    if (!it || it.type === 'message') continue;
    filas.push({
      modelo: `asesor:${typeof it.model === 'string' ? it.model : (o.advisorModel ?? 'desconocido')}`,
      entrada: n(it.input_tokens),
      cache_escrita: n(it.cache_creation_input_tokens),
      cache_leida: n(it.cache_read_input_tokens),
      salida: n(it.output_tokens),
    });
  }
  return { id: m.id ?? o.requestId ?? o.uuid ?? null, dia: String(o.timestamp ?? '').slice(0, 10), filas };
}

/** Suma por día y modelo. Una respuesta ocupa varias líneas (una por bloque): se cuenta una vez por id. */
export function sumar(lineas, { desde = '', hasta = '9999' } = {}, vistos = new Set()) {
  const total = new Map();
  for (const l of lineas) {
    const c = contadores(l);
    if (!c || !/^\d{4}-\d{2}-\d{2}$/.test(c.dia) || c.dia < desde || c.dia > hasta) continue;
    if (c.id) {
      if (vistos.has(c.id)) continue;
      vistos.add(c.id);
    }
    for (const f of c.filas) {
      const k = `${c.dia}\t${f.modelo}`;
      const t = total.get(k) ?? {
        dia: c.dia,
        modelo: f.modelo,
        peticiones: 0,
        entrada: 0,
        cache_escrita: 0,
        cache_leida: 0,
        salida: 0,
      };
      t.peticiones += 1;
      for (const campo of CAMPOS.slice(1)) t[campo] += f[campo];
      total.set(k, t);
    }
  }
  return [...total.values()].sort((a, b) => a.dia.localeCompare(b.dia) || a.modelo.localeCompare(b.modelo));
}

/** Archivos .jsonl de las carpetas de este proyecto (y sus subagentes). */
export function registros(base) {
  if (!existsSync(base)) return [];
  const salida = [];
  const recorrer = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) recorrer(p);
      else if (e.name.endsWith('.jsonl')) salida.push(p);
    }
  };
  for (const d of readdirSync(base)) {
    const p = path.join(base, d);
    if (PROYECTO.test(d) && statSync(p).isDirectory()) recorrer(p);
  }
  return salida;
}

function tabla(filas) {
  const fmt = (x) => x.toLocaleString('es-ES');
  const cab = ['Día', 'Modelo', 'Peticiones', 'Entrada', 'Caché escrita', 'Caché leída', 'Salida'];
  const datos = filas.map((f) => [f.dia, f.modelo, ...CAMPOS.map((c) => fmt(f[c]))]);
  const porModelo = new Map();
  for (const f of filas) {
    const t = porModelo.get(f.modelo) ?? Object.fromEntries(CAMPOS.map((c) => [c, 0]));
    for (const c of CAMPOS) t[c] += f[c];
    porModelo.set(f.modelo, t);
  }
  for (const [m, t] of porModelo) datos.push(['TOTAL', m, ...CAMPOS.map((c) => fmt(t[c]))]);
  const anchos = cab.map((h, i) => Math.max(h.length, ...datos.map((d) => String(d[i]).length)));
  const linea = (d) =>
    d.map((x, i) => (i < 2 ? String(x).padEnd(anchos[i]) : String(x).padStart(anchos[i]))).join('  ');
  return [linea(cab), anchos.map((a) => '-'.repeat(a)).join('  '), ...datos.map(linea)].join('\n');
}

async function main() {
  const args = process.argv.slice(2);
  const valor = (n) => {
    const i = args.indexOf(n);
    return i >= 0 ? args[i + 1] : undefined;
  };
  const base = path.join(process.env.CLAUDE_CONFIG_DIR ?? path.join(os.homedir(), '.claude'), 'projects');
  const filtro = { desde: valor('--desde') ?? '', hasta: valor('--hasta') ?? '9999' };
  const vistos = new Set();
  const filas = [];
  for (const archivo of registros(base)) {
    const lineas = [];
    for await (const l of createInterface({
      input: createReadStream(archivo, 'utf8'),
      crlfDelay: Number.POSITIVE_INFINITY,
    })) {
      if (l.includes('"usage"')) lineas.push(l);
    }
    filas.push(...sumar(lineas, filtro, vistos));
  }
  // Un mismo día y modelo puede venir de varios archivos: se agrupa otra vez.
  const juntas = new Map();
  for (const f of filas) {
    const k = `${f.dia}\t${f.modelo}`;
    const t = juntas.get(k) ?? { ...f, ...Object.fromEntries(CAMPOS.map((c) => [c, 0])) };
    for (const c of CAMPOS) t[c] += f[c];
    juntas.set(k, t);
  }
  const resultado = [...juntas.values()].sort((a, b) => a.dia.localeCompare(b.dia) || a.modelo.localeCompare(b.modelo));
  if (args.includes('--json')) process.stdout.write(`${JSON.stringify(resultado, null, 2)}\n`);
  else process.stdout.write(`${resultado.length ? tabla(resultado) : 'Sin registros de uso para este proyecto.'}\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
