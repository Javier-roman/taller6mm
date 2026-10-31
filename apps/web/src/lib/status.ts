// Estado de las tres bases D1 para la página de inicio provisional (decisión 14 del plan): cada
// binding debe apuntar a la base que dice su tabla `meta`. Un binding cruzado se marca como error.
import { BASES, type Base, BINDINGS } from '@taller6mm/db';

export interface BaseStatus {
  base: Base;
  binding: string;
  state: 'ok' | 'cruzada' | 'sin_migrar' | 'error';
  /** Nombre que la propia base dice tener (null si no se pudo leer). */
  reportedName: string | null;
  migration: string | null;
}

/** Lo mínimo de D1 que se usa aquí (facilita los tests con dobles). */
export interface MetaReader {
  prepare(query: string): { all<T>(): Promise<{ results: T[] }> };
}

export async function readBaseStatus(base: Base, db: MetaReader): Promise<BaseStatus> {
  const binding = BINDINGS[base];
  try {
    const { results } = await db.prepare('SELECT key, value FROM meta').all<{ key: string; value: string }>();
    const meta = Object.fromEntries(results.map((r) => [r.key, r.value]));
    const reportedName = meta['base'] ?? null;
    return {
      base,
      binding,
      state: reportedName === base ? 'ok' : 'cruzada',
      reportedName,
      migration: meta['migracion'] ?? null,
    };
  } catch (error) {
    const missingTable = error instanceof Error && /no such table/i.test(error.message);
    return { base, binding, state: missingTable ? 'sin_migrar' : 'error', reportedName: null, migration: null };
  }
}

export function readAllBases(env: Record<(typeof BINDINGS)[Base], MetaReader>): Promise<BaseStatus[]> {
  return Promise.all(BASES.map((base) => readBaseStatus(base, env[BINDINGS[base]])));
}
