// Esquema Drizzle de la base `core`, parte de catálogo (docs/07 §3.1, ADR-0012). Sin comunidad ni
// moderación todavía (fases 5-6). Reglas que garantiza la propia base con CHECK (principios 2, 3 y 5):
//   - una cota conocida lleva fuente, confianza y fecha; una desconocida es NULL + estado `pending`;
//   - un activo de terceros o de demostración nunca es publicable;
//   - todo lo `verified` lleva URL, fecha y confianza.
// Las mismas reglas viven en Zod (`@taller6mm/domain`) para validar antes de llegar aquí.
import { sql } from 'drizzle-orm';
import {
  type AnySQLiteColumn,
  check,
  index,
  integer,
  primaryKey,
  real,
  sqliteTable,
  text,
  uniqueIndex,
} from 'drizzle-orm/sqlite-core';
import { metaTable } from './meta.ts';

export const meta = metaTable();

/** Valores permitidos como lista SQL (`'a','b'`). Solo constantes del código, nunca entrada externa. */
const list = (values: readonly string[]) => sql.raw(values.map((v) => `'${v}'`).join(','));

export const CONFIDENCE = ['high', 'medium', 'low'] as const;
export const LEVELS = ['T0', 'T1', 'T2', 'T3'] as const;
export const SOURCE_STATUS = ['verified', 'pending'] as const;
export const INTERFACE_STATUS = ['verified', 'pending', 'proposed'] as const;
export const INTERFACE_ROLES = ['offers', 'requires', 'unspecified'] as const;
export const PART_KINDS = ['part', 'accessory', 'consumable'] as const;
export const DIMENSION_SUBJECT_TYPES = ['interface', 'platform', 'part_family', 'part', 'replica'] as const;
export const DIMENSION_STATUS = ['verified', 'cited', 'pending'] as const;
export const DIMENSION_UNIT = ['mm', 'count'] as const;
export const ASSET_VIEW = ['2d', '3d'] as const;
export const ASSET_LICENSE = ['own', 'ceded', 'cc0', 'cc-by', 'third-party-reference'] as const;

// --- Marcas, plataformas e interfaces --------------------------------------------------------------

export const brands = sqliteTable('brands', {
  id: text('id').primaryKey(),
  name: text('name').notNull().unique(),
  isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
});

export const platformFamilies = sqliteTable('platform_families', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
});

/** Estándar de montaje (Picatinny, rosca de 14 mm, M-LOK, STANAG…). Sus medidas viven en `dimensions`. */
export const interfaces = sqliteTable(
  'interfaces',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    kind: text('kind'),
    description: text('description'),
    status: text('status', { enum: INTERFACE_STATUS }).notNull(),
    sourceUrl: text('source_url'),
    sourceCheckedOn: text('source_checked_on'),
    confidence: text('confidence', { enum: CONFIDENCE }),
    notes: text('notes'),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    check('interfaces_status_ck', sql`${t.status} IN (${list(INTERFACE_STATUS)})`),
    check('interfaces_confidence_ck', sql`${t.confidence} IS NULL OR ${t.confidence} IN (${list(CONFIDENCE)})`),
    check(
      'interfaces_verified_has_source_ck',
      sql`${t.status} <> 'verified' OR (${t.sourceUrl} IS NOT NULL AND ${t.sourceCheckedOn} IS NOT NULL AND ${t.confidence} IS NOT NULL)`,
    ),
  ],
);

/** Plataforma de réplica (M4A1, AK-74…): agrupa réplicas de varios fabricantes con la misma base. */
export const platforms = sqliteTable(
  'platforms',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    familyId: text('family_id')
      .notNull()
      .references(() => platformFamilies.id),
    /** JSON validado con Zod: mecanismos (AEG, GBBR, HPA…) y variantes conocidas. */
    mechanisms: text('mechanisms').notNull(),
    variants: text('variants').notNull(),
    magazineWellInterfaceId: text('magazine_well_interface_id').references(() => interfaces.id),
    status: text('status', { enum: SOURCE_STATUS }).notNull(),
    sourceUrl: text('source_url'),
    sourceCheckedOn: text('source_checked_on'),
    confidence: text('confidence', { enum: CONFIDENCE }),
    notes: text('notes'),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    index('platforms_family_idx').on(t.familyId),
    check('platforms_status_ck', sql`${t.status} IN (${list(SOURCE_STATUS)})`),
    check('platforms_confidence_ck', sql`${t.confidence} IS NULL OR ${t.confidence} IN (${list(CONFIDENCE)})`),
    check(
      'platforms_verified_has_source_ck',
      sql`${t.status} <> 'verified' OR (${t.sourceUrl} IS NOT NULL AND ${t.sourceCheckedOn} IS NOT NULL AND ${t.confidence} IS NOT NULL)`,
    ),
  ],
);

