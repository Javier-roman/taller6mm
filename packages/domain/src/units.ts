// Longitudes en milímetros con 0,1 mm de precisión (docs/07 §3.4). Todo el catálogo, el motor de
// compatibilidad y los assets trabajan en mm; la escena 3D convierte a metros en el borde.
import { z } from 'zod';

const TENTHS_EPSILON = 1e-9;

/** ¿Es `value` un múltiplo de 0,1 (con tolerancia de coma flotante)? */
export function isTenthOfMillimeter(value: number): boolean {
  if (!Number.isFinite(value)) return false;
  const scaled = value * 10;
  return Math.abs(scaled - Math.round(scaled)) < TENTHS_EPSILON;
}

export const MillimetersSchema = z
  .number()
  .refine(Number.isFinite, 'La longitud debe ser un número finito')
  .refine(isTenthOfMillimeter, 'Las longitudes se guardan con 0,1 mm de precisión')
  .brand<'Millimeters'>();

/** Longitud en milímetros, redondeada a 0,1 mm. */
export type Millimeters = z.infer<typeof MillimetersSchema>;

/**
 * Crea un `Millimeters` redondeando a la décima más cercana (las mitades se alejan de cero,
 * igual para positivos y negativos). Lanza `RangeError` si el valor no es finito.
 */
export function mm(value: number): Millimeters {
  if (!Number.isFinite(value)) throw new RangeError(`Longitud no finita: ${value}`);
  const rounded = (Math.sign(value) * Math.round(Math.abs(value) * 10)) / 10;
  // Evita -0: en datos y en JSON no aporta nada y confunde las comparaciones.
  return MillimetersSchema.parse(Object.is(rounded, -0) ? 0 : rounded);
}
