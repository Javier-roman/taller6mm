// La sala de La Armería en 3D: pared de ladrillo, suelo de hormigón con raíles, tubos LED en el techo y
// tres cuerpos de compactus verde oliva casi negro (ref-08), con sus zonas, más el banco de trabajo con
// flexo. Todo es geometría propia o procedural. SIN siluetas de réplicas (Javi, 22-11-2026): las ranuras,
// peanas y el tapete quedan vacíos y resueltos, y sus huecos son los sockets de sockets.ts.
// La sala no decide nada: pinta lo que diga `ControlSala`. El nivel A (3D) la alimenta con el director
// (intro, hover, linterna) y el horneado (horno/) fija cada grupo de luz por separado para el póster y el B.
import { type ThreeEvent, useFrame, useThree } from '@react-three/fiber';
import { colors } from '@taller6mm/ui/tokens';
import { type ReactNode, type RefObject, useLayoutEffect, useMemo, useRef } from 'react';
import {
  type AmbientLight,
  Color,
  type Group,
  type HemisphereLight,
  MeshStandardMaterial,
  Object3D,
  PMREMGenerator,
  type PointLight,
  type SpotLight,
  type Texture,
  Vector3,
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { crearIluminacion, type Iluminacion } from '../director.ts';
import { ARMERO, SOCKETS, VITRINA } from '../sockets.ts';
import { BANCO, ESTANTERIAS, type Estanteria, MUEBLE, ORDEN_ESTANTERIAS, ZONAS, type Zona } from '../zonas.ts';
import {
  Alicate,
  Bateria,
  Bombona,
  Bote,
  Caballete,
  CajaCarton,
  CajaHerramientas,
  CajonBotes,
  Calibre,
  Carpeta,
  Casco,
  Chaleco,
  CintaMetrica,
  Destornillador,
  Diana,
  Etiqueta,
  Gafas,
  HojaPlano,
  Linterna,
  LlavesAllen,
  Maletin,
  Perchero,
  PlanoEnmarcado,
  Regla,
  SoporteCasco,
  TINTAS_CARPETA,
} from './atrezo.tsx';
import { ajustarReflejo, crearReflejoFalso } from './efectos.ts';
import { Caja, Cilindro, useSombras, type V3 } from './geom.tsx';
import { CALIDO, crearMateriales, type Materiales } from './materiales.ts';
import { texturaHuecoArmero, texturaRotulo, texturaSenalOjos, texturaTiraNumerada } from './texturas.ts';

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
  /**
   * Factor del flexo. En tiempo real (A) va a 0,6: sin iluminación global y con bloom, a plena potencia la
   * réplica del banco se quemaba a blanco (critico-diseno, 2.ª revisión). El horno exporta a 1 para Cycles.
   */
  flexo: number;
}

export const crearControl = (luz: Iluminacion = crearIluminacion(1)): ControlSala => ({
  luz,
  zonaActiva: null,
  linterna: new Vector3(0, 1.4, MUEBLE.frente),
  desplazamiento: { izquierda: 0, centro: 0, derecha: 0 },
  colorTubo: new Color('#dfe9ff'),
  calidad: 'alta',
  flexo: 1,
});

/** Intensidades de referencia (candelas: luces físicas de three r155+), ajustadas con capturas. */
export const LUZ = {
  tubo: 85,
  /** Foco rasante sobre el ladrillo: un tercio del tubo, para ver la textura sin perder la penumbra. */
  paredLavado: 28,
  tuboEmisivo: 3.4,
  // El flexo es la mancha más brillante de la sala: el banco es el protagonista (critico-diseno).
  // El flexo es la mancha más brillante de la sala: el banco manda (critico-diseno, 23-11-2026).
  flexo: 110,
  bombilla: 8,
  vitrina: 2.4,
  led: 1.8,
  ambiente: 0.06,
  hemisferio: 0.1,
  acento: 34,
  linterna: 120,
  // El rótulo solo emite lo grabado (texto, cota y marcas): se puede subir sin lavar la lámina.
  rotuloBase: 0.34,
  // Al pasar por un módulo se enciende su rótulo (y no hay tooltip): 1,6 veces la emisión activa anterior.
  rotuloActivo: 0.32 * 1.6,
  // El rótulo del banco cuelga del faldón, a la sombra del tablero: sin más emisión no se lee (critico-diseno).
  rotuloBanco: 2,
  marca: 1.5,
  pantalla: 0.9,
  /** Reflejos del entorno (IBL): sin ellos el metal se ve negro. */
  entorno: 0.08,
  // Sin haces de luz visibles (Javi, 11-11-2026: parecían de videojuego). La luz es indirecta: los tubos
  // iluminan paredes, suelo y muebles, y el aire no se ve.
  /** Reflejos falsos del suelo bajo los tubos y el flexo (efectos.ts). */
  reflejo: 3.5,
} as const;

