// Tostada (docs/02 §4.5): avisos breves tras una acción. La región viva existe siempre (si no, los
// lectores de pantalla no anuncian lo que entra). WCAG 2.2.1: los errores y avisos no desaparecen
// solos; las demás se cierran tras `duracionMs` y el temporizador se pausa con puntero o foco encima.
import { type ReactNode, useEffect, useRef } from 'react';
import { IconoAlerta, IconoCheck, IconoCruz, IconoInfo } from './iconos.tsx';
import { cx } from './util.ts';

export type TonoTostada = 'info' | 'ok' | 'aviso' | 'error';

export interface TostadaDatos {
  id: string;
  tono: TonoTostada;
  texto: string;
  /** Cierre automático. Ignorado en `aviso` y `error`. */
  duracionMs?: number;
}

const ICONO: Record<TonoTostada, () => ReactNode> = {
  info: IconoInfo,
  ok: IconoCheck,
  aviso: IconoAlerta,
  error: IconoAlerta,
};

function Tostada({ datos, onCerrar }: { datos: TostadaDatos; onCerrar: (id: string) => void }) {
  const Icono = ICONO[datos.tono];
  const temporizador = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const automatica = datos.duracionMs !== undefined && datos.tono !== 'error' && datos.tono !== 'aviso';
  const arrancar = () => {
    if (!automatica) return;
    clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => onCerrar(datos.id), datos.duracionMs);
  };
  const parar = () => clearTimeout(temporizador.current);
  useEffect(() => {
    arrancar();
    return parar;
  }, [datos.id]);
  return (
    <li
      className={cx('t6-tostada', `t6-tostada--${datos.tono}`)}
      // El error se anuncia al instante (alert); el resto, sin interrumpir (status).
      role={datos.tono === 'error' ? 'alert' : 'status'}
      onMouseEnter={parar}
      onMouseLeave={arrancar}
      onFocus={parar}
      onBlur={arrancar}
    >
      <Icono />
      <p>{datos.texto}</p>
      <button type="button" className="t6-tostada__cerrar" onClick={() => onCerrar(datos.id)}>
        <IconoCruz />
        <span className="t6-sr">Cerrar aviso</span>
      </button>
    </li>
  );
}

export interface TostadasProps {
  tostadas: readonly TostadaDatos[];
  onCerrar: (id: string) => void;
}

export function Tostadas({ tostadas, onCerrar }: TostadasProps) {
  return (
    <section className="t6-tostadas" aria-label="Avisos">
      <ul>
        {tostadas.map((t) => (
          <Tostada key={t.id} datos={t} onCerrar={onCerrar} />
        ))}
      </ul>
    </section>
  );
}
