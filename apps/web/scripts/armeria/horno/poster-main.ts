// Compone el póster: la sala en reposo (penumbra o «Más luz») a partir de los pases horneados, con el
// mismo compositor que el nivel B. Devuelve WebP en base64 a 1920 y 960 px. Lo abre scripts/armeria/poster.mjs.
import { colors } from '@taller6mm/ui/tokens';
import type { Luz } from '../../../src/components/armeria/estado.ts';
import {
  crearCompositor,
  descargarPase,
  PASES_NEUTRALIZABLES,
  srgb,
} from '../../../src/components/armeria/nivel-b/compositor.ts';
import { parametrosReposo } from '../../../src/components/armeria/nivel-b/reposo.ts';
import { archivoPase, PASES_LUZ } from '../../../src/components/armeria/pases.ts';

const lienzo = document.getElementById('lienzo');
if (!(lienzo instanceof HTMLCanvasElement)) throw new Error('Falta #lienzo');
const gl = lienzo.getContext('webgl2', { alpha: false, antialias: false, preserveDrawingBuffer: true });
if (!gl) throw new Error('Sin WebGL2');
const compositor = crearCompositor(gl, srgb(colors['negro-pavonado']));

interface Poster {
  listo: boolean;
  componer: (luz: Luz, calidad: number) => Promise<{ ancho: number; base64: string }[]>;
}
declare global {
  interface Window {
    __poster?: Poster;
  }
}

async function cargar() {
  const imagenes: Record<string, ImageBitmap | null> = {};
  for (const pase of PASES_LUZ) imagenes[pase] = await descargarPase(`/pases/${archivoPase(pase)}`);
  // El póster no usa linterna ni parallax: los pases de datos son neutros.
  for (const pase of PASES_NEUTRALIZABLES) imagenes[pase] = null;
  compositor.subir(imagenes);
}

const aWebp = (canvas: HTMLCanvasElement, calidad: number) =>
  canvas.toDataURL('image/webp', calidad).replace(/^data:image\/webp;base64,/, '');

cargar().then(() => {
  window.__poster = {
    listo: true,
    async componer(luz, calidad) {
      gl.viewport(0, 0, lienzo.width, lienzo.height);
      compositor.pintar(parametrosReposo(luz, [lienzo.width, lienzo.height]));
      const salidas = [{ ancho: 1920, base64: aWebp(lienzo, calidad) }];
      const pequeno = document.createElement('canvas');
      pequeno.width = 960;
      pequeno.height = 540;
      pequeno.getContext('2d')?.drawImage(lienzo, 0, 0, 960, 540);
      salidas.push({ ancho: 960, base64: aWebp(pequeno, calidad) });
      return salidas;
    },
  };
});
