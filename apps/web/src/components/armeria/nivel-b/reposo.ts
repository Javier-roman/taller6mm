// La sala en reposo para el compositor del nivel B: sin intro, sin linterna y sin zona activa. Es lo que se
// ve en el póster y lo que enseña el nivel B cuando nada se mueve, así que póster, vista ligera y B son la
// misma sala (critico-diseno, 05-11-2026).
import type { Luz } from '../estado.ts';
import { VARIANTES_LUZ } from '../luz.ts';
import { type ParametrosPintado, razonDeColor, type V2 } from './compositor.ts';

/** Los pases se hornearon con los tubos de «penumbra»: otra luz tiñe con la razón de colores. */
export const tinteDe = (luz: Luz) => razonDeColor(VARIANTES_LUZ[luz].colorTubo, VARIANTES_LUZ.penumbra.colorTubo);

export function parametrosReposo(
  luz: Luz,
  resolucion: V2,
  visible: V2 = [1, 1],
  centro: V2 = [0.5, 0.5],
): ParametrosPintado {
  const v = VARIANTES_LUZ[luz];
  return {
    centro,
    visible,
    parallax: [0, 0],
    linterna: [0.5, 0.5],
    linternaNivel: 0,
    resolucion,
    tubos: [v.reposo, v.reposo, v.reposo],
    tubosResplandor: [v.reposo, v.reposo, v.reposo],
    tinte: tinteDe(luz),
    ambiente: v.ambiente,
    calidas: v.calidas,
    rotulos: 1,
    rectActivo: [0, 0, 0, 0],
    filaActiva: -1,
    extra: 0,
    acento: 0,
    tiempo: 0,
  };
}
