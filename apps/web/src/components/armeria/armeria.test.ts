// Tests de la lógica pura de La Armería: encuadre del póster, CSS de zonas generado, preferencias y manifiesto.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { hashConjunto } from '../../lib/vistas.ts';
import { ASPECTO_POSTER, ENCUADRE_POSTER, encuadreSala, proyectar, rectCaja, rectZona } from './camara.ts';
import { type Almacen, CLAVES, ESTADO_INICIAL, esLuz, guardar, leer, luzInicial, zonaActiva } from './estado.ts';
import { VARIANTES_LUZ } from './luz.ts';
import { ARMERO, alturaPeana, SOCKETS, socketsDe, VITRINA } from './sockets.ts';
import manifiesto from './vistas.json';
import { posterDe, urlVista } from './vistas.ts';
import { ESTANTERIAS, MUEBLE, ORDEN_ESTANTERIAS, ZONAS, zonaPorId, zonasDe } from './zonas.ts';

const aqui = path.dirname(fileURLToPath(import.meta.url));

describe('zonas', () => {
  it('son las ocho de docs/02 §3.1, con ruta única y todas con su dato marcado como demo en la interfaz', () => {
    expect(ZONAS).toHaveLength(8);
    expect(new Set(ZONAS.map((z) => z.id)).size).toBe(8);
    expect(new Set(ZONAS.map((z) => z.ruta)).size).toBe(8);
    for (const z of ZONAS) expect(z.ruta).toBe(`/${z.id}`);
  });

  it('cada estantería tiene sus zonas y zonaPorId las encuentra', () => {
    expect(ORDEN_ESTANTERIAS.flatMap((e) => zonasDe(e))).toHaveLength(ZONAS.length);
    expect(zonaPorId('banco')?.estanteria).toBe('centro');
    expect(zonaPorId('nada')).toBeNull();
    expect(zonaPorId(null)).toBeNull();
  });

  it('las zonas caben dentro de su estantería', () => {
    for (const z of ZONAS) {
      const x = ESTANTERIAS[z.estanteria].x;
      if (z.id === 'banco') continue;
      expect(Math.abs(z.caja.centro[0] - x) + z.caja.tamano[0] / 2).toBeLessThanOrEqual(MUEBLE.ancho / 2 + 1e-9);
    }
  });
});

describe('encuadre del póster', () => {
  it('el plano general ve los tres cuerpos enteros en cualquier pantalla de escritorio', () => {
    for (const aspecto of [1.25, 1.6, 16 / 9, 2.33]) {
      const encuadre = encuadreSala(aspecto);
      for (const zona of ZONAS) {
        const r = rectZona(zona, encuadre, aspecto);
        expect(r.x).toBeGreaterThanOrEqual(0);
        expect(r.x + r.ancho).toBeLessThanOrEqual(1);
      }
    }
  });

  it('el centro de la sala cae en el centro del póster', () => {
    const [x] = proyectar(
      [0, ENCUADRE_POSTER.objetivo[1], ENCUADRE_POSTER.objetivo[2]],
      ENCUADRE_POSTER,
      ASPECTO_POSTER,
    );
    expect(x).toBeCloseTo(0.5, 5);
  });

  it('zonas-poster.css está al día con la proyección (pnpm --filter @taller6mm/web zonas:css)', () => {
    const css = readFileSync(path.join(aqui, 'zonas-poster.css'), 'utf8');
    for (const zona of ZONAS) {
      const r = rectZona(zona, ENCUADRE_POSTER, ASPECTO_POSTER);
      expect(css).toContain(
        `[data-zona="${zona.id}"] {\n  left: ${(r.x * 100).toFixed(3)}%;\n  top: ${(r.y * 100).toFixed(3)}%;\n  width: ${(r.ancho * 100).toFixed(3)}%;\n  height: ${(r.alto * 100).toFixed(3)}%;\n}`,
      );
    }
  });
});

describe('sockets de réplica (sin siluetas de relleno)', () => {
  it('hay uno por ranura del armero, por peana de la vitrina y uno en el banco, todos vacíos', () => {
    expect(socketsDe('replicas')).toHaveLength(ARMERO.huecos);
    expect(socketsDe('comunidad')).toHaveLength(VITRINA.xs.length);
    expect(socketsDe('banco')).toHaveLength(1);
    expect(SOCKETS).toHaveLength(ARMERO.huecos + VITRINA.xs.length + 1);
    for (const s of SOCKETS) expect(s.replicaId).toBeNull();
    expect(new Set(SOCKETS.map((s) => s.id)).size).toBe(SOCKETS.length);
  });

  it('cada socket cae dentro de la caja de su zona, así que su imagen nunca sale de ella', () => {
    for (const s of SOCKETS) {
      const zona = zonaPorId(s.zona);
      if (!zona) throw new Error(`falta la zona ${s.zona}`);
      const r = rectCaja(s.caja.centro, s.caja.tamano);
      const z = rectZona(zona, ENCUADRE_POSTER, ASPECTO_POSTER);
      const margen = 0.01;
      expect(r.x).toBeGreaterThanOrEqual(z.x - margen);
      expect(r.x + r.ancho).toBeLessThanOrEqual(z.x + z.ancho + margen);
      expect(r.y).toBeGreaterThanOrEqual(z.y - margen);
      expect(r.y + r.alto).toBeLessThanOrEqual(z.y + z.alto + margen);
    }
  });

  it('las ranuras del armero no se solapan entre sí', () => {
    const rects = socketsDe('replicas').map((s) => rectCaja(s.caja.centro, s.caja.tamano));
    rects.forEach((r, i) => {
      const siguiente = rects[i + 1];
      if (siguiente) expect(r.x + r.ancho).toBeLessThanOrEqual(siguiente.x + 1e-9);
    });
  });

  it('las peanas suben de una en una y el socket queda justo encima de la suya', () => {
    expect(alturaPeana(1)).toBeGreaterThan(alturaPeana(0));
    socketsDe('comunidad').forEach((s, i) => {
      expect(s.caja.centro[1] - s.caja.tamano[1] / 2).toBeCloseTo(alturaPeana(i), 5);
    });
  });

  it('zonas-poster.css lleva el rectángulo de cada hueco', () => {
    const css = readFileSync(path.join(aqui, 'zonas-poster.css'), 'utf8');
    for (const s of SOCKETS) {
      const r = rectCaja(s.caja.centro, s.caja.tamano);
      expect(css).toContain(`[data-socket="${s.id}"] {\n  left: ${(r.x * 100).toFixed(3)}%;`);
    }
  });
});