const xDe = (e: Estanteria) => ESTANTERIAS[e].x;
const zFondo = MUEBLE.frente - MUEBLE.fondo / 2;

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

/** Marcador vacío de un socket (sockets.ts): ahí se colocará la imagen real de la réplica. Sin geometría visible. */
function Socket({ id, estanteria }: { id: string; estanteria: Estanteria }) {
  const socket = SOCKETS.find((s) => s.id === id);
  if (!socket) return null;
  const [x, y, z] = socket.caja.centro;
  return <group name={`socket.${id}`} position={[x - xDe(estanteria), y, z]} userData={{ socket: id }} />;
}

/** Armero: ranuras numeradas (vacías, con su apoyo y su gancho) y, sobre ellas, una barra con gafas colgadas. */
function Armero({ mat }: { mat: Materiales }) {
  const { huecos, util } = ARMERO;
  const paso = util / huecos;
  const tira = useMemo(() => texturaTiraNumerada(1, huecos), [huecos]);
  const yBarra = 2.64;
  const huecoMat = useMemo(
    () => new MeshStandardMaterial({ map: texturaHuecoArmero(), transparent: true, roughness: 0.9 }),
    [],
  );
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
      {Array.from({ length: huecos }, (_, i) => {
        const x = -util / 2 + (i + 0.5) * paso;
        return (
          <group key={`ranura-${i}`}>
            {/* Apoyo de goma para la culata */}
            <Caja p={[x, MUEBLE.baldaMedia + 0.025, zFondo + 0.04]} t={[0.09, 0.02, 0.1]} m={mat.polimeroNegro} />
            {/* Gancho de sujeción en el fondo, a media altura de la réplica */}
            <Caja
              p={[x, MUEBLE.baldaMedia + 0.82, zFondo - MUEBLE.fondo / 2 + 0.05]}
              t={[0.07, 0.012, 0.05]}
              m={mat.acero}
            />
            <Caja
              p={[x, MUEBLE.baldaMedia + 0.845, zFondo - MUEBLE.fondo / 2 + 0.075]}
              t={[0.07, 0.04, 0.012]}
              m={mat.acero}
            />
            <mesh
              position={[x, MUEBLE.baldaMedia + 0.03 + ARMERO.alto / 2, zFondo - MUEBLE.fondo / 2 + 0.024]}
              material={huecoMat}
            >
              <planeGeometry args={[paso * 0.9, ARMERO.alto]} />
            </mesh>
            <Socket id={`armero-${String(i + 1).padStart(2, '0')}`} estanteria="izquierda" />
          </group>
        );
      })}
      <mesh position={[0, MUEBLE.baldaMedia - 0.03, MUEBLE.frente + 0.001]}>
        <planeGeometry args={[util, 0.05]} />
        <meshStandardMaterial map={tira} roughness={0.7} />
      </mesh>
      {/* Regla de papel en milímetros en el lateral izquierdo (1:1) y un número de ranura en el fondo de cada hueco */}
      <group
        position={[-MUEBLE.ancho / 2 + 0.028, MUEBLE.baldaMedia + 0.03 + ARMERO.alto / 2, zFondo + 0.15]}
        rotation={[0, Math.PI / 2, 0]}
      >
        <Regla mm={ARMERO.alto * 1000} />
      </group>
      {Array.from({ length: huecos }, (_, i) => (
        <Etiqueta
          key={`num-${i}`}
          p={[-util / 2 + (i + 0.5) * paso, MUEBLE.baldaMedia + 1.0, zFondo - MUEBLE.fondo / 2 + 0.03]}
          t={[0.12, 0.06]}
          codigo={String(i + 1).padStart(2, '0')}
          linea2={`${Math.round(paso * 1000)} mm`}
        />
      ))}
      {/* Tira LED fría bajo la cabecera: ilumina la barra de gafas (sigue a los tubos de la izquierda) */}
      <Caja p={[0, MUEBLE.alto - 0.05, MUEBLE.frente - 0.06]} t={[2.4, 0.018, 0.03]} m={mat.ledIzquierda} />
      {/* Barra superior con gafas de protección: el armero también guarda lo que se lleva puesto */}
      <Cilindro p={[0, yBarra, zFondo - 0.1]} rad={0.009} h={util + 0.1} m={mat.aceroClaro} r={[0, 0, Math.PI / 2]} />
      {[-1, 1].map((lado) => (
        <Caja
          key={`soporte-${lado}`}
          p={[lado * (util / 2 + 0.03), yBarra, zFondo - 0.2]}
          t={[0.02, 0.04, 0.2]}
          m={mat.acero}
        />
      ))}
      {Array.from({ length: 9 }, (_, i) => (
        <group key={`gafas-${i}`} position={[-1.02 + i * 0.255, yBarra - 0.185, zFondo - 0.1]}>
          <Gafas mat={mat} giro={((i % 3) - 1) * 0.16} />
        </group>
      ))}
    </group>
  );
}

