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
/** Aspecto del póster y de los pases del B (16:9). */
export const ASPECTO_POSTER = 16 / 9;
/** Mitad del ancho que se ve en el póster: los tres cuerpos (±4,13 m) y aire alrededor. */
const MEDIO_ANCHO_POSTER = 4.75;
/** Mitad del ancho que debe verse siempre en escritorio: los tres cuerpos y un margen mínimo. */
const MEDIO_ANCHO_MINIMO = 4.3;
/**
 * Fracción del ancho del póster (y de los pases del B) que se ve siempre fuera del móvil: en pantallas
 * más estrechas que 16:9 (tableta 4:3) la imagen no se recorta más que esto; sobra arriba y abajo, donde
 * van la cabecera y la navegación. El mismo valor está en armeria.css (.armeria-poster__lienzo).
 */
export const ANCHO_MINIMO_VISIBLE = MEDIO_ANCHO_MINIMO / MEDIO_ANCHO_POSTER;
/** Cámara a la altura de los ojos de alguien de pie, con un picado de unos 7° (critico-diseno). */
const ALTURA_CAMARA = 2.05;
// Objetivo alto: los tubos quedan bajo la cabecera (y ≥ 104 px a 1440 × 900) y se ve de dónde nacen los haces
// (critico-diseno, 05-11-2026). Con 1,2 quedaban tapados por el degradado de la cabecera.
const OBJETIVO_SALA: V3 = [0, 1.52, MUEBLE.frente];

const tanMedio = (fov: number) => Math.tan((fov * Math.PI) / 360);
const DISTANCIA_POSTER = MEDIO_ANCHO_POSTER / (tanMedio(FOV) * ASPECTO_POSTER);

/**
 * Plano general de la sala para un aspecto dado. Recorta igual que el póster (como object-fit:
 * cover), para que el fundido del póster a la escena no mueva nada: más ancho que 16:9, cierra el
 * campo vertical; más estrecho, mantiene la cámara del póster mientras quepan los tres cuerpos y,
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

/** El póster y los pases del B se renderizan con este encuadre fijo (16:9). */
export const ENCUADRE_POSTER = encuadreSala(ASPECTO_POSTER);

/** Picado de la cámara sobre el tablero del banco al abrirlo: se ve el tapete, no las patas. */
const PICADO_BANCO = (25 * Math.PI) / 180;
/** Altura en pantalla (0 arriba, 1 abajo) del centro del tablero en móvil: justo encima del carrusel. */
export const TABLERO_EN_MOVIL = 0.74;

/**
 * Encuadre de una zona: de frente, con margen, desplazada `dz` si su cuerpo ha rodado. En móvil
 * (`anchoVisible`) se ve la zona entera con un poco de aire y asoman las vecinas (pasillo). El banco se
 * mira desde arriba, apuntando al tablero.
 */
export function encuadreZona(zona: Zona, aspecto: number, dz = 0, anchoVisible?: number, fov = FOV): Encuadre {
  const [x, y, z] = zona.caja.centro;
  const [ancho, alto, fondo] = zona.caja.tamano;
  const t = tanMedio(fov);
  if (zona.id === 'banco') {
    const tablero = 0.95;
    const d = anchoVisible ? Math.min(anchoVisible, 1.8) / 2 / (t * aspecto) : 2.3;
    const posicion: V3 = [x, tablero + d * Math.sin(PICADO_BANCO), z + d * Math.cos(PICADO_BANCO)];
    if (!anchoVisible) return { posicion, objetivo: [x, tablero, z], fov };
    // Móvil (retrato): mirando al centro del tablero, la mitad inferior se quedaba en las patas y el
    // suelo. Se sube el objetivo hasta que el tablero cae en el tercio inferior y la vitrina de detrás
    // llena el de arriba (petición de Javi, 04-11-2026).
    let bajo = 0;
    let alto = 3;
    for (let i = 0; i < 30; i++) {
      const medio = (bajo + alto) / 2;
      const y = proyectar([x, tablero, z], { posicion, objetivo: [x, tablero + medio, z], fov }, aspecto)[1];
      if (y < TABLERO_EN_MOVIL) bajo = medio;
      else alto = medio;
    }
    return { posicion, objetivo: [x, tablero + bajo, z], fov };
  }
  const d = anchoVisible
    ? anchoVisible / 2 / (t * aspecto)
    : Math.max((ancho / 2 + 0.45) / (t * aspecto), (alto / 2 + 0.35) / t);
  const frente = z + fondo / 2 + dz;
  return { posicion: [x, y + 0.06, frente + d], objetivo: [x, y - 0.04, z + dz], fov };
}

