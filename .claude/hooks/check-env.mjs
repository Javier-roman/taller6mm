#!/usr/bin/env node
// Hook SessionStart de Taller6mm: avisa de problemas del entorno antes de empezar a trabajar.
//   - Sesión con privilegios de administrador (Windows) o de root (macOS/Linux)
//   - Proyecto dentro de OneDrive (bloquea archivos de node_modules al sincronizar)
//   - Versión mayor de Node distinta de la fijada en .node-version
//   - Falta pnpm o gitleaks (este último lo usa el pre-commit)
// Nunca bloquea: si algo falla, no dice nada.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

async function readStdin(ms = 3000) {
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

function isElevated() {
  try {
    if (process.platform === 'win32') {
      // S-1-16-12288 = nivel de integridad alto (proceso elevado). No depende del idioma de Windows.
      const r = spawnSync('whoami', ['/groups', '/fo', 'csv', '/nh'], {
        encoding: 'utf8',
        timeout: 5000,
        windowsHide: true,
      });
      return r.status === 0 && /S-1-16-12288/.test(r.stdout ?? '');
    }
    return typeof process.getuid === 'function' && process.getuid() === 0;
  } catch {
    return false;
  }
}

// Busca un ejecutable en el PATH sin lanzar una shell (en Windows, con las extensiones de PATHEXT).
function onPath(name) {
  const exts = process.platform === 'win32' ? (process.env.PATHEXT ?? '.EXE;.CMD;.BAT').split(';') : [''];
  return (process.env.PATH ?? '')
    .split(path.delimiter)
    .filter(Boolean)
    .some((dir) => exts.some((ext) => existsSync(path.join(dir, name + ext.toLowerCase())) || existsSync(path.join(dir, name + ext))));
}

const warnings = [];
try {
  let input = {};
  try {
    input = JSON.parse(await readStdin());
  } catch {
    // Sin entrada: se usa el directorio actual.
  }
  const dir = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
  const norm = (p) => p.replace(/\\/g, '/').toLowerCase();

  if (isElevated()) {
    warnings.push(
      'La sesión tiene privilegios de administrador: cierra Claude Code y ábrelo desde una terminal normal (sin «Ejecutar como administrador»).',
    );
  }

  const oneDriveRoots = [process.env.OneDrive, process.env.OneDriveCommercial, process.env.OneDriveConsumer].filter(Boolean);
  if (oneDriveRoots.some((r) => norm(dir).startsWith(norm(r))) || /\/onedrive\b/.test(norm(dir))) {
    warnings.push(
      'El proyecto está dentro de OneDrive, que bloquea archivos de node_modules al sincronizar (errores EPERM o EBUSY): muévelo a una ruta como C:\\dev\\.',
    );
  }

  const pinFile = path.join(dir, '.node-version');
  const pinned = existsSync(pinFile) ? readFileSync(pinFile, 'utf8').trim().replace(/^v/, '') : '22';
  const wantMajor = Number(pinned.split('.')[0]);
  const haveMajor = Number(process.versions.node.split('.')[0]);
  if (Number.isFinite(wantMajor) && haveMajor !== wantMajor) {
    warnings.push(`Node.js ${process.versions.node}: el proyecto fija Node ${pinned} en .node-version.`);
  }

  if (!onPath('pnpm')) warnings.push('No encuentro pnpm en el PATH: instálalo con `npm install --global pnpm`.');
  if (!onPath('gitleaks')) {
    warnings.push('No encuentro gitleaks (lo usa el pre-commit): instálalo con `winget install --id Gitleaks.Gitleaks --exact`.');
  }
} catch {
  // Nunca bloquear.
}

if (warnings.length) {
  const text = warnings.join(' ');
  process.stdout.write(
    JSON.stringify({
      systemMessage: `⚠ Entorno de Taller6mm: ${text}`,
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: `Avisos de entorno detectados al iniciar la sesión: ${text} Según CLAUDE.md, mientras haya privilegios de administrador no se instalan dependencias ni se ejecutan scripts del proyecto.`,
      },
    }),
  );
}
