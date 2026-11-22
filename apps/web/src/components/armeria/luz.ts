// Niveles de luz de la sala. Sin DOM ni WebGL: lo usan la interfaz, el nivel B y el nivel A.
// Penumbra por defecto; «Más luz» es una ayuda de legibilidad con la misma temperatura (ADR-0002: la variante
// cálida «Taller abierto» se descartó porque borraba el contraste entre los tubos fríos y el flexo cálido).
import type { Luz } from './estado.ts';

export interface VarianteLuz {
  readonly nombre: string;
  /** Nivel de los tubos en reposo. */
  readonly reposo: number;
  /** Tubos de la estantería activa y del resto mientras hay una zona activa. */
  readonly foco: number;
  readonly resto: number;
  readonly calidas: number;
  readonly ambiente: number;
  /** Color de los tubos (hex): frío, como en ref-08. */
  readonly colorTubo: string;
}

export const VARIANTES_LUZ: Readonly<Record<Luz, VarianteLuz>> = {
  // Penumbra más marcada (Javi, 04-11-2026): menos luz de relleno para que se lean el brillo del metal y el
  // reflejo del suelo. «Más luz» sigue a la vista para leer.
  penumbra: {
    nombre: 'Cierre de taller (penumbra)',
    reposo: 0.34,
    foco: 1,
    resto: 0.18,
    calidas: 1,
    ambiente: 0.4,
    colorTubo: '#dfe9ff',
  },
  'mas-luz': {
    nombre: 'Más luz',
    reposo: 0.7,
    foco: 1.05,
    resto: 0.55,
    calidas: 1,
    ambiente: 1.3,
    colorTubo: '#dfe9ff',
  },
};
