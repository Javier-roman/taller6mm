// Barra de dato (docs/02 §4.5 y docs/03 §6): como las de los gunsmith, pero con datos reales y su
// escala (la distribución de builds de la misma plataforma). Nunca «daño» ni «precisión».
// Es un `meter` accesible; el relleno es un SVG con atributos de presentación, así que no necesita
// estilos en línea (la CSP los bloquea). Estados: listo, incompleto (el valor es un mínimo), sin
// dato, carga y error.
import { useId } from 'react';
import {
  formatearComprobado,
  formatearDato,
  formatearNumero,
  requiereFecha,
  textoFaltan,
  UNIDADES,
  type UnidadConFecha,
} from './formato.ts';
import { IconoAlerta, IconoDesconocido } from './iconos.tsx';

interface BarraDatoComun {
  etiqueta: string;
  /** En la unidad guardada (g, mm, céntimos…). `null`: ninguna pieza tiene el dato. */
  valor: number | null;
  escala: { readonly min: number; readonly max: number };
  /** Marca de comparación, p. ej. la mediana de las builds de la plataforma. */
  referencia?: { readonly valor: number; readonly etiqueta: string };
  /** Lectura de la escala («Más ligera que el 70 % de las builds M4»). */
  nota?: string;
  /** Piezas sin el dato: el valor mostrado es un mínimo. */
  piezasSinDato?: number;
  estado?: 'listo' | 'carga' | 'error';
  mensajeError?: string;
}

/**
 * Precio y stock caducan: llevan SIEMPRE la fecha de su última comprobación (principio 2 de
 * CLAUDE.md), así que `comprobado` es obligatoria con `eur` y `tiendas` (en una build, la del
 * precio más antiguo). `null` se muestra como «Sin fecha de comprobación», nunca se inventa.
 */
interface BarraDatoConFecha extends BarraDatoComun {
  unidad: UnidadConFecha;
  /** ISO 8601 en UTC o `null` si no se sabe. */
  comprobado: string | null;
  /** Momento de referencia (ISO) para «hace 3 h». Sin él, la fecha absoluta. */
  ahora?: string;
}

interface BarraDatoSinFecha extends BarraDatoComun {
  unidad: 'g' | 'mm';
  comprobado?: undefined;
  ahora?: undefined;
}

export type BarraDatoProps = BarraDatoConFecha | BarraDatoSinFecha;

const porcentaje = (valor: number, min: number, max: number) =>
  max > min ? Math.round(Math.min(1, Math.max(0, (valor - min) / (max - min))) * 1000) / 10 : 0;

export function BarraDato({
  etiqueta,
  valor,
  unidad,
  escala,
  referencia,
  nota,
  piezasSinDato = 0,
  estado = 'listo',
  mensajeError,
  comprobado,
  ahora,
}: BarraDatoProps) {
  const etiquetaId = `${useId()}-etiqueta`;
  const { simbolo, nombre } = UNIDADES[unidad];
  const conValor = estado === 'listo' && valor !== null;
  const visual = estado !== 'listo' ? estado : valor === null ? 'sin-dato' : piezasSinDato > 0 ? 'incompleto' : 'listo';
  const conFecha = requiereFecha(unidad);
  const comprobacion = conFecha && comprobado ? formatearComprobado(comprobado, ahora) : null;
  const textoComprobacion = comprobacion ? `comprobado ${comprobacion.texto}` : 'sin fecha de comprobación';

  const lectura = conValor
    ? [
        `${piezasSinDato > 0 ? 'al menos ' : ''}${formatearDato(valor, unidad)}`,
        piezasSinDato > 0 ? textoFaltan(piezasSinDato, unidad) : null,
        nota ?? null,
        referencia ? `${referencia.etiqueta}: ${formatearDato(referencia.valor, unidad)}` : null,
        conFecha ? textoComprobacion : null,
      ]
        .filter(Boolean)
        .join('; ')
    : '';

  return (
    <div className="t6-dato" data-estado={visual} aria-busy={estado === 'carga' || undefined}>
      <div className="t6-dato__cabecera">
        <span id={etiquetaId} className="t6-dato__etiqueta">
          {etiqueta}
        </span>
        <span className="t6-dato__valor">
          {conValor ? (
            <>
              {piezasSinDato > 0 ? <span aria-hidden="true">≥</span> : null}
              <data value={valor}>{formatearNumero(valor, unidad)}</data>
              <abbr className="t6-dato__unidad" title={nombre}>
                {simbolo}
              </abbr>
            </>
          ) : visual === 'sin-dato' ? (
            <>
              <IconoDesconocido />
              Sin dato
            </>
          ) : (
            <>
              <span aria-hidden="true">—</span>
              {estado === 'carga' ? <span className="t6-sr">Cargando</span> : null}
            </>
          )}
        </span>
      </div>

      {conValor ? (
        <meter
          className="t6-sr"
          aria-labelledby={etiquetaId}
          min={escala.min}
          max={escala.max}
          value={Math.min(escala.max, Math.max(escala.min, valor))}
          aria-valuetext={lectura}
        />
      ) : null}
      {conValor ? (
        <div className="t6-dato__pista" aria-hidden="true">
          <svg
            className="t6-dato__grafico"
            viewBox="0 0 100 8"
            preserveAspectRatio="none"
            aria-hidden="true"
            focusable="false"
          >
            <rect
              className="t6-dato__relleno"
              x="0"
              y="0"
              width={porcentaje(valor, escala.min, escala.max)}
              height="8"
            />
            {referencia ? (
              <line
                className="t6-dato__referencia"
                x1={porcentaje(referencia.valor, escala.min, escala.max)}
                x2={porcentaje(referencia.valor, escala.min, escala.max)}
                y1="0"
                y2="8"
              />
            ) : null}
          </svg>
        </div>
      ) : (
        <div className="t6-dato__pista" aria-hidden="true" />
      )}

      <div className="t6-dato__escala" aria-hidden="true">
        <span>{formatearDato(escala.min, unidad)}</span>
        <span>{formatearDato(escala.max, unidad)}</span>
      </div>

      {estado === 'error' ? (
        <p className="t6-mensaje t6-mensaje--error">
          <IconoAlerta />
          {mensajeError ?? 'No se ha podido calcular este dato. Inténtalo de nuevo en unos minutos.'}
        </p>
      ) : visual === 'sin-dato' ? (
        <p className="t6-mensaje t6-mensaje--desconocido">
          <IconoDesconocido />
          {nota ?? 'Ninguna pieza de la build tiene este dato todavía.'}
        </p>
      ) : conValor && (nota || referencia || piezasSinDato > 0 || conFecha) ? (
        <p className="t6-dato__nota" aria-hidden="true">
          {piezasSinDato > 0 ? <span className="t6-mensaje--aviso">{textoFaltan(piezasSinDato, unidad)}</span> : null}
          {nota ? <span>{nota}</span> : null}
          {referencia ? (
            <span className="t6-dato__referencia-leyenda">
              {referencia.etiqueta}: {formatearDato(referencia.valor, unidad)}
            </span>
          ) : null}
          {conFecha ? (
            comprobacion ? (
              <span className="t6-dato__comprobado">
                Comprobado{' '}
                <time dateTime={comprobacion.iso} title={comprobacion.completo}>
                  {comprobacion.texto}
                </time>
              </span>
            ) : (
              <span className="t6-dato__comprobado t6-mensaje--desconocido">
                <IconoDesconocido />
                Sin fecha de comprobación
              </span>
            )
          ) : null}
        </p>
      ) : null}
    </div>
  );
}
