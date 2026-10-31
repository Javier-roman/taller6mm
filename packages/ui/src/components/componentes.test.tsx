// @vitest-environment happy-dom
// Render en servidor (lo que Astro envía sin JS) de cada componente y sus estados.
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, test } from 'vitest';
import {
  BarraDato,
  Boton,
  BotonEnlace,
  Cargador,
  formatearDato,
  InsigniaFidelidad,
  NIVELES_FIDELIDAD,
  Placa,
  Rotulo,
  VARIANTES_BOTON,
} from './index.ts';

const html = (node: React.ReactNode) => renderToStaticMarkup(node);
const doc = (node: React.ReactNode) => {
  const template = document.createElement('template');
  template.innerHTML = html(node);
  return template.content;
};

describe('Botón', () => {
  test.each(VARIANTES_BOTON)('variante %s: botón real, type="button" por defecto', (variante) => {
    const out = html(<Boton variante={variante}>Guardar build</Boton>);
    expect(out).toContain(`class="t6-boton t6-boton--${variante}"`);
    expect(out).toContain('type="button"');
    expect(out).toContain('Guardar build');
  });

  test('cargando: sigue enfocable, avisa con aria-busy y no se puede volver a pulsar', () => {
    const out = html(
      <Boton cargando textoCarga="Guardando…">
        Guardar
      </Boton>,
    );
    expect(out).toContain('aria-busy="true"');
    expect(out).toContain('aria-disabled="true"');
    expect(out).not.toContain('disabled=""');
    expect(out).toContain('Guardando…');
    expect(out).toContain('t6-cargador');
  });

  test('error: mensaje enlazado con aria-describedby', () => {
    const root = doc(<Boton error="No se ha guardado: revisa tu conexión.">Guardar</Boton>);
    const button = root.querySelector('button');
    const id = button?.getAttribute('aria-describedby') ?? '';
    expect(id).not.toBe('');
    expect(root.querySelector(`[id="${id}"]`)?.textContent).toContain('revisa tu conexión');
    expect(button?.getAttribute('data-estado')).toBe('error');
  });

  test('deshabilitado nativo y estado de demostración', () => {
    expect(html(<Boton disabled>Comprar</Boton>)).toContain('disabled=""');
    expect(html(<Boton demo="hover">Comprar</Boton>)).toContain('data-demo="hover"');
  });

  test('BotonEnlace es un enlace con la misma apariencia', () => {
    const out = html(
      <BotonEnlace href="/banco" variante="laton">
        Monta tu réplica
      </BotonEnlace>,
    );
    expect(out).toMatch(/^<a href="\/banco" class="t6-boton t6-boton--laton"/);
  });
});

