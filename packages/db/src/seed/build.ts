// Construye las semillas de `core` y `busqueda` a partir del catálogo JSON (`catalogo/`). Lógica pura:
// recibe el JSON ya leído y devuelve sentencias SQL, sin tocar disco ni red. Todo lo sembrado lleva
// `is_demo = 1` (principio 2): es catálogo de ejemplo hasta que haya fuente por réplica.
//
// Reglas de honestidad que aplica al importar (ADR-0011, ADR-0012):
//   - una cota solo entra con valor si trae URL https de fuente; si no, no se siembra (se cuenta en el informe);
//   - lo desconocido se siembra como cota `pending` (todo NULL), nunca como un número supuesto;
//   - cada cota pasa por `DimensionSchema` de `@taller6mm/domain` antes de convertirse en SQL.
import {
  type Confidence,
  type Dimension,
  DimensionSchema,
  type FidelityLevel,
  type IsoDateSchema,
} from '@taller6mm/domain';
import { getTableColumns, getTableName } from 'drizzle-orm';
import type { SQLiteTable } from 'drizzle-orm/sqlite-core';
import { SEARCH_TABLE } from '../busqueda.ts';
import * as core from '../core.ts';
import {
  CotasFileSchema,
  FamiliasFileSchema,
  InterfacesFileSchema,
  PiezasFileSchema,
  PlataformasFileSchema,
  type RawCatalog,
} from './sources.ts';

type Insert<T extends SQLiteTable> = T['$inferInsert'];
type IsoDate = typeof IsoDateSchema._output;

export interface SeedReport {
  rows: Record<string, number>;
  /** Cotas de piezas que no se siembran como valor por no tener URL de fuente. */
  droppedUnsourcedPartDimensions: number;
  /** Cotas de réplica sin réplica sembrada a la que colgarlas. */
  skippedReplicaDimensions: number;
  /** Interfaces citadas por piezas que no tienen ficha en el catálogo (se crean `proposed`). */
  proposedInterfaces: string[];
}

export interface Seed {
  statements: string[];
  report: SeedReport;
}

// --- SQL ------------------------------------------------------------------------------------------

export function sqlLiteral(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined) return 'NULL';
  if (typeof value === 'boolean') return value ? '1' : '0';
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new RangeError(`Número no finito en la semilla: ${value}`);
    return String(value);
  }
  if (value.includes('\0')) throw new RangeError('Cadena con NUL en la semilla');
  return `'${value.replaceAll("'", "''")}'`;
}

