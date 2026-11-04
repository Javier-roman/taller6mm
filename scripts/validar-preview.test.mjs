// Tests del validador de builds de preview (scripts/validar-preview.mjs; ADR-0008). La build de un PR
// es un dato sin confianza: cualquier desvío de la configuración de `main` tiene que rechazarse.
// Ejecuta: node --test "scripts/*.test.mjs"
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';
import { buildPreview } from './fixtures/wrangler-build-preview.mjs';
import { configuracionPreview, leerReferencia, sinComentarios, vacio, validar } from './validar-preview.mjs';

const referencia = leerReferencia();
const buena = () => buildPreview(referencia);

describe('validar-preview', () => {
  test('acepta la build que genera hoy el entorno preview', () => {
    assert.deepEqual(validar(buena(), referencia), []);
  });

  test('acepta la configuración con la que se despliegan las Previews', () => {
    assert.deepEqual(validar(configuracionPreview(referencia), referencia), []);
  });

  test('sin entorno preview en la referencia no hay configuración', () => {
    assert.throws(() => configuracionPreview({ name: 'x' }), /entorno `preview`/);
    assert.ok(validar(buena(), { name: 'x' }).length > 0);
  });

  const casos = {
    'otro Worker (producción)': (c) => {
      c.name = 'taller6mm-web';
    },
    'otra base (la de producción)': (c) => {
      c.d1_databases = [...c.d1_databases, { binding: 'PROD', database_name: 'taller6mm-core', database_id: 'x' }];
    },
    'otro id de base': (c) => {
      c.d1_databases[0] = { ...c.d1_databases[0], database_id: '11111111-1111-4111-8111-111111111111' };
    },
    'un service binding (a jobs)': (c) => {
      c.services = [{ binding: 'JOBS', service: 'taller6mm-jobs' }];
    },
    'un bucket R2': (c) => {
      c.r2_buckets = [{ binding: 'X', bucket_name: 'taller6mm-uploads' }];
    },
    rutas: (c) => {
      c.routes = [{ pattern: 'taller6mm.es/*', zone_name: 'taller6mm.es' }];
    },
    'un cron': (c) => {
      c.triggers = { crons: ['* * * * *'] };
    },
    'variables cambiadas': (c) => {
      c.vars = { ENVIRONMENT: 'production' };
    },
    'previews con un bucket': (c) => {
      c.previews = { ...c.previews, r2_buckets: [{ binding: 'X', bucket_name: 'y' }] };
    },
    'previews con otra base': (c) => {
      c.previews = { ...c.previews, d1_databases: c.d1_databases.slice(1) };
    },
    'sin bloque previews': (c) => {
      c.previews = undefined;
    },
    'un main fuera de la build': (c) => {
      c.main = '../../evil.mjs';
    },
    'una clave desconocida con valor': (c) => {
      c.unsafe = { bindings: [{ name: 'X', type: 'y' }] };
    },
    // Claves que decidirían qué archivos del runner se suben o qué se ejecuta con el token (A1).
    'base_dir fuera de la build': (c) => {
      c.base_dir = '/';
    },
    'un build personalizado': (c) => {
      c.build = { command: 'curl https://example.invalid' };
    },
    'un alias': (c) => {
      c.alias = { x: '/proc/self/environ' };
    },
    'un define': (c) => {
      c.define = { TOKEN: 'process.env.CLOUDFLARE_API_TOKEN' };
    },
    'un tsconfig': (c) => {
      c.tsconfig = '../../../tsconfig.json';
    },
    'reglas de texto para todo': (c) => {
      c.rules = [{ type: 'Text', globs: ['**/*'], fallthrough: true }];
    },
    'empaquetado activado': (c) => {
      c.no_bundle = false;
    },
    find_additional_modules: (c) => {
      c.find_additional_modules = true;
    },
    'estáticos en otra carpeta': (c) => {
      c.assets = { binding: 'ASSETS', directory: '../../..' };
    },
    'otra cuenta': (c) => {
      c.account_id = '0123456789abcdef0123456789abcdef';
    },
    // Con `secrets`, wrangler incluye process.env (donde está el token) al cargar las variables.
    secrets: (c) => {
      c.secrets = { required: ['CLOUDFLARE_API_TOKEN'] };
    },
    'otra fecha de compatibilidad': (c) => {
      c.compatibility_date = '2020-01-01';
    },
    'límites de CPU': (c) => {
      c.limits = { cpu_ms: 30000 };
    },
  };
  for (const [nombre, cambiar] of Object.entries(casos)) {
    test(`rechaza ${nombre}`, () => {
      const c = buena();
      cambiar(c);
      assert.ok(validar(c, referencia).length > 0);
    });
  }

  test('sinComentarios respeta las cadenas con //', () => {
    assert.deepEqual(JSON.parse(sinComentarios('{ "url": "https://a.b//c", // nota\n "x": [1, 2,], }')), {
      url: 'https://a.b//c',
      x: [1, 2],
    });
  });

  test('vacío a efectos de despliegue', () => {
    assert.ok(vacio({ crons: [] }) && vacio([]) && vacio({ producers: [], consumers: [] }));
    assert.ok(!vacio([{ binding: 'X' }]) && !vacio({ crons: ['* * * * *'] }));
  });
});
