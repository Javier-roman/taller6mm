// Avatar (docs/02 §4.3: la única «pastilla» redonda del sistema). Imagen del usuario o iniciales.
import { cx } from './util.ts';

export interface AvatarProps {
  nombre: string;
  /** Imagen del usuario (con su permiso). Sin ella, las iniciales. */
  src?: string;
  tamano?: 's' | 'm' | 'l';
  className?: string;
}

const iniciales = (nombre: string) =>
  nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');

export function Avatar({ nombre, src, tamano = 'm', className }: AvatarProps) {
  return (
    <span className={cx('t6-avatar', `t6-avatar--${tamano}`, className)}>
      {src ? (
        <img src={src} alt={nombre} loading="lazy" decoding="async" />
      ) : (
        <>
          <span aria-hidden="true">{iniciales(nombre)}</span>
          <span className="t6-sr">{nombre}</span>
        </>
      )}
    </span>
  );
}
