// Hoja de contenido de un módulo de La Armería: se abre al elegir una zona (clic, Intro o «Monta tu réplica») y
// resume qué hay dentro con DATOS DE EJEMPLO marcados «Demo» (contenido-demo.ts). Reutiliza los componentes de
// /sistema (Placa, FichaPieza, Tabla, EtiquetaPrecio, Chip, Aviso…): ningún estilo propio para lo que ya existe.
// Cada hoja lleva título, un resumen con dato fechado y un enlace o acción a su sección futura (docs/10): mientras la
// fase no llega, la acción es un botón deshabilitado que lo explica (`aria-disabled`, sigue enfocable).
import {
  Aviso,
  Boton,
  BotonEnlace,
  Chip,
  EtiquetaPrecio,
  FichaPieza,
  formatearComprobado,
  formatearDato,
  InsigniaCompatibilidad,
  Placa,
  Tabla,
  Valoracion,
} from '@taller6mm/ui/componentes';
import { type ReactNode, type Ref, useId } from 'react';
import {
  ACCESORIOS_MUESTRA,
  ACCESORIOS_TOTAL,
  BAJADAS,
  BUILDS_TOP,
  COMPATIBILIDAD_EJEMPLO,
  FAMILIAS_PREVISTAS,
  frescura,
  GUIAS_MUESTRA,
  GUIAS_TOTAL,
  porcentajeBajada,
  RANURAS_BANCO,
  RESUMENES,
  TAQUILLA_SIN_SESION,
  TIENDAS,
} from './contenido-demo.ts';
import { Demo } from './Demo.tsx';
import { socketsDe } from './sockets.ts';
import type { Zona } from './zonas.ts';

/** Última fase del roadmap que está construida: una sección con `fase` mayor aún no existe (docs/10). */
export const FASE_ACTUAL = 1;

const ACCION: Readonly<Record<string, string>> = {
  replicas: 'Abrir el armero',
  accesorios: 'Abrir el almacén',
  comunidad: 'Ver la comunidad',
  banco: 'Abrir el banco',
  mercado: 'Abrir el mercado',
  tiendas: 'Ver las tiendas',
  guias: 'Abrir los manuales',
  taquilla: 'Abrir mi taquilla',
};

/** Fecha de una comprobación en absoluto («el 26 nov 2026, 19:40»): la página está prerenderizada y no caduca. */
function Fecha({ iso, prefijo = 'Comprobado' }: { iso: string | null; prefijo?: string }) {
  const comp = iso ? formatearComprobado(iso) : null;
  if (!comp) return <span className="armeria__fecha armeria__fecha--sin">Sin fecha de comprobación</span>;
  return (
    <span className="armeria__fecha">
      {prefijo ? `${prefijo} ` : null}
      <time dateTime={comp.iso} title={comp.completo}>
        {comp.texto}
      </time>
    </span>
  );
}

function Seccion({ titulo, children }: { titulo: string; children: ReactNode }) {
  const id = useId();
  return (
    <section className="armeria__hoja-seccion" aria-labelledby={id}>
      <h3 id={id} className="armeria__hoja-subtitulo">
        {titulo}
      </h3>
      {children}
    </section>
  );
}

// ── Cuerpos de cada módulo ──────────────────────────────────────────────────────────────────────

function CuerpoArmero() {
  const ranuras = socketsDe('replicas');
  const publicadas = ranuras.filter((r) => r.replicaId !== null).length;
  return (
    <>
      {publicadas === 0 ? (
        <Aviso tipo="provisional" titulo="Aún no hay réplicas publicadas">
          Cada réplica entrará con sus medidas en mm, su fuente y su nivel de fidelidad (T0 a T3). Hasta entonces, las
          ranuras del armero están libres y listas.
        </Aviso>
      ) : null}
      <Seccion titulo="Ranuras del armero">
        <ol className="armeria__ranuras">
          {ranuras.map((r, i) => (
            <li key={r.id} className="armeria__ranura" data-libre={r.replicaId === null}>
              <span aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
              <span className="t6-sr">
                Ranura {i + 1}: {r.replicaId === null ? 'libre' : r.replicaId}
              </span>
            </li>
          ))}
        </ol>
      </Seccion>
      <Seccion titulo="Familias previstas">
        <ul className="armeria__lista-simple">
          {FAMILIAS_PREVISTAS.map((f) => (
            <li key={f.id} className="armeria__fila">
              <span className="armeria__fila-nombre">{f.nombre}</span>
              <span className="armeria__fila-meta">{f.tipo}</span>
              <Chip tono="desconocido">Sin ficha</Chip>
            </li>
          ))}
        </ul>
      </Seccion>
    </>
  );
}

