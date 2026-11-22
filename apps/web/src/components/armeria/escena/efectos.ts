// Efectos de penumbra de La Armería (Javi, 04-11-2026): reflejo del suelo pulido. Sin haces de luz visibles
// (Javi, 11-11-2026: parecían de videojuego; la luz es indirecta). Solo para el render en tiempo real (nivel A):
// al hornear con Cycles se excluyen (`userData.soloTiempoReal`) porque allí los reflejos salen del trazado.
import { AdditiveBlending, type Color, Mesh, PlaneGeometry, ShaderMaterial } from 'three';

/** Nivel y color de un reflejo (lo llama la sala en cada fotograma). */
export function ajustarReflejo(haz: Mesh<PlaneGeometry, ShaderMaterial>, intensidad: number, color: Color) {
  // En los pases de datos del horno (albedo, normales) los materiales se sustituyen y no hay uniforms.
  const u = (haz.material as Partial<ShaderMaterial>).uniforms;
  if (!u) return;
  if (u['uIntensidad']) u['uIntensidad'].value = intensidad;
  if (u['uColor']) (u['uColor'].value as Color).copy(color);
}

/**
 * Reflejo falso en el suelo pulido: una franja aditiva y difuminada bajo una fuente de luz (tubos o
 * flexo), estirada hacia el espectador como en el hormigón brillante. Sin render extra: un espejo de
 * verdad (Reflector) repintaba la escena entera en cada fotograma y colgaba el postprocesado.
 */
export function crearReflejoFalso(ancho: number, largo: number, color: Color): Mesh<PlaneGeometry, ShaderMaterial> {
  const material = new ShaderMaterial({
    uniforms: { uColor: { value: color.clone() }, uIntensidad: { value: 0 } },
    vertexShader: /* glsl */ `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uColor;
      uniform float uIntensidad;
      varying vec2 vUv;
      void main() {
        // Campana en el ancho y caída hacia el espectador.
        float x = (vUv.x - 0.5) * 2.0;
        float ancho = exp(-x * x * 4.5);
        // Tras girar el plano, v = 0 queda junto a la fuente: brilla al pie del mueble y se apaga hacia el espectador.
        float largo = pow(clamp(1.0 - vUv.y, 0.0, 1.0), 2.2);
        float a = uIntensidad * ancho * largo;
        gl_FragColor = vec4(uColor * a, a);
      }`,
    transparent: true,
    depthWrite: false,
    blending: AdditiveBlending,
  });
  const plano = new Mesh(new PlaneGeometry(ancho, largo), material);
  plano.rotation.x = -Math.PI / 2;
  plano.renderOrder = 9;
  plano.userData['soloTiempoReal'] = true;
  return plano;
}
