#!/usr/bin/env node
// Hornea con Cycles los pases de luz del prototipo B (Javi, 04-11-2026): exporta la sala del prototipo A a
// glTF desde /prototipos/hornear y lanza Blender portátil sin interfaz (hornear-b-cycles.py). Los pases de
// datos (albedo, normal, profundidad) los sigue sacando hornear-b.mjs desde three.js.
// Uso: node scripts/prototipos/hornear-b-cycles.mjs [--base http://127.0.0.1:4398] [--muestras 128]
//      [--blender C:\tools\blender\blender.exe] [--exposicion 0] [--ambiente 0.04] [--bruma 0.012] [--solo base]
// Variable BLENDER: ruta de blender.exe (por defecto C:\tools\blender\blender.exe).
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { argumentos, navegador, pausa, servidor, webDir } from './comun.mjs';

const args = argumentos({ ruta: '/prototipos/hornear' });
const blender = String(args.blender ?? process.env.BLENDER ?? 'C:\\tools\\blender\\blender.exe');
const destino = path.join(webDir, 'public', 'prototipos', 'armeria-b');
mkdirSync(destino, { recursive: true });
const tmp = mkdtempSync(path.join(tmpdir(), 't6m-horno-'));
const glb = path.join(tmp, 'sala.glb');

const { base, parar } = await servidor(args, args.ruta);
const browser = await navegador();
try {
  const page = await (
    await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })
  ).newPage();
  await page.goto(`${base}${args.ruta}`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__horno?.listo === true, null, { timeout: 60_000 });
  await pausa(1500);
  const b64 = await page.evaluate(() => window.__horno.exportar());
  writeFileSync(glb, Buffer.from(b64, 'base64'));
  console.log(`✔ sala.glb · ${Math.round(Buffer.byteLength(b64, 'base64') / 1024)} KB`);
} finally {
  await browser.close();
  parar();
}

const extra = ['muestras', 'exposicion', 'ambiente', 'bruma', 'solo', 'ancho', 'alto'].flatMap((k) =>
  args[k] !== undefined ? [`--${k}`, String(args[k])] : [],
);
const r = spawnSync(
  blender,
  [
    '--background',
    '--factory-startup',
    '--python',
    path.join(webDir, 'scripts', 'prototipos', 'hornear-b-cycles.py'),
    '--',
    glb,
    destino,
    ...extra,
  ],
  { stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
);
for (const linea of `${r.stdout}\n${r.stderr}`.split(/\r?\n/)) {
  if (/^HORNO|Error|Traceback|Saved:/.test(linea)) console.log(linea);
}
process.exit(r.status ?? 1);
