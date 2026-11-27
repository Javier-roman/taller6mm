// Hook de La Armería: une el estado puro (estado.ts) con el navegador (matchMedia, URL, localStorage).
// Las acciones son estables (no cambian entre renders) para no volver a renderizar la escena sin motivo.
import { useEffect, useMemo, useState } from 'react';
import { almacenLocal, CLAVES, ESTADO_INICIAL, type EstadoArmeria, guardar, type Luz, luzInicial } from './estado.ts';

export interface Acciones {
  apuntar: (id: string | null) => void;
  enfocar: (id: string | null) => void;
  abrir: (id: string) => void;
  cerrar: () => void;
  cambiarLuz: (luz: Luz) => void;
}

export function useArmeria() {
  const [estado, setEstado] = useState<EstadoArmeria>(ESTADO_INICIAL);

  // Una sola vez, ya en el navegador: nada de esto existe en el servidor y el primer render debe coincidir
  // con el HTML que llegó (póster y navegación en penumbra).
  useEffect(() => {
    const parametros = new URLSearchParams(location.search);
    const movimiento = matchMedia('(prefers-reduced-motion: reduce)');
    const actualizar = () => setEstado((e) => ({ ...e, reducido: movimiento.matches }));
    movimiento.addEventListener('change', actualizar);
    setEstado((e) => ({
      ...e,
      hidratado: true,
      reducido: movimiento.matches,
      luz: luzInicial(parametros.get('luz'), almacenLocal()),
    }));
    return () => movimiento.removeEventListener('change', actualizar);
  }, []);

  const acciones = useMemo<Acciones>(
    () => ({
      apuntar: (id) => setEstado((e) => (e.apuntada === id ? e : { ...e, apuntada: id })),
      enfocar: (id) => setEstado((e) => (e.enfocada === id ? e : { ...e, enfocada: id })),
      abrir: (id) => setEstado((e) => ({ ...e, abierta: id })),
      cerrar: () => setEstado((e) => ({ ...e, abierta: null })),
      cambiarLuz: (luz) => {
        setEstado((e) => ({ ...e, luz }));
        guardar(almacenLocal(), CLAVES.luz, luz);
      },
    }),
    [],
  );

  return { estado, acciones };
}
