// Director de luces de La Armería: TS puro (sin three.js ni DOM), compartido por el prototipo A
// (luces reales) y el B (pases horneados). Decide, fotograma a fotograma, el nivel de cada grupo de
// luz: intro de los tubos, encendido al pasar por un módulo, linterna y acento.
//
// Seguridad ante destellos (WCAG 2.3.1): nunca más de 3 destellos por segundo. Cada tubo solo hace
// un parpadeo (subida, bajada y subida = 1,5 destellos), los tubos de la intro van separados
// 0,8 s y el parpadeo al pasar el ratón se limita a uno cada 1,2 s; el resto son rampas suaves.
// Con movimiento reducido no hay intro ni parpadeos.
import { type Estanteria, ORDEN_ESTANTERIAS } from './zonas.ts';

export type Variante = 'penumbra' | 'taller';

export interface Iluminacion {
  /** Nivel de cada fila de tubos (0–1, puede pasar un poco de 1 en el arranque). */
  tubos: Record<Estanteria, number>;
  /** Flexo del banco y luz de la vitrina. */
  calidas: number;
  ambiente: number;
  /** Emisión de los rótulos de zona (el activo se multiplica aparte). */
  rotulos: number;
  /** Rótulo de la marca en la cabecera central: se «estampa» al final de la intro. */
  marca: number;
  /** Foco de acento sobre la zona activa. */
  acento: number;
  linterna: number;
}

export const VARIANTES: Readonly<
  Record<
    Variante,
    {
      readonly nombre: string;
      readonly reposo: number;
      readonly foco: number;
      readonly resto: number;
      readonly calidas: number;
      readonly ambiente: number;
      /** Color de los tubos (hex): frío tipo ref-08 o cálido de taller. */
      readonly colorTubo: string;
    }
  >
> = {
  penumbra: {
    nombre: 'Penumbra fría (ref-08)',
    reposo: 0.46,
    foco: 1,
    resto: 0.32,
    calidas: 1,
    ambiente: 1,
    colorTubo: '#dfe9ff',
  },
  taller: {
    nombre: 'Taller abierto (cálida)',
    reposo: 0.95,
    foco: 1.1,
    resto: 0.78,
    calidas: 1.4,
    ambiente: 2.4,
    colorTubo: '#ffd6a0',
  },
};

export const crearIluminacion = (nivel = 1): Iluminacion => ({
  tubos: { izquierda: nivel, centro: nivel, derecha: nivel },
  calidas: nivel,
  ambiente: nivel,
  rotulos: nivel,
  marca: nivel,
  acento: 0,
  linterna: 0,
});

/** Momentos de la intro (s). Dura 2,9 s: el máximo de docs/02 §3.2 es 3 s. */
export const INTRO = {
  inicioTubos: 0.35,
  separacion: 0.8,
  calidas: 2.3,
  rotulos: 2.35,
  marca: 2.5,
  fin: 2.9,
} as const;

const suave = (x: number) => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};

/** Arranque de un tubo fluorescente: destello, apagón y rampa hasta `nivel`. `t` en s desde el inicio. */
export function curvaArranque(t: number, desde: number, nivel: number) {
  // Desde apagado, el valle es casi negro; desde la penumbra, solo baja a la mitad.
  const valle = desde > 0.05 ? desde * 0.55 : 0.05;
  if (t < 0) return desde;
  if (t < 0.07) return Math.max(desde, nivel * 0.92);
  if (t < 0.3) return valle;
  return valle + (nivel - valle) * suave((t - 0.3) / 0.2);
}

export interface EntradaDirector {
  /** Estantería de la zona activa (hover, foco de teclado o la centrada en móvil). */
  estanteriaActiva: Estanteria | null;
  zonaActiva: boolean;
  /** El puntero está sobre la escena en un dispositivo con ratón. */
  linterna: boolean;
}

export class Director {
  private t = 0;
  private introHasta: number;
  private readonly base: Record<Estanteria, number>;
  private readonly arranque: Record<Estanteria, number | null> = { izquierda: null, centro: null, derecha: null };
  private ultimoParpadeo = -10;
  private anterior: Estanteria | null = null;
  readonly luz: Iluminacion = crearIluminacion(0);

  constructor(private readonly opciones: { intro: boolean; reducido: boolean; variante: Variante }) {
    const v = VARIANTES[opciones.variante];
    const intro = opciones.intro && !opciones.reducido;
    this.introHasta = intro ? INTRO.fin : 0;
    this.base = { izquierda: v.reposo, centro: v.reposo, derecha: v.reposo };
    if (!intro) Object.assign(this.luz, this.reposo());
  }

