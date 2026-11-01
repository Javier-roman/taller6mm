/** Une clases CSS ignorando las vacías. */
export const cx = (...parts: ReadonlyArray<string | false | null | undefined>): string =>
  parts.filter(Boolean).join(' ');

/** Estados de puntero y foco que /sistema fuerza en estático para documentarlos (`data-demo`). */
export type EstadoDemo = 'hover' | 'activo' | 'foco';