function CuerpoAccesorios() {
  return (
    <Seccion titulo={`Muestra: ${ACCESORIOS_MUESTRA.length} de ${ACCESORIOS_TOTAL}`}>
      <ul className="armeria__fichas">
        {ACCESORIOS_MUESTRA.map((a) => (
          <li key={a.id}>
            <FichaPieza
              nombre={a.nombre}
              marca={a.categoria}
              nivel="T0"
              medidas={a.medidas}
              precio={a.centimos === null ? null : { centimos: a.centimos, comprobado: a.comprobado }}
              tiendas={a.tiendas}
              nivelTitulo={4}
            />
          </li>
        ))}
      </ul>
    </Seccion>
  );
}

function CuerpoComunidad() {
  return (
    <Seccion titulo="Builds más valoradas">
      <ol className="armeria__builds">
        {BUILDS_TOP.map((b, i) => (
          <li key={b.id} className="armeria__build">
            <span className="armeria__build-puesto" aria-hidden="true">
              {i + 1}
            </span>
            <div className="armeria__build-cuerpo">
              <h4 className="armeria__build-nombre">
                <span className="t6-sr">Puesto {i + 1}: </span>
                {b.nombre}
              </h4>
              <p className="armeria__fila-meta">
                Base {b.base} · {b.piezas} piezas · {b.autor}
              </p>
              <Valoracion nota={b.nota} opiniones={b.opiniones} />
              <EtiquetaPrecio compacta centimos={b.centimos} comprobado={b.comprobado} stock="desconocido" />
            </div>
          </li>
        ))}
      </ol>
    </Seccion>
  );
}

function CuerpoBanco() {
  const { veredicto, motivo, fuente, confianza } = COMPATIBILIDAD_EJEMPLO;
  return (
    <>
      <Aviso tipo="info" titulo="Todavía no tienes ninguna build en curso">
        Aquí verás «Continúa tu build» en cuanto montes una réplica. Cada pieza se comprueba contra la ranura que ocupa.
      </Aviso>
      <Seccion titulo="Ranuras de una réplica larga">
        <ul className="armeria__lista-simple">
          {RANURAS_BANCO.map((r) => (
            <li key={r.id} className="armeria__fila">
              <span className="armeria__fila-nombre">{r.nombre}</span>
              <Chip tono="neutro" sinIcono>
                Libre
              </Chip>
            </li>
          ))}
        </ul>
      </Seccion>
      <Seccion titulo="Qué encaja y por qué">
        <InsigniaCompatibilidad veredicto={veredicto} motivo={motivo} fuente={fuente} confianza={confianza} />
      </Seccion>
    </>
  );
}

function CuerpoMercado() {
  return (
    <Seccion titulo="Bajadas de precio">
      <ul className="armeria__bajadas">
        {BAJADAS.map((b) => (
          <li key={b.id} className="armeria__bajada">
            <div className="armeria__bajada-cabecera">
              <h4 className="armeria__build-nombre">{b.pieza}</h4>
              <Chip tono="ok" sinIcono>
                <span aria-hidden="true">↓ {porcentajeBajada(b)} %</span>
                <span className="t6-sr">Bajada del {porcentajeBajada(b)} %</span>
              </Chip>
            </div>
            <p className="armeria__fila-meta">
              Antes <del>{formatearDato(b.antes, 'eur')}</del>
            </p>
            <EtiquetaPrecio centimos={b.ahora} tienda={b.tienda} comprobado={b.comprobado} stock={b.stock} />
          </li>
        ))}
      </ul>
    </Seccion>
  );
}

const TONO_FRESCURA = { 'al-dia': 'ok', desfasada: 'aviso', 'sin-comprobar': 'desconocido' } as const;
const TEXTO_FRESCURA = { 'al-dia': 'Al día', desfasada: 'Desfasada', 'sin-comprobar': 'Sin comprobar' } as const;

