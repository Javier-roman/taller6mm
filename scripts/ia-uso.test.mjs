// Tests de pnpm ia:uso con líneas sintéticas (sin leer registros reales).
import assert from 'node:assert/strict';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { contadores, registros, sumar } from './ia-uso.mjs';

const respuesta = (id, model, dia, u, extra = {}) =>
  JSON.stringify({
    type: 'assistant',
    timestamp: `${dia}T10:00:00.000Z`,
    message: { id, model, content: [{ type: 'text', text: 'CONTENIDO SECRETO' }], usage: u },
    ...extra,
  });

const U = { input_tokens: 10, cache_creation_input_tokens: 100, cache_read_input_tokens: 1000, output_tokens: 5 };

test('solo devuelve contadores, nunca el contenido', () => {
  const c = contadores(respuesta('m1', 'claude-sonnet-5-5', '2026-11-05', U));
  assert.equal(c.id, 'm1');
  assert.equal(c.dia, '2026-11-05');
  assert.doesNotMatch(JSON.stringify(c), /SECRETO/);
  assert.equal(contadores('{"type":"user","message":{"content":"x"}}'), null);
  assert.equal(contadores('no json'), null);
  assert.equal(contadores(respuesta('s', '<synthetic>', '2026-11-05', U)), null);
});

test('una respuesta repetida en varias líneas cuenta una vez', () => {
  const l = respuesta('m1', 'claude-sonnet-5-5', '2026-11-05', U);
  const [f] = sumar([l, l, l]);
  assert.deepEqual(f, {
    dia: '2026-11-05',
    modelo: 'claude-sonnet-5-5',
    peticiones: 1,
    entrada: 10,
    cache_escrita: 100,
    cache_leida: 1000,
    salida: 5,
  });
});

test('separa por día y modelo, filtra fechas y cuenta el asesor aparte', () => {
  const conAsesor = {
    ...U,
    iterations: [
      { type: 'message', input_tokens: 10, output_tokens: 5 },
      { type: 'advisor_message', model: 'claude-opus-5-5', input_tokens: 2000, output_tokens: 300 },
    ],
  };
  const filas = sumar(
    [
      respuesta('a', 'claude-sonnet-5-5', '2026-11-05', conAsesor),
      respuesta('b', 'claude-opus-5-5', '2026-11-05', U),
      respuesta('c', 'claude-sonnet-5-5', '2026-11-06', U),
      respuesta('d', 'claude-sonnet-5-5', '2026-10-01', U),
    ],
    { desde: '2026-11-01' },
  );
  assert.deepEqual(
    filas.map((f) => `${f.dia} ${f.modelo} ${f.peticiones} ${f.salida}`),
    [
      '2026-11-05 asesor:claude-opus-5-5 1 300',
      '2026-11-05 claude-opus-5-5 1 5',
      '2026-11-05 claude-sonnet-5-5 1 5',
      '2026-11-06 claude-sonnet-5-5 1 5',
    ],
  );
});

test('lee las carpetas del proyecto (y la antigua de bancada), con subagentes, y no otras', () => {
  const base = path.join(os.tmpdir(), `t6m-uso-${process.pid}`);
  for (const d of ['C--dev-taller6mm/s1/subagents', 'C--dev-bancada', 'C--dev-taller6mm-armeria', 'C--dev-otro']) {
    mkdirSync(path.join(base, d), { recursive: true });
  }
  writeFileSync(path.join(base, 'C--dev-taller6mm', 's1.jsonl'), '');
  writeFileSync(path.join(base, 'C--dev-taller6mm', 's1', 'subagents', 'a.jsonl'), '');
  writeFileSync(path.join(base, 'C--dev-bancada', 'v.jsonl'), '');
  writeFileSync(path.join(base, 'C--dev-taller6mm-armeria', 'w.jsonl'), '');
  writeFileSync(path.join(base, 'C--dev-otro', 'x.jsonl'), '');
  const nombres = registros(base)
    .map((p) => path.basename(p))
    .sort();
  assert.deepEqual(nombres, ['a.jsonl', 's1.jsonl', 'v.jsonl', 'w.jsonl']);
  assert.deepEqual(registros(path.join(base, 'no-existe')), []);
  rmSync(base, { recursive: true, force: true });
});