  get variante() {
    return this.opciones.variante;
  }

  /** 0 → 1 durante la intro; 1 cuando ha terminado o se ha saltado. */
  get progresoIntro() {
    return this.introHasta === 0 ? 1 : Math.min(1, this.t / this.introHasta);
  }

  get enIntro() {
    return this.t < this.introHasta;
  }

  /** ¿Hay algo moviéndose? Si no, la escena puede dejar de pintar (ahorra GPU y batería). */
  get enReposo() {
    return !this.enIntro && ORDEN_ESTANTERIAS.every((e) => this.arranque[e] === null) && this.convergido;
  }

  private convergido = false;

  saltarIntro() {
    if (!this.enIntro) return;
    this.introHasta = 0;
    Object.assign(this.luz, this.reposo());
  }

  private reposo(): Iluminacion {
    const v = VARIANTES[this.opciones.variante];
    return {
      tubos: { izquierda: v.reposo, centro: v.reposo, derecha: v.reposo },
      calidas: v.calidas,
      ambiente: v.ambiente,
      rotulos: 1,
      marca: 1,
      acento: 0,
      linterna: 0,
    };
  }

  actualizar(dt: number, entrada: EntradaDirector): Iluminacion {
    this.t += dt;
    const v = VARIANTES[this.opciones.variante];
    const luz = this.luz;

    if (this.enIntro) {
      const t = this.t;
      ORDEN_ESTANTERIAS.forEach((e, i) => {
        const t0 = INTRO.inicioTubos + i * INTRO.separacion;
        luz.tubos[e] = t < t0 ? 0 : curvaArranque(t - t0, 0, v.reposo);
      });
      luz.ambiente = v.ambiente * suave((t - INTRO.inicioTubos) / (INTRO.calidas - INTRO.inicioTubos));
      luz.calidas = v.calidas * suave((t - INTRO.calidas) / 0.3);
      luz.rotulos = suave((t - INTRO.rotulos) / 0.25);
      // El estampado del logo: un solo golpe de luz que se asienta (1 destello).
      const m = t - INTRO.marca;
      luz.marca = m < 0 ? 0 : m < 0.08 ? 1.8 : 1 + 0.8 * Math.max(0, 1 - (m - 0.08) / 0.25);
      luz.acento = 0;
      luz.linterna = 0;
      return luz;
    }

    const activa = entrada.estanteriaActiva;
    const k = 1 - Math.exp(-5 * dt);
    let movimiento = 0;
    for (const e of ORDEN_ESTANTERIAS) {
      const objetivo = activa === null ? v.reposo : e === activa ? v.foco : v.resto;
      const antes = this.base[e];
      this.base[e] = antes + (objetivo - antes) * k;
      movimiento += Math.abs(objetivo - this.base[e]);
    }
    // Parpadeo de arranque al llegar a otra estantería, como mucho uno cada 1,2 s.
    if (activa !== this.anterior) {
      if (activa && !this.opciones.reducido && this.t - this.ultimoParpadeo > 1.2) {
        this.arranque[activa] = this.t;
        this.ultimoParpadeo = this.t;
      }
      this.anterior = activa;
    }
    for (const e of ORDEN_ESTANTERIAS) {
      const t0 = this.arranque[e];
      if (t0 !== null && this.t - t0 > 0.5) this.arranque[e] = null;
      const inicio = this.arranque[e];
      luz.tubos[e] = inicio === null ? this.base[e] : curvaArranque(this.t - inicio, v.resto, this.base[e]);
    }
    const acercar = (actual: number, objetivo: number) => {
      const nuevo = actual + (objetivo - actual) * k;
      movimiento += Math.abs(objetivo - nuevo);
      return nuevo;
    };
    luz.calidas = acercar(luz.calidas, v.calidas);
    luz.ambiente = acercar(luz.ambiente, v.ambiente);
    luz.rotulos = acercar(luz.rotulos, 1);
    luz.marca = acercar(luz.marca, 1);
    luz.acento = acercar(luz.acento, entrada.zonaActiva ? 1 : 0);
    luz.linterna = acercar(luz.linterna, entrada.linterna ? 1 : 0);
    this.convergido = movimiento < 0.004;
    return luz;
  }
}
