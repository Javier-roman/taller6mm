// Contenido de EJEMPLO de las hojas de los ocho módulos de La Armería (Fase 1, rebanada S2).
// Todo lo de este archivo es `is_demo: true`: no hay catálogo, ni tiendas, ni comunidad hasta las Fases 2 a 5
// (docs/10), y la interfaz lo dice con la marca «Demo». Reglas que se cumplen aquí (principios 1 y 2):
//  - Todo precio lleva la fecha de su comprobación en ISO UTC (o `null` + bandera: «Sin fecha de comprobación»).
//  - Dinero en céntimos enteros; longitudes en mm; sin estadísticas de videojuego.
//  - Las tiendas se llaman «de ejemplo»: ningún precio de aquí es de una tienda real.
//  - Las réplicas del armero NO se inventan: 0 publicadas y huecos (`sockets.ts`) listos para las reales.
// Lógica pura, sin React ni DOM: se prueba en contenido-demo.test.ts.

/** Cuándo se «comprobó» cada dato de ejemplo (el día de esta rebanada). */
export const COMPROBADO_DEMO = '2026-11-26T18:40:00Z';
export const COMPROBADO_DEMO_ANTIGUO = '2026-11-24T09:10:00Z';

export interface MarcaDemo {
  readonly is_demo: true;
}

/** Línea de resumen de cada hoja: un dato y la fecha en que se comprobó (`null` = nunca se comprobó). */
export interface ResumenDemo {
  readonly texto: string;
  /**
   * Cuándo se comprobó; `null` = nunca se comprobó. `undefined` = el dato es un estado (sin sesión, sin build) y no
   * caduca ni se comprueba: no lleva fecha, para no inventarla.
   */
  readonly comprobado?: string | null;
  /** `true` = dato de ejemplo (lleva la marca «Demo»); `false` = hecho real de este momento (0 réplicas, sin sesión). */
  readonly is_demo: boolean;
}

// ── Armero ───────────────────────────────────────────────────────────────────────────────────────
export interface FamiliaPrevista extends MarcaDemo {
  readonly id: string;
  readonly nombre: string;
  readonly tipo: string;
}

/** Las cuatro familias con las que arrancará el catálogo (alcance acordado): sin ficha publicada todavía. */
export const FAMILIAS_PREVISTAS: readonly FamiliaPrevista[] = [
  { id: 'hi-capa', nombre: 'Hi-Capa', tipo: 'Pistola', is_demo: true },
  { id: 'glock', nombre: 'Glock', tipo: 'Pistola', is_demo: true },
  { id: 'm4', nombre: 'M4', tipo: 'Rifle AEG', is_demo: true },
  { id: 'ak', nombre: 'AK', tipo: 'Rifle AEG', is_demo: true },
];

// ── Accesorios ───────────────────────────────────────────────────────────────────────────────────
export interface AccesorioDemo extends MarcaDemo {
  readonly id: string;
  readonly nombre: string;
  readonly categoria: string;
  /** Mejor precio en céntimos; `null` si ninguna tienda lo publica. */
  readonly centimos: number | null;
  readonly comprobado: string | null;
  readonly tiendas: number | null;
  /** Envolvente en mm para el plano T0; `null` si se desconoce. */
  readonly medidas: { readonly largoMm: number | null; readonly diametroMm: number | null };
}

export const ACCESORIOS_TOTAL = 186;
export const TIENDAS_TOTAL = 8;

export const ACCESORIOS_MUESTRA: readonly AccesorioDemo[] = [
  {
    id: 'canon-363',
    nombre: 'Cañón de precisión 6,03 × 363 mm',
    categoria: 'Cañones internos',
    centimos: 2495,
    comprobado: COMPROBADO_DEMO,
    tiendas: 6,
    medidas: { largoMm: 363, diametroMm: 6 },
    is_demo: true,
  },
  {
    id: 'silenciador-230',
    nombre: 'Silenciador 230 mm, rosca 14 mm CCW',
    categoria: 'Bocachas y silenciadores',
    centimos: 3990,
    comprobado: COMPROBADO_DEMO_ANTIGUO,
    tiendas: 3,
    medidas: { largoMm: 230, diametroMm: 35 },
    is_demo: true,
  },
];

// ── Vitrina de la comunidad ──────────────────────────────────────────────────────────────────────
export interface BuildDemo extends MarcaDemo {
  readonly id: string;
  readonly nombre: string;
  readonly autor: string;
  readonly base: string;
  readonly piezas: number;
  /** Precio total de las piezas en céntimos y fecha del precio más antiguo de la build. */
  readonly centimos: number;
  readonly comprobado: string;
  readonly nota: number;
  readonly opiniones: number;
}

