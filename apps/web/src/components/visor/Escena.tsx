// Escena 3D del visor de prueba (R3F). Escena estática re-iluminable (ADR-0002 §3): solo se pinta cuando
// algo cambia (`frameloop="demand"`), así que con movimiento reducido no hay animación ninguna y con
// movimiento normal solo el amortiguado de la órbita.
//
// La luz es la del estudio de `catalogo/iluminacion-presets.json`, la misma receta que el render de Blender:
// softboxes de área sobre un mundo en degradado. Aquí se hornean en un entorno (PMREM) que ilumina y da
// reflejos a los materiales PBR, y una luz direccional tenue desde la clave proyecta la sombra de contacto.
// Origen de escena = centro de la caja del modelo; luces y cámara se miden en la diagonal `d` del modelo.
import { OrbitControls } from '@react-three/drei';
import { Canvas, useThree } from '@react-three/fiber';
import { COLOR_TOKENS } from '@taller6mm/ui/tokens';
import { type ComponentRef, type RefObject, useEffect, useMemo, useRef } from 'react';
import {
  ACESFilmicToneMapping,
  AgXToneMapping,
  BackSide,
  Box3,
  CanvasTexture,
  Color,
  DoubleSide,
  LinearSRGBColorSpace,
  MathUtils,
  Mesh,
  MeshBasicMaterial,
  NeutralToneMapping,
  type Object3D,
  type PerspectiveCamera,
  PlaneGeometry,
  PMREMGenerator,
  Scene,
  ShaderMaterial,
  SphereGeometry,
  Spherical,
  Sprite,
  SpriteMaterial,
  SRGBColorSpace,
  Vector3,
} from 'three';
import { type Apariencia, aplicarApariencia, type Pendiente } from './apariencia.ts';
import { liberarModelo } from './cargarGlb.ts';
import { type ControlBrillo, dirAGltf, type PresetEstudio } from './iluminacion.ts';
import type { MaterialesVisor } from './modelos.ts';

/** Acciones de la cámara que el HTML (botones y teclado) llama desde fuera del lienzo. */
export interface ApiVista {
  girar: (acimut: number, polar: number) => void;
  acercar: (factor: number) => void;
  reiniciar: () => void;
}

