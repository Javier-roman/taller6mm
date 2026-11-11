// Tests de la lógica pura de La Armería (prototipos de la Fase 1): seguridad ante destellos del
// director de luces (WCAG 2.3.1), proyección del póster y CSS de zonas generado.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import {
  ASPECTO_POSTER,
  anchoVisibleMovil,
  ENCUADRE_POSTER,
  encuadreSala,
  encuadreZona,
  MOVIL_REFERENCIA,
  proyectar,
  recorteMovil,
  rectZona,
  TABLERO_EN_MOVIL,
} from './camara.ts';
import { crearCanal } from './canal.ts';
import { Director, INTRO, VARIANTES } from './director.ts';
import { CONJUNTOS_MOVIL, conjuntoDe, recorteConjunto } from './recortes.ts';
import { type Estanteria, ORDEN_ESTANTERIAS, ZONA_INICIAL, ZONAS } from './zonas.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const DT = 1 / 120;

/**
 * Cuenta destellos como WCAG: un destello es un par de cambios opuestos de luminancia de al menos un
 * 10 %. Se mira la suma de los tubos (la luz de la sala) y se cuentan los cambios de sentido.
 */
function maxDestellosPorSegundo(serie: number[]) {
  const giros: number[] = [];
  let extremo = serie[0] ?? 0;
  let sentido = 0;
  serie.forEach((v, i) => {
    const delta = v - extremo;
    if (sentido >= 0 && delta < -0.1 * Math.max(extremo, 0.05)) {
      if (sentido > 0) giros.push(i);
      sentido = -1;
      extremo = v;
    } else if (sentido <= 0 && delta > 0.1 * Math.max(extremo, 0.05)) {
      if (sentido < 0) giros.push(i);
      sentido = 1;
      extremo = v;
    } else if ((sentido > 0 && v > extremo) || (sentido < 0 && v < extremo)) {
      extremo = v;
    }
  });
  const ventana = Math.round(1 / DT);
  let max = 0;
  for (const inicio of giros) {
    const dentro = giros.filter((g) => g >= inicio && g < inicio + ventana).length;
    max = Math.max(max, dentro / 2);
  }
  return max;
}

const luzSala = (d: Director) => ORDEN_ESTANTERIAS.reduce((s, e) => s + d.luz.tubos[e], 0);

describe('director de luces', () => {
  it('la intro dura como mucho 3 s y no pasa de 3 destellos por segundo', () => {
    const d = new Director({ intro: true, reducido: false, variante: 'penumbra' });
    const serie: number[] = [];
    const porTubo: Record<Estanteria, number[]> = { izquierda: [], centro: [], derecha: [] };
    for (let t = 0; t < 3.2; t += DT) {
      d.actualizar(DT, { estanteriaActiva: null, zonaActiva: false, linterna: false });
      serie.push(luzSala(d));
      for (const e of ORDEN_ESTANTERIAS) porTubo[e].push(d.luz.tubos[e]);
    }
    expect(INTRO.fin).toBeLessThanOrEqual(3);
    expect(d.enIntro).toBe(false);
    expect(maxDestellosPorSegundo(serie)).toBeLessThanOrEqual(3);
    for (const e of ORDEN_ESTANTERIAS) expect(maxDestellosPorSegundo(porTubo[e])).toBeLessThanOrEqual(3);
  });

  it('pasar el ratón muy deprisa por las estanterías no provoca más de 3 destellos por segundo', () => {
    const d = new Director({ intro: false, reducido: false, variante: 'penumbra' });
    const serie: number[] = [];
    const porTubo: Record<Estanteria, number[]> = { izquierda: [], centro: [], derecha: [] };
    for (let i = 0; i < 6 / DT; i++) {
      // Cambia de estantería cada 0,15 s: el peor caso de un ratón nervioso.
      const activa = ORDEN_ESTANTERIAS[Math.floor((i * DT) / 0.15) % 3] ?? null;
      d.actualizar(DT, { estanteriaActiva: activa, zonaActiva: true, linterna: true });
      serie.push(luzSala(d));
      for (const e of ORDEN_ESTANTERIAS) porTubo[e].push(d.luz.tubos[e]);
    }
    for (const e of ORDEN_ESTANTERIAS) expect(maxDestellosPorSegundo(porTubo[e])).toBeLessThanOrEqual(3);
    expect(maxDestellosPorSegundo(serie)).toBeLessThanOrEqual(3);
  });

  it('con movimiento reducido no hay intro ni parpadeos: la sala arranca en reposo', () => {
    const d = new Director({ intro: true, reducido: true, variante: 'penumbra' });
    expect(d.enIntro).toBe(false);
    d.actualizar(DT, { estanteriaActiva: 'centro', zonaActiva: true, linterna: false });
    expect(d.luz.tubos.centro).toBeGreaterThan(VARIANTES.penumbra.reposo);
    const antes = d.luz.tubos.centro;
    d.actualizar(0.05, { estanteriaActiva: 'centro', zonaActiva: true, linterna: false });
    expect(d.luz.tubos.centro).toBeGreaterThanOrEqual(antes);
  });

  it('se puede saltar la intro (Esc, clic o «Saltar»)', () => {
    const d = new Director({ intro: true, reducido: false, variante: 'penumbra' });
    d.actualizar(0.5, { estanteriaActiva: null, zonaActiva: false, linterna: false });
    expect(d.enIntro).toBe(true);
    d.saltarIntro();
    expect(d.enIntro).toBe(false);
    expect(d.progresoIntro).toBe(1);
  });
});

