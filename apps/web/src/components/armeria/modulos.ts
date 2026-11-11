// Prototipo B en móvil: compositor de los recortes por módulo (recortes.ts). El pase único de la sala se
// veía borroso ampliado en un móvil de 3× (critico-diseno, 2.ª revisión); aquí cada módulo se pinta con su
// recorte horneado a 1 píxel de pase por píxel físico, nunca ampliado. Al deslizar entre módulos de
// conjuntos distintos, una vista empuja a la otra; dentro de un conjunto, el encuadre se desplaza.
// WebGL2 a pelo, como EscenaB: ocho texturas (cuatro pases por vista), sin pases de datos.
import {
  ASPECTO_POSTER,
  ENCUADRE_POSTER,
  MOVIL_REFERENCIA,
  type Rect,
  rectZona,
  segmentoTubo,
  ventanaZona,
} from './camara.ts';
import { type Iluminacion, VARIANTES, type Variante } from './director.ts';
import { compilar, GLSL_COMUN } from './glsl.ts';
import {
  CONJUNTOS_MOVIL,
  type ConjuntoMovil,
  conjuntoDe,
  PASES_RECORTE,
  paseHorneado,
  recorteConjunto,
  rutaRecorte,
  VARIANTES_RECORTE,
} from './recortes.ts';
import { ESTANTERIAS, ZONAS, type Zona } from './zonas.ts';

