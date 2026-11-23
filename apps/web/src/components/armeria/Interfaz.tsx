// Interfaz HTML de La Armería, común a los tres niveles (póster, B y A): cabecera, navegación de zonas y
// hoja de la zona abierta. La navegación real es siempre HTML semántico (docs/02 §3.4): la escena es una
// mejora progresiva por encima. Teclado: un solo tabulador para toda la navegación (roving tabindex), con
// ← → ↑ ↓ Inicio y Fin entre zonas, Intro para entrar y Esc para cerrar la hoja.
import { BRAND } from '@taller6mm/ui/brand';
import { Boton, Placa } from '@taller6mm/ui/componentes';
import { type KeyboardEvent, type ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import { type EstadoArmeria, zonaActiva } from './estado.ts';
import { VARIANTES_LUZ } from './luz.ts';
import { TEXTO_ALTERNATIVO } from './Poster.tsx';
import type { Acciones } from './useArmeria.ts';
import { ESTANTERIAS, ORDEN_ESTANTERIAS, ZONAS, zonaPorId, zonasDe } from './zonas.ts';
import './armeria.css';

function Demo({ plural = false }: { plural?: boolean }) {
  return (
    <span className="armeria__demo">
      Demo<span className="t6-sr">{plural ? ' (datos de ejemplo)' : ' (dato de ejemplo)'}</span>
    </span>
  );
}

/** «186 accesorios · 8 tiendas»: si el dato parte en dos líneas, el «·» se queda al final de la primera. */
const sinSeparadorHuerfano = (dato: string) => dato.replaceAll(' · ', ' · ');

/** Bombilla: «Más luz». */
function IconoLuz() {
  return (
    <svg className="armeria__icono" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1 2V16h5.2v-.2c0-.8.4-1.5 1-2A6 6 0 0 0 12 3Z" />
    </svg>
  );
}

export interface InterfazProps {
  estado: EstadoArmeria;
  acciones: Acciones;
  /** El póster o la escena (lienzo). */
  children: ReactNode;
  /** Con la escena pintando, el póster (y su texto alternativo) se oculta: el lector oye lo mismo una vez. */
  escenaActiva?: boolean;
}

export function InterfazArmeria({ estado, acciones, children, escenaActiva = false }: InterfazProps) {
  const enlaces = useRef<Record<string, HTMLAnchorElement | null>>({});
  const panel = useRef<HTMLDivElement>(null);
  const volverA = useRef<string | null>(null);
  const [foco, setFoco] = useState<string>(ZONAS[0]?.id ?? 'replicas');
  const abierta = zonaPorId(estado.abierta);
  const activa = zonaActiva(estado);

  const abrir = useCallback(
    (id: string) => {
      volverA.current = id;
      acciones.abrir(id);
    },
    [acciones],
  );
  const cerrar = useCallback(() => {
    acciones.cerrar();
    const id = volverA.current;
    if (id) requestAnimationFrame(() => enlaces.current[id]?.focus());
  }, [acciones]);

  // Esc cierra la hoja de la zona (docs/02 §3.2).
  useEffect(() => {
    if (!estado.abierta) return;
    const tecla = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape') cerrar();
    };
    addEventListener('keydown', tecla);
    return () => removeEventListener('keydown', tecla);
  }, [estado.abierta, cerrar]);

  // Al abrir una zona, el foco va a su hoja y el lector oye su nombre.
  useEffect(() => {
    if (estado.abierta) panel.current?.focus();
  }, [estado.abierta]);

  const teclaZona = (e: KeyboardEvent<HTMLAnchorElement>, id: string) => {
    const i = ZONAS.findIndex((z) => z.id === id);
    let destino: number | null = null;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') destino = (i + 1) % ZONAS.length;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') destino = (i - 1 + ZONAS.length) % ZONAS.length;
    if (e.key === 'Home') destino = 0;
    if (e.key === 'End') destino = ZONAS.length - 1;
    const z = destino === null ? undefined : ZONAS[destino];
    if (!z) return;
    e.preventDefault();
    setFoco(z.id);
    enlaces.current[z.id]?.focus();
  };

  return (
    <div className="armeria" data-hidratado={estado.hidratado} data-abierta={Boolean(abierta)} data-luz={estado.luz}>
      <div className="armeria__escena">
        {children}
        {escenaActiva ? <p className="t6-sr">{TEXTO_ALTERNATIVO}</p> : null}
      </div>

      <div className="armeria__capa">
        <header className="armeria__cabecera">
          <div className="armeria__identidad">
            <a className="armeria__marca" href="/">
              {BRAND.name}
            </a>
            <p className="armeria__lema">{BRAND.tagline}</p>
          </div>
          {/* Hasta tener réplicas modeladas a escala real (frente de fidelidad), las siluetas son de atrezo. */}
          <p className="armeria__nota">
            Datos de demostración
            <span className="armeria__provisional">Réplicas reales: próximamente</span>
          </p>
          {/* Acción principal: el banco (configurador) es el protagonista de la web. */}
          <Boton variante="laton" className="armeria__accion" onClick={() => abrir('banco')}>
            Monta tu réplica
          </Boton>
          {/* «Más luz» siempre a la vista: penumbra por defecto, pero el texto nunca debe costar leerlo. */}
          <fieldset className="armeria__ajustes">
            <legend className="t6-sr">Ajustes de la sala</legend>
            <button
              type="button"
              className="armeria__ajuste"
              aria-pressed={estado.luz === 'mas-luz'}
              title={`Luz: ${VARIANTES_LUZ[estado.luz].nombre}`}
              onClick={() => acciones.cambiarLuz(estado.luz === 'mas-luz' ? 'penumbra' : 'mas-luz')}
            >
              <IconoLuz />
              Más luz
            </button>
          </fieldset>
        </header>

        <nav className="armeria__nav" aria-label="Zonas de La Armería">
          {ORDEN_ESTANTERIAS.map((e) => (
            <section key={e} className="armeria__grupo" aria-labelledby={`armeria-grupo-${e}`} data-estanteria={e}>
              <h2 id={`armeria-grupo-${e}`} className="armeria__grupo-titulo">
                {ESTANTERIAS[e].titulo}
                <span className="armeria__demo armeria__demo--grupo">
                  Demo<span className="t6-sr"> (datos de ejemplo)</span>
                </span>
              </h2>
              <ul className="armeria__lista">
                {zonasDe(e).map((z) => (
                  <li key={z.id} className="armeria__item">
                    <a
                      ref={(el) => {
                        enlaces.current[z.id] = el;
                      }}
                      href={z.ruta}
                      className="armeria__zona"
                      data-activa={z.id === activa}
                      tabIndex={z.id === foco ? 0 : -1}
                      onFocus={() => {
                        setFoco(z.id);
                        acciones.enfocar(z.id);
                      }}
                      onBlur={() => acciones.enfocar(null)}
                      onPointerEnter={() => acciones.apuntar(z.id)}
                      onPointerLeave={() => acciones.apuntar(null)}
                      onKeyDown={(ev) => teclaZona(ev, z.id)}
                      onClick={(ev) => {
                        ev.preventDefault();
                        abrir(z.id);
                      }}
                    >
                      <span className="armeria__zona-nombre">{z.rotulo}</span>
                      <span className="armeria__zona-dato">
                        <span>{sinSeparadorHuerfano(z.dato)}</span>
                        <Demo />
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>
      </div>

      {abierta ? (
        <div
          className="armeria__panel"
          role="dialog"
          aria-modal="false"
          aria-label={abierta.nombre}
          tabIndex={-1}
          ref={panel}
        >
          <Placa titulo={abierta.nombre} nivelTitulo={2} codigo={abierta.ruta} as="div">
            <p className="armeria__panel-texto">{abierta.descripcion}</p>
            <p className="armeria__panel-dato">
              {abierta.dato} <Demo />
            </p>
            <p className="armeria__panel-nota">
              Esta sección llega en la Fase {abierta.fase}. En la versión final, la cámara entra en el pasillo y un
              fundido lleva a <code>{abierta.ruta}</code>.
            </p>
            <div className="armeria__panel-acciones">
              <Boton variante="laton" aria-disabled="true" title={`Llega en la Fase ${abierta.fase}`}>
                Entrar · Fase {abierta.fase}
              </Boton>
              <Boton variante="fantasma" onClick={cerrar}>
                Volver a la sala
              </Boton>
            </div>
          </Placa>
        </div>
      ) : null}
    </div>
  );
}
