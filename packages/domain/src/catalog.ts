// Contratos del catálogo (docs/07 §3.1, ADR-0011, ADR-0012): confianza, nivel de fidelidad, cotas con
// fuente y activos con licencia. Lo desconocido es `null` + bandera (`status: 'pending'`), nunca un
// valor inventado (principio 2). Las mismas reglas están en CHECK de SQL en `packages/db`: aquí se
// validan al leer y al escribir, allí las garantiza la base aunque falle el código.
import { z } from 'zod';

export const CONFIDENCES = ['high', 'medium', 'low'] as const;
export const ConfidenceSchema = z.enum(CONFIDENCES);
export type Confidence = z.infer<typeof ConfidenceSchema>;

/** Nivel de fidelidad de docs/05 (T0 plano técnico … T3 escaneado y verificado). */
export const FIDELITY_LEVELS = ['T0', 'T1', 'T2', 'T3'] as const;
export const FidelityLevelSchema = z.enum(FIDELITY_LEVELS);
export type FidelityLevel = z.infer<typeof FidelityLevelSchema>;

export const FIDELITY_LABELS = ['ilustrativa', 'aproximada', 'verificada'] as const;
export type FidelityLabel = (typeof FIDELITY_LABELS)[number];

/** Etiqueta visible de la pieza (ADR-0011 §4): T0 ilustrativa, T1-T2 aproximada, T3 verificada. */
export function fidelityLabel(level: FidelityLevel): FidelityLabel {
  if (level === 'T0') return 'ilustrativa';
  return level === 'T3' ? 'verificada' : 'aproximada';
}

export const DIMENSION_SUBJECTS = ['interface', 'platform', 'part_family', 'part', 'replica'] as const;
export const DimensionSubjectSchema = z.enum(DIMENSION_SUBJECTS);

/** `verified` = ficha del fabricante o norma; `cited` = fuente pública no oficial; `pending` = desconocida. */
export const DIMENSION_STATUSES = ['verified', 'cited', 'pending'] as const;
export const DimensionStatusSchema = z.enum(DIMENSION_STATUSES);

export const DIMENSION_UNITS = ['mm', 'count'] as const;

const HttpsUrlSchema = z
  .string()
  .regex(/^https:\/\/\S+$/, 'La fuente debe ser una URL https')
  .max(2048);
/** Fecha ISO 8601 (solo día, en UTC) de la última comprobación. */
export const IsoDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Fecha ISO 8601 AAAA-MM-DD');

const nonNegative = z.number().finite().nonnegative();

/**
 * Cota con fuente. Las medidas de las interfaces estándar vienen de pulgadas y llevan hasta 0,01 mm
 * (5,23 mm), por eso no usan `Millimeters` (0,1 mm): ahí se conserva lo publicado.
 */
export const DimensionSchema = z
  .object({
    subjectType: DimensionSubjectSchema,
    subjectId: z.string().min(1),
    key: z.string().min(1),
    value: nonNegative.nullable(),
    min: nonNegative.nullable(),
    max: nonNegative.nullable(),
    unit: z.enum(DIMENSION_UNITS),
    status: DimensionStatusSchema,
    sources: z.array(HttpsUrlSchema),
    confidence: ConfidenceSchema.nullable(),
    checkedOn: IsoDateSchema.nullable(),
    note: z.string().nullable(),
  })
  .superRefine((d, ctx) => {
    const known = d.value !== null || d.min !== null || d.max !== null;
    if (d.status === 'pending') {
      if (known) ctx.addIssue({ code: 'custom', message: 'Una cota pendiente no puede llevar valor' });
      return;
    }
    if (!known) ctx.addIssue({ code: 'custom', message: 'Una cota no pendiente necesita un valor' });
    if (d.sources.length === 0) ctx.addIssue({ code: 'custom', message: 'Ninguna cota sin fuente' });
    if (d.confidence === null) ctx.addIssue({ code: 'custom', message: 'Ninguna cota sin confianza' });
    if (d.checkedOn === null) ctx.addIssue({ code: 'custom', message: 'Ninguna cota sin fecha de consulta' });
    if (d.min !== null && d.max !== null && d.min > d.max)
      ctx.addIssue({ code: 'custom', message: 'El mínimo no puede superar al máximo' });
  });
export type Dimension = z.infer<typeof DimensionSchema>;

/** Licencias de un activo; `third-party-reference` es solo referencia interna (principio 5). */
export const LICENSE_STATUSES = ['own', 'ceded', 'cc0', 'cc-by', 'third-party-reference'] as const;
export const LicenseStatusSchema = z.enum(LICENSE_STATUSES);

export const ASSET_VIEWS = ['2d', '3d'] as const;

/** Activo: solo referencia al nivel y la licencia; los binarios viven en R2 privado. */
export const AssetSchema = z
  .object({
    id: z.string().min(1),
    level: FidelityLevelSchema,
    view: z.enum(ASSET_VIEWS),
    licenseStatus: LicenseStatusSchema,
    licenseText: z.string().nullable(),
    publishable: z.boolean(),
    isDemo: z.boolean(),
  })
  .superRefine((a, ctx) => {
    if (a.publishable && a.licenseStatus === 'third-party-reference')
      ctx.addIssue({ code: 'custom', message: 'Una foto o modelo de terceros nunca se publica' });
    if (a.publishable && a.isDemo)
      ctx.addIssue({ code: 'custom', message: 'Un activo de demostración no es publicable' });
  });
export type Asset = z.infer<typeof AssetSchema>;
