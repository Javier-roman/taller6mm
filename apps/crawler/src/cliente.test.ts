import { describe, expect, test } from 'vitest';
import {
  BloqueadoPorRobots,
  BloqueoDetectado,
  CircuitoAbierto,
  ClienteRespetuoso,
  type EntradaRegistro,
  esZonaPrivada,
  mismoSitio,
  type OpcionesCliente,
  ZonaPrivada,
} from './cliente.ts';

const UA = 'Taller6mmBot/0.1.0 (+https://taller6mm.example/bot)';

type Ruta = { estado: number; cuerpo?: string; cabeceras?: Record<string, string> } | (() => never);

/** Web falsa: mapa URL → respuesta, con un reloj falso que solo avanza al esperar. */
function montar(rutas: Record<string, Ruta | Ruta[]>, extra: Partial<OpcionesCliente> = {}) {
  let reloj = 1_000_000;
  const esperas: number[] = [];
  const pedidas: { url: string; t: number; ua: string | null; cookie: string | null }[] = [];
  const registro: EntradaRegistro[] = [];
  const cuentas = new Map<string, number>();
  const fetchFalso = (async (entrada: URL | string | Request, init?: RequestInit) => {
    const url = String(entrada);
    const h = new Headers(init?.headers);
    pedidas.push({ url, t: reloj, ua: h.get('user-agent'), cookie: h.get('cookie') });
    const def = rutas[url];
    const n = cuentas.get(url) ?? 0;
    cuentas.set(url, n + 1);
    const r = Array.isArray(def) ? def[Math.min(n, def.length - 1)] : def;
    if (!r) return new Response('no', { status: 404 });
    if (typeof r === 'function') return r();
    return new Response(r.cuerpo ?? '', { status: r.estado, headers: r.cabeceras ?? {} });
  }) as typeof fetch;
  const hosts = [...new Set(Object.keys(rutas).map((u) => new URL(u).hostname.replace(/^www\./, '')))];
  const cliente = new ClienteRespetuoso({
    userAgent: UA,
    hostsPermitidos: hosts.length ? hosts : ['vacio.example'],
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

const ROBOTS_OK = {
  estado: 200,
  cuerpo: 'User-agent: *\nDisallow: /tienda-cerrada\nContent-Signal: search=yes, ai-train=no',
};
const dif = (t: number[], i: number) => (t[i] ?? 0) - (t[i - 1] ?? 0);

describe('ClienteRespetuoso: lo básico', () => {
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

  test('guarda la evidencia de robots.txt aunque nos lo prohíba todo', async () => {
    const { cliente } = montar({
      'https://t.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nDisallow: /' },
    });
    const info = await cliente.robots(new URL('https://t.example/'));
    expect(info.texto).toContain('Disallow: /');
    expect(info.sha256).toMatch(/^[0-9a-f]{64}$/);
    await expect(cliente.obtener('https://t.example/x')).rejects.toBeInstanceOf(BloqueadoPorRobots);
  });

  test('peticiones en paralelo al mismo sitio: robots una sola vez y en serie', async () => {
    const { cliente, pedidas } = montar({
      'https://p.example/robots.txt': { estado: 404 },
      'https://p.example/a': { estado: 200 },
      'https://p.example/b': { estado: 200 },
    });
    await Promise.all([cliente.obtener('https://p.example/a'), cliente.obtener('https://p.example/b')]);
    expect(pedidas.filter((p) => p.url.endsWith('robots.txt'))).toHaveLength(1);
    expect(
      dif(
        pedidas.map((p) => p.t),
        2,
      ),
    ).toBeGreaterThanOrEqual(3000);
  });
});

describe('ClienteRespetuoso: robots.txt', () => {
  test('404 = sin restricciones; 5xx = todo prohibido', async () => {
    const sin = montar({ 'https://b.example/x': { estado: 200, cuerpo: 'ok' } });
    expect((await sin.cliente.obtener('https://b.example/x')).estado).toBe(200);
    const caida = montar({ 'https://a.example/robots.txt': { estado: 500 } });
    await expect(caida.cliente.obtener('https://a.example/x')).rejects.toBeInstanceOf(BloqueadoPorRobots);
  });

  test.each([401, 403, 429, 451])('robots.txt con %i: la web nos bloquea y se para el sitio', async (estado) => {
    const { cliente, pedidas } = montar({
      'https://w.example/robots.txt': { estado },
      'https://w.example/p': { estado: 200 },
    });
    await expect(cliente.obtener('https://w.example/p')).rejects.toBeInstanceOf(BloqueoDetectado);
    await expect(cliente.obtener('https://w.example/otra')).rejects.toBeInstanceOf(BloqueoDetectado);
    expect(pedidas.map((p) => p.url)).toEqual(['https://w.example/robots.txt']);
  });

  test('un robots.txt 200 que es HTML o un desafío cuenta como bloqueo', async () => {
    const { cliente } = montar({
      'https://c.example/robots.txt': {
        estado: 200,
        cuerpo: '<!doctype html><title>Just a moment...</title>',
        cabeceras: { 'content-type': 'text/html' },
      },
    });
    await expect(cliente.obtener('https://c.example/p')).rejects.toBeInstanceOf(BloqueoDetectado);
  });

  test('sigue la redirección de robots.txt dentro del sitio', async () => {
    const { cliente } = montar({
      'https://x.example/robots.txt': { estado: 301, cabeceras: { location: 'https://www.x.example/robots.txt' } },
      'https://www.x.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nDisallow: /privada' },
      'https://x.example/ok': { estado: 200 },
    });
    expect((await cliente.obtener('https://x.example/ok')).estado).toBe(200);
    await expect(cliente.obtener('https://x.example/privada')).rejects.toBeInstanceOf(BloqueadoPorRobots);
  });

  test('un Crawl-delay de más de 60 s para el sitio', async () => {
    const { cliente } = montar({
      'https://lenta.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nCrawl-delay: 86400' },
    });
    await expect(cliente.obtener('https://lenta.example/x')).rejects.toThrow('Crawl-delay excesivo');
  });
});

