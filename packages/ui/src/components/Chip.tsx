// Chip e insignia (docs/02 §4.5): etiqueta corta de estado o categoría. El tono nunca va solo:
// cada tono de estado lleva su icono y el texto lo pone quien lo usa.
import type { ReactNode } from 'react';
import { IconoAlerta, IconoCheck, IconoCruz, IconoDesconocido, IconoInfo } from './iconos.tsx';
import { cx } from './util.ts';

export type TonoChip = 'neutro' | 'laton' | 'ok' | 'aviso' | 'error' | 'desconocido';
export const TONOS_CHIP: readonly TonoChip[] = ['neutro', 'laton', 'ok', 'aviso', 'error', 'desconocido'];

const ICONO: Record<TonoChip, () => ReactNode> = {
  neutro: IconoInfo,
  laton: IconoInfo,
  ok: IconoCheck,
  aviso: IconoAlerta,
  error: IconoCruz,
  desconocido: IconoDesconocido,
};

export interface ChipProps {
  tono?: TonoChip;
  /** Sin icono, solo para categorías neutras (marca, plataforma). */
  sinIcono?: boolean;
  className?: string;
  children: ReactNode;
}

export function Chip({ tono = 'neutro', sinIcono = false, className, children }: ChipProps) {
  const Icono = ICONO[tono];
  const conIcono = !sinIcono && tono !== 'neutro' && tono !== 'laton';
  return (
    <span className={cx('t6-chip', `t6-chip--${tono}`, className)}>
      {conIcono ? <Icono /> : null}
      {children}
    </span>
  );
}
