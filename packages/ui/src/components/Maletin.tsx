// Maletín (docs/02 §4.5): diálogo modal sobre `<dialog>` nativo. `showModal()` da trampa de foco,
// Escape y fondo inerte sin código propio; al cerrar, el foco vuelve al elemento que lo abrió.
// Clic en el fondo cierra (el botón «Cerrar» es la alternativa de teclado).
import { type ReactNode, useEffect, useId, useRef } from 'react';
import { IconoCruz } from './iconos.tsx';
import { cx } from './util.ts';

export interface MaletinProps {
  abierto: boolean;
  onCerrar: () => void;
  titulo: string;
  /** Pie con las acciones (botones). */
  acciones?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function Maletin({ abierto, onCerrar, titulo, acciones, className, children }: MaletinProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const tituloId = useId();

  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo || typeof dialogo.showModal !== 'function') return;
    if (abierto && !dialogo.open) dialogo.showModal();
    if (!abierto && dialogo.open) dialogo.close();
  }, [abierto]);

  return (
    // biome-ignore lint/a11y/useKeyWithClickEvents: clic en el fondo es un atajo de ratón; Escape y «Cerrar» cubren el teclado.
    <dialog
      ref={ref}
      className={cx('t6-maletin', className)}
      aria-labelledby={tituloId}
      onClose={onCerrar}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCerrar();
      }}
    >
      <div className="t6-maletin__marco">
        <header className="t6-maletin__cabecera">
          <h2 id={tituloId} className="t6-maletin__titulo">
            {titulo}
          </h2>
          <button type="button" className="t6-maletin__cerrar" onClick={onCerrar}>
            <IconoCruz />
            <span className="t6-sr">Cerrar</span>
          </button>
        </header>
        <div className="t6-maletin__cuerpo">{children}</div>
        {acciones ? <footer className="t6-maletin__pie">{acciones}</footer> : null}
      </div>
    </dialog>
  );
}
