// Esquema Drizzle de la base `core` (docs/07 §3). De momento solo la tabla `meta`.
import { metaTable } from './meta.ts';

export const meta = metaTable();
