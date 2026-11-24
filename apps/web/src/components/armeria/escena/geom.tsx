// Piezas geométricas comunes de la sala: caja biselada, cilindro, sombras y alias de vectores. Sin lógica de La Armería.
import { type RefObject, useLayoutEffect, useMemo } from 'react';
import { type BufferGeometry, type Group, type Material, type Mesh, Quaternion, Vector3 } from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';

export type V3 = readonly [number, number, number];

const biselados = new Map<string, BufferGeometry>();

/**
 * Caja con aristas biseladas (4 mm como mucho): las aristas recogen la luz de los tubos y dejan de parecer de
 * cuchilla (critico-diseno, 23-11-2026: lo que más delata una escena de plantilla). Cada medida se crea una vez.
 */
function cajaBiselada([ancho, alto, fondo]: V3): BufferGeometry {
  const radio = Math.min(0.004, Math.min(ancho, alto, fondo) * 0.42);
  const clave = `${ancho.toFixed(4)}|${alto.toFixed(4)}|${fondo.toFixed(4)}`;
  let g = biselados.get(clave);
  if (!g) {
    g = new RoundedBoxGeometry(ancho, alto, fondo, 2, radio);
    biselados.set(clave, g);
  }
  return g;
}

/** Caja de `t` (ancho, alto, fondo) en `p`, con rotación `r` (rad). */
export function Caja({ p, t, m, r = [0, 0, 0] }: { p: V3; t: V3; m: Material; r?: V3 }) {
  const geometria = useMemo(() => cajaBiselada(t), [t]);
  return <mesh position={[...p]} rotation={[...r]} material={m} geometry={geometria} />;
}

/** Cilindro de radio `rad` y altura `h`, de pie por defecto; `r` lo gira (p. ej. tumbado sobre su eje z). */
export function Cilindro({
  p,
  rad,
  h,
  m,
  r = [0, 0, 0],
  seg = 20,
}: {
  p: V3;
  rad: number;
  h: number;
  m: Material;
  r?: V3;
  seg?: number;
}) {
  return (
    <mesh position={[...p]} rotation={[...r]} material={m}>
      <cylinderGeometry args={[rad, rad, h, seg]} />
    </mesh>
  );
}

/** Barra cilíndrica entre dos puntos `a` y `b` (m): brazos de lámpara, hilos, cables. */
export function Barra({ a, b, rad, m, seg = 12 }: { a: V3; b: V3; rad: number; m: Material; seg?: number }) {
  const { posicion, largo, cuaternion } = useMemo(() => {
    const desde = new Vector3(...a);
    const dir = new Vector3(...b).sub(desde);
    const largo = dir.length();
    return {
      posicion: desde.clone().addScaledVector(dir, 0.5).toArray() as [number, number, number],
      largo,
      cuaternion: new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), dir.normalize()),
    };
  }, [a, b]);
  return (
    <mesh position={posicion} quaternion={cuaternion} material={m}>
      <cylinderGeometry args={[rad, rad, largo, seg]} />
    </mesh>
  );
}

/** Sombras para todo lo que cuelga del grupo. */
export function useSombras(grupo: RefObject<Group | null>) {
  useLayoutEffect(() => {
    grupo.current?.traverse((o) => {
      if ((o as Mesh).isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
  }, [grupo]);
}
