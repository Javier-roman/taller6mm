// Póster de La Armería: la composición en reposo de la sala (Cycles) como <img> en el HTML inicial, con las
// zonas clicables encima. Es el primer pintado (LCP), la vista ligera y la caída de los niveles B y A.
import type { Acciones } from './useArmeria.ts';
import { POSTER } from './vistas.ts';
import { ZONAS } from './zonas.ts';

export const TEXTO_ALTERNATIVO =
  'La Armería en penumbra: tres cuerpos de compactus verde oliva sobre raíles. A la izquierda, Catálogo (armero de réplicas y almacén de accesorios); en el centro, la vitrina de la comunidad y el banco de trabajo con su flexo; a la derecha, Mercado (tablón, mostrador de tiendas, manuales y taquilla).';

export interface PosterProps {
  acciones: Pick<Acciones, 'apuntar' | 'abrir'>;
  /** Una escena (B o A) ya pinta por encima: el póster se oculta. */
  oculto?: boolean;
}

export function Poster({ acciones, oculto = false }: PosterProps) {
  return (
    <div className="armeria-poster" data-oculto={oculto}>
      <div className="armeria-poster__lienzo">
        <img
          className="armeria-poster__imagen"
          src={POSTER.src}
          srcSet={POSTER.srcSet}
          sizes="100vw"
          width={POSTER.ancho}
          height={POSTER.alto}
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
      </div>
    </div>
  );
}
