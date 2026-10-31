// Tests del lanzador del MCP de Playwright. Ejecuta: node --test ".claude/**/*.test.mjs"
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  assertSafeConfig,
  browserFor,
  buildLaunch,
  CLOUD_CHROMIUM,
  cloudExecutable,
  droppedEnvNames,
  findNpxCli,
  LaunchError,
  MCP_PACKAGE,
  sanitizeEnv,
} from './playwright-launch.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..');
const launcher = path.join(here, 'playwright.mjs');
const readJson = (file) => JSON.parse(readFileSync(file, 'utf8'));
const only =
  (...files) =>
  (p) =>
    files.includes(p);

const WIN_NODE = 'C:\\Program Files\\nodejs\\node.exe';
const WIN_NPX = 'C:\\Program Files\\nodejs\\node_modules\\npm\\bin\\npx-cli.js';
const NVM_NODE = '/home/javi/.nvm/versions/node/v26.13.0/bin/node';
const NVM_NPX = '/home/javi/.nvm/versions/node/v26.13.0/lib/node_modules/npm/bin/npx-cli.js';

describe('navegador por plataforma', () => {
  test('Edge en Windows y Chromium en macOS y Linux', () => {
    assert.equal(browserFor('win32'), 'msedge');
    assert.equal(browserFor('linux'), 'chromium');
    assert.equal(browserFor('darwin'), 'chromium');
  });
});

describe('findNpxCli', () => {
  test('Windows: npx-cli.js junto a node.exe (instalador oficial)', () => {
    assert.equal(findNpxCli({ platform: 'win32', execPath: WIN_NODE, exists: only(WIN_NPX) }), WIN_NPX);
  });

  test('Linux o macOS: <prefijo>/lib/node_modules (nvm, tarball oficial)', () => {
    assert.equal(findNpxCli({ platform: 'linux', execPath: NVM_NODE, exists: only(NVM_NPX) }), NVM_NPX);
  });

  test('POSIX: sigue el enlace de npx en el PATH si npm no está junto a node', () => {
    const real = '/usr/local/lib/node_modules/npm/bin/npx-cli.js';
    const found = findNpxCli({
      platform: 'linux',
      execPath: '/usr/bin/node',
      pathEnv: '/usr/bin:/usr/local/bin',
      exists: only('/usr/local/bin/npx', real),
      realpath: (p) => (p === '/usr/local/bin/npx' ? real : p),
    });
    assert.equal(found, real);
  });

  test('Windows: deduce npx-cli.js del npx.cmd del PATH', () => {
    const cli = 'D:\\tools\\node\\node_modules\\npm\\bin\\npx-cli.js';
    const found = findNpxCli({
      platform: 'win32',
      execPath: 'D:\\otro\\node.exe',
      pathEnv: 'C:\\Windows;D:\\tools\\node',
      exists: only('D:\\tools\\node\\npx.cmd', cli),
    });
    assert.equal(found, cli);
  });

  test('sin npm: null y buildLaunch falla con un mensaje claro', () => {
    assert.equal(
      findNpxCli({ platform: 'linux', execPath: '/usr/bin/node', pathEnv: '/usr/bin', exists: () => false }),
      null,
    );
    assert.throws(
      () =>
        buildLaunch({
          platform: 'linux',
          execPath: '/usr/bin/node',
          env: { PATH: '/usr/bin' },
          root: '/r',
          exists: () => false,
        }),
      (error) => error instanceof LaunchError && /npx/.test(error.message),
    );
  });
});

