#!/usr/bin/env node
// Hornea con Cycles los pases de luz del prototipo B (Javi, 04-11-2026): exporta la sala del prototipo A a
// glTF desde /prototipos/hornear y lanza Blender portátil sin interfaz (hornear-b-cycles.py). Los pases de
// datos (albedo, normal, profundidad) los sigue sacando hornear-b.mjs desde three.js.
// Uso: node scripts/prototipos/hornear-b-cycles.mjs [--base http://127.0.0.1:4398] [--muestras 128]
//      [--blender C:\tools\blender\blender.exe] [--exposicion 0] [--ambiente 0.04] [--bruma 0.012] [--solo base]
//      [--ancho 2560 --alto 1440] [--hilos 12] [--salida <carpeta>] [--modulo <zona>|todos]
// Variable BLENDER: ruta de blender.exe (por defecto C:\tools\blender\blender.exe).
// Los pases en uso se hornearon con --ancho 2560 --alto 1440 y lo demás por defecto (unos 4 min por pase en CPU).
//
// ── Recortes por módulo para el móvil (--modulo): DISEÑO, aún sin conectar al compositor ──────────────
// Problema (critico-diseno, 2.ª revisión): en un móvil de 3× el B enseña unos 545 px del pase de 2560 px
// en 1170 px físicos (ampliado ×2,1) y además pinta a DPR 1,5: borroso.
// 1. Geometría: recorteMovil(zona) (camara.ts) da, para cada módulo, la ventana del encuadre que ve el
//    móvil de referencia (430 × 956 px CSS a 3×) con el módulo centrado y 16 px de aire a cada lado.
// 2. Horneado: este script, con --modulo, hornea esa ventana con la misma cámara (borde de render de
//    Cycles) a 1290 px de ancho: 1 píxel de pase por píxel físico, nunca ampliado. Salen en
//    <salida>/movil/<zona>/<pase>.webp. Con --hilos se le dejan núcleos al resto del equipo.
// 3. Variantes: de cada pase, 1290 px (3×) y 860 px (2× o ahorro de datos), reducido del primero. El
//    compositor elige por `clientWidth × min(devicePixelRatio, 3)`, como un srcset; el póster móvil pasa
//    a ser una imagen por módulo con `srcset` de verdad (poster.mjs, compuesto en reposo de estos pases).
// 4. Compositor (EscenaB en móvil): cada módulo es una «diapositiva». Al deslizar, se pintan la actual y
//    la vecina una junto a otra (12 texturas, dentro de las 16 unidades de WebGL2); solo viven en la GPU el
//    módulo centrado y sus dos vecinos, y los pases de datos siguen sin cargarse (no hay linterna).
//    Resolución dinámica: DPR 1,5 mientras algo se mueve y hasta 3 en el fotograma de reposo.
// 5. Presupuesto (docs/02 §3.6, ≤ 2 MB en móvil): se carga el banco (módulo por defecto) y, en reposo, sus
//    vecinos; el resto, al acercarse. Las cifras medidas del banco están en el informe de la rebanada.
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { recorteMovil } from '../../src/components/armeria/camara.ts';
import { ZONAS } from '../../src/components/armeria/zonas.ts';
import { argumentos, navegador, pausa, servidor, webDir } from './comun.mjs';

const args = argumentos({ ruta: '/prototipos/hornear' });
const blender = String(args.blender ?? process.env.BLENDER ?? 'C:\\tools\\blender\\blender.exe');
const destino = args.salida
  ? path.resolve(String(args.salida))
  : path.join(webDir, 'public', 'prototipos', 'armeria-b');
mkdirSync(destino, { recursive: true });
// Sin --modulo, el encuadre entero; con él, el recorte de una zona (o de todas) para el móvil.
const modulos = args.modulo ? ZONAS.filter((z) => args.modulo === 'todos' || z.id === args.modulo) : [null];
if (!modulos.length) throw new Error(`No hay ninguna zona «${args.modulo}»`);
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

const opciones = (claves) => claves.flatMap((k) => (args[k] !== undefined ? [`--${k}`, String(args[k])] : []));
let estado = 0;
for (const zona of modulos) {
  const recorte = zona ? recorteMovil(zona) : null;
  const salida = zona ? path.join(destino, 'movil', zona.id) : destino;
  mkdirSync(salida, { recursive: true });
  const extra = [
    ...opciones(['muestras', 'exposicion', 'ambiente', 'bruma', 'solo']),
    ...(recorte
      ? [
          '--recorte',
          [recorte.x, recorte.y, recorte.ancho, recorte.alto].map((n) => n.toFixed(5)).join(','),
          '--ancho',
          String(recorte.px[0]),
        ]
      : opciones(['ancho', 'alto'])),
  ];
  const inicio = Date.now();
  const r = spawnSync(
    blender,
    [
      ...(args.hilos ? ['--threads', String(args.hilos)] : []),
      '--background',
      '--factory-startup',
      '--python',
      path.join(webDir, 'scripts', 'prototipos', 'hornear-b-cycles.py'),
      '--',
      glb,
      salida,
      ...extra,
    ],
    { stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
  );
  for (const linea of `${r.stdout}\n${r.stderr}`.split(/\r?\n/)) {
    if (/^HORNO|Error|Traceback|Saved:/.test(linea)) console.log(linea);
  }
  const minutos = ((Date.now() - inicio) / 60_000).toFixed(1);
  console.log(`✔ ${zona ? `módulo ${zona.id} (${recorte.px.join(' × ')} px)` : 'encuadre entero'} · ${minutos} min`);
  estado ||= r.status ?? 1;
}
process.exit(estado);
