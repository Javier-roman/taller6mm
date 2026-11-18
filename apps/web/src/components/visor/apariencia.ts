// Apariencia del visor: aplica a cada pieza el material de la biblioteca propia del pipeline
// (apps/pipeline/.../materiales, exportado por `exportar_visor.py` a `materiales-visor.json`) como
// MeshStandardMaterial de three.js. Es la misma receta que el render de la escalera (N3-N4), así que web y
// render comparten fuente: color RGB lineal, metalicidad, rugosidad media y variación, grano, asignación por
// familia y variación entre piezas por CRC32.
//
// Las mallas no llevan UV (nacen de generadores), así que la estructura del material se proyecta en caja
// (triplanar) sobre coordenadas de modelo en metros, como el render (no las del atributo: con la
// cuantización Meshopt son enteros normalizados, y la textura saldría a otra escala). De la base CC0 interna solo llegan dos mapas
// derivados a 512 px (rugosidad y normal): aportan ESTRUCTURA (variación de rugosidad y relieve); el color y
// el brillo medio los fija la receta. Nunca se publican ni se proyectan fotos de terceros.
//
// Desgaste (N4): el roce de las aristas con el metal pelado se deduce en pantalla de la variación de la
// normal (`fwidth`): sin datos extra en la malla, pero depende de la resolución (aproximación del prototipo;
// el render de Cycles lo hace con bordes biselados reales). La suciedad en cavidades (oclusión) aún no está.

import { COLOR_TOKENS } from '@taller6mm/ui/tokens';
import {
  Box3,
  Color,
  DataTexture,
  DoubleSide,
  EdgesGeometry,
  LinearSRGBColorSpace,
  LineDashedMaterial,
  LineSegments,
  type Material,
  type Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  NoColorSpace,
  type Object3D,
  RepeatWrapping,
  type Texture,
  TextureLoader,
  Vector2,
  Vector3,
} from 'three';
import type { ControlBrillo } from './iluminacion.ts';
import { type AsignacionVisor, BASE_VISOR, type MaterialesVisor, type MaterialVisor } from './modelos.ts';

// ───────────────────────────── Shader: triplanar + desgaste ─────────────────────────────

const PARS_FRAGMENTO = /* glsl */ `
varying vec3 vObjPos;
varying vec3 vObjNrm;
uniform mat3 normalMatrix;
uniform sampler2D uRug;
uniform sampler2D uNrm;
uniform float uEscala;
uniform vec3 uOffset;
uniform float uTexMedia;
uniform float uTexSigma;
uniform float uGanancia;
uniform float uRugBase;
uniform float uRugDelta;
uniform vec2 uRugBanda;
uniform float uGrano;
uniform float uNormEsc;
uniform float uColorVar;
uniform vec3 uDesgColor;
uniform float uDesgRug;
uniform float uDesgMet;
uniform float uDesgCant;
vec3 tPeso(vec3 n) {
  vec3 w = pow(abs(n), vec3(4.0));
  return w / (w.x + w.y + w.z + 1e-5);
}
float tRug(vec3 p, vec3 w, float k) {
  vec3 q = p * (k / uEscala) + uOffset;
  return texture2D(uRug, q.yz).g * w.x + texture2D(uRug, q.zx).g * w.y + texture2D(uRug, q.xy).g * w.z;
}
`;

const RUGOSIDAD = /* glsl */ `
vec3 wObj = tPeso(normalize(vObjNrm));
float rugZ = tRug(vObjPos, wObj, 1.0) - uTexMedia;
float roughnessFactor = clamp(uRugBase + rugZ * uGanancia + uRugDelta, uRugBanda.x, uRugBanda.y);
`;

const NORMAL_Y_DESGASTE = /* glsl */ `
diffuseColor.rgb *= uColorVar * (1.0 + rugZ * uGrano);
{
  vec3 q = vObjPos / uEscala + uOffset;
  vec3 tx = texture2D(uNrm, q.yz).xyz * 2.0 - 1.0;
  vec3 ty = texture2D(uNrm, q.zx).xyz * 2.0 - 1.0;
  vec3 tz = texture2D(uNrm, q.xy).xyz * 2.0 - 1.0;
  vec3 pert = vec3(0.0, tx.x, tx.y) * wObj.x + vec3(ty.y, 0.0, ty.x) * wObj.y + vec3(tz.x, tz.y, 0.0) * wObj.z;
  normal = normalize(normal + normalMatrix * pert * uNormEsc);
}
{
  float curv = length(fwidth(normal));
  float borde = smoothstep(0.05, 0.3, curv);
  float z = (tRug(vObjPos, wObj, 3.7) - uTexMedia) / max(uTexSigma, 1e-3);
  float rotura = smoothstep(-0.7, 0.9, z);
  float desg = clamp(borde * (0.35 + 0.65 * rotura) * uDesgCant, 0.0, 1.0);
  diffuseColor.rgb = mix(diffuseColor.rgb, uDesgColor, desg);
  metalnessFactor = mix(metalnessFactor, uDesgMet, desg);
  roughnessFactor = mix(roughnessFactor, uDesgRug, desg);
}
`;

