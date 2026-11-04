// Tests de scripts/preparar-preview.mjs (ADR-0008; revisor-seguridad, 03-11-2026, A1). La build de un PR
// es un dato sin confianza: a su Preview solo llega su código, y siempre con la configuración de `main`.
// Ejecuta: node --test "scripts/*.test.mjs"
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { after, describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { buildPreview } from './fixtures/wrangler-build-preview.mjs';
import { preparar } from './preparar-preview.mjs';
import { configuracionPreview, leerReferencia, validar } from './validar-preview.mjs';

const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'preparar-preview.mjs');
const referencia = leerReferencia();
const temporal = mkdtempSync(path.join(tmpdir(), 'taller6mm-preparar-'));
after(() => rmSync(temporal, { recursive: true, force: true }));

let n = 0;
const carpeta = () => path.join(temporal, String(++n));

/** Un artefacto como el que sube previews.yml; `cambiar` lo altera (undefined borra el archivo). */
function artefacto(cambiar = () => {}) {
  const archivos = {
    'server/entry.mjs': 'export default {};\n//# sourceMappingURL=entry.mjs.map\n',
    'server/entry.mjs.map': '{"version":3,"sources":["../../src/worker.ts"],"mappings":""}',
    'server/chunks/react_BSHLiuuV.mjs': 'export const a = 1;\n//# sourceMappingURL=react_BSHLiuuV.mjs.map',
    'server/chunks/react_BSHLiuuV.mjs.map': '{"version":3,"sources":[],"mappings":""}',
    // Como en la build real: una dependencia empaquetada deja la referencia a su propio mapa a medio archivo.
    'server/chunks/index_DddSzUKz.mjs': 'const t = 1;\n//# sourceMappingURL=table.js.map\nexport { t };\n',
    'server/wrangler.json': JSON.stringify(buildPreview(referencia)),
    'client/_headers': '/*\n  X-Frame-Options: DENY\n',
    'client/.assetsignore': '_worker.js\n',
    'client/.well-known/security.txt': 'Contact: https://example.invalid/\n',
    'client/_astro/app.js': 'console.log(1);\n',
    'client/sistema/index.html': '<!doctype html><title>Sistema</title>\n',
  };
  cambiar(archivos);
  const dir = carpeta();
  mkdirSync(dir, { recursive: true });
  for (const [ruta, contenido] of Object.entries(archivos)) {
    if (contenido === undefined) continue;
    const destino = path.join(dir, ...ruta.split('/'));
    mkdirSync(path.dirname(destino), { recursive: true });
    writeFileSync(destino, contenido);
  }
  return dir;
}

function listar(dir, base = '') {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const relativa = base ? `${base}/${e.name}` : e.name;
    return e.isDirectory() ? listar(path.join(dir, e.name), relativa) : [relativa];
  });
}

const conConfig = (cambiar) => (a) => {
  const c = buildPreview(referencia);
  cambiar(c);
  a['server/wrangler.json'] = JSON.stringify(c);
};

