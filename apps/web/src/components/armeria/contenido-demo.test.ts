// Los datos de ejemplo de las hojas cumplen los principios 1 y 2: marcados `is_demo`, con fecha de comprobación,
// en céntimos enteros y coherentes con los datos de los rótulos (zonas.ts) y con los sockets del armero.
import { describe, expect, it } from 'vitest';
import {
  ACCESORIOS_MUESTRA,
  ACCESORIOS_TOTAL,
  BAJADAS,
  BUILDS_TOP,
  COMPROBADO_DEMO,
  FAMILIAS_PREVISTAS,
  frescura,
  GUIAS_MUESTRA,
  GUIAS_TOTAL,
  porcentajeBajada,
  RANURAS_BANCO,
  RESUMENES,
  TAQUILLA_SIN_SESION,
  TIENDAS,
} from './contenido-demo.ts';
import { ARMERO, socketsDe } from './sockets.ts';
import { ZONAS } from './zonas.ts';

const esFechaIso = (valor: string) => !Number.isNaN(Date.parse(valor)) && valor.endsWith('Z');
const esEntero = (n: number) => Number.isInteger(n) && n > 0;

describe('contenido de ejemplo', () => {
  it('todo elemento y todo resumen llevan la marca is_demo', () => {
    const elementos = [
      ...FAMILIAS_PREVISTAS,
      ...ACCESORIOS_MUESTRA,
      ...BUILDS_TOP,
      ...RANURAS_BANCO,
      ...BAJADAS,
      ...TIENDAS,
      ...GUIAS_MUESTRA,
      ...Object.values(RESUMENES),
      TAQUILLA_SIN_SESION,
    ];
    for (const e of elementos) expect(e.is_demo).toBe(true);
  });

  it('hay un resumen fechado para cada una de las ocho zonas', () => {
    expect(Object.keys(RESUMENES).sort()).toEqual(ZONAS.map((z) => z.id).sort());
    for (const r of Object.values(RESUMENES)) {
      expect(r.texto.length).toBeGreaterThan(0);
      expect(r.comprobado === null || esFechaIso(r.comprobado)).toBe(true);
    }
  });

  it('los precios son céntimos enteros con fecha ISO UTC (o null explícito, nunca 0)', () => {
    for (const a of ACCESORIOS_MUESTRA) {
      if (a.centimos !== null) expect(esEntero(a.centimos)).toBe(true);
      if (a.centimos !== null) expect(a.comprobado !== null && esFechaIso(a.comprobado)).toBe(true);
    }
    for (const b of BUILDS_TOP) {
      expect(esEntero(b.centimos)).toBe(true);
      expect(esFechaIso(b.comprobado)).toBe(true);
    }
    for (const b of BAJADAS) {
      expect(esEntero(b.antes) && esEntero(b.ahora)).toBe(true);
      expect(b.ahora).toBeLessThan(b.antes);
      expect(esFechaIso(b.comprobado)).toBe(true);
    }
  });

  it('los datos de los rótulos de zonas.ts coinciden con el contenido de las hojas', () => {
    const dato = (id: string) => ZONAS.find((z) => z.id === id)?.dato.replaceAll(' ', ' ') ?? '';
    const ocupadas = socketsDe('replicas').filter((s) => s.replicaId !== null).length;
    expect(dato('replicas')).toBe(`${ocupadas} réplicas publicadas`);
    expect(dato('accesorios')).toBe(`${ACCESORIOS_TOTAL} accesorios · ${TIENDAS.length} tiendas`);
    expect(dato('mercado').startsWith(`${BAJADAS.length} bajadas`)).toBe(true);
    expect(dato('tiendas').startsWith(`${TIENDAS.length} tiendas`)).toBe(true);
    expect(dato('guias')).toBe(`${GUIAS_TOTAL} guías`);
    expect(ACCESORIOS_MUESTRA.length).toBeLessThan(ACCESORIOS_TOTAL);
    expect(GUIAS_MUESTRA.length).toBeLessThan(GUIAS_TOTAL);
  });

  it('el armero no inventa réplicas: 0 publicadas y una ranura libre por hueco', () => {
    const ranuras = socketsDe('replicas');
    expect(ranuras).toHaveLength(ARMERO.huecos);
    expect(ranuras.every((s) => s.replicaId === null)).toBe(true);
    expect(RESUMENES.replicas?.texto.startsWith('0 réplicas publicadas')).toBe(true);
  });

  it('la taquilla sin sesión no muestra cifras inventadas', () => {
    expect(TAQUILLA_SIN_SESION).toMatchObject({ sesion: false, builds: 0, favoritos: 0, alertas: 0 });
  });

  it('las tiendas se llaman «de ejemplo» y una no tiene fecha (bandera, no valor inventado)', () => {
    for (const t of TIENDAS) expect(t.nombre).toContain('de ejemplo');
    expect(TIENDAS.some((t) => t.comprobado === null)).toBe(true);
  });

  it('frescura: al día en 24 h, desfasada después y sin comprobar si no hay fecha', () => {
    expect(frescura(COMPROBADO_DEMO)).toBe('al-dia');
    expect(frescura('2026-11-24T09:10:00Z')).toBe('desfasada');
    expect(frescura(null)).toBe('sin-comprobar');
    expect(frescura('no es una fecha')).toBe('sin-comprobar');
  });

  it('porcentajeBajada redondea al entero', () => {
    expect(porcentajeBajada({ antes: 2995, ahora: 2495 })).toBe(17);
    expect(porcentajeBajada({ antes: 1000, ahora: 1000 })).toBe(0);
  });
});
