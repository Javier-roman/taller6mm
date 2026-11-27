// Fuentes de los rótulos dibujados en canvas (IBM Plex Sans Condensed para títulos e IBM Plex Mono para medidas y
// cotas, ADR-0010). Módulo aparte y sin three.js para poder esperarlas antes de pedir el chunk 3D.
import { FONT_FAMILIES } from '@taller6mm/ui/tokens';

/** Espera a que las fuentes de los rótulos estén listas antes de dibujarlos en el canvas. */
export async function fuentesListas() {
  if (typeof document === 'undefined' || !('fonts' in document)) return;
  await Promise.all([
    document.fonts.load(`700 64px ${FONT_FAMILIES.rotulo}`),
    document.fonts.load(`600 64px ${FONT_FAMILIES.grabado}`),
    document.fonts.load(`400 32px ${FONT_FAMILIES.datos}`),
    document.fonts.load(`500 32px ${FONT_FAMILIES.datos}`),
    document.fonts.load(`600 32px ${FONT_FAMILIES.datos}`),
    document.fonts.load(`700 32px ${FONT_FAMILIES.datos}`),
  ]).catch(() => undefined);
}
