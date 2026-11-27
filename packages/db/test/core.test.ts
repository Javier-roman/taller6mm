// Migración 0001_catalogo de `core`: crea las tablas y la propia base impone las reglas de honestidad
// (principios 2, 3 y 5) con CHECK y claves foráneas, además de Zod en el código.
import { applyD1Migrations } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { beforeAll, describe, expect, test } from 'vitest';

const db = env.CORE;

beforeAll(async () => {
  await applyD1Migrations(db, env.CORE_MIGRATIONS);
});

/** Ejecuta una sentencia y devuelve si la base la rechazó. */
async function rejects(sql: string, ...binds: unknown[]): Promise<boolean> {
  try {
    await db
      .prepare(sql)
      .bind(...binds)
      .run();
    return false;
  } catch {
    return true;
  }
}

const run = (sql: string, ...binds: unknown[]) =>
  db
    .prepare(sql)
    .bind(...binds)
    .run();

describe('0001_catalogo', () => {
  test('se aplica tras 0000_meta, es idempotente y crea las tablas del catálogo', async () => {
    await applyD1Migrations(db, env.CORE_MIGRATIONS);
    const applied = await db.prepare('SELECT name FROM d1_migrations ORDER BY id').all<{ name: string }>();
    expect(applied.results.map((r) => r.name)).toEqual(['0000_meta.sql', '0001_catalogo.sql']);
    const tables = await db
      .prepare(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE '\\_%' ESCAPE '\\' AND name NOT LIKE 'sqlite%' ORDER BY name",
      )
      .all<{ name: string }>();
    expect(tables.results.map((r) => r.name)).toEqual([
      'assets',
      'brands',
      'categories',
      'd1_migrations',
      'dimensions',
      'interfaces',
      'meta',
      'part_families',
      'part_family_interfaces',
      'part_family_platform_families',
      'part_interfaces',
      'parts',
      'platform_brands',
      'platform_families',
      'platform_interfaces',
      'platforms',
      'replicas',
    ]);
  });

  test('la migración es aditiva: no toca la tabla meta ni sus filas', async () => {
    const rows = await db.prepare('SELECT key, value FROM meta ORDER BY key').all<{ key: string; value: string }>();
    expect(rows.results).toEqual([
      { key: 'base', value: 'core' },
      { key: 'migracion', value: '0000_meta' },
    ]);
  });
});

describe('claves foráneas y niveles', () => {
  test('una plataforma exige una familia existente', async () => {
    expect(
      await rejects(
        "INSERT INTO platforms (id, name, family_id, mechanisms, variants, status, is_demo) VALUES ('x', 'X', 'no-existe', '[]', '[]', 'pending', 1)",
      ),
    ).toBe(true);
  });

  test('el nivel de una pieza solo admite T0 a T3', async () => {
    await run("INSERT INTO parts (id, name, kind, level, is_demo) VALUES ('ok-t3', 'ok', 'part', 'T3', 1)");
    expect(
      await rejects("INSERT INTO parts (id, name, kind, level, is_demo) VALUES ('mal', 'mal', 'part', 'T4', 1)"),
    ).toBe(true);
    const defaulted = await run("INSERT INTO parts (id, name, kind, is_demo) VALUES ('def', 'def', 'part', 1)");
    expect(defaulted.success).toBe(true);
    const row = await db.prepare("SELECT level FROM parts WHERE id = 'def'").first<string>('level');
    expect(row).toBe('T0'); // sin nivel dado, el más honesto
  });

  test('una interfaz marcada verified exige fuente, fecha y confianza', async () => {
    expect(
      await rejects("INSERT INTO interfaces (id, name, status, is_demo) VALUES ('v-sin-fuente', 'V', 'verified', 1)"),
    ).toBe(true);
    const ok = await run(
      "INSERT INTO interfaces (id, name, status, source_url, source_checked_on, confidence, is_demo) VALUES ('v-ok', 'V', 'verified', 'https://example.test', '2026-11-01', 'medium', 1)",
    );
    expect(ok.success).toBe(true);
    expect(
      (await run("INSERT INTO interfaces (id, name, status, is_demo) VALUES ('p-ok', 'P', 'pending', 1)")).success,
    ).toBe(true);
  });
});