function CuerpoTiendas() {
  return (
    <Tabla
      titulo="Tiendas de ejemplo y frescura de sus datos"
      columnas={[
        { id: 'tienda', titulo: 'Tienda' },
        { id: 'via', titulo: 'Origen' },
        { id: 'comprobado', titulo: 'Comprobado' },
        { id: 'estado', titulo: 'Estado' },
      ]}
      filas={TIENDAS.map((t) => {
        const f = frescura(t.comprobado);
        return {
          id: t.id,
          celdas: {
            tienda: (
              <>
                {t.nombre}
                <span className="armeria__fila-meta armeria__bloque">{t.pais}</span>
              </>
            ),
            via: t.via,
            comprobado: <Fecha iso={t.comprobado} prefijo="" />,
            estado: <Chip tono={TONO_FRESCURA[f]}>{TEXTO_FRESCURA[f]}</Chip>,
          },
        };
      })}
    />
  );
}

function CuerpoGuias() {
  return (
    <Seccion titulo={`Muestra: ${GUIAS_MUESTRA.length} de ${GUIAS_TOTAL}`}>
      <ul className="armeria__lista-simple">
        {GUIAS_MUESTRA.map((g) => (
          <li key={g.id} className="armeria__fila armeria__fila--apilada">
            <span className="armeria__fila-nombre">{g.titulo}</span>
            <span className="armeria__fila-meta">
              {g.tema} · <Fecha iso={g.revisada} prefijo="revisada" />
            </span>
          </li>
        ))}
      </ul>
    </Seccion>
  );
}

function CuerpoTaquilla() {
  const t = TAQUILLA_SIN_SESION;
  return (
    <>
      <Aviso tipo="info" titulo="Inicia sesión para abrir tu taquilla">
        Tus builds, favoritos y alertas de precio estarán aquí. Se podrá entrar con enlace mágico, Google, Discord o
        passkey.
      </Aviso>
      <Seccion titulo="Lo que guardarás">
        <dl className="armeria__cifras">
          <div>
            <dt>Builds guardadas</dt>
            <dd>{t.builds}</dd>
          </div>
          <div>
            <dt>Favoritos</dt>
            <dd>{t.favoritos}</dd>
          </div>
          <div>
            <dt>Alertas de precio</dt>
            <dd>{t.alertas}</dd>
          </div>
        </dl>
      </Seccion>
    </>
  );
}

const CUERPOS: Readonly<Record<string, () => ReactNode>> = {
  replicas: CuerpoArmero,
  accesorios: CuerpoAccesorios,
  comunidad: CuerpoComunidad,
  banco: CuerpoBanco,
  mercado: CuerpoMercado,
  tiendas: CuerpoTiendas,
  guias: CuerpoGuias,
  taquilla: CuerpoTaquilla,
};

export interface HojaProps {
  zona: Zona;
  onCerrar: () => void;
  panelRef: Ref<HTMLDivElement>;
}

export function Hoja({ zona, onCerrar, panelRef }: HojaProps) {
  const notaId = useId();
  const Cuerpo = CUERPOS[zona.id];
  const resumen = RESUMENES[zona.id];
  const disponible = zona.fase <= FASE_ACTUAL;
  const accion = ACCION[zona.id] ?? 'Abrir';
  return (
    <div
      className="armeria__hoja"
      data-zona={zona.id}
      data-lado={zona.estanteria === 'derecha' ? 'izquierda' : 'derecha'}
      role="dialog"
      aria-modal="false"
      aria-label={zona.nombre}
      tabIndex={-1}
      ref={panelRef}
    >
      <Placa titulo={zona.nombre} nivelTitulo={2} codigo={zona.ruta} as="div">
        <p className="armeria__hoja-descripcion">{zona.descripcion}</p>
        {resumen ? (
          <p className="armeria__hoja-resumen">
            <strong className="armeria__hoja-dato">{resumen.texto}</strong>
            <Demo />
            <Fecha iso={resumen.comprobado} />
          </p>
        ) : null}
        {Cuerpo ? <Cuerpo /> : null}
        <div className="armeria__hoja-acciones">
          {disponible ? (
            <BotonEnlace variante="laton" href={zona.ruta}>
              {accion}
            </BotonEnlace>
          ) : (
            <Boton variante="laton" aria-disabled="true" aria-describedby={notaId}>
              {accion}
            </Boton>
          )}
          <Boton variante="fantasma" onClick={onCerrar}>
            Volver a la sala
          </Boton>
          {disponible ? null : (
            <p id={notaId} className="armeria__hoja-nota">
              Esta sección ({zona.ruta}) llega en la Fase {zona.fase}.
            </p>
          )}
        </div>
      </Placa>
    </div>
  );
}
