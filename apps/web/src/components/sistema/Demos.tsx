// Islas de demostración de /sistema: los componentes interactivos necesitan estado, así que cada uno
// vive en su isla (client:visible). Todo el contenido son datos de ejemplo.
import { Boton, Maletin, Pestanas, Tooltip, type TostadaDatos, Tostadas } from '@taller6mm/ui/componentes';
import { useState } from 'react';

export function DemoPestanas() {
  return (
    <Pestanas
      etiqueta="Datos de la réplica de ejemplo"
      pestanas={[
        {
          id: 'medidas',
          titulo: 'Medidas',
          panel: <p className="text-niebla">Longitud total y del cañón, en milímetros, con su fuente.</p>,
        },
        {
          id: 'compat',
          titulo: 'Compatibilidad',
          panel: <p className="text-niebla">Qué encaja y por qué, con su motivo y su confianza.</p>,
        },
        {
          id: 'mercado',
          titulo: 'Mercado',
          panel: <p className="text-niebla">Precio y stock por tienda, siempre con su fecha de comprobación.</p>,
        },
        { id: 'comunidad', titulo: 'Comunidad', panel: null, desactivada: true },
      ]}
    />
  );
}

export function DemoMaletin() {
  const [abierto, setAbierto] = useState(false);
  return (
    <>
      <Boton variante="acero" onClick={() => setAbierto(true)}>
        Abrir maletín
      </Boton>
      <Maletin
        abierto={abierto}
        onCerrar={() => setAbierto(false)}
        titulo="Borrar build"
        acciones={
          <>
            <Boton variante="fantasma" onClick={() => setAbierto(false)}>
              Cancelar
            </Boton>
            <Boton variante="peligro" onClick={() => setAbierto(false)}>
              Borrar build
            </Boton>
          </>
        }
      >
        <p className="text-niebla">
          Se borrará «M4 de ejemplo» de este dispositivo. Esta acción no se puede deshacer. Escape o «Cerrar» vuelven al
          botón que abrió el maletín.
        </p>
      </Maletin>
    </>
  );
}

export function DemoTostadas() {
  const [lista, setLista] = useState<TostadaDatos[]>([]);
  const añadir = (t: Omit<TostadaDatos, 'id'>) => setLista((l) => [...l, { ...t, id: crypto.randomUUID() }]);
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3">
        <Boton onClick={() => añadir({ tono: 'ok', texto: 'Build guardada en este dispositivo.', duracionMs: 8000 })}>
          Tostada correcta
        </Boton>
        <Boton onClick={() => añadir({ tono: 'info', texto: 'Hay precios nuevos para tu build.', duracionMs: 8000 })}>
          Tostada informativa
        </Boton>
        <Boton
          variante="peligro"
          onClick={() => añadir({ tono: 'error', texto: 'No se ha guardado: se ha perdido la conexión.' })}
        >
          Tostada de error
        </Boton>
      </div>
      <Tostadas tostadas={lista} onCerrar={(id) => setLista((l) => l.filter((t) => t.id !== id))} />
    </div>
  );
}

export function DemoTooltip({ visible = false }: { visible?: boolean }) {
  return (
    <Tooltip texto="CCW: rosca a izquierdas. Una bocacha CW no encaja sin adaptador." demo={visible}>
      <Boton variante="acero">Rosca CCW</Boton>
    </Tooltip>
  );
}