/** Interfaces que expone una plataforma (rosca del cañón, raíl, pozo de cargador…). */
export const platformInterfaces = sqliteTable(
  'platform_interfaces',
  {
    platformId: text('platform_id')
      .notNull()
      .references(() => platforms.id),
    interfaceId: text('interface_id')
      .notNull()
      .references(() => interfaces.id),
  },
  (t) => [
    primaryKey({ columns: [t.platformId, t.interfaceId] }),
    index('platform_interfaces_iface_idx').on(t.interfaceId),
  ],
);

/** Fabricantes que hacen réplicas de la plataforma (conocimiento del sector hasta que haya fuente por réplica). */
export const platformBrands = sqliteTable(
  'platform_brands',
  {
    platformId: text('platform_id')
      .notNull()
      .references(() => platforms.id),
    brandId: text('brand_id')
      .notNull()
      .references(() => brands.id),
  },
  (t) => [primaryKey({ columns: [t.platformId, t.brandId] })],
);

/** Modelo concreto de un fabricante sobre una plataforma. El nivel de fidelidad es siempre visible (ADR-0011). */
export const replicas = sqliteTable(
  'replicas',
  {
    id: text('id').primaryKey(),
    platformId: text('platform_id')
      .notNull()
      .references(() => platforms.id),
    brandId: text('brand_id')
      .notNull()
      .references(() => brands.id),
    model: text('model').notNull(),
    /** AEG, GBBR, HPA…; NULL = desconocido. */
    mechanism: text('mechanism'),
    level: text('level', { enum: LEVELS }).notNull().default('T0'),
    sourceUrl: text('source_url'),
    sourceCheckedOn: text('source_checked_on'),
    notes: text('notes'),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    uniqueIndex('replicas_brand_model_uq').on(t.brandId, t.model),
    index('replicas_platform_idx').on(t.platformId),
    check('replicas_level_ck', sql`${t.level} IN (${list(LEVELS)})`),
  ],
);

// --- Categorías, familias de piezas y piezas -------------------------------------------------------

/** Árbol de categorías (grupos: cuerpos, guardamanos, cañones, ópticas…). */
export const categories = sqliteTable(
  'categories',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    parentId: text('parent_id').references((): AnySQLiteColumn => categories.id),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [index('categories_parent_idx').on(t.parentId)],
);

/** Familia de piezas (guardamanos M-LOK, cargador AR midcap…): qué parámetros e interfaces maneja. */
export const partFamilies = sqliteTable(
  'part_families',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    categoryId: text('category_id')
      .notNull()
      .references(() => categories.id),
    expectedLevel: text('expected_level', { enum: LEVELS }).notNull(),
    /** `aplica_a: ["*"]` del catálogo: sirve a cualquier plataforma. */
    appliesToAll: integer('applies_to_all', { mode: 'boolean' }).notNull(),
    parameters: text('parameters').notNull(),
    exampleBrands: text('example_brands').notNull(),
    status: text('status', { enum: SOURCE_STATUS }).notNull(),
    sourceUrl: text('source_url'),
    sourceCheckedOn: text('source_checked_on'),
    confidence: text('confidence', { enum: CONFIDENCE }),
    notes: text('notes'),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    index('part_families_category_idx').on(t.categoryId),
    check('part_families_level_ck', sql`${t.expectedLevel} IN (${list(LEVELS)})`),
    check('part_families_status_ck', sql`${t.status} IN (${list(SOURCE_STATUS)})`),
    check('part_families_confidence_ck', sql`${t.confidence} IS NULL OR ${t.confidence} IN (${list(CONFIDENCE)})`),
    check(
      'part_families_verified_has_source_ck',
      sql`${t.status} <> 'verified' OR (${t.sourceUrl} IS NOT NULL AND ${t.sourceCheckedOn} IS NOT NULL AND ${t.confidence} IS NOT NULL)`,
    ),
  ],
);

