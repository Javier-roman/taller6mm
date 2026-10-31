// Tipos del motor de compatibilidad (docs/03 §5.1). TS puro, determinista y sin E/S.
// Cada veredicto lleva motivo, fuente y confianza (principio 3: compatibilidad explicable).
import { z } from 'zod';

export const VERDICTS = [
  'compatible',
  'compatible_con_adaptador',
  'requiere_modificacion',
  'incompatible',
  'desconocido',
] as const;

export const VerdictSchema = z.enum(VERDICTS);
export type Verdict = z.infer<typeof VerdictSchema>;

/** De dónde sale el dato. `comunidad` lleva el número de informes que lo respaldan. */
export const SourceSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('estandar'), reference: z.string().min(1) }),
  z.object({ kind: z.literal('fabricante'), reference: z.string().min(1) }),
  z.object({ kind: z.literal('comunidad'), reports: z.int().positive() }),
  z.object({ kind: z.literal('manual'), reviewer: z.string().min(1) }),
]);
export type Source = z.infer<typeof SourceSchema>;

/** Confianza entre 0 y 1. Se muestra como alta (≥ 0,8), media (≥ 0,5) o baja. */
export const ConfidenceSchema = z.number().min(0).max(1);
export type Confidence = z.infer<typeof ConfidenceSchema>;

export type ConfidenceLabel = 'alta' | 'media' | 'baja';

export function confidenceLabel(confidence: Confidence): ConfidenceLabel {
  const c = ConfidenceSchema.parse(confidence);
  if (c >= 0.8) return 'alta';
  if (c >= 0.5) return 'media';
  return 'baja';
}

export const VerdictReportSchema = z
  .object({
    verdict: VerdictSchema,
    reason: z.string().trim().min(1, 'Todo veredicto explica su motivo'),
    source: SourceSchema,
    confidence: ConfidenceSchema,
  })
  .readonly();
export type VerdictReport = z.infer<typeof VerdictReportSchema>;

/**
 * Gravedad para el estado global de un build: manda el peor veredicto. `desconocido` pesa más
 * que cualquier forma de «encaja», porque nunca se presenta como compatible.
 */
const SEVERITY: Record<Verdict, number> = {
  compatible: 0,
  compatible_con_adaptador: 1,
  requiere_modificacion: 2,
  desconocido: 3,
  incompatible: 4,
};

/** Estado global de un conjunto de veredictos. Un build vacío es `compatible`. */
export function overallVerdict(verdicts: Iterable<Verdict>): Verdict {
  let worst: Verdict = 'compatible';
  for (const v of verdicts) if (SEVERITY[v] > SEVERITY[worst]) worst = v;
  return worst;
}

/** ¿Se puede presentar como «encaja»? Solo los dos veredictos que no exigen trabajo de taller. */
export function fits(verdict: Verdict): boolean {
  return verdict === 'compatible' || verdict === 'compatible_con_adaptador';
}
