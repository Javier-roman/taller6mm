// Insignia de fidelidad T0–T3 (docs/05 §2): acompaña siempre al render para que se sepa qué se está
// viendo. El nivel va en texto, icono y forma, nunca solo en color. Sin nivel → «Sin verificar»
// (principio 2: lo desconocido se dice, no se disimula).
import { IconoDesconocido } from './iconos.tsx';
import { cx } from './util.ts';

export const NIVELES_FIDELIDAD = {
  T0: { nombre: 'Plano técnico', descripcion: 'Silueta vectorial a escala con las cotas del fabricante.' },
  T1: { nombre: 'Foto licenciada', descripcion: 'Foto con licencia, recortada y calibrada a escala.' },
  T2: { nombre: 'Modelo fiel', descripcion: 'Modelo 3D propio, calibrado a las medidas reales.' },
  T3: { nombre: 'Escaneado y verificado', descripcion: 'Escaneo o CAD oficial, con cotas verificadas a calibre.' },
} as const;

export type NivelFidelidad = keyof typeof NIVELES_FIDELIDAD;

export interface InsigniaFidelidadProps {
  nivel: NivelFidelidad | null;
  /** Solo el código (T2) a la vista; el nombre queda para lectores de pantalla. */
  compacta?: boolean;
  className?: string;
}

export function InsigniaFidelidad({ nivel, compacta = false, className }: InsigniaFidelidadProps) {
  if (nivel === null) {
    return (
      <span className={cx('t6-insignia', 't6-insignia--sin-nivel', className)} data-nivel="ninguno">
        <IconoDesconocido />
        <span className="t6-sr">Fidelidad: </span>
        <span className="t6-insignia__nombre">Sin verificar</span>
      </span>
    );
  }
  const { nombre } = NIVELES_FIDELIDAD[nivel];
  return (
    <span className={cx('t6-insignia', `t6-insignia--${nivel.toLowerCase()}`, className)} data-nivel={nivel}>
      {/* El cuadrito se llena con el nivel: T0 vacío, T1 un tercio, T2 dos tercios, T3 lleno. */}
      <i className="t6-insignia__nivel" aria-hidden="true" />
      <span className="t6-sr">Fidelidad: </span>
      <span className="t6-insignia__codigo">{nivel}</span>
      {compacta ? <span className="t6-sr"> · {nombre}</span> : <span className="t6-insignia__nombre">{nombre}</span>}
    </span>
  );
}
