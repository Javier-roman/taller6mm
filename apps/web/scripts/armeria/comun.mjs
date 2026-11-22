// Utilidades de los scripts de horneado de La Armería: un servidor de Vite aparte (solo para el horno, no es la
// web: sirve las páginas de scripts/armeria/horno y los pases de assets-src/vistas/armeria) y el navegador.
// El navegador es Edge (canal msedge) si está, como el MCP de Playwright; si no, el Chromium de Playwright.
import { createReadStream, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';
import { createServer } from 'vite';

const aqui = path.dirname(fileURLToPath(import.meta.url));
export const webDir = path.resolve(aqui, '..', '..');
export const raiz = path.resolve(webDir, '..', '..');
/** Carpeta de los binarios de las vistas (fuera de git; en git solo el manifiesto). */
export const carpetaVistas = path.join(raiz, 'assets-src', 'vistas', 'armeria');

/** `--clave valor` y `--bandera` a un objeto, sobre unos valores por defecto. */
export function argumentos(defectos = {}) {
  const args = { ...defectos };
  const lista = process.argv.slice(2);
  for (let i = 0; i < lista.length; i++) {
    const a = lista[i];
    if (!a?.startsWith('--')) continue;
    const sig = lista[i + 1];
    if (sig === undefined || sig.startsWith('--')) args[a.slice(2)] = true;
    else {
      args[a.slice(2)] = sig;
      i++;
    }
  }
  return args;
}

// Solo archivos .webp con nombre simple: el servidor del horno nunca sale de la carpeta de vistas.
const PASE = /^\/([a-z0-9][a-z0-9-]*\.webp)$/;

/** Arranca Vite sobre scripts/armeria/horno. Devuelve la URL base y cómo pararlo. */
export async function servidorHorno() {
  const servidor = await createServer({
    root: path.join(aqui, 'horno'),
    configFile: false,
    logLevel: 'warn',
    clearScreen: false,
    esbuild: { jsx: 'automatic' },
    server: { host: '127.0.0.1', port: 0, fs: { allow: [raiz] } },
    plugins: [
      {
        name: 'pases-armeria',
        configureServer(vite) {
          vite.middlewares.use('/pases', (req, res, next) => {
            const m = PASE.exec(new URL(req.url ?? '/', 'http://x').pathname);
            const archivo = m ? path.join(carpetaVistas, m[1]) : null;
            if (!archivo || !existsSync(archivo)) return next();
            res.setHeader('content-type', 'image/webp');
            createReadStream(archivo).pipe(res);
          });
        },
      },
    ],
  });
  await servidor.listen();
  const base = (servidor.resolvedUrls?.local?.[0] ?? '').replace(/\/$/, '');
  if (!base) throw new Error('El servidor del horno no devolvió su URL');
  return { base, parar: () => servidor.close() };
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

export const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