export const partFamilyPlatformFamilies = sqliteTable(
  'part_family_platform_families',
  {
    partFamilyId: text('part_family_id')
      .notNull()
      .references(() => partFamilies.id),
    platformFamilyId: text('platform_family_id')
      .notNull()
      .references(() => platformFamilies.id),
  },
  (t) => [primaryKey({ columns: [t.partFamilyId, t.platformFamilyId] })],
);

/**
 * Interfaces de una familia. El catálogo actual no distingue si la familia las ofrece o las requiere:
 * queda `unspecified` (honesto) hasta que el motor de compatibilidad lo aclare.
 */
export const partFamilyInterfaces = sqliteTable(
  'part_family_interfaces',
  {
    partFamilyId: text('part_family_id')
      .notNull()
      .references(() => partFamilies.id),
    interfaceId: text('interface_id')
      .notNull()
      .references(() => interfaces.id),
    role: text('role', { enum: INTERFACE_ROLES }).notNull(),
  },
  (t) => [
    primaryKey({ columns: [t.partFamilyId, t.interfaceId, t.role] }),
    index('part_family_interfaces_iface_idx').on(t.interfaceId),
    check('part_family_interfaces_role_ck', sql`${t.role} IN (${list(INTERFACE_ROLES)})`),
  ],
);

/** Pieza o accesorio concreto. El nivel es siempre visible (ADR-0011): la etiqueta se deriva en `domain`. */
export const parts = sqliteTable(
  'parts',
  {
    id: text('id').primaryKey(),
    partFamilyId: text('part_family_id').references(() => partFamilies.id),
    /** Familia del generador paramétrico (`optica.red_dot_tubular`); NULL si no procede de uno. */
    generatorFamily: text('generator_family'),
    name: text('name').notNull(),
    kind: text('kind', { enum: PART_KINDS }).notNull(),
    brandId: text('brand_id').references(() => brands.id),
    level: text('level', { enum: LEVELS }).notNull().default('T0'),
    /** Parámetros de entrada del generador (JSON). No son cotas: las cotas con fuente van en `dimensions`. */
    parameters: text('parameters'),
    notes: text('notes'),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    index('parts_family_idx').on(t.partFamilyId),
    check('parts_kind_ck', sql`${t.kind} IN (${list(PART_KINDS)})`),
    check('parts_level_ck', sql`${t.level} IN (${list(LEVELS)})`),
  ],
);

/** Interfaces que una pieza ofrece o requiere. */
export const partInterfaces = sqliteTable(
  'part_interfaces',
  {
    partId: text('part_id')
      .notNull()
      .references(() => parts.id),
    interfaceId: text('interface_id')
      .notNull()
      .references(() => interfaces.id),
    role: text('role', { enum: ['offers', 'requires'] as const }).notNull(),
  },
  (t) => [
    primaryKey({ columns: [t.partId, t.interfaceId, t.role] }),
    index('part_interfaces_iface_idx').on(t.interfaceId),
    check('part_interfaces_role_ck', sql`${t.role} IN ('offers','requires')`),
  ],
);

// --- Cotas y activos -------------------------------------------------------------------------------

/**
 * Cotas con fuente, confianza y fecha. Polimórfica (`subject_type` + `subject_id`): la integridad
 * del sujeto la valida la capa de datos y las semillas. Lo desconocido: `status = 'pending'` y todo
 * NULL; nunca un valor inventado.
 */
