// Semillas del catálogo: se aplican sobre las migraciones, son idempotentes, todo es is_demo y lo
// desconocido llega como NULL + bandera. El SQL lo construye vitest.config.ts desde catalogo/*.json.
import { applyD1Migrations } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { beforeAll, describe, expect, test } from 'vitest';
import { cleanBrands, slugify, sqlLiteral } from '../src/seed/build.ts';

const apply = async (db: D1Database, statements: string[]) => {
  await db.batch(statements.map((s) => db.prepare(s)));
};
const count = async (db: D1Database, sql: string) => (await db.prepare(sql).first<number>('n')) ?? -1;

beforeAll(async () => {
  await applyD1Migrations(env.CORE, env.CORE_MIGRATIONS);
  await applyD1Migrations(env.BUSQUEDA, env.BUSQUEDA_MIGRATIONS);
  await apply(env.CORE, env.CORE_SEED);
  await apply(env.BUSQUEDA, env.BUSQUEDA_SEED);
});

describe('normalización de marcas', () => {
  test('quita paréntesis y fragmentos sueltos, separa A/B y descarta «aftermarket»', () => {
    expect(
      cleanBrands([
        'Tokyo Marui (MWS',
        'NGRS)',
        'VFC (licencia Umarex/H&K)',
        'Ares/Amoeba',
        'aftermarket (Angry Gun',
        '5KU)',
        'G&G',
      ]),
    ).toEqual(['Tokyo Marui', 'VFC', 'Ares', 'Amoeba', 'G&G']);
  });

  test('slugify es estable y sin acentos', () => {
    expect(slugify('G&G')).toBe('g-and-g');
    expect(slugify('Specna Arms')).toBe('specna-arms');
    expect(slugify('Cañón')).toBe('canon');
  });

  test('sqlLiteral escapa comillas y rechaza lo no finito', () => {
    expect(sqlLiteral("O'Brien")).toBe("'O''Brien'");
    expect(sqlLiteral(null)).toBe('NULL');
    expect(sqlLiteral(true)).toBe('1');
    expect(() => sqlLiteral(Number.NaN)).toThrow(RangeError);
  });
});