type Uniformes = Record<string, { value: unknown }>;

/** Un material del visor, con lo necesario para reajustar su rugosidad cuando cambia la luz o el brillo. */
export interface MaterialVivo {
  id: string;
  material: MeshStandardMaterial;
  uniformes: Uniformes;
  /** Rugosidad media de la receta: la banda de rugosidad se centra aquí. */
  media: number;
  texturasListas: boolean;
}

export interface Pendiente {
  rol: string;
  centro: Vector3;
}

export interface Apariencia {
  vivos: MaterialVivo[];
  pendientes: Pendiente[];
  /** Fija el desplazamiento de rugosidad del preset y el brillo (la banda sale de los límites del catálogo). */
  ajustarLuz: (rugosidadDelta: number, brillo: number, control: ControlBrillo) => void;
  /** Libera lo que creó la apariencia (materiales y geometrías de los marcadores). */
  liberar: () => void;
}

// ───────────────────────────── Texturas ─────────────────────────────

const cacheTexturas = new Map<string, Promise<Texture>>();
const cargador = new TextureLoader();

function cargarTextura(ruta: string): Promise<Texture> {
  const url = `${BASE_VISOR}${ruta}`;
  let p = cacheTexturas.get(url);
  if (!p) {
    p = cargador.loadAsync(url).then((t) => {
      t.wrapS = t.wrapT = RepeatWrapping;
      t.colorSpace = NoColorSpace; // son datos (rugosidad y normal), no color
      t.anisotropy = 4;
      return t;
    });
    cacheTexturas.set(url, p);
  }
  return p;
}

function texturaPlana(r: number, g: number, b: number): DataTexture {
  const t = new DataTexture(new Uint8Array([r, g, b, 255]), 1, 1);
  t.wrapS = t.wrapT = RepeatWrapping;
  t.needsUpdate = true;
  return t;
}

// ───────────────────────────── Materiales ─────────────────────────────

const lineal = (c: readonly [number, number, number], k = 1) =>
  new Color().setRGB(c[0] * k, c[1] * k, c[2] * k, LinearSRGBColorSpace);

function crearMaterial(id: string, mat: MaterialVisor, asig: AsignacionVisor, alCargar: () => void): MaterialVivo {
  const tex = mat.texturas;
  const sigma = tex?.rug_desviacion ?? 0;
  const ganancia = tex && sigma > 0 ? Math.min(mat.rugosidad.variacion / sigma, 2.5) : 0;
  const s = asig.semilla;
  const dado = (i: number) => ((s >>> (i * 8)) & 0xff) / 255;
  const uniformes: Uniformes = {
    uRug: {
      value: texturaPlana(Math.round((tex?.rug_media ?? 0.5) * 255), Math.round((tex?.rug_media ?? 0.5) * 255), 0),
    },
    uNrm: { value: texturaPlana(128, 128, 255) },
    uEscala: { value: tex?.escala_m ?? 0.2 },
    uOffset: { value: new Vector3(dado(0) * 7, dado(1) * 7, dado(2) * 7) },
    uTexMedia: { value: tex?.rug_media ?? 0.5 },
    uTexSigma: { value: sigma || 0.05 },
    uGanancia: { value: ganancia },
    uRugBase: { value: mat.rugosidad.media + asig.variacion.rugosidad },
    uRugDelta: { value: 0 },
    uRugBanda: { value: new Vector2(0.02, 1) },
    uGrano: { value: Math.min(mat.grano.relieve * 2.5, 0.5) },
    uNormEsc: { value: Math.min(Math.max(mat.grano.relieve * 5, 0.25), 1) },
    uColorVar: { value: asig.variacion.color },
    uDesgColor: { value: lineal(mat.desgaste.color) },
    uDesgRug: { value: mat.desgaste.rugosidad },
    uDesgMet: { value: mat.desgaste.metalico },
    uDesgCant: { value: Math.min(mat.desgaste.cantidad * asig.variacion.desgaste, 1) },
  };
  const material = new MeshStandardMaterial({
    color: lineal(mat.color),
    metalness: mat.metalico,
    roughness: mat.rugosidad.media,
  });
  material.name = `mat.${id}`;
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniformes);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vObjPos;\nvarying vec3 vObjNrm;')
      .replace(
        '#include <begin_vertex>',
        '#include <begin_vertex>\nvObjPos = (modelMatrix * vec4(position, 1.0)).xyz;\nvObjNrm = normalize(mat3(modelMatrix) * normal);',
      );
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${PARS_FRAGMENTO}`)
      .replace('#include <roughnessmap_fragment>', RUGOSIDAD)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>\n${NORMAL_Y_DESGASTE}`);
  };
  material.customProgramCacheKey = () => 'visor-estructura-v1';
  const vivo: MaterialVivo = { id, material, uniformes, media: mat.rugosidad.media, texturasListas: false };
  if (tex) {
    const pend: Promise<void>[] = [
      cargarTextura(tex.rugosidad).then((t) => {
        (uniformes['uRug'] as { value: unknown }).value = t;
      }),
    ];
    if (tex.normal) {
      pend.push(
        cargarTextura(tex.normal).then((t) => {
          (uniformes['uNrm'] as { value: unknown }).value = t;
        }),
      );
    }
    void Promise.all(pend).then(() => {
      vivo.texturasListas = true;
      alCargar();
    });
  }
  return vivo;
}

