// Tests del hook guardián del MCP. Ejecuta: node --test ".claude/**/*.test.mjs"
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { checkMcp } from './guard-mcp-rules.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = '/home/javi/taller6mm';
const decide = (tool, input, root = ROOT, platform = 'linux') =>
  checkMcp(`mcp__playwright__${tool}`, input, root, platform)?.[0] ?? 'allow';

describe('herramientas bloqueadas', () => {
  test('browser_run_code_unsafe y browser_file_upload, siempre', () => {
    assert.equal(decide('browser_run_code_unsafe', { code: 'async () => 1' }), 'deny');
    assert.equal(decide('browser_file_upload', { paths: ['/home/javi/taller6mm/.playwright-mcp/a.png'] }), 'deny');
  });

  test('las herramientas sin rutas siguen el flujo normal', () => {
    assert.equal(decide('browser_navigate', { url: 'http://localhost:4321/' }), 'allow');
    assert.equal(decide('browser_snapshot', {}), 'allow');
    assert.equal(decide('browser_take_screenshot', { type: 'png' }), 'allow');
  });
});

describe('rutas de archivo', () => {
  const allowed = [
    ['browser_take_screenshot', { filename: '.playwright-mcp/sistema-390.png' }],
    ['browser_take_screenshot', { filename: 'docs/informes/capturas/2026-10-31-sistema/1440.png' }],
    ['browser_take_screenshot', { filename: '/home/javi/taller6mm/docs/informes/capturas/x.png' }],
    ['browser_console_messages', { filename: '.playwright-mcp/consola.txt' }],
  ];
  for (const [tool, input] of allowed) {
    test(`permite ${tool} ${JSON.stringify(input)}`, () => assert.equal(decide(tool, input), 'allow'));
  }

  const denied = [
    ['browser_take_screenshot', { filename: '.claude/playwright-mcp.json' }],
    ['browser_take_screenshot', { filename: '.playwright-mcp/../.dev.vars' }],
    ['browser_take_screenshot', { filename: '/etc/passwd' }],
    ['browser_take_screenshot', { filename: '.playwright-mcp' }],
    ['browser_evaluate', { function: '() => 1', filename: 'apps/web/src/pages/index.astro' }],
    ['browser_set_storage_state', { filename: 'apps/web/.dev.vars' }],
    ['browser_drop', { paths: ['.playwright-mcp/ok.png', '/home/javi/.ssh/id_ed25519'] }],
    ['browser_pdf_save', { filename: 'docs/informes/capturas-falsas/x.pdf' }],
    ['browser_take_screenshot', { filename: '' }],
    ['browser_take_screenshot', { filename: 42 }],
  ];
  for (const [tool, input] of denied) {
    test(`deniega ${tool} ${JSON.stringify(input)}`, () => assert.equal(decide(tool, input), 'deny'));
  }

  test('Windows: sin distinguir mayúsculas y con barras invertidas', () => {
    const root = 'C:\\dev\\bancada';
    assert.equal(decide('browser_take_screenshot', { filename: '.PLAYWRIGHT-MCP\\a.png' }, root, 'win32'), 'allow');
    assert.equal(decide('browser_take_screenshot', { filename: 'C:\\dev\\bancada\\.dev.vars' }, root, 'win32'), 'deny');
    assert.equal(decide('browser_take_screenshot', { filename: 'D:\\otra\\a.png' }, root, 'win32'), 'deny');
  });
});

describe('hook (proceso real)', () => {
  const run = (payload) =>
    spawnSync(process.execPath, [path.join(here, 'guard-mcp.mjs')], {
      input: typeof payload === 'string' ? payload : JSON.stringify(payload),
      encoding: 'utf8',
      env: { ...process.env, CLAUDE_PROJECT_DIR: ROOT },
    });

  test('deniega con el formato de PreToolUse', () => {
    const r = run({ tool_name: 'mcp__playwright__browser_take_screenshot', tool_input: { filename: '/etc/passwd' } });
    const out = JSON.parse(r.stdout);
    assert.equal(out.hookSpecificOutput.hookEventName, 'PreToolUse');
    assert.equal(out.hookSpecificOutput.permissionDecision, 'deny');
  });

  test('no dice nada cuando no hay nada que decidir', () => {
    const r = run({ tool_name: 'mcp__playwright__browser_navigate', tool_input: { url: 'http://localhost:4321/' } });
    assert.equal(r.stdout, '');
  });

  test('falla cerrado con una entrada ilegible', () => {
    const r = run('esto no es JSON');
    assert.equal(JSON.parse(r.stdout).hookSpecificOutput.permissionDecision, 'deny');
  });
});
