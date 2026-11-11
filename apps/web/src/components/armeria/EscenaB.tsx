// Prototipo B · 2,5D re-iluminable: WebGL2 a pelo (sin three.js) sobre los pases horneados de la
// misma sala. Un único shader suma los pases de luz con el nivel de cada grupo (lo decide el mismo
// director que en A), re-ilumina la zona activa, aplica la linterna sobre las normales y la
// profundidad, mueve la imagen con un parallax leve y termina con AgX, viñeta y grano.
// La cámara no se mueve: «abrir» una zona es un zoom 2D sobre la imagen (apertura simulada).
import { type RefObject, useEffect, useMemo, useRef } from 'react';
import { ANCHO_MINIMO_VISIBLE, ASPECTO_POSTER, ENCUADRE_POSTER, type Rect, rectZona, segmentoTubo } from './camara.ts';
import { type CanalEscena, crearVigia } from './canal.ts';
import { Director, type Iluminacion, VARIANTES, type Variante } from './director.ts';
import { compilar, GLSL_COMUN } from './glsl.ts';
import { cabenRecortes, crearModulos, type Modulos, sufijoRecorte } from './modulos.ts';
import { PASES_DATOS, PASES_LUZ, type Pase, PROFUNDIDAD, RUTA_PASES } from './pases.ts';
import { CONJUNTOS_MOVIL, conjuntoDe, recorteConjunto, VARIANTES_RECORTE } from './recortes.ts';
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
  onApuntar: (id: string | null) => void;
  onElegir: (id: string) => void;
  onListo: () => void;
  onIntroFin: () => void;
  onLento: () => void;
}

const FRAGMENTOS = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 salida;
uniform sampler2D uBase, uTuboI, uTuboC, uTuboD, uCalidas, uRotulos, uAlbedo, uNormal, uProf;
uniform vec2 uCentro, uVisible, uParallax, uLinterna, uResolucion;
uniform vec3 uTubos, uTubosLuz, uTinte, uFondo;
uniform float uAmbiente, uCalidasN, uRotulosN, uAcento, uExtra, uLinternaN, uTiempo, uTanFov, uAspecto;
uniform vec4 uRectActivo;
uniform int uFilaActiva;
uniform vec4 uSegmentos[3];

