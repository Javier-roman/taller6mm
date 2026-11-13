// Valida catalogo/cotas-airsoft.json: ninguna cota sin fuente, URL y fecha en todo lo no null,
// confianza válida y familias existentes. Solo Node, sin dependencias.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
const cotas = load('cotas-airsoft.json').cotas;
const familias = new Set(load('familias.json').familias.map((f) => f.id));

const KEBAB = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const ISO = /^\d{4}-\d{2}-\d{2}$/;
const CONFIANZAS = ['alta', 'media', 'baja'];
const ESTADOS = ['verificado', 'citado', 'pendiente'];
// Webs vetadas por reserva de IA o por prohibir reproducir (docs/04 §3, diligencia 05-11-2026).
const VETADAS = [
  'fullmetal',
  'ranger',
  'icsbb',
  'evike.eu',
  'evike-europe',
  'hobbyexpert',
  'airsoftgandia',
  'quimera',
  'vsgun',
];
const tieneValor = (c) => c.valor !== null || c.valor_min !== null || c.valor_max !== null;

test('ids únicos y en kebab-case', () => {
  const ids = cotas.map((c) => c.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const id of ids) assert.match(id, KEBAB);
});

test('estado y ámbito válidos; piezas con familia existente', () => {
  for (const c of cotas) {
    assert.ok(ESTADOS.includes(c.estado), `${c.id}: estado ${c.estado}`);
    assert.ok(['pieza', 'replica'].includes(c.ambito), `${c.id}: ámbito`);
    if (c.ambito === 'pieza') assert.ok(familias.has(c.familia), `${c.id}: familia desconocida ${c.familia}`);
  }
});

test('ninguna cota sin fuente: todo lo no null lleva URL, fecha y confianza', () => {
  for (const c of cotas.filter(tieneValor)) {
    assert.ok(Array.isArray(c.fuentes) && c.fuentes.length > 0, `${c.id}: sin fuente`);
    for (const u of c.fuentes) assert.match(u, /^https:\/\/\S+$/, `${c.id}: URL inválida`);
    assert.match(c.fecha_consulta ?? '', ISO, `${c.id}: fecha`);
    assert.ok(CONFIANZAS.includes(c.confianza), `${c.id}: confianza ${c.confianza}`);
    assert.notEqual(c.estado, 'pendiente', `${c.id}: con valor no puede ser pendiente`);
    assert.ok(c.unidad, `${c.id}: sin unidad`);
  }
});

test('lo null está pendiente, sin fuente inventada ni confianza', () => {
  for (const c of cotas.filter((x) => !tieneValor(x))) {
    assert.equal(c.estado, 'pendiente', `${c.id}`);
    assert.equal(c.confianza, null, `${c.id}`);
    assert.deepEqual(c.fuentes, [], `${c.id}`);
    assert.ok(c.nota, `${c.id}: un hueco debe explicar por qué`);
  }
});

test('confianza alta solo con ficha del fabricante (estado verificado)', () => {
  for (const c of cotas) {
    assert.equal(c.confianza === 'alta', c.estado === 'verificado', `${c.id}: alta ⇔ verificado`);
  }
});

test('rangos coherentes y media con al menos dos fuentes', () => {
  for (const c of cotas.filter(tieneValor)) {
    if (c.valor_min !== null || c.valor_max !== null) {
      assert.ok(c.valor_min !== null && c.valor_max !== null && c.valor_min <= c.valor_max, `${c.id}: rango`);
    }
    if (c.confianza === 'media') assert.ok(c.fuentes.length >= 2, `${c.id}: media exige ≥ 2 fuentes`);
  }
});

test('no se usan webs vetadas', () => {
  for (const c of cotas) {
    for (const u of c.fuentes) {
      const host = new URL(u).hostname.replace(/[^a-z]/g, '');
      for (const v of VETADAS) assert.ok(!host.includes(v), `${c.id}: fuente vetada ${u}`);
    }
  }
});

test('manifiesto de referencias CC: licencia abierta y hash', () => {
  const { referencias } = load('referencias-cc.json');
  for (const r of referencias) {
    assert.match(r.sha256, /^[0-9a-f]{64}$/, r.id);
    assert.match(r.url, /^https:\/\/\S+$/, r.id);
    assert.ok(r.autor && r.atribucion && r.vista, r.id);
    assert.match(r.licencia, /^(CC0|CC BY \d|CC-BY|Dominio público)/, `${r.id}: licencia no admitida`);
  }
});
