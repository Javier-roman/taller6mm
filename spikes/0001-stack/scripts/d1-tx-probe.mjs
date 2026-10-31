// Sonda de transacciones sobre el D1 local (el mismo simulador que usa `astro preview`):
//   1. `BEGIN` crudo con prepare().run()
//   2. drizzle `db.transaction()` que inserta y luego lanza un error: ¿hay rollback de verdad?
//   3. drizzle `db.batch()` con una sentencia que falla: ¿es atómico?
// Requisitos: `pnpm db:migrate:local`. Uso: node scripts/d1-tx-probe.mjs → d1-tx-results.json
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { eq, sql } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/d1';
import { getPlatformProxy } from 'wrangler';
import * as schemaModule from '../src/db/schema.ts';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { env, dispose } = await getPlatformProxy({ configPath: path.join(root, 'wrangler.jsonc'), persist: true });
const db = drizzle(env.DB, { schema: schemaModule });
const { meta } = schemaModule;
const results = {};
const exists = async (key) => (await db.select().from(meta).where(eq(meta.key, key))).length > 0;
const cleanup = () => db.delete(meta).where(sql`${meta.key} LIKE 'probe-%'`);

try {
  await cleanup();

  try {
    await env.DB.prepare('BEGIN').run();
    results.rawBegin = { ok: true };
    await env.DB.prepare('ROLLBACK').run();
  } catch (error) {
    results.rawBegin = { ok: false, error: String(error?.message ?? error) };
  }

  try {
    await db.transaction(async (tx) => {
      await tx.insert(meta).values({ key: 'probe-tx', value: '1' });
      throw new Error('rollback intencionado');
    });
    results.drizzleTransaction = { ok: true };
  } catch (error) {
    results.drizzleTransaction = { threw: String(error?.message ?? error) };
  }
  results.drizzleTransaction.rowLeftBehind = await exists('probe-tx');
  results.drizzleTransaction.atomic = !results.drizzleTransaction.rowLeftBehind;

  try {
    await db.batch([
      db.insert(meta).values({ key: 'probe-batch', value: '1' }),
      db.insert(meta).values({ key: 'probe-batch', value: 'duplicada' }), // viola la clave primaria
    ]);
    results.drizzleBatch = { ok: true };
  } catch (error) {
    results.drizzleBatch = { threw: String(error?.message ?? error).slice(0, 200) };
  }
  results.drizzleBatch.rowLeftBehind = await exists('probe-batch');
  results.drizzleBatch.atomic = !results.drizzleBatch.rowLeftBehind;
} finally {
  await cleanup();
  await dispose();
}

const out = { measuredAt: new Date().toISOString(), ...results };
writeFileSync(path.join(root, 'd1-tx-results.json'), `${JSON.stringify(out, null, 2)}\n`);
console.log(JSON.stringify(out, null, 2));
