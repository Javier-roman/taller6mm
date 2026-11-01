// Datos de la página viva /sistema. Las clases de Tailwind van escritas enteras para que su
// escáner las encuentre (no detecta clases construidas en tiempo de ejecución).
import type { ColorToken } from '@taller6mm/ui/tokens';

export const FONDO: Record<ColorToken, string> = {
  'negro-pavonado': 'bg-negro-pavonado',
  carbon: 'bg-carbon',
  grafito: 'bg-grafito',
  acero: 'bg-acero',
  hueso: 'bg-hueso',
  niebla: 'bg-niebla',
  laton: 'bg-laton',
  'laton-claro': 'bg-laton-claro',
  fde: 'bg-fde',
  'verde-ranger': 'bg-verde-ranger',
  'naranja-senal': 'bg-naranja-senal',
  'estado-ok': 'bg-estado-ok',
  'estado-aviso': 'bg-estado-aviso',
  'estado-error': 'bg-estado-error',
  'estado-desconocido': 'bg-estado-desconocido',
};

export const TEXTO: Record<ColorToken, string> = {
  'negro-pavonado': 'text-negro-pavonado',
  carbon: 'text-carbon',
  grafito: 'text-grafito',
  acero: 'text-acero',
  hueso: 'text-hueso',
  niebla: 'text-niebla',
  laton: 'text-laton',
  'laton-claro': 'text-laton-claro',
  fde: 'text-fde',
  'verde-ranger': 'text-verde-ranger',
  'naranja-senal': 'text-naranja-senal',
  'estado-ok': 'text-estado-ok',
  'estado-aviso': 'text-estado-aviso',
  'estado-error': 'text-estado-error',
  'estado-desconocido': 'text-estado-desconocido',
};

export const GRUPOS_COLOR = [
  { grupo: 'superficie', titulo: 'Superficies' },
  { grupo: 'texto', titulo: 'Texto' },
  { grupo: 'acento', titulo: 'Acentos' },
  { grupo: 'estado', titulo: 'Estados' },
] as const;

export const ESCALA_TEXTO = [
  { token: 'xs', clase: 'text-xs', px: 12 },
  { token: 's', clase: 'text-s', px: 14 },
  { token: 'm', clase: 'text-m', px: 16 },
  { token: 'l', clase: 'text-l', px: 20 },
  { token: 'xl', clase: 'text-xl', px: 25 },
  { token: '2xl', clase: 'text-2xl', px: 31 },
  { token: '3xl', clase: 'text-3xl', px: 39 },
  { token: '4xl', clase: 'text-4xl', px: 49 },
  { token: '5xl', clase: 'text-5xl', px: 61 },
] as const;

export const ESCALA_ESPACIO = [
  { token: '1', clase: 'w-1', px: 4 },
  { token: '2', clase: 'w-2', px: 8 },
  { token: '3', clase: 'w-3', px: 12 },
  { token: '4', clase: 'w-4', px: 16 },
  { token: '6', clase: 'w-6', px: 24 },
  { token: '8', clase: 'w-8', px: 32 },
  { token: '12', clase: 'w-12', px: 48 },
  { token: '16', clase: 'w-16', px: 64 },
  { token: '24', clase: 'w-24', px: 96 },
] as const;

// Cifra y unidad con espacio duro (U+00A0): nunca se separan en dos líneas.
export const RADIOS = [
  { token: 's', clase: 'rounded-s', valor: '2 px' },
  { token: 'm', clase: 'rounded-m', valor: '3 px' },
  { token: 'l', clase: 'rounded-l', valor: '4 px' },
] as const;
export const SOMBRAS = [
  { token: 'placa', clase: 'shadow-placa', uso: 'Placas y tarjetas' },
  { token: 'elevada', clase: 'shadow-elevada', uso: 'Maletín (modal) y hover de placas' },
  { token: 'boton', clase: 'shadow-boton', uso: 'Botones con relieve' },
  { token: 'hundida', clase: 'shadow-hundida', uso: 'Pistas, campos y botón pulsado' },
] as const;

export const SECCIONES = [
  { id: 'color', titulo: 'Color' },
  { id: 'tipografia', titulo: 'Tipografía' },
  { id: 'espacio', titulo: 'Espacio y forma' },
  { id: 'movimiento', titulo: 'Movimiento' },
  { id: 'boton', titulo: 'Botón' },
  { id: 'placa', titulo: 'Placa' },
  { id: 'rotulo', titulo: 'Rótulo' },
  { id: 'fidelidad', titulo: 'Fidelidad' },
  { id: 'dato', titulo: 'Barra de dato' },
  { id: 'cargador', titulo: 'Cargador' },
] as const;
