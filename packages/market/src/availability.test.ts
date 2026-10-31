import fc from 'fast-check';
import { describe, expect, test } from 'vitest';
import { AvailabilitySchema, isPurchasable, normalizeAvailability } from './index.ts';

describe('normalizeAvailability', () => {
  test.each([
    ['https://schema.org/InStock', 'en_stock'],
    ['http://schema.org/InStock', 'en_stock'],
    ['https://www.schema.org/InStock', 'en_stock'],
    ['schema:InStock', 'en_stock'],
    ['InStock', 'en_stock'],
    ['  instock ', 'en_stock'],
    ['in_stock', 'en_stock'],
    ['OnlineOnly', 'en_stock'],
    ['LimitedAvailability', 'pocas_unidades'],
    ['PreOrder', 'preventa'],
    ['PreSale', 'preventa'],
    ['BackOrder', 'bajo_pedido'],
    ['MadeToOrder', 'bajo_pedido'],
    ['OutOfStock', 'agotado'],
    ['SoldOut', 'agotado'],
    ['Reserved', 'agotado'],
    ['Discontinued', 'descatalogado'],
    ['InStoreOnly', 'desconocido'],
    ['https://example.com/InStock', 'desconocido'],
    ['en stock', 'desconocido'],
    ['', 'desconocido'],
  ])('%j → %s', (raw, expected) => {
    expect(normalizeAvailability(raw)).toBe(expected);
  });

  test('cualquier tipo que no sea texto es desconocido', () => {
    for (const raw of [undefined, null, 1, true, {}, ['InStock']]) {
      expect(normalizeAvailability(raw)).toBe('desconocido');
    }
  });

  test('propiedad: nunca lanza y siempre devuelve un valor del enum', () => {
    fc.assert(
      fc.property(fc.anything(), (raw) => {
        expect(AvailabilitySchema.safeParse(normalizeAvailability(raw)).success).toBe(true);
      }),
    );
  });

  test('solo se puede comprar lo que está en stock, en preventa o bajo pedido', () => {
    expect(isPurchasable('en_stock')).toBe(true);
    expect(isPurchasable('pocas_unidades')).toBe(true);
    expect(isPurchasable('agotado')).toBe(false);
    expect(isPurchasable('descatalogado')).toBe(false);
    expect(isPurchasable('desconocido')).toBe(false);
  });
});
