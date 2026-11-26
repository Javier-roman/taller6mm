import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const raiz = join(dirname(fileURLToPath(import.meta.url)), '..');
const registro = JSON.parse(readFileSync(join(raiz, 'catalogo', 'replicas-ilustrativas.json'), 'utf8'));
const modelos = registro.modelos;

// Solo CC0 y CC BY (con atribución). Nada de SA, NC ni ND.
const LICENCIAS = /^(CC0 1\.0|CC BY 4\.0)$/;
const CLASES = new Set(Object.keys(registro.clases));

test('hay entre 3 y 10 modelos y los ids no se repiten', () => {
  assert.ok(modelos.length >= 3 && modelos.length <= 10);
  assert.equal(new Set(modelos.map((m) => m.id)).size, modelos.length);
});

for (const m of modelos) {
  test(`${m.id}: procedencia, licencia y atribución`, () => {
    const f = m.fuente;
    assert.match(f.licencia, LICENCIAS, `licencia no permitida: ${f.licencia}`);
    assert.match(f.url_licencia, /^https:\/\/creativecommons\.org\//);
    assert.match(f.url_ficha, /^https:\/\/(opengameart\.org|sketchfab\.com)\//);
    assert.ok(typeof f.autor === 'string' && f.autor.trim().length > 0, 'falta el autor');
    assert.match(f.fecha_verificacion, /^\d{4}-\d{2}-\d{2}$/);
    assert.match(f.sha256, /^[0-9a-f]{64}$/);
    assert.match(f.archivo, /^assets-src\/raw\/modelos-cc\//, 'el binario vive en la carpeta ignorada');
    assert.ok(f.atribucion.includes(f.autor), 'la atribución nombra al autor');
    if (f.licencia.startsWith('CC BY')) {
      assert.ok(f.atribucion.includes('CC BY 4.0'), 'CC BY exige atribución con la licencia');
    }
  });

  test(`${m.id}: ilustrativa, T0 y no publicable hasta revisión humana`, () => {
    assert.equal(m.nivel, 'T0');
    assert.equal(m.ilustrativa, true);
    assert.equal(m.publicable, false, 'publicable solo tras revisión humana de procedencia (docs/05 §5)');
    assert.equal(m.medidas_verificadas, false);
    assert.equal(m.es_replica_exacta, false);
    assert.ok(m.marcajes.texturas_originales_descartadas === true, 'las texturas originales no se usan');
    assert.ok(m.marcajes.logos_o_marcajes_en_geometria === false, 'sin logos ni marcajes en la forma');
    assert.ok(typeof m.aviso === 'string' && m.aviso.length > 20, 'el aviso al visitante es obligatorio');
  });

  test(`${m.id}: escala honesta (cota citada o convención con bandera)`, () => {
    const e = m.escala;
    assert.ok(['citada', 'convencion', 'relativa'].includes(e.tipo));
    assert.ok(Number.isFinite(e.largo_mm_render) && e.largo_mm_render > 0);
    if (e.tipo === 'citada') {
      assert.ok(e.fuente_cota && e.confianza, 'una cota citada lleva fuente y confianza');
    } else {
      assert.equal(e.longitud_mm_verificada, null, 'lo no verificado es null');
      assert.ok(e.bandera && e.bandera.length > 10, 'la convención lleva bandera');
    }
  });

  test(`${m.id}: configuración de render coherente`, () => {
    const r = m.render;
    assert.ok(CLASES.has(r.clase));
    assert.ok(r.materiales?.[r.zona_defecto], 'la zona por defecto existe');
    for (const z of r.zonas) assert.ok(r.materiales[z.mat], `material desconocido: ${z.mat}`);
  });
}
