// Aviso (docs/02 §4.5 y §4.7): mensaje en bloque. «Provisional» marca datos o assets que aún no
// están verificados (principio 1 y 2: se dice, no se disimula). Estático por defecto (`role="note"`);
// con `viva` se anuncia: `alert` para errores, `status` para el resto.
import type { ReactNode } from 'react';
import { IconoAlerta, IconoCheck, IconoInfo, IconoReloj } from './iconos.tsx';
import { cx } from './util.ts';

export type TipoAviso = 'info' | 'provisional' | 'aviso' | 'error' | 'ok';
export const TIPOS_AVISO: readonly TipoAviso[] = ['info', 'provisional', 'aviso', 'error', 'ok'];

const ICONO = {
  info: IconoInfo,
  provisional: IconoReloj,
  aviso: IconoAlerta,
  error: IconoAlerta,
  ok: IconoCheck,
} as const;

export interface AvisoProps {
  tipo?: TipoAviso;
  titulo: string;
  /** Anunciarlo a lectores de pantalla cuando aparece (mensajes que llegan tras una acción). */
  viva?: boolean;
  /** Acción asociada (un botón o enlace). */
  accion?: ReactNode;
  className?: string;
  children?: ReactNode;
}

export function Aviso({ tipo = 'info', titulo, viva = false, accion, className, children }: AvisoProps) {
  const Icono = ICONO[tipo];
  const role = viva ? (tipo === 'error' ? 'alert' : 'status') : 'note';
  return (
    <div className={cx('t6-aviso', `t6-aviso--${tipo}`, className)} role={role}>
      <span className="t6-aviso__icono">
        <Icono />
      </span>
      <div className="t6-aviso__cuerpo">
        <p className="t6-aviso__titulo">{titulo}</p>
        {children ? <div className="t6-aviso__texto">{children}</div> : null}
        {accion ? <div className="t6-aviso__accion">{accion}</div> : null}
      </div>
    </div>
  );
}
