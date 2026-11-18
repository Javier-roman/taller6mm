// Escena 3D del visor de prueba (R3F). Escena estática re-iluminable (ADR-0002 §3): solo se pinta cuando
// algo cambia (`frameloop="demand"`), así que con movimiento reducido no hay animación ninguna y con
// movimiento normal solo el amortiguado de la órbita. Origen de escena = centro de la caja del modelo,
// luces y cámara se colocan en radios del modelo, así un preset vale para una pieza de 60 mm y para un
// rifle de 800 mm.
import { OrbitControls } from '@react-three/drei';
import { Canvas, useThree } from '@react-three/fiber';
import { type ComponentRef, type RefObject, useEffect, useMemo, useRef } from 'react';
import {
  Box3,
  MathUtils,
  type Mesh,
  NeutralToneMapping,
  type Object3D,
  type PerspectiveCamera,
  PMREMGenerator,
  Spherical,
  Vector3,
} from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { liberarModelo } from './cargarGlb.ts';
import { type LuzPreset, type PresetIluminacion, resolverColor } from './iluminacion.ts';

/** Acciones de la cámara que el HTML (botones y teclado) llama desde fuera del lienzo. */
export interface ApiVista {
  girar: (acimut: number, polar: number) => void;
  acercar: (factor: number) => void;
  reiniciar: () => void;
}

export interface Encuadre {
  /** Radio de la esfera que envuelve al modelo, en metros. */
  radio: number;
  /** Mitad del alto de la caja: el suelo de sombras va debajo. */
  mitadAlto: number;
  centro: Vector3;
}

export function calcularEncuadre(objeto: Object3D): Encuadre {
  objeto.updateMatrixWorld(true);
  const caja = new Box3().setFromObject(objeto);
  const centro = caja.getCenter(new Vector3());
  const tam = caja.getSize(new Vector3());
  return { radio: Math.max(tam.length() / 2, 1e-3), mitadAlto: tam.y / 2, centro };
}

const MAS_LUZ = 1.8;
const ACIMUT_INICIAL = MathUtils.degToRad(28);
const ELEVACION_INICIAL = MathUtils.degToRad(14);

function distanciaDeEncuadre(camara: PerspectiveCamera, radio: number): number {
  const vfov = MathUtils.degToRad(camara.fov);
  const hfov = 2 * Math.atan(Math.tan(vfov / 2) * camara.aspect);
  return (radio / Math.sin(Math.min(vfov, hfov) / 2)) * 1.08;
}

function Camara({
  encuadre,
  apiRef,
  reducido,
}: {
  encuadre: Encuadre;
  apiRef: RefObject<ApiVista | null>;
  reducido: boolean;
}) {
  const controles = useRef<ComponentRef<typeof OrbitControls>>(null);
  const { camera, invalidate, size } = useThree();

  // Vista inicial: tres cuartos desde la izquierda del tirador (+Z), la boca a la derecha de la pantalla.
  // Se vuelve a calcular al cambiar de modelo y al cambiar la proporción del lienzo (móvil ↔ escritorio).
  const aspecto = Math.round((size.width / Math.max(size.height, 1)) * 10);
  useEffect(() => {
    const cam = camera as PerspectiveCamera;
    const d = distanciaDeEncuadre(cam, encuadre.radio);
    cam.position.set(
      d * Math.cos(ELEVACION_INICIAL) * Math.sin(ACIMUT_INICIAL),
      d * Math.sin(ELEVACION_INICIAL),
      d * Math.cos(ELEVACION_INICIAL) * Math.cos(ACIMUT_INICIAL),
    );
    cam.near = encuadre.radio / 50;
    cam.far = encuadre.radio * 60;
    cam.updateProjectionMatrix();
    cam.lookAt(0, 0, 0);
    controles.current?.target.set(0, 0, 0);
    controles.current?.update();
    invalidate();
  }, [camera, encuadre, invalidate, aspecto]);

  useEffect(() => {
    const cam = camera as PerspectiveCamera;
    const dist = () => cam.position.distanceTo(controles.current?.target ?? new Vector3());
    apiRef.current = {
      girar: (acimut, polar) => {
        const c = controles.current;
        if (!c) return;
        const desde = cam.position.clone().sub(c.target);
        const s = new Spherical().setFromVector3(desde);
        s.theta += acimut;
        s.phi = MathUtils.clamp(s.phi + polar, 0.05, Math.PI - 0.05);
        cam.position.copy(c.target).add(desde.setFromSpherical(s));
        cam.lookAt(c.target);
        c.update();
        invalidate();
      },
      acercar: (factor) => {
        const c = controles.current;
        if (!c) return;
        const nuevo = MathUtils.clamp(dist() * factor, c.minDistance, c.maxDistance);
        const dir = cam.position.clone().sub(c.target).normalize();
        cam.position.copy(c.target).addScaledVector(dir, nuevo);
        c.update();
        invalidate();
      },
      reiniciar: () => {
        const d = distanciaDeEncuadre(cam, encuadre.radio);
        cam.position.set(
          d * Math.cos(ELEVACION_INICIAL) * Math.sin(ACIMUT_INICIAL),
          d * Math.sin(ELEVACION_INICIAL),
          d * Math.cos(ELEVACION_INICIAL) * Math.cos(ACIMUT_INICIAL),
        );
        controles.current?.target.set(0, 0, 0);
        cam.lookAt(0, 0, 0);
        controles.current?.update();
        invalidate();
      },
    };
    return () => {
      apiRef.current = null;
    };
  }, [apiRef, camera, encuadre, invalidate]);

  return (
    <OrbitControls
      ref={controles}
      makeDefault
      enableDamping={!reducido}
      dampingFactor={0.12}
      minDistance={encuadre.radio * 1.2}
      maxDistance={encuadre.radio * 10}
      maxPolarAngle={Math.PI * 0.98}
    />
  );
}

