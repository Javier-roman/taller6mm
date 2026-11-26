// Punto de stock (docs/02 §4.5): estado de existencias con forma, icono y texto, nunca solo color.
// El stock caduca: la fecha de comprobación la lleva EtiquetaPrecio o quien lo muestre.
import { IconoAlerta, IconoCheck, IconoCruz, IconoDesconocido } from './iconos.tsx';
import { cx } from './util.ts';

export type EstadoStock = 'en-stock' | 'pocas' | 'agotado' | 'desconocido';
export const ESTADOS_STOCK: Readonly<Record<EstadoStock, string>> = {
  'en-stock': 'En stock',
  pocas: 'Pocas unidades',
  agotado: 'Agotado',
  desconocido: 'Stock desconocido',
};

const ICONO = {
  'en-stock': IconoCheck,
  pocas: IconoAlerta,
  agotado: IconoCruz,
  desconocido: IconoDesconocido,
} as const;

export function PuntoStock({ estado, className }: { estado: EstadoStock; className?: string }) {
  const Icono = ICONO[estado];
  return (
    <span className={cx('t6-stock', `t6-stock--${estado}`, className)} data-stock={estado}>
      <Icono />
      {ESTADOS_STOCK[estado]}
    </span>
  );
}
