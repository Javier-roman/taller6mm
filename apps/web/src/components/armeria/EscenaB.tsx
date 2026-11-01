// Prototipo B · 2,5D re-iluminable: WebGL2 a pelo (sin three.js) sobre los pases horneados de la
// misma sala. Un único shader suma los pases de luz con el nivel de cada grupo (lo decide el mismo
// director que en A), re-ilumina la zona activa, aplica la linterna sobre las normales y la
// profundidad, mueve la imagen con un parallax leve y termina con AgX, viñeta y grano.
// La cámara no se mueve: «abrir» una zona es un zoom 2D sobre la imagen (apertura simulada).
import { type RefObject, useEffect, useMemo, useRef } from 'react';
import { ASPECTO_POSTER, ENCUADRE_POSTER, proyectar, type Rect, rectZona } from './camara.ts';
import type { CanalEscena } from './canal.ts';
import { Director, VARIANTES, type Variante } from './director.ts';
import { EXPOSICION_HORNO, PASES_DATOS, PASES_LUZ, type Pase, PROFUNDIDAD, RUTA_PASES } from './pases.ts';
import { ESTANTERIAS, ORDEN_ESTANTERIAS, ZONAS, zonaPorId } from './zonas.ts';

export interface EscenaBProps {
  canal: RefObject<CanalEscena>;
  zonaActiva: string | null;
  zonaAbierta: string | null;
  movil: boolean;
  reducido: boolean;
  intro: boolean;
  variante: Variante;
  medir: boolean;
  etiqueta: RefObject<HTMLElement | null>;
  onApuntar: (id: string | null) => void;
  onElegir: (id: string) => void;
  onListo: () => void;
  onIntroFin: () => void;
  onLento: () => void;
}

const VERTICES = `#version 300 es
in vec2 aPos;
out vec2 vUv;
void main() {
  vUv = vec2(aPos.x * 0.5 + 0.5, 0.5 - aPos.y * 0.5);
  gl_Position = vec4(aPos, 0.0, 1.0);
}`;

const FRAGMENTOS = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 salida;
uniform sampler2D uBase, uTuboI, uTuboC, uTuboD, uCalidas, uRotulos, uAlbedo, uNormal, uProf;
uniform vec2 uCentro, uVisible, uParallax, uLinterna, uResolucion;
uniform vec3 uTubos, uTinte;
uniform float uAmbiente, uCalidasN, uRotulosN, uAcento, uLinternaN, uTiempo, uTanFov, uAspecto;
uniform vec4 uRectActivo;
uniform int uFilaActiva;
uniform vec4 uSegmentos[3];

const float EXPO = ${EXPOSICION_HORNO.toFixed(4)};
const float CERCA = ${PROFUNDIDAD.cerca.toFixed(4)};
const float LEJOS = ${PROFUNDIDAD.lejos.toFixed(4)};

