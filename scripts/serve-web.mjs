#!/usr/bin/env node
// Sirve la build de apps/web en workerd para los e2e y Lighthouse: aplica las migraciones locales
// y arranca `wrangler dev` sobre la configuración que genera Astro (la misma que `wrangler deploy`).
// Requiere `pnpm build` antes. Uso: node scripts/serve-web.mjs [puerto]
import { spawn } from 'node:child_process';
import path from 'node:path';
import { migrate, persistTo } from './db.mjs';
import { bin, quietEnv, root } from './run.mjs';

const port = process.argv[2] ?? '4321';
const webDir = path.join(root, 'apps', 'web');

if (migrate() !== 0) process.exit(1);

const child = spawn(
  process.execPath,
  [bin('wrangler', 'bin/wrangler.js', webDir), 'dev', '--ip', '127.0.0.1', '--port', port, '--persist-to', persistTo],
  { cwd: webDir, stdio: 'inherit', env: quietEnv },
);
child.on('exit', (code) => process.exit(code ?? 0));
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    try {
      child.kill(process.platform === 'win32' ? 'SIGTERM' : signal);
    } catch {
      // El proceso ya terminó.
    }
  });
}
