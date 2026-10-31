import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { themeCss, tokensCss } from './css.ts';
import {
  AA,
  BRAND,
  COLOR_PAIRS,
  COLOR_TOKENS,
  checkPair,
  colors,
  contrastRatio,
  DURATIONS,
  FONT_SIZES,
  REDUCED_DURATIONS,
  SPACING,
} from './index.ts';

const styles = (name: string) => readFileSync(new URL(`./styles/${name}`, import.meta.url), 'utf8');

describe('tokens', () => {
  test('todos los colores son hexadecimales de 6 dígitos', () => {
    for (const [name, value] of Object.entries(colors)) expect(value, name).toMatch(/^#[0-9A-F]{6}$/);
  });

  test('los nombres son kebab-case en español, sin acentos', () => {
    for (const name of Object.keys(colors)) expect(name).toMatch(/^[a-z]+(?:-[a-z]+)*$/);
  });

  test('escala tipográfica modular 1,25 (12/14/16/20/25/31/39/49/61 px)', () => {
    const px = Object.values(FONT_SIZES).map((rem) => Number.parseFloat(rem) * 16);
    expect(px).toEqual([12, 14, 16, 20, 25, 31, 39, 49, 61]);
  });

  test('rejilla de 4 px: 4/8/12/16/24/32/48/64/96', () => {
    const px = Object.entries(SPACING).map(([key, rem]) => [Number(key) * 4, Number.parseFloat(rem) * 16]);
    for (const [expected, actual] of px) expect(actual).toBe(expected);
    expect(px.map(([p]) => p)).toEqual([4, 8, 12, 16, 24, 32, 48, 64, 96]);
  });

  test('con movimiento reducido nada pasa de 120 ms', () => {
    for (const value of Object.values(REDUCED_DURATIONS)) expect(Number.parseInt(value, 10)).toBeLessThanOrEqual(120);
    expect(Object.keys(REDUCED_DURATIONS)).toEqual(Object.keys(DURATIONS));
  });
});

describe('contraste AA (WCAG 2.2: 1.4.3 y 1.4.11)', () => {
  test('la fórmula da los valores de referencia', () => {
    expect(contrastRatio('#000000', '#FFFFFF')).toBeCloseTo(21, 5);
    expect(contrastRatio('#777777', '#FFFFFF')).toBeCloseTo(4.48, 2);
    expect(contrastRatio('#123456', '#123456')).toBe(1);
  });

  test.each(COLOR_PAIRS.map((pair) => [`${pair.fg} sobre ${pair.bg} (${pair.use})`, pair] as const))(
    '%s',
    (_name, pair) => {
      const result = checkPair(pair);
      expect(result.ratio, `${result.ratio.toFixed(2)}:1 < ${result.min}:1`).toBeGreaterThanOrEqual(result.min);
    },
  );

  test('los dos colores corregidos pasan donde antes fallaban, sin cambiar de familia', () => {
    for (const name of ['estado-error', 'estado-desconocido'] as const) {
      const { hex, previous } = COLOR_TOKENS[name];
      expect(contrastRatio(previous, colors.grafito)).toBeLessThan(AA.texto);
      expect(contrastRatio(hex, colors.grafito)).toBeGreaterThanOrEqual(AA.texto);
      expect(contrastRatio(hex, colors['negro-pavonado'])).toBeGreaterThanOrEqual(AA.texto);
    }
  });

  test('todo color de texto o de estado tiene sus pares declarados sobre las tres superficies', () => {
    const textColors = Object.entries(COLOR_TOKENS)
      .filter(([, spec]) => spec.group === 'texto' || spec.group === 'estado')
      .map(([name]) => name);
    for (const fg of textColors) {
      for (const bg of ['negro-pavonado', 'carbon', 'grafito']) {
        expect(
          COLOR_PAIRS.some((p) => p.fg === fg && p.bg === bg && p.kind === 'texto'),
          `${fg} sobre ${bg}`,
        ).toBe(true);
      }
    }
  });
});

describe('CSS generado (styles/tokens.css y styles/theme.css)', () => {
  test('está al día con tokens.ts (si falla: pnpm --filter @taller6mm/ui css)', () => {
    expect(styles('tokens.css')).toBe(tokensCss());
    expect(styles('theme.css')).toBe(themeCss());
  });

  test('cada color está como variable CSS y como color de Tailwind', () => {
    for (const [name, hex] of Object.entries(colors)) {
      expect(tokensCss()).toContain(`--${name}: ${hex};`);
      expect(themeCss()).toContain(`--color-${name}: var(--${name});`);
    }
  });
});

describe('estilos escritos a mano: solo tokens (.claude/rules/ui.md)', () => {
  test.each(['componentes.css', 'base.css'])('%s no tiene colores, medidas ni duraciones sueltas', (file) => {
    const css = styles(file).replace(/\/\*[\s\S]*?\*\//g, '');
    expect(css, 'color hexadecimal').not.toMatch(/#[0-9a-f]{3,8}\b/i);
    expect(css, 'rgb()/hsl() literal').not.toMatch(/\b(?:rgba?|hsla?|oklch|oklab)\(/i);
    expect(css, 'medida en px o rem').not.toMatch(/(?<![\w-])\d*\.?\d+(?:px|rem)\b/);
    expect(css, 'duración en ms o s').not.toMatch(/(?<![\w-])\d*\.?\d+m?s\b/);
    expect(css, 'curva propia').not.toMatch(/cubic-bezier|steps\(/);
  });

  test('las fuentes son las cuatro de docs/02 §4.2, autoalojadas', () => {
    const css = styles('fuentes.css');
    for (const pkg of [
      '@fontsource-variable/archivo',
      '@fontsource/cinzel',
      '@fontsource/big-shoulders-stencil',
      '@fontsource/jetbrains-mono',
    ]) {
      expect(css).toContain(pkg);
    }
    expect(css).not.toMatch(/fonts\.(googleapis|gstatic)\.com/);
  });
});

describe('marca', () => {
  test('nombre visible y prefijo del código de build', () => {
    expect(BRAND.name).toBe('Taller6mm');
    expect(BRAND.buildCodePrefix).toBe('T6M');
  });
});
