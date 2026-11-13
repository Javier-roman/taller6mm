// Valida catalogo/ar-m4.json: ids únicos, referencias a familias, interfaces y plataformas válidas,
// oleada en 1..3 y ninguna cota verificada sin URL y fecha. Solo Node, sin dependencias.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
const mapa = load('ar-m4.json');
const familias = new Set(load('familias.json').familias.map((f) => f.id));
const plataformas = new Set(load('plataformas.json').plataformas.map((p) => p.id));
const nuevas = new Set(mapa.interfaces_nuevas.map((i) => i.id));
const interfaces = new Set([...load('interfaces.json').interfaces.map((i) => i.id), ...nuevas]);
const zonas = new Set(mapa.zonas.map((z) => z.id));

const KEBAB = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const ISO = /^\d{4}-\d{2}-\d{2}$/;
const NIVELES = ['T0', 'T1', 'T2'];
const ESTADOS = ['pendiente', 'verificado'];
const VETADAS = ['fullmetal', 'ranger', 'icsbb', 'evike.eu', 'evike-europe', 'hobbyexpert'];

test('ids únicos y en kebab-case (elementos e interfaces nuevas)', () => {
  const ids = mapa.elementos.map((e) => e.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const id of ids) assert.match(id, KEBAB);
  for (const id of nuevas) {
    assert.match(id, KEBAB);
    assert.ok(!load('interfaces.json').interfaces.some((i) => i.id === id), `${id} ya existe`);
  }
});

test('referencias válidas a zonas, familias, interfaces y plataformas', () => {
  for (const e of mapa.elementos) {
    assert.ok(zonas.has(e.zona), `${e.id}: zona ${e.zona}`);
    assert.ok(familias.has(e.familia), `${e.id}: familia ${e.familia}`);
    for (const i of [...e.interfaces_usa, ...e.interfaces_ofrece])
      assert.ok(interfaces.has(i), `${e.id}: interfaz ${i}`);
    for (const p of e.plataformas) assert.ok(plataformas.has(p), `${e.id}: plataforma ${p}`);
    assert.ok(Array.isArray(e.parametros) && e.parametros.length > 0, `${e.id}: parámetros`);
  }
});

test('prioridad de oleada 1..3, nivel y estado válidos', () => {
  for (const e of mapa.elementos) {
    assert.ok([1, 2, 3].includes(e.oleada), `${e.id}: oleada ${e.oleada}`);
    assert.ok(NIVELES.includes(e.nivel_esperado), `${e.id}: nivel ${e.nivel_esperado}`);
    assert.ok(ESTADOS.includes(e.estado), `${e.id}: estado ${e.estado}`);
    assert.ok(e.fuente_cotas?.tipo in mapa.fuentes_tipo, `${e.id}: tipo de fuente`);
  }
});

test('sin cotas verificadas sin URL y fecha; sin webs vetadas', () => {
  for (const e of mapa.elementos) {
    if (e.estado === 'verificado') assert.ok(e.cotas.length > 0, `${e.id}: verificado sin cotas`);
    for (const c of e.cotas) {
      assert.ok(typeof c.fuente === 'string' && /^https?:\/\//.test(c.fuente), `${e.id}: cota sin URL`);
      assert.match(String(c.fecha_consulta), ISO, `${e.id}: cota sin fecha`);
      for (const v of VETADAS) assert.ok(!c.fuente.toLowerCase().includes(v), `${e.id}: web vetada ${v}`);
    }
  }
});

test('el orden de la oleada 1 cubre zonas existentes sin repetir', () => {
  const orden = mapa.orden_oleada1.map((o) => o.zona);
  assert.equal(new Set(orden).size, orden.length);
  for (const z of orden) assert.ok(zonas.has(z), z);
  for (const [i, o] of mapa.orden_oleada1.entries()) assert.equal(o.orden, i + 1);
});
