// Contrato entre el horno (Horno.tsx, three.js) y el compositor del prototipo B (EscenaB.ts, WebGL2
// sin three.js): qué pases hay, con qué exposición se guardan y cómo va codificada la profundidad.

/** Los pases de luz se guardan con esta exposición: el B los divide para recuperar hasta 2,0 lineal. */
export const EXPOSICION_HORNO = 0.5;
/** Profundidad codificada en 8 bits entre estas distancias (m) a la cámara. */
export const PROFUNDIDAD = { cerca: 1.5, lejos: 12 } as const;
/** Resolución de los pases: la del póster (16:9). */
export const TAMANO_PASE = { ancho: 1920, alto: 1080 } as const;

export const PASES_LUZ = ['base', 'tubo-izquierda', 'tubo-centro', 'tubo-derecha', 'calidas', 'rotulos'] as const;
export const PASES_DATOS = ['albedo', 'normal', 'profundidad'] as const;
export type Pase = (typeof PASES_LUZ)[number] | (typeof PASES_DATOS)[number];

export const RUTA_PASES = '/prototipos/armeria-b';
