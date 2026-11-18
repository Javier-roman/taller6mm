// Presets de iluminación del visor: lectura segura de `catalogo/iluminacion-presets.json`
// («iluminacion-presets/v1»), la fuente única que comparten el render de Blender (escalera de calidad) y
// esta web. Aquí solo hay tipos, validación acotada y la conversión de ejes; la escena los pinta en
// `Entorno.tsx` con la misma receta que Blender: softboxes de área sobre un mundo en degradado.
//
// Unidades del catálogo (ver su `nota`): posiciones y tamaños en múltiplos de `d`, la diagonal de la caja de
// la pieza o del conjunto; `energia_d2` en vatios por d² (Blender, luz de área); colores en RGB lineal. Las
// direcciones están en ejes de Blender (Z arriba, la cámara «lado» en −Y); el glTF es Y arriba y la cámara
// «izquierda» en +Z (docs/05 §4), así que `dir` (bx, by, bz) pasa a (bx, bz, −by).
export const ESQUEMA_PRESETS = 'iluminacion-presets/v1';

export type Rgb = readonly [number, number, number];
export type Vector3Tupla = readonly [number, number, number];

export interface LuzEstudio {
  id: string;
  /** Dirección en ejes de Blender; no está normalizada (su módulo cuenta en la distancia real). */
  dir: Vector3Tupla;
  /** Múltiplo de `d` por el módulo de `dir`. */
  dist: number;
  energia_d2: number;
  /** Lado de la luz de área, en múltiplos de `d`. */
  tam_d: number;
  color: Rgb;
}

export interface PresetEstudio {
  id: string;
  /** El catálogo no trae nombre visible: sale del id («mate_suave» → «Mate suave»). */
  nombre: string;
  descripcion: string;
  exposicion_ev: number;
  tono: 'AgX' | 'Neutral' | 'Filmic';
  mundo: { abajo: Rgb; arriba: Rgb; intensidad: number };
  suelo: { color: Rgb; rugosidad: number; metalico: number };
  /** Desplazamiento de la rugosidad de todos los materiales (más luz difusa = algo más mate). */
  rugosidad_delta: number;
  luces: readonly LuzEstudio[];
}

export interface ControlBrillo {
  global: { min: number; max: number; defecto: number };
  rug_por_factor: number;
  banda_rugosidad: number;
  rugosidad_minima_absoluta: number;
}

export interface ConjuntoPresets {
  esquema: typeof ESQUEMA_PRESETS;
  defecto: string;
  brillo: ControlBrillo;
  presets: readonly PresetEstudio[];
}

const MAX_PRESETS = 24;
const MAX_LUCES = 10;
const TONOS = ['AgX', 'Neutral', 'Filmic'] as const;

export type ResultadoPresets = { ok: true; valor: ConjuntoPresets } | { ok: false; error: string };

const esObjeto = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const esNum = (v: unknown, min: number, max: number): v is number =>
  typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;
const esTupla = (v: unknown, min: number, max: number): v is [number, number, number] =>
  Array.isArray(v) && v.length === 3 && v.every((n) => esNum(n, min, max));

const NOMBRES: Readonly<Record<string, string>> = {
  mate_suave: 'Mate suave',
  estudio_contraste: 'Estudio',
  dramatica_penumbra: 'Penumbra',
};

/** Nombre visible: el catálogo no lo trae. Los conocidos llevan nombre corto con tilde; el resto sale del id. */
export function nombreDePreset(id: string): string {
  const conocido = NOMBRES[id];
  if (conocido) return conocido;
  const t = id.replaceAll('_', ' ');
  return t.charAt(0).toUpperCase() + t.slice(1);
}

/** Dirección de Blender (Z arriba) → glTF (Y arriba): (x, y, z) → (x, z, −y). */
export function dirAGltf(d: Vector3Tupla): [number, number, number] {
  return [d[0], d[2], -d[1]];
}

function leerLuz(v: unknown, donde: string): LuzEstudio | string {
  if (!esObjeto(v)) return `${donde}: no es un objeto`;
  const { id, dir, dist, energia_d2, tam_d, color } = v;
  if (typeof id !== 'string' || id.length === 0) return `${donde}: id inválido`;
  if (!esTupla(dir, -20, 20) || dir.every((n) => n === 0)) return `${donde}: dir debe ser [x, y, z] no nulo`;
  if (!esNum(dist, 0.1, 20)) return `${donde}: dist fuera de 0,1-20`;
  if (!esNum(energia_d2, 0, 5000)) return `${donde}: energia_d2 fuera de 0-5000`;
  if (!esNum(tam_d, 0.01, 20)) return `${donde}: tam_d fuera de 0,01-20`;
  if (!esTupla(color, 0, 4)) return `${donde}: color debe ser RGB lineal`;
  return { id, dir, dist, energia_d2, tam_d, color };
}

