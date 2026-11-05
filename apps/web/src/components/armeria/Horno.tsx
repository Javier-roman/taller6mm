// Horno del prototipo B: renderiza la misma sala del prototipo A desde el encuadre fijo del póster y
// saca un pase por grupo de luz (sumables), más albedo, normales y profundidad. Lo usa
// scripts/prototipos/hornear-b.mjs; no es una página para usuarios.
// Sustituye al render de Blender (Cycles) que proponía docs/02 §3.5: Blender no está instalado en el
// equipo de Javi (instalarlo pide permisos de administrador), así que los pases salen del rasterizador
// de three.js, con sombras de mapa en vez de trazado de rayos.
import { Canvas, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useState } from 'react';
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
  type SpotLight,
  SRGBColorSpace,
  Vector3,
} from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { ENCUADRE_POSTER } from './camara.ts';
import { crearIluminacion, type Iluminacion } from './director.ts';
import { fuentesListas } from './fuentes.ts';
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

    // Los efectos de tiempo real (haces y reflejos falsos) no entran en ningún pase horneado: en Cycles
    // salen del volumen y del trazado, y en los pases de datos ensuciarían normales y profundidad.
    const conEfectosOcultos = <T,>(trabajo: () => T): T => {
      const ocultos: { visible: boolean }[] = [];
      scene.traverse((o) => {
        if (o.userData['soloTiempoReal'] && o.visible) {
          o.visible = false;
          ocultos.push(o);
        }
      });
      try {
        return trabajo();
      } finally {
        for (const o of ocultos) o.visible = true;
      }
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
        const url = conEfectosOcultos(() => {
          advance(performance.now() + 32);
          return gl.domElement.toDataURL('image/webp', calidad);
        });
        restaurar();
        scene.background = background;
        scene.fog = fog;
        return url;
      },
      /**
       * Sala y cámara del póster en glTF binario (base64) para hornear con Cycles: todos los grupos a su
       * nivel de referencia, con las luces y los emisivos nombrados por grupo (luz:*, emisivo:*).
       */
      exportar: async () => {
        restaurar();
        const luz = crearIluminacion(1);
        luz.acento = 0;
        luz.linterna = 0;
        Object.assign(control.luz, luz);
        control.luz.tubos = { ...luz.tubos };
        advance(performance.now());
        advance(performance.now() + 16);
        const ocultos: { visible: boolean }[] = [];
        scene.traverse((o) => {
          if (o.userData['soloTiempoReal'] && o.visible) {
            o.visible = false;
            ocultos.push(o);
          }
          // glTF (y Blender) orientan un foco por el −Z de su nodo; three, por su `target`. Se gira cada
          // foco hacia su objetivo para que la dirección viaje en el glTF (three no usa esa rotación).
          const foco = o as SpotLight;
          if (foco.isSpotLight) {
            foco.target.updateMatrixWorld();
            foco.lookAt(foco.target.getWorldPosition(new Vector3()));
            foco.updateMatrixWorld();
          }
        });
        try {
          const glb = (await new GLTFExporter().parseAsync([scene, camera], {
            binary: true,
            onlyVisible: true,
          })) as ArrayBuffer;
          const bytes = new Uint8Array(glb);
          let bin = '';
          for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
          return btoa(bin);
        } finally {
          for (const o of ocultos) o.visible = true;
        }
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
  // Los rótulos se dibujan en canvas: sin las fuentes cargadas saldrían en una sans genérica.
  const [fuentes, setFuentes] = useState(false);
  useEffect(() => {
    fuentesListas().then(() => setFuentes(true));
  }, []);
  if (!fuentes) return null;
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
