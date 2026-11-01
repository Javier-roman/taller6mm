// Indicador de carga (docs/02 §4.5): un cargador que se llena con bolas de 6 mm, una a una, con la
// curva «pesada». Sin etiqueta es decorativo (dentro de un botón, el texto ya dice «Guardando…»).
// Con etiqueta, anuncia el estado (role="status"). Con movimiento reducido: lleno y quieto.

/** Bolas que caben en la silueta: 5 de 6 mm, como un cargador visto de lado. */
export const BOLAS_CARGADOR = 5;

export function Cargador({ etiqueta }: { etiqueta?: string }) {
  const cuerpo = (
    <span className="t6-cargador__cuerpo" aria-hidden="true">
      {Array.from({ length: BOLAS_CARGADOR }, (_, i) => (
        <span key={i} className="t6-cargador__bola" />
      ))}
    </span>
  );
  if (!etiqueta) {
    return (
      <span className="t6-cargador" aria-hidden="true">
        {cuerpo}
      </span>
    );
  }
  return (
    <span className="t6-cargador" role="status">
      {cuerpo}
      <span className="t6-cargador__etiqueta">{etiqueta}</span>
    </span>
  );
}
