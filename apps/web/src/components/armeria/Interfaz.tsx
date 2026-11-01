// Interfaz HTML de La Armería, común a los prototipos A y B: cabecera, navegación de zonas (barra en
// escritorio, carrusel con scroll-snap en móvil), etiqueta flotante, panel de la zona, botón de saltar
// la intro y póster con zonas clicables. La navegación real es siempre HTML (docs/02 §3.4): el 3D y el
// 2,5D son una mejora progresiva por encima.
import { BRAND } from '@taller6mm/ui/brand';
import { Boton, Placa } from '@taller6mm/ui/componentes';
import {
  type KeyboardEvent,
  type ReactNode,
  type RefObject,
  type UIEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { VARIANTES, type Variante } from './director.ts';
import { ESTANTERIAS, ORDEN_ESTANTERIAS, ZONAS, zonaPorId, zonasDe } from './zonas.ts';
import './armeria.css';

const CLAVE = {
  intro: 'taller6mm:armeria:intro-vista',
  vista: 'taller6mm:armeria:vista',
  luz: 'taller6mm:armeria:luz',
} as const;

const leer = (clave: string) => {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
};
const guardar = (clave: string, valor: string) => {
  try {
    localStorage.setItem(clave, valor);
  } catch {
    // Navegación privada o almacenamiento lleno: la preferencia dura lo que la visita.
  }
};

export type Vista = 'escena' | 'ligera';

export interface EstadoArmeria {
  hidratado: boolean;
  movil: boolean;
  reducido: boolean;
  variante: Variante;
  vista: Vista;
  /** El navegador puede con la escena (WebGL2, sin ahorro de datos) y no ha ido lenta. */
  capaz: boolean;
  lento: boolean;
  /** La escena ya ha pintado su primer fotograma: el póster puede irse. */
  listo: boolean;
  intro: boolean;
  introActiva: boolean;
  zonaActiva: string | null;
  zonaAbierta: string | null;
  centrada: string;
  calidad: 'alta' | 'baja';
  medir: boolean;
}

export function useArmeria() {
  const [hidratado, setHidratado] = useState(false);
  const [movil, setMovil] = useState(false);
  const [reducido, setReducido] = useState(false);
  const [variante, setVariante] = useState<Variante>('penumbra');
  const [vista, setVista] = useState<Vista>('escena');
  const [capaz, setCapaz] = useState(false);
  const [lento, setLento] = useState(false);
  const [listo, setListo] = useState(false);
  const [intro, setIntro] = useState(false);
  const [introActiva, setIntroActiva] = useState(false);
  const [apuntada, setApuntada] = useState<string | null>(null);
  const [enfocada, setEnfocada] = useState<string | null>(null);
  const [centrada, setCentrada] = useState<string>(ZONAS[0]?.id ?? 'replicas');
  const [abierta, setAbierta] = useState<string | null>(null);
  const [calidad, setCalidad] = useState<'alta' | 'baja'>('alta');
  const [medir, setMedir] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const mqMovil = matchMedia('(max-width: 52.125rem)');
    const mqReducido = matchMedia('(prefers-reduced-motion: reduce)');
    const actualizar = () => {
      setMovil(mqMovil.matches);
      setReducido(mqReducido.matches);
    };
    actualizar();
    mqMovil.addEventListener('change', actualizar);
    mqReducido.addEventListener('change', actualizar);

    const luz = params.get('luz') ?? leer(CLAVE.luz);
    if (luz === 'taller' || luz === 'penumbra') setVariante(luz);
    const pedida = params.get('vista') ?? leer(CLAVE.vista);
    if (pedida === 'ligera') setVista('ligera');
    // Póster si no hay WebGL2 o si el usuario pide ahorrar datos (docs/02 §3.4).
    const conexion = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    let webgl2 = false;
    try {
      webgl2 = Boolean(document.createElement('canvas').getContext('webgl2'));
    } catch {
      webgl2 = false;
    }
    setCapaz(webgl2 && !conexion?.saveData);
    const tactil = matchMedia('(pointer: coarse)').matches;
    const forzada = params.get('calidad');
    setCalidad(forzada === 'alta' || forzada === 'baja' ? forzada : tactil || mqMovil.matches ? 'baja' : 'alta');
    setMedir(params.has('medir'));
    const introPedida = params.get('intro');
    const quiereIntro = introPedida === '1' || (introPedida !== '0' && leer(CLAVE.intro) === null);
    setIntro(quiereIntro && !mqReducido.matches);
    setHidratado(true);
    return () => {
      mqMovil.removeEventListener('change', actualizar);
      mqReducido.removeEventListener('change', actualizar);
    };
  }, []);

  const zonaActiva = abierta ?? apuntada ?? enfocada ?? (movil ? centrada : null);

  const acciones = useMemo(
    () => ({
      apuntar: (id: string | null) => setApuntada(id),
      enfocar: (id: string | null) => setEnfocada(id),
      centrar: (id: string) => setCentrada(id),
      abrir: (id: string) => setAbierta(id),
      cerrar: () => setAbierta(null),
      listo: () => setListo(true),
      introEmpieza: () => setIntroActiva(true),
      introTermina: () => {
        setIntroActiva(false);
        setIntro(false);
        guardar(CLAVE.intro, new Date().toISOString());
      },
      lento: () => setLento(true),
      cambiarLuz: (v: Variante) => {
        setVariante(v);
        guardar(CLAVE.luz, v);
      },
      cambiarVista: (v: Vista) => {
        setVista(v);
        setListo(false);
        guardar(CLAVE.vista, v);
      },
    }),
    [],
  );

  const estado: EstadoArmeria = {
    hidratado,
    movil,
    reducido,
    variante,
    vista,
    capaz,
    lento,
    listo,
    intro,
    introActiva,
    zonaActiva,
    zonaAbierta: abierta,
    centrada,
    calidad,
    medir,
  };
  return { estado, acciones };
}

