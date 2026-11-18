import { describe, expect, it } from 'vitest';
import { dirAGltf, nombreDePreset, parsearPresets } from './iluminacion.ts';
import { parsearIndice, parsearMateriales } from './modelos.ts';
import { PRESETS_MINIMOS } from './presets-minimos.ts';

const luz = { id: 'clave', dir: [0.5, -1, 1.1], dist: 1.3, energia_d2: 85, tam_d: 2.6, color: [1, 1, 1] };
const preset = (extra: Record<string, unknown> = {}) => ({
  descripcion: 'Un preset de prueba.',
  exposicion_ev: -0.35,
  tono: 'AgX',
  mundo: { abajo: [0.1, 0.1, 0.1], arriba: [0.3, 0.3, 0.3], intensidad: 1 },
  suelo: { color: [0.2, 0.2, 0.2], rugosidad: 0.5, metalico: 0 },
  rugosidad_delta: 0.05,
  luces: [luz],
  ...extra,
});
const brillo = {
  global: { min: 0.5, max: 1.5, defecto: 1 },
  rug_por_factor: 0.12,
  banda_rugosidad: 0.1,
  rugosidad_minima_absoluta: 0.02,
};
const conjunto = (presets: Record<string, unknown>, extra: Record<string, unknown> = {}) => ({
  esquema: 'iluminacion-presets/v1',
  defecto: 'mate_suave',
  brillo,
  presets,
  ...extra,
});

describe('presets de iluminación del visor (iluminacion-presets/v1)', () => {
  it('la copia mínima, escrita como archivo del catálogo, se lee sin error y su defecto es mate_suave', () => {
    const archivo = conjunto(
      Object.fromEntries(PRESETS_MINIMOS.presets.map(({ id: _id, nombre: _nombre, ...resto }) => [_id, resto])),
      { defecto: PRESETS_MINIMOS.defecto, brillo: PRESETS_MINIMOS.brillo },
    );
    const r = parsearPresets(archivo);
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.valor.presets).toEqual(PRESETS_MINIMOS.presets);
    expect(PRESETS_MINIMOS.defecto).toBe('mate_suave');
  });

  it('lee el catálogo en su forma de archivo y pone nombre visible', () => {
    const r = parsearPresets(conjunto({ mate_suave: preset() }));
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.valor.presets[0]?.nombre).toBe('Mate suave');
      expect(r.valor.presets[0]?.tono).toBe('AgX');
    }
  });

  it('convierte ejes de Blender (Z arriba) a glTF (Y arriba)', () => {
    expect(dirAGltf([0.5, -1, 1.1])).toEqual([0.5, 1.1, 1]);
    expect(nombreDePreset('dramatica_penumbra')).toBe('Penumbra');
    expect(nombreDePreset('otro_preset')).toBe('Otro preset');
  });

  it.each([
    ['no es un objeto', 'texto'],
    ['otro esquema', conjunto({ mate_suave: preset() }, { esquema: 'iluminacion-presets/v2' })],
    ['sin presets', conjunto({})],
    ['defecto inexistente', conjunto({ mate_suave: preset() }, { defecto: 'otro' })],
    ['id con mayúsculas', conjunto({ Mate: preset() }, { defecto: 'Mate' })],
    ['exposición absurda', conjunto({ mate_suave: preset({ exposicion_ev: 400 }) })],
    ['tono desconocido', conjunto({ mate_suave: preset({ tono: 'Raro' }) })],
    ['mundo sin color', conjunto({ mate_suave: preset({ mundo: { intensidad: 1 } }) })],
    ['luz sin dirección', conjunto({ mate_suave: preset({ luces: [{ ...luz, dir: [0, 0, 0] }] }) })],
    ['energía NaN', conjunto({ mate_suave: preset({ luces: [{ ...luz, energia_d2: Number.NaN }] }) })],
    ['tamaño cero', conjunto({ mate_suave: preset({ luces: [{ ...luz, tam_d: 0 }] }) })],
    ['demasiadas luces', conjunto({ mate_suave: preset({ luces: Array.from({ length: 11 }, () => luz) }) })],
    ['sin control de brillo', conjunto({ mate_suave: preset() }, { brillo: null })],
  ])('rechaza: %s', (_motivo, datos) => {
    expect(parsearPresets(datos).ok).toBe(false);
  });
});

describe('índice y materiales del visor', () => {
  it('acepta el esquema esperado y rechaza lo demás', () => {
    const ok = { esquema: 'visor-indice/v1', aviso: '', presets_externos: null, piezas: [], montajes: [] };
    expect(parsearIndice(ok).montajes).toEqual([]);
    expect(() => parsearIndice({ ...ok, esquema: 'otro' })).toThrow();
    expect(() => parsearIndice({ ...ok, piezas: null })).toThrow();
    expect(() => parsearIndice(null)).toThrow();
  });

  it('los materiales exportados traen su esquema y listas', () => {
    const ok = { esquema: 'materiales-visor/v1', materiales: {}, asignaciones: {} };
    expect(parsearMateriales(ok).asignaciones).toEqual({});
    expect(() => parsearMateriales({ ...ok, esquema: 'x' })).toThrow();
    expect(() => parsearMateriales({ ...ok, materiales: [] })).toThrow();
  });
});