describe('preparar-preview', () => {
  test('copia solo el código del PR y escribe la configuración de main', () => {
    const destino = carpeta();
    const r = preparar(artefacto(), destino, referencia);
    assert.deepEqual(JSON.parse(readFileSync(path.join(destino, 'server', 'wrangler.json'), 'utf8')), r.config);
    assert.deepEqual(r.config, configuracionPreview(referencia));
    assert.deepEqual(listar(destino).sort(), [
      'client/.assetsignore',
      'client/.well-known/security.txt',
      'client/_astro/app.js',
      'client/_headers',
      'client/sistema/index.html',
      'server/chunks/index_DddSzUKz.mjs',
      'server/chunks/react_BSHLiuuV.mjs',
      'server/chunks/react_BSHLiuuV.mjs.map',
      'server/entry.mjs',
      'server/entry.mjs.map',
      'server/wrangler.json',
    ]);
  });

  test('la configuración desplegada solo tiene las claves de main y pasa el validador', () => {
    const config = configuracionPreview(referencia);
    assert.deepEqual(Object.keys(config).sort(), [
      'assets',
      'compatibility_date',
      'compatibility_flags',
      'd1_databases',
      'main',
      'name',
      'no_bundle',
      'observability',
      'preview_urls',
      'previews',
      'rules',
      'send_metrics',
      'upload_source_maps',
      'vars',
      'workers_dev',
    ]);
    assert.equal(config.name, 'taller6mm-web-preview');
    assert.equal(config.no_bundle, true);
    assert.deepEqual(config.assets, { binding: 'ASSETS', directory: '../client' });
    assert.deepEqual(validar(config, referencia), []);
  });

  const casos = {
    // Archivos que no son código o que nunca deben subirse.
    'un .env en server': (a) => {
      a['server/.env'] = 'CLOUDFLARE_API_BASE_URL=https://example.invalid';
    },
    'un .dev.vars en server': (a) => {
      a['server/.dev.vars'] = 'X=1';
    },
    'un .env.production en client': (a) => {
      a['client/.env.production'] = 'X=1';
    },
    'una carpeta oculta en client': (a) => {
      a['client/.git/config'] = '[core]';
    },
    '.well-known fuera de la raíz de client': (a) => {
      a['client/docs/.well-known/x.txt'] = 'x';
    },
    'un .txt en server (se subiría como módulo de texto)': (a) => {
      a['server/notas.txt'] = 'x';
    },
    'un .wasm en server': (a) => {
      a['server/x.wasm'] = 'x';
    },
    'un .json extra en server': (a) => {
      a['server/datos.json'] = '{}';
    },
    'otra carpeta en el artefacto': (a) => {
      a['node_modules/x/index.js'] = 'x';
    },
    'un archivo suelto en la raíz del artefacto': (a) => {
      a['wrangler.json'] = '{}';
    },
    'sin server/entry.mjs': (a) => {
      a['server/entry.mjs'] = undefined;
    },
    'sin server/wrangler.json': (a) => {
      a['server/wrangler.json'] = undefined;
    },
    'sin client/': (a) => {
      for (const k of Object.keys(a)) if (k.startsWith('client/')) a[k] = undefined;
    },
    // Mapas de código: wrangler lee y sube el archivo que nombran.
    'un sourceMappingURL que sube de carpeta': (a) => {
      a['server/entry.mjs'] = 'x;\n//# sourceMappingURL=../../../../home/runner/.credentials.map\n';
    },
    'un sourceMappingURL absoluto': (a) => {
      a['server/entry.mjs'] = 'x;\n//# sourceMappingURL=/proc/self/environ\n';
    },
    'un sourceMappingURL con espacio y ../ detrás': (a) => {
      a['server/entry.mjs'] = 'x;\n//# sourceMappingURL=entry.mjs.map ../../../x.map\n';
    },
    'un sourceMappingURL con \\r y ../ detrás': (a) => {
      a['server/entry.mjs'] = 'x;\n//# sourceMappingURL=entry.mjs.map\r../../../x.map\n';
    },
    'un sourceMappingURL file:': (a) => {
      a['server/chunks/react_BSHLiuuV.mjs'] = 'x;\n//# sourceMappingURL=file:///etc/passwd.map';
    },
    'un sourceMappingURL con //@': (a) => {
      a['server/entry.mjs'] = 'x;\n//@ sourceMappingURL=../../../x.map\n';
    },
    // wrangler solo usa la última línea; aquí se exige que todas sean correctas.
    'un sourceMappingURL malo antes de uno bueno': (a) => {
      a['server/entry.mjs'] = 'x;\n//# sourceMappingURL=../../../x.map\ny;\n//# sourceMappingURL=entry.mjs.map\n';
    },
    // Configuración del PR distinta de la de main (no se usa, pero delata un cambio que la Preview no tendría).
    'base_dir en la configuración del PR': conConfig((c) => {
      c.base_dir = '/';
    }),
    'un build personalizado': conConfig((c) => {
      c.build = { command: 'curl https://example.invalid' };
    }),
    'un alias': conConfig((c) => {
      c.alias = { x: '/proc/self/environ' };
    }),
    'reglas de texto para todo': conConfig((c) => {
      c.rules = [{ type: 'Text', globs: ['**/*'] }];
    }),
    'empaquetado activado': conConfig((c) => {
      c.no_bundle = false;
    }),
    find_additional_modules: conConfig((c) => {
      c.find_additional_modules = true;
    }),
    'otra cuenta': conConfig((c) => {
      c.account_id = '0123456789abcdef0123456789abcdef';
    }),
    secrets: conConfig((c) => {
      c.secrets = { required: ['CLOUDFLARE_API_TOKEN'] };
    }),
    'otro Worker': conConfig((c) => {
      c.name = 'taller6mm-web';
    }),
    'un wrangler.json ilegible': (a) => {
      a['server/wrangler.json'] = '{ no es json';
    },
  };
  for (const [nombre, cambiar] of Object.entries(casos)) {
    test(`rechaza ${nombre}`, () => {
      const destino = carpeta();
      assert.throws(() => preparar(artefacto(cambiar), destino, referencia), /no se puede desplegar/);
      assert.ok(!existsSync(destino), 'no copia nada si la build no es válida');
    });
  }

  // En Windows `\` es separador y los caracteres de control no valen en un nombre: estos casos solo se
  // pueden crear en Linux y macOS (los ejecuta el CI en ubuntu-latest).
  const nombresRaros = {
    'un nombre con barra invertida y ..': 'server/x\\..\\..\\..\\preview\\client\\cebo.mjs',
    'un nombre con barra invertida': 'server/chunks\\a.mjs',
    'un nombre con salto de línea': 'client/a\nb.js',
  };
  for (const [nombre, ruta] of Object.entries(nombresRaros)) {
    test(`rechaza ${nombre}`, (t) => {
      if (process.platform === 'win32') {
        t.skip('en Windows no se puede crear ese nombre');
        return;
      }
      const destino = carpeta();
      const origen = artefacto((a) => {
        a[ruta] = 'export {};\n';
      });
      assert.throws(() => preparar(origen, destino, referencia), /nombre de archivo no permitido/);
      assert.ok(!existsSync(destino), 'no copia nada si la build no es válida');
    });
  }

  test('rechaza enlaces simbólicos', (t) => {
    const origen = artefacto();
    try {
      symlinkSync(path.join(origen, 'server', 'entry.mjs'), path.join(origen, 'server', 'enlace.mjs'));
    } catch {
      t.skip('este sistema no deja crear enlaces simbólicos sin permisos');
      return;
    }
    assert.throws(() => preparar(origen, carpeta(), referencia), /enlace simbólico/);
  });

  test('la carpeta limpia tiene que estar vacía', () => {
    const destino = carpeta();
    mkdirSync(destino, { recursive: true });
    writeFileSync(path.join(destino, 'resto.mjs'), 'x');
    assert.throws(() => preparar(artefacto(), destino, referencia), /no está vacía/);
  });

  test('por línea de comandos: 0 si vale, 1 si no', () => {
    const ok = spawnSync(process.execPath, [script, artefacto(), carpeta()], { encoding: 'utf8' });
    assert.equal(ok.status, 0, ok.stderr);
    assert.match(ok.stdout, /taller6mm-web-preview/);
    const mal = spawnSync(process.execPath, [script, artefacto(casos['un .env en server']), carpeta()], {
      encoding: 'utf8',
    });
    assert.equal(mal.status, 1);
    assert.match(mal.stderr, /archivo de secretos/);
  });
});
