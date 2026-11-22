#!/usr/bin/env node
// Prepara las vistas horneadas de La Armería (póster y pases de luz): hash, copia local y subida a R2.
// Los binarios (WebP) viven en assets-src/vistas/armeria/ y NO se suben a git (.gitignore); en git solo queda
// el manifiesto src/components/armeria/vistas.json con sus hashes. Cada conjunto vive en una ruta con el hash
// de su contenido (/assets/armeria/<hash>/<archivo>): inmutable, sin invalidar nada (src/lib/vistas.ts).
//
//   node scripts/armeria/vistas.mjs manifiesto        recalcula hashes y escribe el manifiesto
//   node scripts/armeria/vistas.mjs local             copia el conjunto a public/assets/armeria/<hash>/ (desarrollo, e2e)
//   node scripts/armeria/vistas.mjs r2 [--bucket b]   IMPRIME los comandos de subida a R2; no ejecuta nada remoto
//
// La subida la ejecuta una persona con su sesión de wrangler (preview: taller6mm-assets-preview). Este script
// nunca llama a la red ni toca credenciales.
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CACHE_INMUTABLE, hashConjunto } from '../../src/lib/vistas.ts';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const webDir = path.resolve(aqui, '..', '..');
const raiz = path.resolve(webDir, '..', '..');
const origen = path.join(raiz, 'assets-src', 'vistas', 'armeria');
const manifiesto = path.join(webDir, 'src', 'components', 'armeria', 'vistas.json');
const publico = path.join(webDir, 'public', 'assets', 'armeria');
const BUCKET_PREVIEW = 'taller6mm-assets-preview';

const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex');

function leerOrigen() {
  let nombres;
  try {
    nombres = readdirSync(origen).filter((n) => n.endsWith('.webp'));
  } catch {
    throw new Error(`No existe ${origen}: faltan los binarios de las vistas (assets-src/vistas/armeria/*.webp).`);
  }
  if (!nombres.length) throw new Error(`No hay archivos .webp en ${origen}`);
  return nombres.sort().map((nombre) => {
    const datos = readFileSync(path.join(origen, nombre));
    return { nombre, sha256: sha256(datos), bytes: datos.byteLength };
  });
}

const leerManifiesto = () => JSON.parse(readFileSync(manifiesto, 'utf8'));

async function comando(cmd, args) {
  if (cmd === 'manifiesto') {
    const archivos = leerOrigen();
    const hash = await hashConjunto(Object.fromEntries(archivos.map((a) => [a.nombre, a.sha256])));
    const salida = {
      hash,
      archivos: Object.fromEntries(archivos.map((a) => [a.nombre, { sha256: a.sha256, bytes: a.bytes }])),
    };
    writeFileSync(manifiesto, `${JSON.stringify(salida, null, 2)}\n`);
    const total = archivos.reduce((s, a) => s + a.bytes, 0);
    console.log(
      `✔ ${path.relative(raiz, manifiesto)} · hash ${hash} · ${archivos.length} archivos · ${Math.round(total / 1024)} KB`,
    );
    return;
  }

  // El resto usa el manifiesto y comprueba que los binarios son los suyos.
  const m = leerManifiesto();
  const reales = leerOrigen();
  for (const a of reales) {
    if (m.archivos[a.nombre]?.sha256 !== a.sha256)
      throw new Error(`${a.nombre} no coincide con el manifiesto: ejecuta «manifiesto» y revisa el cambio.`);
  }
  const faltan = Object.keys(m.archivos).filter((n) => !reales.some((a) => a.nombre === n));
  if (faltan.length) throw new Error(`Faltan binarios del manifiesto: ${faltan.join(', ')}`);

  if (cmd === 'local') {
    rmSync(publico, { recursive: true, force: true });
    const destino = path.join(publico, m.hash);
    mkdirSync(destino, { recursive: true });
    for (const a of reales) copyFileSync(path.join(origen, a.nombre), path.join(destino, a.nombre));
    console.log(
      `✔ ${reales.length} archivos en ${path.relative(raiz, destino)} (servidos como /assets/armeria/${m.hash}/…)`,
    );
    return;
  }

  if (cmd === 'r2') {
    const bucket = typeof args.bucket === 'string' ? args.bucket : BUCKET_PREVIEW;
    if (!/^[a-z0-9][a-z0-9-]{2,62}$/.test(bucket)) throw new Error(`Nombre de bucket no válido: ${bucket}`);
    console.log(`# Subida de las vistas ${m.hash} al bucket ${bucket} (ejecútalo tú, con tu sesión de wrangler).`);
    console.log('# Desde apps/web. Objetos inmutables: la clave lleva el hash del contenido.');
    for (const a of reales) {
      const rel = path.relative(webDir, path.join(origen, a.nombre)).split(path.sep).join('/');
      console.log(
        `pnpm exec wrangler r2 object put ${bucket}/armeria/${m.hash}/${a.nombre} --file ${rel} --content-type image/webp --cache-control "${CACHE_INMUTABLE}" --remote`,
      );
    }
    console.log(
      `# Comprobación: GET /assets/armeria/${m.hash}/${reales[0]?.nombre} debe dar 200 con cache-control inmutable.`,
    );
    return;
  }

  throw new Error(`Orden desconocida «${cmd}». Usa: manifiesto | local | r2`);
}

const [cmd = '', ...resto] = process.argv.slice(2);
const args = {};
for (let i = 0; i < resto.length; i++) {
  const a = resto[i];
  if (a?.startsWith('--')) args[a.slice(2)] = resto[i + 1] && !resto[i + 1].startsWith('--') ? resto[++i] : true;
}
comando(cmd, args).catch((e) => {
  console.error(`✘ ${e instanceof Error ? e.message : String(e)}`);
  process.exit(1);
});
