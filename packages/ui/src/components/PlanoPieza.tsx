// Plano T0 de una pieza (docs/05 §2 y ADR-0010): vista lateral ortogonal sobre papel, con las cotas
// de la ficha del fabricante. Sustituye al «Sin imagen» cuando una pieza no tiene render propio.
// Honestidad: lo único que se dibuja es la ENVOLVENTE (largo × diámetro) a escala; no inventa la
// silueta. Las cotas solo se ponen en vistas ortogonales y solo con medidas conocidas; sin ninguna,
// la lámina lo dice. Dibujo en atributos SVG (sin `style`, la CSP los bloquea).
import { cx } from './util.ts';

export interface PlanoPiezaProps {
  /** Nombre de la pieza, para el texto alternativo. */
  nombre: string;
  /** Largo en mm, o `null` si se desconoce. */
  largoMm: number | null;
  /** Diámetro o alto en mm, o `null` si se desconoce. */
  diametroMm: number | null;
  className?: string;
}

const ANCHO = 400;
const ALTO = 300;
const AREA = { ancho: 240, alto: 110 } as const;

/** 229 → «229,0»: un decimal, como las fichas de fabricante. */
const cota = (valor: number) =>
  new Intl.NumberFormat('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(valor);

export function PlanoPieza({ nombre, largoMm, diametroMm, className }: PlanoPiezaProps) {
  if (largoMm === null || largoMm <= 0) {
    return (
      <svg
        className={cx('t6-plano', className)}
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        role="img"
        aria-label={`${nombre}: sin medidas verificadas, no hay plano`}
      >
        <rect x="40" y="60" width="320" height="180" fill="none" stroke="currentColor" strokeDasharray="6 4" />
        <path
          d="M40 240 360 60M40 60l320 180"
          stroke="currentColor"
          strokeWidth=".6"
          strokeDasharray="2 6"
          fill="none"
        />
        <text className="t6-plano__texto" x="200" y="156" textAnchor="middle">
          SIN MEDIDAS VERIFICADAS
        </text>
      </svg>
    );
  }
  const conDiametro = diametroMm !== null && diametroMm > 0;
  const escala = conDiametro ? Math.min(AREA.ancho / largoMm, AREA.alto / diametroMm) : AREA.ancho / largoMm;
  const w = largoMm * escala;
  const h = conDiametro ? diametroMm * escala : 0;
  const x0 = (ANCHO - w) / 2;
  const yc = 130;
  const y0 = yc - h / 2;
  const yBajo = yc + Math.max(h / 2, 4);
  const yCotaL = yBajo + 36;
  const xCotaD = x0 + w + 32;
  const alt = conDiametro
    ? `Plano lateral de ${nombre}: ${cota(largoMm)} mm de largo y ${cota(diametroMm)} mm de diámetro`
    : `Plano lateral de ${nombre}: ${cota(largoMm)} mm de largo`;
  return (
    <svg className={cx('t6-plano', className)} viewBox={`0 0 ${ANCHO} ${ALTO}`} role="img" aria-label={alt}>
      {/* Envolvente a escala y eje de simetría */}
      {conDiametro ? (
        <rect x={x0} y={y0} width={w} height={h} fill="none" stroke="currentColor" strokeWidth="1.6" />
      ) : (
        <path d={`M${x0} ${yc}h${w}`} stroke="currentColor" strokeWidth="1.6" />
      )}
      <path
        d={`M${x0 - 20} ${yc}h${w + 40}`}
        stroke="currentColor"
        strokeWidth=".6"
        strokeDasharray="14 4 2 4"
        fill="none"
      />
      {/* Cota de largo */}
      <g stroke="currentColor" strokeWidth=".8" fill="none">
        <path d={`M${x0} ${yBajo + 4}V${yCotaL + 6}M${x0 + w} ${yBajo + 4}V${yCotaL + 6}`} />
        <path d={`M${x0} ${yCotaL}H${x0 + w}`} />
        <path d={`M${x0 - 3} ${yCotaL + 3}l6 -6M${x0 + w - 3} ${yCotaL + 3}l6 -6`} />
      </g>
      <text className="t6-plano__texto" x={x0 + w / 2} y={yCotaL + 20} textAnchor="middle">
        {cota(largoMm)} mm
      </text>
      {/* Cota de diámetro */}
      {conDiametro ? (
        <>
          <g stroke="currentColor" strokeWidth=".8" fill="none">
            <path d={`M${x0 + w + 4} ${y0}H${xCotaD + 6}M${x0 + w + 4} ${y0 + h}H${xCotaD + 6}`} />
            <path d={`M${xCotaD} ${y0}V${y0 + h}`} />
            <path d={`M${xCotaD - 3} ${y0 + 3}l6 -6M${xCotaD - 3} ${y0 + h + 3}l6 -6`} />
          </g>
          <text className="t6-plano__texto" x={xCotaD + 10} y={yc + 4}>
            Ø{cota(diametroMm)}
          </text>
        </>
      ) : null}
    </svg>
  );
}
