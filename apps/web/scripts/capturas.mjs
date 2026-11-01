#!/usr/bin/env node
// Capturas de una página a 390, 834 y 1440 px, con y sin movimiento reducido, en
// docs/informes/capturas/ (revisión de diseño: /revisar-ui y critico-diseno).
// Requiere `pnpm build`. Arranca la build en workerd (scripts/serve-web.mjs) y la para al acabar.
// Uso: node scripts/capturas.mjs [ruta=/sistema] [prefijo=sistema]
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..');
const ruta = process.argv[2] ?? '/sistema';
const prefijo = process.argv[3] ?? 'sistema';
const port = 4399;
const base = `http://127.0.0.1:${port}`;
const outDir = path.join(root, 'docs', 'informes', 'capturas');
const ANCHOS = [
  { ancho: 390, alto: 844 },
  { ancho: 834, alto: 1112 },
  { ancho: 1440, alto: 900 },
];

// Mismo criterio que playwright.config.ts para elegir el navegador.
const { CLAUDE_CODE_REMOTE, PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } = process.env;
const cloud = '/opt/pw-browsers/chromium';
const executablePath =
  PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? (CLAUDE_CODE_REMOTE === 'true' && existsSync(cloud) ? cloud : undefined);

async function waitFor(url, ms = 90_000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // Aún arrancando.
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`El servidor no respondió en ${ms / 1000} s:\n${log}`);
}

const server = spawn(process.execPath, [path.join(root, 'scripts', 'serve-web.mjs'), String(port)], {
  cwd: root,
  stdio: ['ignore', 'pipe', 'pipe'],
  detached: process.platform !== 'win32',
});
let log = '';
for (const stream of [server.stdout, server.stderr]) {
  stream.on('data', (d) => {
    log = (log + d).slice(-4000);
  });
}
const stop = () => {
  try {
    if (process.platform === 'win32') server.kill();
    else if (server.pid) process.kill(-server.pid, 'SIGTERM');
  } catch {
    // Ya terminó.
  }
};

let failed = false;
try {
  await waitFor(`${base}${ruta}`);
  mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch(executablePath ? { executablePath } : {});
  for (const reducido of [false, true]) {
    for (const { ancho, alto } of ANCHOS) {
      const context = await browser.newContext({
        viewport: { width: ancho, height: alto },
        reducedMotion: reducido ? 'reduce' : 'no-preference',
        colorScheme: 'dark',
      });
      const page = await context.newPage();
      const errores = [];
      page.on('console', (m) => m.type() === 'error' && errores.push(m.text()));
      await page.goto(`${base}${ruta}`, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const file = path.join(outDir, `${prefijo}-${ancho}${reducido ? '-reducido' : ''}.png`);
      await page.screenshot({ path: file, fullPage: true });
      console.log(`✔ ${path.relative(root, file)}${errores.length ? ` · ${errores.length} errores de consola` : ''}`);
      for (const e of errores) console.log(`   ✘ ${e}`);
      if (errores.length) failed = true;
      await context.close();
    }
  }
  await browser.close();
} finally {
  stop();
}
process.exit(failed ? 1 : 0);
