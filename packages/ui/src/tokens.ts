// Tokens de diseño de docs/02 §4: fuente única. De aquí salen las variables CSS (styles/tokens.css),
// el @theme de Tailwind v4 (styles/theme.css) y este export TS. Tras cambiar algo:
//   pnpm --filter @taller6mm/ui css
// Un test falla si los CSS generados no coinciden con este archivo.

export type ColorGroup = 'superficie' | 'texto' | 'acento' | 'estado';

interface ColorSpec {
  readonly hex: `#${string}`;
  readonly group: ColorGroup;
  /** Uso según docs/02 §4.1. */
  readonly use: string;
  /** Valor inicial de docs/02 si se corrigió (contraste AA). */
  readonly previous?: `#${string}`;
}

/** Colores con nombre de acabado (docs/02 §4.1). */
export const COLOR_TOKENS = {
  'negro-pavonado': { hex: '#0B0C0E', group: 'superficie', use: 'Fondo base' },
  carbon: { hex: '#121417', group: 'superficie', use: 'Superficies' },
  grafito: { hex: '#1C1F23', group: 'superficie', use: 'Paneles elevados' },
  acero: { hex: '#2A2F35', group: 'superficie', use: 'Bordes y divisores' },
  hueso: { hex: '#E8E4DC', group: 'texto', use: 'Texto principal' },
  niebla: { hex: '#9AA3AD', group: 'texto', use: 'Texto secundario' },
  laton: { hex: '#B8925A', group: 'acento', use: 'Acento principal (premium, clásico)' },
  'laton-claro': { hex: '#D9B77E', group: 'acento', use: 'Hover y realce del acento' },
  fde: { hex: '#A08A6A', group: 'acento', use: 'Acento secundario (Flat Dark Earth)' },
  'verde-ranger': { hex: '#4B5A3F', group: 'acento', use: 'Acento terciario (fondos y chapas)' },
  // #E4572E daba 4,49:1 sobre grafito (por debajo de AA para texto). Misma tinta, algo más de luz:
  // 4,65:1 en la peor superficie, así que ya puede ser texto en las tres (decisión de Javi, 31-10-2026).
  'naranja-senal': {
    hex: '#E75A31',
    group: 'acento',
    use: 'Interacción activa, ranura seleccionada y anillo de foco',
    previous: '#E4572E',
  },
  'estado-ok': { hex: '#3FA66B', group: 'estado', use: 'En stock / compatible' },
  'estado-aviso': { hex: '#E0A526', group: 'estado', use: 'Pocas unidades / con adaptador' },
  // #D2453F daba 4,35:1 sobre negro pavonado y 3,67:1 sobre grafito. Misma tinta y croma en OKLCH,
  // solo más luz: 4,63:1 en la peor superficie.
  'estado-error': { hex: '#E65850', group: 'estado', use: 'Agotado / incompatible', previous: '#D2453F' },
  // #6B7480 daba 4,13:1 sobre negro pavonado y 3,49:1 sobre grafito. Mismo criterio: 4,61:1.
  'estado-desconocido': { hex: '#7F8894', group: 'estado', use: 'Sin datos', previous: '#6B7480' },
} as const satisfies Record<string, ColorSpec>;

export type ColorToken = keyof typeof COLOR_TOKENS;

/** Solo los valores hexadecimales, por nombre. */
export const colors = Object.fromEntries(Object.entries(COLOR_TOKENS).map(([name, spec]) => [name, spec.hex])) as {
  readonly [K in ColorToken]: (typeof COLOR_TOKENS)[K]['hex'];
};

/** Familias (docs/02 §4.2), con alternativas del sistema mientras carga la fuente. */
export const FONT_FAMILIES = {
  /** Marca y nombres de zona en grande: capitales de inscripción. */
  grabado: "'Cinzel', 'Trajan Pro', Georgia, 'Times New Roman', serif",
  /** Etiquetas de zona, chips y rótulos: plantilla industrial. */
  rotulo: "'Big Shoulders Stencil', 'Arial Narrow', 'Roboto Condensed', sans-serif-condensed, sans-serif",
  /** Interfaz: variable con eje de anchura. */
  interfaz: "'Archivo Variable', 'Archivo', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  /** Medidas, precios y códigos, con cifras tabulares. */
  datos: "'JetBrains Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace",
} as const;

/** Escala modular 1,25 (12/14/16/20/25/31/39/49/61 px) en rem, para respetar el tamaño elegido. */
export const FONT_SIZES = {
  xs: '0.75rem',
  s: '0.875rem',
  m: '1rem',
  l: '1.25rem',
  xl: '1.5625rem',
  '2xl': '1.9375rem',
  '3xl': '2.4375rem',
  '4xl': '3.0625rem',
  '5xl': '3.8125rem',
} as const;

export const FONT_WEIGHTS = { regular: '400', medio: '500', semi: '600', negrita: '700' } as const;

/** Eje de anchura de Archivo: condensada para datos densos, normal para lectura. */
export const FONT_STRETCH = { condensada: '75%', semicondensada: '87.5%', normal: '100%' } as const;

