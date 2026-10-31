// Lógica del lanzador del MCP de Playwright (sin E/S propia: se prueba con playwright.test.mjs).
//
// Por qué existe: `.mcp.json` usaba `cmd /c npx` y el canal `msedge`, que solo funcionan en Windows.
// Ahora Claude Code arranca `node .claude/mcp/playwright.mjs` en cualquier sistema, y este módulo
// decide el comando real:
//   - Windows: Microsoft Edge (canal `msedge`), que ya viene con el sistema.
//   - macOS y Linux: el Chromium de Playwright (canal `chrome-for-testing`), con el sandbox activo.
// El lanzador ejecuta npx con el mismo Node, sin shell propia y desde un directorio de trabajo fuera
// del repo (npx sí usa una shell para arrancar el binario; ver la revisión de seguridad del PR).
//
// La configuración de seguridad vive en `.claude/playwright-mcp.json` y se valida con una lista
// blanca estricta. @playwright/mcp aplica las variables PLAYWRIGHT_MCP_* por encima de ese archivo,
// así que se eliminan del entorno del proceso hijo salvo dos inocuas.

import path from 'node:path';

/** Versión fijada: nunca `latest` ni rangos. Cambiarla es una decisión revisada en un PR. */
export const MCP_PACKAGE = '@playwright/mcp@0.0.83';

/** Configuración común a todas las plataformas, relativa a la raíz del proyecto. */
export const CONFIG_RELATIVE = ['.claude', 'playwright-mcp.json'];

/** Chromium preinstalado en los contenedores en la nube de Claude Code (Linux). */
export const CLOUD_CHROMIUM = '/opt/pw-browsers/chromium';

/** Variables PLAYWRIGHT_MCP_* que se respetan: no pueden relajar el aislamiento ni los orígenes. */
export const ENV_ALLOWED = new Set(['PLAYWRIGHT_MCP_EXECUTABLE_PATH', 'PLAYWRIGHT_MCP_HEADLESS']);

/** Desactiva a propósito el sandbox de Chromium en Linux (distros sin espacios de nombres de usuario). */
export const NO_SANDBOX_ENV = 'TALLER6MM_MCP_NO_SANDBOX';

export class LaunchError extends Error {
  name = 'LaunchError';
}

const pathFor = (platform) => (platform === 'win32' ? path.win32 : path.posix);

/** ¿Está `child` dentro de `parent` (o es el mismo)? Sin distinguir mayúsculas en Windows. */
export function isInside(child, parent, platform) {
  const p = pathFor(platform);
  const norm = (s) => (platform === 'win32' ? s.toLowerCase() : s);
  const rel = p.relative(norm(p.resolve(parent)), norm(p.resolve(child)));
  return rel === '' || (!rel.startsWith('..') && !p.isAbsolute(rel));
}

/** Edge en Windows; Chromium de Playwright en el resto. */
export function browserFor(platform) {
  return platform === 'win32' ? 'msedge' : 'chromium';
}

/**
 * Busca `npx-cli.js` (el npx de npm en JavaScript) para ejecutarlo con `node`.
 * Orden: junto al ejecutable de Node (instalador oficial, nvm, fnm, Volta) y después en el PATH.
 * Ignora las entradas relativas del PATH y cualquier candidato dentro del repo: un `npx-cli.js`
 * plantado en el proyecto nunca se ejecuta.
 * @param {{ platform: string, execPath: string, pathEnv?: string, root: string,
 *           exists: (p: string) => boolean, realpath?: (p: string) => string }} opts
 * @returns {string | null}
 */
export function findNpxCli({ platform, execPath, pathEnv = '', root, exists, realpath = (p) => p }) {
  const p = pathFor(platform);
  const tail = ['node_modules', 'npm', 'bin', 'npx-cli.js'];
  const fromDir = (dir) => [
    p.join(dir, ...tail), // Windows: C:\Program Files\nodejs\node_modules\npm\bin\npx-cli.js
    p.join(dir, '..', 'lib', ...tail), // POSIX: <prefijo>/bin/node → <prefijo>/lib/node_modules/npm
  ];
  const candidates = p.isAbsolute(execPath) ? fromDir(p.dirname(execPath)) : [];

  const delimiter = platform === 'win32' ? ';' : ':';
  const names = platform === 'win32' ? ['npx.cmd', 'npx.exe', 'npx'] : ['npx'];
  for (const dir of pathEnv.split(delimiter).filter((d) => d && p.isAbsolute(d))) {
    for (const name of names) {
      const entry = p.join(dir, name);
      if (!exists(entry)) continue;
      try {
        // En POSIX `npx` suele ser un enlace a .../npm/bin/npx-cli.js.
        const real = realpath(entry);
        if (real.endsWith('npx-cli.js')) candidates.push(real);
      } catch {
        // Enlace roto: se prueban las rutas derivadas del directorio.
      }
      candidates.push(...fromDir(dir));
    }
  }
  return candidates.find((c) => !isInside(c, root, platform) && exists(c)) ?? null;
}