function leerPreset(id: string, v: unknown): PresetEstudio | string {
  const donde = `presets.${id}`;
  if (!esObjeto(v)) return `${donde}: no es un objeto`;
  const { descripcion, exposicion_ev, tono, mundo, suelo, rugosidad_delta, luces } = v;
  if (typeof descripcion !== 'string' || descripcion.length > 600) return `${donde}: descripcion inválida`;
  if (!esNum(exposicion_ev, -6, 6)) return `${donde}: exposicion_ev fuera de -6 a 6`;
  const tonoOk = tono === undefined ? 'AgX' : TONOS.find((t) => t === tono);
  if (!tonoOk) return `${donde}: tono «${String(tono)}» desconocido`;
  if (!esObjeto(mundo) || !esTupla(mundo['abajo'], 0, 4) || !esTupla(mundo['arriba'], 0, 4)) {
    return `${donde}: mundo inválido`;
  }
  if (!esNum(mundo['intensidad'], 0, 20)) return `${donde}: mundo.intensidad fuera de 0-20`;
  if (!esObjeto(suelo) || !esTupla(suelo['color'], 0, 4) || !esNum(suelo['rugosidad'], 0, 1)) {
    return `${donde}: suelo inválido`;
  }
  if (!esNum(suelo['metalico'], 0, 1)) return `${donde}: suelo.metalico fuera de 0-1`;
  if (rugosidad_delta !== undefined && !esNum(rugosidad_delta, -0.5, 0.5)) {
    return `${donde}: rugosidad_delta fuera de ±0,5`;
  }
  if (!Array.isArray(luces) || luces.length > MAX_LUCES)
    return `${donde}: luces debe ser una lista de 0 a ${MAX_LUCES}`;
  const lucesOk: LuzEstudio[] = [];
  for (const [j, l] of luces.entries()) {
    const r = leerLuz(l, `${donde}.luces[${j}]`);
    if (typeof r === 'string') return r;
    lucesOk.push(r);
  }
  return {
    id,
    nombre: nombreDePreset(id),
    descripcion,
    exposicion_ev,
    tono: tonoOk,
    mundo: { abajo: mundo['abajo'], arriba: mundo['arriba'], intensidad: mundo['intensidad'] },
    suelo: { color: suelo['color'], rugosidad: suelo['rugosidad'], metalico: suelo['metalico'] },
    rugosidad_delta: rugosidad_delta ?? 0,
    luces: lucesOk,
  };
}

function leerBrillo(v: unknown): ControlBrillo | string {
  if (!esObjeto(v) || !esObjeto(v['global'])) return 'brillo inválido';
  const g = v['global'];
  if (!esNum(g['min'], 0.1, 1) || !esNum(g['max'], 1, 4) || !esNum(g['defecto'], 0.1, 4)) {
    return 'brillo.global inválido';
  }
  if (!esNum(v['rug_por_factor'], 0, 1) || !esNum(v['banda_rugosidad'], 0, 1)) return 'brillo: rugosidad inválida';
  if (!esNum(v['rugosidad_minima_absoluta'], 0, 1)) return 'brillo.rugosidad_minima_absoluta inválida';
  return {
    global: { min: g['min'], max: g['max'], defecto: g['defecto'] },
    rug_por_factor: v['rug_por_factor'],
    banda_rugosidad: v['banda_rugosidad'],
    rugosidad_minima_absoluta: v['rugosidad_minima_absoluta'],
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
  const brillo = leerBrillo(datos['brillo']);
  if (typeof brillo === 'string') return { ok: false, error: brillo };
  const crudos = datos['presets'];
  if (!esObjeto(crudos)) return { ok: false, error: 'presets debe ser un objeto id → preset' };
  const ids = Object.keys(crudos);
  if (ids.length === 0 || ids.length > MAX_PRESETS) {
    return { ok: false, error: `presets debe tener de 1 a ${MAX_PRESETS} entradas` };
  }
  const presets: PresetEstudio[] = [];
  for (const id of ids) {
    if (!/^[a-z0-9_]+$/.test(id)) return { ok: false, error: `presets: id «${id}» inválido` };
    const p = leerPreset(id, crudos[id]);
    if (typeof p === 'string') return { ok: false, error: p };
    presets.push(p);
  }
  const defecto = datos['defecto'];
  if (typeof defecto !== 'string' || !ids.includes(defecto)) {
    return { ok: false, error: 'defecto debe ser el id de uno de los presets' };
  }
  return { ok: true, valor: { esquema: ESQUEMA_PRESETS, defecto, brillo, presets } };
}
