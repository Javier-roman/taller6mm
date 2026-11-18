// Copia mínima de `catalogo/iluminacion-presets.json` para cuando el script de preparación no la encuentre
// (el catálogo lo crea otro agente: rama feat/escalera-dura-iluminacion). Mismos números y mismo formato; en
// cuanto el catálogo esté en `main`, el visor lee el archivo y esta copia queda solo de reserva. El nombre
// visible sale del id, como en la lectura del catálogo.
import { type ConjuntoPresets, ESQUEMA_PRESETS, nombreDePreset, type PresetEstudio } from './iluminacion.ts';

const preset = (id: string, p: Omit<PresetEstudio, 'id' | 'nombre'>): PresetEstudio => ({
  id,
  nombre: nombreDePreset(id),
  ...p,
});

export const PRESETS_MINIMOS: ConjuntoPresets = {
  esquema: ESQUEMA_PRESETS,
  defecto: 'mate_suave',
  brillo: {
    global: { min: 0.5, max: 1.5, defecto: 1 },
    rug_por_factor: 0.12,
    banda_rugosidad: 0.1,
    rugosidad_minima_absoluta: 0.02,
  },
  presets: [
    preset('mate_suave', {
      descripcion:
        'Por defecto. Luz de estudio amplia y difusa: softboxes grandes, reflejos contenidos y contraluz tenue. Para juzgar forma y material sin brillos que quemen.',
      exposicion_ev: -0.35,
      tono: 'AgX',
      mundo: { abajo: [0.16, 0.16, 0.165], arriba: [0.3, 0.3, 0.31], intensidad: 1 },
      suelo: { color: [0.18, 0.18, 0.18], rugosidad: 0.75, metalico: 0 },
      rugosidad_delta: 0.06,
      luces: [
        { id: 'clave', dir: [0.5, -1, 1.1], dist: 1.3, energia_d2: 85, tam_d: 2.6, color: [1, 1, 1] },
        { id: 'relleno', dir: [1.3, 0.9, 0.4], dist: 1.5, energia_d2: 48, tam_d: 2.8, color: [0.88, 0.93, 1] },
        { id: 'contra-a', dir: [-1.3, 0.6, 0.7], dist: 1.4, energia_d2: 55, tam_d: 1.1, color: [1, 0.97, 0.92] },
        { id: 'contra-b', dir: [-1, -0.9, 0.5], dist: 1.4, energia_d2: 36, tam_d: 1, color: [0.92, 0.95, 1] },
        { id: 'sombrero', dir: [0, 0, 1.6], dist: 1.2, energia_d2: 38, tam_d: 2.2, color: [1, 1, 1] },
      ],
    }),
    preset('estudio_contraste', {
      descripcion:
        'Estudio de producto con más contraste: luces más pequeñas y duras, contraluz marcado. Es el estudio antiguo de la escalera, ya con el brillo acotado.',
      exposicion_ev: -0.15,
      tono: 'AgX',
      mundo: { abajo: [0.11, 0.11, 0.115], arriba: [0.26, 0.26, 0.27], intensidad: 1 },
      suelo: { color: [0.18, 0.18, 0.18], rugosidad: 0.45, metalico: 0 },
      rugosidad_delta: 0,
      luces: [
        { id: 'clave', dir: [0.5, -1, 1.1], dist: 1.3, energia_d2: 120, tam_d: 1.6, color: [1, 1, 1] },
        { id: 'relleno', dir: [1.3, 0.9, 0.4], dist: 1.5, energia_d2: 40, tam_d: 1.6, color: [0.85, 0.92, 1] },
        { id: 'contra-a', dir: [-1.3, 0.6, 0.7], dist: 1.4, energia_d2: 170, tam_d: 0.35, color: [1, 0.97, 0.9] },
        { id: 'contra-b', dir: [-1, -0.9, 0.5], dist: 1.4, energia_d2: 110, tam_d: 0.3, color: [0.9, 0.95, 1] },
        { id: 'sombrero', dir: [0, 0, 1.6], dist: 1.2, energia_d2: 30, tam_d: 1.2, color: [1, 1, 1] },
      ],
    }),
    preset('dramatica_penumbra', {
      descripcion:
        'Penumbra dramática: fondo oscuro, una clave lateral y un contraluz que dibuja la silueta. Para la portada y la Armería; no sirve para medir sombras.',
      exposicion_ev: -0.6,
      tono: 'AgX',
      mundo: { abajo: [0.03, 0.03, 0.035], arriba: [0.09, 0.09, 0.1], intensidad: 1 },
      suelo: { color: [0.06, 0.06, 0.065], rugosidad: 0.55, metalico: 0 },
      rugosidad_delta: 0.03,
      luces: [
        { id: 'clave', dir: [1.4, -0.6, 0.8], dist: 1.3, energia_d2: 120, tam_d: 0.9, color: [1, 0.95, 0.88] },
        { id: 'relleno', dir: [-0.6, 1, 0.3], dist: 1.6, energia_d2: 6, tam_d: 2, color: [0.7, 0.8, 1] },
        { id: 'contra-a', dir: [-1.3, 0.6, 0.7], dist: 1.4, energia_d2: 140, tam_d: 0.4, color: [0.85, 0.92, 1] },
        { id: 'contra-b', dir: [-1, -0.9, 0.5], dist: 1.4, energia_d2: 80, tam_d: 0.35, color: [1, 0.95, 0.9] },
      ],
    }),
  ],
};
