// La Armería (inicio, Fase 1 · prototipos A y B): tres estanterías —izquierda, centro y derecha—
// cuyas zonas llevan a cada función de la web (dirección de Javi, 01-11-2026, sobre docs/02 §3.1).
// Como en ref-08, son tres cuerpos de compactus casi pegados sobre raíles que vienen hacia el
// espectador. Unidades de escena en metros (docs/05 §4). Los datos de los rótulos son de EJEMPLO
// (demo): no hay catálogo hasta la Fase 2, y la interfaz lo dice.

export type Estanteria = 'izquierda' | 'centro' | 'derecha';

export interface Zona {
  readonly id: string;
  /** Nombre del módulo (docs/02 §3.1). */
  readonly nombre: string;
  /** Texto del rótulo a plantilla. */
  readonly rotulo: string;
  /** Dato vivo del rótulo. En los prototipos, de ejemplo. */
  readonly dato: string;
  /** Qué encontrarás dentro (panel del prototipo y texto alternativo). */
  readonly descripcion: string;
  readonly ruta: string;
  readonly estanteria: Estanteria;
  /** Caja de la zona en la escena: centro [x, y, z] y tamaño [ancho, alto, fondo] en metros. */
  readonly caja: {
    readonly centro: readonly [number, number, number];
    readonly tamano: readonly [number, number, number];
  };
  /** Dónde cuelga su rótulo [x, y, z]. */
  readonly anclaRotulo: readonly [number, number, number];
  /** Fase del roadmap en la que llega la sección (docs/10). */
  readonly fase: number;
}

/** Medidas comunes de las estanterías (m). */
export const MUEBLE = { ancho: 2.7, alto: 2.72, fondo: 0.6, frente: -1.75, baldaMedia: 1.28, zocalo: 0.12 } as const;

/** Centro en x de cada estantería, su rótulo de cabecera y su número de cuerpo (ref-08). */
export const ESTANTERIAS: Readonly<
  Record<Estanteria, { readonly x: number; readonly titulo: string; readonly numero: string }>
> = {
  izquierda: { x: -2.78, titulo: 'Catálogo', numero: '01' },
  centro: { x: 0, titulo: 'Taller', numero: '02' },
  derecha: { x: 2.78, titulo: 'Mercado', numero: '03' },
};

export const ORDEN_ESTANTERIAS: readonly Estanteria[] = ['izquierda', 'centro', 'derecha'];

/** Banco de trabajo, delante de la estantería central. */
export const BANCO = { x: 0, z: -0.55, ancho: 2.25, fondo: 0.9, alto: 0.93 } as const;

const zFondo = MUEBLE.frente - MUEBLE.fondo / 2;
const zRotulo = MUEBLE.frente + 0.012;
const arriba = { y: (MUEBLE.baldaMedia + MUEBLE.alto) / 2, alto: MUEBLE.alto - MUEBLE.baldaMedia };
const abajo = { y: (MUEBLE.zocalo + MUEBLE.baldaMedia) / 2, alto: MUEBLE.baldaMedia - MUEBLE.zocalo };
// Los rótulos cuelgan de lo alto de su compartimento, como las tiras numeradas de ref-08.
const yRotuloArriba = MUEBLE.alto - 0.16;
const yRotuloAbajo = MUEBLE.baldaMedia - 0.16;

const izq = ESTANTERIAS.izquierda.x;
const der = ESTANTERIAS.derecha.x;
const mitad = MUEBLE.ancho / 4; // centro de cada compartimento de la estantería derecha (2 × 2)

