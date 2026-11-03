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

/**
 * Vigía de rendimiento (docs/02 §3.6: ≥ 30 FPS o póster). Mira los últimos 2 s de fotogramas seguidos
 * (un hueco de más de 1 s es reposo de la escena, que pinta bajo demanda, no un fotograma lento) y avisa
 * una sola vez si la media se queda por debajo del umbral durante 2,5 s. Cuenta también los fotogramas
 * largos: son justo los que delatan a un equipo que no llega (auditor-rendimiento).
 */
export function crearVigia(umbral = 30) {
  let desde = 0;
  let avisado = false;
  return (fotogramas: readonly number[], activo: boolean, ahora: number): boolean => {
    if (avisado || !activo) {
      desde = 0;
      return false;
    }
    let suma = 0;
    let n = 0;
    for (let i = fotogramas.length - 1; i >= 0 && suma < 2; i--) {
      const d = fotogramas[i] ?? 0;
      if (d > 1) break;
      suma += d;
      n++;
    }
    if (suma < 1.5 || n < 3) return false;
    if (n / suma >= umbral) {
      desde = 0;
      return false;
    }
    desde ||= ahora;
    if (ahora - desde < 2500) return false;
    avisado = true;
    return true;
  };
}