export const BUILDS_TOP: readonly BuildDemo[] = [
  {
    id: 'cqb-ligera',
    nombre: 'CQB ligera para interior',
    autor: 'usuario-demo-1',
    base: 'M4',
    piezas: 14,
    centimos: 48750,
    comprobado: COMPROBADO_DEMO,
    nota: 4.6,
    opiniones: 38,
    is_demo: true,
  },
  {
    id: 'pistola-competicion',
    nombre: 'Pistola de competición',
    autor: 'usuario-demo-2',
    base: 'Hi-Capa',
    piezas: 11,
    centimos: 31200,
    comprobado: COMPROBADO_DEMO_ANTIGUO,
    nota: 4.4,
    opiniones: 21,
    is_demo: true,
  },
  {
    id: 'ak-de-campo',
    nombre: 'AK de campo, acabado FDE',
    autor: 'usuario-demo-3',
    base: 'AK',
    piezas: 16,
    centimos: 52995,
    comprobado: COMPROBADO_DEMO,
    nota: 4.1,
    opiniones: 17,
    is_demo: true,
  },
];

// ── Banco de trabajo ─────────────────────────────────────────────────────────────────────────────
export interface RanuraDemo extends MarcaDemo {
  readonly id: string;
  readonly nombre: string;
}

/** Las ranuras de una réplica larga: cada una se rellena con una pieza compatible (docs/03). */
export const RANURAS_BANCO: readonly RanuraDemo[] = [
  { id: 'cuerpo', nombre: 'Cuerpo y réplica base', is_demo: true },
  { id: 'canon', nombre: 'Cañón interno', is_demo: true },
  { id: 'bocacha', nombre: 'Bocacha', is_demo: true },
  { id: 'cargador', nombre: 'Cargador', is_demo: true },
  { id: 'optica', nombre: 'Óptica', is_demo: true },
  { id: 'culata', nombre: 'Culata', is_demo: true },
];

/** Veredicto de ejemplo con motivo, fuente y confianza (principio 3). Es el ejemplo de docs/02 §4.7. */
export const COMPATIBILIDAD_EJEMPLO = {
  veredicto: 'adaptador',
  motivo:
    'Esta bocacha es de rosca a derechas (CW) y tu réplica es a izquierdas (CCW). Necesitas un adaptador: 3 tiendas desde 8,95 €.',
  fuente: { nombre: 'Ficha del fabricante (ejemplo)' },
  confianza: 'alta',
  is_demo: true,
} as const;

// ── Tablón de mercado ────────────────────────────────────────────────────────────────────────────
export interface BajadaDemo extends MarcaDemo {
  readonly id: string;
  readonly pieza: string;
  readonly tienda: string;
  /** Precio anterior y actual, en céntimos. */
  readonly antes: number;
  readonly ahora: number;
  readonly comprobado: string;
  readonly stock: 'en-stock' | 'pocas' | 'agotado' | 'desconocido';
}

export const BAJADAS: readonly BajadaDemo[] = [
  {
    id: 'b1',
    pieza: 'Cañón de precisión 6,03 × 363 mm',
    tienda: 'Tienda de ejemplo 2',
    antes: 2995,
    ahora: 2495,
    comprobado: COMPROBADO_DEMO,
    stock: 'en-stock',
    is_demo: true,
  },
  {
    id: 'b2',
    pieza: 'Maletín rígido 100 cm',
    tienda: 'Tienda de ejemplo 5',
    antes: 5990,
    ahora: 4990,
    comprobado: COMPROBADO_DEMO,
    stock: 'pocas',
    is_demo: true,
  },
  {
    id: 'b3',
    pieza: 'Cargador Hi-Capa 5.1, 30 bolas',
    tienda: 'Tienda de ejemplo 1',
    antes: 1695,
    ahora: 1395,
    comprobado: COMPROBADO_DEMO_ANTIGUO,
    stock: 'desconocido',
    is_demo: true,
  },
];

/** Bajada en porcentaje entero (positivo = más barato). */
export const porcentajeBajada = (b: Pick<BajadaDemo, 'antes' | 'ahora'>): number =>
  Math.round(((b.antes - b.ahora) / b.antes) * 100);

// ── Mostrador de tiendas ─────────────────────────────────────────────────────────────────────────
export type FrescuraTienda = 'al-dia' | 'desfasada' | 'sin-comprobar';

export interface TiendaDemo extends MarcaDemo {
  readonly id: string;
  readonly nombre: string;
  readonly pais: string;
  /** Cómo se leen sus datos: primero feeds y APIs oficiales (principio 4). */
  readonly via: 'Feed' | 'API' | 'Páginas públicas';
  readonly comprobado: string | null;
}

