// Encuadres de La Armería, en TS puro (sin three.js): el prototipo A los usa para su cámara, el
// póster y el B los usan para colocar las zonas HTML encima de la imagen con la misma proyección.
import { MUEBLE, type Zona } from './zonas.ts';

export type V3 = readonly [number, number, number];

export interface Encuadre {
  readonly posicion: V3;
  readonly objetivo: V3;
  /** Campo de visión vertical en grados. */
  readonly fov: number;
}

export const FOV = 42;
/** Mitad del ancho que debe verse siempre en escritorio: los tres cuerpos (±4,13 m) y un margen. */
const MEDIO_ANCHO_SALA = 4.75;
const OBJETIVO_SALA: V3 = [0, 1.45, MUEBLE.frente];

const tanMedio = (fov: number) => Math.tan((fov * Math.PI) / 360);

/** Plano general de la sala para un aspecto dado (escritorio, póster y horneado del B). */
export function encuadreSala(aspecto: number, fov = FOV): Encuadre {
  const d = Math.max(6.75, MEDIO_ANCHO_SALA / (tanMedio(fov) * aspecto));
  return { posicion: [0, 1.62, OBJETIVO_SALA[2] + d], objetivo: OBJETIVO_SALA, fov };
}

/** El póster y los pases del B se renderizan con este encuadre fijo (16:9). */
export const ASPECTO_POSTER = 16 / 9;
export const ENCUADRE_POSTER = encuadreSala(ASPECTO_POSTER);

/**
 * Encuadre de una zona: de frente, con margen, desplazada `dz` si su cuerpo ha rodado. En móvil
 * (`anchoVisible`) no cabe la zona entera: se ve su parte central y asoman las vecinas (pasillo).
 */
export function encuadreZona(zona: Zona, aspecto: number, dz = 0, anchoVisible?: number, fov = FOV): Encuadre {
  const [x, y, z] = zona.caja.centro;
  const [ancho, alto, fondo] = zona.caja.tamano;
  const t = tanMedio(fov);
  const d = anchoVisible
    ? anchoVisible / 2 / (t * aspecto)
    : Math.max((ancho / 2 + 0.45) / (t * aspecto), (alto / 2 + 0.35) / t);
  const frente = z + fondo / 2 + dz;
  const elevacion = zona.id === 'banco' ? 0.95 : 0.06;
  return {
    posicion: [x, y + elevacion, frente + d],
    objetivo: [x, y - (zona.id === 'banco' ? 0.12 : 0.04), z + dz],
    fov,
  };
}

type M3 = [number, number, number];
const resta = (a: V3, b: V3): M3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const punto = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cruz = (a: V3, b: V3): M3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unidad = (a: V3): M3 => {
  const l = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};

/** Proyección perspectiva de un punto: [x, y] en 0–1 desde la esquina superior izquierda. */
export function proyectar(p: V3, encuadre: Encuadre, aspecto: number): [number, number] {
  const delante = unidad(resta(encuadre.objetivo, encuadre.posicion));
  const derecha = unidad(cruz(delante, [0, 1, 0]));
  const arriba = cruz(derecha, delante);
  const d = resta(p, encuadre.posicion);
  const profundidad = Math.max(1e-3, punto(d, delante));
  const t = tanMedio(encuadre.fov);
  const nx = punto(d, derecha) / (profundidad * t * aspecto);
  const ny = punto(d, arriba) / (profundidad * t);
  return [(nx + 1) / 2, (1 - ny) / 2];
}

export interface Rect {
  readonly x: number;
  readonly y: number;
  readonly ancho: number;
  readonly alto: number;
}

/** Rectángulo en pantalla (0–1) de la cara frontal de la caja de una zona. */
export function rectZona(zona: Zona, encuadre: Encuadre, aspecto: number): Rect {
  const [cx, cy, cz] = zona.caja.centro;
  const [w, h, f] = zona.caja.tamano;
  const esquinas: V3[] = [-1, 1].flatMap((sx) =>
    [-1, 1].map((sy) => [cx + (sx * w) / 2, cy + (sy * h) / 2, cz + f / 2] as V3),
  );
  const puntos = esquinas.map((p) => proyectar(p, encuadre, aspecto));
  const xs = puntos.map((p) => p[0]);
  const ys = puntos.map((p) => p[1]);
  const x = Math.min(...xs);
  const y = Math.min(...ys);
  return { x, y, ancho: Math.max(...xs) - x, alto: Math.max(...ys) - y };
}
