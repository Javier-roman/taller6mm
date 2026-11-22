import assert from 'node:assert/strict';
import { test } from 'node:test';
import { decidir } from './fusionar-pr.mjs';

const ok = { nombre: 'verify', estado: 'pass' };

test('fusiona solo con CI verde y rama limpia', () => {
  assert.equal(decidir({ estado: 'OPEN', mergeState: 'CLEAN', checks: [ok] }).accion, 'fusionar');
});

test('espera si hay checks pendientes', () => {
  const r = decidir({ estado: 'OPEN', mergeState: 'BLOCKED', checks: [ok, { nombre: 'e2e', estado: 'pending' }] });
  assert.equal(r.accion, 'esperar');
});

test('nunca fusiona con un check en rojo', () => {
  const r = decidir({ estado: 'OPEN', mergeState: 'BLOCKED', checks: [ok, { nombre: 'sast', estado: 'fail' }] });
  assert.equal(r.accion, 'parar');
  assert.match(r.motivo, /sast/);
});

test('actualiza la rama si va por detrás', () => {
  assert.equal(decidir({ estado: 'OPEN', mergeState: 'BEHIND', checks: [ok] }).accion, 'actualizar');
});

test('para con conflictos y con PR cerrado; reconoce el ya fusionado', () => {
  assert.equal(decidir({ estado: 'OPEN', mergeState: 'DIRTY', checks: [ok] }).accion, 'parar');
  assert.equal(decidir({ estado: 'CLOSED', mergeState: 'UNKNOWN', checks: [] }).accion, 'parar');
  assert.equal(decidir({ estado: 'MERGED', mergeState: 'UNKNOWN', checks: [] }).accion, 'hecho');
});

test('ignora los checks omitidos', () => {
  const r = decidir({
    estado: 'OPEN',
    mergeState: 'CLEAN',
    checks: [ok, { nombre: 'PR cerrado', estado: 'skipping' }],
  });
  assert.equal(r.accion, 'fusionar');
});