/**
 * Entorno del proceso hijo: sin PLAYWRIGHT_MCP_* (salvo la lista blanca), sin scripts de
 * instalación en lo que descargue npx y, en Windows, sin buscar ejecutables en el directorio
 * actual. En Windows los nombres de variable no distinguen mayúsculas, así que el filtro tampoco.
 * @param {Record<string, string | undefined>} env
 * @param {string} platform
 */
export function sanitizeEnv(env, platform) {
  /** @type {Record<string, string>} */
  const out = {};
  for (const [key, value] of Object.entries(env)) {
    if (value === undefined) continue;
    const upper = key.toUpperCase();
    if (upper.startsWith('PLAYWRIGHT_MCP_') && !ENV_ALLOWED.has(upper)) continue;
    if (upper === 'NPM_CONFIG_IGNORE_SCRIPTS' || upper === 'NODEFAULTCURRENTDIRECTORYINEXEPATH') continue;
    out[key] = value;
  }
  out.npm_config_ignore_scripts = 'true';
  if (platform === 'win32') out.NoDefaultCurrentDirectoryInExePath = '1';
  return out;
}

/** Variables PLAYWRIGHT_MCP_* que se descartarían (para avisar por stderr, sin sus valores). */
export function droppedEnvNames(env) {
  return Object.keys(env).filter((k) => {
    const upper = k.toUpperCase();
    return upper.startsWith('PLAYWRIGHT_MCP_') && !ENV_ALLOWED.has(upper);
  });
}

/**
 * En la nube de Claude Code el Chromium de Playwright ya está instalado, pero con otra revisión
 * que la que pide @playwright/mcp; se usa ese binario salvo que el usuario indique otro.
 */
export function cloudExecutable({ platform, env, exists }) {
  if (platform !== 'linux' || env.CLAUDE_CODE_REMOTE !== 'true') return null;
  if (env.PLAYWRIGHT_MCP_EXECUTABLE_PATH) return null;
  return exists(CLOUD_CHROMIUM) ? CLOUD_CHROMIUM : null;
}

/**
 * Sandbox de Chromium. Con el canal `chrome-for-testing`, @playwright/mcp lo desactiva en Linux;
 * aquí se fuerza con `--sandbox` salvo como root (Chromium no lo admite) o si el usuario lo
 * desactiva a propósito. En Windows y macOS ya está activo.
 * @returns {{ args: string[], warning: string | null }}
 */
export function sandboxArgs({ platform, uid, env }) {
  if (platform !== 'linux') return { args: [], warning: null };
  if (env[NO_SANDBOX_ENV] === '1') {
    return { args: [], warning: `Chromium sin sandbox porque ${NO_SANDBOX_ENV}=1.` };
  }
  if (uid === 0) {
    return { args: [], warning: 'Chromium sin sandbox: la sesión corre como root (solo aceptable en un contenedor).' };
  }
  return { args: ['--sandbox'], warning: null };
}

/**
 * Directorio de trabajo del proceso hijo, fuera del repo: así ni npx ni la shell que usa para
 * arrancar el binario encuentran nada plantado en el proyecto.
 */
export function workDirFor({ platform, env, home, root }) {
  const p = pathFor(platform);
  const leaf = ['taller6mm', 'playwright-mcp'];
  let base;
  if (platform === 'win32') base = env.LOCALAPPDATA ?? p.join(home, 'AppData', 'Local');
  else if (platform === 'darwin') base = p.join(home, 'Library', 'Caches');
  else base = env.XDG_CACHE_HOME && p.isAbsolute(env.XDG_CACHE_HOME) ? env.XDG_CACHE_HOME : p.join(home, '.cache');
  const dir = p.join(base, ...leaf);
  if (!p.isAbsolute(dir) || isInside(dir, root, platform)) {
    throw new LaunchError('El directorio de trabajo del MCP no puede estar dentro del repo.');
  }
  return dir;
}

