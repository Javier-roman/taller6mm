// Precarga de fuentes (docs/02 §4.2): solo IBM Plex Sans Condensed 400 (interfaz y lectura) y 600
// (titulares), en su subconjunto latino. Vite resuelve `?url` al mismo archivo con hash que
// referencia fuentes.css, así que la precarga y el @font-face apuntan a la misma URL (lo comprueba
// el e2e de /sistema).

import plex400 from '@fontsource/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-400-normal.woff2?url';
import plex600 from '@fontsource/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-600-normal.woff2?url';

export const FONT_PRELOADS: readonly string[] = [plex400, plex600];
