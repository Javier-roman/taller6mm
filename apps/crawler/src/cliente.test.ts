import { describe, expect, test } from 'vitest';
import { BloqueadoPorRobots, CircuitoAbierto, ClienteRespetuoso, type EntradaRegistro, mismoSitio } from './cliente.ts';

const UA = 'Taller6mmBot/0.1.0 (+https://taller6mm.example/bot)';

type Ruta = { estado: number; cuerpo?: string; cabeceras?: Record<string, string> } | (() => never);

/** Web falsa: mapa URL → respuesta, con un reloj falso que solo avanza al esperar. */
function montar(
  rutas: Record<string, Ruta | Ruta[]>,
  extra: Partial<ConstructorParameters<typeof ClienteRespetuoso>[0]> = {},
) {
  let reloj = 1_000_000;
  const esperas: number[] = [];
  const pedidas: { url: string; ua: string | null; cookie: string | null }[] = [];
  const registro: EntradaRegistro[] = [];
  const cuentas = new Map<string, number>();
  const fetchFalso = (async (entrada: URL | string | Request, init?: RequestInit) => {
    const url = String(entrada);
    const h = new Headers(init?.headers);
    pedidas.push({ url, ua: h.get('user-agent'), cookie: h.get('cookie') });
    const def = rutas[url];
    const n = cuentas.get(url) ?? 0;
    cuentas.set(url, n + 1);
    const r = Array.isArray(def) ? def[Math.min(n, def.length - 1)] : def;
    if (!r) return new Response('no', { status: 404 });
    if (typeof r === 'function') return r();
    return new Response(r.cuerpo ?? '', { status: r.estado, headers: r.cabeceras ?? {} });
  }) as typeof fetch;
  const cliente = new ClienteRespetuoso({
    userAgent: UA,
    fetch: fetchFalso,
    ahora: () => reloj,
    esperar: async (ms) => {
      esperas.push(ms);
      reloj += ms;
    },
    azar: () => 0.5,
    registrar: (e) => registro.push(e),
    ...extra,
  });
  return { cliente, esperas, pedidas, registro };
}

const ROBOTS_OK = { estado: 200, cuerpo: 'User-agent: *\nDisallow: /carrito\nContent-Signal: search=yes, ai-train=no' };

