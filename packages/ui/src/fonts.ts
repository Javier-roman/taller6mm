// Precarga de fuentes (docs/02 §4.2): solo Archivo (interfaz) y Cinzel (titulares), en su
// subconjunto latino. Vite resuelve `?url` al mismo archivo con hash que referencia fuentes.css,
// así que la precarga y el @font-face apuntan a la misma URL (lo comprueba el e2e de /sistema).

import cinzel from '@fontsource/cinzel/files/cinzel-latin-600-normal.woff2?url';
import archivo from '@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2?url';

export const FONT_PRELOADS: readonly string[] = [archivo, cinzel];