describe('cotas: lo desconocido es NULL + bandera, nunca inventado', () => {
  const insert = (key: string, cols: string, values: string) =>
    run(
      `INSERT INTO dimensions (subject_type, subject_id, key, unit, ${cols}, is_demo) VALUES ('part', 'p', '${key}', 'mm', ${values}, 1)`,
    );

  test('una cota desconocida (pending, todo NULL) es válida', async () => {
    const r = await insert('largo', 'status, sources', "'pending', '[]'");
    expect(r.success).toBe(true);
    const row = await db.prepare("SELECT value, confidence, checked_on FROM dimensions WHERE key = 'largo'").first();
    expect(row).toEqual({ value: null, confidence: null, checked_on: null });
  });

  test('una cota pending con valor se rechaza (sería un dato inventado)', async () => {
    expect(
      await rejects(
        "INSERT INTO dimensions (subject_type, subject_id, key, unit, status, sources, value, is_demo) VALUES ('part','p','inv','mm','pending','[]', 5, 1)",
      ),
    ).toBe(true);
  });

  test('una cota conocida sin fuente, sin confianza o sin fecha se rechaza', async () => {
    const base = (extra: string) =>
      `INSERT INTO dimensions (subject_type, subject_id, key, unit, status, value, ${extra}, is_demo)`;
    expect(
      await rejects(
        `${base('sources, confidence, checked_on')} VALUES ('part','p','sinfuente','mm','cited', 5, '[]', 'low', '2026-11-01', 1)`,
      ),
    ).toBe(true);
    expect(
      await rejects(
        `${base('sources, checked_on')} VALUES ('part','p','sinconf','mm','cited', 5, '["https://e.test"]', '2026-11-01', 1)`,
      ),
    ).toBe(true);
    expect(
      await rejects(
        `${base('sources, confidence')} VALUES ('part','p','sinfecha','mm','cited', 5, '["https://e.test"]', 'low', 1)`,
      ),
    ).toBe(true);
    const ok = await run(
      "INSERT INTO dimensions (subject_type, subject_id, key, unit, status, value, sources, confidence, checked_on, is_demo) VALUES ('part','p','conocida','mm','cited', 5.23, '[\"https://e.test\"]', 'low', '2026-11-01', 1)",
    );
    expect(ok.success).toBe(true);
  });

  test('rango sin valor central válido; rango invertido, negativos y claves repetidas, no', async () => {
    const ins = (key: string, min: number, max: number, value = 'NULL') =>
      `INSERT INTO dimensions (subject_type, subject_id, key, unit, status, value, value_min, value_max, sources, confidence, checked_on, is_demo) VALUES ('part','p','${key}','mm','cited',${value},${min},${max},'["https://e.test"]','medium','2026-11-01',1)`;
    expect((await run(ins('rango', 785, 889))).success).toBe(true);
    expect(await rejects(ins('invertido', 9, 3))).toBe(true);
    expect(await rejects(ins('negativo', -1, 3))).toBe(true);
    expect(await rejects(ins('rango', 1, 2))).toBe(true); // misma (sujeto, clave)
  });

  test('la unidad y el estado están acotados', async () => {
    expect(
      await rejects(
        "INSERT INTO dimensions (subject_type, subject_id, key, unit, status, sources, is_demo) VALUES ('part','p','u','cm','pending','[]',1)",
      ),
    ).toBe(true);
    expect(
      await rejects(
        "INSERT INTO dimensions (subject_type, subject_id, key, unit, status, sources, is_demo) VALUES ('part','p','s','mm','estimada','[]',1)",
      ),
    ).toBe(true);
  });
});

describe('activos: referencia al nivel y la licencia, sin binarios', () => {
  beforeAll(async () => {
    await run("INSERT INTO parts (id, name, kind, is_demo) VALUES ('pieza-a', 'A', 'part', 0)");
  });
  const asset = (
    id: string,
    license: string,
    publishable: number,
    isDemo: number,
    partId: string | null = "'pieza-a'",
  ) =>
    `INSERT INTO assets (id, part_id, view, level, license_status, publishable, is_demo) VALUES ('${id}', ${partId}, '3d', 'T0', '${license}', ${publishable}, ${isDemo})`;

  test('lo propio y real puede ser publicable', async () => {
    expect((await run(asset('own-ok', 'own', 1, 0))).success).toBe(true);
  });

  test('una referencia de terceros o un activo de demostración nunca es publicable (principio 5)', async () => {
    expect(await rejects(asset('tercero', 'third-party-reference', 1, 0))).toBe(true);
    expect(await rejects(asset('demo', 'own', 1, 1))).toBe(true);
    expect((await run(asset('tercero-interno', 'third-party-reference', 0, 0))).success).toBe(true);
  });

  test('un activo pertenece a una pieza o a una réplica, nunca a ninguna ni a las dos', async () => {
    expect(await rejects(asset('huerfano', 'own', 0, 1, 'NULL'))).toBe(true);
  });

  test('licencias y vistas fuera de la lista se rechazan', async () => {
    expect(await rejects(asset('lic', 'copyright-desconocido', 0, 1))).toBe(true);
  });
});
