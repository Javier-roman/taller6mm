// Tipos y contratos compartidos de Taller6mm (Zod 4). Lógica pura: sin E/S.
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
