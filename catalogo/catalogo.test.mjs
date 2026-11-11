// Valida el catálogo maestro: ids únicos, referencias existentes, ninguna cota sin fuente
// y todo lo «verificado» con URL y fecha. Solo Node, sin dependencias.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
const interfaces = load('interfaces.json').interfaces;
const { familias: familiasPlataforma, plataformas } = load('plataformas.json');
const familias = load('familias.json').familias;

const KEBAB = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const ESTADOS = ['verificado', 'pendiente'];
const NIVELES = ['T0', 'T1', 'T2'];
const ISO = /^\d{4}-\d{2}-\d{2}$/;
const esUrl = (u) => typeof u === 'string' && /^https:\/\/\S+$/.test(u);

const unicos = (lista, etiqueta) => {
  const ids = lista.map((x) => x.id);
  assert.equal(new Set(ids).size, ids.length, `ids duplicados en ${etiqueta}`);
  for (const id of ids) assert.match(id, KEBAB, `${etiqueta}: id no kebab-case: ${id}`);
};

test('ids únicos y en kebab-case', () => {
  unicos(interfaces, 'interfaces');
  unicos(plataformas, 'plataformas');
  unicos(familias, 'familias');
  unicos(familiasPlataforma, 'familias de plataforma');
});

test('todas las referencias existen', () => {
  const ifaceIds = new Set(interfaces.map((i) => i.id));
  const famPl = new Set(familiasPlataforma.map((f) => f.id));
  for (const p of plataformas) {
    assert.ok(famPl.has(p.familia), `${p.id}: familia desconocida ${p.familia}`);
    for (const i of p.interfaces) assert.ok(ifaceIds.has(i), `${p.id}: interfaz desconocida ${i}`);
    if (p.pozo_cargador !== null)
      assert.ok(ifaceIds.has(p.pozo_cargador), `${p.id}: pozo desconocido ${p.pozo_cargador}`);
  }
  for (const f of familias) {
    for (const i of f.interfaces) assert.ok(ifaceIds.has(i), `${f.id}: interfaz desconocida ${i}`);
    for (const a of f.aplica_a) assert.ok(a === '*' || famPl.has(a), `${f.id}: aplica_a desconocido ${a}`);
  }
});

test('estado válido y niveles T0-T2', () => {
  for (const x of [...interfaces, ...plataformas, ...familias])
    assert.ok(ESTADOS.includes(x.estado), `${x.id}: estado ${x.estado}`);
  for (const f of familias) assert.ok(NIVELES.includes(f.nivel_esperado), `${f.id}: nivel ${f.nivel_esperado}`);
});

test('ninguna cota sin fuente, URL, fecha y confianza', () => {
  for (const i of interfaces) {
    for (const c of i.cotas) {
      assert.equal(typeof c.valor, 'number', `${i.id}: cota «${c.nombre}» sin valor numérico`);
      assert.ok(c.unidad, `${i.id}: cota «${c.nombre}» sin unidad`);
      assert.ok(esUrl(c.fuente), `${i.id}: cota «${c.nombre}» sin URL de fuente`);
      assert.match(c.fecha_consulta ?? '', ISO, `${i.id}: cota «${c.nombre}» sin fecha`);
      assert.ok(['alta', 'media'].includes(c.confianza), `${i.id}: cota «${c.nombre}» sin confianza`);
    }
    if (i.estado === 'pendiente') assert.equal(i.cotas.length, 0, `${i.id}: pendiente no puede llevar cotas`);
  }
  for (const x of [...plataformas, ...familias])
    assert.equal(x.cotas, undefined, `${x.id}: las cotas viven en interfaces`);
});

test('todo lo verificado tiene URL y fecha', () => {
  for (const x of [...interfaces, ...plataformas, ...familias]) {
    if (x.estado !== 'verificado') continue;
    assert.ok(x.fuente && esUrl(x.fuente.url), `${x.id}: verificado sin URL`);
    assert.match(x.fuente.fecha_consulta ?? '', ISO, `${x.id}: verificado sin fecha`);
    assert.ok(['alta', 'media'].includes(x.confianza), `${x.id}: verificado sin confianza`);
  }
});

test('el catálogo tiene la amplitud mínima esperada', () => {
  assert.ok(plataformas.length >= 80);
  assert.ok(familias.length >= 60);
  assert.ok(interfaces.length >= 60);
});
