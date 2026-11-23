// Valida el registro de la familia de pistolas (Hi-Capa y Glock, generador paramétrico): nada publicable, nivel null,
// es_demo, cotas con fuente, plataformas existentes, montajes completos que encajan y ningún GLB rastreado por git.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(dir, '..');
const { piezas, montajes } = JSON.parse(fs.readFileSync(path.join(dir, 'pistolas-piezas.json'), 'utf8'));
const { plataformas } = JSON.parse(fs.readFileSync(path.join(dir, 'plataformas.json'), 'utf8'));
const idsPlataforma = new Set(plataformas.map((p) => p.id));

test('ids únicos y las cinco familias de la tanda presentes', () => {
  assert.ok(piezas.length >= 14);
  assert.equal(new Set(piezas.map((p) => p.id)).size, piezas.length);
  const familias = new Set(piezas.map((p) => p.familia));
  for (const f of [
    'armazon.pistola',
    'cacha.hicapa',
    'corredera.pistola',
    'canon.pistola',
    'mira.pistola',
    'cargador.gas_pistola',
  ]) {
    assert.ok(familias.has(f), f);
  }
  assert.ok(!piezas.some((p) => /revolver/i.test(p.id)), 'el revólver queda fuera del alcance');
});

test('ninguna pieza es publicable, todas son demo y sin nivel, con malla cerrada', () => {
  for (const p of piezas) {
    assert.equal(p.publicable, false, p.id);
    assert.equal(p.publicable_3d, false, p.id);
    assert.equal(p.nivel, null, p.id);
    assert.equal(p.es_demo, true, p.id);
    assert.equal(p.license_status, 'propio', p.id);
    assert.match(p.sha256_glb, /^[0-9a-f]{64}$/, p.id);
    assert.equal(p.aristas_abiertas, 0, p.id);
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

test('las plataformas citadas existen en plataformas.json', () => {
  for (const p of piezas) {
    assert.ok(p.plataformas.length > 0, p.id);
    for (const pl of p.plataformas) assert.ok(idsPlataforma.has(pl), `${p.id}: plataforma ${pl}`);
  }
});

test('los dos montajes completos encajan y son T0 sin publicar', () => {
  assert.deepEqual(montajes.map((m) => m.id).sort(), ['glock-17-gbb', 'hicapa-5-1']);
  for (const m of montajes) {
    assert.equal(m.todo_encaja, true, m.id);
    assert.equal(m.nivel, 'T0', m.id);
    assert.equal(m.publicable_3d, false, m.id);
    for (const c of m.comprobaciones) assert.equal(c.encaja, true, `${m.id}: ${c.hijo}`);
    const roles = new Set(m.piezas.map((p) => p.id));
    for (const r of ['armazon', 'corredera', 'canon', 'mira_trasera', 'mira_delantera', 'cargador']) {
      assert.ok(roles.has(r), `${m.id}: falta ${r}`);
    }
    for (const p of m.piezas) assert.equal(p.aristas_abiertas, 0, `${m.id}: ${p.id}`);
  }
  assert.ok(montajes.find((m) => m.id === 'hicapa-5-1').piezas.some((p) => p.id === 'cacha_izq'));
});

test('ningún GLB está rastreado por git', () => {
  const rastreados = execFileSync('git', ['ls-files'], { cwd: raiz, encoding: 'utf8' });
  assert.ok(!/\.(glb|gltf)$/im.test(rastreados));
});
