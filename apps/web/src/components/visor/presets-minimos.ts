// Presets mínimos del visor: valen mientras no exista catalogo/iluminacion-presets.json (formato en
// iluminacion.ts). Los colores son tokens de @taller6mm/ui. La penumbra imita la de La Armería (ADR-0002):
// luz indirecta, sin haces visibles, y «Más luz» sube el nivel sin cambiar la temperatura.
import type { ConjuntoPresets } from './iluminacion.ts';

export const PRESETS_MINIMOS: ConjuntoPresets = {
  esquema: 'iluminacion-presets/v1',
  por_defecto: 'mate',
  presets: [
    {
      id: 'mate',
      nombre: 'Mate',
      descripcion: 'Luz difusa y pareja, sin brillos duros: para ver la forma sin que los reflejos la disfracen.',
      fondo: 'carbon',
      exposicion: 1.05,
      entorno: 0.55,
      luces: [
        { tipo: 'hemisferio', color: 'hueso', color_suelo: 'niebla', intensidad: 1.2 },
        { tipo: 'direccional', color: 'hueso', intensidad: 1.6, posicion: [-1.2, 2.4, 2], sombra: true, suavidad: 1 },
        { tipo: 'direccional', color: 'niebla', intensidad: 0.8, posicion: [1.6, 0.8, -1.6] },
      ],
    },
    {
      id: 'estudio',
      nombre: 'Estudio',
      descripcion: 'Clave a tres cuartos, relleno a 3:1 y dos contraluces que dibujan el canto (guía de aspecto §7).',
      fondo: 'grafito',
      exposicion: 1,
      entorno: 0.8,
      luces: [
        {
          tipo: 'direccional',
          color: 'hueso',
          intensidad: 3.2,
          posicion: [-1.4, 1.8, 2.2],
          sombra: true,
          suavidad: 0.5,
        },
        { tipo: 'direccional', color: 'hueso', intensidad: 1.05, posicion: [1.8, 0.6, 1.6] },
        { tipo: 'direccional', color: 'hueso', intensidad: 2.2, posicion: [-0.4, 1.2, -2.4] },
        { tipo: 'direccional', color: 'hueso', intensidad: 1.6, posicion: [1.2, 1.4, -2] },
      ],
    },
    {
      id: 'taller',
      nombre: 'Taller',
      descripcion: 'Cenital fría de los tubos del techo y el flexo cálido del banco a un lado.',
      fondo: 'negro-pavonado',
      exposicion: 1,
      entorno: 0.35,
      luces: [
        { tipo: 'hemisferio', color: 'niebla', color_suelo: 'acero', intensidad: 0.5 },
        { tipo: 'direccional', color: 'hueso', intensidad: 2.2, posicion: [0.2, 3, 0.6], sombra: true, suavidad: 0.7 },
        { tipo: 'foco', color: 'laton-claro', intensidad: 3.4, posicion: [2.2, 1.4, 1.4], sombra: true, suavidad: 0.6 },
      ],
    },
    {
      id: 'penumbra',
      nombre: 'Penumbra',
      descripcion: 'La sala de La Armería: casi a oscuras, con un tubo lejano. «Más luz» la abre sin cambiar de color.',
      fondo: 'negro-pavonado',
      exposicion: 0.9,
      entorno: 0.12,
      luces: [
        { tipo: 'hemisferio', color: 'niebla', color_suelo: 'acero', intensidad: 0.18 },
        { tipo: 'direccional', color: 'hueso', intensidad: 1.3, posicion: [-0.6, 3, 0.4], sombra: true, suavidad: 0.8 },
      ],
    },
    {
      id: 'rasante',
      nombre: 'Rasante',
      descripcion: 'Luz baja y lateral que marca el relieve (roscas, ranuras, líneas de partición).',
      fondo: 'carbon',
      exposicion: 1,
      entorno: 0.15,
      luces: [
        {
          tipo: 'direccional',
          color: 'hueso',
          intensidad: 3.4,
          posicion: [-3, 0.35, 0.6],
          sombra: true,
          suavidad: 0.2,
        },
        { tipo: 'hemisferio', color: 'niebla', color_suelo: 'acero', intensidad: 0.3 },
      ],
    },
  ],
};
