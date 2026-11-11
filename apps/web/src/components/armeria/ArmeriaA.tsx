// Prototipo A de La Armería (Fase 1): escena 3D en tiempo real con React Three Fiber.
// Esta isla es ligera (interfaz + póster); el chunk 3D (three.js, R3F y postprocesado) se pide
// después del primer pintado, con las fuentes de los rótulos ya listas, y solo si hay WebGL2.
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { type CanalEscena, crearCanal } from './canal.ts';
import { fuentesListas } from './fuentes.ts';
import { conEscena, InterfazArmeria, Poster, useArmeria } from './Interfaz.tsx';

const EscenaA = lazy(() => import('./EscenaA.tsx'));

export default function ArmeriaA() {
  const { estado, acciones } = useArmeria();
  const canal = useRef<CanalEscena>(crearCanal());
  const etiqueta = useRef<HTMLDivElement>(null);
  const [cargar, setCargar] = useState(false);
  const escena = conEscena(estado);

  useEffect(() => {
    if (!escena) return;
    let vivo = true;
    const pedir = () => {
      // El chunk 3D se descarga en paralelo a las fuentes; solo los rótulos necesitan esperarlas.
      void import('./EscenaA.tsx');
      fuentesListas().then(() => {
        if (vivo) setCargar(true);
      });
    };
    const id =
      typeof requestIdleCallback === 'function'
        ? requestIdleCallback(pedir, { timeout: 1200 })
        : window.setTimeout(pedir, 200);
    return () => {
      vivo = false;
      if (typeof cancelIdleCallback === 'function') cancelIdleCallback(id);
      else clearTimeout(id);
    };
  }, [escena]);

  const saltarIntro = useCallback(() => {
    canal.current.director?.saltarIntro();
    canal.current.pintar();
    acciones.introTermina();
  }, [acciones]);

  // La intro empieza cuando la escena ya pinta. Si llega tarde (más de 1,5 s), el usuario ya ha visto
  // la sala en el póster: no se apaga para volver a encenderla (critico-diseno).
  useEffect(() => {
    if (!estado.listo || !estado.intro || estado.introActiva) return;
    if (!estado.forzarIntro && performance.now() > 1500) saltarIntro();
    else acciones.introEmpieza();
  }, [estado.listo, estado.intro, estado.introActiva, estado.forzarIntro, acciones, saltarIntro]);

  return (
    <InterfazArmeria
      prototipo="A"
      descripcion="3D en tiempo real"
      tecnica="React Three Fiber"
      estado={estado}
      acciones={acciones}
      etiqueta={etiqueta}
      onSaltarIntro={saltarIntro}
      onProgreso={(p) => {
        canal.current.progreso = p;
        canal.current.pintar();
      }}
    >
      <Poster acciones={acciones} oculto={escena && estado.listo} movil={estado.movil} />
      {escena && cargar ? (
        <div className="armeria__lienzo" data-listo={estado.listo}>
          <Suspense fallback={null}>
            <EscenaA
              canal={canal}
              zonaActiva={estado.zonaActiva}
              zonaAbierta={estado.zonaAbierta}
              movil={estado.movil}
              reducido={estado.reducido}
              intro={estado.intro}
              variante={estado.variante}
              calidad={estado.calidad}
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