describe('módulo por defecto', () => {
  it('la escena arranca en el banco sin esperar al carrusel (también con movimiento reducido)', () => {
    expect(ZONA_INICIAL).toBe('banco');
    expect(ZONAS[crearCanal().progreso]?.id).toBe('banco');
  });
});

describe('encuadres', () => {
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

  it('en móvil el tablero del banco cae en el tercio inferior, sin franja vacía debajo', () => {
    const banco = ZONAS.find((z) => z.id === 'banco');
    if (!banco) throw new Error('falta la zona banco');
    for (const aspecto of [390 / 844, 375 / 667, 430 / 932]) {
      const e = encuadreZona(banco, aspecto, 0, anchoVisibleMovil(banco));
      const [, y] = proyectar([banco.caja.centro[0], 0.95, banco.caja.centro[2]], e, aspecto);
      expect(y).toBeCloseTo(TABLERO_EN_MOVIL, 2);
    }
  });

  it('el recorte de cada módulo para el móvil lo contiene con su aire y da 1 px de pase por px físico', () => {
    const { ancho, densidad, aire } = MOVIL_REFERENCIA;
    for (const zona of ZONAS) {
      const r = rectZona(zona, ENCUADRE_POSTER, ASPECTO_POSTER);
      const c = recorteMovil(zona);
      expect(c.x).toBeGreaterThanOrEqual(0);
      expect(c.y).toBeGreaterThanOrEqual(0);
      expect(c.x + c.ancho).toBeLessThanOrEqual(1 + 1e-9);
      expect(c.y + c.alto).toBeLessThanOrEqual(1 + 1e-9);
      // El módulo cabe entero, con al menos `aire` px CSS a cada lado.
      const pxPorUv = ancho / c.ancho;
      expect((r.x - c.x) * pxPorUv).toBeGreaterThanOrEqual(aire - 1e-6);
      expect((c.x + c.ancho - r.x - r.ancho) * pxPorUv).toBeGreaterThanOrEqual(aire - 1e-6);
      // Ancho útil: al menos 390 × 3 px (critico-diseno) y nunca ampliado en el móvil de referencia.
      expect(c.px[0]).toBeGreaterThanOrEqual(1170);
      expect(c.px[0]).toBe(ancho * densidad);
    }
  });

  it('cada zona tiene su conjunto de recortes, que cubre su ventana y cabe en una textura de móvil', () => {
    for (const zona of ZONAS) {
      const conjunto = conjuntoDe(zona.id);
      if (!conjunto) throw new Error(`la zona ${zona.id} no está en ningún conjunto`);
      expect(conjunto.fila).toBe(zona.estanteria);
      const c = recorteConjunto(conjunto);
      const r = recorteMovil(zona);
      expect(c.x).toBeLessThanOrEqual(r.x + 1e-9);
      expect(c.y).toBeLessThanOrEqual(r.y + 1e-9);
      expect(c.x + c.ancho).toBeGreaterThanOrEqual(r.x + r.ancho - 1e-9);
      expect(c.y + c.alto).toBeGreaterThanOrEqual(r.y + r.alto - 1e-9);
      // Nunca ampliado: al menos tantos píxeles de pase por uv como pide la zona.
      expect(c.px[0] / c.ancho).toBeGreaterThanOrEqual(r.px[0] / r.ancho - 1e-6);
    }
    // 4096 px es el tamaño máximo de textura que garantizan los móviles.
    for (const conjunto of CONJUNTOS_MOVIL) {
      const [ancho, alto] = recorteConjunto(conjunto).px;
      expect(Math.max(ancho, alto)).toBeLessThanOrEqual(4096);
    }
  });

  it('zonas-poster.css está al día con la proyección (scripts/prototipos/zonas-poster.mjs)', () => {
    const css = readFileSync(path.join(here, 'zonas-poster.css'), 'utf8');
    for (const zona of ZONAS) {
      const r = rectZona(zona, ENCUADRE_POSTER, ASPECTO_POSTER);
      expect(css).toContain(`[data-zona="${zona.id}"] {\n  left: ${(r.x * 100).toFixed(3)}%;`);
      expect(css).toContain(`[data-zona="${zona.id}"] {\n  --zona-ancho: ${Number(r.ancho.toFixed(5))};`);
    }
  });
});