export const dimensions = sqliteTable(
  'dimensions',
  {
    id: integer('id').primaryKey({ autoIncrement: true }),
    subjectType: text('subject_type', { enum: DIMENSION_SUBJECT_TYPES }).notNull(),
    subjectId: text('subject_id').notNull(),
    key: text('key').notNull(),
    /** Valor publicado, sin redondear (las interfaces vienen de pulgadas: 5,23 mm). */
    value: real('value'),
    valueMin: real('value_min'),
    valueMax: real('value_max'),
    unit: text('unit', { enum: DIMENSION_UNIT }).notNull(),
    status: text('status', { enum: DIMENSION_STATUS }).notNull(),
    /** JSON: lista de URLs https. */
    sources: text('sources').notNull(),
    confidence: text('confidence', { enum: CONFIDENCE }),
    checkedOn: text('checked_on'),
    note: text('note'),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    uniqueIndex('dimensions_subject_key_uq').on(t.subjectType, t.subjectId, t.key),
    check('dimensions_subject_type_ck', sql`${t.subjectType} IN (${list(DIMENSION_SUBJECT_TYPES)})`),
    check('dimensions_unit_ck', sql`${t.unit} IN (${list(DIMENSION_UNIT)})`),
    check('dimensions_status_ck', sql`${t.status} IN (${list(DIMENSION_STATUS)})`),
    check('dimensions_confidence_ck', sql`${t.confidence} IS NULL OR ${t.confidence} IN (${list(CONFIDENCE)})`),
    check(
      'dimensions_nonnegative_ck',
      sql`(${t.value} IS NULL OR ${t.value} >= 0) AND (${t.valueMin} IS NULL OR ${t.valueMin} >= 0) AND (${t.valueMax} IS NULL OR ${t.valueMax} >= 0)`,
    ),
    // Desconocida: nada relleno. Conocida: valor (o rango), fuente, confianza y fecha.
    check(
      'dimensions_honest_ck',
      sql`(${t.status} = 'pending' AND ${t.value} IS NULL AND ${t.valueMin} IS NULL AND ${t.valueMax} IS NULL AND ${t.confidence} IS NULL AND ${t.checkedOn} IS NULL AND json_array_length(${t.sources}) = 0)
        OR (${t.status} <> 'pending' AND (${t.value} IS NOT NULL OR ${t.valueMin} IS NOT NULL OR ${t.valueMax} IS NOT NULL) AND ${t.confidence} IS NOT NULL AND ${t.checkedOn} IS NOT NULL AND json_array_length(${t.sources}) > 0)`,
    ),
    check('dimensions_range_ck', sql`${t.valueMin} IS NULL OR ${t.valueMax} IS NULL OR ${t.valueMin} <= ${t.valueMax}`),
  ],
);

/** Referencia a un activo (nivel y licencia). Los binarios viven en R2 privado: aquí solo su clave. */
export const assets = sqliteTable(
  'assets',
  {
    id: text('id').primaryKey(),
    partId: text('part_id').references(() => parts.id),
    replicaId: text('replica_id').references(() => replicas.id),
    view: text('view', { enum: ASSET_VIEW }).notNull(),
    level: text('level', { enum: LEVELS }).notNull(),
    licenseStatus: text('license_status', { enum: ASSET_LICENSE }).notNull(),
    licenseText: text('license_text'),
    sourceUrl: text('source_url'),
    /** Clave del objeto en R2 (nunca el binario). NULL = aún no subido. */
    r2Key: text('r2_key'),
    sha256: text('sha256'),
    publishable: integer('publishable', { mode: 'boolean' }).notNull().default(false),
    isDemo: integer('is_demo', { mode: 'boolean' }).notNull(),
  },
  (t) => [
    index('assets_part_idx').on(t.partId),
    index('assets_replica_idx').on(t.replicaId),
    check('assets_view_ck', sql`${t.view} IN (${list(ASSET_VIEW)})`),
    check('assets_level_ck', sql`${t.level} IN (${list(LEVELS)})`),
    check('assets_license_ck', sql`${t.licenseStatus} IN (${list(ASSET_LICENSE)})`),
    check('assets_one_owner_ck', sql`(${t.partId} IS NULL) <> (${t.replicaId} IS NULL)`),
    // Principio 5: solo se publica lo propio o lo cedido; las fotos de terceros son referencia interna.
    check(
      'assets_publishable_ck',
      sql`${t.publishable} = 0 OR (${t.licenseStatus} <> 'third-party-reference' AND ${t.isDemo} = 0)`,
    ),
  ],
);