export interface Encuadre {
  /** Radio de la esfera que envuelve al modelo, en metros (mitad de la diagonal de la caja). */
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

const ACIMUT_INICIAL = MathUtils.degToRad(28);
const ELEVACION_INICIAL = MathUtils.degToRad(14);
/** Radiancia de un softbox por cada vatio por d² y por d² de superficie: calibra el brillo del estudio. */
const K_SOFTBOX = 0.5;
/** El suelo del estudio de Blender, iluminado por los softboxes, aclara el fondo: aquí no hay suelo, se compensa. */
const GANANCIA_FONDO = 2.6;
const DISTANCIA_ENTORNO = 20;

function distanciaDeEncuadre(camara: PerspectiveCamera, radio: number): number {
  const vfov = MathUtils.degToRad(camara.fov);
  const hfov = 2 * Math.atan(Math.tan(vfov / 2) * camara.aspect);
  // En vertical (móvil) la pieza larga ocupa todo el ancho: se deja aire; en horizontal se llena el lienzo.
  return (radio / Math.sin(Math.min(vfov, hfov) / 2)) * (camara.aspect < 1 ? 1.12 : 0.88);
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
    cam.far = encuadre.radio * 80;
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

const TONO = { AgX: AgXToneMapping, Neutral: NeutralToneMapping, Filmic: ACESFilmicToneMapping } as const;

const lineal = (c: readonly [number, number, number], k = 1) =>
  new Color().setRGB(c[0] * k, c[1] * k, c[2] * k, LinearSRGBColorSpace);

/** Entorno del estudio: mundo en degradado y un softbox por luz de área, a la misma dirección y tamaño angular. */
function construirEstudio(preset: PresetEstudio): Scene {
  const escena = new Scene();
  const mundo = new Mesh(
    new SphereGeometry(DISTANCIA_ENTORNO * 2, 32, 16),
    new ShaderMaterial({
      side: BackSide,
      depthWrite: false,
      uniforms: {
        uAbajo: { value: lineal(preset.mundo.abajo, preset.mundo.intensidad) },
        uArriba: { value: lineal(preset.mundo.arriba, preset.mundo.intensidad) },
      },
      vertexShader:
        'varying vec3 vD; void main() { vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader:
        'varying vec3 vD; uniform vec3 uAbajo; uniform vec3 uArriba; void main() { gl_FragColor = vec4(mix(uAbajo, uArriba, vD.y * 0.5 + 0.5), 1.0); }',
    }),
  );
  escena.add(mundo);
  for (const l of preset.luces) {
    const dir = new Vector3(...dirAGltf(l.dir));
    const modulo = dir.length();
    const ancho = 2 * DISTANCIA_ENTORNO * Math.tan(Math.min(l.tam_d / (modulo * l.dist), 2.6) / 2);
    const radiancia = (K_SOFTBOX * l.energia_d2) / (l.tam_d * l.tam_d);
    const panel = new Mesh(
      new PlaneGeometry(ancho, ancho),
      new MeshBasicMaterial({ color: lineal(l.color, radiancia), side: DoubleSide, toneMapped: false }),
    );
    panel.position.copy(dir.normalize().multiplyScalar(DISTANCIA_ENTORNO));
    panel.lookAt(0, 0, 0);
    escena.add(panel);
  }
  return escena;
}

function liberarEstudio(e: Scene): void {
  e.traverse((o) => {
    const m = o as Mesh;
    if (!m.isMesh) return;
    m.geometry.dispose();
    (m.material as ShaderMaterial | MeshBasicMaterial).dispose();
  });
}

function degradadoDeFondo(preset: PresetEstudio, brillo: number): CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 4;
  c.height = 128;
  const ctx = c.getContext('2d');
  if (ctx) {
    const k = 2 ** preset.exposicion_ev * brillo * GANANCIA_FONDO;
    const g = ctx.createLinearGradient(0, 0, 0, c.height);
    g.addColorStop(0, `#${lineal(preset.mundo.arriba, preset.mundo.intensidad * k).getHexString(SRGBColorSpace)}`);
    g.addColorStop(1, `#${lineal(preset.mundo.abajo, preset.mundo.intensidad * k).getHexString(SRGBColorSpace)}`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, c.width, c.height);
  }
  const t = new CanvasTexture(c);
  t.colorSpace = SRGBColorSpace;
  return t;
}

function Estudio({ preset, brillo, encuadre }: { preset: PresetEstudio; brillo: number; encuadre: Encuadre }) {
  const { gl, scene, invalidate } = useThree();

  // Tono y exposición: EV del preset más log2 del brillo (la fórmula del catálogo).
  useEffect(() => {
    gl.toneMapping = TONO[preset.tono];
    gl.toneMappingExposure = 2 ** preset.exposicion_ev * brillo;
    invalidate();
  }, [gl, preset.tono, preset.exposicion_ev, brillo, invalidate]);

  // Entorno horneado: se rehace solo al cambiar de preset.
  useEffect(() => {
    const estudio = construirEstudio(preset);
    const pm = new PMREMGenerator(gl);
    const rt = pm.fromScene(estudio, 0, 0.1, DISTANCIA_ENTORNO * 4);
    pm.dispose();
    scene.environment = rt.texture;
    scene.environmentIntensity = 1;
    invalidate();
    return () => {
      scene.environment = null;
      rt.dispose();
      liberarEstudio(estudio);
    };
  }, [gl, scene, preset, invalidate]);

  // Fondo: el degradado del mundo, tal como lo vería la cámara (con la exposición del preset).
  useEffect(() => {
    const fondo = degradadoDeFondo(preset, brillo);
    scene.background = fondo;
    invalidate();
    return () => {
      scene.background = null;
      fondo.dispose();
    };
  }, [scene, preset, brillo, invalidate]);

  // Una sola luz direccional, tenue, desde la clave: solo para la sombra de contacto sobre el suelo.
  const clave = preset.luces.find((l) => l.id === 'clave') ?? preset.luces[0];
  const r = encuadre.radio;
  const pos = useMemo(() => {
    if (!clave) return new Vector3(1, 2, 1);
    return new Vector3(...dirAGltf(clave.dir)).normalize().multiplyScalar(r * 6);
  }, [clave, r]);
  return (
    <directionalLight
      position={pos}
      intensity={0.45}
      castShadow
      shadow-mapSize={[2048, 2048]}
      shadow-radius={6}
      shadow-bias={-0.0002}
      shadow-normalBias={r * 0.02}
    >
      <orthographicCamera attach="shadow-camera" args={[-r * 1.4, r * 1.4, r * 1.4, -r * 1.4, r * 0.5, r * 14]} />
    </directionalLight>
  );
}

/** Etiqueta «Pendiente · pieza» como sprite de tamaño fijo en pantalla (sin DOM: no hay raíces de React extra). */
function crearEtiqueta(p: Pendiente): Sprite {
  const texto = `PENDIENTE · ${p.rol.replaceAll('_', ' ').toUpperCase()}`;
  const fuente = getComputedStyle(document.body).getPropertyValue('--fuente-rotulo').trim() || 'sans-serif';
  const c = document.createElement('canvas');
  const dpr = 2;
  c.height = 40 * dpr;
  const ctx = c.getContext('2d');
  const fijarFuente = () => `${15 * dpr}px ${fuente}`;
  if (ctx) {
    ctx.font = fijarFuente();
    c.width = Math.ceil(ctx.measureText(texto).width) + 24 * dpr;
    ctx.font = fijarFuente();
    ctx.fillStyle = COLOR_TOKENS.carbon.hex;
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.setLineDash([6 * dpr, 4 * dpr]);
    ctx.strokeStyle = COLOR_TOKENS['estado-aviso'].hex;
    ctx.lineWidth = dpr;
    ctx.strokeRect(dpr, dpr, c.width - 2 * dpr, c.height - 2 * dpr);
    ctx.fillStyle = COLOR_TOKENS.hueso.hex;
    ctx.textBaseline = 'middle';
    ctx.fillText(texto, 12 * dpr, c.height / 2 + dpr);
  }
  const mapa = new CanvasTexture(c);
  mapa.colorSpace = SRGBColorSpace;
  const sprite = new Sprite(
    new SpriteMaterial({ map: mapa, sizeAttenuation: false, depthTest: false, transparent: true, toneMapped: false }),
  );
  const alto = 0.024;
  sprite.scale.set((alto * c.width) / c.height, alto, 1);
  sprite.position.copy(p.centro);
  sprite.renderOrder = 10;
  return sprite;
}

function Modelo({
  objeto,
  encuadre,
  preset,
  control,
  brillo,
  materiales,
  claveDe,
}: {
  objeto: Object3D;
  encuadre: Encuadre;
  preset: PresetEstudio;
  control: ControlBrillo;
  brillo: number;
  materiales: MaterialesVisor | null;
  claveDe: (rol: string | null) => string | null;
}) {
  const { invalidate } = useThree();

  // Materiales de la biblioteca sobre las mallas (una vez por modelo). Los marcadores sin modelo pasan a
  // fantasma rayado y salen en `pendientes`.
  const aplicada = useMemo<Apariencia | null>(
    () => (materiales ? aplicarApariencia(objeto, materiales, claveDe, invalidate) : null),
    [objeto, materiales, claveDe, invalidate],
  );

  useEffect(() => {
    aplicada?.ajustarLuz(preset.rugosidad_delta, brillo, control);
    invalidate();
  }, [aplicada, preset.rugosidad_delta, brillo, control, invalidate]);

  useEffect(() => {
    objeto.traverse((o) => {
      const m = o as Mesh;
      if (!m.isMesh) return;
      const fantasma = (m.material as MeshBasicMaterial).isMeshBasicMaterial === true;
      m.castShadow = !fantasma;
      m.receiveShadow = !fantasma;
    });
    invalidate();
  }, [objeto, aplicada, invalidate]);

  // La memoria de GPU del modelo que se sustituye (o se desmonta) se libera aquí.
  useEffect(() => () => aplicada?.liberar(), [aplicada]);
  const etiquetas = useMemo(() => (aplicada?.pendientes ?? []).map(crearEtiqueta), [aplicada]);
  useEffect(
    () => () => {
      for (const e of etiquetas) {
        e.material.map?.dispose();
        e.material.dispose();
      }
    },
    [etiquetas],
  );
  useEffect(() => () => liberarModelo(objeto), [objeto]);

  return (
    <>
      <group position={[-encuadre.centro.x, -encuadre.centro.y, -encuadre.centro.z]}>
        <primitive object={objeto} />
        {etiquetas.map((e) => (
          <primitive key={e.uuid} object={e} />
        ))}
      </group>
      {/* Suelo que solo recibe sombra: sin él, la sombra de contacto no se leería. */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -encuadre.mitadAlto - encuadre.radio * 0.01, 0]}
        receiveShadow
      >
        <planeGeometry args={[encuadre.radio * 30, encuadre.radio * 30]} />
        <shadowMaterial opacity={0.4} />
      </mesh>
    </>
  );
}

export interface EscenaProps {
  objeto: Object3D;
  preset: PresetEstudio;
  control: ControlBrillo;
  brillo: number;
  reducido: boolean;
  materiales: MaterialesVisor | null;
  claveDe: (rol: string | null) => string | null;
  apiRef: RefObject<ApiVista | null>;
}

export default function Escena({
  objeto,
  preset,
  control,
  brillo,
  reducido,
  materiales,
  claveDe,
  apiRef,
}: EscenaProps) {
  const encuadre = useMemo(() => calcularEncuadre(objeto), [objeto]);
  return (
    <Canvas
      frameloop="demand"
      shadows="percentage"
      dpr={[1, 2]}
      camera={{ fov: 30, near: 0.01, far: 100 }}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
    >
      <Estudio preset={preset} brillo={brillo} encuadre={encuadre} />
      <Modelo
        objeto={objeto}
        encuadre={encuadre}
        preset={preset}
        control={control}
        brillo={brillo}
        materiales={materiales}
        claveDe={claveDe}
      />
      <Camara encuadre={encuadre} apiRef={apiRef} reducido={reducido} />
    </Canvas>
  );
}
