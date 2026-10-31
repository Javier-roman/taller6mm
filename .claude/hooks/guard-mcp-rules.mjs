// Reglas del hook guardián del MCP de Playwright (lógica pura: se prueba con guard-mcp.test.mjs).
//
// Varias herramientas de @playwright/mcp leen o escriben archivos (`filename` en capturas, PDF,
// consola, red, trazas o estado de almacenamiento; `paths` al subir o soltar archivos). Esas rutas
// no pasan por las reglas `deny` de lectura ni por las rutas protegidas de Claude Code, así que
// una página con instrucciones inyectadas podría pedir que se lea `.dev.vars` o que se reescriba
// la configuración del propio MCP. Aquí solo se permiten rutas dentro de dos carpetas de salida.
import path from 'node:path';

/** Carpetas (relativas a la raíz del repo) donde el MCP puede leer y escribir. */
// Como segmentos: se unen con el separador de la plataforma que se evalúa, no con el del sistema que
// ejecuta (en Windows, `path.join` del sistema metería barras invertidas en rutas POSIX).
export const MCP_DIRS = [['.playwright-mcp'], ['docs', 'informes', 'capturas']];

/** Herramientas que nunca se usan: ejecutan código arbitrario en Node o suben archivos. */
const DENIED_TOOLS = new Set(['browser_run_code_unsafe', 'browser_file_upload']);

/** Parámetros con rutas de archivo en @playwright/mcp 0.0.83. */
const PATH_KEYS = new Set(['filename', 'paths']);

const deny = (reason) => ['deny', reason];

function isInside(child, parent, platform) {
  const p = platform === 'win32' ? path.win32 : path.posix;
  const norm = (s) => (platform === 'win32' ? s.toLowerCase() : s);
  const rel = p.relative(norm(p.resolve(parent)), norm(p.resolve(child)));
  return rel === '' || (!rel.startsWith('..') && !p.isAbsolute(rel));
}

/**
 * Devuelve ['deny', motivo] o null (sigue el flujo normal de permisos).
 * @param {string} toolName p. ej. `mcp__playwright__browser_take_screenshot`
 * @param {unknown} toolInput
 * @param {string} root raíz del proyecto
 * @param {string} [platform]
 */
export function checkMcp(toolName, toolInput, root, platform = process.platform) {
  const name = String(toolName ?? '').replace(/^mcp__[^_]+(?:_[^_]+)*?__/, '');
  if (DENIED_TOOLS.has(name)) {
    return deny(`${name} está bloqueada en Taller6mm: ejecuta código en Node o sube archivos locales.`);
  }
  if (typeof toolInput !== 'object' || toolInput === null) return null;

  const p = platform === 'win32' ? path.win32 : path.posix;
  const allowed = MCP_DIRS.map((segments) => p.join(root, ...segments));
  for (const [key, value] of Object.entries(toolInput)) {
    if (!PATH_KEYS.has(key)) continue;
    const values = Array.isArray(value) ? value : [value];
    for (const v of values) {
      if (typeof v !== 'string' || v.trim() === '') return deny(`Ruta no válida en «${key}».`);
      const resolved = p.resolve(root, v);
      if (!allowed.some((dir) => isInside(resolved, dir, platform) && resolved !== p.resolve(dir))) {
        return deny(
          `El MCP de Playwright solo puede leer o escribir archivos dentro de ${MCP_DIRS.map((d) => d.join('/')).join(' o ')} (pedido: ${v}).`,
        );
      }
    }
  }
  return null;
}
