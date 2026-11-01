// Botón (docs/02 §4.5): latón (acción principal), acero (secundaria), fantasma y peligro.
// Estados: hover, foco, activo, deshabilitado, carga (sigue enfocable con aria-disabled y avisa con
// aria-busy) y error (mensaje enlazado con aria-describedby). Objetivo táctil de 44 px.
import { type AnchorHTMLAttributes, type ButtonHTMLAttributes, type ReactNode, useId } from 'react';
import { Cargador } from './Cargador.tsx';
import { IconoAlerta } from './iconos.tsx';
import { cx, type EstadoDemo } from './util.ts';

export type VarianteBoton = 'laton' | 'acero' | 'fantasma' | 'peligro';
export const VARIANTES_BOTON: readonly VarianteBoton[] = ['laton', 'acero', 'fantasma', 'peligro'];

interface Comun {
  variante?: VarianteBoton;
  icono?: ReactNode;
  /** Solo para /sistema: fuerza la apariencia de hover, activo o foco. */
  demo?: EstadoDemo;
  children: ReactNode;
}

export type BotonProps = Comun &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> & {
    /** Acción en curso: no se puede volver a pulsar, pero el foco no se pierde. */
    cargando?: boolean;
    /** Texto mientras carga («Guardando…»). */
    textoCarga?: string;
    /** Qué falló en la última acción y qué hacer. */
    error?: string;
  };

export function Boton({
  variante = 'acero',
  icono,
  demo,
  children,
  cargando = false,
  textoCarga,
  error,
  className,
  type = 'button',
  ...resto
}: BotonProps) {
  const errorId = `${useId()}-error`;
  const boton = (
    <button
      {...resto}
      type={type}
      className={cx('t6-boton', `t6-boton--${variante}`, className)}
      data-demo={demo}
      data-estado={error ? 'error' : undefined}
      aria-busy={cargando || undefined}
      aria-disabled={cargando || resto['aria-disabled'] || undefined}
      aria-describedby={error ? errorId : resto['aria-describedby']}
    >
      {cargando ? <Cargador /> : icono}
      <span>{cargando && textoCarga ? textoCarga : children}</span>
    </button>
  );
  if (!error) return boton;
  return (
    <span className="t6-accion">
      {boton}
      <span id={errorId} className="t6-mensaje t6-mensaje--error">
        <IconoAlerta />
        {error}
      </span>
    </span>
  );
}

export type BotonEnlaceProps = Comun & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'children'> & { href: string };

/** Enlace con aspecto de botón (navegación, no acciones). */
export function BotonEnlace({ variante = 'acero', icono, demo, children, className, ...resto }: BotonEnlaceProps) {
  return (
    <a {...resto} className={cx('t6-boton', `t6-boton--${variante}`, className)} data-demo={demo}>
      {icono}
      <span>{children}</span>
    </a>
  );
}
