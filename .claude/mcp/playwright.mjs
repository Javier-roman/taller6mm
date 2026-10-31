#!/usr/bin/env node
// Lanzador multiplataforma del MCP de Playwright de Taller6mm (lo arranca Claude Code desde .mcp.json).
// La lógica está en playwright-launch.mjs; aquí solo hay E/S.
//
// IMPORTANTE: stdout es el canal del protocolo MCP. Este script no escribe nada en stdout salvo con
// `--print`, que muestra el comando resuelto (sin variables de entorno) y sale sin arrancar nada:
//   node .claude/mcp/playwright.mjs --print
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, realpathSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { assertSafeConfig, buildLaunch, CONFIG_RELATIVE, droppedEnvNames, LaunchError } from './playwright-launch.mjs';

// La raíz se deduce de la ubicación del script, no del directorio actual ni de variables de entorno.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const log = (message) => process.stderr.write(`[taller6mm/playwright-mcp] ${message}\n`);
const fail = (message) => {
  log(message);
  process.exit(1);
};

let launch;
try {
  const raw = readFileSync(path.join(root, ...CONFIG_RELATIVE), 'utf8');
  assertSafeConfig(JSON.parse(raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw));
  launch = buildLaunch({
    platform: process.platform,
    execPath: process.execPath,
    env: process.env,
    root,
    home: os.homedir(),
    uid: typeof process.getuid === 'function' ? process.getuid() : -1,
    exists: existsSync,
    realpath: realpathSync,
  });
} catch (error) {
  fail(error instanceof LaunchError || error instanceof SyntaxError ? error.message : String(error));
}

if (process.argv.includes('--print')) {
  const { command, args, warnings, options } = launch;
  process.stdout.write(`${JSON.stringify({ command, args, cwd: options.cwd, warnings }, null, 2)}\n`);
  process.exit(0);
}

const dropped = droppedEnvNames(process.env);
if (dropped.length) log(`Ignoro ${dropped.join(', ')}: la configuración está en ${CONFIG_RELATIVE.join('/')}.`);
for (const warning of launch.warnings) log(warning);

try {
  mkdirSync(launch.options.cwd, { recursive: true, mode: 0o700 });
} catch (error) {
  fail(
    `No puedo crear el directorio de trabajo ${launch.options.cwd}: ${error instanceof Error ? error.message : error}`,
  );
}

const child = spawn(launch.command, launch.args, launch.options);
child.on('error', (error) => fail(`No se pudo arrancar @playwright/mcp: ${error.message}`));
child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)));

// Reenvío de señales. En Windows solo existen SIGINT/SIGTERM/SIGKILL para `kill()`: se traduce a
// SIGTERM. Si algo falla, el cierre de stdin basta: @playwright/mcp cierra el navegador al detectarlo.
for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
  process.on(signal, () => {
    if (child.exitCode !== null) return;
    try {
      child.kill(process.platform === 'win32' ? 'SIGTERM' : signal);
    } catch {
      // Sin más: el proceso hijo termina al cerrarse stdin.
    }
  });
}
