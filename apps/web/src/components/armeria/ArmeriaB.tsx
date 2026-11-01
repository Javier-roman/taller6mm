// Prototipo B de La Armería (Fase 1): 2,5D re-iluminable. La isla es la misma interfaz que en A; la
// escena es un compositor WebGL2 de ~10 KB que suma pases horneados de la sala (sin three.js).
import { lazy, Suspense, useCallback, useEffect, useRef } from 'react';
import { type CanalEscena, crearCanal } from './canal.ts';
import { conEscena, InterfazArmeria, Poster, useArmeria } from './Interfaz.tsx';

const EscenaB = lazy(() => import('./EscenaB.tsx'));

export default function ArmeriaB() {
  const { estado, acciones } = useArmeria();
  const canal = useRef<CanalEscena>(crearCanal());
  const etiqueta = useRef<HTMLDivElement>(null);
  const escena = conEscena(estado);

  useEffect(() => {
    if (estado.listo && estado.intro && !estado.introActiva) acciones.introEmpieza();
  }, [estado.listo, estado.intro, estado.introActiva, acciones]);

  const saltarIntro = useCallback(() => {
    canal.current.director?.saltarIntro();
    canal.current.pintar();
    acciones.introTermina();
  }, [acciones]);

  return (
    <InterfazArmeria
      prototipo="B"
      descripcion="2,5D re-iluminable"
      tecnica="pases horneados + WebGL2"
      estado={estado}
      acciones={acciones}
      etiqueta={etiqueta}
      onSaltarIntro={saltarIntro}
      onProgreso={(p) => {
        canal.current.progreso = p;
        canal.current.pintar();
      }}
    >
      <Poster acciones={acciones} zonaActiva={estado.zonaActiva} oculto={escena && estado.listo} movil={estado.movil} />
      {escena ? (
        <div className="armeria__lienzo" data-listo={estado.listo} aria-hidden="true">
          <Suspense fallback={null}>
            <EscenaB
              canal={canal}
              zonaActiva={estado.zonaActiva}
              zonaAbierta={estado.zonaAbierta}
              movil={estado.movil}
              reducido={estado.reducido}
              intro={estado.intro}
              variante={estado.variante}
              medir={estado.medir}
              etiqueta={etiqueta}
              onApuntar={acciones.apuntar}
              onElegir={acciones.abrir}
              onListo={acciones.listo}
              onIntroFin={acciones.introTermina}
              onLento={acciones.lento}
            />
          </Suspense>
        </div>
      ) : null}
    </InterfazArmeria>
  );
}