const FRAGMENTOS = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 salida;
uniform sampler2D uBaseA, uTuboA, uCalidasA, uRotulosA, uBaseB, uTuboB, uCalidasB, uRotulosB;
// Por vista (A y, al deslizar, B): ventana del encuadre que se ve, recorte que cubre su textura, zona
// iluminada, tubo de su fila y luz (nivel de la fila, extra en la zona, acento del rótulo, nivel del tubo).
uniform vec4 uVenA, uVenB, uRecA, uRecB, uZonaA, uZonaB, uSegA, uSegB, uLuzA, uLuzB;
uniform vec3 uTinte, uFondo;
uniform vec2 uResolucion;
uniform float uDesliz, uAmbiente, uCalidasN, uRotulosN, uTiempo, uAspecto, uPlano;
${GLSL_COMUN}
void main() {
  float s = vUv.x + uDesliz;
  bool b = s >= 1.0;
  vec2 p = vec2(b ? s - 1.0 : s, vUv.y);
  vec4 ven = b ? uVenB : uVenA;
  vec4 rec = b ? uRecB : uRecA;
  vec4 zona = b ? uZonaB : uZonaA;
  vec4 seg = b ? uSegB : uSegA;
  vec4 luz = b ? uLuzB : uLuzA;
  vec2 uv = ven.xy + p * ven.zw;
  vec2 t = (uv - rec.xy) / max(rec.zw, vec2(1e-6));
  vec3 base, tubo, calidas, rot;
  // textureLod: dentro de una rama no hay derivadas, y los recortes no llevan mipmaps (van a 1:1 o reducidos).
  if (b) {
    base = textureLod(uBaseB, t, 0.0).rgb;
    tubo = textureLod(uTuboB, t, 0.0).rgb;
    calidas = textureLod(uCalidasB, t, 0.0).rgb;
    rot = textureLod(uRotulosB, t, 0.0).rgb;
  } else {
    base = textureLod(uBaseA, t, 0.0).rgb;
    tubo = textureLod(uTuboA, t, 0.0).rgb;
    calidas = textureLod(uCalidasA, t, 0.0).rgb;
    rot = textureLod(uRotulosA, t, 0.0).rgb;
  }
  // Como en la sala entera: lo que la fila sube sobre el reposo solo se ve dentro de la zona activa.
  float m = zona.z > 0.0 ? rect(uv, zona, 0.012) : 0.0;
  vec3 c = base * uAmbiente
    + tubo * uTinte * (luz.x + luz.y * m)
    + calidas * uCalidasN
    + rot * (uRotulosN + luz.z * m * 1.76);
  c /= EXPO;
  vec2 q = vec2(uAspecto, 1.0);
  c += uTinte * luz.w * resplandor(segmento(uv * q, seg.xy * q, seg.zw * q));
  c = agx(c);
  if (uPlano < 0.5) {
    vec2 v = (vUv - 0.5) * vec2(uResolucion.x / uResolucion.y, 1.0);
    c *= 1.0 - 0.62 * smoothstep(0.45, 1.25, length(v));
    float g = fract(sin(dot(gl_FragCoord.xy + uTiempo * 61.0, vec2(12.9898, 78.233))) * 43758.5453);
    c += (g - 0.5) * 0.05 * c;
  }
  // Fuera del recorte (o si aún no ha cargado) se pinta el fondo de la página.
  float dentro = rec.z > 0.0
    ? step(0.0, t.x) * step(t.x, 1.0) * smoothstep(0.0, 0.002, t.y) * smoothstep(0.0, 0.002, 1.0 - t.y)
    : 0.0;
  salida = vec4(mix(uFondo, aSrgb(clamp(c, 0.0, 1.0)), dentro), 1.0);
}`;

/** Como mucho, tres conjuntos en la GPU: el que se ve y sus vecinos (el mayor ocupa unos 65 MB a 3×). */
const MAXIMO_EN_GPU = 3;

const RECORTES = new Map(CONJUNTOS_MOVIL.map((c) => [c.id, recorteConjunto(c)]));
const ZONAS_EN_POSTER = new Map(ZONAS.map((z) => [z.id, rectZona(z, ENCUADRE_POSTER, ASPECTO_POSTER)]));

/**
 * ¿La pantalla es lo bastante estrecha para que un módulo a todo el ancho no amplíe su recorte? Hasta el
 * ancho del móvil de referencia (el lienzo no pasa de 3×); el póster usa el mismo corte en CSS.
 */
export const cabenRecortes = (anchoCss: number) => anchoCss <= MOVIL_REFERENCIA.ancho;

/** Variante de los pases para una pantalla, como un srcset: la menor que no se amplía. */
export function sufijoRecorte(anchoCss: number, densidad: number) {
  const fisicos = anchoCss * Math.min(densidad, MOVIL_REFERENCIA.densidad);
  const entero = MOVIL_REFERENCIA.ancho * MOVIL_REFERENCIA.densidad;
  return (VARIANTES_RECORTE.find((v) => fisicos <= entero * v.escala) ?? { sufijo: '' }).sufijo;
}

export interface EntradaModulos {
  /** Tamaño de la pantalla en px CSS. */
  ancho: number;
  alto: number;
  /** Posición del carrusel en zonas (admite decimales mientras se desliza). */
  progreso: number;
  abierta: Zona | null;
  /** 0–1: con una zona abierta, sube al tercio superior (la hoja de abajo ocupa hasta el 45 %). */
  sube: number;
  /** Zona iluminada (la centrada o la última, mientras se apaga). */
  iluminada: Zona | null;
  luz: Iluminacion;
  variante: Variante;
  enIntro: boolean;
  tinte: readonly number[];
  rotulos: number;
  tiempo: number;
}

interface Carga {
  texturas: (WebGLTexture | null)[] | null;
  uso: number;
}

export function crearModulos(
  gl: WebGL2RenderingContext,
  opciones: { fondo: readonly number[]; sufijo: string; alCargar: () => void; alFallar: () => void },
) {
  const programa = compilar(gl, FRAGMENTOS);
  gl.useProgram(programa);
  const ubicaciones = new Map<string, WebGLUniformLocation | null>();
  const u = (nombre: string) => {
    if (!ubicaciones.has(nombre)) ubicaciones.set(nombre, gl.getUniformLocation(programa, nombre));
    return ubicaciones.get(nombre) ?? null;
  };
  (['A', 'B'] as const).forEach((vista, i) => {
    PASES_RECORTE.forEach((pase, k) => {
      gl.uniform1i(u(`u${pase[0]?.toUpperCase()}${pase.slice(1)}${vista}`), i * PASES_RECORTE.length + k);
    });
  });
  gl.uniform1f(u('uAspecto'), ASPECTO_POSTER);
  gl.uniform3fv(u('uFondo'), opciones.fondo);
  const UNIDAD_DE_CARGA = 2 * PASES_RECORTE.length;

  const textura = (fuente: ImageBitmap | null) => {
    const t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + UNIDAD_DE_CARGA);
    gl.bindTexture(gl.TEXTURE_2D, t);
    // Los pases de luz se guardaron en sRGB: la GPU los pasa a lineal al leerlos.
    if (fuente) gl.texImage2D(gl.TEXTURE_2D, 0, gl.SRGB8_ALPHA8, gl.RGBA, gl.UNSIGNED_BYTE, fuente);
    else
      gl.texImage2D(
        gl.TEXTURE_2D,
        0,
        gl.SRGB8_ALPHA8,
        1,
        1,
        0,
        gl.RGBA,
        gl.UNSIGNED_BYTE,
        new Uint8Array([0, 0, 0, 255]),
      );
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t;
  };
  const negra = textura(null);

  let vivo = true;
  let avisado = false;
  let reloj = 0;
  const cargas = new Map<string, Carga>();
  const descargar = async (ruta: string) => {
    const respuesta = await fetch(ruta);
    if (!respuesta.ok) throw new Error(`Falta ${ruta}`);
    return createImageBitmap(await respuesta.blob(), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
  };
  const soltar = (id: string) => {
    for (const t of cargas.get(id)?.texturas ?? []) gl.deleteTexture(t);
    cargas.delete(id);
  };
  /** Conjuntos que no se pudieron descargar: no se reintentan en cada fotograma. */
  const fallidos = new Set<string>();
  /**
   * Pide un conjunto si no está; si no cabe, suelta el que lleva más tiempo sin verse (salvo los protegidos).
   * Si falla uno que hace falta para pintar, se avisa (la escena cae al póster); si era un vecino, se espera
   * a que haga falta.
   */
  const pedir = (conjunto: ConjuntoMovil | null, protegidos: ReadonlySet<string>, necesario: boolean) => {
    if (!conjunto) return;
    if (fallidos.has(conjunto.id)) {
      if (necesario && !avisado) {
        avisado = true;
        opciones.alFallar();
      }
      return;
    }
    const ya = cargas.get(conjunto.id);
    if (ya) {
      ya.uso = ++reloj;
      return;
    }
    if (cargas.size >= MAXIMO_EN_GPU) {
      const viejo = [...cargas].filter(([id]) => !protegidos.has(id)).sort((a, b) => a[1].uso - b[1].uso)[0];
      if (!viejo) return;
      soltar(viejo[0]);
    }
    const carga: Carga = { texturas: null, uso: ++reloj };
    cargas.set(conjunto.id, carga);
    Promise.all(
      PASES_RECORTE.map((pase) => {
        const nombre = paseHorneado(conjunto, pase);
        return nombre ? descargar(rutaRecorte(conjunto, nombre, opciones.sufijo)) : null;
      }),
    )
      .then((imagenes) => {
        if (vivo && cargas.get(conjunto.id) === carga) {
          carga.texturas = imagenes.map((imagen) => (imagen ? textura(imagen) : null));
          opciones.alCargar();
        }
        for (const imagen of imagenes) imagen?.close();
      })
      .catch(() => {
        if (cargas.get(conjunto.id) === carga) cargas.delete(conjunto.id);
        fallidos.add(conjunto.id);
        if (!vivo) return;
        if (necesario && !avisado) {
          avisado = true;
          opciones.alFallar();
        } else opciones.alCargar();
      });
  };

  /** Lo último pintado, para saber qué zona hay bajo un toque. */
  let vista = { a: { x: 0, y: 0, ancho: 1, alto: 1 } as Rect, b: { x: 0, y: 0, ancho: 1, alto: 1 } as Rect, desliz: 0 };

  const enviar = (
    letra: 'A' | 'B',
    unidad: number,
    conjunto: ConjuntoMovil | null,
    ventana: Rect,
    e: EntradaModulos,
  ) => {
    const texturas = conjunto ? cargas.get(conjunto.id)?.texturas : null;
    const recorte = conjunto && texturas ? RECORTES.get(conjunto.id) : undefined;
    PASES_RECORTE.forEach((_, k) => {
      gl.activeTexture(gl.TEXTURE0 + unidad + k);
      gl.bindTexture(gl.TEXTURE_2D, texturas?.[k] ?? negra);
    });
    gl.uniform4f(u(`uVen${letra}`), ventana.x, ventana.y, ventana.ancho, ventana.alto);
    gl.uniform4f(u(`uRec${letra}`), recorte?.x ?? 0, recorte?.y ?? 0, recorte?.ancho ?? 0, recorte?.alto ?? 0);
    if (!conjunto) return;
    const nivel = e.luz.tubos[conjunto.fila];
    const iluminada = e.enIntro ? null : e.iluminada;
    // La fila de la zona iluminada no pasa del reposo fuera de ella.
    const reposo = iluminada?.estanteria === conjunto.fila ? Math.min(nivel, VARIANTES[e.variante].reposo) : nivel;
    const zona = iluminada && conjunto.zonas.includes(iluminada.id) ? ZONAS_EN_POSTER.get(iluminada.id) : undefined;
    gl.uniform4f(u(`uZona${letra}`), zona?.x ?? 0, zona?.y ?? 0, zona?.ancho ?? 0, zona?.alto ?? 0);
    gl.uniform4f(u(`uLuz${letra}`), reposo, zona ? nivel - reposo : 0, zona ? e.luz.acento : 0, nivel);
    gl.uniform4fv(u(`uSeg${letra}`), segmentoTubo(ESTANTERIAS[conjunto.fila].x));
  };

  const comunes = (e: EntradaModulos, plano: boolean) => {
    gl.uniform2f(u('uResolucion'), gl.drawingBufferWidth, gl.drawingBufferHeight);
    gl.uniform3fv(u('uTinte'), e.tinte);
    gl.uniform1f(u('uAmbiente'), e.luz.ambiente);
    gl.uniform1f(u('uCalidasN'), e.luz.calidas);
    gl.uniform1f(u('uRotulosN'), e.rotulos);
    gl.uniform1f(u('uTiempo'), e.tiempo);
    gl.uniform1f(u('uPlano'), plano ? 1 : 0);
  };

  return {
    /** ¿Está en la GPU el conjunto de esta zona? */
    lista: (zona: Zona | undefined) => Boolean(zona && cargas.get(conjuntoDe(zona.id)?.id ?? '')?.texturas),

    pintar(e: EntradaModulos) {
      // A menos de dos milésimas de una zona, es esa zona: el carrusel en reposo nunca da un entero exacto.
      const progreso = Math.abs(e.progreso - Math.round(e.progreso)) < 0.002 ? Math.round(e.progreso) : e.progreso;
      const i = Math.min(ZONAS.length - 1, Math.max(0, Math.floor(progreso)));
      const za = e.abierta ?? (ZONAS[i] as Zona);
      const zb = e.abierta ?? ZONAS[i + 1] ?? za;
      const ca = conjuntoDe(za.id);
      const cb = conjuntoDe(zb.id);
      const ventana = (zona: Zona): Rect => {
        const v = ventanaZona(zona, e.ancho, e.alto);
        return { ...v, y: v.y + e.sube * 0.2 * v.alto };
      };
      let a = ventana(za);
      const b = ventana(zb);
      let desliz = za === zb ? 0 : Math.min(1, Math.max(0, progreso - i));
      if (ca === cb) {
        // Mismo recorte: el encuadre se desplaza de una zona a la otra.
        const mezcla = (p: number, q: number) => p + (q - p) * desliz;
        a = { x: mezcla(a.x, b.x), y: mezcla(a.y, b.y), ancho: mezcla(a.ancho, b.ancho), alto: mezcla(a.alto, b.alto) };
        desliz = 0;
      }
      vista = { a, b, desliz };
      // Lo que se ve, y después los vecinos del carrusel, para que el siguiente deslizamiento no espere.
      const protegidos = new Set([ca?.id ?? '', cb?.id ?? '']);
      pedir(ca, protegidos, true);
      pedir(cb, protegidos, desliz > 0);
      for (const vecina of [ZONAS[i - 1], ZONAS[i + 2]]) {
        const conjunto = vecina ? conjuntoDe(vecina.id) : null;
        if (conjunto && (cargas.has(conjunto.id) || cargas.size < MAXIMO_EN_GPU)) pedir(conjunto, protegidos, false);
      }
      gl.useProgram(programa);
      comunes(e, false);
      gl.uniform1f(u('uDesliz'), desliz);
      enviar('A', 0, ca, a, e);
      enviar('B', PASES_RECORTE.length, cb, b, e);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    },

    /**
     * Pinta un conjunto entero, sin zona iluminada, viñeta ni grano: de ahí salen los pósteres del móvil
     * (scripts/prototipos/recortes-movil.mjs). El lienzo debe tener ya el tamaño del recorte.
     */
    componer(conjunto: ConjuntoMovil, e: EntradaModulos) {
      const recorte = RECORTES.get(conjunto.id);
      if (!recorte || !cargas.get(conjunto.id)?.texturas) return false;
      gl.useProgram(programa);
      comunes(e, true);
      gl.uniform1f(u('uDesliz'), 0);
      enviar('A', 0, conjunto, recorte, { ...e, iluminada: null });
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      return true;
    },

    /** Pide un conjunto fuera del orden del carrusel (para componer su póster). */
    pedir: (conjunto: ConjuntoMovil) => pedir(conjunto, new Set([conjunto.id]), true),

    /** Punto del encuadre del póster (uv) bajo un punto de la pantalla (0–1). */
    aImagen(nx: number, ny: number) {
      const s = nx + vista.desliz;
      const v = s >= 1 ? vista.b : vista.a;
      return [v.x + (s >= 1 ? s - 1 : s) * v.ancho, v.y + ny * v.alto] as const;
    },

    liberar() {
      vivo = false;
      for (const id of [...cargas.keys()]) soltar(id);
    },
  };
}

export type Modulos = ReturnType<typeof crearModulos>;
