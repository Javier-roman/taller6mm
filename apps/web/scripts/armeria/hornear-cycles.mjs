#!/usr/bin/env node
// Hornea con Cycles los pases de luz de La Armería (nivel B y póster): exporta la sala 3D a glTF desde el horno
// y lanza Blender portátil sin interfaz (hornear-cycles.py), que deja los WebP en assets-src/vistas/armeria/.
// Uso: node scripts/armeria/hornear-cycles.mjs [--muestras 128] [--ancho 2560 --alto 1440] [--hilos 8]
//      [--exposicion 0] [--ambiente 0.04] [--bruma 0] [--solo base,calidas] [--blender C:\tools\blender\blender.exe]
// Variable BLENDER: ruta de blender.exe (por defecto C:\tools\blender\blender.exe). Unos 4 min por pase en CPU a 2560 px.
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { argumentos, carpetaVistas, navegador, pausa, servidorHorno, webDir } from './comun.mjs';

const args = argumentos();
const blender = String(args.blender ?? process.env.BLENDER ?? 'C:\\tools\\blender\\blender.exe');
mkdirSync(carpetaVistas, { recursive: true });
const glb = path.join(mkdtempSync(path.join(tmpdir(), 't6m-horno-')), 'sala.glb');

const { base, parar } = await servidorHorno();
const browser = await navegador();
try {
  const page = await (
    await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })
  ).newPage();
  await page.goto(`${base}/horno.html`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__horno?.listo === true, null, { timeout: 90_000 });
  await pausa(1500);
  const b64 = await page.evaluate(() => window.__horno.exportar());
  writeFileSync(glb, Buffer.from(b64, 'base64'));
  console.log(`✔ sala.glb · ${Math.round(Buffer.byteLength(b64, 'base64') / 1024)} KB`);
} finally {
  await browser.close();
  await parar();
}

const opciones = (claves) => claves.flatMap((k) => (args[k] !== undefined ? [`--${k}`, String(args[k])] : []));
const inicio = Date.now();
const r = spawnSync(
  blender,
  [
    ...(args.hilos ? ['--threads', String(args.hilos)] : []),
    '--background',
    '--factory-startup',
    '--python',
    path.join(webDir, 'scripts', 'armeria', 'hornear-cycles.py'),
    '--',
    glb,
    carpetaVistas,
    ...opciones(['muestras', 'ancho', 'alto', 'exposicion', 'ambiente', 'bruma', 'solo']),
  ],
  { stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
);
for (const linea of `${r.stdout}\n${r.stderr}`.split(/\r?\n/)) {
  if (/^HORNO|Error|Traceback|Saved:/.test(linea)) console.log(linea);
}
console.log(`✔ Cycles · ${((Date.now() - inicio) / 60_000).toFixed(1)} min`);
process.exit(r.status ?? 1);
