// Piezas geométricas comunes de la sala: caja, cilindro, sombras y alias de vectores. Sin lógica de La Armería.
import { type RefObject, useLayoutEffect } from 'react';
import type { Group, Material, Mesh } from 'three';

export type V3 = readonly [number, number, number];

/** Caja de `t` (ancho, alto, fondo) en `p`, con rotación `r` (rad). */
export function Caja({ p, t, m, r = [0, 0, 0] }: { p: V3; t: V3; m: Material; r?: V3 }) {
  return (
    <mesh position={[...p]} rotation={[...r]} material={m}>
      <boxGeometry args={[...t]} />
    </mesh>
  );
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
