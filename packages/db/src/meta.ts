// Tabla `meta` presente en cada base D1 (plan de la Fase 0, decisión 14): guarda el nombre de la
// base y la última migración de datos, para detectar bindings cruzados (con tres bases, leer
// `mercado` creyendo que es `core` es un fallo real y silencioso).
import { sqliteTable, text } from 'drizzle-orm/sqlite-core';

export const BASES = ['core', 'mercado', 'busqueda'] as const;
export type Base = (typeof BASES)[number];

/** Binding de Wrangler de cada base (mismo nombre en web, jobs y tests). */
export const BINDINGS: Readonly<Record<Base, 'CORE' | 'MERCADO' | 'BUSQUEDA'>> = {
  core: 'CORE',
  mercado: 'MERCADO',
  busqueda: 'BUSQUEDA',
};

export function metaTable() {
  return sqliteTable('meta', {
    key: text('key').primaryKey(),
    value: text('value').notNull(),
  });
}
