// La sala de La Armería en 3D (prototipos de la Fase 1): pared de ladrillo, suelo de hormigón con
// raíles, tubos LED en el techo y tres cuerpos de compactus verde oliva casi negro (ref-08), con sus
// zonas, más el banco de trabajo con flexo. Todo es geometría propia o procedural.
// La sala no decide nada: pinta lo que diga `ControlSala`. El prototipo A lo alimenta con el
// director (intro, hover, linterna) y el horneado del B fija cada grupo de luz por separado.
import { type ThreeEvent, useFrame, useThree } from '@react-three/fiber';
import { BRAND } from '@taller6mm/ui/brand';
import { colors } from '@taller6mm/ui/tokens';
import { type ReactNode, type RefObject, useLayoutEffect, useMemo, useRef } from 'react';
import {
  type AmbientLight,
  Color,
  type Group,
  type HemisphereLight,
  type Mesh,
  MeshStandardMaterial,
  Object3D,
  PMREMGenerator,
  type PointLight,
  type SpotLight,
  type Texture,
  Vector3,
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { crearIluminacion, type Iluminacion } from './director.ts';
import {
  texturaCorcho,
  texturaHormigon,
  texturaLadrillo,
  texturaNogal,
  texturaPantalla,
  texturaRotulo,
  texturaTapete,
  texturaTiraNumerada,
} from './texturas.ts';
import { BANCO, ESTANTERIAS, type Estanteria, MUEBLE, ORDEN_ESTANTERIAS, ZONAS, type Zona } from './zonas.ts';

export interface ControlSala {
  luz: Iluminacion;
  zonaActiva: string | null;
  /** Punto del mundo al que apunta la linterna-cursor. */
  linterna: Vector3;
  /** Cuánto ha rodado cada cuerpo del compactus hacia delante sobre sus raíles (m). */
  desplazamiento: Record<Estanteria, number>;
  colorTubo: Color;
  /** «baja»: sin sombras (móvil o GPU modesta). */
  calidad: 'alta' | 'baja';
}

export const crearControl = (luz: Iluminacion = crearIluminacion(1)): ControlSala => ({
  luz,
  zonaActiva: null,
  linterna: new Vector3(0, 1.4, MUEBLE.frente),
  desplazamiento: { izquierda: 0, centro: 0, derecha: 0 },
  colorTubo: new Color('#dfe9ff'),
  calidad: 'alta',
});

/** Intensidades de referencia (candelas: luces físicas de three r155+), ajustadas con capturas. */
export const LUZ = {
  tubo: 85,
  tuboEmisivo: 3.4,
  flexo: 20,
  bombilla: 8,
  vitrina: 9,
  led: 2.6,
  ambiente: 0.06,
  hemisferio: 0.1,
  acento: 34,
  linterna: 34,
  rotuloBase: 0.22,
  rotuloActivo: 0.55,
  marca: 0.9,
  pantalla: 0.9,
  /** Reflejos del entorno (IBL): sin ellos el metal se ve negro. */
  entorno: 0.08,
} as const;

const CALIDO = new Color('#ffb46a');
const xDe = (e: Estanteria) => ESTANTERIAS[e].x;
const zFondo = MUEBLE.frente - MUEBLE.fondo / 2;

function useMateriales() {
  return useMemo(() => {
    const m = (p: ConstructorParameters<typeof MeshStandardMaterial>[0]) => new MeshStandardMaterial(p);
    // Chapa de compactus: verde oliva tan oscuro que casi es negro (ref-08).
    const verde = new Color(colors['verde-ranger']).multiplyScalar(0.42);
    const ladrillo = texturaLadrillo([7, 3]);
    const hormigon = texturaHormigon([8, 6]);
    const pantalla = texturaPantalla();
    return {
      ladrillo: m({ map: ladrillo.mapa, normalMap: ladrillo.normal, roughness: 0.92 }),
      hormigon: m({ map: hormigon.mapa, normalMap: hormigon.normal, roughness: 0.82, metalness: 0.05 }),
      chapa: m({ color: verde, roughness: 0.48, metalness: 0.5 }),
      chapaOscura: m({ color: verde.clone().multiplyScalar(0.45), roughness: 0.7, metalness: 0.3 }),
      techo: m({ color: '#121315', roughness: 1 }),
      acero: m({ color: '#2b2f34', roughness: 0.32, metalness: 0.85 }),
      rail: m({ color: '#8a9097', roughness: 0.22, metalness: 0.95 }),
      polimeroNegro: m({ color: '#17191c', roughness: 0.62 }),
      polimeroFde: m({ color: colors.fde, roughness: 0.7 }),
      polimeroOd: m({ color: colors['verde-ranger'], roughness: 0.7 }),
      maletin: m({ color: '#1b1d20', roughness: 0.46, metalness: 0.1 }),
      kraft: m({ color: '#a8854f', roughness: 0.9 }),
      nogal: m({ map: texturaNogal(), roughness: 0.55 }),
      tapete: m({ map: texturaTapete(), roughness: 0.92 }),
      corcho: m({ map: texturaCorcho(), roughness: 0.95 }),
      papel: m({ color: colors.hueso, roughness: 0.85 }),
      laton: m({ color: colors.laton, roughness: 0.3, metalness: 0.95 }),
      vidrio: m({
        color: '#d8e4ea',
        roughness: 0.08,
        metalness: 0,
        transparent: true,
        opacity: 0.05,
        depthWrite: false,
      }),
      taquilla: m({ color: '#3b434b', roughness: 0.42, metalness: 0.65 }),
      pantalla: m({ map: pantalla, emissiveMap: pantalla, emissive: '#ffffff', emissiveIntensity: LUZ.pantalla }),
      led: m({ color: '#fff3e2', emissive: CALIDO, emissiveIntensity: LUZ.led, roughness: 0.3 }),
      bombilla: m({ color: '#fff3e2', emissive: CALIDO, emissiveIntensity: LUZ.bombilla, roughness: 0.3 }),
    };
  }, []);
}

type Materiales = ReturnType<typeof useMateriales>;

/** Sombras para todo lo que cuelga del grupo. */
function useSombras(grupo: RefObject<Group | null>) {
  useLayoutEffect(() => {
    grupo.current?.traverse((o) => {
      if ((o as Mesh).isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
  }, [grupo]);
}

type V3 = readonly [number, number, number];

function Caja({ p, t, m, r = [0, 0, 0] }: { p: V3; t: V3; m: MeshStandardMaterial; r?: V3 }) {
  return (
    <mesh position={[...p]} rotation={[...r]} material={m}>
      <boxGeometry args={[...t]} />
    </mesh>
  );
}

/** Silueta genérica de réplica (culata abajo): no reproduce ningún modelo real ni sus marcajes. */
function Replica({ material, optica, mat }: { material: MeshStandardMaterial; optica?: boolean; mat: Materiales }) {
  return (
    <group>
      <Caja p={[0, 0.84, 0]} t={[0.022, 0.24, 0.022]} m={mat.acero} />
      <Caja p={[0, 0.58, 0]} t={[0.052, 0.3, 0.05]} m={material} />
      <Caja p={[0.004, 0.32, 0]} t={[0.07, 0.24, 0.056]} m={material} />
      <Caja p={[0.07, 0.32, 0]} t={[0.08, 0.05, 0.03]} r={[0, 0, -0.2]} m={mat.polimeroNegro} />
      <Caja p={[-0.05, 0.22, 0]} t={[0.07, 0.035, 0.034]} r={[0, 0, 0.5]} m={material} />
      <Caja p={[0, 0.1, 0]} t={[0.08, 0.2, 0.046]} m={material} />
      {optica ? (
        <mesh position={[-0.058, 0.36, 0]} material={mat.polimeroNegro}>
          <cylinderGeometry args={[0.018, 0.022, 0.16, 12]} />
        </mesh>
      ) : null}
    </group>
  );
}

/** Estructura de un cuerpo de compactus: fondo, laterales, techo, zócalo, balda y volante. */
function Mueble({ mat, children }: { mat: Materiales; children?: ReactNode }) {
  const g = useRef<Group>(null);
  useSombras(g);
  const { ancho, alto, fondo, frente, baldaMedia, zocalo } = MUEBLE;
  return (
    <group ref={g}>
      <Caja p={[0, alto / 2, zFondo - fondo / 2 + 0.01]} t={[ancho, alto, 0.02]} m={mat.chapaOscura} />
      <Caja p={[-ancho / 2, alto / 2, zFondo]} t={[0.05, alto, fondo]} m={mat.chapa} />
      <Caja p={[ancho / 2, alto / 2, zFondo]} t={[0.05, alto, fondo]} m={mat.chapa} />
      <Caja p={[0, alto, zFondo]} t={[ancho + 0.05, 0.04, fondo]} m={mat.chapa} />
      <Caja p={[0, zocalo / 2, zFondo]} t={[ancho + 0.05, zocalo, fondo + 0.04]} m={mat.chapaOscura} />
      <Caja p={[0, baldaMedia, zFondo]} t={[ancho, 0.03, fondo]} m={mat.chapa} />
      <Caja p={[0, baldaMedia - 0.03, frente - 0.01]} t={[ancho, 0.07, 0.02]} m={mat.chapa} />
      {/* Volante superior, donde va el rótulo de la estantería */}
      <Caja p={[0, alto + 0.17, frente - 0.03]} t={[ancho + 0.05, 0.3, 0.03]} m={mat.chapa} />
      {/* Volante de maniobra del compactus (lateral izquierdo) */}
      <group position={[-ancho / 2 - 0.035, 1.05, frente - 0.12]} rotation={[0, Math.PI / 2, 0]}>
        <mesh material={mat.acero}>
          <torusGeometry args={[0.13, 0.012, 8, 28]} />
        </mesh>
        {[0, 1, 2].map((i) => (
          <Caja key={`radio-${i}`} p={[0, 0, 0]} t={[0.26, 0.016, 0.016]} r={[0, 0, (i * Math.PI) / 3]} m={mat.acero} />
        ))}
      </group>
      {children}
    </group>
  );
}

function Armero({ mat }: { mat: Materiales }) {
  const materiales = [mat.polimeroNegro, mat.polimeroFde, mat.polimeroNegro, mat.polimeroOd];
  const huecos = 9;
  const util = MUEBLE.ancho - 0.2;
  const paso = util / huecos;
  const tira = useMemo(() => texturaTiraNumerada(1, huecos), []);
  return (
    <group>
      {Array.from({ length: huecos + 1 }, (_, i) => (
        <Caja
          key={`sep-${i}`}
          p={[-util / 2 + i * paso, MUEBLE.baldaMedia + 0.2, zFondo]}
          t={[0.012, 0.38, MUEBLE.fondo - 0.08]}
          m={mat.chapa}
        />
      ))}
      {Array.from({ length: huecos }, (_, i) => (
        <group
          key={`rep-${i}`}
          position={[-util / 2 + (i + 0.5) * paso, MUEBLE.baldaMedia + 0.02, zFondo + 0.03]}
          rotation={[0, 0.25 * ((i % 3) - 1), 0]}
          scale={1.05}
        >
          <Replica material={materiales[i % materiales.length] ?? mat.polimeroNegro} optica={i % 2 === 0} mat={mat} />
        </group>
      ))}
      <mesh position={[0, MUEBLE.baldaMedia - 0.03, MUEBLE.frente + 0.001]}>
        <planeGeometry args={[util, 0.05]} />
        <meshStandardMaterial map={tira} roughness={0.7} />
      </mesh>
    </group>
  );
}

function Almacen({ mat }: { mat: Materiales }) {
  const maletin = useMemo(() => new RoundedBoxGeometry(1.18, 0.15, 0.44, 3, 0.03), []);
  return (
    <group>
      {[0, 1, 2, 3].map((fila) =>
        [-0.63, 0.63].map((x) => (
          <group key={`m-${fila}-${x}`} position={[x, MUEBLE.zocalo + 0.085 + fila * 0.165, zFondo + 0.03]}>
            <mesh geometry={maletin} material={mat.maletin} />
            <Caja p={[-0.32, 0, 0.225]} t={[0.07, 0.045, 0.02]} m={mat.acero} />
            <Caja p={[0.32, 0, 0.225]} t={[0.07, 0.045, 0.02]} m={mat.acero} />
            <Caja p={[0, 0.0, 0.232]} t={[0.2, 0.026, 0.03]} m={mat.polimeroNegro} />
            <Caja p={[0.46, 0.02, 0.222]} t={[0.1, 0.05, 0.002]} m={mat.papel} />
          </group>
        )),
      )}
      {[-0.95, -0.35, 0.3, 0.92].map((x, i) => (
        <Caja
          key={`k-${x}`}
          p={[x, 0.93 + (i % 2) * 0.02, zFondo + 0.04]}
          t={[0.42, 0.2 + (i % 2) * 0.05, 0.36]}
          m={mat.kraft}
        />
      ))}
    </group>
  );
}

function Vitrina({ mat, luz }: { mat: Materiales; luz: RefObject<PointLight | null> }) {
  const y0 = MUEBLE.baldaMedia + 0.02;
  const colores = [mat.polimeroFde, mat.polimeroNegro, mat.polimeroOd];
  return (
    <group>
      <Caja p={[0, y0 + 0.05, zFondo + 0.02]} t={[2.4, 0.1, 0.5]} m={mat.nogal} />
      {[-0.78, 0, 0.78].map((x, i) => (
        <group key={`pedestal-${x}`} position={[x, y0 + 0.1, zFondo + 0.04]}>
          <Caja p={[0, 0.07 + i * 0.03, 0]} t={[0.5, 0.14 + i * 0.06, 0.3]} m={mat.polimeroNegro} />
          <group position={[-0.36, 0.2 + i * 0.06, 0]} rotation={[0, 0, -Math.PI / 2]} scale={0.74}>
            <Replica material={colores[i] ?? mat.polimeroNegro} optica mat={mat} />
          </group>
          <Caja p={[0, 0.06 + i * 0.03, 0.155]} t={[0.18, 0.05, 0.01]} m={mat.laton} />
        </group>
      ))}
      {/* Tira LED cálida bajo el techo de la vitrina */}
      <Caja p={[0, MUEBLE.alto - 0.05, MUEBLE.frente - 0.06]} t={[2.4, 0.018, 0.03]} m={mat.led} />
      <pointLight
        ref={luz}
        position={[0, y0 + 1.15, zFondo + 0.12]}
        color={CALIDO}
        intensity={LUZ.vitrina}
        distance={2.6}
        decay={2}
      />
      {[-0.9, -0.3, 0.35, 0.95].map((x) => (
        <Caja key={`b-${x}`} p={[x, 0.32, zFondo + 0.04]} t={[0.5, 0.36, 0.4]} m={x > 0 ? mat.kraft : mat.maletin} />
      ))}
    </group>
  );
}

function Tablon({ mat }: { mat: Materiales }) {
  const notas: [number, number, number][] = [
    [-0.4, 2.3, 0.08],
    [-0.14, 2.36, -0.06],
    [-0.36, 2.04, -0.1],
    [-0.08, 2.1, 0.05],
  ];
  return (
    <group position={[-MUEBLE.ancho / 4, 0, 0]}>
      <Caja p={[0, 2.02, zFondo - 0.25]} t={[1.2, 1.15, 0.03]} m={mat.corcho} />
      {notas.map(([x, y, r]) => (
        <Caja key={`n-${x}-${y}`} p={[x, y, zFondo - 0.23]} t={[0.2, 0.15, 0.004]} r={[0, 0, r]} m={mat.papel} />
      ))}
      <group position={[0.27, 1.5, zFondo + 0.05]} rotation={[0, -0.12, 0]}>
        <Caja p={[0, 0.2, 0]} t={[0.5, 0.33, 0.04]} m={mat.polimeroNegro} />
        <mesh position={[0, 0.2, 0.022]} material={mat.pantalla}>
          <planeGeometry args={[0.46, 0.29]} />
        </mesh>
        <Caja p={[0, 0.0, 0]} t={[0.06, 0.08, 0.06]} m={mat.acero} />
      </group>
    </group>
  );
}

const TINTAS_TIENDA = [colors.laton, colors['estado-ok'], colors.fde, colors['naranja-senal'], colors.niebla];

function Mostrador({ mat }: { mat: Materiales }) {
  const fichas = useMemo(() => TINTAS_TIENDA.map((t) => new MeshStandardMaterial({ color: t, roughness: 0.7 })), []);
  return (
    <group position={[MUEBLE.ancho / 4, 0, 0]}>
      <Caja p={[0, 1.55, zFondo + 0.05]} t={[1.15, 0.05, 0.42]} m={mat.nogal} />
      {fichas.map((f, i) => (
        <group key={`f-${TINTAS_TIENDA[i]}`} position={[-0.4 + i * 0.2, 1.68, zFondo + 0.06]} rotation={[-0.25, 0, 0]}>
          <mesh material={f}>
            <boxGeometry args={[0.15, 0.21, 0.008]} />
          </mesh>
          <Caja p={[0, -0.03, 0.006]} t={[0.1, 0.06, 0.002]} m={mat.papel} />
        </group>
      ))}
      <Caja p={[0, 2.2, zFondo - 0.2]} t={[1.1, 0.5, 0.02]} m={mat.chapaOscura} />
    </group>
  );
}

const TAPAS = ['#5a1f1f', '#1f2a3a', colors['verde-ranger'], '#2a2a2a', '#7a5a2a'];

function Biblioteca({ mat }: { mat: Materiales }) {
  const tapas = useMemo(() => TAPAS.map((c) => new MeshStandardMaterial({ color: c, roughness: 0.75 })), []);
  return (
    <group position={[-MUEBLE.ancho / 4, 0, 0]}>
      {Array.from({ length: 14 }, (_, i) => {
        const alto = 0.3 + ((i * 37) % 11) / 100;
        return (
          <group
            key={`l-${i}`}
            position={[-0.55 + i * 0.08, MUEBLE.zocalo + alto / 2, zFondo + 0.02]}
            rotation={[0, 0, i === 9 ? 0.18 : 0]}
          >
            <mesh material={tapas[i % tapas.length] ?? mat.papel}>
              <boxGeometry args={[0.065, alto, 0.3]} />
            </mesh>
            <Caja p={[0, alto * 0.18, 0.152]} t={[0.04, 0.06, 0.002]} m={mat.papel} />
          </group>
        );
      })}
      {Array.from({ length: 6 }, (_, i) => (
        <Caja
          key={`c-${i}`}
          p={[-0.45 + i * 0.17, 0.72, zFondo + 0.02]}
          t={[0.05, 0.08, 0.32]}
          r={[0, 0, Math.PI / 2]}
          m={mat.kraft}
        />
      ))}
    </group>
  );
}

function Taquilla({ mat, apodo }: { mat: Materiales; apodo: Texture }) {
  const z = MUEBLE.frente;
  return (
    <group position={[MUEBLE.ancho / 4, 0, 0]}>
      <Caja p={[0, 0.66, z - 0.02]} t={[1.18, 1.0, 0.03]} m={mat.taquilla} />
      {Array.from({ length: 5 }, (_, i) => (
        <Caja key={`v-${i}`} p={[0, 0.98 - i * 0.04, z]} t={[0.5, 0.012, 0.012]} m={mat.polimeroNegro} />
      ))}
      <Caja p={[0.46, 0.66, z + 0.01]} t={[0.04, 0.18, 0.03]} m={mat.acero} />
      <mesh position={[0, 0.42, z + 0.001]}>
        <planeGeometry args={[0.8, 0.2]} />
        <meshStandardMaterial map={apodo} roughness={0.6} />
      </mesh>
    </group>
  );
}

function Banco({ mat, flexo }: { mat: Materiales; flexo: RefObject<SpotLight | null> }) {
  const g = useRef<Group>(null);
  useSombras(g);
  const objetivo = useMemo(() => new Object3D(), []);
  const { x, z, ancho, fondo, alto } = BANCO;
  return (
    <group ref={g} position={[x, 0, z]}>
      <primitive object={objetivo} position={[-0.15, alto, 0]} />
      <Caja p={[0, alto - 0.03, 0]} t={[ancho, 0.06, fondo]} m={mat.nogal} />
      {[-1, 1].map((lado) => (
        <group key={`pata-${lado}`}>
          <Caja
            p={[lado * (ancho / 2 - 0.08), (alto - 0.06) / 2, fondo / 2 - 0.08]}
            t={[0.06, alto - 0.06, 0.06]}
            m={mat.acero}
          />
          <Caja
            p={[lado * (ancho / 2 - 0.08), (alto - 0.06) / 2, -fondo / 2 + 0.08]}
            t={[0.06, alto - 0.06, 0.06]}
            m={mat.acero}
          />
        </group>
      ))}
      <Caja p={[0, 0.2, 0]} t={[ancho - 0.2, 0.04, fondo - 0.1]} m={mat.acero} />
      {/* Faldón delantero, donde va el rótulo del banco */}
      <Caja p={[0, alto - 0.12, fondo / 2 + 0.01]} t={[ancho, 0.14, 0.02]} m={mat.acero} />
      <mesh position={[-0.15, alto + 0.003, 0]} rotation={[-Math.PI / 2, 0, 0]} material={mat.tapete}>
        <planeGeometry args={[1.5, 0.66]} />
      </mesh>
      {/* Réplica a medio montar, tumbada sobre el tapete */}
      <group position={[-0.62, alto + 0.03, 0.02]} rotation={[-Math.PI / 2, 0, -Math.PI / 2 + 0.1]}>
        <Replica material={mat.polimeroFde} mat={mat} />
      </group>
      {/* Herramientas */}
      <Caja p={[0.5, alto + 0.02, 0.22]} t={[0.18, 0.02, 0.03]} r={[0, 0.5, 0]} m={mat.acero} />
      <mesh position={[0.35, alto + 0.03, 0.18]} rotation={[0, 0, Math.PI / 2]} material={mat.laton}>
        <cylinderGeometry args={[0.012, 0.012, 0.16, 10]} />
      </mesh>
      <Caja p={[-0.92, alto + 0.03, 0.16]} t={[0.12, 0.06, 0.08]} m={mat.kraft} />
      {/* Flexo: base, brazos, cabeza y bombilla */}
      <group position={[0.78, alto, -0.25]}>
        <mesh material={mat.acero}>
          <cylinderGeometry args={[0.08, 0.09, 0.03, 20]} />
        </mesh>
        <Caja p={[-0.05, 0.28, 0.06]} t={[0.025, 0.56, 0.025]} r={[0.25, 0, 0.2]} m={mat.acero} />
        <Caja p={[-0.25, 0.56, 0.2]} t={[0.025, 0.45, 0.025]} r={[1.05, 0, 0.6]} m={mat.acero} />
        <mesh position={[-0.42, 0.56, 0.32]} rotation={[0.6, 0, 0.5]} material={mat.chapa}>
          <coneGeometry args={[0.09, 0.14, 20, 1, true]} />
        </mesh>
        <mesh position={[-0.44, 0.52, 0.34]} material={mat.bombilla}>
          <sphereGeometry args={[0.03, 12, 12]} />
        </mesh>
        <spotLight
          ref={flexo}
          position={[-0.42, 0.5, 0.34]}
          target={objetivo}
          color={CALIDO}
          intensity={LUZ.flexo}
          angle={0.62}
          penumbra={0.75}
          distance={4}
          decay={2}
          castShadow
          shadow-mapSize={[1024, 1024]}
          shadow-bias={-0.0004}
        />
      </group>
    </group>
  );
}

function PlacaRotulo({
  material,
  posicion,
  tamano,
}: {
  material: MeshStandardMaterial;
  posicion: V3;
  tamano: readonly [number, number];
}) {
  return (
    <mesh position={[...posicion]} material={material}>
      <planeGeometry args={[...tamano]} />
    </mesh>
  );
}

const materialRotulo = (map: Texture) =>
  new MeshStandardMaterial({ map, emissiveMap: map, emissive: '#ffffff', emissiveIntensity: 0, roughness: 0.55 });

export interface SalaProps {
  control: ControlSala;
  /** Hover y clic en las zonas (el horneado no los usa). */
  onApuntar?: (id: string | null) => void;
  onElegir?: (id: string) => void;
}

export function Sala({ control, onApuntar, onElegir }: SalaProps) {
  const mat = useMateriales();
  const { gl, scene } = useThree();
  useLayoutEffect(() => {
    const pmrem = new PMREMGenerator(gl);
    const entorno = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = entorno;
    scene.environmentIntensity = 0;
    pmrem.dispose();
    return () => {
      scene.environment = null;
      entorno.dispose();
    };
  }, [gl, scene]);
  const alta = control.calidad === 'alta';

  const grupos = {
    izquierda: useRef<Group>(null),
    centro: useRef<Group>(null),
    derecha: useRef<Group>(null),
  } satisfies Record<Estanteria, RefObject<Group | null>>;
  const tubos = {
    izquierda: useRef<SpotLight>(null),
    centro: useRef<SpotLight>(null),
    derecha: useRef<SpotLight>(null),
  } satisfies Record<Estanteria, RefObject<SpotLight | null>>;
  const flexo = useRef<SpotLight>(null);
  const vitrina = useRef<PointLight>(null);
  const acento = useRef<SpotLight>(null);
  const linterna = useRef<SpotLight>(null);
  const ambiente = useRef<AmbientLight>(null);
  const hemisferio = useRef<HemisphereLight>(null);

  const tubosMat = useMemo(
    () =>
      Object.fromEntries(
        ORDEN_ESTANTERIAS.map((e) => [
          e,
          new MeshStandardMaterial({ color: '#e9eef7', emissive: '#ffffff', emissiveIntensity: 0, roughness: 0.3 }),
        ]),
      ) as Record<Estanteria, MeshStandardMaterial>,
    [],
  );
  const rotulos = useMemo(
    () =>
      Object.fromEntries(
        ZONAS.map((z) => [z.id, materialRotulo(texturaRotulo(z.rotulo, { dato: z.dato, demo: true }))]),
      ) as Record<string, MeshStandardMaterial>,
    [],
  );
  const cabeceras = useMemo(
    () =>
      Object.fromEntries(
        ORDEN_ESTANTERIAS.map((e) => [
          e,
          materialRotulo(
            texturaRotulo(e === 'centro' ? BRAND.name : ESTANTERIAS[e].titulo, {
              ancho: 1024,
              alto: 160,
              tinta: e === 'centro' ? colors['laton-claro'] : colors.hueso,
            }),
          ),
        ]),
      ) as Record<Estanteria, MeshStandardMaterial>,
    [],
  );
  const numeros = useMemo(
    () =>
      Object.fromEntries(
        ORDEN_ESTANTERIAS.map((e) => [
          e,
          texturaRotulo(ESTANTERIAS[e].numero, { ancho: 256, alto: 160, tinta: colors.hueso }),
        ]),
      ) as unknown as Record<Estanteria, Texture>,
    [],
  );
  const apodo = useMemo(() => texturaRotulo('Invitado', { alto: 200, fondo: '#3b434b', tinta: colors.hueso }), []);

  // Objetivos de los focos (deben estar en la escena para que se actualice su matriz).
  const objetivos = useMemo(
    () => ({
      tubos: Object.fromEntries(ORDEN_ESTANTERIAS.map((e) => [e, new Object3D()])) as Record<Estanteria, Object3D>,
      acento: new Object3D(),
      linterna: new Object3D(),
    }),
    [],
  );

  const destino = useMemo(() => new Vector3(), []);
  const origenAcento = useMemo(() => new Vector3(), []);
  useFrame(({ camera }) => {
    const { luz } = control;
    for (const e of ORDEN_ESTANTERIAS) {
      const nivel = luz.tubos[e];
      const foco = tubos[e].current;
      if (foco) {
        foco.intensity = LUZ.tubo * nivel;
        foco.color.copy(control.colorTubo);
      }
      tubosMat[e].emissiveIntensity = LUZ.tuboEmisivo * Math.min(1.2, nivel * 1.6);
      tubosMat[e].emissive.copy(control.colorTubo);
      const g = grupos[e].current;
      if (g) g.position.z = control.desplazamiento[e];
      // Emisión independiente de los tubos: así cada grupo de luz se suma (pases del prototipo B).
      cabeceras[e].emissiveIntensity = e === 'centro' ? LUZ.marca * luz.marca : LUZ.rotuloBase * 1.4 * luz.rotulos;
    }
    for (const z of ZONAS) {
      const material = rotulos[z.id];
      if (!material) continue;
      const activo = z.id === control.zonaActiva;
      material.emissiveIntensity = luz.rotulos * (activo ? LUZ.rotuloActivo : LUZ.rotuloBase * 1.2);
    }
    if (flexo.current) flexo.current.intensity = LUZ.flexo * luz.calidas;
    mat.bombilla.emissiveIntensity = LUZ.bombilla * luz.calidas;
    mat.led.emissiveIntensity = LUZ.led * luz.calidas;
    if (vitrina.current) vitrina.current.intensity = LUZ.vitrina * luz.calidas;
    mat.pantalla.emissiveIntensity = LUZ.pantalla * Math.min(1, luz.ambiente);
    if (ambiente.current) ambiente.current.intensity = LUZ.ambiente * luz.ambiente;
    scene.environmentIntensity = LUZ.entorno * luz.ambiente;
    if (hemisferio.current) hemisferio.current.intensity = LUZ.hemisferio * luz.ambiente;

    const activa = ZONAS.find((z) => z.id === control.zonaActiva);
    if (acento.current) {
      if (activa) {
        const [x, y, zc] = activa.caja.centro;
        const dz = activa.id === 'banco' ? 0 : control.desplazamiento[activa.estanteria];
        destino.set(x, y, zc + dz);
        origenAcento.set(x, Math.min(3.4, y + 1.7), zc + dz + 2.2);
        acento.current.position.lerp(origenAcento, 0.2);
        objetivos.acento.position.lerp(destino, 0.2);
      }
      acento.current.intensity = LUZ.acento * luz.acento;
      acento.current.color.copy(control.colorTubo);
    }
    if (linterna.current) {
      linterna.current.position.copy(camera.position);
      objetivos.linterna.position.lerp(control.linterna, 0.35);
      linterna.current.intensity = LUZ.linterna * luz.linterna;
    }
  });

  const zonaDe = (id: string) => (e: ThreeEvent<PointerEvent | MouseEvent>) => {
    e.stopPropagation();
    if (e.type === 'click') onElegir?.(id);
    else onApuntar?.(id);
  };

  return (
    <group>
      <ambientLight ref={ambiente} intensity={LUZ.ambiente} color="#9fb0c8" />
      <hemisphereLight ref={hemisferio} args={['#8899aa', '#1a1612', LUZ.hemisferio]} />
      <primitive object={objetivos.acento} />
      <primitive object={objetivos.linterna} />

      {/* Suelo, pared y techo */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 2]} material={mat.hormigon} receiveShadow>
        <planeGeometry args={[24, 16]} />
      </mesh>
      <mesh position={[0, 2.6, MUEBLE.frente - MUEBLE.fondo - 0.04]} material={mat.ladrillo} receiveShadow>
        <planeGeometry args={[24, 5.2]} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 4.2, 2]} material={mat.techo}>
        <planeGeometry args={[24, 16]} />
      </mesh>

      {/* Raíles del compactus: vienen hacia el espectador, como en ref-08 */}
      {ORDEN_ESTANTERIAS.flatMap((e) =>
        [-1.02, 1.02].map((dx) => (
          <Caja key={`rail-${e}-${dx}`} p={[xDe(e) + dx, 0.005, 1.8]} t={[0.05, 0.012, 8.3]} m={mat.rail} />
        )),
      )}

      {/* Filas de tubos LED: carcasa, tubo emisivo y foco */}
      {ORDEN_ESTANTERIAS.map((e) => (
        <group key={`tubo-${e}`} position={[xDe(e), 3.42, -1.05]}>
          <Caja p={[0, 0.05, 0]} t={[2.3, 0.05, 0.16]} m={mat.acero} />
          <mesh rotation={[0, 0, Math.PI / 2]} material={tubosMat[e]}>
            <cylinderGeometry args={[0.024, 0.024, 2.2, 10]} />
          </mesh>
          <primitive object={objetivos.tubos[e]} position={[0, -2.3, -0.9]} />
          <spotLight
            ref={tubos[e]}
            position={[0, -0.05, 0.05]}
            target={objetivos.tubos[e]}
            intensity={0}
            angle={0.86}
            penumbra={0.7}
            distance={9}
            decay={2}
            castShadow={alta}
            shadow-mapSize={[1024, 1024]}
            shadow-bias={-0.0004}
          />
        </group>
      ))}

      {/* Los tres cuerpos del compactus, con su contenido, rótulos y cajas de zona */}
      {ORDEN_ESTANTERIAS.map((e) => (
        <group key={`cuerpo-${e}`} ref={grupos[e]} position={[xDe(e), 0, 0]}>
          <Mueble mat={mat}>
            {e === 'izquierda' ? (
              <>
                <Armero mat={mat} />
                <Almacen mat={mat} />
              </>
            ) : null}
            {e === 'centro' ? <Vitrina mat={mat} luz={vitrina} /> : null}
            {e === 'derecha' ? (
              <>
                <Caja p={[0, MUEBLE.alto / 2, zFondo]} t={[0.03, MUEBLE.alto - 0.1, MUEBLE.fondo]} m={mat.chapa} />
                <Tablon mat={mat} />
                <Mostrador mat={mat} />
                <Biblioteca mat={mat} />
                <Taquilla mat={mat} apodo={apodo} />
              </>
            ) : null}
          </Mueble>
          <PlacaRotulo
            material={cabeceras[e]}
            posicion={[0, MUEBLE.alto + 0.17, MUEBLE.frente - 0.012]}
            tamano={[1.6, 0.25]}
          />
          <mesh position={[MUEBLE.ancho / 2 - 0.2, MUEBLE.zocalo / 2, MUEBLE.frente + 0.025]}>
            <planeGeometry args={[0.16, 0.1]} />
            <meshStandardMaterial map={numeros[e]} roughness={0.6} />
          </mesh>
          {ZONAS.filter((z) => z.estanteria === e && z.id !== 'banco').map((z) => (
            <PlacaRotulo
              key={`rot-${z.id}`}
              material={rotulos[z.id] as MeshStandardMaterial}
              posicion={[z.anclaRotulo[0] - xDe(e), z.anclaRotulo[1], z.anclaRotulo[2]]}
              tamano={z.caja.tamano[0] > 2 ? [0.96, 0.24] : [0.84, 0.21]}
            />
          ))}
          {ZONAS.filter((z) => z.estanteria === e && z.id !== 'banco').map((z) => (
            <CajaZona
              key={`zona-${z.id}`}
              zona={z}
              dx={-xDe(e)}
              onZona={zonaDe(z.id)}
              onSalir={() => onApuntar?.(null)}
            />
          ))}
        </group>
      ))}

      <Banco mat={mat} flexo={flexo} />
      {ZONAS.filter((z) => z.id === 'banco').map((z) => (
        <group key="banco-rotulo">
          <PlacaRotulo
            material={rotulos[z.id] as MeshStandardMaterial}
            posicion={z.anclaRotulo}
            tamano={[0.84, 0.13]}
          />
          <CajaZona zona={z} dx={0} onZona={zonaDe(z.id)} onSalir={() => onApuntar?.(null)} />
        </group>
      ))}

      {/* Foco de acento (la zona activa) y linterna-cursor */}
      <spotLight
        ref={acento}
        position={[0, 3, 0]}
        target={objetivos.acento}
        intensity={0}
        angle={0.4}
        penumbra={0.85}
        distance={7}
        decay={2}
      />
      <spotLight
        ref={linterna}
        target={objetivos.linterna}
        color={colors.hueso}
        intensity={0}
        angle={0.16}
        penumbra={0.9}
        distance={14}
        decay={2}
      />
    </group>
  );
}

/** Caja invisible de una zona: recibe el puntero (R3F) y define su silueta para el horneado. */
function CajaZona({
  zona,
  dx,
  onZona,
  onSalir,
}: {
  zona: Zona;
  dx: number;
  onZona: (e: ThreeEvent<PointerEvent | MouseEvent>) => void;
  onSalir: () => void;
}) {
  const [x, y, z] = zona.caja.centro;
  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: es un objeto de three.js (R3F), no del DOM; la alternativa accesible es la navegación HTML de las zonas.
    <mesh
      position={[x + dx, y, z]}
      visible={false}
      userData={{ zona: zona.id }}
      onPointerOver={onZona}
      onPointerOut={onSalir}
      onClick={onZona}
    >
      <boxGeometry args={[...zona.caja.tamano]} />
    </mesh>
  );
}
