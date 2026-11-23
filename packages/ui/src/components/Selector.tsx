// Selector (docs/02 §4.5): `<select>` nativo con el aspecto del sistema. Lo nativo da teclado,
// lectores de pantalla y móvil gratis. Los mismos estados que Campo.
import type { SelectHTMLAttributes } from 'react';
import { type CampoComun, CampoMarco, useCampoIds } from './CampoMarco.tsx';
import { cx } from './util.ts';

export interface OpcionSelector {
  valor: string;
  texto: string;
  deshabilitada?: boolean;
}

export type SelectorProps = CampoComun & {
  opciones: readonly OpcionSelector[];
  /** Primera opción vacía («Elige una marca»). */
  marcador?: string;
} & Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id' | 'children'>;

export function Selector({
  etiqueta,
  ayuda,
  error,
  cargando,
  demo,
  opciones,
  marcador,
  className,
  ...resto
}: SelectorProps) {
  const { ids, describedBy } = useCampoIds(error, ayuda, cargando);
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
      <select
        {...resto}
        id={ids.control}
        className={cx('t6-campo__control t6-campo__control--selector', className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        aria-busy={cargando || undefined}
      >
        {marcador ? <option value="">{marcador}</option> : null}
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor} disabled={o.deshabilitada}>
            {o.texto}
          </option>
        ))}
      </select>
    </CampoMarco>
  );
}
