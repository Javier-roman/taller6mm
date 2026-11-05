// Efectos de penumbra de La Armería (Javi, 04-11-2026): haces de luz bajo los tubos y reflejo del
// suelo pulido. Solo para el render en tiempo real (prototipo A): al hornear con Cycles se excluyen
// (`userData.soloTiempoReal`) porque allí los haces salen del volumen y los reflejos del trazado.
import {
  AdditiveBlending,
  type Color,
  CylinderGeometry,
  DoubleSide,
  Mesh,
  PlaneGeometry,
  Quaternion,
  ShaderMaterial,
  Vector3,
} from 'three';

/** Cono de luz falsa: brillo en el eje y junto al tubo, nada en los bordes ni al llegar al suelo. */
export function crearHaz(
  origen: Vector3,
  objetivo: Vector3,
  color: Color,
  largo = 3.3,
): Mesh<CylinderGeometry, ShaderMaterial> {
  const material = new ShaderMaterial({
    uniforms: { uColor: { value: color.clone() }, uIntensidad: { value: 0 } },
    vertexShader: /* glsl */ `
      varying vec3 vNormal;
      varying vec3 vVista;
      varying float vAltura;
      void main() {
        vAltura = uv.y;
        vec4 p = modelViewMatrix * vec4(position, 1.0);
        vVista = -p.xyz;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * p;
      }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uColor;
      uniform float uIntensidad;
      varying vec3 vNormal;
      varying vec3 vVista;
      varying float vAltura;
      void main() {
        float eje = pow(clamp(abs(dot(normalize(vNormal), normalize(vVista))), 0.0, 1.0), 2.2);
        // clamp: la interpolación puede dar -1e-17 y pow() de un negativo es NaN (el bloom lo extiende a toda la pantalla).
        float h = clamp(vAltura, 0.0, 1.0);
        // Brilla junto al tubo y queda en un velo tenue a la altura de rótulos y réplicas: no las lava.
        float caida = mix(0.22, 1.0, smoothstep(0.84, 1.0, h)) * smoothstep(0.0, 0.18, h);
        float a = uIntensidad * eje * caida;
        gl_FragColor = vec4(uColor * a, a);
      }`,
    transparent: true,
    depthWrite: false,
    blending: AdditiveBlending,
    side: DoubleSide,
  });
  const geometria = new CylinderGeometry(0.1, 1.45, largo, 32, 1, true);
  const haz = new Mesh(geometria, material);
  const direccion = objetivo.clone().sub(origen).normalize();
  haz.quaternion.copy(new Quaternion().setFromUnitVectors(new Vector3(0, -1, 0), direccion));
  haz.position.copy(origen).addScaledVector(direccion, largo / 2);
  haz.renderOrder = 10;
  haz.userData['soloTiempoReal'] = true;
  return haz;
}

/** Nivel y color de un haz (lo llama la sala en cada fotograma). */
export function ajustarHaz(
  haz: Mesh<CylinderGeometry | PlaneGeometry, ShaderMaterial>,
  intensidad: number,
  color: Color,
) {
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
