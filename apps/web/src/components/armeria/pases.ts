// Contrato entre el horno (horno/Horno.tsx y Blender) y el compositor del nivel B (nivel-b/compositor.ts, WebGL2
// sin three.js): qué pases hay, con qué exposición se guardan y cómo va codificada la profundidad.

/** Los pases de luz se guardan con esta exposición: el B los divide para recuperar hasta 2,0 lineal. */
export const EXPOSICION_HORNO = 0.5;
/**
 * El pase «base» (relleno ambiente) se hornea con el ambiente de Blender a 0,3 (subido desde el 0,2 de las
 * pruebas para que se lea el ladrillo y el fondo de los módulos) y entra al compositor tal cual. Si se hornea con
 * otro valor, esta ganancia lo iguala (la luz es lineal): ganancia = ambiente deseado / ambiente horneado.
 */
export const GANANCIA_BASE = 1;
/** Profundidad codificada en 8 bits entre estas distancias (m) a la cámara. */
export const PROFUNDIDAD = { cerca: 1.5, lejos: 12 } as const;
/** Resolución de los pases (16:9): 2560 × 1440, la que se hornea con Cycles; el póster sale a 1920 y 960. */
export const TAMANO_PASE = { ancho: 2560, alto: 1440 } as const;

export const PASES_LUZ = ['base', 'tubo-izquierda', 'tubo-centro', 'tubo-derecha', 'calidas', 'rotulos'] as const;
export const PASES_DATOS = ['albedo', 'normal', 'profundidad'] as const;
export type Pase = (typeof PASES_LUZ)[number] | (typeof PASES_DATOS)[number];

/** Nombre del archivo de cada pase en el conjunto de vistas (assets-src/vistas/armeria, scripts/armeria/vistas.mjs). */
export const archivoPase = (pase: Pase) => `${pase}.webp`;
