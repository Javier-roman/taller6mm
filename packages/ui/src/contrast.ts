// Contraste WCAG 2.2 (1.4.3 texto y 1.4.11 componentes) y pares de color que el sistema permite.
// Un test comprueba cada par: si un color cambia y deja de llegar, el test falla.
import { type ColorToken, colors } from './tokens.ts';

const channel = (value: number) => {
  const c = value / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
};

/** Luminancia relativa de un color #RRGGBB (WCAG 2.x). */
export function relativeLuminance(hex: string): number {
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
  if (!m) throw new Error(`Color no válido: ${hex}`);
  const [r, g, b] = [m[1], m[2], m[3]].map((part) => channel(Number.parseInt(part ?? '', 16)));
  return 0.2126 * (r ?? 0) + 0.7152 * (g ?? 0) + 0.0722 * (b ?? 0);
}

/** Relación de contraste entre dos colores (de 1 a 21). */
export function contrastRatio(a: string, b: string): number {
  const [hi, lo] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x);
  return ((hi ?? 0) + 0.05) / ((lo ?? 0) + 0.05);
}

/** Mínimos AA: texto normal 4,5:1; texto grande y componentes o gráficos 3:1. */
export const AA = { texto: 4.5, textoGrande: 3, componente: 3 } as const;
export type PairKind = keyof typeof AA;

export interface ColorPair {
  readonly fg: ColorToken;
  readonly bg: ColorToken;
  readonly kind: PairKind;
  readonly use: string;
}

const SURFACES = ['negro-pavonado', 'carbon', 'grafito'] as const satisfies readonly ColorToken[];
const onSurfaces = (fg: ColorToken, use: string, kind: PairKind = 'texto'): ColorPair[] =>
  SURFACES.map((bg) => ({ fg, bg, kind, use }));

/**
 * Pares declarados. Todo color que se use como texto sobre las tres superficies aparece aquí.
 * `naranja-senal` no es color de texto sobre grafito (4,49:1): se usa como indicador (3:1) y como
 * texto solo sobre negro pavonado y carbón.
 */
export const COLOR_PAIRS: readonly ColorPair[] = [
  ...onSurfaces('hueso', 'Texto principal'),
  ...onSurfaces('niebla', 'Texto secundario'),
  ...onSurfaces('laton', 'Acento y enlaces'),
  ...onSurfaces('laton-claro', 'Acento en hover'),
  ...onSurfaces('fde', 'Acento secundario'),
  ...onSurfaces('estado-ok', 'Estado: en stock / compatible'),
  ...onSurfaces('estado-aviso', 'Estado: pocas unidades / con adaptador'),
  ...onSurfaces('estado-error', 'Estado: agotado / incompatible'),
  ...onSurfaces('estado-desconocido', 'Estado: sin datos'),
  { fg: 'naranja-senal', bg: 'negro-pavonado', kind: 'texto', use: 'Señal como texto' },
  { fg: 'naranja-senal', bg: 'carbon', kind: 'texto', use: 'Señal como texto' },
  ...onSurfaces('naranja-senal', 'Anillo de foco y ranura seleccionada', 'componente'),
  ...onSurfaces('laton', 'Borde de componente activo', 'componente'),
  { fg: 'hueso', bg: 'acero', kind: 'texto', use: 'Botón acero' },
  { fg: 'negro-pavonado', bg: 'laton', kind: 'texto', use: 'Botón latón' },
  { fg: 'negro-pavonado', bg: 'laton-claro', kind: 'texto', use: 'Botón latón en hover' },
  { fg: 'negro-pavonado', bg: 'estado-error', kind: 'texto', use: 'Botón peligro en hover' },
  { fg: 'hueso', bg: 'verde-ranger', kind: 'texto', use: 'Rótulo sobre chapa verde' },
  { fg: 'negro-pavonado', bg: 'laton-claro', kind: 'texto', use: 'Insignia T3' },
];

export interface PairResult extends ColorPair {
  readonly ratio: number;
  readonly min: number;
  readonly passes: boolean;
}

export function checkPair(pair: ColorPair): PairResult {
  const ratio = contrastRatio(colors[pair.fg], colors[pair.bg]);
  const min = AA[pair.kind];
  return { ...pair, ratio, min, passes: ratio >= min };
}
