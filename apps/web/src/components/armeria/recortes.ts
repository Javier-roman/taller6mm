// Recortes del prototipo B para el móvil (critico-diseno, 2.ª revisión): el pase único de 2560 px se veía
// borroso, ampliado ×2 en un móvil de 3×. Cada conjunto es una ventana del encuadre del póster horneada
// aparte (hornear-b-cycles.mjs --conjunto) a 1 píxel de pase por píxel físico del móvil de referencia, con
// solo los pases de luz que se notan en esa ventana. TS puro: lo usan el horno, el compositor y los tests.
import { ASPECTO_POSTER, type RecorteMovil, recorteMovil } from './camara.ts';
import { RUTA_PASES } from './pases.ts';
import { type Estanteria, ZONAS, type Zona } from './zonas.ts';

/** Pases de un conjunto, en el orden de las unidades de textura del compositor. */
export const PASES_RECORTE = ['base', 'tubo', 'calidas', 'rotulos'] as const;
export type PaseRecorte = (typeof PASES_RECORTE)[number];

export interface ConjuntoMovil {
  readonly id: string;
  /** Zonas que se ven con este recorte (comparten textura: entre ellas el encuadre se desplaza). */
  readonly zonas: readonly string[];
  /** Fila de tubos que ilumina el conjunto: su pase es el «tubo» del recorte. */
  readonly fila: Estanteria;
  /** Sin flexo ni vitrina a la vista, el pase de cálidas no se hornea (textura negra). */
  readonly calidas: boolean;
}

export const CONJUNTOS_MOVIL: readonly ConjuntoMovil[] = [
  { id: 'izquierda', zonas: ['replicas', 'accesorios'], fila: 'izquierda', calidas: false },
  { id: 'vitrina', zonas: ['comunidad'], fila: 'centro', calidas: true },
  { id: 'banco', zonas: ['banco'], fila: 'centro', calidas: true },
  // La estantería derecha va en dos columnas: entera serían 10 megapíxeles por pase (122 MB de GPU).
  { id: 'derecha-tablon', zonas: ['mercado', 'guias'], fila: 'derecha', calidas: false },
  { id: 'derecha-tiendas', zonas: ['tiendas', 'taquilla'], fila: 'derecha', calidas: false },
];

export const conjuntoDe = (zona: string) => CONJUNTOS_MOVIL.find((c) => c.zonas.includes(zona)) ?? null;

/** Nombre del pase horneado (el de la sala entera) que hace de `pase` en un conjunto; null si no lleva. */
export function paseHorneado(conjunto: ConjuntoMovil, pase: PaseRecorte) {
  if (pase === 'tubo') return `tubo-${conjunto.fila}`;
  if (pase === 'calidas' && !conjunto.calidas) return null;
  return pase;
}

/** Variantes de cada pase, como un srcset: la entera (móvil de 3×) y la reducida a 2/3 (2× o menos). */
export const VARIANTES_RECORTE = [
  { sufijo: '-2x', escala: 2 / 3 },
  { sufijo: '', escala: 1 },
] as const;

export const rutaRecorte = (conjunto: ConjuntoMovil, pase: string, sufijo: string) =>
  `${RUTA_PASES}/movil/${conjunto.id}/${pase}${sufijo}.webp`;

const zonasDe = (conjunto: ConjuntoMovil) =>
  conjunto.zonas.map((id) => ZONAS.find((z) => z.id === id)).filter((z): z is Zona => Boolean(z));

/**
 * Ventana del encuadre (uv 0–1) que cubre el conjunto: la unión de lo que ve el móvil de referencia con
 * cada una de sus zonas centrada, a la escala de la zona más estrecha (ninguna se amplía).
 */
export function recorteConjunto(conjunto: ConjuntoMovil): RecorteMovil {
  const recortes = zonasDe(conjunto).map((z) => recorteMovil(z));
  const x = Math.min(...recortes.map((r) => r.x));
  const y = Math.min(...recortes.map((r) => r.y));
  const ancho = Math.max(...recortes.map((r) => r.x + r.ancho)) - x;
  const alto = Math.max(...recortes.map((r) => r.y + r.alto)) - y;
  // Píxeles de pase por unidad de uv horizontal.
  const escala = Math.max(...recortes.map((r) => r.px[0] / r.ancho));
  return { x, y, ancho, alto, px: [Math.ceil(ancho * escala), Math.ceil((alto * escala) / ASPECTO_POSTER)] };
}

/** Media query del móvil estrecho, donde valen los recortes: hasta el ancho del móvil de referencia. */
export const MEDIA_RECORTES = '(max-width: 26.875rem)';
/** El recorte se ve algo más ancho que la pantalla (lleva el aire de los lados): para elegir en el srcset. */
export const TAMANOS_RECORTE = '110vw';

/** Póster de un conjunto (su composición en reposo) en las variantes de su srcset. */
export function srcsetPoster(conjunto: ConjuntoMovil) {
  const [ancho] = recorteConjunto(conjunto).px;
  return VARIANTES_RECORTE.map(
    (v) => `/prototipos/armeria/movil/${conjunto.id}${v.sufijo}.webp ${Math.round(ancho * v.escala)}w`,
  ).join(', ');
}

/**
 * Fracción del ancho de un recorte que una pantalla puede ver de más por cada lado sin que se note: los
 * móviles más estrechos que el de referencia (su aire de 16 px pesa más) se asoman hasta un 0,8 %.
 * Pendiente: hornear los recortes con ese margen.
 */
export const MARGEN_RECORTE = 0.01;
