// Insignia de compatibilidad (docs/00 y docs/03 §6; principio 3): cada veredicto lleva motivo, fuente
// y confianza, y el tipo no compila sin ellos. El veredicto va en texto, icono y forma.
import type { ReactNode } from 'react';
import { IconoAdaptador, IconoCheck, IconoCruz, IconoDesconocido } from './iconos.tsx';
import { cx } from './util.ts';

export type Veredicto = 'compatible' | 'adaptador' | 'incompatible' | 'desconocido';
export type Confianza = 'alta' | 'media' | 'baja';

export const VEREDICTOS: Readonly<Record<Veredicto, string>> = {
  compatible: 'Compatible',
  adaptador: 'Con adaptador',
  incompatible: 'Incompatible',
  desconocido: 'Sin datos suficientes',
};
export const CONFIANZAS: Readonly<Record<Confianza, string>> = { alta: 'Alta', media: 'Media', baja: 'Baja' };

const ICONO: Record<Veredicto, () => ReactNode> = {
  compatible: IconoCheck,
  adaptador: IconoAdaptador,
  incompatible: IconoCruz,
  desconocido: IconoDesconocido,
};

export interface InsigniaCompatibilidadProps {
  veredicto: Veredicto;
  /** Por qué, en una frase que ayuda («Rosca a derechas (CW) y tu réplica es CCW»). */
  motivo: string;
  /** De dónde sale: ficha del fabricante, medida propia, comunidad… */
  fuente: { nombre: string; href?: string };
  confianza: Confianza;
  /** Solo el veredicto, con motivo y fuente para lectores de pantalla (listas y fichas). */
  compacta?: boolean;
  className?: string;
}

export function InsigniaCompatibilidad({
  veredicto,
  motivo,
  fuente,
  confianza,
  compacta = false,
  className,
}: InsigniaCompatibilidadProps) {
  const Icono = ICONO[veredicto];
  return (
    <div className={cx('t6-compat', `t6-compat--${veredicto}`, compacta && 't6-compat--compacta', className)}>
      <p className="t6-compat__veredicto">
        <Icono />
        {VEREDICTOS[veredicto]}
      </p>
      {compacta ? (
        <p className="t6-sr">
          {motivo} Fuente: {fuente.nombre}. Confianza {CONFIANZAS[confianza].toLowerCase()}.
        </p>
      ) : (
        <>
          <p className="t6-compat__motivo">{motivo}</p>
          <dl className="t6-compat__meta">
            <div>
              <dt>Fuente</dt>
              <dd>{fuente.href ? <a href={fuente.href}>{fuente.nombre}</a> : fuente.nombre}</dd>
            </div>
            <div>
              <dt>Confianza</dt>
              <dd data-confianza={confianza}>
                <span className="t6-compat__nivel" aria-hidden="true">
                  <i />
                  <i />
                  <i />
                </span>
                {CONFIANZAS[confianza]}
              </dd>
            </div>
          </dl>
        </>
      )}
    </div>
  );
}