// AgX de three.js r186 (tonemapping_pars_fragment), el mismo que usa el prototipo A.
const mat3 REC2020_A_SRGB = mat3(vec3(1.6605, -0.1246, -0.0182), vec3(-0.5876, 1.1329, -0.1006), vec3(-0.0728, -0.0083, 1.1187));
const mat3 SRGB_A_REC2020 = mat3(vec3(0.6274, 0.0691, 0.0164), vec3(0.3293, 0.9195, 0.0880), vec3(0.0433, 0.0113, 0.8956));
vec3 contraste(vec3 x) {
  vec3 x2 = x * x;
  vec3 x4 = x2 * x2;
  return 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232;
}
vec3 agx(vec3 c) {
  const mat3 dentro = mat3(vec3(0.856627153315983, 0.137318972929847, 0.11189821299995), vec3(0.0951212405381588, 0.761241990602591, 0.0767994186031903), vec3(0.0482516061458583, 0.101439036467562, 0.811302368396859));
  const mat3 fuera = mat3(vec3(1.1271005818144368, -0.1413297634984383, -0.14132976349843826), vec3(-0.11060664309660323, 1.157823702216272, -0.11060664309660294), vec3(-0.016493938717834573, -0.016493938717834257, 1.2519364065950405));
  c = dentro * (SRGB_A_REC2020 * c);
  c = clamp((log2(max(c, 1e-10)) + 12.47393) / 16.499999, 0.0, 1.0);
  c = fuera * contraste(c);
  return clamp(REC2020_A_SRGB * pow(max(vec3(0.0), c), vec3(2.2)), 0.0, 1.0);
}
vec3 aSrgb(vec3 c) {
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}
vec3 posVista(vec2 uv, float d) {
  vec2 ndc = vec2(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0);
  return vec3(ndc.x * uTanFov * uAspecto * d, ndc.y * uTanFov * d, -d);
}
float rect(vec2 p, vec4 r, float s) {
  vec2 a = smoothstep(r.xy - s, r.xy + s, p);
  vec2 b = 1.0 - smoothstep(r.xy + r.zw - s, r.xy + r.zw + s, p);
  return a.x * a.y * b.x * b.y;
}
float segmento(vec2 p, vec2 a, vec2 b) {
  vec2 pa = p - a;
  vec2 ba = b - a;
  return length(pa - ba * clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0));
}
void main() {
  vec2 uv = uCentro + (vUv - 0.5) * uVisible;
  uv += uParallax * (1.0 - texture(uProf, uv).r);
  vec3 tI = texture(uTuboI, uv).rgb;
  vec3 tC = texture(uTuboC, uv).rgb;
  vec3 tD = texture(uTuboD, uv).rgb;
  vec3 rot = texture(uRotulos, uv).rgb;
  vec3 c = texture(uBase, uv).rgb * uAmbiente
    + (tI * uTubos.x + tC * uTubos.y + tD * uTubos.z) * uTinte
    + texture(uCalidas, uv).rgb * uCalidasN
    + rot * uRotulosN;
  if (uRectActivo.z > 0.0) {
    // Acento: la zona activa recibe otra vez la luz de su fila de tubos y su rótulo se enciende.
    float m = rect(uv, uRectActivo, 0.012) * uAcento;
    vec3 fila = uFilaActiva == 0 ? tI : (uFilaActiva == 1 ? tC : tD);
    c += fila * uTinte * m * 0.75 + rot * m * 1.1;
  }
  c /= EXPO;
  if (uLinternaN > 0.001) {
    float d = mix(CERCA, LEJOS, texture(uProf, uv).r);
    vec3 p = posVista(uv, d);
    vec3 n = normalize(texture(uNormal, uv).xyz * 2.0 - 1.0);
    float cono = smoothstep(cos(0.17), cos(0.06), dot(normalize(p), normalize(posVista(uLinterna, 1.0))));
    float lambert = max(dot(n, normalize(-p)), 0.0);
    c += texture(uAlbedo, uv).rgb * lambert * cono * uLinternaN * 34.0 / (3.14159 * d * d) * vec3(1.0, 0.97, 0.92);
  }
  // Resplandor de los tubos (sustituye al bloom de A).
  vec2 q = uv * vec2(uAspecto, 1.0);
  for (int i = 0; i < 3; i++) {
    float nivel = i == 0 ? uTubos.x : (i == 1 ? uTubos.y : uTubos.z);
    float dd = segmento(q, uSegmentos[i].xy * vec2(uAspecto, 1.0), uSegmentos[i].zw * vec2(uAspecto, 1.0));
    c += uTinte * nivel * (exp(-dd * dd / 0.000012) * 1.6 + exp(-dd * dd / 0.0011) * 0.22);
  }
  c = agx(c);
  vec2 v = (vUv - 0.5) * vec2(uResolucion.x / uResolucion.y, 1.0);
  c *= 1.0 - 0.62 * smoothstep(0.45, 1.25, length(v));
  float g = fract(sin(dot(gl_FragCoord.xy + uTiempo * 61.0, vec2(12.9898, 78.233))) * 43758.5453);
  c += (g - 0.5) * 0.05 * c;
  salida = vec4(aSrgb(clamp(c, 0.0, 1.0)), 1.0);
}`;

/** Rectángulos de las zonas sobre la imagen (uv 0–1, y hacia abajo). El banco va primero: está delante. */
const RECTS: { id: string; rect: Rect }[] = [...ZONAS]
  .sort((a, b) => (a.id === 'banco' ? -1 : b.id === 'banco' ? 1 : 0))
  .map((z) => ({ id: z.id, rect: rectZona(z, ENCUADRE_POSTER, ASPECTO_POSTER) }));

/** Tubos de cada estantería proyectados sobre la imagen (para su resplandor). */
const SEGMENTOS = ORDEN_ESTANTERIAS.map((e) => {
  const x = ESTANTERIAS[e].x;
  const a = proyectar([x - 1.1, 3.42, -1.05], ENCUADRE_POSTER, ASPECTO_POSTER);
  const b = proyectar([x + 1.1, 3.42, -1.05], ENCUADRE_POSTER, ASPECTO_POSTER);
  return [a[0], a[1], b[0], b[1]] as const;
});

const lineal = (hex: string) =>
  [1, 3, 5].map((i) => {
    const c = Number.parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });

/** Los pases se hornearon con los tubos fríos de «penumbra»: otra variante tiñe con la razón de colores. */
function tinte(variante: Variante) {
  const base = lineal(VARIANTES.penumbra.colorTubo);
  const destino = lineal(VARIANTES[variante].colorTubo);
  return destino.map((c, i) => c / (base[i] ?? 1)) as [number, number, number];
}

const tanFov = Math.tan((ENCUADRE_POSTER.fov * Math.PI) / 360);

function compilar(gl: WebGL2RenderingContext) {
  const shader = (tipo: number, fuente: string) => {
    const s = gl.createShader(tipo);
    if (!s) throw new Error('No se pudo crear el shader');
    gl.shaderSource(s, fuente);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) ?? 'Shader inválido');
    return s;
  };
  const programa = gl.createProgram();
  gl.attachShader(programa, shader(gl.VERTEX_SHADER, VERTICES));
  gl.attachShader(programa, shader(gl.FRAGMENT_SHADER, FRAGMENTOS));
  gl.linkProgram(programa);
  if (!gl.getProgramParameter(programa, gl.LINK_STATUS))
    throw new Error(gl.getProgramInfoLog(programa) ?? 'Programa inválido');
  return programa;
}

async function cargarPase(pase: Pase) {
  const respuesta = await fetch(`${RUTA_PASES}/${pase}.webp`);
  if (!respuesta.ok) throw new Error(`Falta el pase ${pase}`);
  return createImageBitmap(await respuesta.blob(), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}

const UNIDADES: Pase[] = [...PASES_LUZ, ...PASES_DATOS];
const UNIFORME_DE: Record<Pase, string> = {
  base: 'uBase',
  'tubo-izquierda': 'uTuboI',
  'tubo-centro': 'uTuboC',
  'tubo-derecha': 'uTuboD',
  calidas: 'uCalidas',
  rotulos: 'uRotulos',
  albedo: 'uAlbedo',
  normal: 'uNormal',
  profundidad: 'uProf',
};

export default function EscenaB(props: EscenaBProps) {
  const lienzo = useRef<HTMLCanvasElement>(null);
  const ultimas = useRef(props);
  ultimas.current = props;
  const { intro, reducido, variante, canal } = props;
  const director = useMemo(() => new Director({ intro, reducido, variante }), [intro, reducido, variante]);
  useEffect(() => {
    canal.current.director = director;
    canal.current.pintar();
  }, [canal, director]);

  useEffect(() => {
    const canvas = lienzo.current;
    if (!canvas) return;
    const gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      preserveDrawingBuffer: ultimas.current.medir,
      powerPreference: 'high-performance',
    });
    if (!gl) {
      ultimas.current.onLento();
      return;
    }
    let vivo = true;
    let cuadro = 0;
    let anterior = performance.now();
    let listo = false;
    let introAvisada = false;
    const estado = {
      centro: [0.5, 0.5],
      zoom: 1,
      parallax: [0, 0],
      puntero: [0, 0] as [number, number],
      linterna: [0.5, 0.5] as [number, number],
      dentro: false,
      apuntada: null as string | null,
      movimiento: 1,
    };
    const linternaPosible = matchMedia('(hover: hover) and (pointer: fine)').matches;
    const programa = compilar(gl);
    gl.useProgram(programa);
    const u = (nombre: string) => gl.getUniformLocation(programa, nombre);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(programa, 'aPos');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
    gl.uniform4fv(u('uSegmentos'), SEGMENTOS.flat());
    gl.uniform1f(u('uTanFov'), tanFov);
    gl.uniform1f(u('uAspecto'), ASPECTO_POSTER);

    const tamano = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.round(canvas.clientWidth * dpr);
      const h = Math.round(canvas.clientHeight * dpr);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    };

    /** Ventana visible de la imagen (uv) para el aspecto de la pantalla y un zoom. */
    const visible = (zoom: number) => {
      const aspecto = canvas.clientWidth / Math.max(1, canvas.clientHeight);
      const base = aspecto >= ASPECTO_POSTER ? [1, ASPECTO_POSTER / aspecto] : [aspecto / ASPECTO_POSTER, 1];
      return [(base[0] ?? 1) / zoom, (base[1] ?? 1) / zoom] as const;
    };
    const aImagen = (x: number, y: number) => {
      const [vw, vh] = visible(estado.zoom);
      return [
        (estado.centro[0] ?? 0.5) + (x / canvas.clientWidth - 0.5) * vw,
        (estado.centro[1] ?? 0.5) + (y / canvas.clientHeight - 0.5) * vh,
      ] as const;
    };
    const aPantalla = (uvx: number, uvy: number) => {
      const [vw, vh] = visible(estado.zoom);
      return [
        ((uvx - (estado.centro[0] ?? 0.5)) / vw + 0.5) * canvas.clientWidth,
        ((uvy - (estado.centro[1] ?? 0.5)) / vh + 0.5) * canvas.clientHeight,
      ] as const;
    };
    const zonaEn = (x: number, y: number) => {
      const [ux, uy] = aImagen(x, y);
      return (
        RECTS.find(({ rect: r }) => ux >= r.x && ux <= r.x + r.ancho && uy >= r.y && uy <= r.y + r.alto)?.id ?? null
      );
    };

    const objetivo = () => {
      const p = ultimas.current;
      const abierta = zonaPorId(p.zonaAbierta);
      const centroDe = (id: string) => {
        const r = RECTS.find((z) => z.id === id)?.rect;
        return r ? [r.x + r.ancho / 2, r.y + r.alto / 2] : [0.5, 0.5];
      };
      if (p.movil) {
        const progreso = Math.min(ZONAS.length - 1, Math.max(0, canal.current.progreso));
        const i = Math.floor(progreso);
        const f = progreso - i;
        const a = centroDe(abierta?.id ?? ZONAS[i]?.id ?? 'banco');
        const b = abierta ? a : centroDe(ZONAS[Math.min(ZONAS.length - 1, i + 1)]?.id ?? 'banco');
        return {
          centro: [
            (a[0] ?? 0.5) + ((b[0] ?? 0.5) - (a[0] ?? 0.5)) * f,
            (a[1] ?? 0.5) + ((b[1] ?? 0.5) - (a[1] ?? 0.5)) * f,
          ],
          zoom: 1.35,
        };
      }
      if (abierta) {
        const r = RECTS.find((z) => z.id === abierta.id)?.rect;
        if (r) {
          const zoom = Math.min(2.2, 0.6 / Math.max(r.ancho, r.alto * 0.9));
          const [vw] = visible(zoom);
          // El panel ocupa la derecha: la zona se ve a la izquierda.
          return { centro: [r.x + r.ancho / 2 + 0.16 * vw, r.y + r.alto / 2], zoom };
        }
      }
      return { centro: [0.5, 0.5], zoom: 1 };
    };

    const pintar = (ahora: number) => {
      if (!vivo) return;
      cuadro = 0;
      const dt = Math.min((ahora - anterior) / 1000, 1 / 20);
      anterior = ahora;
      const p = ultimas.current;
      const d = canal.current.director;
      if (!d) return;
      tamano();
      const activa = zonaPorId(p.zonaActiva);
      const abierta = zonaPorId(p.zonaAbierta);
      const luz = d.actualizar(dt, {
        estanteriaActiva: activa?.estanteria ?? null,
        zonaActiva: Boolean(activa),
        linterna: linternaPosible && estado.dentro && !abierta,
      });

      // Encuadre: zoom y desplazamiento suaves (instantáneos con movimiento reducido).
      const meta = objetivo();
      const k = p.reducido ? 1 : 1 - Math.exp(-(p.movil ? 7 : 4.2) * dt);
      estado.movimiento =
        Math.abs(meta.zoom - estado.zoom) +
        Math.abs((meta.centro[0] ?? 0) - (estado.centro[0] ?? 0)) +
        Math.abs((meta.centro[1] ?? 0) - (estado.centro[1] ?? 0));
      estado.zoom += (meta.zoom - estado.zoom) * k;
      const [vw, vh] = visible(estado.zoom);
      const limitar = (c: number, v: number) => Math.min(1 - v / 2, Math.max(v / 2, c));
      estado.centro = [
        limitar((estado.centro[0] ?? 0.5) + ((meta.centro[0] ?? 0.5) - (estado.centro[0] ?? 0.5)) * k, vw),
        limitar((estado.centro[1] ?? 0.5) + ((meta.centro[1] ?? 0.5) - (estado.centro[1] ?? 0.5)) * k, vh),
      ];
      // Parallax con el ratón (nunca con movimiento reducido ni con una zona abierta).
      const par = !p.reducido && !p.movil && !abierta ? estado.puntero : [0, 0];
      estado.parallax = [
        (estado.parallax[0] ?? 0) + (-(par[0] ?? 0) * 0.006 - (estado.parallax[0] ?? 0)) * k,
        (estado.parallax[1] ?? 0) + ((par[1] ?? 0) * 0.004 - (estado.parallax[1] ?? 0)) * k,
      ];

      gl.uniform2f(u('uCentro'), estado.centro[0] ?? 0.5, estado.centro[1] ?? 0.5);
      gl.uniform2f(u('uVisible'), vw, vh);
      gl.uniform2f(u('uParallax'), estado.parallax[0] ?? 0, estado.parallax[1] ?? 0);
      gl.uniform2f(u('uResolucion'), canvas.width, canvas.height);
      gl.uniform3f(u('uTubos'), luz.tubos.izquierda, luz.tubos.centro, luz.tubos.derecha);
      gl.uniform3fv(u('uTinte'), tinte(d.variante));
      gl.uniform1f(u('uAmbiente'), luz.ambiente);
      gl.uniform1f(u('uCalidasN'), luz.calidas);
      // Los rótulos de zona y la marca comparten pase: la marca manda durante la intro.
      gl.uniform1f(u('uRotulosN'), d.enIntro ? Math.max(luz.rotulos, luz.marca * 0.8) : luz.rotulos);
      const r = activa ? RECTS.find((z) => z.id === activa.id)?.rect : undefined;
      gl.uniform4f(u('uRectActivo'), r?.x ?? 0, r?.y ?? 0, r?.ancho ?? 0, r?.alto ?? 0);
      gl.uniform1i(u('uFilaActiva'), activa ? ORDEN_ESTANTERIAS.indexOf(activa.estanteria) : -1);
      gl.uniform1f(u('uAcento'), luz.acento);
      gl.uniform2f(u('uLinterna'), estado.linterna[0], estado.linterna[1]);
      gl.uniform1f(u('uLinternaN'), luz.linterna);
      gl.uniform1f(u('uTiempo'), (ahora / 1000) % 100);
      gl.drawArrays(gl.TRIANGLES, 0, 3);

      // Etiqueta HTML de la zona activa, sobre su rótulo.
      const el = p.etiqueta.current;
      if (el) {
        if (activa && !abierta && !p.movil) {
          const [ax, ay] = proyectar(
            [
              activa.anclaRotulo[0],
              activa.anclaRotulo[1] + (activa.id === 'banco' ? 0.12 : 0.2),
              activa.anclaRotulo[2],
            ],
            ENCUADRE_POSTER,
            ASPECTO_POSTER,
          );
          const [x, y] = aPantalla(ax, ay);
          el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) translate(-50%, -100%)`;
          el.dataset['visible'] = 'true';
        } else {
          el.dataset['visible'] = 'false';
        }
      }

      const f = canal.current.fotogramas;
      f.push(dt);
      if (f.length > 240) f.shift();
      if (!listo) {
        listo = true;
        p.onListo();
      }
      if (!d.enIntro && !introAvisada) {
        introAvisada = true;
        p.onIntroFin();
      }
      const quieto =
        d.enReposo && estado.movimiento < 0.0005 && !(estado.dentro && luz.linterna > 0.01 && linternaPosible);
      if (p.medir || !quieto) pedir();
    };
    const pedir = () => {
      if (!cuadro && vivo) cuadro = requestAnimationFrame(pintar);
    };
    canal.current.pintar = pedir;

    // Puntero: linterna, parallax, zona apuntada y clic.
    const mover = (e: PointerEvent) => {
      const caja = canvas.getBoundingClientRect();
      const x = e.clientX - caja.left;
      const y = e.clientY - caja.top;
      estado.puntero = [(x / caja.width) * 2 - 1, (y / caja.height) * 2 - 1];
      const [ux, uy] = aImagen(x, y);
      estado.linterna = [ux, uy];
      estado.dentro = true;
      if (!ultimas.current.movil) {
        const id = zonaEn(x, y);
        if (id !== estado.apuntada) {
          estado.apuntada = id;
          ultimas.current.onApuntar(id);
        }
      }
      pedir();
    };
    const salir = () => {
      estado.dentro = false;
      if (estado.apuntada) {
        estado.apuntada = null;
        ultimas.current.onApuntar(null);
      }
      pedir();
    };
    const clic = (e: MouseEvent) => {
      const caja = canvas.getBoundingClientRect();
      const id = zonaEn(e.clientX - caja.left, e.clientY - caja.top);
      if (id) ultimas.current.onElegir(id);
    };
    canvas.addEventListener('pointermove', mover);
    canvas.addEventListener('pointerleave', salir);
    canvas.addEventListener('click', clic);
    const alCambiarTamano = () => pedir();
    addEventListener('resize', alCambiarTamano);

    // Mediciones (?medir), con la misma interfaz que el prototipo A.
    if (ultimas.current.medir) {
      const w = window as Window & { __armeria?: unknown };
      w.__armeria = {
        fotogramas: () => [...canal.current.fotogramas],
        gpu: () => {
          const ext = gl.getExtension('WEBGL_debug_renderer_info');
          return String(ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER));
        },
        dpr: () => canvas.width / Math.max(1, canvas.clientWidth),
        info: () => ({ llamadas: 1, texturas: UNIDADES.length }),
        luz: () => JSON.parse(JSON.stringify(canal.current.director?.luz ?? null)),
      };
    }

    Promise.all(UNIDADES.map(cargarPase))
      .then((imagenes) => {
        if (!vivo) return;
        imagenes.forEach((imagen, i) => {
          const pase = UNIDADES[i] as Pase;
          const datos = (PASES_DATOS as readonly string[]).includes(pase) && pase !== 'albedo';
          const textura = gl.createTexture();
          gl.activeTexture(gl.TEXTURE0 + i);
          gl.bindTexture(gl.TEXTURE_2D, textura);
          // Luz y albedo se guardaron en sRGB: la GPU los pasa a lineal al leerlos. Los datos, en bruto.
          gl.texImage2D(gl.TEXTURE_2D, 0, datos ? gl.RGBA8 : gl.SRGB8_ALPHA8, gl.RGBA, gl.UNSIGNED_BYTE, imagen);
          gl.generateMipmap(gl.TEXTURE_2D);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
          gl.uniform1i(u(UNIFORME_DE[pase]), i);
          imagen.close();
        });
        pedir();
      })
      .catch(() => ultimas.current.onLento());

    return () => {
      vivo = false;
      cancelAnimationFrame(cuadro);
      canvas.removeEventListener('pointermove', mover);
      canvas.removeEventListener('pointerleave', salir);
      canvas.removeEventListener('click', clic);
      removeEventListener('resize', alCambiarTamano);
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    };
  }, [canal]);

  // Cada cambio de la interfaz pide un fotograma.
  useEffect(() => {
    canal.current.pintar();
  }, [props.zonaActiva, props.zonaAbierta, props.movil, props.reducido, director, canal]);

  return <canvas ref={lienzo} className="armeria__canvas-b" />;
}
