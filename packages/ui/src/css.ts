// Genera styles/tokens.css (variables CSS) y styles/theme.css (@theme de Tailwind v4) desde tokens.ts.
// Lo usan scripts/write-css.ts (para escribirlos) y css.test.ts (para comprobar que están al día).
import {
  BREAKPOINTS,
  COLOR_TOKENS,
  DURATIONS,
  EASINGS,
  FONT_FAMILIES,
  FONT_SIZES,
  FONT_STRETCH,
  FONT_WEIGHTS,
  GLOWS,
  LETTER_SPACING,
  LIGHTS,
  LINE_HEIGHTS,
  NOISE_TEXTURE,
  RADII,
  REDUCED_DURATIONS,
  SHADOWS,
  SHEENS,
  SPACING,
  STROKES,
  TOUCH_TARGET,
  WIDTHS,
} from './tokens.ts';

const HEADER =
  '/* Generado desde packages/ui/src/tokens.ts con `pnpm --filter @taller6mm/ui css`. No lo edites a mano. */';

type Group = Readonly<Record<string, string>>;

const declarations = (prefix: string, group: Group, indent = '  ') =>
  Object.entries(group).map(([key, value]) => `${indent}--${prefix}${key}: ${value};`);

/** Variables CSS con los nombres de docs/02 (`--laton`, `--espacio-4`, `--duracion-micro`…). */
export function tokensCss(): string {
  const colors = Object.fromEntries(Object.entries(COLOR_TOKENS).map(([name, spec]) => [name, spec.hex]));
  return [
    HEADER,
    ':root {',
    '  /* Color (docs/02 §4.1) */',
    ...declarations('', colors),
    '',
    '  /* Tipografía (§4.2) */',
    ...declarations('fuente-', FONT_FAMILIES),
    ...declarations('texto-', FONT_SIZES),
    ...declarations('peso-', FONT_WEIGHTS),
    ...declarations('anchura-', FONT_STRETCH),
    ...declarations('interlineado-', LINE_HEIGHTS),
    ...declarations('interletra-', LETTER_SPACING),
    '',
    '  /* Espacio, forma y profundidad (§4.3) */',
    ...declarations('espacio-', SPACING),
    `  --objetivo-tactil: ${TOUCH_TARGET};`,
    ...declarations('ancho-', WIDTHS),
    ...declarations('radio-', RADII),
    ...declarations('trazo-', STROKES),
    ...declarations('sombra-', SHADOWS),
    ...declarations('resplandor-', GLOWS),
    ...declarations('brillo-', SHEENS),
    ...declarations('luz-', LIGHTS),
    `  --textura-ruido: ${NOISE_TEXTURE};`,
    '',
    '  /* Movimiento (§4.4) */',
    ...declarations('duracion-', DURATIONS),
    ...declarations('curva-', EASINGS),
    '}',
    '',
    '/* Movimiento reducido: fundidos de 120 ms como máximo y sin escena. */',
    '@media (prefers-reduced-motion: reduce) {',
    '  :root {',
    ...declarations('duracion-', REDUCED_DURATIONS, '    '),
    '  }',
    '}',
    '',
  ].join('\n');
}

const mapTo = (namespace: string, source: string, group: Group) =>
  Object.keys(group).map((key) => `  --${namespace}${key}: var(--${source}${key});`);

/**
 * Tema de Tailwind v4 enlazado a las variables (`inline`: las utilidades usan `var(--laton)`).
 * No se importa el tema por defecto de Tailwind: solo existen estos tokens (`bg-grafito`, `p-4`,
 * `font-datos`, `text-xl`, `rounded-m`, `shadow-placa`, `ease-mecanica`, `tablet:`…).
 */
export function themeCss(): string {
  return [
    HEADER,
    '@theme inline {',
    ...Object.keys(COLOR_TOKENS).map((name) => `  --color-${name}: var(--${name});`),
    ...mapTo('font-', 'fuente-', FONT_FAMILIES),
    ...mapTo('text-', 'texto-', FONT_SIZES),
    ...mapTo('font-weight-', 'peso-', FONT_WEIGHTS),
    ...mapTo('leading-', 'interlineado-', LINE_HEIGHTS),
    ...mapTo('tracking-', 'interletra-', LETTER_SPACING),
    ...mapTo('spacing-', 'espacio-', SPACING),
    '  --spacing-tactil: var(--objetivo-tactil);',
    ...mapTo('container-', 'ancho-', WIDTHS),
    ...mapTo('radius-', 'radio-', RADII),
    ...mapTo('shadow-', 'sombra-', SHADOWS),
    ...mapTo('ease-', 'curva-', EASINGS),
    ...declarations('breakpoint-', BREAKPOINTS),
    '  --default-font-family: var(--fuente-interfaz);',
    '  --default-mono-font-family: var(--fuente-datos);',
    '  --default-transition-duration: var(--duracion-componente);',
    '  --default-transition-timing-function: var(--curva-mecanica);',
    '}',
    '',
  ].join('\n');
}
