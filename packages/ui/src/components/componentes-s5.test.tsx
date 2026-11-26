// @vitest-environment happy-dom
// Componentes de la rebanada S5: render en servidor y, en los interactivos, comportamiento de teclado.
import { act } from 'react';
import { createRoot } from 'react-dom/client';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, test } from 'vitest';
import {
  Aviso,
  Campo,
  Chip,
  EtiquetaPrecio,
  FichaPieza,
  InsigniaCompatibilidad,
  Pestanas,
  PuntoStock,
  Selector,
  Tabla,
  Tooltip,
  Tostadas,
  Valoracion,
} from './index.ts';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const html = (node: React.ReactNode) => renderToStaticMarkup(node);
const doc = (node: React.ReactNode) => {
  const template = document.createElement('template');
  template.innerHTML = html(node);
  return template.content;
};
const montar = async (node: React.ReactNode) => {
  const host = document.createElement('div');
  document.body.append(host);
  const root = createRoot(host);
  await act(async () => root.render(node));
  return { host, root };
};

describe('Campo y Selector', () => {
  test('etiqueta enlazada, ayuda y error en aria-describedby, aria-invalid', () => {
    const root = doc(<Campo etiqueta="Calibre" ayuda="En mm, p. ej. 6,03" error="Introduce un número." />);
    const input = root.querySelector('input');
    expect(root.querySelector('label')?.getAttribute('for')).toBe(input?.id);
    expect(input?.getAttribute('aria-invalid')).toBe('true');
    for (const id of (input?.getAttribute('aria-describedby') ?? '').split(' ')) {
      expect(root.querySelector(`[id="${id}"]`)).not.toBeNull();
    }
  });

  test('deshabilitado, obligatorio, multilínea y carga', () => {
    expect(html(<Campo etiqueta="Nombre" disabled />)).toContain('disabled=""');
    expect(html(<Campo etiqueta="Nombre" required />)).toContain('(obligatorio)');
    expect(html(<Campo etiqueta="Notas" multilinea />)).toContain('<textarea');
    const carga = doc(<Campo etiqueta="Código" cargando />);
    expect(carga.querySelector('input')?.getAttribute('aria-busy')).toBe('true');
    expect(carga.querySelector('[role="status"]')?.textContent).toBe('Comprobando…');
  });

  test('Selector nativo con marcador y opción deshabilitada', () => {
    const root = doc(
      <Selector
        etiqueta="Plataforma"
        marcador="Elige una"
        opciones={[
          { valor: 'm4', texto: 'M4' },
          { valor: 'ak', texto: 'AK', deshabilitada: true },
        ]}
      />,
    );
    expect(root.querySelectorAll('option')).toHaveLength(3);
    expect(root.querySelector('option[disabled]')?.textContent).toBe('AK');
  });
});

describe('Chip, stock y aviso', () => {
  test('los tonos de estado llevan icono; el neutro no', () => {
    expect(html(<Chip tono="ok">Compatible</Chip>)).toContain('<svg');
    expect(html(<Chip>Marca</Chip>)).not.toContain('<svg');
  });

  test.each(['en-stock', 'pocas', 'agotado', 'desconocido'] as const)('stock %s: texto e icono', (estado) => {
    const root = doc(<PuntoStock estado={estado} />);
    expect(root.textContent?.length).toBeGreaterThan(5);
    expect(root.querySelector('svg')).not.toBeNull();
  });

  test('aviso estático es note; vivo es status o alert', () => {
    expect(html(<Aviso titulo="Provisional" tipo="provisional" />)).toContain('role="note"');
    expect(html(<Aviso titulo="Ok" tipo="ok" viva />)).toContain('role="status"');
    expect(html(<Aviso titulo="Fallo" tipo="error" viva />)).toContain('role="alert"');
  });
});

