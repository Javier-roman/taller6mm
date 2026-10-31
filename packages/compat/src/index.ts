// Motor de compatibilidad de Taller6mm (docs/03 §5). TS puro, sin E/S y determinista.
export {
  type Confidence,
  type ConfidenceLabel,
  ConfidenceSchema,
  confidenceLabel,
  fits,
  overallVerdict,
  type Source,
  SourceSchema,
  VERDICTS,
  type Verdict,
  type VerdictReport,
  VerdictReportSchema,
  VerdictSchema,
} from './verdict.ts';
