// Campo de texto (docs/02 §4.5): etiqueta visible, ayuda y error enlazados, objetivo de 44 px.
// Estados: normal, foco, deshabilitado, error (aria-invalid) y carga (aria-busy, no bloquea el foco).
import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react';
import { type CampoComun, CampoMarco, useCampoIds } from './CampoMarco.tsx';
import { cx } from './util.ts';

type Base = CampoComun & { multilinea?: false } & Omit<InputHTMLAttributes<HTMLInputElement>, 'id' | 'size'>;
type Multi = CampoComun & { multilinea: true } & Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'>;
export type CampoProps = Base | Multi;

export function Campo(props: CampoProps) {
  const { etiqueta, ayuda, error, cargando, demo, className, multilinea, ...resto } = props;
  const { ids, describedBy } = useCampoIds(error, ayuda, cargando);
  const comunes = {
    id: ids.control,
    className: cx('t6-campo__control', className),
    'aria-invalid': error ? (true as const) : undefined,
    'aria-describedby': describedBy,
    'aria-busy': cargando || undefined,
  };
  return (
    <CampoMarco
      ids={ids}
      etiqueta={etiqueta}
      ayuda={ayuda}
      error={error}
      cargando={cargando}
      demo={demo}
      obligatorio={Boolean(resto.required)}
      deshabilitado={Boolean(resto.disabled)}
    >
      {multilinea ? (
        <textarea
          {...(resto as TextareaHTMLAttributes<HTMLTextAreaElement>)}
          {...comunes}
          rows={(resto as TextareaHTMLAttributes<HTMLTextAreaElement>).rows ?? 3}
        />
      ) : (
        <input {...(resto as InputHTMLAttributes<HTMLInputElement>)} {...comunes} />
      )}
    </CampoMarco>
  );
}
