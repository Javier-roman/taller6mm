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
      // Se compone una sola vez a 2560 × 1440 y se reduce a 1920 y 960 (escritorio con escala del 125–150 %
      // necesita más de 1920 px físicos; el 960 es para anchos pequeños).
      gl.viewport(0, 0, lienzo.width, lienzo.height);
      compositor.pintar(parametrosReposo(luz, [lienzo.width, lienzo.height]));
      const salidas = [{ ancho: 2560, base64: aWebp(lienzo, calidad) }];
      for (const ancho of [1920, 960]) {
        const reducido = document.createElement('canvas');
        reducido.width = ancho;
        reducido.height = Math.round((ancho * 9) / 16);
        const ctx = reducido.getContext('2d');
        if (!ctx) throw new Error('Canvas 2D no disponible');
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(lienzo, 0, 0, reducido.width, reducido.height);
        salidas.push({ ancho, base64: aWebp(reducido, calidad) });
      }
      return salidas;
    },
  };
});
