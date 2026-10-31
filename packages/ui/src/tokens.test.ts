import { describe, expect, test } from 'vitest';
import { BRAND, colors } from './index.ts';

describe('tokens', () => {
  test('todos los colores son hexadecimales de 6 dígitos', () => {
    for (const [name, value] of Object.entries(colors)) {
      expect(value, name).toMatch(/^#[0-9A-F]{6}$/);
    }
  });

  test('los nombres son kebab-case en español, sin acentos', () => {
    for (const name of Object.keys(colors)) expect(name).toMatch(/^[a-z]+(?:-[a-z]+)*$/);
  });
});

describe('marca', () => {
  test('nombre visible y prefijo del código de build', () => {
    expect(BRAND.name).toBe('Taller6mm');
    expect(BRAND.buildCodePrefix).toBe('T6M');
  });
});