/** Entorno procedural (sin descargas): da reflejos a los metales; la intensidad la manda el preset. */
function Entorno({ intensidad }: { intensidad: number }) {
  const { gl, scene, invalidate } = useThree();
  const mapa = useMemo(() => {
    const pm = new PMREMGenerator(gl);
    const rt = pm.fromScene(new RoomEnvironment(), 0.04);
    pm.dispose();
    return rt;
  }, [gl]);
  useEffect(() => () => mapa.dispose(), [mapa]);
  useEffect(() => {
    scene.environment = intensidad > 0 ? mapa.texture : null;
    scene.environmentIntensity = intensidad;
    invalidate();
    return () => {
      scene.environment = null;
    };
  }, [scene, mapa, intensidad, invalidate]);
  return null;
}

function Luz({ luz, radio, factor }: { luz: LuzPreset; radio: number; factor: number }) {
  const color = resolverColor(luz.color);
  if (luz.tipo === 'hemisferio') {
    return <hemisphereLight args={[color, resolverColor(luz.color_suelo ?? luz.color), luz.intensidad * factor]} />;
  }
  const [x, y, z] = luz.posicion ?? [0, 1, 0];
  const pos = new Vector3(x, y, z).multiplyScalar(radio);
  const d = pos.length();
  const sombra = luz.sombra === true;
  const radioSombra = 1 + (luz.suavidad ?? 0.5) * 7;
  const propsSombra = {
    castShadow: sombra,
    'shadow-mapSize': [2048, 2048] as [number, number],
    'shadow-radius': radioSombra,
    'shadow-bias': -0.0002,
    'shadow-normalBias': radio * 0.02,
  };
  if (luz.tipo === 'direccional') {
    return (
      <directionalLight color={color} intensity={luz.intensidad * factor} position={pos} {...propsSombra}>
        <orthographicCamera
          attach="shadow-camera"
          args={[-radio * 1.4, radio * 1.4, radio * 1.4, -radio * 1.4, d * 0.05, d * 4]}
        />
      </directionalLight>
    );
  }
  // Puntual y foco: candelas = iluminancia en el centro × distancia², para que valgan a cualquier escala.
  const candelas = luz.intensidad * factor * d * d;
  if (luz.tipo === 'foco') {
    return (
      <spotLight
        color={color}
        intensity={candelas}
        position={pos}
        angle={Math.atan((radio * 1.6) / d)}
        penumbra={0.8}
        decay={2}
        {...propsSombra}
      />
    );
  }
  return <pointLight color={color} intensity={candelas} position={pos} decay={2} {...propsSombra} />;
}

function Iluminacion({ preset, encuadre, masLuz }: { preset: PresetIluminacion; encuadre: Encuadre; masLuz: boolean }) {
  const { gl, invalidate } = useThree();
  const factor = masLuz ? MAS_LUZ : 1;
  useEffect(() => {
    gl.toneMapping = NeutralToneMapping;
    gl.toneMappingExposure = preset.exposicion;
    invalidate();
  }, [gl, preset.exposicion, invalidate]);
  // Las luces con `key` por preset: React las crea de nuevo y no arrastra sombras de la anterior.
  return (
    <group key={preset.id}>
      <color attach="background" args={[resolverColor(preset.fondo)]} />
      <Entorno intensidad={preset.entorno * (masLuz ? 1.5 : 1)} />
      {preset.luces.map((l, i) => (
        <Luz key={`${l.tipo}-${i}`} luz={l} radio={encuadre.radio} factor={factor} />
      ))}
    </group>
  );
}

function Modelo({ objeto, encuadre }: { objeto: Object3D; encuadre: Encuadre }) {
  const { invalidate } = useThree();
  useEffect(() => {
    objeto.traverse((o) => {
      const m = o as Mesh;
      if (!m.isMesh) return;
      const marcador = (Array.isArray(m.material) ? m.material[0] : m.material)?.name === 'mat.marcador';
      m.castShadow = !marcador;
      m.receiveShadow = true;
    });
    invalidate();
  }, [objeto, invalidate]);
  // El modelo que se sustituye (o se desmonta) libera su memoria de GPU.
  useEffect(() => () => liberarModelo(objeto), [objeto]);
  return (
    <>
      <primitive object={objeto} position={[-encuadre.centro.x, -encuadre.centro.y, -encuadre.centro.z]} />
      {/* Suelo que solo recibe sombra: sin él, las luces con sombra no se leerían. */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -encuadre.mitadAlto - encuadre.radio * 0.01, 0]}
        receiveShadow
      >
        <planeGeometry args={[encuadre.radio * 30, encuadre.radio * 30]} />
        <shadowMaterial opacity={0.5} />
      </mesh>
    </>
  );
}

export interface EscenaProps {
  objeto: Object3D;
  preset: PresetIluminacion;
  masLuz: boolean;
  reducido: boolean;
  apiRef: RefObject<ApiVista | null>;
}

export default function Escena({ objeto, preset, masLuz, reducido, apiRef }: EscenaProps) {
  const encuadre = useMemo(() => calcularEncuadre(objeto), [objeto]);
  return (
    <Canvas
      frameloop="demand"
      shadows="percentage"
      dpr={[1, 2]}
      camera={{ fov: 30, near: 0.01, far: 100 }}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
    >
      <Iluminacion preset={preset} encuadre={encuadre} masLuz={masLuz} />
      <Modelo objeto={objeto} encuadre={encuadre} />
      <Camara encuadre={encuadre} apiRef={apiRef} reducido={reducido} />
    </Canvas>
  );
}
