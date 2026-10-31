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
  isInside,
  LaunchError,
  MCP_PACKAGE,
  NO_SANDBOX_ENV,
  sandboxArgs,
  sanitizeEnv,
  workDirFor,
} from './playwright-launch.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..');
const launcher = path.join(here, 'playwright.mjs');
const readJson = (file) => JSON.parse(readFileSync(file, 'utf8'));
const only =
  (...files) =>
  (p) =>
    files.includes(p);

const WIN_ROOT = 'C:\\dev\\bancada';
const WIN_NODE = 'C:\\Program Files\\nodejs\\node.exe';
const WIN_NPX = 'C:\\Program Files\\nodejs\\node_modules\\npm\\bin\\npx-cli.js';
const NIX_ROOT = '/home/javi/taller6mm';
const NVM_NODE = '/home/javi/.nvm/versions/node/v26.13.0/bin/node';
const NVM_NPX = '/home/javi/.nvm/versions/node/v26.13.0/lib/node_modules/npm/bin/npx-cli.js';

describe('navegador por plataforma', () => {
  test('Edge en Windows y Chromium en macOS y Linux', () => {
    assert.equal(browserFor('win32'), 'msedge');
    assert.equal(browserFor('linux'), 'chromium');
    assert.equal(browserFor('darwin'), 'chromium');
  });
});

describe('isInside', () => {
  test('POSIX y Windows (sin distinguir mayúsculas)', () => {
    assert.ok(isInside('/a/b/c', '/a/b', 'linux'));
    assert.ok(!isInside('/a/bc', '/a/b', 'linux'));
    assert.ok(!isInside('/a/b/../x', '/a/b', 'linux'));
    assert.ok(isInside('C:\\DEV\\Bancada\\x', 'c:\\dev\\bancada', 'win32'));
    assert.ok(!isInside('D:\\dev\\bancada\\x', 'C:\\dev\\bancada', 'win32'));
  });
});

describe('findNpxCli', () => {
  test('Windows: npx-cli.js junto a node.exe (instalador oficial)', () => {
    assert.equal(findNpxCli({ platform: 'win32', execPath: WIN_NODE, root: WIN_ROOT, exists: only(WIN_NPX) }), WIN_NPX);
  });

  test('Linux o macOS: <prefijo>/lib/node_modules (nvm, tarball oficial)', () => {
    assert.equal(findNpxCli({ platform: 'linux', execPath: NVM_NODE, root: NIX_ROOT, exists: only(NVM_NPX) }), NVM_NPX);
  });

  test('POSIX: sigue el enlace de npx en el PATH si npm no está junto a node', () => {
    const real = '/usr/local/lib/node_modules/npm/bin/npx-cli.js';
    const found = findNpxCli({
      platform: 'linux',
      execPath: '/usr/bin/node',
      pathEnv: '/usr/bin:/usr/local/bin',
      root: NIX_ROOT,
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
      root: WIN_ROOT,
      exists: only('D:\\tools\\node\\npx.cmd', cli),
    });
    assert.equal(found, cli);
  });

  test('ignora las entradas relativas del PATH (`.`, node_modules/.bin)', () => {
    const found = findNpxCli({
      platform: 'linux',
      execPath: '/usr/bin/node',
      pathEnv: '.:node_modules/.bin',
      root: NIX_ROOT,
      exists: (p) => !p.startsWith('/'),
    });
    assert.equal(found, null);
  });

  test('nunca devuelve un npx-cli.js dentro del repo', () => {
    const planted = `${NIX_ROOT}/node_modules/npm/bin/npx-cli.js`;
    const found = findNpxCli({
      platform: 'linux',
      execPath: `${NIX_ROOT}/bin/node`,
      pathEnv: `${NIX_ROOT}/node_modules/.bin`,
      root: NIX_ROOT,
      exists: (p) => p === planted || p === `${NIX_ROOT}/node_modules/.bin/npx`,
      realpath: () => planted,
    });
    assert.equal(found, null);
  });

  test('sin npm: null y buildLaunch falla con un mensaje claro', () => {
    const noNpm = { platform: 'linux', execPath: '/usr/bin/node', root: NIX_ROOT, exists: () => false };
    assert.equal(findNpxCli({ ...noNpm, pathEnv: '/usr/bin' }), null);
    assert.throws(
      () => buildLaunch({ ...noNpm, env: { PATH: '/usr/bin' }, home: '/home/javi' }),
      (error) => error instanceof LaunchError && /npx/.test(error.message),
    );
  });
});

