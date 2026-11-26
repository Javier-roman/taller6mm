// Valida los registros de las réplicas guiadas por silueta: solo números (nada de píxeles), procedencia «aportadas por
// Javi», todo T0 y no publicable, confianza declarada y variantes siempre marcadas como DERIVADAS.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const load = (n) => JSON.parse(fs.readFileSync(path.join(dir, n), 'utf8'));
const siluetas = load('siluetas-referencia.json').replicas;
const piezas = load('siluetas-piezas.json').replicas;
const variantes = load('variantes-derivadas.json').plataformas;

test('siluetas de referencia: números con fuente y confianza, sin imágenes incrustadas', () => {
  assert.ok(siluetas.length >= 5);
  assert.equal(new Set(siluetas.map((r) => r.id)).size, siluetas.length);
  for (const r of siluetas) {
    assert.match(r.procedencia, /aportadas por Javi/, r.id);
    assert.match(r.fuente_medida, /^medido en foto de referencia interna/, r.id);
    assert.ok(r.calibre.fuente && r.calibre.confianza && r.calibre.mm_por_px > 0, r.id);
    assert.match(r.foto_sha256, /^[0-9a-f]{64}$/, r.id);
    assert.ok(Object.keys(r.partes).length >= 5, r.id);
    for (const p of Object.values(r.partes)) {
      assert.ok(p.contorno_mm.length >= 6);
      for (const [x, y] of p.contorno_mm) assert.ok(Number.isFinite(x) && Number.isFinite(y));
    }
    assert.ok(!/base64|data:image/.test(JSON.stringify(r)), r.id);
    assert.ok(r.colores_fuente.startsWith('medido en foto de referencia interna'), r.id);
  }
});

test('piezas construidas: T0, no publicables, mallas cerradas y IoU declarado', () => {
  const ids = new Set(siluetas.map((r) => r.id));
  for (const r of piezas) {
    assert.ok(ids.has(r.id), r.id);
    assert.equal(r.nivel, 'T0');
    assert.equal(r.publicable_3d, false);
    assert.equal(r.es_demo, false);
    for (const [n, p] of Object.entries(r.partes)) {
      assert.equal(p.aristas_abiertas, 0, `${r.id}.${n}`);
      assert.match(p.sha256, /^[0-9a-f]{16}$/);
    }
    if (r.iou_silueta_lateral !== null) assert.ok(r.iou_silueta_lateral > 0.5 && r.iou_silueta_lateral <= 1);
    assert.ok(r.iou_nota.includes('no una verificación independiente'));
  }
});

test('variantes: siempre derivadas, T0, confianza baja-media y con fuente de longitud', () => {
  const ids = new Set(siluetas.map((r) => r.id));
  assert.ok(variantes.length >= 4);
  for (const pl of variantes) {
    assert.ok(ids.has(pl.base), pl.plataforma);
    assert.ok(pl.variantes.length >= 3, pl.plataforma);
    for (const v of pl.variantes) {
      assert.equal(v.derivada_de, pl.base);
      assert.equal(v.nivel, 'T0');
      assert.equal(v.confianza, 'baja-media');
      assert.equal(v.publicable_3d, false);
      assert.equal(v.es_demo, true);
      assert.match(v.aviso, /^DERIVADA de /);
      assert.ok(v.fuente_longitud.length > 10);
      assert.equal(v.aristas_abiertas, 0, v.id);
    }
  }
});