describe('Placa', () => {
  test('sección con nombre accesible (su título)', () => {
    const root = doc(<Placa titulo="Peso y medidas">Contenido</Placa>);
    const section = root.querySelector('section');
    const id = section?.getAttribute('aria-labelledby') ?? '';
    expect(root.querySelector(`[id="${id}"]`)?.textContent).toBe('Peso y medidas');
  });

  test('con href: un único enlace, el del título', () => {
    const root = doc(
      <Placa titulo="Armero de réplicas" href="/replicas" codigo="MOD-02">
        <p>Ranuras numeradas</p>
      </Placa>,
    );
    expect(root.querySelectorAll('a')).toHaveLength(1);
    expect(root.querySelector('h3 a')?.getAttribute('href')).toBe('/replicas');
    expect(root.querySelector('article')?.className).toContain('t6-placa--enlace');
  });

  test('carga, error y deshabilitada', () => {
    const carga = doc(<Placa titulo="Mercado" estado="carga" />);
    expect(carga.querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(carga.querySelector('[role="status"]')?.textContent).toBe('Cargando…');

    const error = doc(<Placa titulo="Mercado" estado="error" mensaje="No hay conexión con las tiendas." />);
    expect(error.querySelector('[data-estado="error"]')).not.toBeNull();
    expect(error.textContent).toContain('No hay conexión con las tiendas.');

    const off = doc(
      <Placa titulo="Comunidad" href="/comunidad" estado="deshabilitada" mensaje="Llega en la Fase 5." />,
    );
    expect(off.querySelector('a')).toBeNull();
    expect(off.querySelector('[data-estado="deshabilitada"]')).not.toBeNull();
  });
});

describe('Rótulo plantilla', () => {
  test('tamaños, tintas, iluminado y apagado', () => {
    expect(html(<Rotulo>Banco</Rotulo>)).toBe('<span class="t6-rotulo">Banco</span>');
    expect(
      html(
        <Rotulo tamano="l" tinta="laton">
          Armero
        </Rotulo>,
      ),
    ).toContain('t6-rotulo--l t6-rotulo--laton');
    expect(html(<Rotulo iluminado>Mercado</Rotulo>)).toContain('data-iluminado=""');
    const apagado = html(
      <Rotulo iluminado apagado>
        Taquilla
      </Rotulo>,
    );
    expect(apagado).toContain('t6-rotulo--apagado');
    expect(apagado).not.toContain('data-iluminado');
  });
});

describe('Insignia de fidelidad', () => {
  test.each(Object.entries(NIVELES_FIDELIDAD))('%s: código, nombre y prefijo para lectores', (nivel, { nombre }) => {
    const root = doc(<InsigniaFidelidad nivel={nivel as keyof typeof NIVELES_FIDELIDAD} />);
    expect(root.textContent).toBe(`Fidelidad: ${nivel}${nombre}`);
    expect(root.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });

  test('compacta: el nombre solo para lectores de pantalla', () => {
    const root = doc(<InsigniaFidelidad nivel="T2" compacta />);
    expect(root.querySelector('.t6-insignia__nombre')).toBeNull();
    expect(root.textContent).toContain('Modelo fiel');
  });

  test('sin nivel: «Sin verificar», nunca un nivel inventado', () => {
    const root = doc(<InsigniaFidelidad nivel={null} />);
    expect(root.textContent).toBe('Fidelidad: Sin verificar');
    expect(root.querySelector('[data-nivel="ninguno"]')).not.toBeNull();
  });
});

describe('Barra de dato', () => {
  const base = { etiqueta: 'Peso total', unidad: 'g', escala: { min: 2400, max: 4200 } } as const;

  test('meter nativo con valor, escala y lectura completa', () => {
    const root = doc(
      <BarraDato
        {...base}
        valor={3120}
        nota="Más ligera que el 70 % de las builds M4"
        referencia={{ valor: 3400, etiqueta: 'Mediana M4' }}
      />,
    );
    const meter = root.querySelector('meter');
    expect(meter?.getAttribute('value')).toBe('3120');
    expect(meter?.getAttribute('min')).toBe('2400');
    expect(meter?.getAttribute('max')).toBe('4200');
    expect(meter?.getAttribute('aria-valuetext')).toBe(
      '3120 g; Más ligera que el 70 % de las builds M4; Mediana M4: 3400 g',
    );
    const label = root.querySelector(`[id="${meter?.getAttribute('aria-labelledby')}"]`);
    expect(label?.textContent).toBe('Peso total');
    expect(root.querySelector('rect')?.getAttribute('width')).toBe('40');
    expect(root.querySelector('line')?.getAttribute('x1')).toBe('55.6');
  });

  test('el valor fuera de escala no se sale de la barra', () => {
    const root = doc(<BarraDato {...base} valor={5000} />);
    expect(root.querySelector('meter')?.getAttribute('value')).toBe('4200');
    expect(root.querySelector('rect')?.getAttribute('width')).toBe('100');
  });

  test('incompleto: el valor es un mínimo y se dice cuántas piezas faltan', () => {
    const root = doc(<BarraDato {...base} valor={3120} piezasSinDato={2} />);
    expect(root.querySelector('[data-estado="incompleto"]')).not.toBeNull();
    expect(root.querySelector('meter')?.getAttribute('aria-valuetext')).toBe('al menos 3120 g; 2 piezas sin peso');
    expect(root.textContent).toContain('≥');
  });

  test('sin dato: no hay meter ni número inventado', () => {
    const root = doc(<BarraDato {...base} valor={null} />);
    expect(root.querySelector('meter')).toBeNull();
    expect(root.querySelector('[data-estado="sin-dato"]')).not.toBeNull();
    expect(root.textContent).toContain('Sin dato');
  });

  test('carga y error', () => {
    const carga = doc(<BarraDato {...base} valor={null} estado="carga" />);
    expect(carga.querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(carga.querySelector('meter')).toBeNull();
    const error = doc(<BarraDato {...base} valor={3120} estado="error" />);
    expect(error.querySelector('meter')).toBeNull();
    expect(error.textContent).toContain('No se ha podido calcular');
  });

  test('formato es-ES: miles a partir de 5 cifras, céntimos a euros', () => {
    expect(formatearDato(3120, 'g')).toBe('3120 g');
    expect(formatearDato(12500, 'mm')).toBe('12.500 mm');
    expect(formatearDato(41235, 'eur')).toBe('412,35 €');
  });
});

describe('Cargador', () => {
  test('decorativo dentro de un botón; con etiqueta, anuncia el estado', () => {
    expect(html(<Cargador />)).toContain('aria-hidden="true"');
    const root = doc(<Cargador etiqueta="Buscando ofertas" />);
    expect(root.querySelector('[role="status"]')?.textContent).toBe('Buscando ofertas');
  });
});
