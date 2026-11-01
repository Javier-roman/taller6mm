// Rótulo a plantilla (docs/02 §4.2 y §4.5): Big Shoulders Stencil en mayúsculas. Tintas hueso,
// latón y FDE, o pintado sobre chapa verde. «Iluminado» es el tubo LED encendido de La Armería:
// se enciende al pasar por encima o al enfocar el enlace que lo contiene (`.t6-rotulo-enlace`).
import type { ReactNode } from 'react';
import { cx } from './util.ts';

export type TamanoRotulo = 's' | 'm' | 'l';
export type TintaRotulo = 'hueso' | 'laton' | 'fde' | 'chapa';

export interface RotuloProps {
  children: ReactNode;
  tamano?: TamanoRotulo;
  tinta?: TintaRotulo;
  iluminado?: boolean;
  /** Módulo sin datos o aún no disponible. */
  apagado?: boolean;
  as?: 'span' | 'p' | 'strong' | 'h2' | 'h3';
  id?: string;
  className?: string;
}

export function Rotulo({
  children,
  tamano = 'm',
  tinta = 'hueso',
  iluminado = false,
  apagado = false,
  as: Tag = 'span',
  id,
  className,
}: RotuloProps) {
  return (
    <Tag
      id={id}
      className={cx(
        't6-rotulo',
        tamano !== 'm' && `t6-rotulo--${tamano}`,
        tinta !== 'hueso' && `t6-rotulo--${tinta}`,
        apagado && 't6-rotulo--apagado',
        className,
      )}
      data-iluminado={iluminado && !apagado ? '' : undefined}
    >
      {children}
    </Tag>
  );
}