describe('ClienteRespetuoso: ritmo y bloqueos', () => {
  test('espera entre peticiones (Crawl-delay si es mayor); www y sin www comparten pausa', async () => {
    const { cliente, esperas, pedidas } = montar({
      'https://s.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nCrawl-delay: 20' },
      'https://www.s.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nCrawl-delay: 20' },
      'https://s.example/1': { estado: 200 },
      'https://www.s.example/2': { estado: 200 },
    });
    await cliente.obtener('https://s.example/1');
    await cliente.obtener('https://www.s.example/2');
    const t = pedidas.map((p) => p.t);
    expect(t.length).toBe(4);
    for (let i = 1; i < t.length; i++) expect(dif(t, i)).toBeGreaterThanOrEqual(3000);
    expect(esperas).toContain(20000);
  });

  test('sin Crawl-delay, la espera está entre 3 y 10 s', async () => {
    const { cliente, esperas } = montar({
      'https://r.example/robots.txt': { estado: 404 },
      'https://r.example/1': { estado: 200 },
      'https://r.example/2': { estado: 200 },
    });
    await cliente.obtener('https://r.example/1');
    await cliente.obtener('https://r.example/2');
    expect(esperas.length).toBe(2);
    expect(esperas.every((ms) => ms >= 3000 && ms <= 10000)).toBe(true);
  });

  test('la configuración no puede relajar las reglas', () => {
    const base = { userAgent: UA, hostsPermitidos: ['a.example'] };
    expect(() => new ClienteRespetuoso({ ...base, esperaMinMs: 500 })).toThrow('3 s');
    expect(() => new ClienteRespetuoso({ ...base, esperaMaxMs: 0 })).toThrow('máxima');
    expect(() => new ClienteRespetuoso({ ...base, userAgent: 'Mozilla/5.0' })).toThrow('User-Agent');
    expect(() => new ClienteRespetuoso({ ...base, hostsPermitidos: [] })).toThrow('hosts');
  });

  test('429 con Retry-After corto: espera lo que pide y reintenta', async () => {
    const { cliente, esperas } = montar({
      'https://x.example/robots.txt': { estado: 404 },
      'https://x.example/p': [
        { estado: 429, cabeceras: { 'retry-after': '45' } },
        { estado: 200, cuerpo: 'ya' },
      ],
    });
    expect((await cliente.obtener('https://x.example/p')).estado).toBe(200);
    expect(esperas).toContain(45000);
  });

  test('429 con Retry-After de una hora: se abandona el sitio sin reintentar', async () => {
    const { cliente, pedidas } = montar({
      'https://h.example/robots.txt': { estado: 404 },
      'https://h.example/p': { estado: 429, cabeceras: { 'retry-after': '3600' } },
    });
    await expect(cliente.obtener('https://h.example/p')).rejects.toThrow('Retry-After');
    expect(pedidas.filter((p) => p.url.endsWith('/p'))).toHaveLength(1);
  });

  test('403 o una página de CAPTCHA paran el sitio entero', async () => {
    const prohibido = montar({
      'https://f.example/robots.txt': { estado: 404 },
      'https://f.example/p': { estado: 403 },
    });
    await expect(prohibido.cliente.obtener('https://f.example/p')).rejects.toBeInstanceOf(BloqueoDetectado);
    await expect(prohibido.cliente.obtener('https://f.example/q')).rejects.toBeInstanceOf(BloqueoDetectado);
    const captcha = montar({
      'https://k.example/robots.txt': { estado: 404 },
      'https://k.example/p': {
        estado: 200,
        cuerpo: '<div class="g-recaptcha captcha"></div>',
        cabeceras: { 'content-type': 'text/html' },
      },
    });
    await expect(captcha.cliente.obtener('https://k.example/p')).rejects.toBeInstanceOf(BloqueoDetectado);
  });

  test('circuito abierto tras varios 5xx seguidos', async () => {
    const { cliente } = montar(
      { 'https://rota.example/robots.txt': { estado: 404 }, 'https://rota.example/p': { estado: 500 } },
      { fallosParaAbrir: 2 },
    );
    expect((await cliente.obtener('https://rota.example/p')).estado).toBe(500);
    expect((await cliente.obtener('https://rota.example/p')).estado).toBe(500);
    await expect(cliente.obtener('https://rota.example/p')).rejects.toBeInstanceOf(CircuitoAbierto);
  });
});

