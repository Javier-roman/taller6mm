// Póster de La Armería: la composición en reposo de la sala (Cycles) como <img> en el HTML inicial, con las
// zonas clicables encima. Es el primer pintado (LCP), la vista ligera y la caída de los niveles B y A.

import type { Luz } from './estado.ts';
import { SOCKETS } from './sockets.ts';
import type { Acciones } from './useArmeria.ts';
import { posterDe } from './vistas.ts';
import { ZONAS } from './zonas.ts';

export const TEXTO_ALTERNATIVO =
  'La Armería en penumbra: tres cuerpos de compactus verde oliva sobre raíles. A la izquierda, Catálogo (armero de réplicas y almacén de accesorios); en el centro, la vitrina de la comunidad y el banco de trabajo con su flexo; a la derecha, Mercado (tablón, mostrador de tiendas, manuales y taquilla).';

export interface PosterProps {
  acciones: Pick<Acciones, 'apuntar' | 'abrir'>;
  /** Penumbra (por defecto) o «Más luz»: cada una tiene su póster horneado. */
  luz?: Luz;
  /** Una escena (B o A) ya pinta por encima: el póster se oculta. */
  oculto?: boolean;
}

export function Poster({ acciones, luz = 'penumbra', oculto = false }: PosterProps) {
  const poster = posterDe(luz);
  return (
    <div className="armeria-poster" data-oculto={oculto}>
      <div className="armeria-poster__lienzo">
        <img
          className="armeria-poster__imagen"
          src={poster.src}
          srcSet={poster.srcSet}
          sizes="100vw"
          width={poster.ancho}
          height={poster.alto}
          alt={TEXTO_ALTERNATIVO}
          fetchPriority="high"
          decoding="async"
        />
        {/* Zonas clicables para ratón: fuera del árbol de accesibilidad y del tabulador. El teclado y los
            lectores de pantalla usan los mismos enlaces, con su nombre, en la navegación. */}
        <div className="armeria-poster__zonas" aria-hidden="true">
          {ZONAS.map((zona) => (
            <a
              key={zona.id}
              href={zona.ruta}
              className="armeria-poster__zona"
              data-zona={zona.id}
              tabIndex={-1}
              onPointerEnter={() => acciones.apuntar(zona.id)}
              onPointerLeave={() => acciones.apuntar(null)}
              onClick={(e) => {
                e.preventDefault();
                acciones.abrir(zona.id);
              }}
            >
              <span className="armeria-poster__zona-nombre">{zona.nombre}</span>
            </a>
          ))}
        </div>
        {/* Huecos de las réplicas: vacíos hasta que haya imágenes reales (sockets.ts). Sin siluetas de relleno. */}
        <div className="armeria-poster__sockets" aria-hidden="true">
          {SOCKETS.map((socket) => (
            <span
              key={socket.id}
              className="armeria-poster__socket"
              data-socket={socket.id}
              data-vacio={socket.replicaId === null}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