describe('buildLaunch', () => {
  test('Windows: node + npx-cli.js, versión fijada, Edge y sin shell', () => {
    const r = buildLaunch({
      platform: 'win32',
      execPath: WIN_NODE,
      env: { Path: 'C:\\Windows' },
      root: 'C:\\dev\\bancada',
      exists: only(WIN_NPX),
    });
    assert.equal(r.command, WIN_NODE);
    assert.deepEqual(r.args, [
      WIN_NPX,
      '--yes',
      MCP_PACKAGE,
      '--config',
      'C:\\dev\\bancada\\.claude\\playwright-mcp.json',
      '--browser',
      'msedge',
    ]);
    assert.equal(r.options.shell, false);
    assert.equal(r.options.cwd, 'C:\\dev\\bancada');
    assert.equal(r.options.stdio, 'inherit');
    assert.ok(![r.command, ...r.args].some((a) => /(?:^|[\\/])cmd(?:\.exe)?$|^\/c$/i.test(a)), 'sin cmd /c');
  });

  test('Linux en local: Chromium de Playwright sin ruta de ejecutable', () => {
    const r = buildLaunch({
      platform: 'linux',
      execPath: NVM_NODE,
      env: { PATH: '/usr/bin' },
      root: '/home/javi/taller6mm',
      exists: only(NVM_NPX),
    });
    assert.deepEqual(r.args.slice(-2), ['--browser', 'chromium']);
    assert.ok(!r.args.includes('--executable-path'));
    assert.equal(r.args[r.args.indexOf('--config') + 1], '/home/javi/taller6mm/.claude/playwright-mcp.json');
  });

  test('nube de Claude Code: usa el Chromium preinstalado', () => {
    const env = { PATH: '/usr/bin', CLAUDE_CODE_REMOTE: 'true' };
    const r = buildLaunch({
      platform: 'linux',
      execPath: NVM_NODE,
      env,
      root: '/r',
      exists: only(NVM_NPX, CLOUD_CHROMIUM),
    });
    assert.deepEqual(r.args.slice(-2), ['--executable-path', CLOUD_CHROMIUM]);
  });

  test('la ruta del usuario (PLAYWRIGHT_MCP_EXECUTABLE_PATH) manda sobre la de la nube', () => {
    const env = { CLAUDE_CODE_REMOTE: 'true', PLAYWRIGHT_MCP_EXECUTABLE_PATH: '/opt/chrome/chrome' };
    assert.equal(cloudExecutable({ platform: 'linux', env, exists: () => true }), null);
    const r = buildLaunch({
      platform: 'linux',
      execPath: NVM_NODE,
      env,
      root: '/r',
      exists: only(NVM_NPX, CLOUD_CHROMIUM),
    });
    assert.ok(!r.args.includes('--executable-path'));
    assert.equal(r.options.env.PLAYWRIGHT_MCP_EXECUTABLE_PATH, '/opt/chrome/chrome');
  });

  test('la detección de la nube solo aplica en Linux y si el binario existe', () => {
    assert.equal(
      cloudExecutable({ platform: 'darwin', env: { CLAUDE_CODE_REMOTE: 'true' }, exists: () => true }),
      null,
    );
    assert.equal(
      cloudExecutable({ platform: 'linux', env: { CLAUDE_CODE_REMOTE: 'true' }, exists: () => false }),
      null,
    );
    assert.equal(cloudExecutable({ platform: 'linux', env: {}, exists: () => true }), null);
  });

  test('la versión está fijada: nunca latest ni rangos', () => {
    assert.match(MCP_PACKAGE, /^@playwright\/mcp@\d+\.\d+\.\d+$/);
  });
});

describe('sanitizeEnv', () => {
  const env = {
    PATH: '/usr/bin',
    HOME: '/home/javi',
    PLAYWRIGHT_MCP_ALLOWED_ORIGINS: '*',
    playwright_mcp_isolated: 'false', // en Windows las variables no distinguen mayúsculas
    PLAYWRIGHT_MCP_ALLOW_UNRESTRICTED_FILE_ACCESS: 'true',
    PLAYWRIGHT_MCP_CONFIG: '/tmp/otra.json',
    PLAYWRIGHT_MCP_CDP_ENDPOINT: 'http://127.0.0.1:9222',
    PLAYWRIGHT_MCP_EXTENSION: 'true',
    PLAYWRIGHT_MCP_USER_DATA_DIR: '/home/javi/perfil',
    PLAYWRIGHT_MCP_BROWSER: 'firefox',
    PLAYWRIGHT_MCP_EXECUTABLE_PATH: '/opt/chrome/chrome',
    PLAYWRIGHT_MCP_HEADLESS: 'true',
    NPM_CONFIG_IGNORE_SCRIPTS: 'false',
  };

  test('quita las variables que relajarían la configuración y conserva la lista blanca', () => {
    const out = sanitizeEnv(env);
    assert.deepEqual(
      Object.keys(out)
        .filter((k) => /^playwright_mcp_/i.test(k))
        .sort(),
      ['PLAYWRIGHT_MCP_EXECUTABLE_PATH', 'PLAYWRIGHT_MCP_HEADLESS'],
    );
    assert.equal(out.PATH, '/usr/bin');
    assert.equal(out.HOME, '/home/javi');
  });

  test('npx nunca ejecuta scripts de instalación', () => {
    const out = sanitizeEnv(env);
    assert.equal(out.npm_config_ignore_scripts, 'true');
    assert.ok(!('NPM_CONFIG_IGNORE_SCRIPTS' in out));
  });

  test('droppedEnvNames lista solo nombres, nunca valores', () => {
    const names = droppedEnvNames(env);
    assert.ok(names.includes('PLAYWRIGHT_MCP_ALLOWED_ORIGINS'));
    assert.ok(names.includes('playwright_mcp_isolated'));
    assert.ok(!names.includes('PLAYWRIGHT_MCP_HEADLESS'));
    assert.ok(names.every((n) => !n.includes('=')));
  });
});

