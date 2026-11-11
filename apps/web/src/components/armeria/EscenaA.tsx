// Prototipo A · 3D en tiempo real (React Three Fiber). Este módulo es el «chunk 3D»: se carga
// después del primer pintado (el póster ya está en pantalla) y solo si hay WebGL2.
// Pinta bajo demanda: cuando nada se mueve deja de renderizar (0 % de GPU en reposo).
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Bloom, EffectComposer, Noise, ToneMapping, Vignette } from '@react-three/postprocessing';
import { ToneMappingMode } from 'postprocessing';
import { type RefObject, useEffect, useMemo, useRef } from 'react';
import { Color, type PerspectiveCamera, Plane, Raycaster, Vector2, Vector3 } from 'three';
import { anchoVisibleMovil, encuadreSala, encuadreZona, FOV } from './camara.ts';
import { type CanalEscena, crearVigia } from './canal.ts';
import { Director, VARIANTES, type Variante } from './director.ts';
import { crearControl, Sala } from './Sala.tsx';
import { ORDEN_ESTANTERIAS, ZONAS, zonaPorId } from './zonas.ts';

export interface EscenaAProps {
  canal: RefObject<CanalEscena>;
  zonaActiva: string | null;
  zonaAbierta: string | null;
  movil: boolean;
  reducido: boolean;
  intro: boolean;
  variante: Variante;
  calidad: 'alta' | 'baja';
  /** Captura del póster y mediciones: conserva el búfer y pinta siempre. */
  medir: boolean;
  onApuntar: (id: string | null) => void;
  onElegir: (id: string) => void;
  onListo: () => void;
  onIntroFin: () => void;
  onLento: () => void;
}

const ROTACION = { centro: 0.28, lateral: 0.4 };

