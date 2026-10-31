// Tokens de color iniciales de docs/02 §4.1 (nombres de acabado). La rebanada S5 añade el resto
// de tokens (tipografía, espacio, radios, sombras, movimiento), las variables CSS y el @theme de
// Tailwind, y corrige los colores que no alcanzan el contraste AA.
export const colors = {
  'negro-pavonado': '#0B0C0E',
  carbon: '#121417',
  grafito: '#1C1F23',
  acero: '#2A2F35',
  niebla: '#9AA3AD',
  hueso: '#E8E4DC',
  laton: '#B8925A',
  'laton-claro': '#D9B77E',
  fde: '#A08A6A',
  'verde-ranger': '#4B5A3F',
  'naranja-senal': '#E4572E',
  'estado-ok': '#3FA66B',
  'estado-aviso': '#E0A526',
  'estado-error': '#D2453F',
  'estado-desconocido': '#6B7480',
} as const;

export type ColorToken = keyof typeof colors;