export const TIENDAS: readonly TiendaDemo[] = [
  { id: 't1', nombre: 'Tienda de ejemplo 1', pais: 'España', via: 'Feed', comprobado: COMPROBADO_DEMO, is_demo: true },
  { id: 't2', nombre: 'Tienda de ejemplo 2', pais: 'España', via: 'API', comprobado: COMPROBADO_DEMO, is_demo: true },
  { id: 't3', nombre: 'Tienda de ejemplo 3', pais: 'España', via: 'Feed', comprobado: COMPROBADO_DEMO, is_demo: true },
  {
    id: 't4',
    nombre: 'Tienda de ejemplo 4',
    pais: 'Alemania',
    via: 'Páginas públicas',
    comprobado: COMPROBADO_DEMO_ANTIGUO,
    is_demo: true,
  },
  { id: 't5', nombre: 'Tienda de ejemplo 5', pais: 'Francia', via: 'API', comprobado: COMPROBADO_DEMO, is_demo: true },
  {
    id: 't6',
    nombre: 'Tienda de ejemplo 6',
    pais: 'Reino Unido',
    via: 'Páginas públicas',
    comprobado: COMPROBADO_DEMO_ANTIGUO,
    is_demo: true,
  },
  { id: 't7', nombre: 'Tienda de ejemplo 7', pais: 'Italia', via: 'Feed', comprobado: COMPROBADO_DEMO, is_demo: true },
  { id: 't8', nombre: 'Tienda de ejemplo 8', pais: 'Portugal', via: 'API', comprobado: null, is_demo: true },
];

/** Una tienda está «al día» si se comprobó en las últimas 24 h respecto a la fecha de referencia. */
export function frescura(comprobado: string | null, referencia: string = COMPROBADO_DEMO): FrescuraTienda {
  if (comprobado === null) return 'sin-comprobar';
  const edad = Date.parse(referencia) - Date.parse(comprobado);
  return Number.isNaN(edad) ? 'sin-comprobar' : edad <= 24 * 3_600_000 ? 'al-dia' : 'desfasada';
}

// ── Biblioteca de manuales ───────────────────────────────────────────────────────────────────────
export interface GuiaDemo extends MarcaDemo {
  readonly id: string;
  readonly titulo: string;
  readonly tema: string;
  readonly revisada: string;
}

export const GUIAS_TOTAL = 12;

export const GUIAS_MUESTRA: readonly GuiaDemo[] = [
  {
    id: 'g1',
    titulo: 'Rosca de bocacha: CW y CCW',
    tema: 'Compatibilidad',
    revisada: '2026-11-20T10:00:00Z',
    is_demo: true,
  },
  {
    id: 'g2',
    titulo: 'Despiece de un cargador de pistola',
    tema: 'Despieces',
    revisada: '2026-11-18T10:00:00Z',
    is_demo: true,
  },
  { id: 'g3', titulo: 'Cómo medir un cañón interno', tema: 'Medidas', revisada: '2026-11-15T10:00:00Z', is_demo: true },
  {
    id: 'g4',
    titulo: 'Normativa del airsoft en España: resumen',
    tema: 'Normativa',
    revisada: '2026-11-10T10:00:00Z',
    is_demo: true,
  },
];

// ── Taquilla personal ────────────────────────────────────────────────────────────────────────────
export const TAQUILLA_SIN_SESION = {
  sesion: false,
  builds: 0,
  favoritos: 0,
  alertas: 0,
  is_demo: true,
} as const;

// ── Resúmenes de cada hoja (dato fechado) ────────────────────────────────────────────────────────
export const RESUMENES = {
  replicas: { texto: '0 réplicas publicadas · 12 ranuras libres', is_demo: false },
  accesorios: {
    texto: `${ACCESORIOS_TOTAL} accesorios · ${TIENDAS_TOTAL} tiendas`,
    comprobado: COMPROBADO_DEMO,
    is_demo: true,
  },
  comunidad: { texto: `Top de la semana: ${BUILDS_TOP.length} builds`, comprobado: COMPROBADO_DEMO, is_demo: true },
  banco: { texto: 'Sin build en curso', is_demo: false },
  mercado: { texto: `${BAJADAS.length} bajadas de precio`, comprobado: COMPROBADO_DEMO, is_demo: true },
  tiendas: { texto: `${TIENDAS.length} tiendas seguidas`, comprobado: COMPROBADO_DEMO, is_demo: true },
  guias: { texto: `${GUIAS_TOTAL} guías`, comprobado: COMPROBADO_DEMO, is_demo: true },
  taquilla: { texto: 'Sin sesión iniciada', is_demo: false },
} as const satisfies Readonly<Record<string, ResumenDemo>>;

/** Resumen de una zona por id (`undefined` si no existe). */
export const resumenDe = (id: string): ResumenDemo | undefined =>
  (RESUMENES as Readonly<Record<string, ResumenDemo>>)[id];
