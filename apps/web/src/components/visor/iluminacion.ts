// Presets de iluminación del visor de prueba: formato mínimo compartido («iluminacion-presets/v1») y su
// lectura segura. El catálogo definitivo (catalogo/iluminacion-presets.json) lo crea otro agente: este
// formato es el mínimo que el visor necesita y se adaptará a él cuando exista (ver LEEME del visor).
//
// Unidades, pensadas para que un preset no dependa del tamaño de la pieza:
//  - `posicion` es una dirección desde el centro del modelo, en radios del modelo (+Y arriba, +X hacia la
//    boca del cañón, +Z a la izquierda del tirador: docs/05 §4);
//  - `intensidad` es la iluminancia relativa en el centro del modelo (1 ≈ luz de relleno suave); en luces
//    puntuales y focos el visor la convierte en candelas con la distancia, así que la pieza se ve igual
//    de iluminada sea un tubo de culata o un guardamanos largo.
// Los colores son nombres de token de @taller6mm/ui (`hueso`, `laton-claro`…) o #rrggbb.
import { COLOR_TOKENS, type ColorToken } from '@taller6mm/ui/tokens';

export type TipoLuz = 'direccional' | 'puntual' | 'foco' | 'hemisferio';
export const TIPOS_LUZ: readonly TipoLuz[] = ['direccional', 'puntual', 'foco', 'hemisferio'];

export type Vector3Tupla = readonly [number, number, number];

export interface LuzPreset {
  tipo: TipoLuz;
  color: string;
  /** Solo hemisferio: color del hemisferio inferior (luz rebotada del suelo). */
  color_suelo?: string;
  intensidad: number;
  /** Obligatoria salvo en el hemisferio, que siempre apunta arriba-abajo. */
  posicion?: Vector3Tupla;
  /** La luz proyecta sombras (como mucho una o dos por preset: cuestan). */
  sombra?: boolean;
  /** 0 (borde duro) a 1 (muy difuminado). Solo con sombra. */
  suavidad?: number;
}

export interface PresetIluminacion {
  id: string;
  nombre: string;
  descripcion: string;
  /** Color de fondo de la escena. */
  fondo: string;
  /** Exposición del mapa de tonos (1 = neutra). */
  exposicion: number;
  /** Intensidad del entorno procedural que da reflejos a los metales (0 = sin entorno). */
  entorno: number;
  luces: readonly LuzPreset[];
}

export interface ConjuntoPresets {
  esquema: 'iluminacion-presets/v1';
  por_defecto: string;
  presets: readonly PresetIluminacion[];
}

export const ESQUEMA_PRESETS = 'iluminacion-presets/v1';

const HEX = /^#[0-9a-fA-F]{6}$/;
const MAX_PRESETS = 24;
const MAX_LUCES = 8;

export type ResultadoPresets = { ok: true; valor: ConjuntoPresets } | { ok: false; error: string };

const esObjeto = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const esNumero = (v: unknown, min: number, max: number): v is number =>
  typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;
const esTexto = (v: unknown): v is string => typeof v === 'string' && v.length > 0 && v.length <= 400;

export function esColorValido(v: unknown): v is string {
  return typeof v === 'string' && (HEX.test(v) || Object.hasOwn(COLOR_TOKENS, v));
}

/** Token de @taller6mm/ui o #rrggbb → #rrggbb. Un valor inválido no llega aquí (parsearPresets lo rechaza). */
export function resolverColor(valor: string): string {
  if (HEX.test(valor)) return valor;
  return COLOR_TOKENS[valor as ColorToken]?.hex ?? COLOR_TOKENS.hueso.hex;
}

