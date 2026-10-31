// Tests de scripts/run.mjs. Ejecuta: node --test "scripts/*.test.mjs"
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { describe, test } from 'node:test';
import { checkArgs, quietEnv, root } from './run.mjs';

describe('argumentos admitidos', () => {
  test('filtrar paquetes y saltarse la caché local', () => {
    assert.deepEqual(checkArgs('test', []), []);
    assert.deepEqual(checkArgs('test', ['--filter=@taller6mm/ui', '--force']), []);
    assert.deepEqual(checkArgs('build', ['--filter=@taller6mm/web...']), []);
  });

  test('nada que suba la caché, cambie de raíz o escriba archivos', () => {
    for (const arg of [
      '--api=http://127.0.0.1:9',
      '--token=x',
      '--team=y',
      '--cache=remote:rw',
      '--cwd=/tmp',
      '--root-turbo-json=/tmp/turbo.json',
      '--graph=/tmp/g.html',
      '--profile=/tmp/p.json',
      '--filter',
      '--filter=$(id)',
      '--filter=a;b',
    ]) {
      assert.deepEqual(checkArgs('test', [arg]), [arg], arg);
    }
  });

  test('lint y format no admiten ningún argumento (Biome escribiría archivos)', () => {
    assert.deepEqual(checkArgs('lint', ['--log-file=/tmp/x']), ['--log-file=/tmp/x']);
    assert.deepEqual(checkArgs('format', ['--config-path=/tmp']), ['--config-path=/tmp']);
    assert.deepEqual(checkArgs('lint', []), []);
  });

  test('el script rechaza un argumento no admitido antes de lanzar nada', () => {
    const r = spawnSync(process.execPath, [path.join(root, 'scripts', 'run.mjs'), 'test', '--api=http://127.0.0.1:9'], {
      encoding: 'utf8',
    });
    assert.equal(r.status, 2);
    assert.match(r.stderr, /Argumentos no admitidos/);
  });
});

describe('entorno de las herramientas', () => {
  test('sin variables TURBO_* heredadas, salvo la que apaga la telemetría', () => {
    const turbo = Object.keys(quietEnv).filter((name) => /^TURBO_/i.test(name));
    assert.deepEqual(turbo, ['TURBO_TELEMETRY_DISABLED']);
  });
});
