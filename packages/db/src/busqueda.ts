// Esquema de la base `busqueda` (docs/07 §3.3). El índice es una tabla virtual FTS5 que Drizzle no
// sabe describir: se crea en la migración `0001_catalogo_fts.sql` y aquí se declaran sus nombres.
import { metaTable } from './meta.ts';

export const meta = metaTable();

export const SEARCH_TABLE = 'search_catalog';
/** Columnas indexadas (texto buscable) y las que solo acompañan a la fila. */
export const SEARCH_COLUMNS = ['name', 'brand', 'model', 'aliases'] as const;
export const SEARCH_KINDS = ['platform', 'replica', 'part', 'brand', 'interface'] as const;
export type SearchKind = (typeof SEARCH_KINDS)[number];
