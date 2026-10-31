// Integración de Astro: añade `X-Robots-Tag: noindex, nofollow` al bloque `/*` del `_headers` de la
// build cuando el entorno de Cloudflare no es producción (las previews no se indexan; docs/08 §6.2 y
// plan, decisión 16). El entorno sale de `vars.ENVIRONMENT` del wrangler.json que genera la propia
// build (el mismo que verá el Worker en ejecución): una sola fuente de verdad. Ante cualquier duda,
// noindex. Va DENTRO del bloque existente: con dos bloques `/*`, Cloudflare aplica solo uno.
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import type { AstroIntegration } from 'astro';

export const ROBOTS_LINE = '  X-Robots-Tag: noindex, nofollow';

/** Inserta la cabecera tras la línea `/*`. Falla si no existe ese bloque (sería un error de build). */
export function withNoIndex(headersFile: string): string {
  const lines = headersFile.split(/\r?\n/);
  const block = lines.findIndex((l) => l.trim() === '/*');
  if (block === -1) throw new Error('public/_headers no tiene un bloque /*');
  if (lines.includes(ROBOTS_LINE)) return headersFile;
  lines.splice(block + 1, 0, ROBOTS_LINE);
  return lines.join('\n');
}

/** Entorno de la build: `vars.ENVIRONMENT` de dist/server/wrangler.json, o `desconocido`. */
export async function buildEnvironment(clientDir: URL): Promise<string> {
  try {
    const config: unknown = JSON.parse(await readFile(new URL('../server/wrangler.json', clientDir), 'utf8'));
    const vars = (config as { vars?: Record<string, unknown> } | null)?.vars;
    const value = vars?.['ENVIRONMENT'];
    return typeof value === 'string' && value ? value : 'desconocido';
  } catch {
    return 'desconocido';
  }
}

export default function securityHeaders(): AstroIntegration {
  return {
    name: 'taller6mm:security-headers',
    hooks: {
      'astro:build:done': async ({ dir, logger }) => {
        const environment = await buildEnvironment(dir);
        if (environment === 'production') return;
        const file = fileURLToPath(new URL('_headers', dir));
        await writeFile(file, withNoIndex(await readFile(file, 'utf8')));
        logger.info(`X-Robots-Tag: noindex añadido a _headers (entorno «${environment}»).`);
      },
    },
  };
}