const float CERCA = ${PROFUNDIDAD.cerca.toFixed(4)};
const float LEJOS = ${PROFUNDIDAD.lejos.toFixed(4)};
${GLSL_COMUN}
vec3 posVista(vec2 uv, float d) {
  vec2 ndc = vec2(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0);
  return vec3(ndc.x * uTanFov * uAspecto * d, ndc.y * uTanFov * d, -d);
}
void main() {
  vec2 uv = uCentro + (vUv - 0.5) * uVisible;
  // Fuera de la imagen (tableta 4:3: sobra arriba y abajo) se pinta el fondo de la página.
  float dentro = smoothstep(0.0, 0.004, uv.y) * smoothstep(0.0, 0.004, 1.0 - uv.y);
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
    // Zona activa: lo que su fila de tubos sube sobre el reposo se aplica solo dentro de la zona (el cono
    // de luz de encima no se toca, que lavaba los rótulos) y su rótulo se enciende (critico-diseno).
    float m = rect(uv, uRectActivo, 0.012);
    vec3 fila = uFilaActiva == 0 ? tI : (uFilaActiva == 1 ? tC : tD);
    c += fila * uTinte * m * uExtra + rot * m * uAcento * 1.76;
  }
  c /= EXPO;
  if (uLinternaN > 0.001) {
    float d = mix(CERCA, LEJOS, texture(uProf, uv).r);
    vec3 p = posVista(uv, d);
    vec3 n = normalize(texture(uNormal, uv).xyz * 2.0 - 1.0);
    float cono = smoothstep(cos(0.22), cos(0.08), dot(normalize(p), normalize(posVista(uLinterna, 1.0))));
    float lambert = max(dot(n, normalize(-p)), 0.0);
    c += texture(uAlbedo, uv).rgb * lambert * cono * uLinternaN * 120.0 / (3.14159 * d * d) * vec3(1.0, 0.97, 0.92);
  }
  // Resplandor de los tubos (sustituye al bloom de A).
  vec2 q = uv * vec2(uAspecto, 1.0);
  for (int i = 0; i < 3; i++) {
    float nivel = i == 0 ? uTubosLuz.x : (i == 1 ? uTubosLuz.y : uTubosLuz.z);
    float dd = segmento(q, uSegmentos[i].xy * vec2(uAspecto, 1.0), uSegmentos[i].zw * vec2(uAspecto, 1.0));
    c += uTinte * nivel * resplandor(dd);
  }
  c = agx(c);
  vec2 v = (vUv - 0.5) * vec2(uResolucion.x / uResolucion.y, 1.0);
  c *= 1.0 - 0.62 * smoothstep(0.45, 1.25, length(v));
  float g = fract(sin(dot(gl_FragCoord.xy + uTiempo * 61.0, vec2(12.9898, 78.233))) * 43758.5453);
  c += (g - 0.5) * 0.05 * c;
  salida = vec4(mix(uFondo, aSrgb(clamp(c, 0.0, 1.0)), dentro), 1.0);
}`;

/** Rectángulos de las zonas sobre la imagen (uv 0–1, y hacia abajo). El banco va primero: está delante. */
const RECTS: { id: string; rect: Rect }[] = [...ZONAS]
  .sort((a, b) => (a.id === 'banco' ? -1 : b.id === 'banco' ? 1 : 0))
  .map((z) => ({ id: z.id, rect: rectZona(z, ENCUADRE_POSTER, ASPECTO_POSTER) }));

/** Tubos de cada estantería proyectados sobre la imagen (para su resplandor). */
const SEGMENTOS = ORDEN_ESTANTERIAS.map((e) => segmentoTubo(ESTANTERIAS[e].x));

/** «#0b0c0e» → [r, g, b] en 0–1 (sRGB, tal cual sale a pantalla). Negro si no es un hex válido. */
const srgb = (hex: string) =>
  /^#[0-9a-f]{6}$/i.test(hex) ? [1, 3, 5].map((i) => Number.parseInt(hex.slice(i, i + 2), 16) / 255) : [0, 0, 0];

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

async function cargarPase(pase: Pase) {
  const respuesta = await fetch(`${RUTA_PASES}/${pase}.webp`);
  if (!respuesta.ok) throw new Error(`Falta el pase ${pase}`);
  return createImageBitmap(await respuesta.blob(), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}

/** Zoom del encuadre móvil del B: quita la franja de suelo sin pasar de ~1 píxel de pase por píxel físico. */
const ZOOM_MOVIL = 1.22;

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
    // «Lista» solo con los pases subidos: hasta entonces se ve el póster (auditor-rendimiento).
    let texturas = false;
    let ultimoPuntero = 0;
    const vigia = crearVigia(30);
    let introAvisada = false;
    const estado = {
      centro: [0.5, 0.5],
      zoom: 1,
      parallax: [0, 0],
      puntero: [0, 0] as [number, number],
      linterna: [0.5, 0.5] as [number, number],
      dentro: false,
      apuntada: null as string | null,
      /** Última zona activa: su luz se apaga suave al salir, sin saltar. */
      iluminada: null as string | null,
      movimiento: 1,
      /** Recortes del móvil: posición suavizada del carrusel, subida de la zona abierta y resolución fina. */
      p: canal.current.progreso,
      sube: 0,
      fino: false,
    };
    const linternaPosible = matchMedia('(hover: hover) and (pointer: fine)').matches;
    const programa = compilar(gl, FRAGMENTOS);
    gl.useProgram(programa);
    const ubicaciones = new Map<string, WebGLUniformLocation | null>();
    const u = (nombre: string) => {
      if (!ubicaciones.has(nombre)) ubicaciones.set(nombre, gl.getUniformLocation(programa, nombre));
      return ubicaciones.get(nombre) ?? null;
    };
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(programa, 'aPos');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
    gl.uniform4fv(u('uSegmentos'), SEGMENTOS.flat());
    gl.uniform1f(u('uTanFov'), tanFov);
    gl.uniform1f(u('uAspecto'), ASPECTO_POSTER);
    // El fondo de la página (token --negro-pavonado), para lo que sobra fuera de la imagen.
    gl.uniform3fv(u('uFondo'), srgb(getComputedStyle(canvas).getPropertyValue('--negro-pavonado').trim()));

    /** Lo que el compositor de recortes necesita saber de las luces en este fotograma. */
    const entradaModulos = (luz: Iluminacion, variante: Variante, enIntro: boolean, ahora: number) => ({
      ancho: canvas.clientWidth,
      alto: canvas.clientHeight,
      progreso: estado.p,
      abierta: zonaPorId(ultimas.current.zonaAbierta),
      sube: estado.sube,
      iluminada: zonaPorId(estado.iluminada),
      luz,
      variante,
      enIntro,
      tinte: tinte(variante),
      // Los rótulos de zona y la marca comparten pase: la marca manda durante la intro.
      rotulos: enIntro ? Math.max(luz.rotulos, luz.marca * 0.8) : luz.rotulos,
      tiempo: (ahora / 1000) % 100,
    });

    // Móvil estrecho: cada módulo se pinta con su recorte horneado a 1 píxel de pase por píxel físico
    // (modulos.ts). En pantallas más anchas (tableta en vertical) un módulo a todo el ancho ampliaría su
    // recorte: ahí sigue la sala entera, como en escritorio.
    const densidad = window.devicePixelRatio || 1;
    const fondo = srgb(getComputedStyle(canvas).getPropertyValue('--negro-pavonado').trim());
    const zonaCentrada = () =>
      ZONAS[Math.round(Math.min(ZONAS.length - 1, Math.max(0, canal.current.progreso)))] as (typeof ZONAS)[number];
    const modulos: Modulos | null =
      ultimas.current.movil && cabenRecortes(canvas.clientWidth)
        ? crearModulos(gl, {
            fondo,
            sufijo: sufijoRecorte(canvas.clientWidth, densidad),
            alCargar: () => {
              if (!texturas && modulos?.lista(zonaCentrada())) {
                texturas = true;
                anterior = performance.now();
              }
              pedir();
            },
            alFallar: () => ultimas.current.onLento(),
          })
        : null;

    const tamano = () => {
      // Sala entera en móvil, 1,5: cada píxel de pase ya ocupa más de uno de pantalla. Con recortes, 1,5
      // mientras algo se mueve y hasta 3 en el fotograma de reposo, que es el que se mira.
      const tope = modulos ? (estado.fino ? 3 : 1.5) : ultimas.current.movil ? 1.5 : 2;
      const dpr = Math.min(densidad, tope);
      const w = Math.round(canvas.clientWidth * dpr);
      const h = Math.round(canvas.clientHeight * dpr);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    };

    /**
     * Ventana visible de la imagen (uv) para el aspecto de la pantalla y un zoom. Como el póster: llena la
     * pantalla (cover), pero fuera del móvil nunca recorta más que el margen de los lados: en 4:3 se ven
     * los tres cuerpos enteros y la ventana se sale de la imagen por arriba y por abajo.
     */
    const visible = (zoom: number) => {
      const aspecto = canvas.clientWidth / Math.max(1, canvas.clientHeight);
      const ancho = Math.min(1, aspecto / ASPECTO_POSTER);
      const w = ultimas.current.movil ? ancho : Math.max(ancho, ANCHO_MINIMO_VISIBLE);
      return [w / zoom, (w * ASPECTO_POSTER) / aspecto / zoom] as const;
    };
    const aImagen = (x: number, y: number) => {
      if (modulos) return modulos.aImagen(x / canvas.clientWidth, y / canvas.clientHeight);
      const [vw, vh] = visible(estado.zoom);
      return [
        (estado.centro[0] ?? 0.5) + (x / canvas.clientWidth - 0.5) * vw,
        (estado.centro[1] ?? 0.5) + (y / canvas.clientHeight - 0.5) * vh,
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
        // Con movimiento reducido el encuadre no viaja con el dedo: corta de zona a zona.
        const bruto = Math.min(ZONAS.length - 1, Math.max(0, canal.current.progreso));
        const progreso = p.reducido ? Math.round(bruto) : bruto;
        const i = Math.floor(progreso);
        const f = progreso - i;
        const a = centroDe(abierta?.id ?? ZONAS[i]?.id ?? 'banco');
        const b = abierta ? a : centroDe(ZONAS[Math.min(ZONAS.length - 1, i + 1)]?.id ?? 'banco');
        // En reposo se recorta el suelo vacío de abajo (franja bajo el banco, critico-diseno 05-11-2026): ventana
        // vertical fija entre el 10 % y el 92 % del pase. Los pases de 2560 px aguantan ese zoom en vertical.
        // Con una zona abierta, la zona sube al tercio superior: la hoja de abajo ocupa hasta el 45 %.
        const [, vh] = visible(ZOOM_MOVIL);
        const x = (a[0] ?? 0.5) + ((b[0] ?? 0.5) - (a[0] ?? 0.5)) * f;
        const y = abierta ? (a[1] ?? 0.5) + 0.2 * vh : 0.1 + vh / 2;
        return { centro: [x, y], zoom: ZOOM_MOVIL };
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
      if (!texturas) return;
      const bruto = (ahora - anterior) / 1000;
      const dt = Math.min(bruto, 1 / 20);
      anterior = ahora;
      const p = ultimas.current;
      const d = canal.current.director;
      if (!d) return;
      // Recortes: el carrusel manda (con movimiento reducido, corta de zona a zona). Mientras algo se
      // mueve se pinta a menos resolución.
      const progreso = Math.min(ZONAS.length - 1, Math.max(0, canal.current.progreso));
      const metaP = p.reducido ? Math.round(progreso) : progreso;
      const metaSube = p.zonaAbierta ? 1 : 0;
      if (modulos && (Math.abs(metaP - estado.p) + Math.abs(metaSube - estado.sube) > 1e-3 || !d.enReposo))
        estado.fino = false;
      tamano();
      const activa = zonaPorId(p.zonaActiva);
      const abierta = zonaPorId(p.zonaAbierta);
      const luz = d.actualizar(dt, {
        estanteriaActiva: activa?.estanteria ?? null,
        zonaActiva: Boolean(activa),
        linterna: linternaPosible && estado.dentro && !abierta,
      });

      if (activa) estado.iluminada = activa.id;
      const k = p.reducido ? 1 : 1 - Math.exp(-(p.movil ? 7 : 4.2) * dt);
      if (modulos) {
        estado.movimiento = Math.abs(metaP - estado.p) + Math.abs(metaSube - estado.sube);
        estado.p += (metaP - estado.p) * k;
        estado.sube += (metaSube - estado.sube) * k;
        modulos.pintar(entradaModulos(luz, d.variante, d.enIntro, ahora));
      } else {
        pintarSala(k, luz, d, ahora);
      }

      const f = canal.current.fotogramas;
      f.push(bruto);
      if (f.length > 240) f.shift();
      if (!listo) {
        listo = true;
        p.onListo();
      }
      if (!d.enIntro && !introAvisada) {
        introAvisada = true;
        p.onIntroFin();
      }
      // Caída al póster si no llega a 30 FPS (docs/02 §3.6). Con ?medir no cae: se mide tal cual.
      if (vigia(f, !d.enIntro && !p.medir, ahora)) p.onLento();
      // Con el puntero quieto, la linterna llega a su sitio en unos 300 ms: después, deja de pintar.
      const punteroReciente = estado.dentro && linternaPosible && ahora - ultimoPuntero < 400;
      const quieto = d.enReposo && estado.movimiento < 0.0005 && !punteroReciente;
      // Recortes: el último fotograma, ya en reposo, se repite a resolución fina.
      const afinar = Boolean(modulos) && quieto && !estado.fino;
      if (afinar) estado.fino = true;
      if (p.medir || !quieto || afinar) pedir();
    };

    /** La sala entera (escritorio, tableta y móvil ancho): un solo encuadre con zoom, parallax y linterna. */
    const pintarSala = (k: number, luz: Iluminacion, d: Director, ahora: number) => {
      const p = ultimas.current;
      const abierta = zonaPorId(p.zonaAbierta);
      // Encuadre: zoom y desplazamiento suaves (instantáneos con movimiento reducido).
      const meta = objetivo();
      estado.movimiento =
        Math.abs(meta.zoom - estado.zoom) +
        Math.abs((meta.centro[0] ?? 0) - (estado.centro[0] ?? 0)) +
        Math.abs((meta.centro[1] ?? 0) - (estado.centro[1] ?? 0));
      estado.zoom += (meta.zoom - estado.zoom) * k;
      const [vw, vh] = visible(estado.zoom);
      // Si la ventana es mayor que la imagen, la imagen va centrada.
      const limitar = (c: number, v: number) => (v >= 1 ? 0.5 : Math.min(1 - v / 2, Math.max(v / 2, c)));
      estado.centro = [
        limitar((estado.centro[0] ?? 0.5) + ((meta.centro[0] ?? 0.5) - (estado.centro[0] ?? 0.5)) * k, vw),
        limitar((estado.centro[1] ?? 0.5) + ((meta.centro[1] ?? 0.5) - (estado.centro[1] ?? 0.5)) * k, vh),
      ];
      // Parallax con el ratón (nunca con movimiento reducido ni con una zona abierta).
      const par = !p.reducido && !p.movil && !abierta ? estado.puntero : [0, 0];
      estado.parallax = [
        (estado.parallax[0] ?? 0) + (-(par[0] ?? 0) * 0.004 - (estado.parallax[0] ?? 0)) * k,
        (estado.parallax[1] ?? 0) + ((par[1] ?? 0) * 0.0025 - (estado.parallax[1] ?? 0)) * k,
      ];

      gl.uniform2f(u('uCentro'), estado.centro[0] ?? 0.5, estado.centro[1] ?? 0.5);
      gl.uniform2f(u('uVisible'), vw, vh);
      gl.uniform2f(u('uParallax'), estado.parallax[0] ?? 0, estado.parallax[1] ?? 0);
      gl.uniform2f(u('uResolucion'), canvas.width, canvas.height);
      // La fila de la zona activa (o de la última, mientras se apaga) no pasa del reposo en toda la imagen:
      // lo que sube de ahí solo se ve dentro de la zona.
      const iluminada = zonaPorId(estado.iluminada);
      const tope = VARIANTES[d.variante].reposo;
      const niveles = ORDEN_ESTANTERIAS.map((e) => luz.tubos[e]);
      const fila = iluminada && !d.enIntro ? ORDEN_ESTANTERIAS.indexOf(iluminada.estanteria) : -1;
      const extra = fila >= 0 ? Math.max(0, (niveles[fila] ?? 0) - tope) : 0;
      if (fila >= 0) niveles[fila] = Math.min(niveles[fila] ?? 0, tope);
      gl.uniform3f(u('uTubos'), niveles[0] ?? 0, niveles[1] ?? 0, niveles[2] ?? 0);
      gl.uniform3f(u('uTubosLuz'), luz.tubos.izquierda, luz.tubos.centro, luz.tubos.derecha);
      gl.uniform1f(u('uExtra'), extra);
      gl.uniform3fv(u('uTinte'), tinte(d.variante));
      gl.uniform1f(u('uAmbiente'), luz.ambiente);
      gl.uniform1f(u('uCalidasN'), luz.calidas);
      // Los rótulos de zona y la marca comparten pase: la marca manda durante la intro.
      gl.uniform1f(u('uRotulosN'), d.enIntro ? Math.max(luz.rotulos, luz.marca * 0.8) : luz.rotulos);
      const r = iluminada ? RECTS.find((z) => z.id === iluminada.id)?.rect : undefined;
      gl.uniform4f(u('uRectActivo'), r?.x ?? 0, r?.y ?? 0, r?.ancho ?? 0, r?.alto ?? 0);
      gl.uniform1i(u('uFilaActiva'), fila);
      gl.uniform1f(u('uAcento'), luz.acento);
      gl.uniform2f(u('uLinterna'), estado.linterna[0], estado.linterna[1]);
      gl.uniform1f(u('uLinternaN'), luz.linterna);
      gl.uniform1f(u('uTiempo'), (ahora / 1000) % 100);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
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
      ultimoPuntero = performance.now();
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
        info: () => ({ llamadas: 1, texturas: UNIDADES.length, recortes: Boolean(modulos) }),
        /**
         * Póster de un conjunto de recortes: la composición en reposo, sin zona activa, viñeta ni grano, al
         * tamaño del recorte y en las variantes del srcset (scripts/prototipos/recortes-movil.mjs).
         */
        componer: async (id: string, calidad = 0.82) => {
          const conjunto = CONJUNTOS_MOVIL.find((c) => c.id === id);
          const zona = ZONAS.find((z) => conjuntoDe(z.id) === conjunto);
          const d = canal.current.director;
          if (!modulos || !conjunto || !zona || !d) return null;
          modulos.pedir(conjunto);
          for (let i = 0; i < 600 && !modulos.lista(zona); i++) await new Promise((r) => requestAnimationFrame(r));
          const v = VARIANTES[d.variante];
          const reposo: Iluminacion = {
            tubos: { izquierda: v.reposo, centro: v.reposo, derecha: v.reposo },
            calidas: v.calidas,
            ambiente: v.ambiente,
            rotulos: 1,
            marca: 1,
            acento: 0,
            linterna: 0,
          };
          const [ancho, alto] = recorteConjunto(conjunto).px;
          canvas.width = ancho;
          canvas.height = alto;
          gl.viewport(0, 0, ancho, alto);
          if (!modulos.componer(conjunto, entradaModulos(reposo, d.variante, false, 0))) return null;
          const salidas = VARIANTES_RECORTE.map(({ sufijo, escala }) => {
            const c = document.createElement('canvas');
            c.width = Math.round(ancho * escala);
            c.height = Math.round(alto * escala);
            c.getContext('2d')?.drawImage(canvas, 0, 0, c.width, c.height);
            return { sufijo, ancho: c.width, url: c.toDataURL('image/webp', calidad) };
          });
          pedir();
          return salidas;
        },
        luz: () => JSON.parse(JSON.stringify(canal.current.director?.luz ?? null)),
        progreso: () => canal.current.progreso,
      };
    }

    // Sin puntero fino no hay linterna ni parallax: los pases de datos sobran (auditor-rendimiento:
    // −382 kB y −32 MiB de GPU). En su lugar, texturas de 1 × 1 neutras (sin albedo, normal al frente y
    // profundidad al fondo, que anula el parallax).
    const NEUTROS: Partial<Record<Pase, readonly number[]>> = {
      albedo: [0, 0, 0, 255],
      normal: [128, 128, 255, 255],
      profundidad: [255, 255, 255, 255],
    };
    const descargar = (pase: Pase) => (linternaPosible || !NEUTROS[pase] ? cargarPase(pase) : Promise.resolve(null));
    // Con recortes solo se pide el conjunto de la zona centrada; los vecinos, al pintar.
    const conjuntoInicial = modulos ? conjuntoDe(zonaCentrada().id) : null;
    if (modulos && conjuntoInicial) modulos.pedir(conjuntoInicial);
    Promise.all(modulos ? [] : UNIDADES.map(descargar))
      .then((imagenes) => {
        if (!vivo) return;
        imagenes.forEach((imagen, i) => {
          const pase = UNIDADES[i] as Pase;
          const datos = (PASES_DATOS as readonly string[]).includes(pase) && pase !== 'albedo';
          const textura = gl.createTexture();
          gl.activeTexture(gl.TEXTURE0 + i);
          gl.bindTexture(gl.TEXTURE_2D, textura);
          // Luz y albedo se guardaron en sRGB: la GPU los pasa a lineal al leerlos. Los datos, en bruto.
          const formato = datos ? gl.RGBA8 : gl.SRGB8_ALPHA8;
          if (imagen) gl.texImage2D(gl.TEXTURE_2D, 0, formato, gl.RGBA, gl.UNSIGNED_BYTE, imagen);
          else
            gl.texImage2D(
              gl.TEXTURE_2D,
              0,
              formato,
              1,
              1,
              0,
              gl.RGBA,
              gl.UNSIGNED_BYTE,
              new Uint8Array(NEUTROS[pase] ?? [0, 0, 0, 255]),
            );
          gl.generateMipmap(gl.TEXTURE_2D);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
          gl.uniform1i(u(UNIFORME_DE[pase]), i);
          imagen?.close();
        });
        if (modulos) return;
        texturas = true;
        anterior = performance.now();
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
      modulos?.liberar();
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    };
  }, [canal, props.movil]);

  // Cada cambio de la interfaz pide un fotograma.
  useEffect(() => {
    canal.current.pintar();
  }, [props.zonaActiva, props.zonaAbierta, props.movil, props.reducido, director, canal]);

  return <canvas ref={lienzo} className="armeria__canvas-b" />;
}