export type Acciones = ReturnType<typeof useArmeria>['acciones'];

/** ¿Se pinta la escena (A o B) o solo el póster? */
export const conEscena = (e: EstadoArmeria) => e.hidratado && e.capaz && e.vista === 'escena' && !e.lento;

export const TEXTO_ALTERNATIVO =
  'La Armería en penumbra: tres cuerpos de compactus verde oliva sobre raíles. A la izquierda, Catálogo (armero de réplicas y almacén de accesorios); en el centro, la vitrina de la comunidad y el banco de trabajo con su flexo; a la derecha, Mercado (tablón, mostrador de tiendas, manuales y taquilla).';

export function Poster({
  acciones,
  zonaActiva,
  oculto,
  movil,
}: {
  acciones: Acciones;
  zonaActiva: string | null;
  oculto: boolean;
  movil: boolean;
}) {
  const desplazable = useRef<HTMLDivElement>(null);
  // En móvil el póster se recorre en horizontal: empieza en el banco (el protagonista).
  useEffect(() => {
    const el = desplazable.current;
    if (el && movil) el.scrollLeft = (el.scrollWidth - el.clientWidth) / 2;
  }, [movil]);
  return (
    <div className="armeria-poster" data-oculto={oculto} ref={desplazable}>
      <div className="armeria-poster__lienzo">
        <img
          className="armeria-poster__imagen"
          src="/prototipos/armeria/poster-1920.webp"
          srcSet="/prototipos/armeria/poster-960.webp 960w, /prototipos/armeria/poster-1920.webp 1920w"
          sizes="(max-width: 52.125rem) 180vh, 100vw"
          width={1920}
          height={1080}
          alt={TEXTO_ALTERNATIVO}
          fetchPriority="high"
          decoding="async"
        />
        {ORDEN_ESTANTERIAS.map((estanteria) => (
          <span key={estanteria} className="armeria-poster__ancla" data-estanteria={estanteria} />
        ))}
        {/* Zonas clicables para ratón y tacto. Fuera del árbol de accesibilidad y del tabulador: el teclado y los lectores usan los mismos enlaces, con su nombre, en la navegación. */}
        <div className="armeria-poster__zonas" aria-hidden="true">
          {ZONAS.map((zona) => (
            <a
              key={zona.id}
              href={zona.ruta}
              className="armeria-poster__zona"
              data-zona={zona.id}
              data-activa={zona.id === zonaActiva}
              tabIndex={-1}
              onPointerEnter={() => acciones.apuntar(zona.id)}
              onPointerLeave={() => acciones.apuntar(null)}
              onClick={(e) => {
                e.preventDefault();
                acciones.abrir(zona.id);
              }}
            >
              <span className="armeria-poster__zona-nombre">{zona.nombre}</span>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

function Demo() {
  return (
    <span className="armeria__demo">
      Demo<span className="t6-sr"> (dato de ejemplo)</span>
    </span>
  );
}

export interface InterfazProps {
  prototipo: 'A' | 'B';
  descripcion: string;
  /** Técnica, entre paréntesis (se oculta en móvil). */
  tecnica: string;
  estado: EstadoArmeria;
  acciones: Acciones;
  /** Etiqueta flotante que la escena coloca sobre la zona activa. */
  etiqueta: RefObject<HTMLDivElement | null>;
  onSaltarIntro: () => void;
  /** El carrusel móvil informa de su posición (en zonas) para mover la cámara. */
  onProgreso?: (progreso: number) => void;
  /** Capa de la escena (canvas) o el póster. */
  children: ReactNode;
}

export function InterfazArmeria({
  prototipo,
  descripcion,
  tecnica,
  estado,
  acciones,
  etiqueta,
  onSaltarIntro,
  onProgreso,
  children,
}: InterfazProps) {
  const zonas = useRef<Record<string, HTMLAnchorElement | null>>({});
  const nav = useRef<HTMLElement>(null);
  const [foco, setFoco] = useState<string>(ZONAS[0]?.id ?? 'replicas');
  const abierta = zonaPorId(estado.zonaAbierta);
  const activa = zonaPorId(estado.zonaActiva);
  const volverA = useRef<string | null>(null);
  const panel = useRef<HTMLDivElement>(null);

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
    if (id) requestAnimationFrame(() => zonas.current[id]?.focus());
  }, [acciones]);

  // Esc: salta la intro o cierra el panel (docs/02 §3.2).
  useEffect(() => {
    const tecla = (e: globalThis.KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (estado.introActiva) onSaltarIntro();
      else if (estado.zonaAbierta) cerrar();
    };
    addEventListener('keydown', tecla);
    return () => removeEventListener('keydown', tecla);
  }, [estado.introActiva, estado.zonaAbierta, onSaltarIntro, cerrar]);

  // Al abrir una zona, el foco va al panel; el lector oye su nombre.
  useEffect(() => {
    if (estado.zonaAbierta) panel.current?.focus();
  }, [estado.zonaAbierta]);

  // ← y → recorren las zonas (un solo tabulador para toda la navegación: roving tabindex).
  const teclaZona = (e: KeyboardEvent<HTMLAnchorElement>, id: string) => {
    const i = ZONAS.findIndex((z) => z.id === id);
    let destino: number | null = null;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') destino = (i + 1) % ZONAS.length;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') destino = (i - 1 + ZONAS.length) % ZONAS.length;
    if (e.key === 'Home') destino = 0;
    if (e.key === 'End') destino = ZONAS.length - 1;
    if (destino === null) return;
    e.preventDefault();
    const z = ZONAS[destino];
    if (!z) return;
    setFoco(z.id);
    const el = zonas.current[z.id];
    el?.focus();
    if (estado.movil)
      el?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: estado.reducido ? 'auto' : 'smooth' });
  };

  // Carrusel móvil: la tarjeta centrada es la zona activa y su posición mueve la cámara.
  const desplazar = (e: UIEvent<HTMLElement>) => {
    if (!estado.movil) return;
    const el = e.currentTarget;
    const tarjetas = ZONAS.map((z) => zonas.current[z.id]).filter((t): t is HTMLAnchorElement => Boolean(t));
    const primera = tarjetas[0];
    const segunda = tarjetas[1];
    if (!primera || !segunda) return;
    const paso = segunda.offsetLeft - primera.offsetLeft || 1;
    const progreso = (el.scrollLeft + el.clientWidth / 2 - (primera.offsetLeft + primera.offsetWidth / 2)) / paso;
    onProgreso?.(progreso);
    const i = Math.round(Math.min(ZONAS.length - 1, Math.max(0, progreso)));
    const z = ZONAS[i];
    if (z && z.id !== estado.centrada) acciones.centrar(z.id);
  };

  return (
    <div
      className="armeria"
      data-prototipo={prototipo}
      data-movil={estado.movil}
      data-intro={estado.introActiva}
      data-abierta={Boolean(abierta)}
      data-luz={estado.variante}
    >
      <div className="armeria__escena">{children}</div>

      <div className="armeria__capa">
        <header className="armeria__cabecera">
          <a className="armeria__marca" href="/">
            {BRAND.name}
          </a>
          <p className="armeria__prototipo">
            <strong>Prototipo {prototipo}</strong> · {descripcion} <span className="armeria__tecnica">({tecnica})</span>
          </p>
          <fieldset className="armeria__ajustes">
            <legend className="t6-sr">Ajustes de la sala</legend>
            <button
              type="button"
              className="armeria__ajuste"
              aria-pressed={estado.variante === 'taller'}
              onClick={() => acciones.cambiarLuz(estado.variante === 'taller' ? 'penumbra' : 'taller')}
              title={`Luz: ${VARIANTES[estado.variante].nombre}`}
            >
              Luz cálida
            </button>
            <button
              type="button"
              className="armeria__ajuste"
              aria-pressed={estado.vista === 'ligera'}
              onClick={() => acciones.cambiarVista(estado.vista === 'ligera' ? 'escena' : 'ligera')}
            >
              Vista ligera
            </button>
          </fieldset>
        </header>

        {estado.lento ? (
          <p className="armeria__aviso" role="status">
            Tu equipo va justo con la sala en movimiento: te enseñamos la vista ligera.
          </p>
        ) : null}

        <nav className="armeria__nav" aria-label="Zonas de La Armería" ref={nav} onScroll={desplazar}>
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
                        zonas.current[z.id] = el;
                      }}
                      href={z.ruta}
                      className="armeria__zona"
                      data-activa={z.id === estado.zonaActiva}
                      tabIndex={z.id === foco ? 0 : -1}
                      aria-label={z.nombre}
                      aria-describedby={`armeria-dato-${z.id}`}
                      onFocus={() => {
                        setFoco(z.id);
                        acciones.enfocar(z.id);
                      }}
                      onBlur={() => acciones.enfocar(null)}
                      onPointerEnter={() => !estado.movil && acciones.apuntar(z.id)}
                      onPointerLeave={() => !estado.movil && acciones.apuntar(null)}
                      onKeyDown={(ev) => teclaZona(ev, z.id)}
                      onClick={(ev) => {
                        ev.preventDefault();
                        abrir(z.id);
                      }}
                    >
                      <span className="armeria__zona-estanteria" aria-hidden="true">
                        {ESTANTERIAS[e].titulo}
                      </span>
                      <span className="armeria__zona-nombre">{z.rotulo}</span>
                      <span className="armeria__zona-dato" id={`armeria-dato-${z.id}`}>
                        <span className="armeria__zona-dato-texto">{z.dato}</span>
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

      <div className="armeria__etiqueta" ref={etiqueta} aria-hidden="true" data-visible="false">
        {activa ? (
          <>
            <span className="armeria__etiqueta-nombre">{activa.nombre}</span>
            <span className="armeria__etiqueta-dato">
              {activa.dato} <span className="armeria__demo">Demo</span>
            </span>
          </>
        ) : null}
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

      {estado.introActiva ? (
        <button type="button" className="armeria__saltar" onClick={onSaltarIntro}>
          Saltar intro <kbd>Esc</kbd>
        </button>
      ) : null}
    </div>
  );
}
