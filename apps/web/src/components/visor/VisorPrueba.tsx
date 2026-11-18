// Visor de prueba (germen de El Banco, no El Banco): carga los GLB de las piezas y de los montajes M4,
// con órbita, zoom, selector de modelo y selector de iluminación. Todo es T0 y de demostración.
// Isla `client:only="react"`: sin JS no hay escena, pero el panel y la ficha son HTML (alternativa
// ligera, docs/02 §3.6): el selector y la ficha de cada pieza no dependen de WebGL.
import {
  Boton,
  Cargador,
  InsigniaFidelidad,
  NIVELES_FIDELIDAD,
  type NivelFidelidad,
  Placa,
  Rotulo,
} from '@taller6mm/ui/componentes';
import {
  type ChangeEvent,
  type KeyboardEvent,
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { Object3D } from 'three';
import type { ApiVista } from './Escena.tsx';
import type { ConjuntoPresets } from './iluminacion.ts';
import {
  BASE_VISOR,
  cargarIndice,
  cargarMateriales,
  cargarPresetsExternos,
  formatearBytes,
  type IndiceVisor,
  type MaterialesVisor,
  type MontajeIndice,
  type PiezaIndice,
} from './modelos.ts';
import { PRESETS_MINIMOS } from './presets-minimos.ts';

// three y R3F van en su propio trozo: la ficha y los selectores se pintan sin esperar al 3D.
const Escena = lazy(() => import('./Escena.tsx'));

const PASO_GIRO = (15 * Math.PI) / 180;

type Seleccion = { tipo: 'montaje' | 'pieza'; id: string };
const aValor = (s: Seleccion) => `${s.tipo}:${s.id}`;
const deValor = (v: string): Seleccion | null => {
  const [tipo, ...resto] = v.split(':');
  return (tipo === 'montaje' || tipo === 'pieza') && resto.length > 0 ? { tipo, id: resto.join(':') } : null;
};

/** Nombre del material de la biblioteca asignado a una pieza, o la razón por la que no se ve. */
function nombreMaterial(doc: MaterialesVisor | null, clave: string): string {
  const a = doc?.asignaciones[clave];
  const m = a ? doc?.materiales[a.material] : undefined;
  if (!a || !m) return doc ? 'sin material asignado' : 'cargando materiales…';
  return a.cubierta ? m.nombre : `${m.nombre} (por defecto: sin regla en el catálogo)`;
}

const num = (n: number, dec = 0) =>
  n.toLocaleString('es-ES', { maximumFractionDigits: dec, minimumFractionDigits: dec });
const esNivel = (n: string): n is NivelFidelidad => Object.hasOwn(NIVELES_FIDELIDAD, n);

function usarMovimientoReducido(): boolean {
  const [reducido, setReducido] = useState(false);
  useEffect(() => {
    const q = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducido(q.matches);
    const al = (e: MediaQueryListEvent) => setReducido(e.matches);
    q.addEventListener('change', al);
    return () => q.removeEventListener('change', al);
  }, []);
  return reducido;
}

function hayWebGL(): boolean {
  try {
    const c = document.createElement('canvas');
    return Boolean(c.getContext('webgl2') ?? c.getContext('webgl'));
  } catch {
    return false;
  }
}

type EstadoModelo =
  | { fase: 'inactivo' }
  | { fase: 'cargando' }
  | { fase: 'error'; mensaje: string }
  | {
      fase: 'listo';
      objeto: Object3D;
      caja: { largo: number; alto: number; ancho: number };
      mallas: number;
      /** Clave de asignación de materiales de cada pieza del modelo, fijada al cargarlo. */
      claveDe: ClaveDe;
    };

type ModeloListo = Extract<EstadoModelo, { fase: 'listo' }>;
type ClaveDe = (rol: string | null) => string | null;

/**
 * Carga el GLB elegido. Devuelve también el último modelo listo: la escena sigue pintándolo mientras llega
 * el siguiente, así el lienzo (y su contexto WebGL) no se destruye en cada cambio. De liberar el modelo
 * que se sustituye se ocupa la escena.
 */
function usarModelo(archivo: string | null, claveDe: ClaveDe): { estado: EstadoModelo; mostrado: ModeloListo | null } {
  const [estado, setEstado] = useState<EstadoModelo>({ fase: 'inactivo' });
  const [mostrado, setMostrado] = useState<ModeloListo | null>(null);
  const claveRef = useRef(claveDe);
  claveRef.current = claveDe;
  useEffect(() => {
    if (!archivo) return;
    let vigente = true;
    setEstado({ fase: 'cargando' });
    import('./cargarGlb.ts')
      .then(async (m) => ({ m, r: await m.cargarGlb(`${BASE_VISOR}${archivo}`) }))
      .then(({ m, r }) => {
        if (!vigente) return m.liberarModelo(r.objeto);
        const listo: ModeloListo = {
          fase: 'listo',
          objeto: r.objeto,
          caja: r.caja,
          mallas: r.mallas,
          claveDe: claveRef.current,
        };
        setEstado(listo);
        setMostrado(listo);
      })
      .catch((e: unknown) => {
        if (vigente) setEstado({ fase: 'error', mensaje: e instanceof Error ? e.message : 'error desconocido' });
      });
    return () => {
      vigente = false;
    };
  }, [archivo]);
  return { estado, mostrado };
}

export default function VisorPrueba() {
  const idSelector = useId();
  const idAyuda = useId();
  const idBrillo = useId();
  const reducido = usarMovimientoReducido();
  const [webgl] = useState(() => (typeof document === 'undefined' ? true : hayWebGL()));
  const [indice, setIndice] = useState<IndiceVisor | null>(null);
  const [errorIndice, setErrorIndice] = useState<string | null>(null);
  const [conjunto, setConjunto] = useState<ConjuntoPresets>(PRESETS_MINIMOS);
  const [origenPresets, setOrigenPresets] = useState<string>('copia mínima del visor');
  const [materiales, setMateriales] = useState<MaterialesVisor | null>(null);
  const [errorMateriales, setErrorMateriales] = useState<string | null>(null);
  const [seleccion, setSeleccion] = useState<Seleccion | null>(null);
  const [presetId, setPresetId] = useState<string>(PRESETS_MINIMOS.defecto);
  const [brillo, setBrillo] = useState<number>(PRESETS_MINIMOS.brillo.global.defecto);
  const apiRef = useRef<ApiVista | null>(null);

  // Índice de modelos y, si existen, los presets del catálogo.
  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const ind = await cargarIndice(ac.signal);
        setIndice(ind);
        const url = new URLSearchParams(window.location.search).get('modelo');
        const inicial = url ? deValor(url) : null;
        setSeleccion(inicial ?? (ind.montajes[0] ? { tipo: 'montaje', id: ind.montajes[0].id } : null));
        cargarMateriales(ac.signal).then(setMateriales, (e: unknown) => {
          if (!ac.signal.aborted) setErrorMateriales(e instanceof Error ? e.message : 'error desconocido');
        });
        if (ind.presets_externos) {
          const p = await cargarPresetsExternos(ind.presets_externos, ac.signal);
          if (p.valor) {
            setConjunto(p.valor);
            setPresetId(p.valor.defecto);
            setBrillo(p.valor.brillo.global.defecto);
            setOrigenPresets('catalogo/iluminacion-presets.json');
          } else {
            setOrigenPresets(`copia mínima del visor (el catálogo no vale: ${p.error})`);
          }
        }
        const luz = new URLSearchParams(window.location.search).get('luz');
        if (luz) setPresetId(luz);
      } catch (e) {
        if (!ac.signal.aborted) setErrorIndice(e instanceof Error ? e.message : 'error desconocido');
      }
    })();
    return () => ac.abort();
  }, []);

  const montaje = useMemo<MontajeIndice | null>(
    () => (seleccion?.tipo === 'montaje' ? (indice?.montajes.find((m) => m.id === seleccion.id) ?? null) : null),
    [indice, seleccion],
  );
  const pieza = useMemo<PiezaIndice | null>(
    () => (seleccion?.tipo === 'pieza' ? (indice?.piezas.find((p) => p.id === seleccion.id) ?? null) : null),
    [indice, seleccion],
  );
  const preset = conjunto.presets.find((p) => p.id === presetId) ?? conjunto.presets[0];
  // Clave de asignación de materiales por pieza: `pieza` suelta o `montaje/pieza` (la fija el exportador).
  const claveDe = useMemo<ClaveDe>(() => {
    if (montaje) {
      const porRol = new Map(montaje.piezas.map((p) => [p.rol, `${montaje.id}/${p.id}`]));
      return (rol) => (rol ? (porRol.get(rol) ?? null) : null);
    }
    const id = pieza?.id ?? null;
    return () => id;
  }, [montaje, pieza]);
  const { estado: modelo, mostrado } = usarModelo(montaje?.archivo ?? pieza?.archivo ?? null, claveDe);

  const grupos = useMemo(() => {
    const m = new Map<string, PiezaIndice[]>();
    for (const p of indice?.piezas ?? []) m.set(p.grupo, [...(m.get(p.grupo) ?? []), p]);
    return [...m.entries()];
  }, [indice]);

  const alCambiarModelo = (e: ChangeEvent<HTMLSelectElement>) => {
    const s = deValor(e.target.value);
    if (s) setSeleccion(s);
  };

  const alTeclear = useCallback((e: KeyboardEvent<HTMLElement>) => {
    const api = apiRef.current;
    if (!api || e.altKey || e.ctrlKey || e.metaKey) return;
    const acciones: Record<string, () => void> = {
      ArrowLeft: () => api.girar(-PASO_GIRO, 0),
      ArrowRight: () => api.girar(PASO_GIRO, 0),
      ArrowUp: () => api.girar(0, -PASO_GIRO),
      ArrowDown: () => api.girar(0, PASO_GIRO),
      '+': () => api.acercar(0.85),
      '=': () => api.acercar(0.85),
      '-': () => api.acercar(1 / 0.85),
      '0': () => api.reiniciar(),
      Home: () => api.reiniciar(),
    };
    const accion = acciones[e.key];
    if (accion) {
      e.preventDefault();
      accion();
    }
  }, []);

  const nombre = montaje?.nombre ?? pieza?.nombre ?? pieza?.id ?? '';
  const nivel = montaje?.nivel ?? pieza?.nivel ?? null;
  const esDemo = montaje?.es_demo ?? pieza?.es_demo ?? true;
  const triangulos = montaje?.triangulos ?? pieza?.triangulos ?? 0;
  const bytes = montaje?.bytes ?? pieza?.bytes ?? 0;
  const marcadores = montaje?.piezas.filter((p) => !p.tiene_malla) ?? [];

  return (
    <div className="t6-visor">
      <header className="t6-visor__cabecera">
        <Rotulo as="p" tinta="laton" tamano="s">
          Prototipo · germen de El Banco
        </Rotulo>
        <h1 className="t6-visor__titulo">Visor de prueba</h1>
        <p className="t6-visor__aviso">
          Modelos T0 de demostración generados por código: sirven para probar la luz y la cámara, no son la réplica de
          ningún fabricante ni se publican.
        </p>
      </header>

      <div className="t6-visor__cuerpo">
        <section className="t6-visor__escena" aria-label="Escena 3D">
          <div
            className="t6-visor__lienzo"
            role="application"
            aria-roledescription="visor 3D"
            aria-label={nombre ? `Visor 3D: ${nombre}` : 'Visor 3D'}
            aria-describedby={idAyuda}
            // biome-ignore lint/a11y/noNoninteractiveTabindex: el lienzo 3D es un control con teclado propio (flechas, + y -)
            tabIndex={0}
            onKeyDown={alTeclear}
            data-fase={modelo.fase}
          >
            {webgl && mostrado && modelo.fase !== 'error' && preset ? (
              <Suspense fallback={null}>
                <Escena
                  objeto={mostrado.objeto}
                  preset={preset}
                  control={conjunto.brillo}
                  brillo={brillo}
                  reducido={reducido}
                  materiales={materiales}
                  claveDe={mostrado.claveDe}
                  apiRef={apiRef}
                />
              </Suspense>
            ) : null}
            {modelo.fase === 'cargando' || modelo.fase === 'inactivo' ? (
              <div className="t6-visor__estado">
                <Cargador etiqueta="Cargando el modelo…" />
              </div>
            ) : null}
            {!webgl ? (
              <p className="t6-visor__estado t6-visor__estado--texto" role="status">
                Este navegador no puede pintar 3D (WebGL). La ficha de la derecha tiene los mismos datos del modelo.
              </p>
            ) : null}
            {errorMateriales ? (
              <p className="t6-visor__estado t6-visor__estado--texto t6-visor__estado--arriba" role="status">
                Sin materiales de la biblioteca ({errorMateriales}): se ve el material básico del GLB.
              </p>
            ) : null}
            {errorIndice ? (
              <p className="t6-visor__estado t6-visor__estado--texto" role="alert">
                No hay modelos de desarrollo ({errorIndice}). Genéralos con{' '}
                <code>node apps/web/scripts/prototipos/visor-preparar.mjs</code>.
              </p>
            ) : null}
            {modelo.fase === 'error' ? (
              <p className="t6-visor__estado t6-visor__estado--texto" role="alert">
                No se pudo cargar el modelo: {modelo.mensaje}.
              </p>
            ) : null}
          </div>
          <p id={idAyuda} className="t6-visor__ayuda">
            Arrastra para girar y usa la rueda o el pellizco para acercar. Con el visor enfocado: flechas para girar,{' '}
            <kbd>+</kbd> y <kbd>-</kbd> para acercar, <kbd>0</kbd> para volver a la vista inicial.
          </p>
          <div className="t6-visor__barra" role="toolbar" aria-label="Vista">
            <Boton aria-label="Girar a la izquierda" onClick={() => apiRef.current?.girar(-PASO_GIRO, 0)}>
              ←
            </Boton>
            <Boton aria-label="Girar a la derecha" onClick={() => apiRef.current?.girar(PASO_GIRO, 0)}>
              →
            </Boton>
            <Boton aria-label="Girar hacia arriba" onClick={() => apiRef.current?.girar(0, -PASO_GIRO)}>
              ↑
            </Boton>
            <Boton aria-label="Girar hacia abajo" onClick={() => apiRef.current?.girar(0, PASO_GIRO)}>
              ↓
            </Boton>
            <Boton aria-label="Acercar" onClick={() => apiRef.current?.acercar(0.8)}>
              +
            </Boton>
            <Boton aria-label="Alejar" onClick={() => apiRef.current?.acercar(1.25)}>
              −
            </Boton>
            <Boton variante="fantasma" onClick={() => apiRef.current?.reiniciar()}>
              Vista inicial
            </Boton>
          </div>
        </section>

        <div className="t6-visor__panel">
          <Placa titulo="Modelo" nivelTitulo={2} lisa as="section">
            <div className="t6-visor__campo">
              <label htmlFor={idSelector} className="t6-visor__etiqueta">
                Montaje o pieza
              </label>
              <select
                id={idSelector}
                className="t6-visor__selector"
                value={seleccion ? aValor(seleccion) : ''}
                onChange={alCambiarModelo}
                disabled={!indice}
              >
                {indice ? (
                  <>
                    <optgroup label="Montajes M4 completos">
                      {indice.montajes.map((m) => (
                        <option key={m.id} value={aValor({ tipo: 'montaje', id: m.id })}>
                          {m.nombre}
                        </option>
                      ))}
                    </optgroup>
                    {grupos.map(([grupo, piezas]) => (
                      <optgroup key={grupo} label={grupo}>
                        {piezas.map((p) => (
                          <option key={p.id} value={aValor({ tipo: 'pieza', id: p.id })}>
                            {p.id}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </>
                ) : (
                  <option value="">Cargando modelos…</option>
                )}
              </select>
            </div>
          </Placa>

          <Placa titulo="Iluminación" nivelTitulo={2} lisa as="section">
            <fieldset className="t6-visor__luces">
              <legend className="t6-visor__etiqueta">Luz de la escena</legend>
              <div className="t6-visor__opciones">
                {conjunto.presets.map((p) => (
                  <label key={p.id} className="t6-visor__opcion">
                    <input
                      type="radio"
                      name="luz"
                      value={p.id}
                      checked={preset?.id === p.id}
                      onChange={() => setPresetId(p.id)}
                    />
                    <span>{p.nombre}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            {preset ? <p className="t6-visor__descripcion">{preset.descripcion}</p> : null}
            <div className="t6-visor__campo">
              <label htmlFor={idBrillo} className="t6-visor__etiqueta">
                Brillo <output htmlFor={idBrillo}>{num(brillo, 2)}×</output>
              </label>
              <input
                id={idBrillo}
                className="t6-visor__rango"
                type="range"
                min={conjunto.brillo.global.min}
                max={conjunto.brillo.global.max}
                step={0.05}
                value={brillo}
                onChange={(e) => setBrillo(Number(e.target.value))}
              />
              <Boton variante="fantasma" onClick={() => setBrillo(conjunto.brillo.global.max)}>
                Más luz
              </Boton>
            </div>
            <p className="t6-visor__nota">Presets de luz: {origenPresets}.</p>
          </Placa>

          <Placa titulo="Ficha" nivelTitulo={2} lisa as="section">
            <div role="status" aria-live="polite" className="t6-visor__ficha">
              {nombre ? <p className="t6-visor__nombre">{nombre}</p> : null}
              {nivel ? (
                <p>
                  <InsigniaFidelidad nivel={esNivel(nivel) ? nivel : null} />
                </p>
              ) : null}
              {esDemo ? (
                <p className="t6-visor__nota">
                  De demostración (parámetros de barrido): no es la medida de ningún modelo comercial. No publicable en
                  3D.
                </p>
              ) : null}
              {modelo.fase === 'listo' ? (
                <dl className="t6-visor__datos">
                  <div>
                    <dt>Caja de la malla</dt>
                    <dd>
                      {num(modelo.caja.largo)} × {num(modelo.caja.alto)} × {num(modelo.caja.ancho)} mm
                    </dd>
                  </div>
                  <div>
                    <dt>Triángulos</dt>
                    <dd>{num(triangulos)}</dd>
                  </div>
                  <div>
                    <dt>Peso del GLB (Meshopt)</dt>
                    <dd>{formatearBytes(bytes)}</dd>
                  </div>
                </dl>
              ) : null}
              {montaje?.aviso ? <p className="t6-visor__nota">{montaje.aviso}</p> : null}
            </div>

            {montaje ? (
              <details className="t6-visor__detalle" open>
                <summary>Piezas del montaje ({montaje.piezas.length})</summary>
                <ul className="t6-visor__lista">
                  {montaje.piezas.map((p) => (
                    <li key={p.id}>
                      <span className="t6-visor__rol">{p.rol.replaceAll('_', ' ')}</span>
                      <span className="t6-visor__familia">{p.familia}</span>
                      {p.tiene_malla ? (
                        <span className="t6-visor__material">
                          {nombreMaterial(materiales, `${montaje.id}/${p.id}`)}
                        </span>
                      ) : (
                        <span className="t6-visor__marca">Pendiente: sin modelo ni cotas</span>
                      )}
                    </li>
                  ))}
                </ul>
                {marcadores.length > 0 ? (
                  <p className="t6-visor__nota">
                    Las piezas «pendiente» se dibujan como un fantasma rayado: son huecos del catálogo, no geometría
                    real, y no cuentan en las medidas.
                  </p>
                ) : null}
              </details>
            ) : null}

            {pieza ? (
              <>
                <p className="t6-visor__nota">Familia: {pieza.familia ?? 'sin familia'}</p>
                <p className="t6-visor__nota">Material: {nombreMaterial(materiales, pieza.id)}</p>
                {pieza.cotas.length > 0 ? (
                  <details className="t6-visor__detalle">
                    <summary>Cotas y confianza ({pieza.cotas.length})</summary>
                    <table className="t6-visor__tabla">
                      <thead>
                        <tr>
                          <th scope="col">Cota</th>
                          <th scope="col">Valor</th>
                          <th scope="col">Confianza</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pieza.cotas.map((c) => (
                          <tr key={c.clave}>
                            <th scope="row">{c.clave}</th>
                            <td>{c.valor_mm === null ? 'desconocido' : `${num(c.valor_mm, 2)} mm`}</td>
                            <td>{c.confianza}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </details>
                ) : null}
                {pieza.notas.length > 0 ? (
                  <details className="t6-visor__detalle">
                    <summary>Límites del modelo ({pieza.notas.length})</summary>
                    <ul className="t6-visor__lista t6-visor__lista--notas">
                      {pieza.notas.map((n) => (
                        <li key={n}>{n}</li>
                      ))}
                    </ul>
                  </details>
                ) : null}
              </>
            ) : null}
          </Placa>
        </div>
      </div>
    </div>
  );
}
