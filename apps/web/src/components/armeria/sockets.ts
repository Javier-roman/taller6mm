// Sockets de réplica de La Armería: los puntos de anclaje donde irán las imágenes reales de cada réplica.
// Hasta que haya réplicas reales (frente de fidelidad, otro trabajo) la sala NO pinta siluetas de relleno
// (Javi, 22-11-2026: «quedan terriblemente mal»): las baldas, ranuras y peanas quedan vacías pero resueltas, y
// cada hueco está definido aquí, en metros de la escena, con el tamaño máximo que puede ocupar una réplica.
// De esta caja salen (a) el rectángulo del hueco sobre el póster y el nivel B (CSS generado), y (b) la posición
// del marcador del nivel A. Cuando exista la imagen de una réplica, basta con poner su `replicaId` aquí y
// pintarla dentro de ese rectángulo, sin tocar la sala ni volver a hornear nada.
import type { V3 } from './camara.ts';
import { BANCO, ESTANTERIAS, type Estanteria, MUEBLE } from './zonas.ts';

export type OrientacionSocket = 'vertical' | 'horizontal';

export interface Socket {
  readonly id: string;
  /** Zona de La Armería a la que pertenece. */
  readonly zona: 'replicas' | 'comunidad' | 'banco';
  readonly estanteria: Estanteria;
  /** Caja del hueco: centro y tamaño máximo (m, ancho × alto × fondo) que puede ocupar una réplica. */
  readonly caja: { readonly centro: V3; readonly tamano: V3 };
  /** Cómo se coloca la réplica: de pie en el armero, tumbada en la vitrina y sobre el tapete del banco. */
  readonly orientacion: OrientacionSocket;
  /** Réplica del catálogo que ocupa el hueco; `null` = vacío (no hay imagen real todavía). */
  readonly replicaId: string | null;
}

const zFondo = MUEBLE.frente - MUEBLE.fondo / 2;

/** Ranuras del armero (12 por cuerpo, como las de ref-08) y su geometría, compartidas con la sala. */
export const ARMERO = {
  huecos: 12,
  util: MUEBLE.ancho - 0.2,
  /** Alto máximo de una réplica de pie (m): la más larga habitual, con su culata en la balda. */
  alto: 1.1,
} as const;

/** Peanas de la vitrina: x en el cuerpo central y altura de cada peana (la tercera, la más alta). */
export const VITRINA = {
  xs: [-0.78, 0, 0.78],
  y0: MUEBLE.baldaMedia + 0.02,
  largo: 0.82,
} as const;

/** Altura de la cara superior de la peana `i` de la vitrina. */
export const alturaPeana = (i: number) => VITRINA.y0 + 0.1 + 0.14 + i * 0.06;

const armero: Socket[] = Array.from({ length: ARMERO.huecos }, (_, i) => {
  const paso = ARMERO.util / ARMERO.huecos;
  return {
    id: `armero-${String(i + 1).padStart(2, '0')}`,
    zona: 'replicas',
    estanteria: 'izquierda',
    caja: {
      centro: [
        ESTANTERIAS.izquierda.x - ARMERO.util / 2 + (i + 0.5) * paso,
        MUEBLE.baldaMedia + 0.03 + ARMERO.alto / 2,
        zFondo + 0.04,
      ],
      tamano: [paso * 0.9, ARMERO.alto, 0.3],
    },
    orientacion: 'vertical',
    replicaId: null,
  };
});

const vitrina: Socket[] = VITRINA.xs.map((x, i) => ({
  id: `vitrina-${i + 1}`,
  zona: 'comunidad',
  estanteria: 'centro',
  caja: {
    centro: [ESTANTERIAS.centro.x + x, alturaPeana(i) + 0.11, zFondo + 0.04],
    tamano: [VITRINA.largo, 0.22, 0.3],
  },
  orientacion: 'horizontal',
  replicaId: null,
}));

/** Sobre el tapete del banco, la réplica «a medio montar» del usuario. */
const banco: Socket[] = [
  {
    id: 'banco-1',
    zona: 'banco',
    estanteria: 'centro',
    caja: { centro: [BANCO.x - 0.2, BANCO.alto + 0.07, BANCO.z + 0.04], tamano: [1.0, 0.14, 0.26] },
    orientacion: 'horizontal',
    replicaId: null,
  },
];

export const SOCKETS: readonly Socket[] = [...armero, ...vitrina, ...banco];

export const socketsDe = (zona: Socket['zona']) => SOCKETS.filter((s) => s.zona === zona);
