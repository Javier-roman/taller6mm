// Tests de fable-fin.mjs. Ejecuta: node --test ".claude/**/*.test.mjs"
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { esFable, FIN_FABLE, haPasadoElPlazo, quitarAsesorFable } from './fable-fin.mjs';

const tmp = () => mkdtempSync(path.join(os.tmpdir(), 't6m-fable-'));
const escribir = (dir, contenido) => {
  const f = path.join(dir, 'settings.local.json');
  writeFileSync(f, typeof contenido === 'string' ? contenido : JSON.stringify(contenido));
  return f;
};
const leer = (f) => JSON.parse(readFileSync(f, 'utf8'));

test('el plazo es el 16-11-2026 a las 23:59:59 de Madrid (CET)', () => {
  assert.equal(new Date(FIN_FABLE).toISOString(), '2026-11-16T22:59:59.000Z');
  assert.equal(
    new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', dateStyle: 'short', timeStyle: 'medium' }).format(
      FIN_FABLE,
    ),
    '16/11/26, 23:59:59',
  );
});

test('hasta el último segundo no cambia nada; un milisegundo después, sí', () => {
  const d = tmp();
  const f = escribir(d, { advisorModel: 'fable', otra: 1 });
  assert.equal(quitarAsesorFable(f, FIN_FABLE).cambio, 'ninguno');
  assert.equal(leer(f).advisorModel, 'fable');
  assert.equal(haPasadoElPlazo(FIN_FABLE), false);
  assert.equal(haPasadoElPlazo(FIN_FABLE + 1), true);
  const r = quitarAsesorFable(f, FIN_FABLE + 1);
  assert.equal(r.cambio, 'quitado');
  assert.match(r.mensaje, /Reinicia Claude Code/);
  assert.equal('advisorModel' in leer(f), false);
  rmSync(d, { recursive: true });
});

test('conserva las demás claves y es idempotente', () => {
  const d = tmp();
  const f = escribir(d, { enabledMcpjsonServers: ['playwright'], advisorModel: 'claude-fable-5-2', x: { y: 1 } });
  const t = FIN_FABLE + 60_000;
  assert.equal(quitarAsesorFable(f, t).cambio, 'quitado');
  assert.deepEqual(leer(f), { enabledMcpjsonServers: ['playwright'], x: { y: 1 } });
  assert.equal(quitarAsesorFable(f, t).cambio, 'ninguno');
  rmSync(d, { recursive: true });
});

test('solo quita el asesor si es Fable', () => {
  const d = tmp();
  const f = escribir(d, { advisorModel: 'opus' });
  assert.equal(quitarAsesorFable(f, FIN_FABLE + 1).cambio, 'ninguno');
  assert.equal(leer(f).advisorModel, 'opus');
  assert.ok(esFable('fable') && esFable('claude-fable-5-1[1m]') && !esFable('opus') && !esFable(undefined));
  rmSync(d, { recursive: true });
});

test('archivo ausente, JSON inválido o con otra forma: nunca lanza ni destruye', () => {
  const d = tmp();
  assert.equal(quitarAsesorFable(path.join(d, 'no-existe.json'), FIN_FABLE + 1).cambio, 'ninguno');
  const roto = escribir(d, '{ no es json');
  assert.equal(quitarAsesorFable(roto, FIN_FABLE + 1).cambio, 'error');
  assert.equal(readFileSync(roto, 'utf8'), '{ no es json');
  const lista = escribir(d, '[1,2]');
  assert.equal(quitarAsesorFable(lista, FIN_FABLE + 1).cambio, 'ninguno');
  rmSync(d, { recursive: true });
});
