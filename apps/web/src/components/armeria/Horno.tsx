// Horno del prototipo B: renderiza la misma sala del prototipo A desde el encuadre fijo del póster y
// saca un pase por grupo de luz (sumables), más albedo, normales y profundidad. Lo usa
// scripts/prototipos/hornear-b.mjs; no es una página para usuarios.
// Sustituye al render de Blender (Cycles) que proponía docs/02 §3.5: Blender no está instalado en el
// equipo de Javi (instalarlo pide permisos de administrador), así que los pases salen del rasterizador
// de three.js, con sombras de mapa en vez de trazado de rayos.
import { Canvas, useThree } from '@react-three/fiber';
import { useEffect, useMemo } from 'react';
import {
  Color,
  LinearSRGBColorSpace,
  LinearToneMapping,
  type Material,
  type Mesh,
  MeshBasicMaterial,
  MeshNormalMaterial,
  type MeshStandardMaterial,
  type PerspectiveCamera,
  ShaderMaterial,
  SRGBColorSpace,
} from 'three';
import { ENCUADRE_POSTER } from './camara.ts';
import { crearIluminacion, type Iluminacion } from './director.ts';
import { EXPOSICION_HORNO, type Pase, PROFUNDIDAD } from './pases.ts';
import { crearControl, Sala } from './Sala.tsx';
import { ORDEN_ESTANTERIAS } from './zonas.ts';

const apagada = (): Iluminacion => ({ ...crearIluminacion(0), tubos: { izquierda: 0, centro: 0, derecha: 0 } });

function nivelesDe(pase: Pase): Iluminacion {
  const luz = apagada();
  if (pase === 'base') luz.ambiente = 1;
  if (pase === 'calidas') luz.calidas = 1;
  if (pase === 'rotulos') {
    luz.rotulos = 1;
    luz.marca = 1;
  }
  for (const e of ORDEN_ESTANTERIAS) if (pase === `tubo-${e}`) luz.tubos[e] = 1;
  return luz;
}

const materialProfundidad = () =>
  new ShaderMaterial({
    uniforms: { cerca: { value: PROFUNDIDAD.cerca }, lejos: { value: PROFUNDIDAD.lejos } },
    vertexShader: `
      varying float vProfundidad;
      void main() {
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vProfundidad = -mv.z;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      uniform float cerca;
      uniform float lejos;
      varying float vProfundidad;
      void main() {
        float d = clamp((vProfundidad - cerca) / (lejos - cerca), 0.0, 1.0);
        gl_FragColor = vec4(vec3(d), 1.0);
      }`,
  });

function Controlador({ control }: { control: ReturnType<typeof crearControl> }) {
  const { gl, scene, camera, advance } = useThree();
  useEffect(() => {
    const cam = camera as PerspectiveCamera;
    cam.position.set(...ENCUADRE_POSTER.posicion);
    cam.lookAt(...ENCUADRE_POSTER.objetivo);
    cam.fov = ENCUADRE_POSTER.fov;
    cam.updateProjectionMatrix();
    gl.toneMapping = LinearToneMapping;
    gl.toneMappingExposure = EXPOSICION_HORNO;

    const originales = new Map<Mesh, Material | Material[]>();
    const sustituir = (crear: (m: MeshStandardMaterial) => Material) => {
      scene.traverse((o) => {
        const mesh = o as Mesh;
        // Las cajas de zona son invisibles: no se tocan.
        if (!mesh.isMesh || !mesh.visible) return;
        originales.set(mesh, mesh.material);
        const m = (Array.isArray(mesh.material) ? mesh.material[0] : mesh.material) as MeshStandardMaterial;
        mesh.material = crear(m);
      });
    };
    const restaurar = () => {
      for (const [mesh, m] of originales) mesh.material = m;
      originales.clear();
    };

    const w = window as Window & { __horno?: unknown };
    w.__horno = {
      pase: (pase: Pase, calidad = 0.9) => {
        restaurar();
        const { background, fog } = scene;
        gl.outputColorSpace = SRGBColorSpace;
        gl.setClearColor('#000000', 1);
        // Los pases de datos van sin fondo ni niebla y sin conversión de color: valores en bruto.
        if (pase === 'normal' || pase === 'profundidad') {
          scene.background = null;
          scene.fog = null;
        }
        if (pase === 'albedo') {
          sustituir(
            (m) =>
              new MeshBasicMaterial({
                color: m.color,
                map: m.map ?? null,
                transparent: m.transparent,
                opacity: m.opacity,
                toneMapped: false,
                fog: false,
              }),
          );
        } else if (pase === 'normal') {
          gl.outputColorSpace = LinearSRGBColorSpace;
          gl.setClearColor(new Color().setRGB(0.5, 0.5, 1, LinearSRGBColorSpace), 1);
          sustituir((m) => new MeshNormalMaterial({ normalMap: m.normalMap ?? null }));
        } else if (pase === 'profundidad') {
          gl.outputColorSpace = LinearSRGBColorSpace;
          gl.setClearColor('#ffffff', 1);
          const material = materialProfundidad();
          sustituir(() => material);
        }
        const luz = nivelesDe(pase);
        Object.assign(control.luz, luz);
        control.luz.tubos = { ...luz.tubos };
        // Dos fotogramas: el primero actualiza luces y sombras con los niveles nuevos.
        advance(performance.now());
        advance(performance.now() + 16);
        const url = gl.domElement.toDataURL('image/webp', calidad);
        restaurar();
        scene.background = background;
        scene.fog = fog;
        return url;
      },
      listo: true,
    };
  }, [gl, scene, camera, advance, control]);
  return null;
}

export default function Horno() {
  const control = useMemo(() => {
    const c = crearControl(apagada());
    c.calidad = 'alta';
    return c;
  }, []);
  return (
    <div style={{ position: 'fixed', inset: 0 }}>
      <Canvas
        frameloop="never"
        dpr={1}
        shadows="percentage"
        gl={{ antialias: true, preserveDrawingBuffer: true, stencil: false }}
        camera={{ fov: ENCUADRE_POSTER.fov, near: 0.1, far: 40, position: [...ENCUADRE_POSTER.posicion] }}
      >
        <color attach="background" args={['#040506']} />
        <fog attach="fog" args={['#040506', 9, 20]} />
        <Sala control={control} />
        <Controlador control={control} />
      </Canvas>
    </div>
  );
}
