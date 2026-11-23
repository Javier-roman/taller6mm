// Utilidades comunes de Campo y Selector: etiqueta, ayuda y error enlazados con aria-describedby.
import { type ReactNode, useId } from 'react';
import { Cargador } from './Cargador.tsx';
import { IconoAlerta } from './iconos.tsx';

export interface CampoComun {
  /** Texto de la etiqueta, siempre visible (un placeholder no es una etiqueta). */
  etiqueta: string;
  /** Formato esperado o ayuda. Va enlazada al control. */
  ayuda?: string | undefined;
  /** Qué falló y cómo arreglarlo. Pone `aria-invalid`. */
  error?: string | undefined;
  /** Validación o carga de opciones en curso: avisa sin quitar el foco. */
  cargando?: boolean | undefined;
  /** Solo para /sistema: fuerza la apariencia de foco. */
  demo?: 'foco' | undefined;
}

export function useCampoIds(error?: string, ayuda?: string, cargando?: boolean) {
  const base = useId();
  const ids = { control: `${base}-c`, ayuda: `${base}-a`, error: `${base}-e`, carga: `${base}-l` };
  const describedBy =
    [ayuda ? ids.ayuda : null, error ? ids.error : null, cargando ? ids.carga : null].filter(Boolean).join(' ') ||
    undefined;
  return { ids, describedBy };
}

export function CampoMarco({
  ids,
  etiqueta,
  ayuda,
  error,
  cargando,
  obligatorio,
  deshabilitado,
  demo,
  children,
}: CampoComun & {
  ids: ReturnType<typeof useCampoIds>['ids'];
  obligatorio?: boolean;
  deshabilitado?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className="t6-campo"
      data-estado={error ? 'error' : cargando ? 'carga' : deshabilitado ? 'deshabilitado' : undefined}
      data-demo={demo}
    >
      <label className="t6-campo__etiqueta" htmlFor={ids.control}>
        {etiqueta}
        {obligatorio ? <span className="t6-campo__obligatorio"> (obligatorio)</span> : null}
      </label>
      {children}
      {ayuda ? (
        <p id={ids.ayuda} className="t6-mensaje">
          {ayuda}
        </p>
      ) : null}
      {cargando ? (
        <div id={ids.carga} className="t6-mensaje">
          <Cargador etiqueta="Comprobando…" />
        </div>
      ) : null}
      {error ? (
        <p id={ids.error} className="t6-mensaje t6-mensaje--error">
          <IconoAlerta />
          {error}
        </p>
      ) : null}
    </div>
  );
}
