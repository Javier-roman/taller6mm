#!/usr/bin/env node
// Hook PostToolUse (Write|Edit) de Taller6mm.
// Formatea y aplica correcciones seguras al archivo recién editado:
//   - Biome para TS/JS/JSON/CSS/Astro
//   - Ruff para Python (apps/pipeline)
// Si quedan avisos, se los pasa a Claude como contexto para que los corrija.
// Nunca bloquea: si la herramienta aún no está instalada (Fase 0) o algo falla, no hace nada.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';

const BIOME_EXT = new Set([
  '.ts',
  '.tsx',
  '.mts',
  '.cts',
  '.js',
  '.jsx',
  '.mjs',
  '.cjs',
  '.json',
  '.jsonc',
  '.css',
  '.astro',
]);

// Lectura asíncrona de stdin: readFileSync(0) puede fallar con tuberías en Windows.
async function readStdin(ms = 5000) {
  const chunks = [];
  const reading = (async () => {
    for await (const chunk of process.stdin) chunks.push(chunk);
  })().catch(() => {});
  let timer;
  await Promise.race([reading, new Promise((resolve) => (timer = setTimeout(resolve, ms)))]);
  clearTimeout(timer);
  process.stdin.destroy();
  return Buffer.concat(chunks).toString('utf8');
}

function warnings(root, file, result) {
  if (!result || result.status === 0) return null;
  const out = `${result.stdout ?? ''}${result.stderr ?? ''}`.trim().slice(0, 3000);
  if (!out) return null;
  return {
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext: `El formateador/linter dejó avisos en ${path.relative(root, file)}. Corrígelos:\n${out}`,
    },
  };
}

let output = null;
try {
  const input = JSON.parse(await readStdin());
  const file = input?.tool_input?.file_path;
  if (file && existsSync(file)) {
    const root = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
    const ext = path.extname(file).toLowerCase();
    const opts = { cwd: root, encoding: 'utf8', timeout: 50_000, windowsHide: true };

    if (BIOME_EXT.has(ext)) {
      // Se invoca el lanzador JS de Biome con node: funciona igual en Windows, macOS y Linux.
      const biome = path.join(root, 'node_modules', '@biomejs', 'biome', 'bin', 'biome');
      if (existsSync(biome)) {
        output = warnings(
          root,
          file,
          spawnSync(process.execPath, [biome, 'check', '--write', '--no-errors-on-unmatched', file], opts),
        );
      }
    } else if (ext === '.py') {
      const ruff = [
        path.join(root, 'apps', 'pipeline', '.venv', 'Scripts', 'ruff.exe'),
        path.join(root, 'apps', 'pipeline', '.venv', 'bin', 'ruff'),
      ].find((p) => existsSync(p));
      if (ruff) {
        spawnSync(ruff, ['format', file], opts);
        output = warnings(root, file, spawnSync(ruff, ['check', '--fix', file], opts));
      }
    }
  }
} catch {
  // Un fallo del hook nunca debe bloquear el trabajo.
}

if (output) process.stdout.write(JSON.stringify(output));