export const LINE_HEIGHTS = { cuerpo: '1.5', titular: '1.1', compacto: '1.25' } as const;

export const LETTER_SPACING = { grabado: '0.08em', rotulo: '0.06em', versalitas: '0.04em' } as const;

/** Rejilla de 4 px: 4/8/12/16/24/32/48/64/96 (la clave es el múltiplo de 4 px). */
export const SPACING = {
  '1': '0.25rem',
  '2': '0.5rem',
  '3': '0.75rem',
  '4': '1rem',
  '6': '1.5rem',
  '8': '2rem',
  '12': '3rem',
  '16': '4rem',
  '24': '6rem',
} as const;

/** Objetivo táctil mínimo (docs/02 §5 y WCAG 2.5.8): 44 px. */
export const TOUCH_TARGET = '2.75rem';

/** Anchos máximos: medida de lectura (~70 caracteres) y página. */
export const WIDTHS = { lectura: '42rem', pagina: '80rem' } as const;

/** Radios pequeños: industrial y preciso. Sin pastillas salvo avatares. */
export const RADII = { s: '2px', m: '3px', l: '4px', avatar: '9999px' } as const;

/** Grosor de trazos: bordes de 1 px y anillo de foco de 2 px. */
export const STROKES = { fino: '1px', foco: '2px' } as const;

/**
 * Sombras largas y suaves, con el brillo interior superior de 1 px de las placas (el filo del panel
 * que recibe la luz de los tubos del techo). Al 6 % no se percibía: 11 % en placa y 14 % en elevada.
 */
export const SHADOWS = {
  placa: 'inset 0 1px 0 0 rgb(232 228 220 / 0.11), 0 1px 2px 0 rgb(0 0 0 / 0.45), 0 16px 40px -16px rgb(0 0 0 / 0.7)',
  elevada: 'inset 0 1px 0 0 rgb(232 228 220 / 0.14), 0 2px 4px 0 rgb(0 0 0 / 0.45), 0 28px 64px -20px rgb(0 0 0 / 0.8)',
  boton: 'inset 0 1px 0 0 rgb(255 255 255 / 0.16), 0 1px 2px 0 rgb(0 0 0 / 0.5)',
  hundida: 'inset 0 1px 2px 0 rgb(0 0 0 / 0.55)',
} as const;

/** Resplandor del rótulo iluminado (tubo LED encendido). */
export const GLOWS = { rotulo: '0 0 0.75rem rgb(217 183 126 / 0.45), 0 0 0.125rem rgb(217 183 126 / 0.6)' } as const;

/** Duraciones (docs/02 §4.4). Con movimiento reducido se quedan en fundidos de 120 ms o menos. */
export const DURATIONS = { micro: '120ms', componente: '200ms', panel: '320ms', escena: '700ms' } as const;
export const REDUCED_DURATIONS = { micro: '120ms', componente: '120ms', panel: '120ms', escena: '0ms' } as const;

/** Curvas: «mecánica» para casi todo y «pesada» para raíles y cajones. */
export const EASINGS = {
  mecanica: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  pesada: 'cubic-bezier(0.7, 0, 0.2, 1)',
} as const;

/** Puntos de corte (docs/02 §6). El móvil (390 px) es la base. */
export const BREAKPOINTS = { tablet: '52.125rem', escritorio: '80rem', ancho: '90rem', amplio: '120rem' } as const;

/**
 * Brillo interior de las placas: luz cenital muy suave que cae sobre el tercio superior del panel,
 * como la de los tubos LED sobre una chapa. Va con el filo de 1 px de `SHADOWS.placa`.
 */
export const SHEENS = {
  placa: 'linear-gradient(180deg, rgb(232 228 220 / 0.055) 0%, rgb(232 228 220 / 0.018) 22%, rgb(232 228 220 / 0) 48%)',
} as const;

/** Opacidad máxima del ruido sobre el panel (docs/02 §4.3: ≤ 3 %). */
export const NOISE_OPACITY = 0.03;

/**
 * Ruido sutil de las placas como SVG en data URI (lo permite img-src de la CSP). Antes era grano solo
 * blanco con una opacidad media del 1,5 % y no se percibía. Ahora es grano gris de contraste completo
 * (claro y oscuro: feComponentTransfer estira el ruido a 0–1 y fija el alfa) en una capa al 3 %.
 */
export const NOISE_TEXTURE =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='r' x='0' y='0' width='100%25' height='100%25'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3' seed='6' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3CfeComponentTransfer%3E%3CfeFuncR type='linear' slope='2.2' intercept='-0.6'/%3E%3CfeFuncG type='linear' slope='2.2' intercept='-0.6'/%3E%3CfeFuncB type='linear' slope='2.2' intercept='-0.6'/%3E%3CfeFuncA type='table' tableValues='1 1'/%3E%3C/feComponentTransfer%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23r)' opacity='" +
  NOISE_OPACITY +
  '\'/%3E%3C/svg%3E")';