describe('ClienteRespetuoso', () => {
  test('pide robots.txt primero, se identifica, no manda cookies y registra cada petición', async () => {
    const { cliente, pedidas, registro } = montar({
      'https://tienda.example/robots.txt': ROBOTS_OK,
      'https://tienda.example/m4': { estado: 200, cuerpo: '<h1>M4</h1>', cabeceras: { 'content-type': 'text/html' } },
    });
    const r = await cliente.obtener('https://tienda.example/m4');
    expect(new TextDecoder().decode(r.cuerpo)).toBe('<h1>M4</h1>');
    expect(r.evaluacion.senales['ai-train']).toBe('no');
    expect(pedidas.map((p) => p.url)).toEqual(['https://tienda.example/robots.txt', 'https://tienda.example/m4']);
    expect(pedidas.every((p) => p.ua === UA && p.cookie === null)).toBe(true);
    expect(registro.map((e) => e.estado)).toEqual([200, 200]);
  });

  test('respeta Disallow sin llegar a pedir la página', async () => {
    const { cliente, pedidas } = montar({ 'https://tienda.example/robots.txt': ROBOTS_OK });
    await expect(cliente.obtener('https://tienda.example/carrito/1')).rejects.toBeInstanceOf(BloqueadoPorRobots);
    expect(pedidas).toHaveLength(1);
  });

  test('robots con 5xx o sin respuesta = todo prohibido; con 404 = sin restricciones', async () => {
    const caida = montar({ 'https://a.example/robots.txt': { estado: 500 } });
    await expect(caida.cliente.obtener('https://a.example/x')).rejects.toBeInstanceOf(BloqueadoPorRobots);
    const sin = montar({ 'https://b.example/x': { estado: 200, cuerpo: 'ok' } });
    expect((await sin.cliente.obtener('https://b.example/x')).estado).toBe(200);
  });

  test('espera entre 3 y 10 s entre peticiones al mismo sitio, y más si Crawl-delay lo pide', async () => {
    const { cliente, esperas } = montar({
      'https://lenta.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nCrawl-delay: 20' },
      'https://lenta.example/1': { estado: 200 },
      'https://lenta.example/2': { estado: 200 },
      'https://rapida.example/1': { estado: 200 },
    });
    await cliente.obtener('https://lenta.example/1');
    await cliente.obtener('https://lenta.example/2');
    expect(esperas).toEqual([20000, 20000]);
    const otro = montar({ 'https://rapida.example/1': { estado: 200 }, 'https://rapida.example/2': { estado: 200 } });
    await otro.cliente.obtener('https://rapida.example/1');
    await otro.cliente.obtener('https://rapida.example/2');
    expect(otro.esperas.every((ms) => ms >= 3000 && ms <= 10000)).toBe(true);
  });

  test('no se puede configurar una espera menor de 3 s ni otro User-Agent', () => {
    expect(() => new ClienteRespetuoso({ userAgent: UA, esperaMinMs: 500 })).toThrow('3 s');
    expect(() => new ClienteRespetuoso({ userAgent: 'Mozilla/5.0' })).toThrow('User-Agent');
  });

  test('429 con Retry-After: espera lo que pide (con tope) y reintenta poco', async () => {
    const { cliente, esperas } = montar({
      'https://x.example/p': [
        { estado: 429, cabeceras: { 'retry-after': '45' } },
        { estado: 200, cuerpo: 'ya' },
      ],
    });
    const r = await cliente.obtener('https://x.example/p');
    expect(r.estado).toBe(200);
    expect(esperas).toContain(45000);
  });

  test('circuito abierto tras varios fallos seguidos', async () => {
    const { cliente } = montar(
      {
        'https://rota.example/robots.txt': { estado: 404 },
        'https://rota.example/p': { estado: 500 },
      },
      { fallosParaAbrir: 2 },
    );
    expect((await cliente.obtener('https://rota.example/p')).estado).toBe(500);
    expect((await cliente.obtener('https://rota.example/p')).estado).toBe(500);
    await expect(cliente.obtener('https://rota.example/p')).rejects.toBeInstanceOf(CircuitoAbierto);
  });

  test('sigue redirecciones dentro del sitio (con robots en cada salto) y rechaza las de fuera', async () => {
    const { cliente } = montar({
      'https://www.t.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nDisallow: /privado' },
      'https://t.example/robots.txt': { estado: 404 },
      'https://t.example/viejo': { estado: 301, cabeceras: { location: 'https://www.t.example/nuevo' } },
      'https://www.t.example/nuevo': { estado: 200, cuerpo: 'nuevo' },
      'https://t.example/fuera': { estado: 302, cabeceras: { location: 'https://otro.example/' } },
      'https://t.example/a-privado': { estado: 302, cabeceras: { location: 'https://www.t.example/privado/x' } },
    });
    expect((await cliente.obtener('https://t.example/viejo')).url).toBe('https://www.t.example/nuevo');
    await expect(cliente.obtener('https://t.example/fuera')).rejects.toThrow('fuera del sitio');
    await expect(cliente.obtener('https://t.example/a-privado')).rejects.toBeInstanceOf(BloqueadoPorRobots);
  });

  test('corta las respuestas demasiado grandes', async () => {
    const { cliente } = montar(
      { 'https://g.example/foto.jpg': { estado: 200, cuerpo: 'x'.repeat(2048) } },
      { maxBytes: 1024 },
    );
    await expect(cliente.obtener('https://g.example/foto.jpg')).rejects.toThrow('demasiado grande');
  });

  test('mismoSitio trata www como el mismo host', () => {
    expect(mismoSitio(new URL('https://www.a.es/x'), new URL('https://a.es/y'))).toBe(true);
    expect(mismoSitio(new URL('https://a.es'), new URL('https://b.a.es'))).toBe(false);
    expect(mismoSitio(new URL('https://a.es'), new URL('http://a.es'))).toBe(false);
  });
});