/** Almacén: maletines rígidos etiquetados y, encima, cajas de cartón y botes de bolas. */
function Almacen({ mat }: { mat: Materiales }) {
  const yTapa = MUEBLE.zocalo + 0.085 + 3 * 0.165 + 0.075;
  return (
    <group>
      {[0, 1, 2, 3].map((fila) =>
        [-0.63, 0.63].map((x, j) => (
          <group key={`m-${fila}-${x}`} position={[x, MUEBLE.zocalo + 0.085 + fila * 0.165, zFondo + 0.03]}>
            <Maletin mat={mat} codigo={`A-${fila * 2 + j + 1}`} linea2="1 180 × 440" />
          </group>
        )),
      )}
      {/* Cartón: dos cajas apiladas a la izquierda y una a la derecha */}
      <group position={[-0.95, yTapa, zFondo + 0.04]}>
        <CajaCarton mat={mat} t={[0.44, 0.2, 0.36]} codigo="BB-01" linea2="caja 10 uds" />
        <group position={[0, 0.2, 0]}>
          <CajaCarton mat={mat} t={[0.4, 0.17, 0.34]} codigo="BB-02" linea2="caja 10 uds" />
        </group>
      </group>
      <group position={[0.92, yTapa, zFondo + 0.04]}>
        <CajaCarton mat={mat} t={[0.42, 0.24, 0.36]} codigo="GF-03" linea2="gafas" />
      </group>
      {/* Botes de bolas en dos filas */}
      {[0, 1, 2, 3].map((i) =>
        [0, 1].map((fila) => (
          <group key={`bote-${i}-${fila}`} position={[-0.36 + i * 0.14, yTapa, zFondo - 0.03 + fila * 0.14]}>
            <Bote mat={mat} codigo={i % 2 ? '6 mm' : '8 mm'} linea2={i % 2 ? '0,25 g' : '0,20 g'} />
          </group>
        )),
      )}
    </group>
  );
}

/** Vitrina: peanas con soportes (vacías), planos enmarcados al fondo y luz cálida. */
function Vitrina({ mat, luz }: { mat: Materiales; luz: RefObject<PointLight | null> }) {
  const y0 = VITRINA.y0;
  const yPlano = 2.2;
  const zPlano = zFondo - MUEBLE.fondo / 2 + 0.04;
  return (
    <group>
      <Caja p={[0, y0 + 0.05, zFondo + 0.02]} t={[2.4, 0.1, 0.5]} m={mat.contrachapado} />
      {VITRINA.xs.map((x, i) => (
        <group key={`pedestal-${x}`} position={[x, y0 + 0.1, zFondo + 0.04]}>
          <Caja p={[0, 0.07 + i * 0.03, 0]} t={[0.5, 0.14 + i * 0.06, 0.3]} m={mat.polimeroNegro} />
          {/* Dos soportes de acero en la cara superior de la peana, donde descansa la réplica */}
          {[-0.28, 0.28].map((dx) => (
            <Caja
              key={`soporte-${dx}`}
              p={[dx * 0.7, 0.14 + i * 0.06 + 0.012, 0]}
              t={[0.06, 0.024, 0.1]}
              m={mat.acero}
            />
          ))}
          <Caja p={[0, 0.06 + i * 0.03, 0.155]} t={[0.18, 0.05, 0.01]} m={mat.laton} />
        </group>
      ))}
      {VITRINA.xs.map((x, i) => (
        <Socket key={`socket-${x}`} id={`vitrina-${i + 1}`} estanteria="centro" />
      ))}
      {/* Planos enmarcados del propio mobiliario, a escala y con sus cotas reales */}
      <group position={[-0.78, yPlano, zPlano]}>
        <PlanoEnmarcado mat={mat} mm={[MUEBLE.ancho * 1000, MUEBLE.alto * 1000]} titulo="Alzado compactus" />
      </group>
      <group position={[0, yPlano, zPlano]}>
        <PlanoEnmarcado mat={mat} mm={[BANCO.ancho * 1000, BANCO.alto * 1000]} titulo="Banco de trabajo" />
      </group>
      <group position={[0.78, yPlano, zPlano]}>
        <PlanoEnmarcado
          mat={mat}
          mm={[(ARMERO.util / ARMERO.huecos) * 1000, ARMERO.alto * 1000]}
          titulo="Ranura de armero"
        />
      </group>
      {/* Tira LED cálida bajo el techo de la vitrina */}
      <Caja p={[0, MUEBLE.alto - 0.05, MUEBLE.frente - 0.06]} t={[2.4, 0.018, 0.03]} m={mat.led} />
      <pointLight
        name="luz:calidas"
        ref={luz}
        position={[0, y0 + 1.15, zFondo + 0.12]}
        color={CALIDO}
        intensity={LUZ.vitrina}
        distance={2.6}
        decay={2}
      />
    </group>
  );
}

