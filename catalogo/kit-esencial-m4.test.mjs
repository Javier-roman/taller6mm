// Valida el registro del kit esencial M4: licencia CC0/CC BY, URL, autor, atribución, sha256,
// publicable false y que ningún GLB esté rastreado por git. Solo Node, sin dependencias.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(dir, '..');
const { piezas, descartadas, huecos } = JSON.parse(fs.readFileSync(path.join(dir, 'kit-esencial-m4.json'), 'utf8'));
const LICENCIAS = ['CC0 1.0', 'CC BY 4.0'];

test('hay piezas con ids únicos', () => {
  assert.ok(piezas.length >= 5);
  assert.equal(new Set(piezas.map((p) => p.id)).size, piezas.length);
});

test('ninguna pieza es publicable y todas tienen sockets', () => {
  for (const p of piezas) {
    assert.equal(p.publicable, false, p.id);
    assert.ok(p.sockets.length > 0, p.id);
    assert.match(p.sha256_glb, /^[0-9a-f]{64}$/, p.id);
  }
});

test('los modelos CC traen licencia admitida, URL, autor y atribución', () => {
  for (const p of piezas.filter((x) => x.origen === 'modelo-cc')) {
    assert.ok(LICENCIAS.includes(p.licencia), `${p.id}: ${p.licencia}`);
    assert.match(p.url, /^https:\/\//, p.id);
    assert.ok(p.autor, p.id);
    assert.ok(p.atribucion.includes(p.autor) && p.atribucion.includes(p.url), p.id);
    assert.match(p.licencia_verificada, /^\d{4}-\d{2}-\d{2}$/, p.id);
  }
});

test('ninguna escala inventa una cota: o hay fuente o es relativa', () => {
  for (const p of piezas.filter((x) => x.origen === 'modelo-cc')) {
    if (p.escala.modo === 'cota') {
      assert.match(p.escala.fuente, /^https:\/\//, p.id);
      assert.equal(p.escala.confianza, 'baja', p.id);
    } else {
      assert.equal(p.escala.modo, 'relativa', p.id);
    }
  }
});

test('ningún GLB está rastreado por git', () => {
  const rastreados = execFileSync('git', ['ls-files'], { cwd: raiz, encoding: 'utf8' });
  assert.ok(!/\.(glb|gltf)$/im.test(rastreados));
});

test('la culata NIXO está descartada y queda un hueco explícito', () => {
  assert.ok(!piezas.some((p) => p.id === 'culata-nixo'));
  assert.ok(descartadas.some((d) => d.pieza === 'culata-nixo' && d.estado === 'descartado'));
  assert.ok(huecos.some((h) => /pendiente: culata telescópica tipo STR/.test(h.nota)));
});

test('sin escala con cota no hay nivel: candidata con nivel null', () => {
  for (const p of piezas) {
    if (p.escala?.modo === 'relativa' || p.origen === 'generador') {
      assert.equal(p.nivel, null, p.id);
      assert.equal(p.candidata, true, p.id);
    }
  }
});
