// Disponibilidad común de las ofertas (docs/04 §5), mapeada desde schema.org/ItemAvailability.
// Lo que no se reconoce es `desconocido`: nunca se inventa un stock (principio 2, datos honestos).
import { z } from 'zod';

export const AVAILABILITIES = [
  'en_stock',
  'pocas_unidades',
  'preventa',
  'bajo_pedido',
  'agotado',
  'descatalogado',
  'desconocido',
] as const;

export const AvailabilitySchema = z.enum(AVAILABILITIES);
export type Availability = z.infer<typeof AvailabilitySchema>;

/** Valores de https://schema.org/ItemAvailability, en minúsculas. */
const FROM_SCHEMA_ORG: Readonly<Record<string, Availability>> = {
  instock: 'en_stock',
  onlineonly: 'en_stock',
  limitedavailability: 'pocas_unidades',
  preorder: 'preventa',
  presale: 'preventa',
  backorder: 'bajo_pedido',
  madetoorder: 'bajo_pedido',
  outofstock: 'agotado',
  soldout: 'agotado',
  discontinued: 'descatalogado',
  // Solo en tienda física: para comprar en línea no sabemos si hay stock.
  instoreonly: 'desconocido',
  // Reservado para otro cliente: no se puede comprar.
  reserved: 'agotado',
};

/**
 * Normaliza un valor de disponibilidad tal como llega de JSON-LD, microdatos u OpenGraph:
 * `https://schema.org/InStock`, `http://schema.org/InStock`, `schema:InStock` o `InStock`,
 * con cualquier combinación de mayúsculas y espacios. Nunca lanza.
 */
export function normalizeAvailability(raw: unknown): Availability {
  if (typeof raw !== 'string') return 'desconocido';
  const key = raw
    .trim()
    .replace(/^https?:\/\/(?:www\.)?schema\.org\//i, '')
    .replace(/^schema:/i, '')
    .replace(/[\s_-]/g, '')
    .toLowerCase();
  return FROM_SCHEMA_ORG[key] ?? 'desconocido';
}

/** ¿Se puede comprar ahora (o reservar en firme)? Para filtros y alertas de vuelta a stock. */
export function isPurchasable(availability: Availability): boolean {
  return (
    availability === 'en_stock' ||
    availability === 'pocas_unidades' ||
    availability === 'preventa' ||
    availability === 'bajo_pedido'
  );
}
