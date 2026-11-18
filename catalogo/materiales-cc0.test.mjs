import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const raiz = join(dirname(fileURLToPath(import.meta.url)), '..');
const manifiesto = JSON.parse(readFileSync(join(raiz, 'catalogo', 'materiales-cc0.json'), 'utf8'));
const materiales = manifiesto.materiales;

test('hay materiales y los ids no se repiten', () => {
  assert.ok(materiales.length >= 1);
  assert.equal(new Set(materiales.map((m) => m.id)).size, materiales.length);
});

for (const m of materiales) {
  test(`${m.id}: CC0, procedencia y hashes`, () => {
    assert.match(m.licencia, /^CC0 1\.0 Universal$/);
    assert.equal(m.url_licencia, 'https://creativecommons.org/publicdomain/zero/1.0/');
    assert.match(m.url, /^https:\/\/(ambientcg\.com|polyhaven\.com)\//);
    assert.match(m.fecha_consulta, /^\d{4}-\d{2}-\d{2}$/);
    assert.ok(m.archivos.length >= 3);
    for (const a of m.archivos) assert.match(a.sha256, /^[0-9a-f]{64}$/);
  });

  test(`${m.id}: la carpeta no está rastreada por git`, () => {
    assert.match(m.carpeta, /^assets-src\/materiales-cc0\//);
    const rastreados = execFileSync('git', ['ls-files', '--', m.carpeta], { cwd: raiz, encoding: 'utf8' });
    assert.equal(rastreados.trim(), '');
  });
}

test('assets-src/materiales-cc0 está ignorada por git', () => {
  const salida = execFileSync('git', ['check-ignore', 'assets-src/materiales-cc0/x/y.jpg'], {
    cwd: raiz,
    encoding: 'utf8',
  });
  assert.match(salida, /materiales-cc0/);
});
