// Lee `catalogo/*.json` del disco (solo Node: lo usan scripts/db-seed.mjs y vitest.config.ts, nunca un Worker).
import { readFileSync } from 'node:fs';
import path from 'node:path';
import type { RawCatalog } from './sources.ts';

/** Archivos de piezas generadas que entran en la semilla (misma forma en todos). */
export const PIECE_FILES = [
  'm4-tanda3',
  'm4-tanda3-culatas',
  'm4-oleada1-cuerpos',
  'm4-oleada1-piezas',
  'ak-piezas',
  'pistolas-piezas',
] as const;

export function loadCatalog(catalogDir: string): RawCatalog {
  const read = (name: string): unknown => JSON.parse(readFileSync(path.join(catalogDir, `${name}.json`), 'utf8'));
  return {
    interfaces: read('interfaces'),
    plataformas: read('plataformas'),
    familias: read('familias'),
    cotas: read('cotas-airsoft'),
    piezas: Object.fromEntries(PIECE_FILES.map((name) => [name, read(name)])),
  };
}
