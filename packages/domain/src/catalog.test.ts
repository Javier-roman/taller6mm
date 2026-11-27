import { describe, expect, test } from 'vitest';
import { AssetSchema, DimensionSchema, fidelityLabel } from './index.ts';

const base = {
  subjectType: 'interface',
  subjectId: 'picatinny-mil-std-1913',
  key: 'ancho de ranura',
  value: 5.23,
  min: null,
  max: null,
  unit: 'mm',
  status: 'verified',
  sources: ['https://en.wikipedia.org/wiki/Picatinny_rail'],
  confidence: 'medium',
  checkedOn: '2026-11-11',
  note: null,
} as const;

describe('DimensionSchema', () => {
  test('acepta una cota con fuente, confianza y fecha (y conserva 0,01 mm)', () => {
    expect(DimensionSchema.safeParse(base).success).toBe(true);
  });

  test('acepta una cota desconocida: todo null, estado pending', () => {
    const unknown = { ...base, value: null, status: 'pending', sources: [], confidence: null, checkedOn: null };
    expect(DimensionSchema.safeParse(unknown).success).toBe(true);
  });

  test('rechaza un valor sin fuente, sin confianza o sin fecha', () => {
    expect(DimensionSchema.safeParse({ ...base, sources: [] }).success).toBe(false);
    expect(DimensionSchema.safeParse({ ...base, confidence: null }).success).toBe(false);
    expect(DimensionSchema.safeParse({ ...base, checkedOn: null }).success).toBe(false);
  });

  test('rechaza una cota pendiente con valor (sería inventada) y una sin valor ni pendiente', () => {
    expect(DimensionSchema.safeParse({ ...base, status: 'pending' }).success).toBe(false);
    expect(DimensionSchema.safeParse({ ...base, value: null }).success).toBe(false);
  });

  test('rechaza fuentes que no son https, negativos y rangos invertidos', () => {
    expect(DimensionSchema.safeParse({ ...base, sources: ['http://x.test'] }).success).toBe(false);
    expect(DimensionSchema.safeParse({ ...base, value: -1 }).success).toBe(false);
    expect(DimensionSchema.safeParse({ ...base, value: null, min: 9, max: 3 }).success).toBe(false);
  });

  test('un rango sin valor central es una cota conocida', () => {
    expect(DimensionSchema.safeParse({ ...base, value: null, min: 785, max: 889 }).success).toBe(true);
  });
});

describe('AssetSchema', () => {
  const asset = {
    id: 'a1',
    level: 'T0',
    view: '3d',
    licenseStatus: 'own',
    licenseText: 'propia',
    publishable: false,
    isDemo: true,
  } as const;

  test('una referencia de terceros nunca es publicable', () => {
    const third = { ...asset, isDemo: false, licenseStatus: 'third-party-reference' } as const;
    expect(AssetSchema.safeParse(third).success).toBe(true);
    expect(AssetSchema.safeParse({ ...third, publishable: true }).success).toBe(false);
  });

  test('un activo de demostración no es publicable', () => {
    expect(AssetSchema.safeParse({ ...asset, publishable: true }).success).toBe(false);
  });
});

test('etiqueta visible por nivel (ADR-0011)', () => {
  expect(fidelityLabel('T0')).toBe('ilustrativa');
  expect(fidelityLabel('T1')).toBe('aproximada');
  expect(fidelityLabel('T2')).toBe('aproximada');
  expect(fidelityLabel('T3')).toBe('verificada');
});
