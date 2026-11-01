// Canal entre la interfaz (React) y la escena (A o B): estado que cambia en cada fotograma o en cada
// evento de scroll y que no debe provocar renders de React. Sin three.js: va en el chunk inicial.
import type { Director } from './director.ts';

export interface CanalEscena {
  director: Director | null;
  /** Posición del carrusel móvil en «zonas» (0 = primera; admite decimales mientras se desliza). */
  progreso: number;
  /** Pide un fotograma (las escenas pintan bajo demanda). */
  pintar: () => void;
  /** Duración de los últimos fotogramas (s), para medir FPS y para caer al póster si va lenta. */
  fotogramas: number[];
}

export const crearCanal = (): CanalEscena => ({ director: null, progreso: 0, pintar: () => undefined, fotogramas: [] });
