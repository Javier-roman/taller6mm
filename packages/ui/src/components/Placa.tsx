// Placa (docs/02 §4.3 y §4.5): panel de grafito con ruido sutil, borde de acero, brillo interior y
// tornillos en las esquinas. Con `href` toda la placa es un enlace (un solo foco: el del título).
// Estados: hover, foco, activo (si es enlace), carga, error y deshabilitada.
import { type ReactNode, useId } from 'react';
import { IconoAlerta } from './iconos.tsx';
import { cx, type EstadoDemo } from './util.ts';

export type EstadoPlaca = 'listo' | 'carga' | 'error' | 'deshabilitada';

export interface PlacaProps {
  titulo: ReactNode;
  nivelTitulo?: 2 | 3 | 4;
  /** Código grabado en la esquina («PL-01»), en la fuente de datos. */
  codigo?: string;
  href?: string;
  estado?: EstadoPlaca;
  /** Error: qué falló y qué hacer. Deshabilitada: por qué no está disponible. */
  mensaje?: string;
  /** Sin tornillos, para placas pequeñas o anidadas. */
  lisa?: boolean;
  as?: 'section' | 'article' | 'div';
  /** Solo para /sistema: fuerza la apariencia de hover, activo o foco. */
  demo?: EstadoDemo;
  className?: string;
  children?: ReactNode;
}

export function Placa({
  titulo,
  nivelTitulo = 3,
  codigo,
  href,
  estado = 'listo',
  mensaje,
  lisa = false,
  as,
  demo,
  className,
  children,
}: PlacaProps) {
  const tituloId = `${useId()}-titulo`;
  const enlace = href !== undefined && estado !== 'deshabilitada';
  const Tag = as ?? (href ? 'article' : 'section');
  const Titulo = `h${nivelTitulo}` as const;
  return (
    <Tag
      className={cx('t6-placa', enlace && 't6-placa--enlace', lisa && 't6-placa--lisa', className)}
      data-estado={estado === 'listo' ? undefined : estado}
      data-demo={demo}
      aria-busy={estado === 'carga' || undefined}
      aria-labelledby={Tag === 'div' ? undefined : tituloId}
    >
      <header className="t6-placa__cabecera">
        <Titulo id={tituloId} className="t6-placa__titulo">
          {enlace ? (
            <a className="t6-placa__enlace" href={href}>
              {titulo}
            </a>
          ) : (
            titulo
          )}
        </Titulo>
        {codigo ? <span className="t6-placa__codigo">{codigo}</span> : null}
      </header>
      <div className="t6-placa__cuerpo">
        {estado === 'carga' ? (
          <>
            <span className="t6-sr" role="status">
              Cargando…
            </span>
            <span className="t6-esqueleto" aria-hidden="true" />
            <span className="t6-esqueleto t6-esqueleto--corto" aria-hidden="true" />
          </>
        ) : (
          children
        )}
        {estado === 'error' ? (
          <p className="t6-mensaje t6-mensaje--error">
            <IconoAlerta />
            {mensaje ?? 'No se ha podido cargar. Inténtalo de nuevo en unos minutos.'}
          </p>
        ) : null}
        {estado === 'deshabilitada' && mensaje ? <p className="t6-mensaje">{mensaje}</p> : null}
      </div>
    </Tag>
  );
}