export const ZONAS: readonly Zona[] = [
  {
    id: 'replicas',
    nombre: 'Armero de réplicas',
    rotulo: 'Armero',
    dato: '24 réplicas',
    descripcion: 'Ranuras numeradas con cada réplica del catálogo, en vertical y a escala.',
    ruta: '/replicas',
    estanteria: 'izquierda',
    caja: { centro: [izq, arriba.y, zFondo], tamano: [2.6, arriba.alto, MUEBLE.fondo] },
    anclaRotulo: [izq, yRotuloArriba, zRotulo],
    fase: 2,
  },
  {
    id: 'accesorios',
    nombre: 'Almacén de accesorios',
    rotulo: 'Accesorios',
    dato: '186 accesorios · 8 tiendas',
    descripcion: 'Maletines y cajas etiquetadas con todos los accesorios del mercado.',
    ruta: '/accesorios',
    estanteria: 'izquierda',
    caja: { centro: [izq, abajo.y, zFondo], tamano: [2.6, abajo.alto, MUEBLE.fondo] },
    anclaRotulo: [izq, yRotuloAbajo, zRotulo],
    fase: 2,
  },
  {
    id: 'comunidad',
    nombre: 'Vitrina de la comunidad',
    rotulo: 'Vitrina',
    dato: 'Top de la semana',
    descripcion: 'Las tres builds más valoradas de la semana, bajo cristal.',
    ruta: '/comunidad',
    estanteria: 'centro',
    caja: { centro: [0, arriba.y, zFondo], tamano: [2.6, arriba.alto, MUEBLE.fondo] },
    anclaRotulo: [0, yRotuloArriba, zRotulo],
    fase: 5,
  },
  {
    id: 'banco',
    nombre: 'Banco de trabajo',
    rotulo: 'Banco de trabajo',
    dato: 'Monta tu réplica',
    descripcion: 'El configurador: elige tu réplica y móntala pieza a pieza, con medidas reales.',
    ruta: '/banco',
    estanteria: 'centro',
    caja: { centro: [BANCO.x, 0.68, BANCO.z], tamano: [BANCO.ancho, 1.36, BANCO.fondo + 0.05] },
    anclaRotulo: [BANCO.x, BANCO.alto - 0.12, BANCO.z + BANCO.fondo / 2 + 0.035],
    fase: 3,
  },
  {
    id: 'mercado',
    nombre: 'Tablón de mercado',
    rotulo: 'Tablón',
    dato: '3 bajadas hoy',
    descripcion: 'Bajadas de precio y vueltas a stock, con la hora de cada comprobación.',
    ruta: '/mercado',
    estanteria: 'derecha',
    caja: { centro: [der - mitad, arriba.y, zFondo], tamano: [1.3, arriba.alto, MUEBLE.fondo] },
    anclaRotulo: [der - mitad, yRotuloArriba, zRotulo],
    fase: 4,
  },
  {
    id: 'guias',
    nombre: 'Biblioteca de manuales',
    rotulo: 'Manuales',
    dato: '12 guías',
    descripcion: 'Guías de montaje, despieces y normativa de airsoft en España.',
    ruta: '/guias',
    estanteria: 'derecha',
    caja: { centro: [der - mitad, abajo.y, zFondo], tamano: [1.3, abajo.alto, MUEBLE.fondo] },
    anclaRotulo: [der - mitad, yRotuloAbajo, zRotulo],
    fase: 2,
  },
  {
    id: 'tiendas',
    nombre: 'Mostrador de tiendas',
    rotulo: 'Tiendas',
    dato: '8 tiendas · hace 2 h',
    descripcion: 'Las tiendas de España y del extranjero que seguimos, y la frescura de sus datos.',
    ruta: '/tiendas',
    estanteria: 'derecha',
    caja: { centro: [der + mitad, arriba.y, zFondo], tamano: [1.3, arriba.alto, MUEBLE.fondo] },
    anclaRotulo: [der + mitad, yRotuloArriba, zRotulo],
    fase: 4,
  },
  {
    id: 'taquilla',
    nombre: 'Taquilla personal',
    rotulo: 'Taquilla',
    dato: 'Tus builds y alertas',
    descripcion: 'Tus builds guardadas, favoritos y alertas de precio.',
    ruta: '/taquilla',
    estanteria: 'derecha',
    caja: { centro: [der + mitad, abajo.y, zFondo], tamano: [1.3, abajo.alto, MUEBLE.fondo] },
    anclaRotulo: [der + mitad, yRotuloAbajo, zRotulo],
    fase: 5,
  },
];

export const zonaPorId = (id: string | null | undefined) => ZONAS.find((zona) => zona.id === id) ?? null;

export const zonasDe = (estanteria: Estanteria) => ZONAS.filter((zona) => zona.estanteria === estanteria);