function leerLuz(v: unknown, donde: string): LuzPreset | string {
  if (!esObjeto(v)) return `${donde}: no es un objeto`;
  const { tipo, color, color_suelo, intensidad, posicion, sombra, suavidad } = v;
  if (!TIPOS_LUZ.includes(tipo as TipoLuz)) return `${donde}: tipo «${String(tipo)}» desconocido`;
  if (!esColorValido(color)) return `${donde}: color inválido`;
  if (color_suelo !== undefined && !esColorValido(color_suelo)) return `${donde}: color_suelo inválido`;
  if (!esNumero(intensidad, 0, 50)) return `${donde}: intensidad fuera de 0-50`;
  if (tipo !== 'hemisferio') {
    if (!Array.isArray(posicion) || posicion.length !== 3 || !posicion.every((n) => esNumero(n, -50, 50))) {
      return `${donde}: posicion debe ser [x, y, z]`;
    }
    if (posicion.every((n) => n === 0)) return `${donde}: posicion no puede ser el origen`;
  }
  if (sombra !== undefined && typeof sombra !== 'boolean') return `${donde}: sombra debe ser booleano`;
  if (suavidad !== undefined && !esNumero(suavidad, 0, 1)) return `${donde}: suavidad fuera de 0-1`;
  return {
    tipo: tipo as TipoLuz,
    color,
    ...(color_suelo !== undefined ? { color_suelo } : {}),
    intensidad,
    ...(tipo !== 'hemisferio' ? { posicion: posicion as unknown as Vector3Tupla } : {}),
    ...(sombra !== undefined ? { sombra } : {}),
    ...(suavidad !== undefined ? { suavidad } : {}),
  };
}

/**
 * Valida un JSON desconocido (red o archivo) como `ConjuntoPresets`. Acotado a propósito: sin esto, un
 * archivo mal formado pondría números absurdos en la GPU. El primer fallo corta y dice dónde está.
 */
export function parsearPresets(datos: unknown): ResultadoPresets {
  if (!esObjeto(datos)) return { ok: false, error: 'el archivo no es un objeto' };
  if (datos['esquema'] !== ESQUEMA_PRESETS) {
    return { ok: false, error: `esquema esperado ${ESQUEMA_PRESETS}, hay ${String(datos['esquema'])}` };
  }
  const crudos = datos['presets'];
  if (!Array.isArray(crudos) || crudos.length === 0 || crudos.length > MAX_PRESETS) {
    return { ok: false, error: `presets debe ser una lista de 1 a ${MAX_PRESETS}` };
  }
  const presets: PresetIluminacion[] = [];
  const ids = new Set<string>();
  for (const [i, p] of crudos.entries()) {
    const donde = `presets[${i}]`;
    if (!esObjeto(p)) return { ok: false, error: `${donde}: no es un objeto` };
    const { id, nombre, descripcion, fondo, exposicion, entorno, luces } = p;
    if (!esTexto(id) || !/^[a-z0-9-]+$/.test(id)) return { ok: false, error: `${donde}: id inválido` };
    if (ids.has(id)) return { ok: false, error: `${donde}: id «${id}» repetido` };
    ids.add(id);
    if (!esTexto(nombre)) return { ok: false, error: `${donde}: nombre inválido` };
    if (!esTexto(descripcion)) return { ok: false, error: `${donde}: descripcion inválida` };
    if (!esColorValido(fondo)) return { ok: false, error: `${donde}: fondo inválido` };
    if (!esNumero(exposicion, 0.1, 4)) return { ok: false, error: `${donde}: exposicion fuera de 0,1-4` };
    if (!esNumero(entorno, 0, 3)) return { ok: false, error: `${donde}: entorno fuera de 0-3` };
    if (!Array.isArray(luces) || luces.length > MAX_LUCES) {
      return { ok: false, error: `${donde}: luces debe ser una lista de 0 a ${MAX_LUCES}` };
    }
    const lucesOk: LuzPreset[] = [];
    for (const [j, l] of luces.entries()) {
      const r = leerLuz(l, `${donde}.luces[${j}]`);
      if (typeof r === 'string') return { ok: false, error: r };
      lucesOk.push(r);
    }
    presets.push({ id, nombre, descripcion, fondo, exposicion, entorno, luces: lucesOk });
  }
  const porDefecto = datos['por_defecto'];
  if (typeof porDefecto !== 'string' || !ids.has(porDefecto)) {
    return { ok: false, error: 'por_defecto debe ser el id de uno de los presets' };
  }
  return { ok: true, valor: { esquema: ESQUEMA_PRESETS, por_defecto: porDefecto, presets } };
}
