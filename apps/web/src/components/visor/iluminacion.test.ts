import { COLOR_TOKENS } from '@taller6mm/ui/tokens';
import { describe, expect, it } from 'vitest';
import { parsearPresets, resolverColor } from './iluminacion.ts';
import { parsearIndice } from './modelos.ts';
import { PRESETS_MINIMOS } from './presets-minimos.ts';

const luz = { tipo: 'direccional', color: 'hueso', intensidad: 1, posicion: [1, 2, 3] };
const preset = (extra: Record<string, unknown> = {}) => ({
  id: 'prueba',
  nombre: 'Prueba',
  descripcion: 'Un preset de prueba.',
  fondo: 'carbon',
  exposicion: 1,
  entorno: 0.5,
  luces: [luz],
  ...extra,
});
const conjunto = (presets: unknown[], extra: Record<string, unknown> = {}) => ({
  esquema: 'iluminacion-presets/v1',
  por_defecto: 'prueba',
  presets,
  ...extra,
});

describe('presets de iluminación del visor', () => {
  it('los presets mínimos cumplen su propio formato', () => {
    const r = parsearPresets(PRESETS_MINIMOS);
    expect(r.ok).toBe(true);
  });

  it('el preset por defecto de los mínimos es la luz mate', () => {
    expect(PRESETS_MINIMOS.por_defecto).toBe('mate');
    expect(PRESETS_MINIMOS.presets.some((p) => p.id === 'penumbra')).toBe(true);
  });

  it('solo usa colores de token o hexadecimales', () => {
    for (const p of PRESETS_MINIMOS.presets) {
      for (const c of [p.fondo, ...p.luces.flatMap((l) => [l.color, l.color_suelo ?? l.color])]) {
        expect(/^#[0-9a-f]{6}$/i.test(c) || c in COLOR_TOKENS, `${p.id}: ${c}`).toBe(true);
      }
    }
  });

  it('resuelve tokens y hexadecimales a #rrggbb', () => {
    expect(resolverColor('hueso')).toBe(COLOR_TOKENS.hueso.hex);
    expect(resolverColor('#112233')).toBe('#112233');
  });

  it.each([
    ['no es un objeto', 'texto'],
    ['otro esquema', conjunto([preset()], { esquema: 'iluminacion-presets/v2' })],
    ['sin presets', conjunto([])],
    ['por_defecto inexistente', conjunto([preset()], { por_defecto: 'otro' })],
    ['id repetido', conjunto([preset(), preset()])],
    ['id con mayúsculas', conjunto([preset({ id: 'Mate' })], { por_defecto: 'Mate' })],
    ['color desconocido', conjunto([preset({ fondo: 'rosa-chicle' })])],
    ['exposición absurda', conjunto([preset({ exposicion: 400 })])],
    ['luz de tipo desconocido', conjunto([preset({ luces: [{ ...luz, tipo: 'laser' }] })])],
    ['luz sin posición', conjunto([preset({ luces: [{ tipo: 'foco', color: 'hueso', intensidad: 1 }] })])],
    ['luz en el origen', conjunto([preset({ luces: [{ ...luz, posicion: [0, 0, 0] }] })])],
    ['intensidad NaN', conjunto([preset({ luces: [{ ...luz, intensidad: Number.NaN }] })])],
    ['demasiadas luces', conjunto([preset({ luces: Array.from({ length: 9 }, () => luz) })])],
  ])('rechaza: %s', (_motivo, datos) => {
    expect(parsearPresets(datos).ok).toBe(false);
  });

  it('el hemisferio no necesita posición', () => {
    const r = parsearPresets(
      conjunto([preset({ luces: [{ tipo: 'hemisferio', color: 'hueso', color_suelo: 'acero', intensidad: 1 }] })]),
    );
    expect(r.ok).toBe(true);
  });
});

describe('índice de modelos del visor', () => {
  it('acepta el esquema esperado y rechaza lo demás', () => {
    const ok = { esquema: 'visor-indice/v1', aviso: '', presets_externos: null, piezas: [], montajes: [] };
    expect(parsearIndice(ok).montajes).toEqual([]);
    expect(() => parsearIndice({ ...ok, esquema: 'otro' })).toThrow();
    expect(() => parsearIndice({ ...ok, piezas: null })).toThrow();
    expect(() => parsearIndice(null)).toThrow();
  });
});
