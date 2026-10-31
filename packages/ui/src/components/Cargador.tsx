// Indicador de carga (docs/02 §4.5): un cargador que se llena con bolas de 6 mm.
// Sin etiqueta es decorativo (dentro de un botón, el texto ya dice «Guardando…»). Con etiqueta,
// anuncia el estado (role="status"). Con movimiento reducido, las bolas quedan quietas.

export function Cargador({ etiqueta }: { etiqueta?: string }) {
  const bolas = (
    <>
      <span className="t6-cargador__bola" aria-hidden="true" />
      <span className="t6-cargador__bola" aria-hidden="true" />
      <span className="t6-cargador__bola" aria-hidden="true" />
    </>
  );
  if (!etiqueta) {
    return (
      <span className="t6-cargador" aria-hidden="true">
        {bolas}
      </span>
    );
  }
  return (
    <span className="t6-cargador" role="status">
      {bolas}
      <span className="t6-sr">{etiqueta}</span>
    </span>
  );
}
