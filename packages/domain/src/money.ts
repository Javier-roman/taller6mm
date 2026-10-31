// Dinero en unidades menores enteras («céntimos») + moneda ISO 4217 (CLAUDE.md, docs/07 §3.4).
// Nunca coma flotante para importes: 0,1 + 0,2 ≠ 0,3.
import { z } from 'zod';
import { type CurrencyCode, CurrencyCodeSchema, minorUnitDigits } from './currency.ts';

export const CentsSchema = z.int({ error: 'Los importes van en céntimos enteros' }).brand<'Cents'>();

/** Importe en la unidad menor de su moneda (céntimos de euro, peniques, yenes…), entero y seguro. */
export type Cents = z.infer<typeof CentsSchema>;

export const MoneySchema = z.object({ amount: CentsSchema, currency: CurrencyCodeSchema }).readonly();

export type Money = z.infer<typeof MoneySchema>;

export class CurrencyMismatchError extends Error {
  override name = 'CurrencyMismatchError';
  constructor(a: CurrencyCode, b: CurrencyCode) {
    super(`No se pueden sumar ${a} y ${b} sin un tipo de cambio`);
  }
}

/** Valida y crea un importe. Lanza un error de Zod si los datos no son válidos. */
export function money(amount: number, currency: string): Money {
  return MoneySchema.parse({ amount, currency });
}

/** Suma importes de la misma moneda; lanza `CurrencyMismatchError` si difieren. */
export function addMoney(a: Money, b: Money): Money {
  if (a.currency !== b.currency) throw new CurrencyMismatchError(a.currency, b.currency);
  const total = a.amount + b.amount;
  if (!Number.isSafeInteger(total)) throw new RangeError('La suma desborda el rango entero seguro');
  return money(total, a.currency);
}

/** Formato para la interfaz con los decimales de ISO 4217 (por defecto, español de España). */
export function formatMoney(value: Money, locale = 'es-ES'): string {
  const digits = minorUnitDigits(value.currency);
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: value.currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value.amount / 10 ** digits);
}