/** Tablón: corcho con dianas de papel y etiquetas de kraft clavadas, y el monitor de bajadas. */
function Tablon({ mat }: { mat: Materiales }) {
  const zCorcho = zFondo - 0.25;
  const dianas: readonly [number, number, number, number][] = [
    [-0.4, 2.14, 0.05, 3],
    [-0.12, 2.24, -0.06, 7],
    [-0.36, 1.78, -0.04, 11],
    [-0.02, 1.84, 0.04, 17],
  ];
  const etiquetas: readonly [number, number, string][] = [
    [0.38, 2.34, 'T-014'],
    [0.38, 2.2, 'T-015'],
  ];
  return (
    <group position={[-MUEBLE.ancho / 4, 0, 0]}>
      <Caja p={[0, 2.02, zCorcho]} t={[1.2, 1.15, 0.03]} m={mat.corcho} />
      <Caja p={[0, 2.02, zCorcho - 0.001]} t={[1.24, 1.19, 0.02]} m={mat.acero} />
      {/* Tira LED fría bajo la cabecera, sobre el corcho */}
      <Caja p={[0, MUEBLE.alto - 0.05, MUEBLE.frente - 0.06]} t={[1.2, 0.018, 0.03]} m={mat.ledDerecha} />
      {dianas.map(([x, y, r, semilla]) => (
        <group key={`diana-${semilla}`} position={[x, y, zCorcho + 0.0165]} rotation={[0, 0, r]}>
          <Diana semilla={semilla} />
          <Cilindro p={[0, 0.115, 0.004]} rad={0.007} h={0.006} m={mat.laton} r={[Math.PI / 2, 0, 0]} seg={10} />
        </group>
      ))}
      {etiquetas.map(([x, y, codigo]) => (
        <group key={codigo} position={[x, y, zCorcho + 0.0165]}>
          <Etiqueta p={[0, 0, 0]} t={[0.16, 0.08]} codigo={codigo} linea2="comprob." papel={colors.kraft} />
          <Cilindro p={[0, 0.036, 0.004]} rad={0.006} h={0.006} m={mat.laton} r={[Math.PI / 2, 0, 0]} seg={10} />
        </group>
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

/** Mostrador: cascos sobre la balda, etiquetas de kraft al borde y un chaleco colgado al fondo. */
function Mostrador({ mat }: { mat: Materiales }) {
  const yBalda = 1.55;
  const zBalda = zFondo + 0.05;
  return (
    <group position={[MUEBLE.ancho / 4, 0, 0]}>
      <Caja p={[0, yBalda, zBalda]} t={[1.15, 0.05, 0.42]} m={mat.contrachapado} />
      {[-0.3, 0.04].map((x, k) => (
        <group key={`casco-${x}`} position={[x, yBalda + 0.025, zBalda]} rotation={[0, k ? 0.5 : -0.2, 0]}>
          <SoporteCasco mat={mat} />
          <group position={[0, 0.115, 0]} scale={1.35}>
            <Casco mat={mat} tela={k ? 'telaFde' : 'tela'} />
          </group>
        </group>
      ))}
      <group position={[0.37, yBalda + 0.025, zBalda + 0.08]}>
        <Bote mat={mat} codigo="6 mm" linea2="0,25 g" />
      </group>
      <group position={[0.34, yBalda + 0.025, zBalda - 0.09]}>
        <Bombona mat={mat} />
      </group>
      {/* Etiquetas de kraft (portaetiquetas de precio) en el canto de la balda */}
      {[-0.4, -0.08, 0.24].map((x, i) => (
        <Etiqueta
          key={`precio-${x}`}
          p={[x, yBalda - 0.005, zBalda + 0.2125]}
          t={[0.16, 0.04]}
          codigo={`P-0${i + 1}`}
          linea2="— · —"
          papel={colors.kraft}
        />
      ))}
      <Caja p={[0, MUEBLE.alto - 0.05, MUEBLE.frente - 0.06]} t={[1.2, 0.018, 0.03]} m={mat.ledDerecha} />
      {/* Chaleco colgado de la pared del fondo */}
      <Cilindro p={[0, 2.38, zFondo - 0.24]} rad={0.007} h={0.06} m={mat.aceroClaro} r={[Math.PI / 2, 0, 0]} />
      <group position={[0, 2.355, zFondo - 0.21]}>
        <Chaleco mat={mat} tela="telaFde" />
      </group>
    </group>
  );
}

/** Biblioteca: carpetas con etiqueta en el lomo y cajas de archivo sobre su balda. */
function Biblioteca({ mat }: { mat: Materiales }) {
  const tintas = useMemo(() => TINTAS_CARPETA.map((c) => new MeshStandardMaterial({ color: c, roughness: 0.75 })), []);
  const yBalda = 0.66;
  return (
    <group position={[-MUEBLE.ancho / 4, 0, 0]}>
      {Array.from({ length: 12 }, (_, i) => {
        const alto = 0.3 + ((i * 37) % 11) / 100;
        const material = tintas[i % tintas.length] ?? mat.papel;
        return (
          <group
            key={`l-${i}`}
            position={[-0.5 + i * 0.085, MUEBLE.zocalo, zFondo + 0.02]}
            rotation={[0, 0, i === 8 ? 0.18 : 0]}
          >
            <Carpeta
              mat={mat}
              alto={alto}
              color={material}
              codigo={`G-${String(i + 1).padStart(2, '0')}`}
              linea2="guía"
            />
          </group>
        );
      })}
      <Caja p={[0, yBalda, zFondo + 0.02]} t={[1.2, 0.03, 0.4]} m={mat.contrachapado} />
      {[-0.4, -0.13, 0.14, 0.41].map((x, i) => (
        <group key={`archivo-${x}`} position={[x, yBalda + 0.015, zFondo + 0.02]}>
          <CajaCarton mat={mat} t={[0.25, 0.12, 0.3]} codigo={`AR-${i + 1}`} linea2="archivo" />
        </group>
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
      {/* Candado */}
      <Caja p={[0.46, 0.5, z + 0.02]} t={[0.045, 0.06, 0.02]} m={mat.laton} />
      <mesh position={[0, 0.42, z + 0.001]}>
        <planeGeometry args={[0.8, 0.2]} />
        <meshStandardMaterial map={apodo} roughness={0.6} />
      </mesh>
    </group>
  );
}

/** Banco de trabajo: tablero de contrachapado, tapete con regla, atrezo de taller y el flexo. */
function Banco({ mat, flexo }: { mat: Materiales; flexo: RefObject<SpotLight | null> }) {
  const g = useRef<Group>(null);
  useSombras(g);
  const objetivo = useMemo(() => new Object3D(), []);
  const { x, z, ancho, fondo, alto } = BANCO;
  const yTapete = alto + 0.003;
  return (
    <group ref={g} position={[x, 0, z]}>
      <primitive object={objetivo} position={[-0.15, alto, 0]} />
      <Caja p={[0, alto - 0.03, 0]} t={[ancho, 0.06, fondo]} m={mat.tablero} />
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
      {/* Balda baja: caja de herramientas y una caja de cartón */}
      <group position={[-0.93, alto, 0.02]} rotation={[0, 0.12, 0]} scale={1.25}>
        <CajaHerramientas mat={mat} />
      </group>
      <group position={[0.5, 0.22, 0]}>
        <CajaCarton mat={mat} t={[0.5, 0.24, 0.36]} codigo="HT-05" linea2="recambios" />
      </group>
      {/* Faldón delantero, donde va el rótulo del banco */}
      <Caja p={[0, alto - 0.12, fondo / 2 + 0.01]} t={[ancho, 0.14, 0.02]} m={mat.acero} />
      <mesh position={[-0.15, yTapete, 0]} rotation={[-Math.PI / 2, 0, 0]} material={mat.tapete}>
        <planeGeometry args={[1.5, 0.66]} />
      </mesh>
      {/* Hueco de la réplica a medio montar, sobre el tapete (socket banco-1): sin réplica de relleno */}
      <group name="socket.banco-1" position={[-0.2, alto + 0.07, 0.04]} userData={{ socket: 'banco-1' }} />
      {/* Atrezo sobre el tablero, fuera de la franja central del socket */}
      <group position={[0.8, yTapete, 0.14]} scale={1.5}>
        <Linterna mat={mat} />
      </group>
      <group position={[0.66, yTapete, 0.22]} rotation={[0, 0.5, 0]} scale={1.5}>
        <Calibre mat={mat} />
      </group>
      <group position={[-0.66, yTapete, -0.27]} rotation={[0, 0.35, 0]} scale={1.5}>
        <Bateria mat={mat} />
      </group>
      <group position={[-0.5, yTapete, -0.28]} scale={1.3}>
        <Bombona mat={mat} />
      </group>
      <group position={[0.5, yTapete + 0.002, -0.02]} rotation={[0, 0.18, 0]}>
        <HojaPlano mm={[BANCO.ancho * 1000, BANCO.alto * 1000]} titulo="Banco de trabajo" />
      </group>
      <group position={[0.38, yTapete, -0.26]}>
        <Bote mat={mat} codigo="6 mm" linea2="0,20 g" />
      </group>
      <group position={[-0.5, yTapete, 0.26]} rotation={[0, 0.2, 0]}>
        <Caja p={[0, 0.006, 0]} t={[0.2, 0.012, 0.1]} m={mat.polimeroNegro} />
        {[-0.07, -0.02, 0.03, 0.075].map((dx) => (
          <Cilindro key={`tornillo-${dx}`} p={[dx, 0.016, 0]} rad={0.007} h={0.01} m={mat.aceroClaro} seg={10} />
        ))}
      </group>
      <group position={[0.2, yTapete + 0.004, 0.27]} rotation={[0, 0, Math.PI / 2]} scale={1.4}>
        <Destornillador mat={mat} mango="destornilladorNaranja" />
      </group>
      {/* Flexo: base, brazos, cabeza y bombilla */}
      <group position={[0.78, alto, -0.25]}>
        <mesh material={mat.acero}>
          <cylinderGeometry args={[0.08, 0.09, 0.03, 20]} />
        </mesh>
        <Caja p={[-0.05, 0.28, 0.06]} t={[0.025, 0.56, 0.025]} r={[0.25, 0, 0.2]} m={mat.acero} />
        <Caja p={[-0.25, 0.56, 0.2]} t={[0.025, 0.45, 0.025]} r={[1.05, 0, 0.6]} m={mat.acero} />
        <mesh position={[-0.42, 0.56, 0.32]} rotation={[0.6, 0, 0.5]} material={mat.chapa}>
          <coneGeometry args={[0.12, 0.19, 24, 1, true]} />
        </mesh>
        <mesh position={[-0.435, 0.545, 0.335]} material={mat.bombilla}>
          <sphereGeometry args={[0.022, 12, 12]} />
        </mesh>
        <spotLight
          name="luz:calidas"
          ref={flexo}
          position={[-0.42, 0.5, 0.34]}
          target={objetivo}
          color={CALIDO}
          intensity={LUZ.flexo}
          angle={0.45}
          penumbra={0.5}
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

/**
 * Atrezo de suelo y de los márgenes de la pared, bajo y a los lados para no tapar las zonas: a ras de los zócalos
 * (por debajo de unos 45 cm no se ve nada del mueble desde la cámara del póster) y, más altos, solo en los
 * márgenes junto a la pared, donde antes no había nada. Sin réplicas ni armas.
 */
function Ambientacion({ mat }: { mat: Materiales }) {
  const zSuelo = MUEBLE.frente + 1.1;
  const zPared = MUEBLE.frente - MUEBLE.fondo - 0.2;
  return (
    <group>
      {/* Izquierda: dos maletines apilados con una caja de bolas encima y la caja de herramientas al lado */}
      <group position={[-3.15, 0, zSuelo]} rotation={[0, 0.1, 0]} scale={0.75}>
        <group position={[0, 0.075, 0]}>
          <Maletin mat={mat} codigo="A-9" linea2="1 180 × 440" ancho={1.0} />
        </group>
        <group position={[0, 0.225, 0]}>
          <Maletin mat={mat} codigo="A-10" linea2="1 180 × 440" ancho={1.0} />
        </group>
      </group>
      <group position={[-2.1, 0, zSuelo + 0.15]} rotation={[0, -0.25, 0]} scale={1.3}>
        <CajaHerramientas mat={mat} />
      </group>
      {/* Derecha: cajón de botes de bolas, cartones apilados y un casco sobre su soporte */}
      <group position={[2.35, 0, zSuelo]} rotation={[0, 0.15, 0]}>
        <CajonBotes mat={mat} />
      </group>
      <group position={[3.2, 0, zSuelo + 0.05]} rotation={[0, -0.12, 0]}>
        <CajaCarton mat={mat} t={[0.46, 0.2, 0.34]} codigo="BB-04" linea2="caja 10 uds" />
        <group position={[0.02, 0.2, 0]} rotation={[0, 0.2, 0]}>
          <CajaCarton mat={mat} t={[0.38, 0.16, 0.3]} codigo="GF-05" linea2="gafas" />
        </group>
      </group>
      {/* Márgenes de la pared: perchero con chaleco, casco y gafas, y caballete con una diana */}
      <group position={[-4.5, 0, zPared]}>
        <Perchero mat={mat} />
      </group>
      <group position={[4.5, 0, zPared]} rotation={[0, -0.12, 0]}>
        <Caballete mat={mat} semilla={23} />
      </group>
    </group>
  );
}

/** Panel perforado de herramientas tras el banco: destornilladores, alicates, llaves y cinta métrica colgados. */
function PanelHerramientas({ mat }: { mat: Materiales }) {
  const zPanel = zFondo - MUEBLE.fondo / 2 + 0.03;
  const yColgado = 1.17;
  return (
    <group>
      <Caja p={[0, 0.72, zPanel]} t={[2.5, 1.12, 0.02]} m={mat.perforado} />
      {/* Tira LED cálida bajo la balda de la vitrina: ilumina el panel de herramientas */}
      <Caja p={[0, MUEBLE.baldaMedia - 0.045, MUEBLE.frente - 0.1]} t={[2.4, 0.016, 0.03]} m={mat.led} />
      <Caja p={[0, 1.285, zPanel + 0.012]} t={[2.5, 0.025, 0.03]} m={mat.acero} />
      {[-0.95, -0.82, -0.69, -0.56].map((x, i) => (
        <group key={`destornillador-${x}`} position={[x, yColgado, zPanel + 0.045]} scale={1.3}>
          <Destornillador mat={mat} mango={i % 2 ? 'destornilladorOlivo' : 'destornilladorNaranja'} />
        </group>
      ))}
      <group position={[-0.36, yColgado, zPanel + 0.045]}>
        <Alicate mat={mat} />
      </group>
      <group position={[-0.16, yColgado, zPanel + 0.045]}>
        <Alicate mat={mat} />
      </group>
      <group position={[0.06, yColgado, zPanel + 0.045]}>
        <LlavesAllen mat={mat} />
      </group>
      <group position={[0.3, yColgado, zPanel + 0.045]}>
        <CintaMetrica mat={mat} />
      </group>
      <group position={[0.52, yColgado - 0.03, zPanel + 0.045]} rotation={[0, 0, Math.PI]}>
        <Linterna mat={mat} />
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

/** 2,7 m → «2 700»: milímetros con separador de miles de espacio, como en una cota. */
const milimetros = (m: number) => String(Math.round(m * 1000)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

const materialRotulo = ({ mapa, emision }: { mapa: Texture; emision: Texture }) =>
  new MeshStandardMaterial({
    name: 'emisivo:rotulos',
    map: mapa,
    // La lámina debe quedar oscura bajo el foco del tubo: el color se atenúa y solo luce lo grabado (emisión).
    color: '#9c6c61',
    emissiveMap: emision,
    emissive: '#ffffff',
    emissiveIntensity: 0,
    roughness: 0.88,
  });

export interface SalaProps {
  control: ControlSala;
  /** Hover y clic en las zonas (el horneado no los usa). */
  onApuntar?: (id: string | null) => void;
  onElegir?: (id: string) => void;
}

export function Sala({ control, onApuntar, onElegir }: SalaProps) {
  const mat = useMemo(() => crearMateriales(), []);
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
  // Focos rasantes que bañan el ladrillo desde cada tubo (el muro de ref-08 no puede desaparecer).
  const lavado = {
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
          new MeshStandardMaterial({
            name: `emisivo:tubo-${e}`,
            color: '#e9eef7',
            emissive: '#ffffff',
            emissiveIntensity: 0,
            roughness: 0.3,
          }),
        ]),
      ) as Record<Estanteria, MeshStandardMaterial>,
    [],
  );
  // Rótulos en «Plano de cotas»: lámina, marco de trazo, marcas de registro, título en Plex condensada y una
  // línea de cota con la medida real de la zona (mm). El rótulo del banco es más apaisado: su textura también.
  const rotulos = useMemo(
    () =>
      Object.fromEntries(
        ZONAS.map((z) => [z.id, materialRotulo(texturaRotulo(z.rotulo, { alto: z.id === 'banco' ? 160 : 256 }))]),
      ) as Record<string, MeshStandardMaterial>,
    [],
  );
  const cabeceras = useMemo(
    () =>
      Object.fromEntries(
        ORDEN_ESTANTERIAS.map((e) => [
          e,
          materialRotulo(
            texturaRotulo(ESTANTERIAS[e].titulo, {
              ancho: 2048,
              alto: 206,
              cota: `${milimetros(MUEBLE.ancho)} mm`,
              escala: 1.1,
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
          texturaRotulo(ESTANTERIAS[e].numero, { ancho: 256, alto: 160, escala: 1.5 }).mapa,
        ]),
      ) as unknown as Record<Estanteria, Texture>,
    [],
  );
  const apodo = useMemo(() => texturaRotulo('Invitado', { ancho: 1024, alto: 256 }).mapa, []);
  const senalOjos = useMemo(() => texturaSenalOjos(), []);

  // Objetivos de los focos (deben estar en la escena para que se actualice su matriz).
  const objetivos = useMemo(
    () => ({
      tubos: Object.fromEntries(ORDEN_ESTANTERIAS.map((e) => [e, new Object3D()])) as Record<Estanteria, Object3D>,
      pared: Object.fromEntries(ORDEN_ESTANTERIAS.map((e) => [e, new Object3D()])) as Record<Estanteria, Object3D>,
      acento: new Object3D(),
      linterna: new Object3D(),
    }),
    [],
  );

  // Reflejos falsos en el suelo pulido: uno bajo cada fila de tubos y otro, cálido, bajo el flexo.
  const reflejos = useMemo(
    () => ({
      tubos: Object.fromEntries(
        ORDEN_ESTANTERIAS.map((e) => [e, crearReflejoFalso(1.9, 3.6, new Color('#dfe9ff'))]),
      ) as Record<Estanteria, ReturnType<typeof crearReflejoFalso>>,
      flexo: crearReflejoFalso(1.4, 2.2, new Color('#ffb46a')),
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
      const lavar = lavado[e].current;
      if (lavar) {
        lavar.intensity = LUZ.paredLavado * nivel;
        lavar.color.copy(control.colorTubo);
      }
      tubosMat[e].emissiveIntensity = LUZ.tuboEmisivo * Math.min(1.2, nivel * 1.6);
      ajustarReflejo(reflejos.tubos[e], LUZ.reflejo * Math.min(1.2, nivel), control.colorTubo);
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
      material.emissiveIntensity =
        luz.rotulos * (activo ? LUZ.rotuloActivo : LUZ.rotuloBase * 1.2) * (z.id === 'banco' ? LUZ.rotuloBanco : 1);
    }
    if (flexo.current) flexo.current.intensity = LUZ.flexo * control.flexo * luz.calidas;
    ajustarReflejo(reflejos.flexo, LUZ.reflejo * 0.8 * luz.calidas, CALIDO);
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
      {/* Pared: señal de protección ocular obligatoria y el alzado del compactus, a escala, con sus cotas */}
      <mesh position={[-4.87, 1.75, MUEBLE.frente - MUEBLE.fondo - 0.036]}>
        <planeGeometry args={[0.42, 0.42]} />
        <meshStandardMaterial map={senalOjos} roughness={0.6} />
      </mesh>
      <group position={[4.87, 1.75, MUEBLE.frente - MUEBLE.fondo - 0.02]}>
        <PlanoEnmarcado
          mat={mat}
          ancho={0.46}
          mm={[MUEBLE.ancho * 1000, MUEBLE.alto * 1000]}
          titulo="Alzado compactus"
        />
      </group>

      {ORDEN_ESTANTERIAS.map((e) => (
        <primitive key={`reflejo-${e}`} object={reflejos.tubos[e]} position={[xDe(e), 0.004, MUEBLE.frente + 1.8]} />
      ))}
      <primitive object={reflejos.flexo} position={[BANCO.x, 0.004, BANCO.z + 1.3]} />
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
          <Caja p={[0, 0.075, 0]} t={[2.34, 0.03, 0.1]} m={mat.aceroClaro} />
          {[-0.95, 0.95].map((dx) => (
            <Cilindro key={`cable-${dx}`} p={[dx, 0.46, 0]} rad={0.004} h={0.8} m={mat.caucho} seg={6} />
          ))}
          <primitive object={objetivos.pared[e]} position={[0, -0.95, -1.34]} />
          <spotLight
            name={`luz:tubo-${e}`}
            ref={lavado[e]}
            position={[0, 0, -0.04]}
            target={objetivos.pared[e]}
            intensity={0}
            angle={0.62}
            penumbra={0.95}
            distance={5}
            decay={2}
          />
          <mesh rotation={[0, 0, Math.PI / 2]} material={tubosMat[e]}>
            <cylinderGeometry args={[0.024, 0.024, 2.2, 10]} />
          </mesh>
          <primitive object={objetivos.tubos[e]} position={[0, -2.3, -0.9]} />
          <spotLight
            name={`luz:tubo-${e}`}
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
            {e === 'centro' ? (
              <>
                <PanelHerramientas mat={mat} />
                <Vitrina mat={mat} luz={vitrina} />
              </>
            ) : null}
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
            tamano={[MUEBLE.ancho, 0.27]}
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
              tamano={z.caja.tamano[0] > 2 ? [1.0, 0.25] : [0.88, 0.22]}
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
      <Ambientacion mat={mat} />
      {ZONAS.filter((z) => z.id === 'banco').map((z) => (
        <group key="banco-rotulo">
          <PlacaRotulo material={rotulos[z.id] as MeshStandardMaterial} posicion={z.anclaRotulo} tamano={[0.9, 0.14]} />
          <CajaZona zona={z} dx={0} onZona={zonaDe(z.id)} onSalir={() => onApuntar?.(null)} />
        </group>
      ))}

      {/* Foco de acento (la zona activa) y linterna-cursor */}
      <spotLight
        name="luz:acento"
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
        name="luz:linterna"
        ref={linterna}
        target={objetivos.linterna}
        color={colors.hueso}
        intensity={0}
        angle={0.22}
        penumbra={0.6}
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
