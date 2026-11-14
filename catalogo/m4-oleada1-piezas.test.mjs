// Valida catalogo/m4-oleada1-piezas.json: ids únicos, elementos reales del mapa, todo es de demostración,
// nada publicable, sockets presentes, sha256 válido y ningún GLB rastreado por git. Solo Node, sin dependencias.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(dir, '..');
const load = (name) => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
const { piezas } = load('m4-oleada1-piezas.json');
const elementos = new Map(load('ar-m4.json').elementos.map((e) => [e.id, e]));

test('ids únicos y elementos que existen en el mapa', () => {
  assert.equal(new Set(piezas.map((p) => p.id)).size, piezas.length);
  for (const p of piezas) {
    if (p.elemento !== null) assert.ok(elementos.has(p.elemento), `${p.id}: ${p.elemento}`);
  }
});

test('ninguna pieza es publicable ni tiene nivel: son candidatas de demostración', () => {
  for (const p of piezas) {
    assert.equal(p.origen, 'generador', p.id);
    assert.equal(p.publicable, false, p.id);
    assert.equal(p.publicable_3d, false, p.id);
    assert.equal(p.es_demo, true, p.id);
    assert.equal(p.nivel, null, p.id);
    assert.equal(p.candidata, true, p.id);
    assert.ok(p.sockets.length > 0 && p.sockets.every((s) => s.startsWith('socket.')), p.id);
    assert.match(p.sha256_glb, /^[0-9a-f]{64}$/, p.id);
  }
});

test('cada cota con valor lleva fuente, fecha y confianza; sin valor, la bandera desconocido', () => {
  for (const p of piezas) {
    for (const c of p.cotas) {
      assert.ok(c.fuente, `${p.id}.${c.clave}`);
      assert.match(c.fecha, /^\d{4}-\d{2}-\d{2}$/, `${p.id}.${c.clave}`);
      if (c.valor_mm === null) assert.equal(c.desconocido, true, `${p.id}.${c.clave}`);
      else assert.ok(['alta', 'media', 'baja'].includes(c.confianza), `${p.id}.${c.clave}`);
    }
  }
});

test('cubre elementos de la oleada 1 de pistoletes, guardamanos, miras y accesorios', () => {
  const cubiertos = new Set(piezas.map((p) => p.elemento).filter(Boolean));
  const oleada1 = [...cubiertos].filter((id) => elementos.get(id).oleada === 1);
  assert.ok(oleada1.length >= 19, `solo ${oleada1.length}`);
});

test('ningún GLB está rastreado por git', () => {
  const rastreados = execFileSync('git', ['ls-files'], { cwd: raiz, encoding: 'utf8' });
  assert.ok(!/\.(glb|gltf)$/im.test(rastreados));
});
