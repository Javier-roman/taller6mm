#!/usr/bin/env node
// FPS orientativos de un prototipo de La Armería (Fase 1): escritorio a 1440 × 900 moviendo la
// linterna por la sala, y móvil simulado (390 × 844, DPR 3, táctil, CPU 4× más lenta) recorriendo el
// carrusel. Cuenta fotogramas con requestAnimationFrame en la página, con la escena pintando siempre
// (?medir). La GPU es la del equipo (no se puede simular la de un móvil): las cifras de móvil son una
// cota superior para la GPU y realistas para la CPU.
// Uso: node scripts/prototipos/medir.mjs --ruta /prototipos/armeria-a [--base http://127.0.0.1:4321]
//      [--segundos 8] [--salida archivo.json] [--headed]
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { gzipSync } from 'node:zlib';
import { argumentos, ESCRITORIO, esperarEscena, MOVIL, navegador, pausa, root, servidor } from './comun.mjs';

const args = argumentos({ ruta: '/prototipos/armeria-a', segundos: '8' });
const segundos = Number(args.segundos);
const { base, parar } = await servidor(args, args.ruta);
const browser = await navegador({ headless: !args.headed });

async function medirEscenario(nombre, contexto, accion) {
  const { cpu, ...opciones } = contexto;
  const context = await browser.newContext({ ...opciones, reducedMotion: 'no-preference' });
  const page = await context.newPage();
  if (cpu) {
    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
  }
  // Peso de lo que descarga la página, por tipo (JS y CSS también comprimidos con gzip -9).
  const recursos = {};
  const pendientes = [];
  page.on('response', (r) => {
    pendientes.push(
      (async () => {
        const tipo = r.request().resourceType();
        const cuerpo = await r.body().catch(() => null);
        if (!cuerpo) return;
        recursos[tipo] ??= { kb: 0, gzKb: 0, n: 0 };
        recursos[tipo].kb += cuerpo.length / 1024;
        recursos[tipo].n += 1;
        if (tipo === 'script' || tipo === 'stylesheet')
          recursos[tipo].gzKb += gzipSync(cuerpo, { level: 9 }).length / 1024;
      })(),
    );
  });
  const errores = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errores.push(m.text());
  });
  const t0 = Date.now();
  await page.goto(`${base}${args.ruta}?intro=0&medir`, { waitUntil: 'load' });
  const escena = await esperarEscena(page, 60_000);
  const listoEnMs = Date.now() - t0;
  if (!escena) {
    await context.close();
    return { nombre, escena: false, errores };
  }
  await pausa(2000);
  await page.evaluate(() => {
    const w = window;
    w.__medidas = [];
    let previo = performance.now();
    const tick = (t) => {
      w.__medidas.push(t - previo);
      previo = t;
      if (!w.__parar) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
  const fin = Date.now() + segundos * 1000;
  let i = 0;
  while (Date.now() < fin) {
    await accion(page, i++);
    await pausa(16);
  }
  const datos = await page.evaluate(() => {
    const w = window;
    w.__parar = true;
    const m = w.__medidas.slice(5).sort((a, b) => a - b);
    const media = m.reduce((s, d) => s + d, 0) / m.length;
    const pct = (p) => m[Math.min(m.length - 1, Math.floor(p * m.length))];
    const api = w.__armeria;
    return {
      fotogramas: m.length,
      fpsMedio: Math.round((1000 / media) * 10) / 10,
      msP50: Math.round(pct(0.5) * 10) / 10,
      msP95: Math.round(pct(0.95) * 10) / 10,
      gpu: api?.gpu?.() ?? null,
      dpr: api?.dpr?.() ?? null,
      info: api?.info?.() ?? null,
      cayoAlPoster: Boolean(document.querySelector('.armeria__aviso')),
    };
  });
  await Promise.all(pendientes);
  for (const r of Object.values(recursos)) {
    r.kb = Math.round(r.kb * 10) / 10;
    r.gzKb = Math.round(r.gzKb * 10) / 10;
  }
  await context.close();
  return { nombre, escena: true, listoEnMs, ...datos, recursos, errores };
}

const resultados = [];
try {
  resultados.push(
    await medirEscenario('escritorio-1440', ESCRITORIO, async (page, i) => {
      // Lissajous por la sala: linterna, deriva de cámara y cambios de zona.
      const t = i / 30;
      await page.mouse.move(720 + Math.sin(t * 1.3) * 560, 420 + Math.sin(t * 2.1) * 220);
    }),
  );
  resultados.push(
    await medirEscenario('movil-390-cpu4x', { ...MOVIL, cpu: 4 }, async (page, i) => {
      // Recorre el carrusel de zonas adelante y atrás: la cámara viaja por el pasillo.
      await page.evaluate((k) => {
        const nav = document.querySelector('.armeria__nav');
        if (!nav) return;
        const max = nav.scrollWidth - nav.clientWidth;
        nav.scrollLeft = ((Math.sin(k / 20) + 1) / 2) * max;
      }, i);
    }),
  );
} finally {
  await browser.close();
  parar();
}
const salida = { ruta: args.ruta, fecha: new Date().toISOString(), segundos, resultados };
console.log(JSON.stringify(salida, null, 2));
if (args.salida) writeFileSync(path.resolve(root, String(args.salida)), `${JSON.stringify(salida, null, 2)}\n`);