// ───────────────────────────── Aplicación al modelo ─────────────────────────────

const esMarcador = (m: Mesh): boolean => {
  const mat = Array.isArray(m.material) ? m.material[0] : m.material;
  return mat?.name === 'mat.marcador';
};

/** Rol de la pieza al que pertenece una malla (extras del nodo glTF, que three deja en `userData`). */
export function rolDe(o: Object3D): string | null {
  for (let n: Object3D | null = o; n; n = n.parent) {
    const rol = n.userData?.['rol'];
    if (typeof rol === 'string') return rol;
  }
  return null;
}

/**
 * Sustituye los materiales del GLB por los de la biblioteca y los marcadores sin modelo por un fantasma
 * rayado. `claveDe(rol)` devuelve la clave de asignación de la pieza (`pieza` suelta o `montaje/pieza`).
 */
export function aplicarApariencia(
  objeto: Object3D,
  doc: MaterialesVisor,
  claveDe: (rol: string | null) => string | null,
  alCargar: () => void,
): Apariencia {
  const vivos = new Map<string, MaterialVivo>();
  const pendientes: Pendiente[] = [];
  const creados: { dispose: () => void }[] = [];
  const aviso = new Color(COLOR_TOKENS['estado-aviso'].hex);
  objeto.updateMatrixWorld(true);

  objeto.traverse((o) => {
    const m = o as Mesh;
    if (!m.isMesh) return;
    const rol = rolDe(m);
    if (esMarcador(m)) {
      m.material = new MeshBasicMaterial({
        color: aviso,
        transparent: true,
        opacity: 0.09,
        depthWrite: false,
        side: DoubleSide,
      });
      creados.push(m.material);
      m.castShadow = false;
      m.geometry.computeBoundingBox();
      const caja = m.geometry.boundingBox;
      if (caja) {
        const tam = caja.getSize(new Vector3());
        const paso = Math.max(tam.x, tam.y, tam.z) * 0.07;
        const borde = new EdgesGeometry(m.geometry, 15);
        const linea = new LineSegments(
          borde,
          new LineDashedMaterial({
            color: aviso,
            dashSize: paso,
            gapSize: paso * 0.7,
            depthWrite: false,
            transparent: true,
            opacity: 0.9,
          }),
        );
        linea.computeLineDistances();
        m.add(linea);
        creados.push(borde, linea.material as Material);
        // Centro en el espacio del modelo (la malla puede llevar su traslación en el nodo, no en los vértices).
        const mundo = new Box3().setFromObject(m);
        pendientes.push({
          rol: rol ?? 'pieza',
          centro: mundo.getCenter(new Vector3()).add(new Vector3(0, mundo.getSize(new Vector3()).y / 2, 0)),
        });
      }
      return;
    }
    const clave = claveDe(rol);
    const asig = clave ? doc.asignaciones[clave] : undefined;
    const mat = asig ? doc.materiales[asig.material] : undefined;
    if (!asig || !mat) return; // sin asignación: se deja el material del GLB y no se inventa otro
    const id = `${asig.material}@${clave}`;
    let vivo = vivos.get(id);
    if (!vivo) {
      vivo = crearMaterial(asig.material, mat, asig, alCargar);
      vivos.set(id, vivo);
    }
    m.material = vivo.material;
  });

  const lista = [...vivos.values()];
  return {
    vivos: lista,
    pendientes,
    ajustarLuz(rugosidadDelta, brillo, control) {
      const desplazamiento = rugosidadDelta + (1 - brillo) * control.rug_por_factor;
      for (const v of lista) {
        (v.uniformes['uRugDelta'] as { value: number }).value = desplazamiento;
        (v.uniformes['uRugBanda'] as { value: Vector2 }).value.set(
          Math.max(control.rugosidad_minima_absoluta, v.media - control.banda_rugosidad),
          v.media + control.banda_rugosidad,
        );
      }
    },
    liberar() {
      for (const v of lista) v.material.dispose();
      for (const c of creados) c.dispose();
    },
  };
}
