// Lógica del lanzador del MCP de Playwright (sin E/S propia: se prueba con playwright.test.mjs).
//
// Por qué existe: `.mcp.json` usaba `cmd /c npx` y el canal `msedge`, que solo funcionan en Windows.
// Ahora Claude Code arranca `node .claude/mcp/playwright.mjs` en cualquier sistema, y este módulo
// decide el comando real:
//   - Windows: Microsoft Edge (canal `msedge`), que ya viene con el sistema.
//   - macOS y Linux: el Chromium de Playwright (canal `chrome-for-testing`).
// Se ejecuta npx con el mismo Node que corre el lanzador y sin shell: nada de `cmd /c` ni `.cmd`,
// y ningún argumento pasa por un intérprete de comandos.
//
// La configuración de seguridad (perfil aislado, orígenes permitidos y acceso a archivos) vive en
// `.claude/playwright-mcp.json`. @playwright/mcp aplica las variables PLAYWRIGHT_MCP_* por encima
// de ese archivo, así que se eliminan del entorno del proceso hijo salvo una lista blanca inocua.

import path from 'node:path';

/** Versión fijada: nunca `latest` ni rangos. Cambiarla es una decisión revisada (Renovate + PR). */
export const MCP_PACKAGE = '@playwright/mcp@0.0.83';

/** Configuración común a todas las plataformas, relativa a la raíz del proyecto. */
export const CONFIG_RELATIVE = ['.claude', 'playwright-mcp.json'];

/** Chromium preinstalado en los contenedores en la nube de Claude Code (Linux). */
export const CLOUD_CHROMIUM = '/opt/pw-browsers/chromium';

/** Variables PLAYWRIGHT_MCP_* que se respetan: no pueden relajar el aislamiento ni los orígenes. */
export const ENV_ALLOWED = new Set(['PLAYWRIGHT_MCP_EXECUTABLE_PATH', 'PLAYWRIGHT_MCP_HEADLESS']);

export class LaunchError extends Error {
  name = 'LaunchError';
}

const pathFor = (platform) => (platform === 'win32' ? path.win32 : path.posix);

/** Edge en Windows; Chromium de Playwright en el resto. */
export function browserFor(platform) {
  return platform === 'win32' ? 'msedge' : 'chromium';
}

/**
 * Busca `npx-cli.js` (el npx de npm en JavaScript) para ejecutarlo con `node`, sin shell.
 * Orden: junto al ejecutable de Node (instalador oficial, nvm, fnm, Volta) y después en el PATH.
 * @param {{ platform: string, execPath: string, pathEnv?: string, exists: (p: string) => boolean,
 *           realpath?: (p: string) => string }} opts
 * @returns {string | null}
 */
export function findNpxCli({ platform, execPath, pathEnv = '', exists, realpath = (p) => p }) {
  const p = pathFor(platform);
  const tail = ['node_modules', 'npm', 'bin', 'npx-cli.js'];
  const fromDir = (dir) => [
    p.join(dir, ...tail), // Windows: C:\Program Files\nodejs\node_modules\npm\bin\npx-cli.js
    p.join(dir, '..', 'lib', ...tail), // POSIX: <prefijo>/bin/node → <prefijo>/lib/node_modules/npm
  ];
  const candidates = fromDir(p.dirname(execPath));

  const delimiter = platform === 'win32' ? ';' : ':';
  const names = platform === 'win32' ? ['npx.cmd', 'npx.exe', 'npx'] : ['npx'];
  for (const dir of pathEnv.split(delimiter).filter(Boolean)) {
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
  return candidates.find((c) => exists(c)) ?? null;
}

/**
 * Entorno del proceso hijo: sin PLAYWRIGHT_MCP_* (salvo la lista blanca) y sin scripts de
 * instalación en lo que descargue npx. En Windows los nombres de variable no distinguen
 * mayúsculas, así que el filtro tampoco.
 * @param {Record<string, string | undefined>} env
 */
export function sanitizeEnv(env) {
  /** @type {Record<string, string>} */
  const out = {};
  for (const [key, value] of Object.entries(env)) {
    if (value === undefined) continue;
    const upper = key.toUpperCase();
    if (upper.startsWith('PLAYWRIGHT_MCP_') && !ENV_ALLOWED.has(upper)) continue;
    if (upper === 'NPM_CONFIG_IGNORE_SCRIPTS') continue;
    out[key] = value;
  }
  out.npm_config_ignore_scripts = 'true';
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

const ORIGIN = /^https?:\/\/(?:\[[0-9a-f:.]+\]|[a-z0-9.-]+)(?::(?:\d{1,5}|\*))?$/i;

/**
 * Falla cerrado si la configuración deja de aislar el navegador. No obliga a que sea solo
 * localhost (las capturas de la preview necesitarán su origen), pero sí exige una lista
 * explícita: una lista vacía o un comodín de host equivalen a «todo permitido».
 * @param {unknown} config
 */
export function assertSafeConfig(config) {
  const problems = [];
  const c = /** @type {any} */ (config);
  if (c?.browser?.isolated !== true) problems.push('browser.isolated debe ser true');
  if (c?.browser?.userDataDir) problems.push('browser.userDataDir no se admite (perfil persistente)');
  if (c?.allowUnrestrictedFileAccess === true) problems.push('allowUnrestrictedFileAccess debe ser false');
  if (c?.browser?.cdpEndpoint || c?.browser?.remoteEndpoint || c?.extension) {
    problems.push('no se admite conectar con un navegador existente (cdpEndpoint, remoteEndpoint, extension)');
  }
  const origins = c?.network?.allowedOrigins;
  if (!Array.isArray(origins) || origins.length === 0) {
    problems.push('network.allowedOrigins debe ser una lista no vacía');
  } else {
    for (const o of origins) {
      if (typeof o !== 'string' || !ORIGIN.test(o)) problems.push(`origen no válido o demasiado amplio: ${String(o)}`);
    }
  }
  if (problems.length) {
    throw new LaunchError(`.claude/playwright-mcp.json no es seguro: ${problems.join('; ')}.`);
  }
}

/**
 * Calcula el comando completo. Pura: todo lo que depende del sistema llega por parámetro.
 * @param {{ platform: string, execPath: string, env: Record<string, string | undefined>,
 *           root: string, exists: (p: string) => boolean, realpath?: (p: string) => string }} opts
 */
export function buildLaunch({ platform, execPath, env, root, exists, realpath }) {
  const p = pathFor(platform);
  const pathEnv = env.PATH ?? env.Path ?? env.path ?? '';
  const npxCli = findNpxCli({ platform, execPath, pathEnv, exists, realpath });
  if (!npxCli) {
    throw new LaunchError(
      'No encuentro npx (npm) junto a Node ni en el PATH. Reinstala Node.js con npm incluido y vuelve a abrir Claude Code.',
    );
  }
  const args = [
    npxCli,
    '--yes',
    MCP_PACKAGE,
    '--config',
    p.join(root, ...CONFIG_RELATIVE),
    '--browser',
    browserFor(platform),
  ];
  const executable = cloudExecutable({ platform, env, exists });
  if (executable) args.push('--executable-path', executable);
  return {
    command: execPath,
    args,
    options: { cwd: root, env: sanitizeEnv(env), stdio: 'inherit', shell: false, windowsHide: true },
  };
}