function Motor(props: EscenaAProps & { control: ReturnType<typeof crearControl> }) {
  const { canal, control, zonaActiva, zonaAbierta, movil, reducido } = props;
  const { camera, size, gl, invalidate, pointer } = useThree();
  const cam = camera as PerspectiveCamera;
  const listo = useRef(false);
  const introAvisada = useRef(false);
  const vigia = useMemo(() => crearVigia(30), []);
  const ultimoPuntero = useRef(0);
  const sombrasPendientes = useRef(3);
  const tmp = useMemo(
    () => ({
      pos: new Vector3(),
      obj: new Vector3(),
      objActual: new Vector3(...encuadreSala(1.6).objetivo),
      ray: new Raycaster(),
      plano: new Plane(new Vector3(0, 0, 1), 1.95),
      p2: new Vector2(),
      offset: { x: 0, y: 0 },
    }),
    [],
  );
  const dentro = useRef(false);
  const linternaPosible = useMemo(() => matchMedia('(hover: hover) and (pointer: fine)').matches, []);

  // El puntero solo enciende la linterna si está sobre el lienzo.
  useEffect(() => {
    const el = gl.domElement;
    const entrar = () => {
      dentro.current = true;
      invalidate();
    };
    const salir = () => {
      dentro.current = false;
      invalidate();
    };
    const mover = () => {
      ultimoPuntero.current = performance.now();
      invalidate();
    };
    el.addEventListener('pointerenter', entrar);
    el.addEventListener('pointerleave', salir);
    el.addEventListener('pointermove', mover);
    return () => {
      el.removeEventListener('pointerenter', entrar);
      el.removeEventListener('pointerleave', salir);
      el.removeEventListener('pointermove', mover);
    };
  }, [gl, invalidate]);

  // Mediciones (?medir): captura del póster, FPS y GPU para scripts/prototipos/*.mjs.
  useEffect(() => {
    if (!props.medir) return;
    const w = window as Window & { __armeria?: unknown };
    w.__armeria = {
      capturar: (anchos: number[], calidad = 0.86) => {
        const fuente = gl.domElement;
        return anchos.map((ancho) => {
          const c = document.createElement('canvas');
          c.width = ancho;
          c.height = Math.round((ancho * fuente.height) / fuente.width);
          c.getContext('2d')?.drawImage(fuente, 0, 0, c.width, c.height);
          return c.toDataURL('image/webp', calidad);
        });
      },
      fotogramas: () => [...canal.current.fotogramas],
      gpu: () => {
        const ctx = gl.getContext();
        const ext = ctx.getExtension('WEBGL_debug_renderer_info');
        return String(ext ? ctx.getParameter(ext.UNMASKED_RENDERER_WEBGL) : ctx.getParameter(ctx.RENDERER));
      },
      dpr: () => gl.getPixelRatio(),
      info: () => ({
        programas: gl.info.programs?.length ?? 0,
        geometrias: gl.info.memory.geometries,
        texturas: gl.info.memory.textures,
      }),
      luz: () => JSON.parse(JSON.stringify(canal.current.director?.luz ?? null)),
    };
  }, [props.medir, gl, canal]);

  // Sombras bajo demanda: las luces que las proyectan no se mueven; solo hace falta recalcularlas al
  // empezar y mientras rueda un cuerpo del compactus (auditor-rendimiento: −65 % de draw calls).
  useEffect(() => {
    gl.shadowMap.autoUpdate = false;
    gl.shadowMap.needsUpdate = true;
  }, [gl]);

  useEffect(() => {
    canal.current.pintar = () => invalidate();
    invalidate();
  }, [canal, invalidate]);

  // Cualquier cambio de estado de la interfaz pide fotogramas.
  useEffect(() => invalidate(), [zonaActiva, zonaAbierta, movil, reducido, props.variante, invalidate]);

  useFrame((_, delta) => {
    const dt = Math.min(delta, 1 / 20);
    const director = canal.current.director;
    if (!director) return;
    const aspecto = size.width / Math.max(1, size.height);
    const activa = zonaPorId(zonaActiva);
    const abierta = zonaPorId(zonaAbierta);

    // Luces.
    control.zonaActiva = zonaActiva;
    director.actualizar(dt, {
      estanteriaActiva: activa?.estanteria ?? null,
      zonaActiva: Boolean(activa),
      linterna: linternaPosible && dentro.current && !abierta,
    });

    // El cuerpo elegido rueda hacia delante sobre sus raíles (docs/02 §3.2).
    const kMov = reducido ? 1 : 1 - Math.exp(-4.5 * dt);
    let movimiento = 0;
    for (const e of ORDEN_ESTANTERIAS) {
      const objetivo =
        !reducido && abierta && abierta.id !== 'banco' && abierta.estanteria === e
          ? ROTACION[e === 'centro' ? 'centro' : 'lateral']
          : 0;
      const antes = control.desplazamiento[e];
      control.desplazamiento[e] = antes + (objetivo - antes) * kMov;
      const resto = Math.abs(objetivo - control.desplazamiento[e]);
      movimiento += resto;
      if (resto > 1e-4 || Math.abs(antes - control.desplazamiento[e]) > 1e-5) sombrasPendientes.current = 2;
    }

    // Cámara: plano general, zona abierta o, en móvil, la zona del carrusel.
    let encuadre = encuadreSala(aspecto);
    let offsetX = 0;
    let offsetY = 0;
    if (movil) {
      // Con movimiento reducido la cámara no viaja con el dedo: corta de zona a zona.
      const bruto = Math.min(ZONAS.length - 1, Math.max(0, canal.current.progreso));
      const p = reducido ? Math.round(bruto) : bruto;
      const i = Math.floor(p);
      const f = p - i;
      const a = ZONAS[i];
      const b = ZONAS[Math.min(ZONAS.length - 1, i + 1)];
      if (a && b) {
        const ea = encuadreZona(
          abierta ?? a,
          aspecto,
          abierta && abierta.id !== 'banco' ? control.desplazamiento[abierta.estanteria] : 0,
          anchoVisibleMovil(abierta ?? a),
        );
        const eb = abierta ? ea : encuadreZona(b, aspecto, 0, anchoVisibleMovil(b));
        const mezcla = (u: readonly number[], v: readonly number[]) =>
          [0, 1, 2].map((k) => (u[k] ?? 0) + ((v[k] ?? 0) - (u[k] ?? 0)) * f) as [number, number, number];
        encuadre = { posicion: mezcla(ea.posicion, eb.posicion), objetivo: mezcla(ea.objetivo, eb.objetivo), fov: FOV };
      }
      // La zona queda en el hueco entre la cabecera y el carrusel; abierta, en el tercio superior
      // (la hoja de abajo ocupa como mucho el 45 % de la pantalla).
      offsetY = abierta ? 0.2 : 0.04;
    } else if (abierta) {
      encuadre = encuadreZona(
        abierta,
        aspecto,
        abierta.id === 'banco' ? 0 : control.desplazamiento[abierta.estanteria],
      );
      // El panel ocupa la derecha: la zona se ve a la izquierda.
      offsetX = 0.16;
    }
    tmp.pos.set(...encuadre.posicion);
    tmp.obj.set(...encuadre.objetivo);
    if (!movil && !abierta && !reducido) {
      // Deriva suave con el ratón (parallax); nunca con movimiento reducido.
      tmp.pos.x += pointer.x * 0.12;
      tmp.pos.y += pointer.y * 0.05;
    }
    const kCam = reducido ? 1 : 1 - Math.exp(-(movil ? 7 : 4.2) * dt);
    movimiento += cam.position.distanceTo(tmp.pos) + tmp.objActual.distanceTo(tmp.obj);
    cam.position.lerp(tmp.pos, kCam);
    tmp.objActual.lerp(tmp.obj, kCam);
    cam.lookAt(tmp.objActual);
    tmp.offset.x += (offsetX - tmp.offset.x) * kCam;
    tmp.offset.y += (offsetY - tmp.offset.y) * kCam;
    movimiento += Math.abs(offsetX - tmp.offset.x) + Math.abs(offsetY - tmp.offset.y);
    if (Math.abs(tmp.offset.x) > 1e-4 || Math.abs(tmp.offset.y) > 1e-4) {
      cam.setViewOffset(
        size.width,
        size.height,
        tmp.offset.x * size.width,
        tmp.offset.y * size.height,
        size.width,
        size.height,
      );
    } else if (cam.view?.enabled) {
      cam.clearViewOffset();
    }
    cam.fov += (encuadre.fov - cam.fov) * kCam;
    cam.updateProjectionMatrix();

    // Linterna: el haz apunta adonde está el ratón, sobre el plano de las baldas.
    if (dentro.current) {
      tmp.p2.set(pointer.x, pointer.y);
      tmp.ray.setFromCamera(tmp.p2, cam);
      tmp.ray.ray.intersectPlane(tmp.plano, control.linterna);
    }

    if (sombrasPendientes.current > 0) {
      gl.shadowMap.needsUpdate = true;
      sombrasPendientes.current--;
    }

    // Mediciones y caída al póster si no llega a 30 FPS (docs/02 §3.6). Con ?medir no cae: se mide tal cual.
    const f = canal.current.fotogramas;
    f.push(delta);
    if (f.length > 240) f.shift();
    if (vigia(f, !director.enIntro && !props.medir, performance.now())) props.onLento();

    if (!listo.current) {
      listo.current = true;
      props.onListo();
    }
    if (!director.enIntro && !introAvisada.current) {
      introAvisada.current = true;
      props.onIntroFin();
    }
    // Sigue pintando mientras algo se mueve.
    // Con el puntero quieto, la linterna llega a su sitio en unos 300 ms: después, la escena deja de pintar.
    const punteroReciente = dentro.current && linternaPosible && performance.now() - ultimoPuntero.current < 400;
    const quieto = director.enReposo && movimiento < 0.002 && !punteroReciente && sombrasPendientes.current === 0;
    if (props.medir || !quieto) invalidate();
  });
  return null;
}