describe('Etiqueta de precio', () => {
  test('precio con fecha de comprobación y stock', () => {
    const root = doc(
      <EtiquetaPrecio
        centimos={8995}
        tienda="Tienda de ejemplo"
        comprobado="2026-10-31T15:12:00Z"
        ahora="2026-10-31T18:00:00Z"
        stock="en-stock"
      />,
    );
    expect(root.querySelector('data')?.getAttribute('value')).toBe('8995');
    expect(root.querySelector('time')?.getAttribute('datetime')).toBe('2026-10-31T15:12:00.000Z');
    expect(root.textContent).toContain('hace 2');
    expect(root.textContent).toContain('En stock');
  });

  test('sin precio ni fecha se dice, no se inventa', () => {
    const root = doc(<EtiquetaPrecio centimos={null} tienda="X" comprobado={null} stock="desconocido" />);
    expect(root.textContent).toContain('Sin precio');
    expect(root.textContent).toContain('Sin fecha de comprobación');
    expect(root.querySelector('data')).toBeNull();
  });

  test('con href abre en pestaña nueva con rel seguro y lo avisa', () => {
    const root = doc(
      <EtiquetaPrecio centimos={100} tienda="X" comprobado={null} stock="agotado" href="https://example.com/p" />,
    );
    const a = root.querySelector('a');
    expect(a?.getAttribute('rel')).toBe('noopener noreferrer');
    expect(a?.textContent).toContain('pestaña nueva');
  });
});

describe('Insignia de compatibilidad', () => {
  const base = {
    motivo: 'Rosca CW frente a CCW.',
    fuente: { nombre: 'Ficha del fabricante' },
    confianza: 'alta',
  } as const;

  test('muestra veredicto, motivo, fuente y confianza', () => {
    const root = doc(<InsigniaCompatibilidad veredicto="adaptador" {...base} />);
    expect(root.textContent).toContain('Con adaptador');
    expect(root.textContent).toContain('Rosca CW frente a CCW.');
    expect(root.textContent).toContain('Ficha del fabricante');
    expect(root.textContent).toContain('Alta');
  });

  test('compacta: motivo, fuente y confianza para lectores de pantalla', () => {
    const root = doc(<InsigniaCompatibilidad veredicto="incompatible" compacta {...base} />);
    expect(root.querySelector('.t6-sr')?.textContent).toContain('Fuente: Ficha del fabricante');
  });
});

describe('Ficha de pieza', () => {
  const compat = {
    veredicto: 'compatible',
    motivo: 'Mismo estándar.',
    fuente: { nombre: 'Medida propia' },
    confianza: 'media',
  } as const;

  test('un solo enlace, nivel de fidelidad, precio con fecha y compatibilidad', () => {
    const root = doc(
      <FichaPieza
        nombre="Cargador M4 de 120 bolas"
        marca="Marca de ejemplo"
        href="/piezas/1"
        nivel="T1"
        precio={{ centimos: 1295, comprobado: '2026-10-31T15:12:00Z' }}
        tiendas={3}
        compatibilidad={compat}
      />,
    );
    expect(root.querySelectorAll('a')).toHaveLength(1);
    expect(root.textContent).toContain('T1');
    expect(root.textContent).toContain('desde');
    expect(root.querySelector('time')).not.toBeNull();
    expect(root.textContent).toContain('3 tiendas');
  });

  test('sin datos, carga y error', () => {
    const vacia = doc(<FichaPieza nombre="Pieza" marca="M" nivel={null} precio={null} tiendas={null} />);
    expect(vacia.textContent).toContain('Sin verificar');
    expect(vacia.textContent).toContain('Sin precio en ninguna tienda');
    expect(
      doc(<FichaPieza nombre="P" marca="M" nivel="T0" precio={null} tiendas={1} estado="carga" />).querySelector(
        '[aria-busy="true"]',
      ),
    ).not.toBeNull();
    expect(html(<FichaPieza nombre="P" marca="M" nivel="T0" precio={null} tiendas={1} estado="error" />)).toContain(
      'No se ha podido cargar',
    );
  });
});

