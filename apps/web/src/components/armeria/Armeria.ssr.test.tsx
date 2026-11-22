// El HTML que llega del servidor, antes de hidratar: póster con su texto alternativo y dimensiones, ocho
// enlaces de navegación con su ruta, un solo tabulador, «Más luz» a la vista y la marca de datos de demo.
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import Armeria from './Armeria.tsx';
import { TEXTO_ALTERNATIVO } from './Poster.tsx';
import { SOCKETS } from './sockets.ts';
import { posterDe } from './vistas.ts';
import { ZONAS } from './zonas.ts';

const html = renderToString(<Armeria />);
const POSTER = posterDe('penumbra');

describe('La Armería en el HTML inicial', () => {
  it('lleva el póster como <img> con alt, tamaño y prioridad alta (LCP sin saltos)', () => {
    expect(html).toContain(`src="${POSTER.src}"`);
    expect(html).toContain(`width="${POSTER.ancho}"`);
    expect(html).toContain(`height="${POSTER.alto}"`);
    expect(html).toContain('fetchPriority="high"');
    expect(html).toContain(`alt="${TEXTO_ALTERNATIVO}"`);
  });

  it('la navegación HTML tiene las ocho zonas con su enlace, y solo una en el orden de tabulación', () => {
    const nav = html.slice(html.indexOf('<nav'), html.indexOf('</nav>'));
    for (const zona of ZONAS) expect(nav).toContain(`href="${zona.ruta}"`);
    expect(nav.match(/tabindex="0"/g)).toHaveLength(1);
    expect(nav.match(/tabindex="-1"/g)).toHaveLength(ZONAS.length - 1);
  });

  it('las zonas del póster no estorban a los lectores de pantalla ni al tabulador', () => {
    expect(html).toContain('class="armeria-poster__zonas" aria-hidden="true"');
    const zonas = html.match(/<a href="[^"]+" class="armeria-poster__zona"[^>]*>/g) ?? [];
    expect(zonas).toHaveLength(ZONAS.length);
    for (const zona of zonas) expect(zona).toContain('tabindex="-1"');
  });

  it('los huecos de réplica están ahí pero vacíos: ni siluetas ni imágenes de relleno', () => {
    const huecos = html.match(/class="armeria-poster__socket"[^>]*>/g) ?? [];
    expect(huecos).toHaveLength(SOCKETS.length);
    for (const hueco of huecos) expect(hueco).toContain('data-vacio="true"');
    expect(html).toContain('class="armeria-poster__sockets" aria-hidden="true"');
    // Una sola imagen en todo el HTML: el póster.
    expect(html.match(/<img /g)).toHaveLength(1);
  });

  it('«Más luz» siempre visible, sin pulsar por defecto, y la penumbra es el estado inicial', () => {
    expect(html).toMatch(/<button[^>]*aria-pressed="false"[^>]*>.*Más luz/s);
    expect(html).toContain('data-luz="penumbra"');
  });

  it('avisa de que los datos y las siluetas son provisionales', () => {
    expect(html).toContain('Siluetas provisionales');
    expect(html).toContain('Datos de demostración');
    expect(html.match(/\(dato de ejemplo\)/g)).toHaveLength(ZONAS.length);
  });
});
