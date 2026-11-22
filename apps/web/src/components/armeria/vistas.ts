// URLs de las vistas horneadas de La Armería (póster y pases del nivel B). El manifiesto lo escribe
// scripts/armeria/vistas.mjs a partir de los binarios (que no están en git); la ruta lleva el hash del
// conjunto, así que cada versión es inmutable y el Worker la sirve desde R2 con caché de un año (src/lib/vistas.ts).
import { rutaVista } from '../../lib/vistas.ts';
import type { Luz } from './estado.ts';
import manifiesto from './vistas.json';

export const HASH_VISTAS: string = manifiesto.hash;

/** Ruta pública de una vista del conjunto actual, p. ej. `urlVista('poster-1920.webp')`. */
export const urlVista = (nombre: string): string => rutaVista(HASH_VISTAS, nombre);

/** El póster de cada luz: horneado aparte (no es un filtro), con la misma sala y la misma temperatura de luz. */
export function posterDe(luz: Luz) {
  const nombre = luz === 'mas-luz' ? 'poster-mas-luz' : 'poster';
  return {
    ancho: 1920,
    alto: 1080,
    src: urlVista(`${nombre}-1920.webp`),
    srcSet: `${urlVista(`${nombre}-960.webp`)} 960w, ${urlVista(`${nombre}-1920.webp`)} 1920w`,
  } as const;
}
