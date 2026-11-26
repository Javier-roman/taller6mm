// Tabla de datos (docs/02 §4.5): `<table>` real con `caption`, cabeceras con `scope` y la primera
// columna como cabecera de fila. La región desplazable es enfocable para poder recorrerla con
// teclado cuando desborda. Estados: listo, carga, vacía y error.
import { type ReactNode, useId } from 'react';
import { IconoAlerta } from './iconos.tsx';
import { cx } from './util.ts';

export interface ColumnaTabla {
  id: string;
  titulo: string;
  /** Números y precios: alineados a la derecha, en la fuente de datos. */
  numerica?: boolean;
}

export interface TablaProps {
  /** Nombre accesible de la tabla (visible). */
  titulo: string;
  columnas: readonly ColumnaTabla[];
  filas: ReadonlyArray<{ id: string; celdas: Readonly<Record<string, ReactNode>> }>;
  estado?: 'listo' | 'carga' | 'error';
  /** Texto de vacío o de error. */
  mensaje?: string;
  className?: string;
}

export function Tabla({ titulo, columnas, filas, estado = 'listo', mensaje, className }: TablaProps) {
  const tituloId = `${useId()}-t`;
  const vacia = estado === 'listo' && filas.length === 0;
  return (
    <section
      className={cx('t6-tabla', className)}
      aria-labelledby={tituloId}
      // biome-ignore lint/a11y/noNoninteractiveTabindex: región desplazable con nombre; sin foco no se lee con teclado.
      tabIndex={0}
      data-estado={estado === 'listo' ? undefined : estado}
    >
      <table aria-busy={estado === 'carga' || undefined}>
        <caption id={tituloId}>{titulo}</caption>
        <thead>
          <tr>
            {columnas.map((c) => (
              <th key={c.id} scope="col" className={c.numerica ? 't6-tabla__num' : undefined}>
                {c.titulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {estado === 'carga' ? (
            [0, 1, 2].map((i) => (
              <tr key={i}>
                {columnas.map((c) => (
                  <td key={c.id}>
                    <span className="t6-esqueleto" aria-hidden="true" />
                  </td>
                ))}
              </tr>
            ))
          ) : estado === 'error' || vacia ? (
            <tr>
              <td colSpan={columnas.length}>
                <p className={cx('t6-mensaje', estado === 'error' && 't6-mensaje--error')}>
                  {estado === 'error' ? <IconoAlerta /> : null}
                  {mensaje ??
                    (estado === 'error'
                      ? 'No se han podido cargar los datos. Inténtalo de nuevo en unos minutos.'
                      : 'No hay datos que mostrar.')}
                </p>
              </td>
            </tr>
          ) : (
            filas.map((f) => (
              <tr key={f.id}>
                {columnas.map((c, i) =>
                  i === 0 ? (
                    <th key={c.id} scope="row">
                      {f.celdas[c.id]}
                    </th>
                  ) : (
                    <td key={c.id} className={c.numerica ? 't6-tabla__num' : undefined}>
                      {f.celdas[c.id]}
                    </td>
                  ),
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {estado === 'carga' ? (
        <span className="t6-sr" role="status">
          Cargando datos…
        </span>
      ) : null}
    </section>
  );
}