const ORIGIN = /^https?:\/\/(?:\[[0-9a-f:.]+\]|[a-z0-9.-]+)(?::(?:\d{1,5}|\*))?$/i;
const isPlainObject = (v) => typeof v === 'object' && v !== null && !Array.isArray(v);

/**
 * Lista blanca estricta de `.claude/playwright-mcp.json`: solo se admiten estas claves, con estos
 * tipos. Cualquier otra (servidor HTTP, scripts de inicio, opciones de lanzamiento, capacidades
 * extra, perfiles…) hace que el lanzador no arranque. Fallar cerrado es la idea.
 * @param {unknown} config
 */
export function assertSafeConfig(config) {
  const problems = [];
  const unknownKeys = (obj, allowed, prefix) => {
    for (const key of Object.keys(obj)) if (!allowed.includes(key)) problems.push(`clave no admitida: ${prefix}${key}`);
  };

  if (!isPlainObject(config)) {
    throw new LaunchError('.claude/playwright-mcp.json no es seguro: debe ser un objeto JSON.');
  }
  const c = /** @type {Record<string, unknown>} */ (config);
  unknownKeys(c, ['browser', 'network', 'allowUnrestrictedFileAccess'], '');

  const browser = c.browser;
  if (!isPlainObject(browser)) problems.push('browser debe ser un objeto');
  else {
    unknownKeys(browser, ['browserName', 'isolated'], 'browser.');
    if (browser.isolated !== true) problems.push('browser.isolated debe ser true');
    if ('browserName' in browser && browser.browserName !== 'chromium')
      problems.push('browser.browserName debe ser "chromium"');
  }

  const network = c.network;
  if (!isPlainObject(network)) problems.push('network debe ser un objeto');
  else {
    unknownKeys(network, ['allowedOrigins'], 'network.');
    const origins = network.allowedOrigins;
    if (!Array.isArray(origins) || origins.length === 0) {
      problems.push('network.allowedOrigins debe ser una lista no vacía');
    } else {
      for (const o of origins) {
        if (typeof o !== 'string' || !ORIGIN.test(o))
          problems.push(`origen no válido o demasiado amplio: ${String(o)}`);
      }
    }
  }

  if ('allowUnrestrictedFileAccess' in c && c.allowUnrestrictedFileAccess !== false) {
    problems.push('allowUnrestrictedFileAccess debe ser false (booleano) o no aparecer');
  }

  if (problems.length) {
    throw new LaunchError(`.claude/playwright-mcp.json no es seguro: ${problems.join('; ')}.`);
  }
}

/**
 * Calcula el comando completo. Pura: todo lo que depende del sistema llega por parámetro.
 * @param {{ platform: string, execPath: string, env: Record<string, string | undefined>, root: string,
 *           home: string, uid?: number, exists: (p: string) => boolean, realpath?: (p: string) => string }} opts
 */
export function buildLaunch({ platform, execPath, env, root, home, uid = -1, exists, realpath }) {
  const p = pathFor(platform);
  const pathEnv = env.PATH ?? env.Path ?? env.path ?? '';
  const npxCli = findNpxCli({ platform, execPath, pathEnv, root, exists, realpath });
  if (!npxCli) {
    throw new LaunchError(
      'No encuentro npx (npm) junto a Node ni en el PATH. Reinstala Node.js con npm incluido y vuelve a abrir Claude Code.',
    );
  }
  const sandbox = sandboxArgs({ platform, uid, env });
  const args = [
    npxCli,
    '--yes',
    MCP_PACKAGE,
    '--config',
    p.join(root, ...CONFIG_RELATIVE),
    '--browser',
    browserFor(platform),
    ...sandbox.args,
  ];
  const executable = cloudExecutable({ platform, env, exists });
  if (executable) args.push('--executable-path', executable);
  return {
    command: execPath,
    args,
    warnings: sandbox.warning ? [sandbox.warning] : [],
    options: {
      cwd: workDirFor({ platform, env, home, root }),
      env: sanitizeEnv(env, platform),
      stdio: 'inherit',
      shell: false,
      windowsHide: true,
    },
  };
}