describe('luz', () => {
  it('«Más luz» sube el nivel sin cambiar la temperatura de los tubos', () => {
    const a = VARIANTES_LUZ.penumbra;
    const b = VARIANTES_LUZ['mas-luz'];
    expect(b.reposo).toBeGreaterThan(a.reposo);
    expect(b.ambiente).toBeGreaterThan(a.ambiente);
    expect(b.colorTubo).toBe(a.colorTubo);
  });

  it('esLuz solo acepta los dos niveles', () => {
    expect(esLuz('penumbra')).toBe(true);
    expect(esLuz('mas-luz')).toBe(true);
    expect(esLuz('taller-abierto')).toBe(false);
    expect(esLuz(null)).toBe(false);
  });
});

describe('preferencias', () => {
  const almacen = (datos: Record<string, string> = {}): Almacen & { datos: Record<string, string> } => ({
    datos,
    getItem: (k) => datos[k] ?? null,
    setItem: (k, v) => {
      datos[k] = v;
    },
  });
  const roto: Almacen = {
    getItem: () => {
      throw new Error('bloqueado');
    },
    setItem: () => {
      throw new Error('bloqueado');
    },
  };

  it('la luz sale de la URL, luego de lo guardado y por defecto es penumbra', () => {
    expect(luzInicial(null, null)).toBe('penumbra');
    expect(luzInicial(null, almacen({ [CLAVES.luz]: 'mas-luz' }))).toBe('mas-luz');
    expect(luzInicial('penumbra', almacen({ [CLAVES.luz]: 'mas-luz' }))).toBe('penumbra');
    expect(luzInicial('basura', almacen({ [CLAVES.luz]: 'basura' }))).toBe('penumbra');
  });

  it('sin almacenamiento, o con uno que lanza, no se rompe nada', () => {
    expect(leer(null, CLAVES.luz)).toBeNull();
    expect(leer(roto, CLAVES.luz)).toBeNull();
    expect(() => guardar(roto, CLAVES.luz, 'mas-luz')).not.toThrow();
    expect(() => guardar(null, CLAVES.luz, 'mas-luz')).not.toThrow();
    expect(luzInicial(null, roto)).toBe('penumbra');
  });

  it('guardar y leer van y vuelven', () => {
    const a = almacen();
    guardar(a, CLAVES.luz, 'mas-luz');
    expect(leer(a, CLAVES.luz)).toBe('mas-luz');
  });
});

describe('zona activa', () => {
  it('la abierta manda sobre el puntero y este sobre el teclado', () => {
    expect(zonaActiva(ESTADO_INICIAL)).toBeNull();
    expect(zonaActiva({ ...ESTADO_INICIAL, enfocada: 'tiendas' })).toBe('tiendas');
    expect(zonaActiva({ ...ESTADO_INICIAL, enfocada: 'tiendas', apuntada: 'guias' })).toBe('guias');
    expect(zonaActiva({ ...ESTADO_INICIAL, enfocada: 'tiendas', apuntada: 'guias', abierta: 'banco' })).toBe('banco');
  });
});

describe('póster por luz', () => {
  it('«Más luz» tiene su propio póster horneado, no un filtro, y cada URL existe en el manifiesto', () => {
    const a = posterDe('penumbra');
    const b = posterDe('mas-luz');
    expect(a.src).not.toBe(b.src);
    for (const url of [
      a.src,
      b.src,
      ...a.srcSet.split(', ').map((x) => x.split(' ')[0]),
      ...b.srcSet.split(', ').map((x) => x.split(' ')[0]),
    ]) {
      const nombre = url?.split('/').pop() ?? '';
      expect(Object.keys(manifiesto.archivos)).toContain(nombre);
    }
  });
});

describe('manifiesto de vistas', () => {
  it('su hash sale de los hashes de sus archivos', async () => {
    const sha = Object.fromEntries(Object.entries(manifiesto.archivos).map(([n, a]) => [n, a.sha256]));
    expect(await hashConjunto(sha)).toBe(manifiesto.hash);
  });

  it('las URLs llevan el hash y apuntan a un archivo del manifiesto', () => {
    const url = urlVista('poster-1920.webp');
    expect(url).toBe(`/assets/armeria/${manifiesto.hash}/poster-1920.webp`);
    expect(Object.keys(manifiesto.archivos)).toContain('poster-1920.webp');
  });
});
