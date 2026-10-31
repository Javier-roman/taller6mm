// Isla 3D del spike: una bocacha de latón (perfil de torno) iluminada por un «flexo» cálido,
// con bloom, viñeta y tone mapping AgX. Entorno procedural (RoomEnvironment): ninguna descarga
// externa, así que no hace falta abrir la CSP a CDNs de HDRI.
import { OrbitControls } from '@react-three/drei';
import { Canvas, useThree } from '@react-three/fiber';
import { Bloom, EffectComposer, ToneMapping, Vignette } from '@react-three/postprocessing';
import { ToneMappingMode } from 'postprocessing';
import { useEffect, useMemo } from 'react';
import { LatheGeometry, NoToneMapping, PMREMGenerator, Vector2 } from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

const MM = 0.001; // datos en mm, escena en metros (docs/05 §4)

/** Perfil (radio, posición) en mm de una bocacha de 24 × 60 mm con ranuras. */
const PROFILE_MM: Array<[number, number]> = [
  [0, 0],
  [7, 0],
  [7, 14],
  [12, 14],
  [12, 22],
  [10.5, 23],
  [10.5, 27],
  [12, 28],
  [12, 36],
  [10.5, 37],
  [10.5, 41],
  [12, 42],
  [12, 58],
  [11, 60],
  [7.5, 60],
  [7.5, 46],
  [0, 46],
];

function Environment() {
  const { gl, scene } = useThree();
  useEffect(() => {
    const pmrem = new PMREMGenerator(gl);
    const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    return () => {
      scene.environment = null;
      env.dispose();
      pmrem.dispose();
    };
  }, [gl, scene]);
  return null;
}

function Muzzle() {
  const geometry = useMemo(() => {
    const points = PROFILE_MM.map(([r, y]) => new Vector2(r * MM, y * MM));
    const g = new LatheGeometry(points, 96);
    g.rotateZ(-Math.PI / 2); // eje del cañón a lo largo de +X
    g.center();
    return g;
  }, []);
  return (
    <mesh geometry={geometry} castShadow>
      <meshStandardMaterial color="#B8925A" metalness={1} roughness={0.28} />
    </mesh>
  );
}

export default function BrassScene() {
  return (
    <Canvas
      frameloop="demand"
      dpr={[1, 2]}
      camera={{ position: [0.05, 0.03, 0.09], fov: 35, near: 0.001, far: 10 }}
      gl={{ antialias: false, toneMapping: NoToneMapping }}
      aria-label="Bocacha de latón en 3D"
      role="img"
    >
      <color attach="background" args={['#0b0c0e']} />
      <Environment />
      <spotLight position={[0.15, 0.2, 0.1]} angle={0.5} penumbra={0.6} intensity={6} color="#ffd7a0" />
      <Muzzle />
      <OrbitControls makeDefault enablePan={false} minDistance={0.05} maxDistance={0.3} />
      <EffectComposer multisampling={4}>
        <Bloom mipmapBlur luminanceThreshold={0.85} intensity={0.6} />
        <Vignette offset={0.3} darkness={0.7} />
        <ToneMapping mode={ToneMappingMode.AGX} />
      </EffectComposer>
    </Canvas>
  );
}
