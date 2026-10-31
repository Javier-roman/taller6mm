import fc from 'fast-check';
import { describe, expect, test } from 'vitest';
import {
  addMoney,
  CentsSchema,
  CURRENCY_CODES,
  CurrencyCodeSchema,
  CurrencyMismatchError,
  formatMoney,
  MillimetersSchema,
  type Money,
  minorUnitDigits,
  mm,
  money,
} from './index.ts';

describe('Millimeters', () => {
  test('redondea a 0,1 mm y las mitades se alejan de cero', () => {
    expect(mm(14)).toBe(14);
    expect(mm(6.01)).toBe(6);
    expect(mm(785.25)).toBe(785.3);
    expect(mm(-0.05)).toBe(-0.1);
    expect(Object.is(mm(-0.04), -0)).toBe(false);
  });

  test('rechaza valores no finitos o con más precisión de 0,1 mm', () => {
    expect(() => mm(Number.NaN)).toThrow(RangeError);
    expect(() => mm(Number.POSITIVE_INFINITY)).toThrow(RangeError);
    expect(MillimetersSchema.safeParse(1.25).success).toBe(false);
    expect(MillimetersSchema.safeParse(23.1).success).toBe(true);
  });

  test('propiedad: mm() es idempotente, válido y se desvía como mucho 0,05 mm', () => {
    fc.assert(
      fc.property(fc.double({ min: -1e6, max: 1e6, noNaN: true, noDefaultInfinity: true }), (x) => {
        const v = mm(x);
        expect(MillimetersSchema.safeParse(v).success).toBe(true);
        expect(mm(v)).toBe(v);
        expect(Math.abs(v - x)).toBeLessThanOrEqual(0.05 + 1e-9);
      }),
    );
  });
});

describe('Cents', () => {
  test('solo enteros seguros', () => {
    expect(CentsSchema.safeParse(1295).success).toBe(true);
    expect(CentsSchema.safeParse(-500).success).toBe(true);
    expect(CentsSchema.safeParse(12.95).success).toBe(false);
    expect(CentsSchema.safeParse(Number.NaN).success).toBe(false);
    expect(CentsSchema.safeParse(2 ** 53).success).toBe(false);
  });
});

describe('CurrencyCode (ISO 4217)', () => {
  test('acepta las monedas de las tiendas previstas y rechaza el resto', () => {
    for (const c of ['EUR', 'USD', 'GBP', 'PLN', 'HKD', 'CHF', 'SEK', 'DKK', 'CZK', 'JPY']) {
      expect(CurrencyCodeSchema.safeParse(c).success).toBe(true);
    }
    for (const c of ['eur', 'EU', 'EURO', 'XXX', 'XTS', 'XAU', 'BGN', 'ANG', 'HRK', '']) {
      expect(CurrencyCodeSchema.safeParse(c).success).toBe(false);
    }
  });

  test('la lista no tiene duplicados y son tres letras mayúsculas', () => {
    expect(new Set(CURRENCY_CODES).size).toBe(CURRENCY_CODES.length);
    for (const c of CURRENCY_CODES) expect(c).toMatch(/^[A-Z]{3}$/);
  });

  test('unidades menores de ISO 4217 (no las de visualización de CLDR)', () => {
    expect(minorUnitDigits('EUR')).toBe(2);
    expect(minorUnitDigits('JPY')).toBe(0);
    expect(minorUnitDigits('KWD')).toBe(3);
    expect(minorUnitDigits('HUF')).toBe(2);
  });
});

describe('Money', () => {
  const currency = fc.constantFrom(...CURRENCY_CODES);
  const amount = fc.integer({ min: -1e12, max: 1e12 });
  const moneyIn = (c: string) => amount.map((a) => money(a, c));

  test('propiedad: sumar es conmutativo y asociativo dentro de una moneda', () => {
    fc.assert(
      fc.property(
        currency.chain((c) => fc.tuple(moneyIn(c), moneyIn(c), moneyIn(c))),
        ([a, b, c]) => {
          expect(addMoney(a, b)).toEqual(addMoney(b, a));
          expect(addMoney(addMoney(a, b), c)).toEqual(addMoney(a, addMoney(b, c)));
        },
      ),
    );
  });

  test('nunca suma monedas distintas', () => {
    expect(() => addMoney(money(100, 'EUR'), money(100, 'USD'))).toThrow(CurrencyMismatchError);
  });

  test('detecta el desbordamiento', () => {
    const big: Money = money(Number.MAX_SAFE_INTEGER, 'EUR');
    expect(() => addMoney(big, money(1, 'EUR'))).toThrow(RangeError);
  });

  test('formatea en es-ES con los decimales de la moneda', () => {
    const spaces = (s: string) => s.replace(/\s/g, ' ');
    expect(spaces(formatMoney(money(895, 'EUR')))).toBe('8,95 €');
    expect(spaces(formatMoney(money(41240, 'EUR')))).toBe('412,40 €');
    expect(spaces(formatMoney(money(1500, 'JPY')))).toMatch(/^1500 (JPY|¥)$/);
  });
});
