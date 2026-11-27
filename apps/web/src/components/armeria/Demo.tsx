// Marca «Demo» de La Armería: todo dato de ejemplo (`is_demo`) la lleva a la vista o, en tarjetas pequeñas, solo
// para el lector de pantalla (principio 2: los datos de ejemplo se dicen, no se disimulan).
export function Demo({ plural = false }: { plural?: boolean }) {
  return (
    <span className="armeria__demo">
      Demo<span className="t6-sr">{plural ? ' (datos de ejemplo)' : ' (dato de ejemplo)'}</span>
    </span>
  );
}