describe('Tabla', () => {
  const columnas = [
    { id: 'nombre', titulo: 'Pieza' },
    { id: 'peso', titulo: 'Peso', numerica: true },
  ];

  test('caption, scope y primera columna como cabecera de fila', () => {
    const root = doc(
      <Tabla titulo="Piezas" columnas={columnas} filas={[{ id: 'a', celdas: { nombre: 'Mira', peso: '120 g' } }]} />,
    );
    expect(root.querySelector('caption')?.textContent).toBe('Piezas');
    expect(root.querySelectorAll('th[scope="col"]')).toHaveLength(2);
    expect(root.querySelector('tbody th')?.getAttribute('scope')).toBe('row');
    expect(root.querySelector('section')?.getAttribute('aria-labelledby')).toBe(root.querySelector('caption')?.id);
  });

  test('vacía, carga y error', () => {
    expect(html(<Tabla titulo="T" columnas={columnas} filas={[]} />)).toContain('No hay datos');
    expect(html(<Tabla titulo="T" columnas={columnas} filas={[]} estado="carga" />)).toContain('aria-busy="true"');
    expect(html(<Tabla titulo="T" columnas={columnas} filas={[]} estado="error" />)).toContain(
      'No se han podido cargar',
    );
  });
});

describe('Valoración', () => {
  test('con nota y sin opiniones', () => {
    expect(html(<Valoracion nota={4.5} opiniones={12} />)).toContain('Valoración 4,5 de 5, 12 opiniones');
    expect(html(<Valoracion nota={null} opiniones={0} />)).toContain('Sin opiniones todavía');
  });
});

describe('Pestañas (teclado)', () => {
  test('flechas, Inicio y Fin cambian la pestaña y saltan las desactivadas', async () => {
    const { host } = await montar(
      <Pestanas
        etiqueta="Secciones"
        pestanas={[
          { id: 'a', titulo: 'A', panel: 'Panel A' },
          { id: 'b', titulo: 'B', panel: 'Panel B', desactivada: true },
          { id: 'c', titulo: 'C', panel: 'Panel C' },
        ]}
      />,
    );
    const tabs = () => [...host.querySelectorAll<HTMLElement>('[role="tab"]')];
    expect(tabs().map((t) => t.getAttribute('tabindex'))).toEqual(['0', '-1', '-1']);
    await act(async () => {
      tabs()[0]?.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    });
    expect(tabs()[2]?.getAttribute('aria-selected')).toBe('true');
    expect(host.querySelector('[role="tabpanel"]:not([hidden])')?.textContent).toBe('Panel C');
    await act(async () => {
      tabs()[2]?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Home', bubbles: true }));
    });
    expect(tabs()[0]?.getAttribute('aria-selected')).toBe('true');
  });
});

describe('Tooltip', () => {
  test('el disparador queda descrito por el tooltip y Escape lo descarta', async () => {
    const { host } = await montar(
      <Tooltip texto="Rosca a derechas">
        <button type="button">CW</button>
      </Tooltip>,
    );
    const boton = host.querySelector('button');
    const tip = host.querySelector('[role="tooltip"]');
    expect(boton?.getAttribute('aria-describedby')).toBe(tip?.id);
    const envoltorio = host.querySelector<HTMLElement>('.t6-tooltip');
    await act(async () => {
      boton?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(envoltorio?.hasAttribute('data-descartado')).toBe(true);
  });
});

describe('Tostadas', () => {
  test('la región existe vacía; los errores son alert y se cierran con botón', async () => {
    expect(html(<Tostadas tostadas={[]} onCerrar={() => {}} />)).toContain('aria-label="Avisos"');
    const cerradas: string[] = [];
    const { host } = await montar(
      <Tostadas
        tostadas={[{ id: 'x', tono: 'error', texto: 'No se ha guardado.', duracionMs: 10 }]}
        onCerrar={(id) => cerradas.push(id)}
      />,
    );
    expect(host.querySelector('[role="alert"]')?.textContent).toContain('No se ha guardado.');
    await act(async () => {
      host.querySelector('button')?.click();
    });
    expect(cerradas).toEqual(['x']);
  });
});
