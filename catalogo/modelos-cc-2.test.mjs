import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const raiz = join(dirname(fileURLToPath(import.meta.url)), '..');
const manifiesto = JSON.parse(readFileSync(join(raiz, 'catalogo', 'modelos-cc-2.json'), 'utf8'));
const modelos = manifiesto.modelos;

// Solo CC0, dominio público y CC-BY. Nada de SA, NC ni ND.
const LICENCIAS = /^(Public domain|CC0|CC BY \d\.\d)$/;
const VEREDICTOS = ['valido_como_base_de_forma', 'solo_referencia', 'cubito_descartado'];

test('hay modelos y como máximo 8 evaluados', () => {
  assert.ok(modelos.length >= 1 && modelos.length <= 8);
});

test('ids, archivos y hashes no se repiten', () => {
  for (const k of ['id', 'archivo', 'sha256']) {
    assert.equal(new Set(modelos.map((m) => m[k])).size, modelos.length, k);
  }
});

for (const m of modelos) {
  test(`${m.id}: licencia, procedencia y atribución`, () => {
    assert.match(m.licencia, LICENCIAS, `licencia no permitida: ${m.licencia}`);
    assert.doesNotMatch(m.licencia, /SA|NC|ND/);
    assert.match(m.url, /^https:\/\/(sketchfab\.com|poly\.pizza)\//);
    assert.match(m.url_licencia, /^https:\/\/creativecommons\.org\//);
    assert.ok(typeof m.autor === 'string' && m.autor.trim().length > 0, 'falta el autor');
    assert.ok(m.atribucion.includes(m.autor) && m.atribucion.includes(m.licencia));
    assert.match(m.sha256, /^[0-9a-f]{64}$/);
    assert.ok(Number.isInteger(m.triangulos) && m.triangulos > 0);
    assert.ok(VEREDICTOS.includes(m.veredicto), `veredicto desconocido: ${m.veredicto}`);
  });

  test(`${m.id}: el binario no está en una ruta rastreada por git`, () => {
    assert.match(m.archivo, /^assets-src\/raw\/modelos-cc\//);
    const r = execFileSync('git', ['ls-files', '--', m.archivo], { cwd: raiz, encoding: 'utf8' });
    assert.equal(r.trim(), '');
  });
}

test('los descartados por licencia no llevan licencia permitida ni binario', () => {
  for (const d of manifiesto.descartados_por_licencia) {
    assert.ok(d.motivo.length > 10);
    assert.doesNotMatch(d.licencia_actual, LICENCIAS);
    assert.equal(d.sha256, undefined);
  }
});

test('ningún modelo 3D de assets-src/raw está rastreado', () => {
  const r = execFileSync('git', ['ls-files', '--', 'assets-src/raw/modelos-cc'], { cwd: raiz, encoding: 'utf8' });
  assert.equal(r.trim(), '');
});
