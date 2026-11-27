// Tipos y contratos compartidos de Taller6mm (Zod 4). Lógica pura: sin E/S.
export {
  ASSET_VIEWS,
  type Asset,
  AssetSchema,
  CONFIDENCES,
  type Confidence,
  ConfidenceSchema,
  DIMENSION_STATUSES,
  DIMENSION_SUBJECTS,
  DIMENSION_UNITS,
  type Dimension,
  DimensionSchema,
  DimensionStatusSchema,
  DimensionSubjectSchema,
  FIDELITY_LABELS,
  FIDELITY_LEVELS,
  type FidelityLabel,
  type FidelityLevel,
  FidelityLevelSchema,
  fidelityLabel,
  IsoDateSchema,
  LICENSE_STATUSES,
  LicenseStatusSchema,
} from './catalog.ts';
export { CURRENCY_CODES, type CurrencyCode, CurrencyCodeSchema, minorUnitDigits } from './currency.ts';
export {
  addMoney,
  type Cents,
  CentsSchema,
  CurrencyMismatchError,
  formatMoney,
  type Money,
  MoneySchema,
  money,
} from './money.ts';
export { isTenthOfMillimeter, type Millimeters, MillimetersSchema, mm } from './units.ts';
