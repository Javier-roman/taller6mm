// La Armería (inicio). Isla de Astro: el servidor pinta el póster y la navegación en el HTML inicial; el
// navegador la hidrata en reposo (`client:idle`). Los niveles B (2,5D) y A (3D) se añaden por encima del
// póster en los siguientes pasos de la Fase 1 y caen a él si algo falla (ADR-0002).
import { InterfazArmeria } from './Interfaz.tsx';
import { Poster } from './Poster.tsx';
import { useArmeria } from './useArmeria.ts';

export default function Armeria() {
  const { estado, acciones } = useArmeria();
  return (
    <InterfazArmeria estado={estado} acciones={acciones}>
      <Poster acciones={acciones} />
    </InterfazArmeria>
  );
}
