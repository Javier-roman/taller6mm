// Iconos propios a plantilla (docs/02 §4.6): trazo de 1,75 sobre 24 × 24, en currentColor.
// Siempre decorativos: el significado lo lleva el texto que los acompaña.
import type { ReactNode } from 'react';

function Icono({ children }: { children: ReactNode }) {
  return (
    <svg
      className="t6-icono"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="square"
      strokeLinejoin="miter"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

/** Error: señal triangular con exclamación. */
export const IconoAlerta = () => (
  <Icono>
    <path d="M12 3 22 20H2L12 3Z" />
    <path d="M12 10v4M12 17v.5" />
  </Icono>
);

/** Sin datos: interrogación dentro de un círculo discontinuo. */
export const IconoDesconocido = () => (
  <Icono>
    <circle cx="12" cy="12" r="9" strokeDasharray="3 2.5" />
    <path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5v.7M12 17v.5" />
  </Icono>
);

/** T0 · Plano técnico: silueta con línea de cota. */
export const IconoPlano = () => (
  <Icono>
    <path d="M3 14h13l2-3h3v3l-2 2H3z" />
    <path d="M3 19h18M3 17.5v3M21 17.5v3" />
  </Icono>
);

/** T1 · Foto licenciada: cámara con diafragma. */
export const IconoFoto = () => (
  <Icono>
    <path d="M3 7h4l2-2h6l2 2h4v12H3z" />
    <circle cx="12" cy="13" r="3.5" />
  </Icono>
);

/** T2 · Modelo fiel: cubo en perspectiva. */
export const IconoModelo = () => (
  <Icono>
    <path d="M12 3 20 7.5v9L12 21l-8-4.5v-9z" />
    <path d="M4 7.5 12 12l8-4.5M12 12v9" />
  </Icono>
);

/** T3 · Escaneado y verificado: cubo con marca de verificación. */
export const IconoVerificado = () => (
  <Icono>
    <path d="M12 3 20 7.5v9L12 21l-8-4.5v-9z" />
    <path d="m8.5 12 2.5 2.5 4.5-5" />
  </Icono>
);

/** Flecha de avance para enlaces y placas clicables. */
export const IconoFlecha = () => (
  <Icono>
    <path d="M4 12h15M14 7l5 5-5 5" />
  </Icono>
);

/** Correcto / compatible: marca de verificación. */
export const IconoCheck = () => (
  <Icono>
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  </Icono>
);

/** Agotado / incompatible / cerrar: aspa. */
export const IconoCruz = () => (
  <Icono>
    <path d="m6 6 12 12M18 6 6 18" />
  </Icono>
);

/** Información: «i» dentro de un círculo. */
export const IconoInfo = () => (
  <Icono>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v6M12 7.5v.5" />
  </Icono>
);

/** Con adaptador: dos piezas unidas por una intermedia. */
export const IconoAdaptador = () => (
  <Icono>
    <path d="M3 9h5v6H3zM16 9h5v6h-5z" />
    <path d="M8 12h8M11 9v6M13 9v6" />
  </Icono>
);

/** Reloj: dato provisional o pendiente de comprobar. */
export const IconoReloj = () => (
  <Icono>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </Icono>
);

/** Estrella de valoración (el relleno lo decide `llena`). */
export const IconoEstrella = ({ llena }: { llena: boolean }) => (
  <svg
    className="t6-icono"
    viewBox="0 0 24 24"
    fill={llena ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinejoin="miter"
    aria-hidden="true"
    focusable="false"
  >
    <path d="m12 3 2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L12 16.8 6.4 20l1.3-6.2L3 9.5l6.3-.7z" />
  </svg>
);
