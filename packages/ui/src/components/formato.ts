// Formato de datos reales para la interfaz (es-ES): longitudes en mm, pesos en g y dinero en
// céntimos enteros (CLAUDE.md, convenciones). Sin decimales inventados.
import { BRAND } from '../brand.ts';

export type Unidad = 'g' | 'mm' | 'eur' | 'tiendas';

interface UnidadSpec {
  readonly simbolo: string;
  readonly nombre: string;
  /** Qué falta cuando una pieza no tiene el dato («2 piezas sin peso»). */
  readonly falta: string;
  readonly decimales: number;
  /** Divisor desde la unidad guardada (céntimos → euros). */
  readonly divisor: number;
}

export const UNIDADES: Readonly<Record<Unidad, UnidadSpec>> = {
  g: { simbolo: 'g', nombre: 'gramos', falta: 'sin peso', decimales: 0, divisor: 1 },
  mm: { simbolo: 'mm', nombre: 'milímetros', falta: 'sin medida', decimales: 0, divisor: 1 },
  eur: { simbolo: '€', nombre: 'euros', falta: 'sin precio', decimales: 2, divisor: 100 },
  tiendas: { simbolo: 'tiendas', nombre: 'tiendas', falta: 'sin tiendas', decimales: 0, divisor: 1 },
};

/** Número en español de España («3120», «12.500», «412,35»). */
export function formatearNumero(valor: number, unidad: Unidad): string {
  const { decimales, divisor } = UNIDADES[unidad];
  return new Intl.NumberFormat(BRAND.locale, {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(valor / divisor);
}

/** Espacio duro: la cifra y su unidad nunca se separan en dos líneas («412,35 €», «44 px»). */
export const NBSP = ' ';

/** Número con su unidad, para textos accesibles («412,35 €», «3120 g»). */
export function formatearDato(valor: number, unidad: Unidad): string {
  return `${formatearNumero(valor, unidad)}${NBSP}${UNIDADES[unidad].simbolo}`;
}

/** Unidades cuyo dato caduca: precio y stock llevan siempre la fecha de su comprobación (principio 2). */
export const UNIDADES_CON_FECHA = ['eur', 'tiendas'] as const satisfies readonly Unidad[];
export type UnidadConFecha = (typeof UNIDADES_CON_FECHA)[number];
export const requiereFecha = (unidad: Unidad): unidad is UnidadConFecha =>
  (UNIDADES_CON_FECHA as readonly Unidad[]).includes(unidad);

export interface Comprobacion {
  /** ISO 8601 en UTC, para `<time datetime>`. */
  readonly iso: string;
  /** «hace 3 h» si se conoce el momento de referencia; si no, la fecha («31 oct 2026, 18:40»). */
  readonly texto: string;
  /** Fecha y hora completas, para el `title`. */
  readonly completo: string;
}

const fechaCorta = new Intl.DateTimeFormat(BRAND.locale, {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'Europe/Madrid',
});
const fechaCompleta = new Intl.DateTimeFormat(BRAND.locale, {
  dateStyle: 'full',
  timeStyle: 'short',
  timeZone: 'Europe/Madrid',
});

/**
 * Cuándo se comprobó un dato. `ahora` (ISO) permite el texto relativo («hace 3 h»): lo pasa quien
 * renderiza con la hora de la petición. Sin `ahora` (páginas prerenderizadas), la fecha absoluta,
 * que no caduca. Devuelve `null` si la fecha no es válida: se muestra como desconocida.
 */
export function formatearComprobado(iso: string, ahora?: string): Comprobacion | null {
  const momento = Date.parse(iso);
  if (Number.isNaN(momento)) return null;
  const fecha = new Date(momento);
  const completo = fechaCompleta.format(fecha);
  const referencia = ahora === undefined ? Number.NaN : Date.parse(ahora);
  if (Number.isNaN(referencia) || referencia < momento) {
    return { iso: fecha.toISOString(), texto: `el${NBSP}${fechaCorta.format(fecha)}`, completo };
  }
  const minutos = Math.floor((referencia - momento) / 60_000);
  const texto =
    minutos < 1
      ? 'hace un momento'
      : minutos < 60
        ? `hace ${minutos}${NBSP}min`
        : minutos < 60 * 24
          ? `hace ${Math.floor(minutos / 60)}${NBSP}h`
          : minutos < 60 * 24 * 30
            ? `hace ${Math.floor(minutos / (60 * 24))}${NBSP}${Math.floor(minutos / (60 * 24)) === 1 ? 'día' : 'días'}`
            : `el${NBSP}${fechaCorta.format(fecha)}`;
  return { iso: fecha.toISOString(), texto, completo };
}

/** «1 pieza sin peso», «3 piezas sin medida». */
export function textoFaltan(piezas: number, unidad: Unidad): string {
  return `${piezas} ${piezas === 1 ? 'pieza' : 'piezas'} ${UNIDADES[unidad].falta}`;
}
