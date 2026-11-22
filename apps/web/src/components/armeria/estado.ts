// Estado de La Armería, sin React ni DOM: tipos, claves del almacenamiento y lectura segura de preferencias.
// El hook (useArmeria.ts) lo une con el navegador. Lo que dura más que la visita (la luz elegida, la intro
// vista) va en localStorage, que puede faltar o lanzar (navegación privada, sitios bloqueados): sin él, la
// preferencia dura lo que la visita y nada se rompe.

/** «Más luz» es una ayuda de legibilidad: misma temperatura de luz, más nivel (ADR-0002). */
export type Luz = 'penumbra' | 'mas-luz';

export const CLAVES = {
  luz: 'taller6mm:armeria:luz',
  intro: 'taller6mm:armeria:intro-vista',
} as const;

export const esLuz = (valor: unknown): valor is Luz => valor === 'penumbra' || valor === 'mas-luz';

export interface Almacen {
  getItem(clave: string): string | null;
  setItem(clave: string, valor: string): void;
}

/** `localStorage` o nada: acceder a él puede lanzar (cookies bloqueadas). */
export function almacenLocal(): Almacen | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage;
  } catch {
    return null;
  }
}

export function leer(almacen: Almacen | null, clave: string): string | null {
  try {
    return almacen?.getItem(clave) ?? null;
  } catch {
    return null;
  }
}

export function guardar(almacen: Almacen | null, clave: string, valor: string): void {
  try {
    almacen?.setItem(clave, valor);
  } catch {
    // Almacenamiento lleno o bloqueado: la preferencia dura lo que la visita.
  }
}

/** Luz inicial: la pedida en la URL (`?luz=`, para capturas y pruebas), si no la guardada y, si no, penumbra. */
export function luzInicial(parametro: string | null, almacen: Almacen | null): Luz {
  if (esLuz(parametro)) return parametro;
  const guardada = leer(almacen, CLAVES.luz);
  return esLuz(guardada) ? guardada : 'penumbra';
}

export interface EstadoArmeria {
  /** La isla ya se hidrató: hasta entonces solo existe el HTML del servidor. */
  hidratado: boolean;
  /** `prefers-reduced-motion: reduce`: escena estática re-iluminable, sin viaje de cámara ni parallax. */
  reducido: boolean;
  luz: Luz;
  /** Zona bajo el puntero y zona con el foco del teclado (en la navegación o en el póster). */
  apuntada: string | null;
  enfocada: string | null;
  /** Zona cuya hoja está abierta. */
  abierta: string | null;
}

export const ESTADO_INICIAL: EstadoArmeria = {
  hidratado: false,
  reducido: false,
  luz: 'penumbra',
  apuntada: null,
  enfocada: null,
  abierta: null,
};

/** La zona que se destaca: la abierta manda sobre el puntero y este sobre el teclado. */
export const zonaActiva = (e: EstadoArmeria): string | null => e.abierta ?? e.apuntada ?? e.enfocada;
