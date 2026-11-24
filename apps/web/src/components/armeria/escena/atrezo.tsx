// Atrezo de airsoft para vestir la sala SIN réplicas ni armas (Javi, 22-11-2026): gafas, cascos, chalecos,
// botes de bolas, cajas de cartón y maletines etiquetados, dianas de papel, planos enmarcados, herramientas,
// panel perforado, linterna y calibre. Todo es geometría propia y procedural (principio 5: nada de terceros) y
// va con medidas reales en metros. Cada pieza tiene su origen en la base (y = 0), centrada en x y z.
import { colors } from '@taller6mm/ui/tokens';
import { useMemo } from 'react';
import { MeshStandardMaterial } from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { Caja, Cilindro, type V3 } from './geom.tsx';
import type { Materiales } from './materiales.ts';
import { texturaDiana, texturaEtiqueta, texturaPlano, texturaRegla } from './texturas.ts';

/** Material con un mapa de etiqueta o de papel; se crea una vez por etiqueta. */
function usarMapa(mapa: ConstructorParameters<typeof MeshStandardMaterial>[0]) {
  // El papel blanco puro se quemaba bajo los focos (critico-diseno, 24-11-2026): el albedo máximo del papel es ~0,5
  // lineal, como un folio real en una sala en penumbra, y la tinta conserva su contraste.
  return new MeshStandardMaterial({ color: '#c9c6bd', ...mapa });
}

/** Etiqueta de papel pegada en una cara frontal (mira a +z). */
export function Etiqueta({
  p,
  t,
  codigo,
  linea2,
  papel,
}: {
  p: V3;
  t: readonly [number, number];
  codigo: string;
  linea2: string;
  papel?: string;
}) {
  const material = useMemo(
    () => usarMapa({ map: texturaEtiqueta(codigo, linea2, papel), roughness: 0.7 }),
    [codigo, linea2, papel],
  );
  return (
    <mesh position={[...p]} material={material}>
      <planeGeometry args={[...t]} />
    </mesh>
  );
}

/** Caja de cartón con cinta y etiqueta. */
export function CajaCarton({
  mat,
  t = [0.42, 0.2, 0.36],
  codigo,
  linea2,
}: {
  mat: Materiales;
  t?: V3;
  codigo: string;
  linea2: string;
}) {
  const [ancho, alto, fondo] = t;
  return (
    <group>
      <Caja p={[0, alto / 2, 0]} t={t} m={mat.kraft} />
      <Caja p={[0, alto + 0.0006, 0]} t={[0.07, 0.001, fondo + 0.002]} m={mat.cinta} />
      {/* Solapas: junta central de la tapa y cinta que baja por la cara frontal, con el borde de la solapa marcado */}
      <Caja p={[0, alto + 0.0003, 0]} t={[ancho + 0.002, 0.0006, 0.003]} m={mat.caucho} />
      <Caja p={[0, alto * 0.78, fondo / 2 + 0.0006]} t={[0.07, alto * 0.44, 0.0012]} m={mat.cinta} />
      <Caja p={[0, alto * 0.56, fondo / 2 + 0.0004]} t={[ancho + 0.002, 0.0015, 0.0008]} m={mat.caucho} />
      <Etiqueta
        p={[-ancho * 0.18, alto * 0.46, fondo / 2 + 0.001]}
        t={[ancho * 0.36, alto * 0.38]}
        codigo={codigo}
        linea2={linea2}
      />
    </group>
  );
}

/** Diana de papel clavada: hoja con círculos e impactos. */
export function Diana({ semilla, ancho = 0.2 }: { semilla: number; ancho?: number }) {
  const material = useMemo(() => usarMapa({ map: texturaDiana(semilla), roughness: 0.85 }), [semilla]);
  return (
    <mesh material={material}>
      <planeGeometry args={[ancho, ancho * 1.25]} />
    </mesh>
  );
}

/** Plano enmarcado: papel con alzado y cotas, y marco oscuro. */
export function PlanoEnmarcado({
  mat,
  ancho = 0.5,
  mm,
  titulo,
}: {
  mat: Materiales;
  ancho?: number;
  mm: readonly [number, number];
  titulo: string;
}) {
  const alto = ancho * 0.75;
  const material = useMemo(
    () => usarMapa({ map: texturaPlano(mm[0], mm[1], titulo), color: '#797771', roughness: 0.95 }),
    [mm, titulo],
  );
  return (
    <group>
      <Caja p={[0, 0, 0]} t={[ancho + 0.04, alto + 0.04, 0.025]} m={mat.marco} />
      <mesh position={[0, 0, 0.0135]} material={material}>
        <planeGeometry args={[ancho, alto]} />
      </mesh>
    </group>
  );
}

/** Destornillador colgado por su agujero: mango, vástago y punta. */
export function Destornillador({
  mat,
  mango,
}: {
  mat: Materiales;
  mango: 'destornilladorNaranja' | 'destornilladorOlivo';
}) {
  return (
    <group>
      <Cilindro p={[0, -0.05, 0]} rad={0.0145} h={0.1} m={mat[mango]} seg={14} />
      <Cilindro p={[0, -0.135, 0]} rad={0.0035} h={0.07} m={mat.aceroClaro} seg={8} />
      <Cilindro p={[0, -0.0, 0]} rad={0.012} h={0.012} m={mat.caucho} seg={14} />
    </group>
  );
}

