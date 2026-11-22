// Ficha de pieza (docs/02 §4.5): miniatura, nombre, «desde X €», nº de tiendas y compatibilidad.
// Con `href`, toda la ficha se puede pulsar pero el foco es uno solo (el del nombre). El nivel de
// fidelidad acompaña siempre a la imagen (principio 1) y el precio a su fecha (principio 2).
import type { ReactNode } from 'react';
import { EtiquetaPrecio, type EtiquetaPrecioProps } from './EtiquetaPrecio.tsx';
import { InsigniaCompatibilidad, type InsigniaCompatibilidadProps } from './InsigniaCompatibilidad.tsx';
import { InsigniaFidelidad, type NivelFidelidad } from './InsigniaFidelidad.tsx';
import { IconoAlerta, IconoFoto } from './iconos.tsx';
import { cx, type EstadoDemo } from './util.ts';

export interface FichaPiezaProps {
  nombre: string;
  marca: string;
  href?: string;
  /** Imagen propia o cedida (docs/05): nunca fotos de terceros. Sin ella, marcador a plantilla. */
  miniatura?: { src: string; alt: string };
  /** Nivel de la imagen mostrada; `null` si no se ha verificado. */
  nivel: NivelFidelidad | null;
  /** Mejor precio. `null`: ninguna tienda lo publica. */
  precio: Pick<EtiquetaPrecioProps, 'centimos' | 'comprobado' | 'ahora'> | null;
  tiendas: number | null;
  compatibilidad?: Pick<InsigniaCompatibilidadProps, 'veredicto' | 'motivo' | 'fuente' | 'confianza'>;
  estado?: 'listo' | 'carga' | 'error' | 'deshabilitada';
  mensaje?: string;
  nivelTitulo?: 2 | 3 | 4;
  demo?: EstadoDemo;
  className?: string;
  children?: ReactNode;
}

export function FichaPieza({
  nombre,
  marca,
  href,
  miniatura,
  nivel,
  precio,
  tiendas,
  compatibilidad,
  estado = 'listo',
  mensaje,
  nivelTitulo = 3,
  demo,
  className,
}: FichaPiezaProps) {
  const Titulo = `h${nivelTitulo}` as const;
  const enlace = href !== undefined && estado === 'listo';
  if (estado === 'carga') {
    return (
      <article className={cx('t6-ficha', className)} aria-busy="true" aria-label="Cargando pieza">
        <span className="t6-sr" role="status">
          Cargando pieza…
        </span>
        <span className="t6-ficha__imagen t6-esqueleto" aria-hidden="true" />
        <div className="t6-ficha__cuerpo" aria-hidden="true">
          <span className="t6-esqueleto" />
          <span className="t6-esqueleto t6-esqueleto--corto" />
        </div>
      </article>
    );
  }
  return (
    <article
      className={cx('t6-ficha', enlace && 't6-ficha--enlace', className)}
      data-estado={estado === 'listo' ? undefined : estado}
      data-demo={demo}
    >
      <div className="t6-ficha__imagen">
        {miniatura ? (
          <img src={miniatura.src} alt={miniatura.alt} width="320" height="200" loading="lazy" decoding="async" />
        ) : (
          <span className="t6-ficha__vacio">
            <IconoFoto />
            Sin imagen
          </span>
        )}
        <InsigniaFidelidad nivel={nivel} compacta className="t6-ficha__nivel" />
      </div>
      <div className="t6-ficha__cuerpo">
        <p className="t6-ficha__marca">{marca}</p>
        <Titulo className="t6-ficha__nombre">
          {enlace ? (
            <a className="t6-ficha__enlace" href={href}>
              {nombre}
            </a>
          ) : (
            nombre
          )}
        </Titulo>
        {estado === 'error' ? (
          <p className="t6-mensaje t6-mensaje--error">
            <IconoAlerta />
            {mensaje ?? 'No se ha podido cargar la pieza. Inténtalo de nuevo en unos minutos.'}
          </p>
        ) : estado === 'deshabilitada' ? (
          <p className="t6-mensaje">{mensaje ?? 'No disponible por ahora.'}</p>
        ) : (
          <>
            {precio ? (
              <EtiquetaPrecio
                compacta
                desde
                centimos={precio.centimos}
                comprobado={precio.comprobado}
                ahora={precio.ahora}
                tienda=""
                stock="desconocido"
              />
            ) : (
              <p className="t6-mensaje t6-mensaje--desconocido">Sin precio en ninguna tienda</p>
            )}
            <p className="t6-ficha__tiendas">
              {tiendas === null ? 'Nº de tiendas desconocido' : `${tiendas} ${tiendas === 1 ? 'tienda' : 'tiendas'}`}
            </p>
            {compatibilidad ? <InsigniaCompatibilidad compacta {...compatibilidad} /> : null}
          </>
        )}
      </div>
    </article>
  );
}
