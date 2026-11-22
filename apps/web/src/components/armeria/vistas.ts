// URLs de las vistas horneadas de La Armería (póster y pases del nivel B). El manifiesto lo escribe
// scripts/armeria/vistas.mjs a partir de los binarios (que no están en git); la ruta lleva el hash del
// conjunto, así que cada versión es inmutable y el Worker la sirve desde R2 con caché de un año (src/lib/vistas.ts).
import { rutaVista } from '../../lib/vistas.ts';
import manifiesto from './vistas.json';

export const HASH_VISTAS: string = manifiesto.hash;

/** Ruta pública de una vista del conjunto actual, p. ej. `urlVista('poster-1920.webp')`. */
export const urlVista = (nombre: string): string => rutaVista(HASH_VISTAS, nombre);

export const POSTER = {
  ancho: 1920,
  alto: 1080,
  src: urlVista('poster-1920.webp'),
  srcSet: `${urlVista('poster-960.webp')} 960w, ${urlVista('poster-1920.webp')} 1920w`,
} as const;
