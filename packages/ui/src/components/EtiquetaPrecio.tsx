// Etiqueta de precio (docs/02 §4.5): precio, tienda, «comprobado hace X» y estado de stock.
// Principio 2: `comprobado` es obligatoria en el tipo (ISO UTC o `null` si no se sabe) y un precio
// desconocido es `null`, nunca 0. Dinero en céntimos enteros.
import { formatearComprobado, formatearDato } from './formato.ts';
import { IconoDesconocido } from './iconos.tsx';
import { type EstadoStock, PuntoStock } from './PuntoStock.tsx';
import { cx } from './util.ts';

export interface EtiquetaPrecioProps {
  /** Céntimos de euro, o `null` si la tienda no publica precio. */
  centimos: number | null;
  tienda: string;
  /** ISO 8601 UTC de la última comprobación, o `null` si no consta. Obligatoria, sin valor por defecto. */
  comprobado: string | null;
  /** Momento de referencia (ISO) para «hace 3 h». Sin él, la fecha absoluta. */
  ahora?: string | undefined;
  stock: EstadoStock;
  /** «Desde» cuando es el mínimo de varias tiendas. */
  desde?: boolean;
  /** Versión sin tienda ni stock, para fichas. */
  compacta?: boolean;
  /** Enlace a la tienda (rel y target seguros). */
  href?: string;
  cargando?: boolean;
  className?: string;
}

export function EtiquetaPrecio({
  centimos,
  tienda,
  comprobado,
  ahora,
  stock,
  desde = false,
  compacta = false,
  href,
  cargando = false,
  className,
}: EtiquetaPrecioProps) {
  const comp = comprobado ? formatearComprobado(comprobado, ahora) : null;
  const precio =
    centimos === null ? (
      <span className="t6-precio__importe t6-precio__importe--sin">
        <IconoDesconocido />
        Sin precio
      </span>
    ) : (
      <span className="t6-precio__importe">
        {desde ? <span className="t6-precio__desde">desde </span> : null}
        <data value={centimos}>{formatearDato(centimos, 'eur')}</data>
      </span>
    );
  const nombreTienda = href ? (
    <a href={href} rel="noopener noreferrer" target="_blank">
      {tienda}
      <span className="t6-sr"> (se abre en una pestaña nueva)</span>
    </a>
  ) : (
    tienda
  );
  return (
    <div className={cx('t6-precio', compacta && 't6-precio--compacta', className)} aria-busy={cargando || undefined}>
      {cargando ? (
        <>
          <span className="t6-sr" role="status">
            Cargando precio…
          </span>
          <span className="t6-esqueleto" aria-hidden="true" />
        </>
      ) : (
        <>
          {precio}
          {compacta ? null : <span className="t6-precio__tienda">{nombreTienda}</span>}
          {compacta ? null : <PuntoStock estado={stock} />}
          <span className="t6-precio__fecha">
            {comp ? (
              <>
                Comprobado{' '}
                <time dateTime={comp.iso} title={comp.completo}>
                  {comp.texto}
                </time>
              </>
            ) : (
              <>
                <IconoDesconocido />
                Sin fecha de comprobación
              </>
            )}
          </span>
        </>
      )}
    </div>
  );
}