describe('buildLaunch', () => {
  test('Windows: node + npx-cli.js, versión fijada, Edge, sin shell y fuera del repo', () => {
    const r = buildLaunch({
      platform: 'win32',
      execPath: WIN_NODE,
      env: { Path: 'C:\\Windows', LOCALAPPDATA: 'C:\\Users\\javie\\AppData\\Local' },
      root: WIN_ROOT,
      home: 'C:\\Users\\javie',
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
    assert.equal(r.options.cwd, 'C:\\Users\\javie\\AppData\\Local\\taller6mm\\playwright-mcp');
    assert.equal(r.options.env.NoDefaultCurrentDirectoryInExePath, '1');
    assert.equal(r.options.stdio, 'inherit');
    assert.ok(![r.command, ...r.args].some((a) => /(?:^|[\\/])cmd(?:\.exe)?$|^\/c$/i.test(a)), 'sin cmd /c');
  });

  test('Linux sin root: Chromium de Playwright con el sandbox forzado', () => {
    const r = buildLaunch({
      platform: 'linux',
      execPath: NVM_NODE,
      env: { PATH: '/usr/bin' },
      root: NIX_ROOT,
      home: '/home/javi',
      uid: 1000,
      exists: only(NVM_NPX),
    });
    assert.deepEqual(r.args.slice(-3), ['--browser', 'chromium', '--sandbox']);
    assert.ok(!r.args.includes('--executable-path'));
    assert.equal(r.args[r.args.indexOf('--config') + 1], `${NIX_ROOT}/.claude/playwright-mcp.json`);
    assert.equal(r.options.cwd, '/home/javi/.cache/taller6mm/playwright-mcp');
    assert.deepEqual(r.warnings, []);
  });

  test('nube de Claude Code (root): Chromium preinstalado y aviso de que va sin sandbox', () => {
    const r = buildLaunch({
      platform: 'linux',
      execPath: NVM_NODE,
      env: { PATH: '/usr/bin', CLAUDE_CODE_REMOTE: 'true' },
      root: '/r',
      home: '/root',
      uid: 0,
      exists: only(NVM_NPX, CLOUD_CHROMIUM),
    });
    assert.deepEqual(r.args.slice(-2), ['--executable-path', CLOUD_CHROMIUM]);
    assert.ok(!r.args.includes('--sandbox'));
    assert.match(r.warnings[0], /root/);
  });

  test('la ruta del usuario (PLAYWRIGHT_MCP_EXECUTABLE_PATH) manda sobre la de la nube', () => {
    const env = { CLAUDE_CODE_REMOTE: 'true', PLAYWRIGHT_MCP_EXECUTABLE_PATH: '/opt/chrome/chrome' };
    assert.equal(cloudExecutable({ platform: 'linux', env, exists: () => true }), null);
    const r = buildLaunch({
      platform: 'linux',
      execPath: NVM_NODE,
      env,
      root: '/r',
      home: '/root',
      uid: 0,
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

describe('sandboxArgs', () => {
  test('Linux sin root: --sandbox; con root o con la variable de exclusión, sin sandbox y con aviso', () => {
    assert.deepEqual(sandboxArgs({ platform: 'linux', uid: 1000, env: {} }), { args: ['--sandbox'], warning: null });
    assert.equal(sandboxArgs({ platform: 'linux', uid: 0, env: {} }).args.length, 0);
    const optOut = sandboxArgs({ platform: 'linux', uid: 1000, env: { [NO_SANDBOX_ENV]: '1' } });
    assert.deepEqual(optOut.args, []);
    assert.match(optOut.warning, new RegExp(NO_SANDBOX_ENV));
  });

  test('Windows y macOS ya lo tienen activo: no se toca', () => {
    assert.deepEqual(sandboxArgs({ platform: 'win32', uid: -1, env: {} }), { args: [], warning: null });
    assert.deepEqual(sandboxArgs({ platform: 'darwin', uid: 501, env: {} }), { args: [], warning: null });
  });
});

describe('workDirFor', () => {
  test('carpeta de caché del usuario en cada sistema', () => {
    assert.equal(
      workDirFor({ platform: 'darwin', env: {}, home: '/Users/javi', root: '/Users/javi/dev/taller6mm' }),
      '/Users/javi/Library/Caches/taller6mm/playwright-mcp',
    );
    assert.equal(
      workDirFor({ platform: 'linux', env: { XDG_CACHE_HOME: '/var/cache/javi' }, home: '/home/javi', root: NIX_ROOT }),
      '/var/cache/javi/taller6mm/playwright-mcp',
    );
    assert.equal(
      workDirFor({ platform: 'linux', env: { XDG_CACHE_HOME: 'relativa' }, home: '/home/javi', root: NIX_ROOT }),
      '/home/javi/.cache/taller6mm/playwright-mcp',
    );
  });

  test('nunca dentro del repo', () => {
    assert.throws(
      () =>
        workDirFor({
          platform: 'linux',
          env: { XDG_CACHE_HOME: `${NIX_ROOT}/.cache` },
          home: '/home/javi',
          root: NIX_ROOT,
        }),
      LaunchError,
    );
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
    PLAYWRIGHT_MCP_PORT: '8931',
    PLAYWRIGHT_MCP_CAPS: 'network',
    PLAYWRIGHT_MCP_EXECUTABLE_PATH: '/opt/chrome/chrome',
    PLAYWRIGHT_MCP_HEADLESS: 'true',
    NPM_CONFIG_IGNORE_SCRIPTS: 'false',
    nodefaultcurrentdirectoryinexepath: '0',
  };

  test('quita las variables que relajarían la configuración y conserva la lista blanca', () => {
    const out = sanitizeEnv(env, 'linux');
    const kept = Object.keys(out).filter((k) => /^playwright_mcp_/i.test(k));
    assert.deepEqual(kept.sort(), ['PLAYWRIGHT_MCP_EXECUTABLE_PATH', 'PLAYWRIGHT_MCP_HEADLESS']);
    assert.equal(out.PATH, '/usr/bin');
    assert.equal(out.HOME, '/home/javi');
  });

  test('npx nunca ejecuta scripts de instalación', () => {
    const out = sanitizeEnv(env, 'linux');
    assert.equal(out.npm_config_ignore_scripts, 'true');
    assert.ok(!('NPM_CONFIG_IGNORE_SCRIPTS' in out));
  });

  test('Windows: no se buscan ejecutables en el directorio actual', () => {
    const out = sanitizeEnv(env, 'win32');
    assert.equal(out.NoDefaultCurrentDirectoryInExePath, '1');
    assert.ok(!('nodefaultcurrentdirectoryinexepath' in out));
    assert.ok(!('NoDefaultCurrentDirectoryInExePath' in sanitizeEnv({}, 'linux')));
  });

  test('droppedEnvNames lista solo nombres, nunca valores', () => {
    const names = droppedEnvNames(env);
    assert.ok(names.includes('PLAYWRIGHT_MCP_ALLOWED_ORIGINS'));
    assert.ok(names.includes('playwright_mcp_isolated'));
    assert.ok(!names.includes('PLAYWRIGHT_MCP_HEADLESS'));
    assert.ok(names.every((n) => !n.includes('=')));
  });
});

describe('assertSafeConfig (lista blanca estricta)', () => {
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
    assert.equal(base.browser.launchOptions, undefined, 'el canal lo decide el lanzador');
  });

  test('admite un origen https concreto (la preview, en S3) y omitir allowUnrestrictedFileAccess', () => {
    const preview = 'https://pr-12-taller6mm-web-preview.javi.workers.dev';
    assert.doesNotThrow(() => assertSafeConfig(variant((c) => c.network.allowedOrigins.push(preview))));
    assert.doesNotThrow(() => assertSafeConfig(variant((c) => delete c.allowUnrestrictedFileAccess)));
  });

  const unsafe = {
    'perfil no aislado': (c) => (c.browser.isolated = false),
    'isolated como texto': (c) => (c.browser.isolated = 'true'),
    'sin isolated': (c) => delete c.browser.isolated,
    'otro navegador': (c) => (c.browser.browserName = 'firefox'),
    'perfil persistente': (c) => (c.browser.userDataDir = '/home/javi/perfil'),
    'acceso libre a archivos': (c) => (c.allowUnrestrictedFileAccess = true),
    'acceso libre como texto "true"': (c) => (c.allowUnrestrictedFileAccess = 'true'),
    'acceso libre como texto "false"': (c) => (c.allowUnrestrictedFileAccess = 'false'),
    'acceso libre como número': (c) => (c.allowUnrestrictedFileAccess = 1),
    'sin lista de orígenes': (c) => delete c.network.allowedOrigins,
    'lista vacía (= todo permitido)': (c) => (c.network.allowedOrigins = []),
    'comodín total': (c) => c.network.allowedOrigins.push('*'),
    'comodín de subdominio': (c) => c.network.allowedOrigins.push('https://*.workers.dev'),
    'origen con ruta': (c) => c.network.allowedOrigins.push('https://example.com/x'),
    'otro esquema': (c) => c.network.allowedOrigins.push('file:///etc'),
    'orígenes bloqueados (no se usan)': (c) => (c.network.blockedOrigins = ['https://x.test']),
    'navegador existente por CDP': (c) => (c.browser.cdpEndpoint = 'http://127.0.0.1:9222'),
    'navegador remoto': (c) => (c.browser.remoteEndpoint = 'ws://127.0.0.1:3000'),
    'extensión del navegador': (c) => (c.extension = true),
    'servidor HTTP (puerto)': (c) => (c.server = { port: 8931 }),
    'servidor HTTP en 0.0.0.0': (c) => (c.server = { host: '0.0.0.0' }),
    'página de inicio en Node': (c) => (c.browser.initPage = ['init.ts']),
    'script de inicio': (c) => (c.browser.initScript = ['init.js']),
    'opciones de lanzamiento': (c) => (c.browser.launchOptions = { args: ['--no-sandbox'] }),
    'ejecutable propio': (c) => (c.browser.launchOptions = { executablePath: '/tmp/x' }),
    'estado de almacenamiento': (c) => (c.browser.contextOptions = { storageState: 'x.json' }),
    'capacidades extra': (c) => (c.capabilities = ['network']),
    secretos: (c) => (c.secrets = { A: 'b' }),
    'clave desconocida': (c) => (c.cualquierCosa = 1),
  };
  for (const [name, mutate] of Object.entries(unsafe)) {
    test(`rechaza: ${name}`, () => {
      assert.throws(() => assertSafeConfig(variant(mutate)), LaunchError);
    });
  }

  test('rechaza lo que no es un objeto', () => {
    for (const config of [null, [], 'x', 1]) assert.throws(() => assertSafeConfig(config), LaunchError);
  });
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
    assert.ok(!isInside(out.cwd, root, process.platform), 'el directorio de trabajo está fuera del repo');
    assert.ok(out.args.includes(MCP_PACKAGE));
    assert.equal(out.args[out.args.indexOf('--browser') + 1], browserFor(process.platform));
    assert.ok(!r.stdout.includes('secreto-que-no-debe-salir'));
  });

  test('falla cerrado (código 1, nada en stdout) si la configuración no es segura', () => {
    const tmp = mkdtempSync(path.join(tmpdir(), 'taller6mm-mcp-'));
    try {
      mkdirSync(path.join(tmp, '.claude', 'mcp'), { recursive: true });
      for (const f of ['playwright.mjs', 'playwright-launch.mjs']) {
        copyFileSync(path.join(here, f), path.join(tmp, '.claude', 'mcp', f));
      }
      const config = { ...readJson(path.join(root, '.claude', 'playwright-mcp.json')), server: { host: '0.0.0.0' } };
      writeFileSync(path.join(tmp, '.claude', 'playwright-mcp.json'), JSON.stringify(config));
      const script = path.join(tmp, '.claude', 'mcp', 'playwright.mjs');
      const r = spawnSync(process.execPath, [script, '--print'], { encoding: 'utf8' });
      assert.equal(r.status, 1);
      assert.equal(r.stdout, '');
      assert.match(r.stderr, /no es seguro/);
    } finally {
      rmSync(tmp, { recursive: true, force: true });
    }
  });
});
