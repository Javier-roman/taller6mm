// Atrezo de airsoft para vestir la sala SIN réplicas ni armas (Javi, 22-11-2026): gafas, cascos, chalecos,
// botes de bolas, cajas de cartón y maletines etiquetados, dianas de papel, planos enmarcados, herramientas,
// panel perforado, linterna y calibre. Todo es geometría propia y procedural (principio 5: nada de terceros) y
// va con medidas reales en metros. Cada pieza tiene su origen en la base (y = 0), centrada en x y z.
import { colors } from '@taller6mm/ui/tokens';
import { useMemo } from 'react';
import { MeshStandardMaterial, SphereGeometry } from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { Caja, Cilindro, type V3 } from './geom.tsx';
import type { Materiales } from './materiales.ts';
import { texturaDiana, texturaEtiqueta, texturaPlano, texturaRegla } from './texturas.ts';

/** Material con un mapa de etiqueta o de papel; se crea una vez por etiqueta. */
function usarMapa(mapa: ConstructorParameters<typeof MeshStandardMaterial>[0]) {
  return new MeshStandardMaterial(mapa);
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

/** Gafas de protección colgadas de un gancho por su goma: montura, lente tintada y goma en bucle. */
export function Gafas({ mat, giro = 0 }: { mat: Materiales; giro?: number }) {
  return (
    <group rotation={[0, giro, 0]} scale={1.5}>
      {/* Gancho y bucle de la goma */}
      <Cilindro p={[0, 0.17, 0]} rad={0.005} h={0.03} m={mat.aceroClaro} r={[Math.PI / 2, 0, 0]} />
      <mesh position={[0, 0.095, 0]} scale={[1, 1.55, 1]} material={mat.polimeroOd}>
        <torusGeometry args={[0.052, 0.005, 6, 28]} />
      </mesh>
      {/* Montura y lente */}
      <mesh position={[0, 0.025, 0]} material={mat.polimeroFde}>
        <boxGeometry args={[0.17, 0.062, 0.034]} />
      </mesh>
      <mesh position={[0, 0.025, 0.014]} material={mat.lente}>
        <boxGeometry args={[0.15, 0.045, 0.012]} />
      </mesh>
      <Caja p={[0, 0.058, 0.006]} t={[0.172, 0.01, 0.04]} m={mat.caucho} />
    </group>
  );
}

/** Casco ligero con carril frontal y laterales (tipo «fast»), sin picar nada real: cáscara, borde y carriles. */
export function Casco({ mat, tela = 'tela' }: { mat: Materiales; tela?: 'tela' | 'telaFde' | 'telaNegra' }) {
  const cascara = useMemo(() => new SphereGeometry(0.13, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2), []);
  const material = mat[tela];
  return (
    <group>
      <mesh geometry={cascara} scale={[1, 0.78, 1.18]} position={[0, 0.002, 0]} material={material} />
      {/* Borde inferior: cinta de goma */}
      <mesh position={[0, 0.003, 0]} rotation={[Math.PI / 2, 0, 0]} scale={[1, 1.18, 1]} material={mat.caucho}>
        <torusGeometry args={[0.131, 0.0055, 8, 40]} />
      </mesh>
      {/* Carril frontal y carriles laterales */}
      <Caja p={[0, 0.068, 0.145]} t={[0.05, 0.026, 0.014]} m={mat.acero} r={[0.52, 0, 0]} />
      {[-1, 1].map((lado) => (
        <Caja key={`riel-${lado}`} p={[lado * 0.128, 0.05, 0.02]} t={[0.012, 0.034, 0.09]} m={mat.acero} />
      ))}
      {/* Cinta de ajuste trasera */}
      <Caja p={[0, 0.018, -0.15]} t={[0.1, 0.018, 0.018]} m={mat.caucho} />
    </group>
  );
}

/** Chaleco portaplacas colgado: faldón, hombreras, fajín y tres bolsillos al frente. */
export function Chaleco({ mat, tela = 'tela' }: { mat: Materiales; tela?: 'tela' | 'telaFde' | 'telaNegra' }) {
  const material = mat[tela];
  const cuerpo = useMemo(() => new RoundedBoxGeometry(0.4, 0.46, 0.05, 3, 0.02), []);
  const bolsillo = useMemo(() => new RoundedBoxGeometry(0.095, 0.13, 0.04, 2, 0.012), []);
  return (
    <group>
      <mesh geometry={cuerpo} position={[0, -0.23, 0]} material={material} />
      {[-1, 1].map((lado) => (
        <Caja
          key={`hombrera-${lado}`}
          p={[lado * 0.125, 0.025, 0]}
          t={[0.07, 0.1, 0.03]}
          m={material}
          r={[0, 0, lado * 0.08]}
        />
      ))}
      <Caja p={[0, -0.36, 0.03]} t={[0.44, 0.07, 0.03]} m={mat.caucho} />
      {[-0.115, 0, 0.115].map((x) => (
        <mesh key={`bolsillo-${x}`} geometry={bolsillo} position={[x, -0.27, 0.042]} material={material} />
      ))}
      {[-0.115, 0, 0.115].map((x) => (
        <Caja key={`solapa-${x}`} p={[x, -0.215, 0.064]} t={[0.09, 0.025, 0.006]} m={mat.caucho} />
      ))}
      <Cilindro p={[0, 0.085, 0]} rad={0.006} h={0.03} m={mat.aceroClaro} r={[Math.PI / 2, 0, 0]} />
    </group>
  );
}

/** Bote de bolas: cuerpo blanco, tapón naranja y etiqueta de papel con medida. */
export function Bote({
  mat,
  codigo = '6 mm',
  linea2 = '0,20 g',
}: {
  mat: Materiales;
  codigo?: string;
  linea2?: string;
}) {
  return (
    <group>
      <Cilindro p={[0, 0.1, 0]} rad={0.055} h={0.2} m={mat.plasticoBlanco} seg={28} />
      <Cilindro p={[0, 0.215, 0]} rad={0.058} h={0.03} m={mat.tapaNaranja} seg={28} />
      <Etiqueta p={[0, 0.1, 0.0557]} t={[0.062, 0.08]} codigo={codigo} linea2={linea2} />
    </group>
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

/** Cinta métrica: carcasa con cinta asomando. */
export function CintaMetrica({ mat }: { mat: Materiales }) {
  return (
    <group>
      <Cilindro p={[0, -0.04, 0]} rad={0.04} h={0.05} m={mat.laton} r={[Math.PI / 2, 0, 0]} seg={28} />
      <Caja p={[0.045, -0.075, 0]} t={[0.03, 0.012, 0.045]} m={mat.polimeroNegro} />
    </group>
  );
}

/** Linterna de mano tumbada o colgada: cuerpo, cabeza y anillo. */
export function Linterna({ mat }: { mat: Materiales }) {
  return (
    <group>
      <Cilindro p={[0, 0, 0]} rad={0.0185} h={0.15} m={mat.polimeroNegro} seg={18} />
      <Cilindro p={[0, 0.0925, 0]} rad={0.027} h={0.04} m={mat.acero} seg={18} />
      <Cilindro p={[0, 0.1135, 0]} rad={0.022} h={0.004} m={mat.vidrio} seg={18} />
      <Cilindro p={[0, -0.02, 0]} rad={0.0195} h={0.008} m={mat.aceroClaro} seg={18} />
      <Cilindro p={[0, 0.03, 0]} rad={0.0195} h={0.008} m={mat.aceroClaro} seg={18} />
    </group>
  );
}

/** Calibre digital (pie de rey): regla, nonio y mordazas, tumbado. */
export function Calibre({ mat }: { mat: Materiales }) {
  return (
    <group>
      <Caja p={[0, 0.003, 0]} t={[0.2, 0.006, 0.018]} m={mat.aceroClaro} />
      <Caja p={[0.07, 0.009, 0.004]} t={[0.05, 0.016, 0.026]} m={mat.polimeroNegro} />
      <Caja p={[-0.098, 0.012, 0]} t={[0.004, 0.026, 0.018]} m={mat.aceroClaro} />
      <Caja p={[0.047, 0.012, 0]} t={[0.004, 0.024, 0.018]} m={mat.aceroClaro} />
    </group>
  );
}

/** Caja de herramientas abierta: cuerpo, asa, bandeja con piezas sueltas (tornillos y bolsitas). */
export function CajaHerramientas({ mat }: { mat: Materiales }) {
  const cuerpo = useMemo(() => new RoundedBoxGeometry(0.42, 0.16, 0.2, 3, 0.012), []);
  return (
    <group>
      <mesh geometry={cuerpo} position={[0, 0.08, 0]} material={mat.acero} />
      <Caja p={[0, 0.162, 0]} t={[0.4, 0.004, 0.18]} m={mat.caucho} />
      {[-0.13, -0.045, 0.04, 0.125].map((x, i) => (
        <Caja key={`hueco-${x}`} p={[x, 0.166, i % 2 ? 0.03 : -0.02]} t={[0.07, 0.01, 0.08]} m={mat.polimeroNegro} />
      ))}
      <Caja p={[0, 0.19, 0.0]} t={[0.2, 0.012, 0.012]} m={mat.destornilladorNaranja} r={[0, 0.0, 0]} />
      {[-0.19, 0.19].map((x) => (
        <Caja key={`soporte-asa-${x}`} p={[x, 0.17, 0]} t={[0.012, 0.04, 0.02]} m={mat.aceroClaro} />
      ))}
      <Caja p={[0, 0.1, 0.1005]} t={[0.05, 0.03, 0.004]} m={mat.aceroClaro} />
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

/** Batería LiPo: funda azul con etiqueta y el cable con conector. */
export function Bateria({ mat }: { mat: Materiales }) {
  return (
    <group>
      <Caja p={[0, 0.0105, 0]} t={[0.13, 0.021, 0.04]} m={mat.bateria} />
      <Etiqueta p={[0, 0.0222, 0]} t={[0.06, 0.026]} codigo="11,1 V" linea2="LiPo 1300" />
      <Caja p={[0.075, 0.009, 0]} t={[0.03, 0.01, 0.016]} m={mat.polimeroNegro} />
      <Cilindro
        p={[0.095, 0.009, 0.012]}
        rad={0.003}
        h={0.05}
        m={mat.destornilladorNaranja}
        r={[0, 0, Math.PI / 2]}
        seg={8}
      />
    </group>
  );
}

/** Bombona de green gas: cuerpo verde con tapa metálica y etiqueta. */
export function Bombona({ mat }: { mat: Materiales }) {
  return (
    <group>
      <Cilindro p={[0, 0.09, 0]} rad={0.032} h={0.18} m={mat.bombona} seg={24} />
      <Cilindro p={[0, 0.19, 0]} rad={0.014} h={0.02} m={mat.aceroClaro} seg={16} />
      <Cilindro p={[0, 0.205, 0]} rad={0.008} h={0.012} m={mat.aceroClaro} seg={12} />
      <Etiqueta p={[0, 0.09, 0.0322]} t={[0.05, 0.07]} codigo="GAS" linea2="green" />
    </group>
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

/** Soporte de casco: pie, columna y cabeza redondeada donde descansa. */
export function SoporteCasco({ mat }: { mat: Materiales }) {
  return (
    <group>
      <Cilindro p={[0, 0.008, 0]} rad={0.07} h={0.016} m={mat.acero} seg={24} />
      <Cilindro p={[0, 0.07, 0]} rad={0.012} h={0.12} m={mat.acero} seg={12} />
      <mesh position={[0, 0.138, 0]} material={mat.acero} scale={[1, 0.6, 1.2]}>
        <sphereGeometry args={[0.07, 20, 12]} />
      </mesh>
    </group>
  );
}
