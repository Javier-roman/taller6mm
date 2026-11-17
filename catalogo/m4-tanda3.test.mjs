// Valida el registro de la tanda 3 del M4 (generador paramétrico): nada publicable, nivel null, es_demo, cotas con
// fuente, elementos existentes en ar-m4.json, interfaces conocidas o propuestas, malla cerrada y ningún GLB en git.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(dir, '..');
const leer = (nombre) => JSON.parse(fs.readFileSync(path.join(dir, nombre), 'utf8'));
const { piezas, interfaces_nuevas: propuestas } = leer('m4-tanda3.json');
const mapa = leer('ar-m4.json');
const ids = new Set(mapa.elementos.map((e) => e.id));
const interfaces = new Set([
  ...leer('interfaces.json').interfaces.map((i) => i.id),
  ...mapa.interfaces_nuevas.map((i) => i.id),
  ...propuestas.map((i) => i.id),
]);

test('ids únicos y elementos del mapa existentes', () => {
  assert.ok(piezas.length >= 25);
  assert.equal(new Set(piezas.map((p) => p.id)).size, piezas.length);
  for (const p of piezas) assert.ok(p.elemento === null || ids.has(p.elemento), p.id);
});

test('ninguna pieza es publicable, todas son demo, sin nivel y con malla cerrada', () => {
  for (const p of piezas) {
    assert.equal(p.publicable, false, p.id);
    assert.equal(p.publicable_3d, false, p.id);
    assert.equal(p.nivel, null, p.id);
    assert.equal(p.es_demo, true, p.id);
    assert.equal(p.license_status, 'propio', p.id);
    assert.equal(p.aristas_abiertas, 0, p.id);
    assert.match(p.sha256_glb, /^[0-9a-f]{64}$/, p.id);
    assert.ok(p.sockets.length > 0, p.id);
  }
});

test('cada cota tiene fuente y lo desconocido es null con bandera', () => {
  for (const p of piezas) {
    for (const c of p.cotas) {
      assert.ok(c.fuente, `${p.id}.${c.clave}`);
      if (c.valor_mm === null) assert.equal(c.desconocido, true, `${p.id}.${c.clave}`);
    }
  }
});

test('los sockets usan interfaces del catálogo, del mapa o propuestas en este registro', () => {
  for (const p of piezas) {
    assert.equal(p.sockets.length, p.sockets_interfaz.length, p.id);
    for (const i of [...p.sockets_interfaz, ...p.requiere]) assert.ok(interfaces.has(i), `${p.id}: ${i}`);
  }
});

test('ningún GLB está rastreado por git', () => {
  const rastreados = execFileSync('git', ['ls-files'], { cwd: raiz, encoding: 'utf8' });
  assert.ok(!/\.(glb|gltf)$/im.test(rastreados));
});
