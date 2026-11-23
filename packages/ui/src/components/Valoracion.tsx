// Valoración (docs/02 §4.5): estrellas de solo lectura con la nota en texto. `null` = sin opiniones
// (no se muestra un 0 inventado). Medias de opiniones reales de la comunidad, nunca puntuación de juego.
import { IconoEstrella } from './iconos.tsx';

export interface ValoracionProps {
  /** Media de 0 a 5, o `null` si nadie ha opinado. */
  nota: number | null;
  opiniones: number;
}

export function Valoracion({ nota, opiniones }: ValoracionProps) {
  if (nota === null || opiniones === 0) {
    return <span className="t6-valoracion t6-valoracion--sin">Sin opiniones todavía</span>;
  }
  const media = Math.min(5, Math.max(0, nota));
  const texto = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(media);
  return (
    <span className="t6-valoracion">
      <span className="t6-valoracion__estrellas" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((n) => (
          <IconoEstrella key={n} llena={media >= n - 0.25} />
        ))}
      </span>
      <span className="t6-sr">
        Valoración {texto} de 5, {opiniones} opiniones
      </span>
      <span aria-hidden="true">
        {texto} ({opiniones})
      </span>
    </span>
  );
}
