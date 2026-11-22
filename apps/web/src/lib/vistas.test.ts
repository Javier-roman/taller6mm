import { describe, expect, it } from 'vitest';
import { CACHE_INMUTABLE, type CubetaVistas, claveVista, hashConjunto, rutaVista, servirVista } from './vistas';

const HASH = 'a1b2c3d4e5f6';
const url = (ruta: string) => `https://web.test${ruta}`;

function cubetaCon(objetos: Record<string, string>): CubetaVistas & { pedidas: string[] } {
  const pedidas: string[] = [];
  return {
    pedidas,
    async get(clave) {
      pedidas.push(clave);
      const contenido = objetos[clave];
      if (contenido === undefined) return null;
      const bytes = new TextEncoder().encode(contenido);
      return {
        httpEtag: '"abc123"',
        size: bytes.byteLength,
        body: new Blob([bytes]).stream(),
      };
    },
  };
}

describe('claveVista', () => {
  it('acepta solo /assets/armeria/<hash de 12 hex>/<nombre>.webp', () => {
    expect(claveVista(`/assets/armeria/${HASH}/poster-1920.webp`)).toBe(`armeria/${HASH}/poster-1920.webp`);
  });

  it.each([
    '/assets/armeria/poster.webp',
    `/assets/armeria/${HASH}/`,
    `/assets/armeria/${HASH}/poster.png`,
    `/assets/armeria/${HASH}/../${HASH}/poster.webp`,
    `/assets/armeria/${HASH}/sub/poster.webp`,
    `/assets/armeria/${HASH}/Poster.webp`,
    `/assets/armeria/${HASH}/%2e%2e.webp`,
    `/assets/armeria/${HASH.toUpperCase()}/poster.webp`,
    '/assets/armeria/zzzzzzzzzzzz/poster.webp',
    `/assets/otra/${HASH}/poster.webp`,
  ])('rechaza %s', (ruta) => {
    expect(claveVista(ruta)).toBeNull();
  });
});

describe('rutaVista', () => {
  it('construye una ruta que claveVista reconoce', () => {
    expect(claveVista(rutaVista(HASH, 'base.webp'))).toBe(`armeria/${HASH}/base.webp`);
  });
});

describe('hashConjunto', () => {
  it('no depende del orden y cambia con el contenido', async () => {
    const a = await hashConjunto({ 'a.webp': '11', 'b.webp': '22' });
    expect(a).toMatch(/^[0-9a-f]{12}$/);
    expect(await hashConjunto({ 'b.webp': '22', 'a.webp': '11' })).toBe(a);
    expect(await hashConjunto({ 'a.webp': '11', 'b.webp': '23' })).not.toBe(a);
    expect(await hashConjunto({ 'a.webp': '11', 'c.webp': '22' })).not.toBe(a);
  });
});

describe('servirVista', () => {
  const ruta = `/assets/armeria/${HASH}/poster-1920.webp`;
  const clave = `armeria/${HASH}/poster-1920.webp`;

  it('sirve el objeto con caché inmutable y tipo webp', async () => {
    const cubeta = cubetaCon({ [clave]: 'RIFF' });
    const r = await servirVista(new Request(url(ruta)), cubeta);
    expect(r?.status).toBe(200);
    expect(r?.headers.get('cache-control')).toBe(CACHE_INMUTABLE);
    expect(r?.headers.get('content-type')).toBe('image/webp');
    expect(r?.headers.get('etag')).toBe('"abc123"');
    expect(r?.headers.get('content-length')).toBe('4');
    expect(await r?.text()).toBe('RIFF');
  });

  it('devuelve null (sigue la cadena normal) si el objeto no está en el bucket', async () => {
    expect(await servirVista(new Request(url(ruta)), cubetaCon({}))).toBeNull();
  });

  it('no toca el bucket con rutas que no son vistas ni con otros métodos', async () => {
    const cubeta = cubetaCon({ [clave]: 'RIFF' });
    expect(await servirVista(new Request(url('/replicas')), cubeta)).toBeNull();
    expect(await servirVista(new Request(url(ruta), { method: 'POST', body: 'x' }), cubeta)).toBeNull();
    expect(cubeta.pedidas).toEqual([]);
  });

  it('sin bucket enlazado deja pasar', async () => {
    expect(await servirVista(new Request(url(ruta)), undefined)).toBeNull();
  });

  it('responde 304 si la ETag coincide', async () => {
    const cubeta = cubetaCon({ [clave]: 'RIFF' });
    const r = await servirVista(new Request(url(ruta), { headers: { 'if-none-match': 'W/"abc123", "otra"' } }), cubeta);
    expect(r?.status).toBe(304);
    expect(r?.headers.get('cache-control')).toBe(CACHE_INMUTABLE);
    expect(await r?.text()).toBe('');
  });

  it('HEAD devuelve cabeceras sin cuerpo', async () => {
    const r = await servirVista(new Request(url(ruta), { method: 'HEAD' }), cubetaCon({ [clave]: 'RIFF' }));
    expect(r?.status).toBe(200);
    expect(r?.headers.get('content-length')).toBe('4');
    expect(await r?.text()).toBe('');
  });
});
