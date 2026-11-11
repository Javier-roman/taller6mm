// Fin de la semana de Fable (Javi, 10-11-2026): su plan Pro incluye Fable hasta el 16-11-2026 a las 23:59
// (hora de Madrid, CET = UTC+1, es decir hasta 2026-11-16T22:59:59Z). Pasada esa fecha, el asesor `fable`
// de .claude/settings.local.json (que no se sube) se quita solo y se avisa. Lógica pura con el reloj y el
// archivo inyectables: se prueba en fable-fin.test.mjs, nunca contra el archivo real.
import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs';

/** Instante exacto en que acaba la semana de Fable. */
export const FIN_FABLE = Date.parse('2026-11-16T22:59:59Z');

/** `fable`, `claude-fable-5-2`, `claude-fable-5-1[1m]`… */
export const esFable = (v) => typeof v === 'string' && /fable/i.test(v);

/**
 * Quita `advisorModel` de `archivo` si vale Fable y ya pasó el plazo. Nunca lanza: devuelve
 * { cambio: 'quitado' | 'ninguno' | 'error', mensaje? }. Conserva el resto de claves y es idempotente.
 */
export function quitarAsesorFable(archivo, ahora = Date.now(), fin = FIN_FABLE) {
  try {
    if (ahora <= fin || !existsSync(archivo)) return { cambio: 'ninguno' };
    let datos;
    try {
      datos = JSON.parse(readFileSync(archivo, 'utf8'));
    } catch {
      return {
        cambio: 'error',
        mensaje: 'settings.local.json no es JSON válido: no he podido quitar el asesor Fable.',
      };
    }
    if (!datos || typeof datos !== 'object' || Array.isArray(datos)) return { cambio: 'ninguno' };
    // Esta semana Fable es el modelo principal (`model`) y el asesor (`advisorModel`): se quitan los dos.
    const resto = { ...datos };
    let quitado = false;
    for (const clave of ['advisorModel', 'model']) {
      if (esFable(resto[clave])) {
        delete resto[clave];
        quitado = true;
      }
    }
    if (!quitado) return { cambio: 'ninguno' };
    const tmp = `${archivo}.tmp`;
    writeFileSync(tmp, `${JSON.stringify(resto, null, 2)}\n`);
    renameSync(tmp, archivo);
    return {
      cambio: 'quitado',
      mensaje:
        'Ha terminado la semana de Fable (16-11-2026, 23:59 de Madrid): he quitado Fable (modelo principal y asesor) de .claude/settings.local.json. ' +
        'Reinicia Claude Code para que se aplique y no uses `model: fable` en ningún subagente.',
    };
  } catch {
    return { cambio: 'error', mensaje: 'No he podido quitar el asesor Fable de settings.local.json: quítalo a mano.' };
  }
}

/** Aviso (sin cambiar nada) si pasó el plazo y quedara Fable en algún ajuste. */
export function haPasadoElPlazo(ahora = Date.now(), fin = FIN_FABLE) {
  return ahora > fin;
}