/** INSERT por lotes (D1 limita las variables, no los literales; 50 filas por sentencia es holgado). */
export function insertStatements<T extends SQLiteTable>(table: T, rows: Insert<T>[], batch = 50): string[] {
  const name = getTableName(table);
  const columns = Object.entries(getTableColumns(table)) as [string, { name: string }][];
  const out: string[] = [];
  for (let i = 0; i < rows.length; i += batch) {
    const values = rows.slice(i, i + batch).map((row) => {
      const record = row as Record<string, string | number | boolean | null | undefined>;
      return `(${columns.map(([key]) => sqlLiteral(record[key])).join(', ')})`;
    });
    out.push(
      `INSERT INTO \`${name}\` (${columns.map(([, c]) => `\`${c.name}\``).join(', ')}) VALUES\n${values.join(',\n')}`,
    );
  }
  return out;
}

// --- Normalización --------------------------------------------------------------------------------

const CONFIDENCE_MAP = { alta: 'high', media: 'medium', baja: 'low' } as const satisfies Record<string, Confidence>;
const confidence = (c: keyof typeof CONFIDENCE_MAP | null | undefined): Confidence | null =>
  c ? CONFIDENCE_MAP[c] : null;

export function slugify(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replaceAll('&', ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Los `fabricantes` del catálogo traen notas entre paréntesis y, por haberse separado por comas,
 * fragmentos como «NGRS)». Devuelve nombres de marca limpios: sin paréntesis, sin fragmentos sueltos
 * y con «A/B» separado en dos marcas. «aftermarket» no es una marca.
 */
export function cleanBrands(raw: readonly string[]): string[] {
  const out: string[] = [];
  for (const entry of raw) {
    if (entry.includes(')') && !entry.includes('(')) continue; // fragmento «NGRS)»
    const base = entry.replace(/\s*\(.*$/, '').trim();
    for (const name of base.split('/')) {
      const brand = name.trim();
      if (brand && brand.toLowerCase() !== 'aftermarket') out.push(brand);
    }
  }
  return out;
}

const dim = (d: Dimension & { isDemo?: boolean }): Insert<typeof core.dimensions> => {
  const parsed = DimensionSchema.parse(d);
  return {
    subjectType: parsed.subjectType,
    subjectId: parsed.subjectId,
    key: parsed.key,
    value: parsed.value,
    valueMin: parsed.min,
    valueMax: parsed.max,
    unit: parsed.unit,
    status: parsed.status,
    sources: JSON.stringify(parsed.sources),
    confidence: parsed.confidence,
    checkedOn: parsed.checkedOn,
    note: parsed.note,
    isDemo: true,
  };
};

const pending = (subjectType: Dimension['subjectType'], subjectId: string, key: string, note: string | null) =>
  dim({
    subjectType,
    subjectId,
    key,
    value: null,
    min: null,
    max: null,
    unit: 'mm',
    status: 'pending',
    sources: [],
    confidence: null,
    checkedOn: null,
    note,
  });

// --- Construcción ---------------------------------------------------------------------------------

const DEMO_CLEANUP = [
  'DELETE FROM `assets` WHERE `is_demo` = 1',
  'DELETE FROM `dimensions` WHERE `is_demo` = 1',
  'DELETE FROM `part_interfaces` WHERE `part_id` IN (SELECT `id` FROM `parts` WHERE `is_demo` = 1)',
  'DELETE FROM `parts` WHERE `is_demo` = 1',
  'DELETE FROM `part_family_interfaces` WHERE `part_family_id` IN (SELECT `id` FROM `part_families` WHERE `is_demo` = 1)',
  'DELETE FROM `part_family_platform_families` WHERE `part_family_id` IN (SELECT `id` FROM `part_families` WHERE `is_demo` = 1)',
  'DELETE FROM `part_families` WHERE `is_demo` = 1',
  'DELETE FROM `categories` WHERE `is_demo` = 1 AND `parent_id` IS NOT NULL',
  'DELETE FROM `categories` WHERE `is_demo` = 1',
  'DELETE FROM `replicas` WHERE `is_demo` = 1',
  'DELETE FROM `platform_brands` WHERE `platform_id` IN (SELECT `id` FROM `platforms` WHERE `is_demo` = 1)',
  'DELETE FROM `platform_interfaces` WHERE `platform_id` IN (SELECT `id` FROM `platforms` WHERE `is_demo` = 1)',
  'DELETE FROM `platforms` WHERE `is_demo` = 1',
  'DELETE FROM `interfaces` WHERE `is_demo` = 1',
  'DELETE FROM `platform_families` WHERE `is_demo` = 1',
  'DELETE FROM `brands` WHERE `is_demo` = 1',
];

function parseAll(raw: RawCatalog) {
  return {
    interfaces: InterfacesFileSchema.parse(raw.interfaces).interfaces,
    plataformas: PlataformasFileSchema.parse(raw.plataformas),
    familias: FamiliasFileSchema.parse(raw.familias).familias,
    cotas: CotasFileSchema.parse(raw.cotas).cotas,
    piezas: Object.entries(raw.piezas).map(([set, data]) => [set, PiezasFileSchema.parse(data)] as const),
  };
}

export function buildCoreSeed(raw: RawCatalog): Seed {
  const src = parseAll(raw);
  const report: SeedReport = {
    rows: {},
    droppedUnsourcedPartDimensions: 0,
    skippedReplicaDimensions: 0,
    proposedInterfaces: [],
  };
  const statements: string[] = [...DEMO_CLEANUP];
  const add = <T extends SQLiteTable>(table: T, rows: Insert<T>[]) => {
    report.rows[getTableName(table)] = rows.length;
    statements.push(...insertStatements(table, rows));
  };

  // Marcas (de fabricantes de plataformas y marcas de ejemplo de familias de piezas).
  const brandNames = new Map<string, string>();
  const noteBrand = (name: string) => {
    const id = slugify(name);
    if (id && !brandNames.has(id)) brandNames.set(id, name);
    return id;
  };
  const platformBrandPairs = new Set<string>();
  for (const p of src.plataformas.plataformas)
    for (const b of cleanBrands(p.fabricantes)) platformBrandPairs.add(`${p.id}\t${noteBrand(b)}`);
  for (const f of src.familias) for (const b of cleanBrands(f.marcas_ejemplo)) noteBrand(b);
  add(
    core.brands,
    [...brandNames].map(([id, name]) => ({ id, name, isDemo: true })),
  );

  add(
    core.platformFamilies,
    src.plataformas.familias.map((f) => ({ id: f.id, name: f.nombre, isDemo: true })),
  );

  // Interfaces: las del catálogo, las propuestas por las piezas y las citadas sin ficha.
  const interfaceRows = new Map<string, Insert<typeof core.interfaces>>();
  for (const i of src.interfaces) {
    interfaceRows.set(i.id, {
      id: i.id,
      name: i.nombre,
      kind: i.tipo,
      description: i.descripcion,
      status: i.estado === 'verificado' ? 'verified' : 'pending',
      sourceUrl: i.fuente?.url ?? null,
      sourceCheckedOn: i.fuente?.fecha_consulta ?? null,
      confidence: confidence(i.confianza),
      notes: i.notas,
      isDemo: true,
    });
  }
  for (const [, file] of src.piezas)
    for (const n of file.interfaces_nuevas)
      if (!interfaceRows.has(n.id))
        interfaceRows.set(n.id, {
          id: n.id,
          name: n.id,
          kind: null,
          description: n.descripcion,
          status: 'proposed',
          sourceUrl: null,
          sourceCheckedOn: null,
          confidence: null,
          notes: 'Propuesta por una tanda de piezas; sin ficha ni cotas en el catálogo.',
          isDemo: true,
        });
  for (const [, file] of src.piezas)
    for (const piece of file.piezas)
      for (const id of [...piece.requiere, ...piece.ofrece])
        if (!interfaceRows.has(id)) {
          report.proposedInterfaces.push(id);
          interfaceRows.set(id, {
            id,
            name: id,
            kind: null,
            description: null,
            status: 'proposed',
            sourceUrl: null,
            sourceCheckedOn: null,
            confidence: null,
            notes: 'Citada por piezas generadas; sin ficha ni cotas en el catálogo.',
            isDemo: true,
          });
        }
  report.proposedInterfaces = [...new Set(report.proposedInterfaces)].sort();
  add(core.interfaces, [...interfaceRows.values()]);

  // Plataformas y sus relaciones.
  add(
    core.platforms,
    src.plataformas.plataformas.map((p) => ({
      id: p.id,
      name: p.nombre,
      familyId: p.familia,
      mechanisms: JSON.stringify(p.mecanismos),
      variants: JSON.stringify(p.variantes),
      magazineWellInterfaceId: p.pozo_cargador,
      status: p.estado === 'verificado' ? ('verified' as const) : ('pending' as const),
      sourceUrl: p.fuente?.url ?? null,
      sourceCheckedOn: p.fuente?.fecha_consulta ?? null,
      confidence: confidence(p.confianza),
      notes: p.notas,
      isDemo: true,
    })),
  );
  add(
    core.platformInterfaces,
    src.plataformas.plataformas.flatMap((p) => p.interfaces.map((interfaceId) => ({ platformId: p.id, interfaceId }))),
  );
  add(
    core.platformBrands,
    [...platformBrandPairs].map((pair) => {
      const [platformId = '', brandId = ''] = pair.split('\t');
      return { platformId, brandId };
    }),
  );

  // Categorías (los «grupos» del catálogo) y familias de piezas.
  const groups = [...new Set(src.familias.map((f) => f.grupo))];
  add(
    core.categories,
    groups.map((g) => ({ id: g, name: g, parentId: null, isDemo: true })),
  );
  add(
    core.partFamilies,
    src.familias.map((f) => ({
      id: f.id,
      name: f.nombre,
      categoryId: f.grupo,
      expectedLevel: f.nivel_esperado,
      appliesToAll: f.aplica_a.includes('*'),
      parameters: JSON.stringify(f.parametros),
      exampleBrands: JSON.stringify(cleanBrands(f.marcas_ejemplo)),
      status: f.estado === 'verificado' ? ('verified' as const) : ('pending' as const),
      sourceUrl: f.fuente?.url ?? null,
      sourceCheckedOn: f.fuente?.fecha_consulta ?? null,
      confidence: confidence(f.confianza),
      notes: f.notas,
      isDemo: true,
    })),
  );
  add(
    core.partFamilyPlatformFamilies,
    src.familias.flatMap((f) =>
      f.aplica_a.filter((a) => a !== '*').map((platformFamilyId) => ({ partFamilyId: f.id, platformFamilyId })),
    ),
  );
  add(
    core.partFamilyInterfaces,
    src.familias.flatMap((f) =>
      f.interfaces.map((interfaceId) => ({ partFamilyId: f.id, interfaceId, role: 'unspecified' as const })),
    ),
  );

  // Piezas generadas, sus interfaces y sus activos (solo referencias).
  const counts = new Map<string, number>();
  for (const [, file] of src.piezas) for (const p of file.piezas) counts.set(p.id, (counts.get(p.id) ?? 0) + 1);
  const partRows: Insert<typeof core.parts>[] = [];
  const partInterfaceRows: Insert<typeof core.partInterfaces>[] = [];
  const assetRows: Insert<typeof core.assets>[] = [];
  const dimensionRows: Insert<typeof core.dimensions>[] = [];
  const familyIds = new Set(src.familias.map((f) => f.id));
  for (const [set, file] of src.piezas) {
    for (const p of file.piezas) {
      // Una misma id en dos archivos (culata plegable AK y AR) son piezas distintas: se desambigua.
      const id = (counts.get(p.id) ?? 0) > 1 ? `${p.id}--${set}` : p.id;
      const level: FidelityLevel = p.nivel_puerta ?? 'T0';
      partRows.push({
        id,
        partFamilyId: familyIds.has(p.familia) ? p.familia : null,
        generatorFamily: p.familia,
        name: p.elemento ?? p.id,
        kind: 'part',
        brandId: null,
        level,
        parameters: JSON.stringify(p.parametros),
        notes: p.nivel_nota ?? null,
        isDemo: true,
      });
      for (const interfaceId of new Set(p.requiere))
        partInterfaceRows.push({ partId: id, interfaceId, role: 'requires' });
      for (const interfaceId of new Set(p.ofrece)) partInterfaceRows.push({ partId: id, interfaceId, role: 'offers' });
      const ownLicense = p.license_status === 'propio';
      assetRows.push({
        id: `${id}--3d`,
        partId: id,
        replicaId: null,
        view: '3d',
        level,
        licenseStatus: ownLicense ? 'own' : 'third-party-reference',
        licenseText: p.licencia_texto ?? null,
        sourceUrl: null,
        r2Key: null,
        sha256: p.sha256_glb,
        publishable: false, // todo es es_demo: nunca publicable (principio 5)
        isDemo: true,
      });
      for (const c of p.cotas) {
        const url = /^(https:\/\/\S+)/.exec(c.fuente)?.[1];
        if (c.desconocido || c.valor_mm === null) {
          dimensionRows.push(pending('part', id, c.clave, 'Desconocida en el catálogo de piezas.'));
        } else if (url) {
          const checkedOn: IsoDate = c.fecha ?? file.generado;
          dimensionRows.push(
            dim({
              subjectType: 'part',
              subjectId: id,
              key: c.clave,
              value: c.valor_mm,
              min: null,
              max: null,
              unit: 'mm',
              status: 'cited',
              sources: [url],
              confidence: confidence(c.confianza),
              checkedOn,
              note: c.fecha ? null : 'Fecha = generación del catálogo de piezas, no de la consulta de la fuente.',
            }),
          );
        } else {
          // Parámetro de barrido o estimación «a ojo»: no es una cota con fuente (principio 2).
          report.droppedUnsourcedPartDimensions++;
        }
      }
      for (const pend of p.pendientes) {
        const key = typeof pend === 'string' ? pend : null;
        const alreadyListed = p.cotas.some((c) => c.clave === key);
        if (key && !alreadyListed)
          dimensionRows.push(pending('part', id, key, 'Pendiente según el catálogo de piezas.'));
      }
    }
  }
  add(core.parts, partRows);
  add(core.partInterfaces, partInterfaceRows);
  add(core.assets, assetRows);

  // Cotas de interfaces estándar (de pulgadas a mm sin perder la cifra original en la nota).
  for (const i of src.interfaces)
    for (const c of i.cotas) {
      const inches = c.unidad === 'in';
      dimensionRows.push(
        dim({
          subjectType: 'interface',
          subjectId: i.id,
          key: c.nombre,
          value: inches ? Number((c.valor * 25.4).toFixed(2)) : c.valor,
          min: null,
          max: null,
          unit: 'mm',
          status: i.estado === 'verificado' ? 'verified' : 'cited',
          sources: [c.fuente],
          confidence: confidence(c.confianza),
          checkedOn: c.fecha_consulta,
          note: [inches ? `Publicado como ${c.valor} in.` : null, c.nota].filter(Boolean).join(' ') || null,
        }),
      );
    }

  // Cotas de airsoft: las de piezas cuelgan de su familia; las de réplicas esperan a que exista la réplica.
  for (const c of src.cotas) {
    if (c.ambito === 'replica' || c.familia === null) {
      report.skippedReplicaDimensions++;
      continue;
    }
    const unit = c.unidad.startsWith('mm') ? 'mm' : 'count';
    const key = `${c.parametro} · ${c.producto}`;
    const note =
      [c.unidad === 'mm (CCW)' ? 'Rosca a izquierdas (CCW).' : null, c.nota].filter(Boolean).join(' ') || null;
    if (c.estado === 'pendiente') {
      dimensionRows.push({ ...pending('part_family', c.familia, key, note), unit });
    } else {
      dimensionRows.push(
        dim({
          subjectType: 'part_family',
          subjectId: c.familia,
          key,
          value: c.valor,
          min: c.valor_min,
          max: c.valor_max,
          unit,
          status: 'cited',
          sources: c.fuentes,
          confidence: confidence(c.confianza),
          checkedOn: c.fecha_consulta,
          note,
        }),
      );
    }
  }
  add(core.dimensions, dimensionRows);

  return { statements, report };
}

/** Índice FTS5 de `busqueda`: nombre, marca, modelo (variantes) y alias de lo sembrado en `core`. */
export function buildSearchSeed(raw: RawCatalog): Seed {
  const src = parseAll(raw);
  const rows: string[][] = [];
  const row = (kind: string, id: string, name: string, brand: string, model: string, aliases: string) =>
    rows.push([kind, id, '1', name, brand, model, aliases].map((v) => sqlLiteral(v)));

  const brands = new Map<string, string>();
  for (const p of src.plataformas.plataformas) {
    const names = cleanBrands(p.fabricantes);
    for (const b of names) brands.set(slugify(b), b);
    row('platform', p.id, p.nombre, names.join(' '), p.variantes.join(' '), p.mecanismos.join(' '));
  }
  for (const f of src.familias) for (const b of cleanBrands(f.marcas_ejemplo)) brands.set(slugify(b), b);
  for (const [id, name] of brands) row('brand', id, name, name, '', '');
  for (const i of src.interfaces) row('interface', i.id, i.nombre, '', '', i.tipo);
  const counts = new Map<string, number>();
  for (const [, file] of src.piezas) for (const p of file.piezas) counts.set(p.id, (counts.get(p.id) ?? 0) + 1);
  for (const [set, file] of src.piezas)
    for (const p of file.piezas) {
      const id = (counts.get(p.id) ?? 0) > 1 ? `${p.id}--${set}` : p.id;
      row('part', id, p.elemento ?? p.id, '', '', p.familia);
    }

  const statements = [`DELETE FROM \`${SEARCH_TABLE}\` WHERE \`is_demo\` = '1'`];
  for (let i = 0; i < rows.length; i += 50)
    statements.push(
      `INSERT INTO \`${SEARCH_TABLE}\` (\`kind\`, \`entity_id\`, \`is_demo\`, \`name\`, \`brand\`, \`model\`, \`aliases\`) VALUES\n${rows
        .slice(i, i + 50)
        .map((r) => `(${r.join(', ')})`)
        .join(',\n')}`,
    );
  return {
    statements,
    report: {
      rows: { [SEARCH_TABLE]: rows.length },
      droppedUnsourcedPartDimensions: 0,
      skippedReplicaDimensions: 0,
      proposedInterfaces: [],
    },
  };
}
