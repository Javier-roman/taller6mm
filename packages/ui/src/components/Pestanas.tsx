// Pestañas (docs/02 §4.5), patrón WAI-ARIA tabs con activación automática: flechas, Inicio y Fin
// mueven el foco y la selección; solo la pestaña activa está en el orden de tabulación. Las
// desactivadas se saltan. Es una isla: necesita JS, pero renderiza en servidor el panel activo.
import { type KeyboardEvent, type ReactNode, useId, useRef, useState } from 'react';
import { cx } from './util.ts';

export interface Pestana {
  id: string;
  titulo: string;
  panel: ReactNode;
  desactivada?: boolean;
}

export interface PestanasProps {
  /** Nombre accesible del grupo de pestañas. */
  etiqueta: string;
  pestanas: readonly Pestana[];
  inicial?: string;
  className?: string;
}

export function Pestanas({ etiqueta, pestanas, inicial, className }: PestanasProps) {
  const base = useId();
  const habilitadas = pestanas.filter((p) => !p.desactivada);
  const [activa, setActiva] = useState(inicial ?? habilitadas[0]?.id);
  const refs = useRef(new Map<string, HTMLButtonElement>());

  const mover = (e: KeyboardEvent<HTMLButtonElement>, actual: string) => {
    const i = habilitadas.findIndex((p) => p.id === actual);
    const siguiente =
      e.key === 'ArrowRight'
        ? habilitadas[(i + 1) % habilitadas.length]
        : e.key === 'ArrowLeft'
          ? habilitadas[(i - 1 + habilitadas.length) % habilitadas.length]
          : e.key === 'Home'
            ? habilitadas[0]
            : e.key === 'End'
              ? habilitadas.at(-1)
              : undefined;
    if (!siguiente) return;
    e.preventDefault();
    setActiva(siguiente.id);
    refs.current.get(siguiente.id)?.focus();
  };

  return (
    <div className={cx('t6-pestanas', className)}>
      <div role="tablist" aria-label={etiqueta} className="t6-pestanas__lista">
        {pestanas.map((p) => {
          const seleccionada = p.id === activa;
          return (
            <button
              key={p.id}
              ref={(el) => {
                if (el) refs.current.set(p.id, el);
                else refs.current.delete(p.id);
              }}
              type="button"
              role="tab"
              id={`${base}-${p.id}-t`}
              aria-selected={seleccionada}
              aria-controls={`${base}-${p.id}-p`}
              tabIndex={seleccionada ? 0 : -1}
              disabled={p.desactivada}
              className="t6-pestanas__pestana"
              onClick={() => setActiva(p.id)}
              onKeyDown={(e) => mover(e, p.id)}
            >
              {p.titulo}
            </button>
          );
        })}
      </div>
      {pestanas.map((p) => (
        <div
          key={p.id}
          role="tabpanel"
          id={`${base}-${p.id}-p`}
          aria-labelledby={`${base}-${p.id}-t`}
          hidden={p.id !== activa}
          // biome-ignore lint/a11y/noNoninteractiveTabindex: WAI-ARIA: el panel entra en la tabulación si no tiene nada enfocable.
          tabIndex={0}
          className="t6-pestanas__panel"
        >
          {p.id === activa ? p.panel : null}
        </div>
      ))}
    </div>
  );
}
