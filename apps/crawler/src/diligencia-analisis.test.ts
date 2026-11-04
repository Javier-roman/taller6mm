import { describe, expect, test } from 'vitest';
import {
  datosEstructurados,
  elegirPaginas,
  enlacesMismoHost,
  locsDeSitemap,
  pasajesRelevantes,
  plataforma,
  sitemapsDeRobots,
  textoDeHtml,
} from './diligencia-analisis.ts';

describe('análisis de la diligencia debida', () => {
  test('sitemaps declarados en robots y <loc> de un sitemap', () => {
    expect(
      sitemapsDeRobots('User-agent: *\nSitemap: https://t.example/sitemap.xml\nsitemap:https://t.example/s2.xml'),
    ).toEqual(['https://t.example/sitemap.xml', 'https://t.example/s2.xml']);
    expect(
      locsDeSitemap(
        '<urlset><url><loc>https://t.example/a?x=1&amp;y=2</loc></url><url><loc><![CDATA[https://t.example/b]]></loc></url></urlset>',
      ),
    ).toEqual(['https://t.example/a?x=1&y=2', 'https://t.example/b']);
  });

  test('elige legales, categorías y productos repartidos', () => {
    const urls = [
      'https://t.example/aviso-legal',
      'https://t.example/condiciones-generales',
      'https://t.example/categoria/fusiles/',
      ...Array.from({ length: 40 }, (_, i) => `https://t.example/producto/replica-numero-${i}`),
    ];
    const s = elegirPaginas(urls, 5);
    expect(s.legales).toEqual(['https://t.example/aviso-legal', 'https://t.example/condiciones-generales']);
    expect(s.categorias).toEqual(['https://t.example/categoria/fusiles/']);
    expect(s.productos).toHaveLength(4);
    expect(new Set(s.productos).size).toBe(4);
    expect(s.productos[1]).not.toBe('https://t.example/producto/replica-numero-1');
  });

  test('enlaces del mismo host (con o sin www) y absolutos', () => {
    const html =
      '<a href="/legal">L</a><a href="https://www.t.example/p">P</a><a href="https://otra.example/x">X</a><a href="#top">T</a>';
    expect(enlacesMismoHost(html, 'https://t.example/')).toEqual([
      'https://t.example/legal',
      'https://www.t.example/p',
    ]);
  });

  test('detecta la plataforma', () => {
    expect(plataforma('<script src="https://cdn.shopify.com/s/x.js">')).toBe('shopify');
    expect(plataforma('<link href="/wp-content/plugins/woocommerce/a.css">')).toBe('woocommerce');
    expect(plataforma('<script>var prestashop = {}</script>')).toBe('prestashop');
    expect(plataforma('<div data-mage-init="{}">')).toBe('magento');
    expect(plataforma('<html></html>')).toBe('desconocida');
  });

  test('datos estructurados: JSON-LD Product/Offer, OpenGraph e imágenes', () => {
    const html = `<meta property="og:type" content="product"><script type="application/ld+json">{"@type":"Product","offers":{"@type":"Offer"}}</script><img src="a"><img src="b">`;
    expect(datosEstructurados(html)).toEqual({
      jsonLdTipos: ['Offer', 'Product'],
      tieneProducto: true,
      tieneOferta: true,
      ogProducto: true,
      imagenes: 2,
    });
  });

  test('texto legible y pasajes que hablan de extracción e imágenes', () => {
    const html =
      '<script>no</script><p>Queda prohibida la extracción automatizada de contenidos mediante robots o scrapers.</p><p>Horario de 10 a 14 h, de lunes a viernes, salvo festivos.</p><p>Las imágenes de esta web son propiedad de la tienda y no pueden reproducirse.</p>';
    const texto = textoDeHtml(html);
    expect(texto).not.toContain('no</script>');
    expect(pasajesRelevantes(texto)).toEqual([
      'Queda prohibida la extracción automatizada de contenidos mediante robots o scrapers.',
      'Las imágenes de esta web son propiedad de la tienda y no pueden reproducirse.',
    ]);
  });
});
