#!/usr/bin/env node
// Lanzador multiplataforma del MCP de Playwright de Taller6mm (lo arranca Claude Code desde .mcp.json).
// La lógica está en playwright-launch.mjs; aquí solo hay E/S.
//
// IMPORTANTE: stdout es el canal del protocolo MCP. Este script no escribe nada en stdout salvo con
// `--print`, que muestra el comando resuelto (sin variables de entorno) y sale sin arrancar nada:
//   node .claude/mcp/playwright.mjs --print
import { spawn } from 'node:child_process';
import { existsSync, readFileSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { assertSafeConfig, buildLaunch, CONFIG_RELATIVE, droppedEnvNames, LaunchError } from './playwright-launch.mjs';

// La raíz se deduce de la ubicación del script, no del directorio actual ni de variables de entorno.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const fail = (message) => {
  process.stderr.write(`[taller6mm/playwright-mcp] ${message}\n`);
  process.exit(1);
};

let launch;
try {
  const configPath = path.join(root, ...CONFIG_RELATIVE);
  const raw = readFileSync(configPath, 'utf8');
  assertSafeConfig(JSON.parse(raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw));
  launch = buildLaunch({
    platform: process.platform,
    execPath: process.execPath,
    env: process.env,
    root,
    exists: existsSync,
    realpath: realpathSync,
  });
} catch (error) {
  fail(error instanceof LaunchError || error instanceof SyntaxError ? error.message : String(error));
}

if (process.argv.includes('--print')) {
  process.stdout.write(`${JSON.stringify({ command: launch.command, args: launch.args, cwd: launch.options.cwd }, null, 2)}\n`);
  process.exit(0);
}

const dropped = droppedEnvNames(process.env);
if (dropped.length) {
  process.stderr.write(`[taller6mm/playwright-mcp] Ignoro ${dropped.join(', ')}: la configuración está en ${CONFIG_RELATIVE.join('/')}.\n`);
}

const child = spawn(launch.command, launch.args, launch.options);
child.on('error', (error) => fail(`No se pudo arrancar @playwright/mcp: ${error.message}`));
child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
  process.on(signal, () => {
    if (child.exitCode === null) child.kill(signal);
  });
}