describe('assertSafeConfig', () => {
  const base = readJson(path.join(root, '.claude', 'playwright-mcp.json'));
  const variant = (mutate) => {
    const copy = structuredClone(base);
    mutate(copy);
    return copy;
  };

  test('la configuración del repo es segura y no depende de la plataforma', () => {
    assert.doesNotThrow(() => assertSafeConfig(base));
    assert.equal(base.browser.isolated, true);
    assert.deepEqual(base.network.allowedOrigins, ['http://localhost:*', 'http://127.0.0.1:*']);
    assert.equal(base.allowUnrestrictedFileAccess, false);
    assert.equal(base.browser.launchOptions?.channel, undefined, 'el canal lo decide el lanzador');
  });

  test('admite un origen https concreto (la preview, en S3)', () => {
    assert.doesNotThrow(() =>
      assertSafeConfig(
        variant((c) => c.network.allowedOrigins.push('https://pr-12-taller6mm-web-preview.javi.workers.dev')),
      ),
    );
  });

  const unsafe = {
    'perfil no aislado': (c) => (c.browser.isolated = false),
    'sin isolated': (c) => delete c.browser.isolated,
    'perfil persistente': (c) => (c.browser.userDataDir = '/home/javi/perfil'),
    'acceso libre a archivos': (c) => (c.allowUnrestrictedFileAccess = true),
    'sin lista de orígenes': (c) => delete c.network.allowedOrigins,
    'lista vacía (= todo permitido)': (c) => (c.network.allowedOrigins = []),
    'comodín total': (c) => c.network.allowedOrigins.push('*'),
    'comodín de subdominio': (c) => c.network.allowedOrigins.push('https://*.workers.dev'),
    'origen con ruta': (c) => c.network.allowedOrigins.push('https://example.com/x'),
    'otro esquema': (c) => c.network.allowedOrigins.push('file:///etc'),
    'navegador existente por CDP': (c) => (c.browser.cdpEndpoint = 'http://127.0.0.1:9222'),
    'extensión del navegador': (c) => (c.extension = true),
  };
  for (const [name, mutate] of Object.entries(unsafe)) {
    test(`rechaza: ${name}`, () => {
      assert.throws(() => assertSafeConfig(variant(mutate)), LaunchError);
    });
  }
});

describe('.mcp.json', () => {
  test('arranca el lanzador con node, sin cmd /c ni npx', () => {
    const server = readJson(path.join(root, '.mcp.json')).mcpServers.playwright;
    assert.equal(server.type, 'stdio');
    assert.equal(server.command, 'node');
    assert.equal(server.args.length, 1);
    assert.match(server.args[0], /^\$\{CLAUDE_PROJECT_DIR:-\.\}\/\.claude\/mcp\/playwright\.mjs$/);
  });
});

describe('lanzador (proceso real)', () => {
  test('--print muestra el comando resuelto sin el entorno y sale con 0', () => {
    const r = spawnSync(process.execPath, [launcher, '--print'], {
      encoding: 'utf8',
      env: { ...process.env, PLAYWRIGHT_MCP_ALLOWED_ORIGINS: 'secreto-que-no-debe-salir' },
    });
    assert.equal(r.status, 0, r.stderr);
    const out = JSON.parse(r.stdout);
    assert.equal(out.command, process.execPath);
    assert.equal(out.cwd, root);
    assert.ok(out.args.includes(MCP_PACKAGE));
    assert.equal(out.args[out.args.indexOf('--browser') + 1], browserFor(process.platform));
    assert.ok(!r.stdout.includes('secreto-que-no-debe-salir'));
  });

  test('falla cerrado (código 1, nada en stdout) si la configuración no es segura', () => {
    const tmp = mkdtempSync(path.join(tmpdir(), 'taller6mm-mcp-'));
    try {
      mkdirSync(path.join(tmp, '.claude', 'mcp'), { recursive: true });
      for (const f of ['playwright.mjs', 'playwright-launch.mjs'])
        copyFileSync(path.join(here, f), path.join(tmp, '.claude', 'mcp', f));
      writeFileSync(
        path.join(tmp, '.claude', 'playwright-mcp.json'),
        JSON.stringify({ browser: { isolated: false }, network: {} }),
      );
      const r = spawnSync(process.execPath, [path.join(tmp, '.claude', 'mcp', 'playwright.mjs'), '--print'], {
        encoding: 'utf8',
      });
      assert.equal(r.status, 1);
      assert.equal(r.stdout, '');
      assert.match(r.stderr, /no es seguro/);
    } finally {
      rmSync(tmp, { recursive: true, force: true });
    }
  });
});