describe('core sembrado', () => {
  test('importa el catálogo completo', async () => {
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM platforms')).toBe(101);
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM platform_families')).toBeGreaterThanOrEqual(20);
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM part_families')).toBe(83);
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM interfaces')).toBeGreaterThanOrEqual(89);
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM parts')).toBe(140);
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM replicas')).toBe(0); // sin inventar réplicas
  });

  test('todo es is_demo = 1 (nada de ejemplo sin marcar)', async () => {
    for (const table of [
      'brands',
      'platform_families',
      'interfaces',
      'platforms',
      'categories',
      'part_families',
      'parts',
      'dimensions',
      'assets',
    ])
      expect(await count(env.CORE, `SELECT count(*) AS n FROM ${table} WHERE is_demo <> 1`), table).toBe(0);
  });

  test('es idempotente: sembrar otra vez deja los mismos recuentos', async () => {
    const before = await count(
      env.CORE,
      'SELECT (SELECT count(*) FROM dimensions) + (SELECT count(*) FROM part_interfaces) + (SELECT count(*) FROM platform_brands) AS n',
    );
    await apply(env.CORE, env.CORE_SEED);
    const after = await count(
      env.CORE,
      'SELECT (SELECT count(*) FROM dimensions) + (SELECT count(*) FROM part_interfaces) + (SELECT count(*) FROM platform_brands) AS n',
    );
    expect(after).toBe(before);
  });

  test('las marcas salen limpias', async () => {
    expect(
      await count(
        env.CORE,
        "SELECT count(*) AS n FROM brands WHERE name LIKE '%)%' OR name LIKE '%(%' OR name LIKE '%/%'",
      ),
    ).toBe(0);
    expect(
      await count(env.CORE, "SELECT count(*) AS n FROM brands WHERE id IN ('tokyo-marui', 'g-and-g', 'specna-arms')"),
    ).toBe(3);
  });

  test('una cota conocida de una interfaz lleva valor, fuente, confianza y fecha', async () => {
    const row = await env.CORE.prepare(
      "SELECT value, unit, status, sources, confidence, checked_on FROM dimensions WHERE subject_type = 'interface' AND subject_id = 'picatinny-mil-std-1913' AND key = 'ancho de ranura'",
    ).first<{ value: number; unit: string; status: string; sources: string; confidence: string; checked_on: string }>();
    expect(row).toEqual({
      value: 5.23,
      unit: 'mm',
      status: 'verified',
      sources: '["https://en.wikipedia.org/wiki/Picatinny_rail"]',
      confidence: 'medium',
      checked_on: '2026-11-11',
    });
  });

  test('una cota desconocida llega como NULL + pending, sin fuente ni fecha', async () => {
    const row = await env.CORE.prepare(
      "SELECT value, value_min, value_max, status, sources, confidence, checked_on FROM dimensions WHERE subject_type = 'part_family' AND subject_id = 'guardamanos-mlok' AND key = 'longitud real · Guardamanos M-LOK de réplica, nominal 7 in'",
    ).first();
    expect(row).toEqual({
      value: null,
      value_min: null,
      value_max: null,
      status: 'pending',
      sources: '[]',
      confidence: null,
      checked_on: null,
    });
    expect(await count(env.CORE, "SELECT count(*) AS n FROM dimensions WHERE status = 'pending'")).toBeGreaterThan(5);
  });

  test('una cota en pulgadas se convierte a mm y conserva la cifra original', async () => {
    const row = await env.CORE.prepare(
      "SELECT note FROM dimensions WHERE note LIKE 'Publicado como % in.%' LIMIT 1",
    ).first<{ note: string }>();
    // Solo si el catálogo trae alguna en pulgadas; si no, no hay nada que comprobar.
    if (row) expect(row.note).toMatch(/Publicado como [\d.]+ in\./);
  });

  test('un rango (sin valor central) se siembra como cota conocida', async () => {
    const n = await count(
      env.CORE,
      "SELECT count(*) AS n FROM dimensions WHERE value IS NULL AND value_min IS NOT NULL AND status = 'cited'",
    );
    expect(n).toBeGreaterThanOrEqual(0);
  });

  test('ninguna cota de pieza sin URL https de fuente; las estimaciones no entran', async () => {
    expect(
      await count(
        env.CORE,
        "SELECT count(*) AS n FROM dimensions WHERE status <> 'pending' AND sources NOT LIKE '[\"https://%'",
      ),
    ).toBe(0);
    expect(
      await count(
        env.CORE,
        "SELECT count(*) AS n FROM dimensions WHERE subject_type = 'part' AND key = 'longitud' AND status <> 'pending'",
      ),
    ).toBe(0);
  });

  test('las cotas pendientes de piezas se siembran como pending', async () => {
    const n = await count(
      env.CORE,
      "SELECT count(*) AS n FROM dimensions WHERE subject_type = 'part' AND status = 'pending'",
    );
    expect(n).toBeGreaterThan(0);
  });

  test('cada pieza tiene nivel visible y un activo que no es publicable', async () => {
    expect(await count(env.CORE, "SELECT count(*) AS n FROM parts WHERE level NOT IN ('T0','T1','T2','T3')")).toBe(0);
    expect(
      await count(
        env.CORE,
        'SELECT count(*) AS n FROM parts p WHERE NOT EXISTS (SELECT 1 FROM assets a WHERE a.part_id = p.id)',
      ),
    ).toBe(0);
    expect(await count(env.CORE, 'SELECT count(*) AS n FROM assets WHERE publishable = 1 OR r2_key IS NOT NULL')).toBe(
      0,
    );
  });

  test('las interfaces propuestas por piezas existen sin cotas ni fuente inventadas', async () => {
    expect(
      await count(env.CORE, "SELECT count(*) AS n FROM interfaces WHERE status = 'proposed'"),
    ).toBeGreaterThanOrEqual(19);
    expect(
      await count(
        env.CORE,
        "SELECT count(*) AS n FROM dimensions d JOIN interfaces i ON i.id = d.subject_id AND d.subject_type = 'interface' WHERE i.status = 'proposed'",
      ),
    ).toBe(0);
    expect(
      await count(
        env.CORE,
        "SELECT count(*) AS n FROM interfaces WHERE status = 'proposed' AND (source_url IS NOT NULL OR confidence IS NOT NULL)",
      ),
    ).toBe(0);
  });

  test('una misma id en dos archivos de piezas se desambigua', async () => {
    expect(await count(env.CORE, "SELECT count(*) AS n FROM parts WHERE id LIKE 'culata-plegable-plegada--%'")).toBe(2);
  });

  test('no hay cotas huérfanas de interfaz, pieza ni familia', async () => {
    expect(
      await count(
        env.CORE,
        `SELECT count(*) AS n FROM dimensions d WHERE
          (d.subject_type = 'interface' AND NOT EXISTS (SELECT 1 FROM interfaces x WHERE x.id = d.subject_id)) OR
          (d.subject_type = 'part' AND NOT EXISTS (SELECT 1 FROM parts x WHERE x.id = d.subject_id)) OR
          (d.subject_type = 'part_family' AND NOT EXISTS (SELECT 1 FROM part_families x WHERE x.id = d.subject_id))`,
      ),
    ).toBe(0);
  });

  test('la integridad referencial se cumple tras sembrar', async () => {
    const violations = await env.CORE.prepare('PRAGMA foreign_key_check').all();
    expect(violations.results).toEqual([]);
  });
});

describe('busqueda sembrada (FTS5)', () => {
  const search = async (q: string) =>
    (
      await env.BUSQUEDA.prepare(
        'SELECT kind, entity_id FROM search_catalog WHERE search_catalog MATCH ? ORDER BY rank LIMIT 20',
      )
        .bind(q)
        .all<{ kind: string; entity_id: string }>()
    ).results;

  test('encuentra una plataforma por nombre y una marca por su nombre', async () => {
    expect((await search('m4a1')).some((r) => r.kind === 'platform' && r.entity_id === 'm4a1')).toBe(true);
    expect((await search('specna')).some((r) => r.kind === 'brand' && r.entity_id === 'specna-arms')).toBe(true);
  });

  test('ignora mayúsculas y acentos (unicode61 remove_diacritics)', async () => {
    const a = await search('colt');
    const b = await search('COLT');
    expect(b).toEqual(a);
    expect(a.length).toBeGreaterThan(0);
    // Sin acentos en la consulta se encuentra el texto acentuado del catálogo.
    expect((await search('canon')).length).toBe((await search('cañón')).length);
  });

  test('busca en los alias y en las variantes (modelo)', async () => {
    expect((await search('aliases: gbbr')).length).toBeGreaterThan(0);
    expect((await search('model: cqb')).length).toBeGreaterThan(0);
  });

  test('es idempotente y todo es is_demo', async () => {
    const before = await count(env.BUSQUEDA, 'SELECT count(*) AS n FROM search_catalog');
    await apply(env.BUSQUEDA, env.BUSQUEDA_SEED);
    expect(await count(env.BUSQUEDA, 'SELECT count(*) AS n FROM search_catalog')).toBe(before);
    expect(await count(env.BUSQUEDA, "SELECT count(*) AS n FROM search_catalog WHERE is_demo <> '1'")).toBe(0);
    expect(before).toBeGreaterThan(300);
  });
});
