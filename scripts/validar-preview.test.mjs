// Tests del validador de builds de preview (scripts/validar-preview.mjs; ADR-0008). La build de un PR
// es un dato sin confianza: cualquier desvío de la configuración de `main` tiene que rechazarse.
// Ejecuta: node --test "scripts/**/*.test.mjs"
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { sinComentarios, vacio, validar } from './validar-preview.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const referencia = JSON.parse(sinComentarios(readFileSync(path.join(root, 'apps', 'web', 'wrangler.jsonc'), 'utf8')));
const preview = referencia.env.preview;

/** Lo que genera hoy `CLOUDFLARE_ENV=preview astro build` en dist/server/wrangler.json (resumido). */
const buena = () =>
  structuredClone({
    configPath: '/runner/apps/web/dist/server/wrangler.json',
    userConfigPath: '/runner/apps/web/wrangler.jsonc',
    topLevelName: 'taller6mm-web',
    definedEnvironments: ['preview', 'production'],
    name: preview.name,
    main: 'entry.mjs',
    compatibility_date: referencia.compatibility_date,
    compatibility_flags: referencia.compatibility_flags,
    rules: [{ type: 'ESModule', globs: ['**/*.mjs'] }],
    assets: { binding: 'ASSETS', directory: '../client' },
    vars: preview.vars,
    d1_databases: preview.d1_databases,
    previews: preview.previews,
    workers_dev: preview.workers_dev,
    preview_urls: preview.preview_urls,
    observability: { enabled: true },
    triggers: { crons: [] },
    durable_objects: { bindings: [] },
    kv_namespaces: [],
    r2_buckets: [],
    queues: { producers: [], consumers: [] },
    services: [],
  });

describe('validar-preview', () => {
  test('acepta la build que genera hoy el entorno preview', () => {
    assert.deepEqual(validar(buena(), referencia), []);
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
    'un main fuera de la build': (c) => {
      c.main = '../../evil.mjs';
    },
    'una clave desconocida con valor': (c) => {
      c.unsafe = { bindings: [{ name: 'X', type: 'y' }] };
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
