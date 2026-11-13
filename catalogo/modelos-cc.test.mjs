// Valida el manifiesto de modelos 3D de licencia abierta: licencia permitida, URL, autor,
// sha256 y que ningún archivo de modelo esté rastreado por git. Solo Node, sin dependencias.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(dir, '..');
const { modelos } = JSON.parse(fs.readFileSync(path.join(dir, 'modelos-cc.json'), 'utf8'));

const LICENCIAS = ['CC0', 'CC-BY', 'PD'];
const VEREDICTOS = ['valido_base_forma', 'solo_referencia_volumen', 'cubito_descartado'];
const EXT_MODELO = /\.(obj|fbx|blend|glb|gltf|stl|3ds|dae|ply|zip|mtl)$/i;

test('hay modelos y ids únicos', () => {
  assert.ok(modelos.length > 0);
  const ids = modelos.map((m) => m.id);
  assert.equal(new Set(ids).size, ids.length);
});

test('cada modelo: licencia permitida, URL, autor, sha256, fecha y veredicto', () => {
  for (const m of modelos) {
    assert.ok(LICENCIAS.includes(m.licencia), `${m.id}: licencia no permitida ${m.licencia}`);
    assert.match(m.url_ficha, /^https:\/\/\S+$/, `${m.id}: url_ficha`);
    assert.match(m.url_descarga, /^https:\/\/\S+$/, `${m.id}: url_descarga`);
    assert.ok(m.autor && m.autor.length > 1, `${m.id}: autor`);
    assert.match(m.sha256, /^[0-9a-f]{64}$/, `${m.id}: sha256`);
    assert.match(m.fecha_consulta, /^\d{4}-\d{2}-\d{2}$/, `${m.id}: fecha`);
    assert.ok(VEREDICTOS.includes(m.veredicto), `${m.id}: veredicto`);
    assert.ok(m.motivos?.length > 10, `${m.id}: motivos`);
    assert.ok(Number.isInteger(m.triangulos) && m.triangulos > 0, `${m.id}: triángulos`);
    assert.ok(m.bbox_unidades.longitud > 0, `${m.id}: bbox`);
  }
});

test('ningún archivo de modelo está rastreado por git', () => {
  const rastreados = execFileSync('git', ['ls-files'], { cwd: raiz, encoding: 'utf8' }).split('\n').filter(Boolean);
  const malos = rastreados.filter((f) => EXT_MODELO.test(f) || f.startsWith('assets-src/raw/'));
  assert.deepEqual(malos, []);
});
