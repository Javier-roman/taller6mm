// Encuadre del póster de La Armería, en TS puro (sin three.js ni DOM): el póster, el nivel B y las zonas
// HTML usan la misma proyección para que todo caiga en el mismo sitio. El nivel A tiene su propia cámara
// (3D), pero parte de este mismo encuadre general para que el fundido no mueva nada.
import { MUEBLE, type Zona } from './zonas.ts';

export type V3 = readonly [number, number, number];

export interface Encuadre {
  readonly posicion: V3;
  readonly objetivo: V3;
  /** Campo de visión vertical en grados. */
  readonly fov: number;
}

export interface Rect {
  readonly x: number;
  readonly y: number;
  readonly ancho: number;
  readonly alto: number;
}

export const FOV = 42;
/** Aspecto del póster y de los pases del nivel B (16:9). */
export const ASPECTO_POSTER = 16 / 9;
/** Mitad del ancho que se ve en el póster: los tres cuerpos (±4,13 m) y aire alrededor. */
const MEDIO_ANCHO_POSTER = 4.75;
/** Mitad del ancho que debe verse siempre: los tres cuerpos y un margen mínimo. */
const MEDIO_ANCHO_MINIMO = 4.3;
/**
 * Fracción del ancho del póster que se ve siempre: en pantallas más estrechas que 16:9 la imagen no se
 * recorta más que esto y sobra arriba y abajo, donde van la cabecera y la navegación. El mismo valor está
 * en armeria.css (`.armeria-poster__lienzo`).
 */
export const ANCHO_MINIMO_VISIBLE = MEDIO_ANCHO_MINIMO / MEDIO_ANCHO_POSTER;
/** Cámara a la altura de los ojos de alguien de pie, con un picado de unos 7°. */
const ALTURA_CAMARA = 2.05;
// Objetivo alto: los tubos quedan bajo la cabecera y se ve de dónde nacen (critico-diseno, 05-11-2026).
const OBJETIVO_SALA: V3 = [0, 1.52, MUEBLE.frente];

const tanMedio = (fov: number) => Math.tan((fov * Math.PI) / 360);
const DISTANCIA_POSTER = MEDIO_ANCHO_POSTER / (tanMedio(FOV) * ASPECTO_POSTER);

/**
 * Plano general de la sala para un aspecto dado. Más ancho que 16:9 cierra el campo vertical (como
 * `object-fit: cover`); más estrecho, mantiene la cámara del póster mientras quepan los tres cuerpos y,
 * si no caben, retrocede.
 */
export function encuadreSala(aspecto: number): Encuadre {
  if (aspecto >= ASPECTO_POSTER) {
    const fov = (2 * Math.atan((tanMedio(FOV) * ASPECTO_POSTER) / aspecto) * 180) / Math.PI;
    return { posicion: [0, ALTURA_CAMARA, OBJETIVO_SALA[2] + DISTANCIA_POSTER], objetivo: OBJETIVO_SALA, fov };
  }
  const d = Math.max(DISTANCIA_POSTER, MEDIO_ANCHO_MINIMO / (tanMedio(FOV) * aspecto));
  return { posicion: [0, ALTURA_CAMARA, OBJETIVO_SALA[2] + d], objetivo: OBJETIVO_SALA, fov: FOV };
}

/** El póster y los pases del nivel B se renderizan con este encuadre fijo (16:9). */
export const ENCUADRE_POSTER = encuadreSala(ASPECTO_POSTER);

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

/** Tubo de una estantería (centro en `x`) proyectado sobre el póster: [x0, y0, x1, y1] en uv, para su resplandor. */
export function segmentoTubo(x: number): readonly [number, number, number, number] {
  const a = proyectar([x - 1.1, 3.42, -1.05], ENCUADRE_POSTER, ASPECTO_POSTER);
  const b = proyectar([x + 1.1, 3.42, -1.05], ENCUADRE_POSTER, ASPECTO_POSTER);
  return [a[0], a[1], b[0], b[1]];
}
