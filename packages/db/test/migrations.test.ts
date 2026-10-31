// Cada base se migra desde cero en workerd y se identifica a sí misma en `meta`.
import { applyD1Migrations } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { drizzle } from 'drizzle-orm/d1';
import { describe, expect, test } from 'vitest';
import { BASES, type Base, BINDINGS, busqueda, core, mercado } from '../src/index.ts';

const schemas = { core, mercado, busqueda } as const;
const migrationsOf = (base: Base) => env[`${BINDINGS[base]}_MIGRATIONS`];

describe.each(BASES)('base %s', (base) => {
  const db = env[BINDINGS[base]];

  test('0000_meta se aplica desde cero y es idempotente', async () => {
    await applyD1Migrations(db, migrationsOf(base));
    await applyD1Migrations(db, migrationsOf(base)); // la segunda vez no reaplica nada
    const applied = await db.prepare('SELECT name FROM d1_migrations ORDER BY id').all<{ name: string }>();
    expect(applied.results.map((r) => r.name)).toEqual(['0000_meta.sql']);
  });

  test('la tabla meta identifica la base correcta (detecta bindings cruzados)', async () => {
    await applyD1Migrations(db, migrationsOf(base));
    const rows = await drizzle(db, { schema: schemas[base] }).select().from(schemas[base].meta);
    expect(Object.fromEntries(rows.map((r) => [r.key, r.value]))).toEqual({
      base,
      migracion: '0000_meta',
    });
  });
});

test('las tres bases son independientes', async () => {
  for (const base of BASES) await applyD1Migrations(env[BINDINGS[base]], migrationsOf(base));
  const names = await Promise.all(
    BASES.map((base) =>
      env[BINDINGS[base]].prepare("SELECT value FROM meta WHERE key = 'base'").first<string>('value'),
    ),
  );
  expect(names).toEqual(['core', 'mercado', 'busqueda']);
});