export default function EscenaA(props: EscenaAProps) {
  const { canal, variante, reducido, intro, calidad, medir } = props;
  const control = useMemo(() => crearControl(), []);
  const alta = calidad === 'alta';

  // Un director por montaje: la intro se reproduce una sola vez.
  const director = useMemo(() => new Director({ intro, reducido, variante }), [intro, reducido, variante]);
  useEffect(() => {
    canal.current.director = director;
    control.luz = director.luz;
    control.colorTubo = new Color(VARIANTES[variante].colorTubo);
    canal.current.pintar();
    return () => {
      if (canal.current.director === director) canal.current.director = null;
    };
  }, [canal, control, director, variante]);
  control.calidad = calidad;
  control.luz = director.luz;

  const inicial = encuadreSala(16 / 9);
  return (
    <Canvas
      frameloop={medir ? 'always' : 'demand'}
      dpr={[1, alta ? 1.5 : 1.25]}
      shadows={alta ? 'percentage' : false}
      flat
      gl={{ antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: medir, stencil: false }}
      camera={{ fov: FOV, near: 0.1, far: 40, position: [...inicial.posicion] }}
      aria-hidden="true"
    >
      <color attach="background" args={['#040506']} />
      <fog attach="fog" args={['#040506', 9, 20]} />
      <Sala control={control} onApuntar={props.onApuntar} onElegir={props.onElegir} />
      <Motor {...props} control={control} />
      <EffectComposer multisampling={alta ? 2 : 0} enableNormalPass={false}>
        <Bloom
          mipmapBlur
          luminanceThreshold={0.92}
          luminanceSmoothing={0.2}
          intensity={alta ? 0.75 : 0.55}
          radius={0.7}
        />
        <ToneMapping mode={ToneMappingMode.AGX} />
        <Vignette offset={0.28} darkness={0.7} />
        <Noise premultiply opacity={0.14} />
      </EffectComposer>
    </Canvas>
  );
}
