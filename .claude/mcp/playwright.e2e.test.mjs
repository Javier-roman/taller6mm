// Prueba de extremo a extremo del lanzador: arranca @playwright/mcp de verdad (descarga el paquete
// con npx la primera vez), navega a un servidor local y comprueba que un origen fuera de
// `allowedOrigins` queda bloqueado. Necesita red y un navegador, así que es opcional:
//   TALLER6MM_MCP_E2E=1 node --test ".claude/**/*.test.mjs"   (PowerShell: $env:TALLER6MM_MCP_E2E=1)
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import path from 'node:path';
import { createInterface } from 'node:readline';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const launcher = path.join(path.dirname(fileURLToPath(import.meta.url)), 'playwright.mjs');
const enabled = process.env.TALLER6MM_MCP_E2E === '1';

/** Cliente JSON-RPC mínimo sobre stdio (mensajes delimitados por saltos de línea). */
function mcpClient(child) {
  let nextId = 1;
  const pending = new Map();
  createInterface({ input: child.stdout }).on('line', (line) => {
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      return; // stdout solo debería llevar JSON-RPC; cualquier otra cosa haría fallar la respuesta esperada
    }
    const waiter = pending.get(msg.id);
    if (waiter) {
      pending.delete(msg.id);
      waiter(msg);
    }
  });
  return {
    request(method, params = {}) {
      const id = nextId++;
      child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', id, method, params })}\n`);
      return new Promise((resolve) => pending.set(id, resolve));
    },
    notify(method, params = {}) {
      child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', method, params })}\n`);
    },
  };
}

const text = (result) => (result?.result?.content ?? []).map((c) => c.text ?? '').join('\n');

test('el MCP arranca, navega a localhost y bloquea otros orígenes', {
  skip: !enabled && 'define TALLER6MM_MCP_E2E=1',
  timeout: 240_000,
}, async () => {
  const server = createServer((_req, res) => {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end('<!doctype html><html lang="es"><title>Taller6mm MCP</title><h1>Banco de pruebas</h1></html>');
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();

  // Entorno hostil: si el lanzador no filtrara estas variables, relajarían el aislamiento.
  const hostile = {
    PLAYWRIGHT_MCP_ALLOWED_ORIGINS: 'http://example.invalid',
    PLAYWRIGHT_MCP_ISOLATED: 'false',
    PLAYWRIGHT_MCP_ALLOW_UNRESTRICTED_FILE_ACCESS: 'true',
    PLAYWRIGHT_MCP_PORT: '18931',
    PLAYWRIGHT_MCP_CAPS: 'network,devtools',
  };
  const child = spawn(process.execPath, [launcher], {
    stdio: ['pipe', 'pipe', 'inherit'],
    env: { ...process.env, ...hostile },
  });
  try {
    const mcp = mcpClient(child);
    const init = await mcp.request('initialize', {
      protocolVersion: '2025-06-18',
      capabilities: {},
      clientInfo: { name: 'taller6mm-e2e', version: '0.0.0' },
    });
    assert.ok(init.result?.serverInfo, 'respuesta de initialize');
    mcp.notify('notifications/initialized');

    const tools = await mcp.request('tools/list');
    const names = tools.result.tools.map((t) => t.name);
    assert.ok(names.includes('browser_navigate'), names.join(', '));

    const ok = await mcp.request('tools/call', {
      name: 'browser_navigate',
      arguments: { url: `http://127.0.0.1:${port}/` },
    });
    assert.ok(!ok.result?.isError, text(ok));
    assert.match(text(ok), /Taller6mm MCP/);

    const blocked = await mcp.request('tools/call', {
      name: 'browser_navigate',
      arguments: { url: 'http://example.invalid/' },
    });
    assert.match(text(blocked), /ERR_BLOCKED_BY_CLIENT/);

    const file = await mcp.request('tools/call', {
      name: 'browser_navigate',
      arguments: { url: 'file:///etc/hostname' },
    });
    assert.ok(file.result?.isError || /blocked|not allowed|ERR_/i.test(text(file)), text(file));

    // Las capacidades extra del entorno hostil no aparecen (p. ej. browser_route deshace allowedOrigins).
    assert.ok(!names.includes('browser_route'), 'browser_route no debe estar disponible');

    if (names.includes('browser_get_config')) {
      const config = JSON.parse(
        text(await mcp.request('tools/call', { name: 'browser_get_config', arguments: {} })).match(
          /\{[\s\S]*\}/,
        )?.[0] ?? '{}',
      );
      assert.equal(config.browser?.isolated, true);
      assert.notEqual(config.allowUnrestrictedFileAccess, true);
      assert.deepEqual(config.network?.allowedOrigins, ['http://localhost:*', 'http://127.0.0.1:*']);
      assert.equal(config.server?.port, undefined);
    }
  } finally {
    child.stdin.end();
    await new Promise((resolve) => {
      const timer = setTimeout(() => {
        child.kill('SIGKILL');
        resolve();
      }, 20_000);
      child.on('exit', () => {
        clearTimeout(timer);
        resolve();
      });
    });
    server.close();
  }
});
