// Utilidades de los scripts de los prototipos de La Armería (Fase 1): servidor, navegador y esperas.
// Por defecto sirven la build en workerd (como scripts/capturas.mjs); con --base usan un servidor ya
// arrancado (p. ej. `pnpm dev`). El navegador es Edge (canal msedge) si está, como el MCP de Playwright.
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const here = path.dirname(fileURLToPath(import.meta.url));
export const root = path.resolve(here, '..', '..', '..', '..');
export const webDir = path.resolve(here, '..', '..');

/** `--clave valor` y `--bandera` a un objeto, sobre unos valores por defecto. */
export function argumentos(defectos) {
  const args = { ...defectos };
  const lista = process.argv.slice(2);
  for (let i = 0; i < lista.length; i++) {
    const a = lista[i];
    if (!a?.startsWith('--')) continue;
    const clave = a.slice(2);
    const sig = lista[i + 1];
    if (sig === undefined || sig.startsWith('--')) args[clave] = true;
    else {
      args[clave] = sig;
      i++;
    }
  }
  return args;
}

async function esperarUrl(url, ms, log) {
  const fin = Date.now() + ms;
  while (Date.now() < fin) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // Aún arrancando.
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`El servidor no respondió en ${ms / 1000} s:\n${log()}`);
}

/** Devuelve { base, parar }. Sin --base, sirve la build en workerd (requiere `pnpm build`). */
export async function servidor(args, ruta) {
  if (args.base) return { base: String(args.base).replace(/\/$/, ''), parar: () => undefined };
  const puerto = Number(args.puerto ?? 4398);
  const hijo = spawn(process.execPath, [path.join(root, 'scripts', 'serve-web.mjs'), String(puerto)], {
    cwd: root,
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: process.platform !== 'win32',
  });
  let log = '';
  for (const s of [hijo.stdout, hijo.stderr]) {
    s.on('data', (d) => {
      log = (log + d).slice(-4000);
    });
  }
  const parar = () => {
    try {
      if (process.platform === 'win32') hijo.kill();
      else if (hijo.pid) process.kill(-hijo.pid, 'SIGTERM');
    } catch {
      // Ya terminó.
    }
  };
  const base = `http://127.0.0.1:${puerto}`;
  try {
    await esperarUrl(`${base}${ruta}`, 120_000, () => log);
  } catch (e) {
    parar();
    throw e;
  }
  return { base, parar };
}

export async function navegador({ headless = true } = {}) {
  const { CLAUDE_CODE_REMOTE, PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } = process.env;
  const nube = '/opt/pw-browsers/chromium';
  const executablePath =
    PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? (CLAUDE_CODE_REMOTE === 'true' && existsSync(nube) ? nube : undefined);
  const opciones = { headless, args: ['--ignore-gpu-blocklist'] };
  if (executablePath) return chromium.launch({ ...opciones, executablePath });
  try {
    return await chromium.launch({ ...opciones, channel: 'msedge' });
  } catch {
    return chromium.launch(opciones);
  }
}

export const ESCRITORIO = { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 };
export const MOVIL = {
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 3,
  isMobile: true,
  hasTouch: true,
  userAgent:
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36',
};

/** Espera a que la escena (A o B) haya pintado; si cae al póster, devuelve false. */
export async function esperarEscena(page, ms = 30_000) {
  try {
    await page.waitForSelector('[data-listo="true"]', { timeout: ms });
    return true;
  } catch {
    return false;
  }
}

export const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