/** Alicate colgado: dos mangos en V, bisagra y mordazas. */
export function Alicate({ mat }: { mat: Materiales }) {
  return (
    <group>
      {[-1, 1].map((lado) => (
        <group key={`mango-${lado}`}>
          <Caja
            p={[lado * 0.016, -0.045, 0]}
            t={[0.02, 0.09, 0.014]}
            m={mat.destornilladorNaranja}
            r={[0, 0, lado * -0.08]}
          />
          <Caja p={[lado * 0.006, -0.12, 0]} t={[0.014, 0.065, 0.011]} m={mat.aceroClaro} r={[0, 0, lado * 0.1]} />
        </group>
      ))}
      <Cilindro p={[0, -0.095, 0]} rad={0.007} h={0.016} m={mat.acero} r={[Math.PI / 2, 0, 0]} />
    </group>
  );
}

/** Juego de llaves allen: tres L de distinto tamaño. */
export function LlavesAllen({ mat }: { mat: Materiales }) {
  return (
    <group>
      {[0.1, 0.13, 0.16].map((largo, i) => (
        <group key={`llave-${largo}`} position={[(i - 1) * 0.018, 0, 0]}>
          <Caja p={[0, -largo / 2, 0]} t={[0.005, largo, 0.005]} m={mat.aceroClaro} />
          <Caja p={[0.025, -largo, 0]} t={[0.05, 0.005, 0.005]} m={mat.aceroClaro} />
        </group>
      ))}
    </group>
  );
}

/** Maletín rígido apilable con asa, dos cierres y etiqueta. */
export function Maletin({
  mat,
  codigo,
  linea2,
  ancho = 1.18,
}: {
  mat: Materiales;
  codigo: string;
  linea2: string;
  ancho?: number;
}) {
  const cuerpo = useMemo(() => new RoundedBoxGeometry(ancho, 0.15, 0.44, 3, 0.03), [ancho]);
  return (
    <group>
      <mesh geometry={cuerpo} material={mat.maletin} />
      {/* Cierres */}
      {[-ancho * 0.27, ancho * 0.27].map((x) => (
        <group key={`cierre-${x}`}>
          <Caja p={[x, 0.005, 0.225]} t={[0.07, 0.05, 0.02]} m={mat.acero} />
          <Caja p={[x, 0.034, 0.234]} t={[0.05, 0.012, 0.006]} m={mat.aceroClaro} />
        </group>
      ))}
      {/* Asa */}
      <Caja p={[0, 0.082, 0.0]} t={[0.2, 0.014, 0.05]} m={mat.polimeroNegro} />
      <Caja p={[0, 0.0, 0.2275]} t={[0.2, 0.026, 0.03]} m={mat.polimeroNegro} />
      <Etiqueta p={[ancho * 0.36, 0.015, 0.2215]} t={[0.14, 0.07]} codigo={codigo} linea2={linea2} />
    </group>
  );
}

/** Carpeta de anillas de pie, con etiqueta en el lomo. */
export function Carpeta({
  mat,
  alto,
  color,
  codigo,
  linea2,
}: {
  mat: Materiales;
  alto: number;
  color: MeshStandardMaterial;
  codigo: string;
  linea2: string;
}) {
  return (
    <group>
      <mesh position={[0, alto / 2, 0]} material={color}>
        <boxGeometry args={[0.065, alto, 0.3]} />
      </mesh>
      <Etiqueta p={[0, alto * 0.62, 0.1505]} t={[0.05, alto * 0.34]} codigo={codigo} linea2={linea2} />
      <Caja p={[0, 0.003, 0.0]} t={[0.067, 0.006, 0.3]} m={mat.caucho} />
    </group>
  );
}

/** Colores de las carpetas: láminas del plano de cotas y tintas apagadas, sin saturar. */
export const TINTAS_CARPETA = [
  colors.acero,
  colors['verde-ranger'],
  colors.fde,
  colors.grafito,
  '#5b3a2a',
  '#2c3a4a',
] as const;

/** Regla vertical de papel en milímetros, a escala 1:1, para pegar en un lateral. Mira a +z; se gira desde fuera. */
export function Regla({ mm }: { mm: number }) {
  const material = useMemo(() => usarMapa({ map: texturaRegla(mm), roughness: 0.8 }), [mm]);
  return (
    <mesh material={material}>
      <planeGeometry args={[0.096, mm / 1000]} />
    </mesh>
  );
}

/** Hoja de plano sobre el tablero: papel con alzado y cotas, tumbada. */
export function HojaPlano({
  ancho = 0.32,
  mm,
  titulo,
}: {
  ancho?: number;
  mm: readonly [number, number];
  titulo: string;
}) {
  const material = useMemo(
    () => usarMapa({ map: texturaPlano(mm[0], mm[1], titulo), color: '#a7a49c', roughness: 0.9 }),
    [mm, titulo],
  );
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} material={material}>
      <planeGeometry args={[ancho, ancho * 0.75]} />
    </mesh>
  );
}
