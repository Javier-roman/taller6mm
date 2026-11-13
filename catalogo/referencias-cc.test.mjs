import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const raiz = join(dirname(fileURLToPath(import.meta.url)), '..');
const manifiesto = JSON.parse(readFileSync(join(raiz, 'catalogo', 'referencias-cc.json'), 'utf8'));
const refs = manifiesto.referencias;

// Solo dominio público, CC0 y CC-BY (cualquier versión). Nada de SA, NC ni ND.
const LICENCIAS = /^(Public domain|CC0|CC BY \d\.\d)$/;

test('hay referencias y como máximo 60', () => {
  assert.ok(refs.length >= 1 && refs.length <= 60);
});

test('los ids y los archivos no se repiten', () => {
  assert.equal(new Set(refs.map((r) => r.id)).size, refs.length);
  assert.equal(new Set(refs.map((r) => r.archivo)).size, refs.length);
  assert.equal(new Set(refs.map((r) => r.sha256)).size, refs.length);
});

for (const r of refs) {
  test(`${r.id}: licencia, procedencia y atribución`, () => {
    assert.match(r.licencia, LICENCIAS, `licencia no permitida: ${r.licencia}`);
    assert.doesNotMatch(r.licencia, /SA|NC|ND/);
    assert.match(r.url, /^https:\/\/commons\.wikimedia\.org\/wiki\/File:/);
    assert.ok(typeof r.autor === 'string' && r.autor.trim().length > 0, 'falta el autor');
    assert.ok(typeof r.atribucion === 'string' && r.atribucion.includes(r.autor.slice(0, 10)), 'atribución sin autor');
    assert.ok(r.atribucion.includes(r.licencia), 'atribución sin licencia');
    assert.match(r.sha256, /^[0-9a-f]{64}$/);
    assert.match(r.resolucion, /^\d+x\d+$/);
    assert.ok(r.vista && r.plataforma, 'faltan vista o plataforma');
    if (r.licencia !== 'Public domain') {
      assert.match(r.url_licencia ?? '', /^https:\/\/creativecommons\.org\//);
    }
  });

  test(`${r.id}: la foto no está en una ruta rastreada por git`, () => {
    assert.match(r.archivo, /^assets-src\/raw\/referencias-cc\//);
    const rastreados = execFileSync('git', ['ls-files', '--', r.archivo], { cwd: raiz, encoding: 'utf8' });
    assert.equal(rastreados.trim(), '');
  });
}

test('ninguna imagen de assets-src/raw/ está rastreada, y el manifiesto sí', () => {
  const imagenes = execFileSync('git', ['ls-files', '--', 'assets-src/raw/referencias-cc'], {
    cwd: raiz,
    encoding: 'utf8',
  });
  assert.equal(imagenes.trim(), '');
  const manifiestoRastreado = execFileSync('git', ['ls-files', '--', 'catalogo/referencias-cc.json'], {
    cwd: raiz,
    encoding: 'utf8',
  });
  assert.equal(manifiestoRastreado.trim(), 'catalogo/referencias-cc.json');
});
