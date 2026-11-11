// GLSL común a los dos sombreadores del prototipo B (la sala entera y los recortes por módulo del móvil):
// vértices, exposición del horno, AgX, sRGB y las máscaras de zona y de tubo. Sin three.js.
import { EXPOSICION_HORNO } from './pases.ts';

export const VERTICES = `#version 300 es
in vec2 aPos;
out vec2 vUv;
void main() {
  vUv = vec2(aPos.x * 0.5 + 0.5, 0.5 - aPos.y * 0.5);
  gl_Position = vec4(aPos, 0.0, 1.0);
}`;

export const GLSL_COMUN = `
const float EXPO = ${EXPOSICION_HORNO.toFixed(4)};

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
// Resplandor de un tubo (sustituye al bloom de A): un núcleo fino y un halo ancho.
float resplandor(float d) {
  return exp(-d * d / 0.000012) * 1.6 + exp(-d * d / 0.0011) * 0.22;
}
`;

/** Compila y enlaza un programa con el triángulo de pantalla completa (`aPos` en la posición 0). */
export function compilar(gl: WebGL2RenderingContext, fragmentos: string) {
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
  gl.attachShader(programa, shader(gl.FRAGMENT_SHADER, fragmentos));
  gl.bindAttribLocation(programa, 0, 'aPos');
  gl.linkProgram(programa);
  if (!gl.getProgramParameter(programa, gl.LINK_STATUS))
    throw new Error(gl.getProgramInfoLog(programa) ?? 'Programa inválido');
  return programa;
}