describe('ClienteRespetuoso: qué no se pide nunca', () => {
  test('solo hosts aprobados, solo https, sin IP, puertos raros ni credenciales', async () => {
    const { cliente, pedidas } = montar({ 'https://t.example/robots.txt': { estado: 404 } });
    for (const u of [
      'https://otra.example/x',
      'http://t.example/x',
      'https://127.0.0.1/x',
      'https://u:p@t.example/x',
      'https://t.example:8443/x',
    ]) {
      await expect(cliente.obtener(u), u).rejects.toBeInstanceOf(ZonaPrivada);
    }
    expect(pedidas).toHaveLength(0);
  });

  test('zonas privadas: carrito, cuenta, login, búsqueda y añadir al carrito', async () => {
    const { cliente, pedidas } = montar({ 'https://t.example/robots.txt': { estado: 404 } });
    for (const u of [
      'https://t.example/carrito',
      'https://t.example/mi-cuenta/pedidos',
      'https://t.example/iniciar-sesion?back=my-account',
      'https://t.example/buscar?q=m4',
      'https://t.example/producto/m4/?add-to-cart=12',
      'https://t.example/checkout',
    ]) {
      await expect(cliente.obtener(u), u).rejects.toBeInstanceOf(ZonaPrivada);
    }
    expect(pedidas).toHaveLength(0);
    expect(esZonaPrivada(new URL('https://t.example/producto/replica-m4-cyma'))).toBe(false);
  });

  test('redirecciones: dentro del sitio sí (con robots en cada salto); fuera o a http, no', async () => {
    const { cliente } = montar({
      'https://www.t.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nDisallow: /privado' },
      'https://t.example/robots.txt': { estado: 404 },
      'https://t.example/viejo': { estado: 301, cabeceras: { location: 'https://www.t.example/nuevo' } },
      'https://www.t.example/nuevo': { estado: 200, cuerpo: 'nuevo' },
      'https://t.example/fuera': { estado: 302, cabeceras: { location: 'https://otro.example/' } },
      'https://t.example/a-privado': { estado: 302, cabeceras: { location: 'https://www.t.example/privado/x' } },
      'https://t.example/a-http': { estado: 302, cabeceras: { location: 'http://t.example/x' } },
    });
    expect((await cliente.obtener('https://t.example/viejo')).url).toBe('https://www.t.example/nuevo');
    await expect(cliente.obtener('https://t.example/fuera')).rejects.toBeInstanceOf(ZonaPrivada);
    await expect(cliente.obtener('https://t.example/a-privado')).rejects.toBeInstanceOf(BloqueadoPorRobots);
    await expect(cliente.obtener('https://t.example/a-http')).rejects.toBeInstanceOf(ZonaPrivada);
  });

  test('corta las respuestas demasiado grandes', async () => {
    const { cliente } = montar(
      {
        'https://g.example/robots.txt': { estado: 404 },
        'https://g.example/foto.jpg': { estado: 200, cuerpo: 'x'.repeat(2048) },
      },
      { maxBytes: 1024 },
    );
    await expect(cliente.obtener('https://g.example/foto.jpg')).rejects.toThrow('demasiado grande');
  });

  test('mismoSitio trata www como el mismo host y exige https', () => {
    expect(mismoSitio(new URL('https://www.a.es/x'), new URL('https://a.es/y'))).toBe(true);
    expect(mismoSitio(new URL('https://a.es'), new URL('https://b.a.es'))).toBe(false);
    expect(mismoSitio(new URL('https://a.es'), new URL('http://a.es'))).toBe(false);
  });
});
