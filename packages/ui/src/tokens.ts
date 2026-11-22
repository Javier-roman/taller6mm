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

/**
 * Colores (docs/02 §4.1), dirección de arte A «Plano de cotas» (ADR-0010, 22-11-2026). Los NOMBRES
 * se conservan de la dirección anterior (acabados de armero) para no romper clases ni código que ya
 * los usa; el papel que cumple cada uno ahora está en `use`. Ajustes de Javi sobre el prototipo:
 * más diferencia entre tinta y lámina, bordes más marcados y más contraste general, sin saturar.
 */
export const COLOR_TOKENS = {
  'negro-pavonado': { hex: '#080C0F', group: 'superficie', use: 'Tinta: fondo de la mesa de dibujo' },
  carbon: { hex: '#15212A', group: 'superficie', use: 'Lámina: superficie de paneles' },
  grafito: { hex: '#1F303B', group: 'superficie', use: 'Lámina alta: paneles elevados y hover' },
  acero: { hex: '#3D525E', group: 'superficie', use: 'Trazo: bordes y divisores' },
  'trazo-fuerte': { hex: '#7F96A0', group: 'superficie', use: 'Borde de control, cotas secundarias y regla' },
  papel: { hex: '#D7D4CC', group: 'superficie', use: 'Papel: lámina impresa donde viven los renders y planos' },
  hueso: { hex: '#EFEBE1', group: 'texto', use: 'Texto principal' },
  niebla: { hex: '#AFBCC3', group: 'texto', use: 'Texto secundario' },
  'tinta-papel': { hex: '#1B2226', group: 'texto', use: 'Trazo y texto sobre papel' },
  cota: { hex: '#9CC3D0', group: 'acento', use: 'Líneas y textos de cota, registro y etiquetas técnicas' },
  kraft: { hex: '#C9AE84', group: 'acento', use: 'Portaetiquetas de kraft: etiquetas de precio' },
  laton: { hex: '#C29A5B', group: 'acento', use: 'Acento principal: acción y precio' },
  'laton-claro': { hex: '#DDBB82', group: 'acento', use: 'Hover y realce del acento' },
  'sobre-laton': { hex: '#15110B', group: 'texto', use: 'Texto sobre latón' },
  fde: { hex: '#B09A7A', group: 'acento', use: 'Acento secundario (Flat Dark Earth): marcas y referencias' },
  'verde-ranger': { hex: '#4B5A3F', group: 'acento', use: 'Acento terciario (fondos y chapas)' },
  'naranja-senal': {
    hex: '#F27346',
    group: 'acento',
    use: 'Señal: foco, ranura seleccionada y luz de tubo en lo activo',
  },
  'estado-ok': { hex: '#4DB27B', group: 'estado', use: 'En stock / compatible' },
  'estado-aviso': { hex: '#E2A82B', group: 'estado', use: 'Pocas unidades / con adaptador' },
  'estado-error': { hex: '#F0736B', group: 'estado', use: 'Agotado / incompatible' },
  'estado-desconocido': { hex: '#8C96A1', group: 'estado', use: 'Sin datos' },
} as const satisfies Record<string, ColorSpec>;

export type ColorToken = keyof typeof COLOR_TOKENS;

/** Solo los valores hexadecimales, por nombre. */
export const colors = Object.fromEntries(Object.entries(COLOR_TOKENS).map(([name, spec]) => [name, spec.hex])) as {
  readonly [K in ColorToken]: (typeof COLOR_TOKENS)[K]['hex'];
};

/** Familias (docs/02 §4.2), con alternativas del sistema mientras carga la fuente. */
export const FONT_FAMILIES = {
  /** Titulares y marca: la misma Plex condensada, en semibold. */
  grabado: "'IBM Plex Sans Condensed', 'Arial Narrow', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  /** Etiquetas de zona, chips y rótulos: Plex condensada en versalitas. */
  rotulo: "'IBM Plex Sans Condensed', 'Arial Narrow', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  /** Interfaz y lectura: condensada, para datos densos. */
  interfaz: "'IBM Plex Sans Condensed', 'Arial Narrow', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  /** Medidas, precios, códigos y cotas, con cifras tabulares. */
  datos: "'IBM Plex Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace",
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

export const LETTER_SPACING = { grabado: '0.01em', rotulo: '0.1em', versalitas: '0.08em' } as const;

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

/**
 * Anchos máximos. Lectura: ~70 caracteres a 16 px (con 42rem salían 80–99). Entradilla: la misma
 * medida para el texto de 20 px. Página: el ancho del contenido.
 */
export const WIDTHS = { lectura: '34rem', entradilla: '42rem', pagina: '80rem' } as const;

/** Plano de cotas: radio 0 en paneles (l) y marcas (s), 2 px en controles (m). Sin pastillas salvo avatares. */
export const RADII = { s: '0px', m: '2px', l: '0px', avatar: '9999px' } as const;

/** Grosor de trazos: bordes de 1 px y anillo de foco de 2 px. */
export const STROKES = { fino: '1px', foco: '2px' } as const;

/**
 * Sombras largas y suaves, con el brillo interior superior de 1 px de las placas (el filo del panel
 * que recibe la luz de los tubos del techo). Al 6 % no se percibía: 11 % en placa y 14 % en elevada.
 */
export const SHADOWS = {
  placa:
    'inset 0 1px 0 0 rgb(156 195 208 / 0.1), inset 0 0 1.25rem 0 rgb(0 0 0 / 0.45), 0 1px 0 0 rgb(0 0 0 / 0.7), 0 1rem 2rem -1rem rgb(0 0 0 / 0.75)',
  elevada:
    'inset 0 1px 0 0 rgb(156 195 208 / 0.14), inset 0 0 1.25rem 0 rgb(0 0 0 / 0.4), 0 2px 0 0 rgb(0 0 0 / 0.7), 0 1.75rem 3rem -1.25rem rgb(0 0 0 / 0.85)',
  boton: 'inset 0 -2px 0 0 rgb(0 0 0 / 0.28)',
  hundida: 'inset 0 2px 0 0 rgb(0 0 0 / 0.3)',
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
  placa: 'linear-gradient(180deg, rgb(156 195 208 / 0.05) 0%, rgb(156 195 208 / 0.015) 22%, rgb(156 195 208 / 0) 48%)',
} as const;

/**
 * Luces de la sala (docs/02 §1 y §3.1): la cenital fría de los tubos LED y la cálida del flexo del
 * banco. Las usan las cabeceras y, en la Fase 1, La Armería. Son luz sobre una superficie, no color.
 */
export const LIGHTS = {
  cenital: 'radial-gradient(90% 70% at 50% -10%, rgb(232 228 220 / 0.08), rgb(232 228 220 / 0) 70%)',
  flexo: 'radial-gradient(55% 80% at 100% 0%, rgb(217 183 126 / 0.1), rgb(217 183 126 / 0) 65%)',
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

/**
 * Retícula de la mesa de dibujo (ADR-0010): líneas de 1 px cada 16 px (menor) y cada 80 px (mayor),
 * en la tinta de cota y muy tenues. Se pinta con `background-size` de 5 × espacio-4 y espacio-4.
 */
export const RETICULA =
  'linear-gradient(rgb(156 195 208 / 0.1) 1px, transparent 1px), linear-gradient(90deg, rgb(156 195 208 / 0.1) 1px, transparent 1px), linear-gradient(rgb(156 195 208 / 0.05) 1px, transparent 1px), linear-gradient(90deg, rgb(156 195 208 / 0.05) 1px, transparent 1px)';
