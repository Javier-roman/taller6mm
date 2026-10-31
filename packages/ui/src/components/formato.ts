// Formato de datos reales para la interfaz (es-ES): longitudes en mm, pesos en g y dinero en
// céntimos enteros (CLAUDE.md, convenciones). Sin decimales inventados.
import { BRAND } from '../brand.ts';

export type Unidad = 'g' | 'mm' | 'eur' | 'tiendas';

interface UnidadSpec {
  readonly simbolo: string;
  readonly nombre: string;
  /** Qué falta cuando una pieza no tiene el dato («2 piezas sin peso»). */
  readonly falta: string;
  readonly decimales: number;
  /** Divisor desde la unidad guardada (céntimos → euros). */
  readonly divisor: number;
}

export const UNIDADES: Readonly<Record<Unidad, UnidadSpec>> = {
  g: { simbolo: 'g', nombre: 'gramos', falta: 'sin peso', decimales: 0, divisor: 1 },
  mm: { simbolo: 'mm', nombre: 'milímetros', falta: 'sin medida', decimales: 0, divisor: 1 },
  eur: { simbolo: '€', nombre: 'euros', falta: 'sin precio', decimales: 2, divisor: 100 },
  tiendas: { simbolo: 'tiendas', nombre: 'tiendas', falta: 'sin tiendas', decimales: 0, divisor: 1 },
};

/** Número en español de España («3120», «12.500», «412,35»). */
export function formatearNumero(valor: number, unidad: Unidad): string {
  const { decimales, divisor } = UNIDADES[unidad];
  return new Intl.NumberFormat(BRAND.locale, {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(valor / divisor);
}

/** Número con su unidad, para textos accesibles («412,35 €», «3120 g»). */
export function formatearDato(valor: number, unidad: Unidad): string {
  return `${formatearNumero(valor, unidad)} ${UNIDADES[unidad].simbolo}`;
}

/** «1 pieza sin peso», «3 piezas sin medida». */
export function textoFaltan(piezas: number, unidad: Unidad): string {
  return `${piezas} ${piezas === 1 ? 'pieza' : 'piezas'} ${UNIDADES[unidad].falta}`;
}
