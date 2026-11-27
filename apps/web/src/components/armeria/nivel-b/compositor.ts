// Compositor del nivel B (2,5D re-iluminable): WebGL2 a pelo, sin three.js, sobre los pases horneados de la
// sala. Un único shader suma los pases de luz con el nivel de cada grupo (lo decide el director), re-ilumina
// la zona activa, aplica la linterna sobre las normales y la profundidad, mueve la imagen con un parallax leve
// y termina con AgX, viñeta y grano. No sabe nada de React ni del DOM salvo el contexto que se le da: lo usan
// EscenaB (la escena interactiva) y el script del póster, que componen exactamente lo mismo.
import { ANCHO_MINIMO_VISIBLE, ASPECTO_POSTER, ENCUADRE_POSTER, segmentoTubo } from '../camara.ts';
import { compilar, GLSL_COMUN } from '../glsl.ts';
import { GANANCIA_BASE, PASES_DATOS, PASES_LUZ, type Pase, PROFUNDIDAD } from '../pases.ts';
import { ESTANTERIAS, ORDEN_ESTANTERIAS } from '../zonas.ts';

export type V2 = readonly [number, number];
export type V3 = readonly [number, number, number];
export type V4 = readonly [number, number, number, number];

/** Todo lo que cambia de un fotograma a otro. La imagen es la misma: solo cambian estos números. */
export interface ParametrosPintado {
  /** Centro y tamaño de la ventana visible sobre la imagen (uv 0–1, y hacia abajo). */
  centro: V2;
  visible: V2;
  parallax: V2;
  /** Punto de la linterna sobre la imagen (uv) y su nivel (0 = apagada). */
  linterna: V2;
  linternaNivel: number;
  /** Tamaño del lienzo en píxeles (para la viñeta). */
  resolucion: V2;
  /** Nivel con el que se suma cada fila de tubos (izquierda, centro, derecha) y su resplandor. */
  tubos: V3;
  tubosResplandor: V3;
  /** Razón de color de los tubos frente a los pases horneados (1,1,1 si no cambia). */
  tinte: V3;
  ambiente: number;
  calidas: number;
  rotulos: number;
  /** Zona activa: su rectángulo (uv), su fila de tubos (−1 = ninguna) y cuánto sube su fila y su rótulo. */
  rectActivo: V4;
  filaActiva: number;
  extra: number;
  acento: number;
  tiempo: number;
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
const float GANANCIA_BASE = ${GANANCIA_BASE.toFixed(4)};
${GLSL_COMUN}
vec3 posVista(vec2 uv, float d) {
  vec2 ndc = vec2(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0);
  return vec3(ndc.x * uTanFov * uAspecto * d, ndc.y * uTanFov * d, -d);
}
void main() {
  vec2 uv = uCentro + (vUv - 0.5) * uVisible;
  // Fuera de la imagen (pantalla más estrecha que 16:9: sobra arriba y abajo) se pinta el fondo de la página.
  float dentro = smoothstep(0.0, 0.004, uv.y) * smoothstep(0.0, 0.004, 1.0 - uv.y);
  uv += uParallax * (1.0 - texture(uProf, uv).r);
  vec3 tI = texture(uTuboI, uv).rgb;
  vec3 tC = texture(uTuboC, uv).rgb;
  vec3 tD = texture(uTuboD, uv).rgb;
  vec3 rot = texture(uRotulos, uv).rgb;
  vec3 c = texture(uBase, uv).rgb * uAmbiente * GANANCIA_BASE
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
  // Resplandor de los tubos (sustituye al bloom del nivel A).
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

const UNIDADES: readonly Pase[] = [...PASES_LUZ, ...PASES_DATOS];
const UNIFORME_DE: Readonly<Record<Pase, string>> = {
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

/**
 * Sin puntero fino no hay linterna ni parallax y los pases de datos sobran: en su lugar, texturas de 1 × 1
 * neutras (sin albedo, normal al frente y profundidad al fondo, que anula el parallax).
 */
const NEUTROS: Partial<Record<Pase, readonly number[]>> = {
  albedo: [0, 0, 0, 255],
  normal: [128, 128, 255, 255],
  profundidad: [255, 255, 255, 255],
};
export const PASES_NEUTRALIZABLES: readonly Pase[] = Object.keys(NEUTROS) as Pase[];

/** «#0b0c0e» → [r, g, b] en 0–1 (sRGB, tal cual sale a pantalla). Negro si no es un hex válido. */
export const srgb = (hex: string): V3 => {
  if (!/^#[0-9a-f]{6}$/i.test(hex)) return [0, 0, 0];
  const c = (i: number) => Number.parseInt(hex.slice(i, i + 2), 16) / 255;
  return [c(1), c(3), c(5)];
};

const lineal = (hex: string): V3 => {
  const [r, g, b] = srgb(hex);
  const f = (c: number) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return [f(r), f(g), f(b)];
};

/** Razón de color de unos tubos frente a los de los pases horneados (los dos en hex). */
export function razonDeColor(destino: string, base: string): V3 {
  const a = lineal(base);
  const b = lineal(destino);
  return [b[0] / (a[0] || 1), b[1] / (a[1] || 1), b[2] / (a[2] || 1)];
}

/**
 * Ventana visible de la imagen (uv) para el aspecto de la pantalla y un zoom: llena la pantalla (como
 * `cover`), pero nunca recorta más que el margen de los lados, así que en 4:3 se ven los tres cuerpos
 * enteros y la ventana se sale de la imagen por arriba y por abajo.
 */
export function ventanaVisible(ancho: number, alto: number, zoom = 1): V2 {
  const aspecto = ancho / Math.max(1, alto);
  const w = Math.max(Math.min(1, aspecto / ASPECTO_POSTER), ANCHO_MINIMO_VISIBLE);
  return [w / zoom, (w * ASPECTO_POSTER) / aspecto / zoom];
}

const TAN_FOV = Math.tan((ENCUADRE_POSTER.fov * Math.PI) / 360);
const SEGMENTOS = ORDEN_ESTANTERIAS.map((e) => segmentoTubo(ESTANTERIAS[e].x));

export interface Compositor {
  /** Sube los pases (los que falten, o `null`, quedan como textura neutra). Cierra cada ImageBitmap. */
  subir(imagenes: Partial<Record<Pase, ImageBitmap | null>>): void;
  pintar(p: ParametrosPintado): void;
  liberar(): void;
}

/** El compositor sobre un contexto WebGL2; `fondo` es el color de la página (token) para lo que sobra. */
export function crearCompositor(gl: WebGL2RenderingContext, fondo: V3): Compositor {
  const programa = compilar(gl, FRAGMENTOS);
  gl.useProgram(programa);
  const ubicaciones = new Map<string, WebGLUniformLocation | null>();
  const u = (nombre: string) => {
    if (!ubicaciones.has(nombre)) ubicaciones.set(nombre, gl.getUniformLocation(programa, nombre));
    return ubicaciones.get(nombre) ?? null;
  };
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  // Un triángulo que cubre la pantalla.
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(programa, 'aPos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
  gl.uniform4fv(u('uSegmentos'), SEGMENTOS.flat());
  gl.uniform1f(u('uTanFov'), TAN_FOV);
  gl.uniform1f(u('uAspecto'), ASPECTO_POSTER);
  gl.uniform3fv(u('uFondo'), [...fondo]);
  const texturas: WebGLTexture[] = [];

  return {
    subir(imagenes) {
      UNIDADES.forEach((pase, i) => {
        const imagen = imagenes[pase] ?? null;
        const textura = gl.createTexture();
        gl.activeTexture(gl.TEXTURE0 + i);
        gl.bindTexture(gl.TEXTURE_2D, textura);
        // Luz y albedo se guardaron en sRGB: la GPU los pasa a lineal al leerlos. Los datos, en bruto.
        const datos = (PASES_DATOS as readonly Pase[]).includes(pase) && pase !== 'albedo';
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
        if (textura) texturas.push(textura);
        imagen?.close();
      });
    },
    pintar(p) {
      gl.uniform2f(u('uCentro'), ...p.centro);
      gl.uniform2f(u('uVisible'), ...p.visible);
      gl.uniform2f(u('uParallax'), ...p.parallax);
      gl.uniform2f(u('uResolucion'), ...p.resolucion);
      gl.uniform3f(u('uTubos'), ...p.tubos);
      gl.uniform3f(u('uTubosLuz'), ...p.tubosResplandor);
      gl.uniform3f(u('uTinte'), ...p.tinte);
      gl.uniform1f(u('uAmbiente'), p.ambiente);
      gl.uniform1f(u('uCalidasN'), p.calidas);
      gl.uniform1f(u('uRotulosN'), p.rotulos);
      gl.uniform4f(u('uRectActivo'), ...p.rectActivo);
      gl.uniform1i(u('uFilaActiva'), p.filaActiva);
      gl.uniform1f(u('uExtra'), p.extra);
      gl.uniform1f(u('uAcento'), p.acento);
      gl.uniform2f(u('uLinterna'), ...p.linterna);
      gl.uniform1f(u('uLinternaN'), p.linternaNivel);
      gl.uniform1f(u('uTiempo'), p.tiempo);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    },
    liberar() {
      for (const t of texturas) gl.deleteTexture(t);
      texturas.length = 0;
      gl.deleteProgram(programa);
      gl.deleteBuffer(buffer);
    },
  };
}

/** Descarga un pase como ImageBitmap sin tocar su color (la conversión la hace la textura sRGB). */
export async function descargarPase(url: string): Promise<ImageBitmap> {
  const respuesta = await fetch(url);
  if (!respuesta.ok) throw new Error(`Falta la vista ${url} (${respuesta.status})`);
  return createImageBitmap(await respuesta.blob(), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}
