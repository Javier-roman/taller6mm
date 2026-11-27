// Vistas horneadas de La Armería (póster y pases de luz del nivel B, ADR-0002) servidas desde R2.
// Javi decidió el 22-11-2026: sin bucket público. El Worker de la web usa el binding `VISTAS`, que apunta a un
// bucket DEDICADO (`taller6mm-vistas*`, solo con WebP publicables): un binding de R2 permite leer, escribir y
// borrar todo el bucket, así que nunca se enlaza el bucket genérico de assets (revisión de seguridad del PR #65).
// La ruta solo sirve lo que figura en el manifiesto (`vistas.json`). Responde en /assets/armeria/<hash>/<archivo>.webp con Cache-Control inmutable: la ruta lleva el hash del
// contenido, así que un conjunto nuevo es una ruta nueva y nada se invalida. En local (y en cualquier
// entorno donde el objeto no esté en el bucket) `servirVista` devuelve null y el estático de
// public/assets/armeria/ (scripts/armeria/vistas.mjs local) o el 404 de Astro hacen el resto.
// Lógica pura, sin E/S propia: se prueba con un bucket falso (vistas.test.ts).

export const PREFIJO_VISTAS = '/assets/armeria';
/** Un año e `immutable`: la ruta cambia cuando cambia el contenido. */
export const CACHE_INMUTABLE = 'public, max-age=31536000, immutable';

/** Hash corto del conjunto: 12 hex (48 bits) bastan para no repetir rutas entre versiones. */
export const LONGITUD_HASH = 12;

// Solo archivos .webp con nombre en minúsculas, dígitos y guiones: nada de `..`, subcarpetas ni `%`.
const RUTA_VISTA = /^\/assets\/armeria\/([0-9a-f]{12})\/([a-z0-9][a-z0-9-]*\.webp)$/;

/** Clave del objeto en R2 para una ruta pública, o null si la ruta no es una vista válida. */
export function claveVista(pathname: string): string | null {
  const m = RUTA_VISTA.exec(pathname);
  return m ? `armeria/${m[1]}/${m[2]}` : null;
}

/** Claves de R2 que el manifiesto del conjunto autoriza servir (`armeria/<hash>/<archivo>`). */
export function clavesDelManifiesto(manifiesto: {
  readonly hash: string;
  readonly archivos: Readonly<Record<string, unknown>>;
}): ReadonlySet<string> {
  return new Set(Object.keys(manifiesto.archivos).map((nombre) => `armeria/${manifiesto.hash}/${nombre}`));
}

/** Ruta pública de una vista del conjunto con ese hash. */
export function rutaVista(hash: string, nombre: string): string {
  return `${PREFIJO_VISTAS}/${hash}/${nombre}`;
}

/**
 * Hash del conjunto a partir del SHA-256 de cada archivo (nombre → hex). Independiente del orden y del
 * sistema de archivos; lo usan el script de preparación y el test que comprueba el manifiesto.
 */
export async function hashConjunto(sha256PorArchivo: Readonly<Record<string, string>>): Promise<string> {
  const lineas = Object.entries(sha256PorArchivo)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([nombre, sha]) => `${nombre}:${sha}`)
    .join('\n');
  const resumen = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(lineas));
  const hex = [...new Uint8Array(resumen)].map((b) => b.toString(16).padStart(2, '0')).join('');
  return hex.slice(0, LONGITUD_HASH);
}

/** Lo mínimo que usamos de `R2ObjectBody`, para probar sin workerd. */
export interface ObjetoVista {
  readonly body: ReadableStream<Uint8Array> | null;
  readonly httpEtag: string;
  readonly size: number;
}
export interface CubetaVistas {
  get(clave: string): Promise<ObjetoVista | null>;
}

const ENCABEZADOS_BASE = { 'content-type': 'image/webp', 'cache-control': CACHE_INMUTABLE } as const;

/** ¿El `If-None-Match` del cliente acepta esta ETag? (comparación débil, lista o `*`). */
function coincide(ifNoneMatch: string | null, etag: string): boolean {
  if (!ifNoneMatch) return false;
  const limpia = (e: string) => e.trim().replace(/^W\//, '');
  const nuestra = limpia(etag);
  return ifNoneMatch.split(',').some((e) => limpia(e) === '*' || limpia(e) === nuestra);
}

/**
 * Responde a una vista horneada o devuelve null para que siga la cadena normal (estáticos y Astro).
 * Solo GET y HEAD; la cubeta es opcional porque no todos los entornos la tienen enlazada.
 */
export async function servirVista(
  request: Request,
  cubeta: CubetaVistas | undefined,
  permitidas?: ReadonlySet<string>,
): Promise<Response | null> {
  if (!cubeta || (request.method !== 'GET' && request.method !== 'HEAD')) return null;
  const clave = claveVista(new URL(request.url).pathname);
  // Con lista de claves permitidas (el Worker siempre la pasa) no se consulta R2 por rutas desconocidas.
  if (!clave || (permitidas && !permitidas.has(clave))) return null;
  const objeto = await cubeta.get(clave);
  if (!objeto) return null;
  const cabeceras = { ...ENCABEZADOS_BASE, etag: objeto.httpEtag };
  if (coincide(request.headers.get('if-none-match'), objeto.httpEtag)) {
    await objeto.body?.cancel();
    return new Response(null, { status: 304, headers: cabeceras });
  }
  const headers = { ...cabeceras, 'content-length': String(objeto.size) };
  if (request.method === 'HEAD') {
    await objeto.body?.cancel();
    return new Response(null, { status: 200, headers });
  }
  return new Response(objeto.body, { status: 200, headers });
}
