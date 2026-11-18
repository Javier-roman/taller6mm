// Índice de modelos del visor de prueba: lo escribe scripts/prototipos/visor-preparar.mjs junto a los
// GLB optimizados, en public/dev/visor/ (carpeta ignorada por git). Aquí solo hay tipos y lectura segura.
import { type ConjuntoPresets, parsearPresets } from './iluminacion.ts';

export const BASE_VISOR = '/dev/visor/';

export interface CotaIndice {
  clave: string;
  /** `null` = desconocida: se muestra como tal, nunca como 0. */
  valor_mm: number | null;
  confianza: string;
}

export interface PiezaIndice {
  id: string;
  grupo: string;
  archivo: string;
  nombre: string | null;
  familia: string | null;
  nivel: string;
  es_demo: boolean;
  publicable_3d: boolean;
  triangulos: number;
  bytes: number;
  cotas: readonly CotaIndice[];
  notas: readonly string[];
}

export interface PiezaDeMontaje {
  id: string;
  rol: string;
  familia: string;
  nivel: string;
  es_demo: boolean;
  /** `false` = marcador visual de una pieza que aún no tiene modelo (sin cotas). */
  tiene_malla: boolean;
}

export interface MontajeIndice {
  id: string;
  nombre: string;
  descripcion: string;
  archivo: string;
  nivel: string;
  es_demo: boolean;
  publicable_3d: boolean;
  triangulos: number;
  bytes: number;
  aviso: string | null;
  piezas: readonly PiezaDeMontaje[];
}

export interface IndiceVisor {
  esquema: 'visor-indice/v1';
  aviso: string;
  presets_externos: string | null;
  piezas: readonly PiezaIndice[];
  montajes: readonly MontajeIndice[];
}

const esObjeto = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

/**
 * El índice es de confianza (lo escribe nuestro script en local), pero llega por red y por eso se
 * comprueba lo justo: el esquema y que haya listas. Un fallo aquí se muestra como «sin modelos».
 */
export function parsearIndice(datos: unknown): IndiceVisor {
  if (!esObjeto(datos) || datos['esquema'] !== 'visor-indice/v1') throw new Error('índice con otro esquema');
  if (!Array.isArray(datos['piezas']) || !Array.isArray(datos['montajes'])) throw new Error('índice sin listas');
  return datos as unknown as IndiceVisor;
}

export async function cargarIndice(signal: AbortSignal): Promise<IndiceVisor> {
  const r = await fetch(`${BASE_VISOR}indice.json`, { signal });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return parsearIndice(await r.json());
}

/** Presets externos (catalogo/iluminacion-presets.json copiado por el script), o `null` si no hay o no valen. */
export async function cargarPresetsExternos(
  archivo: string,
  signal: AbortSignal,
): Promise<{ valor: ConjuntoPresets | null; error: string | null }> {
  try {
    const r = await fetch(`${BASE_VISOR}${archivo}`, { signal });
    if (!r.ok) return { valor: null, error: `HTTP ${r.status}` };
    const p = parsearPresets(await r.json());
    return p.ok ? { valor: p.valor, error: null } : { valor: null, error: p.error };
  } catch (e) {
    if (signal.aborted) throw e;
    return { valor: null, error: e instanceof Error ? e.message : 'error desconocido' };
  }
}

export const formatearBytes = (bytes: number): string =>
  bytes >= 1024 * 1024
    ? `${(bytes / 1024 / 1024).toLocaleString('es-ES', { maximumFractionDigits: 1 })} MB`
    : `${Math.round(bytes / 1024).toLocaleString('es-ES')} KB`;
