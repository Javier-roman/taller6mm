// Tooltip (docs/02 §4.5), WCAG 1.4.13: aparece con hover y con foco, se puede cerrar con Escape sin
// mover el foco, y el puntero puede pasar sobre él sin que desaparezca. Solo para información
// complementaria: lo esencial va siempre en el texto visible.
import { cloneElement, type ReactElement, useId, useState } from 'react';
import { cx } from './util.ts';

export interface TooltipProps {
  texto: string;
  /** Un único elemento enfocable (botón, enlace); recibe `aria-describedby`. */
  children: ReactElement<{ 'aria-describedby'?: string }>;
  /** Solo para /sistema: lo deja visible. */
  demo?: boolean;
  className?: string;
}

export function Tooltip({ texto, children, demo = false, className }: TooltipProps) {
  const id = useId();
  const [descartado, setDescartado] = useState(false);
  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: solo escucha Escape que burbujea desde el disparador enfocable.
    <span
      className={cx('t6-tooltip', className)}
      data-descartado={descartado || undefined}
      data-demo={demo ? '' : undefined}
      onMouseEnter={() => setDescartado(false)}
      onFocus={() => setDescartado(false)}
      onKeyDown={(e) => {
        if (e.key === 'Escape') setDescartado(true);
      }}
    >
      {cloneElement(children, { 'aria-describedby': id })}
      <span role="tooltip" id={id} className="t6-tooltip__texto">
        {texto}
      </span>
    </span>
  );
}