/** Ancho visible en móvil para una zona: entera y con aire, sin bajar de 1,6 m (pasillo). */
export const anchoVisibleMovil = (zona: Zona) => Math.max(1.6, zona.caja.tamano[0] + 0.15);

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

/**
 * Móvil de referencia de los recortes por módulo del B (critico-diseno, 2.ª revisión: el pase único de
 * 2560 px se veía borroso, ampliado ×2 en un móvil de 3×). Es el más ancho y el más alargado de los
 * habituales (430 × 956 px CSS a 3× = 1290 px físicos de ancho): los demás muestran el recorte reducido,
 * nunca ampliado. `aire` es el margen a cada lado del módulo y `centro`, la altura (0–1) de la pantalla
 * donde cae el centro del módulo: el hueco entre la cabecera y el carrusel.
 */
export const MOVIL_REFERENCIA = { ancho: 430, alto: 956, densidad: 3, aire: 16, centro: 0.52 } as const;

/** Altura (0–1) de la pantalla del móvil donde empieza el carrusel: la sala llega al menos hasta ahí. */
export const FONDO_MOVIL = 0.8;

const acotar = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

/**
 * Ventana del encuadre del póster (uv 0–1) que ve una pantalla de `ancho` × `alto` px CSS con una zona
 * centrada: la zona entera con su aire a los lados y su centro a la altura del hueco entre la cabecera y
 * el carrusel. Si la ventana es más alta que el encuadre (zonas anchas), se sale por arriba (detrás de la
 * cabecera) antes que dejar un hueco sobre el carrusel.
 */
export function ventanaZona(zona: Zona, ancho: number, alto: number, movil = MOVIL_REFERENCIA): Rect {
  const r = rectZona(zona, ENCUADRE_POSTER, ASPECTO_POSTER);
  const w = Math.min(1, (r.ancho * ancho) / (ancho - 2 * movil.aire));
  const x = acotar(r.x + r.ancho / 2 - w / 2, 0, 1 - w);
  const h = (w * ASPECTO_POSTER * alto) / ancho;
  const centrada = r.y + r.alto / 2 - movil.centro * h;
  // Una sola fórmula para los dos casos (ventana más baja o más alta que el encuadre): es la misma que usa
  // el póster del móvil en CSS (zonas-poster.css), que no puede bifurcar.
  const y = acotar(centrada, Math.min(0, 1 - h), Math.max(1 - h, Math.min(0, 1 - FONDO_MOVIL * h)));
  return { x, y, ancho: w, alto: h };
}

export interface RecorteMovil extends Rect {
  /** Tamaño del recorte horneado en píxeles: 1 píxel de pase por píxel físico del móvil de referencia. */
  readonly px: readonly [number, number];
}

/**
 * Lo que hay que hornear para una zona: su ventana en el móvil de referencia, recortada al encuadre.
 * Lo usan el horno (hornear-b-cycles.mjs --conjunto) y los conjuntos de recortes.ts.
 */
export function recorteMovil(zona: Zona, movil: typeof MOVIL_REFERENCIA = MOVIL_REFERENCIA): RecorteMovil {
  const v = ventanaZona(zona, movil.ancho, movil.alto, movil);
  const y = Math.max(0, v.y);
  const alto = Math.min(1, v.y + v.alto) - y;
  // Alto del encuadre entero, en px CSS, a la escala de este recorte.
  const altoMarco = movil.ancho / v.ancho / ASPECTO_POSTER;
  return {
    x: v.x,
    y,
    ancho: v.ancho,
    alto,
    px: [movil.ancho * movil.densidad, Math.round(alto * altoMarco * movil.densidad)],
  };
}

/** Tubo de una estantería (centro en `x`) proyectado sobre el póster: [x0, y0, x1, y1] en uv, para su resplandor. */
export function segmentoTubo(x: number): readonly [number, number, number, number] {
  const a = proyectar([x - 1.1, 3.42, -1.05], ENCUADRE_POSTER, ASPECTO_POSTER);
  const b = proyectar([x + 1.1, 3.42, -1.05], ENCUADRE_POSTER, ASPECTO_POSTER);
  return [a[0], a[1], b[0], b[1]];
}
