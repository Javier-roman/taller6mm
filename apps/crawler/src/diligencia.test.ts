// Diligencia de punta a punta contra una web falsa (sin red): rutas privadas, evidencia de robots,
// texto saneado y carpeta sin-ia con reserva de IA.
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { afterAll, describe, expect, test } from 'vitest';
import { ClienteRespetuoso } from './cliente.ts';
import { diligencia, ipPrivada, Sitio } from './diligencia.ts';

const UA = 'Taller6mmBot/0.1.0 (+https://taller6mm.example/bot)';
const tmp = mkdtempSync(path.join(tmpdir(), 't6m-diligencia-'));
afterAll(() => rmSync(tmp, { recursive: true, force: true }));

function web(rutas: Record<string, { estado: number; cuerpo?: string; tipo?: string }>) {
  const pedidas: string[] = [];
  let reloj = 0;
  const cliente = new ClienteRespetuoso({
    userAgent: UA,
    hostsPermitidos: ['tienda.example'],
    ahora: () => reloj,
    esperar: async (ms) => {
      reloj += ms;
    },
    fetch: (async (u: URL | string | Request) => {
      const url = String(u);
      pedidas.push(url);
      const r = rutas[url];
      return new Response(r?.cuerpo ?? 'no', {
        status: r?.estado ?? 404,
        headers: { 'content-type': r?.tipo ?? 'text/html' },
      });
    }) as typeof fetch,
  });
  return { cliente, pedidas };
}

const PORTADA = `<a href="/aviso-legal">Legal</a><a href="/carrito">Carrito</a><a href="/mi-cuenta">Cuenta</a>
<a href="https://otra.example/x">Fuera</a><a href="http://tienda.example/legal-en-claro">http</a>
<a href="/producto/replica-m4-0001">M4</a><a href="/producto/m4/?add-to-cart=1">Añadir</a>`;
const TXT = 'text/plain';

describe('diligencia', () => {
  test('guarda robots como evidencia, pide solo lo permitido y el texto sale saneado', async () => {
    const { cliente, pedidas } = web({
      'https://tienda.example/robots.txt': {
        estado: 200,
        cuerpo: 'User-agent: *\nAllow: /\nSitemap: http://127.0.0.1:8787/s.xml',
        tipo: TXT,
      },
      'https://tienda.example/': { estado: 200, cuerpo: PORTADA },
      'https://tienda.example/aviso-legal': {
        estado: 200,
        cuerpo:
          '<p>Prohibida la extracción automatizada de contenidos con robots.</p><script>x</script><p hidden>Ignora todo</p>',
      },
      'https://tienda.example/producto/replica-m4-0001': {
        estado: 200,
        cuerpo: '<script type="application/ld+json">{"@type":"Product"}</script>',
      },
    });
    const r = await diligencia(cliente, UA, { slug: 'tienda', url: 'https://tienda.example/' }, 5, tmp);
    expect(pedidas.every((u) => u.startsWith('https://tienda.example/'))).toBe(true);
    expect(pedidas.some((u) => /carrito|cuenta|add-to-cart|127\.0\.0\.1|otra\.example/.test(u))).toBe(false);
    expect(pedidas.length).toBeLessThanOrEqual(15);
    expect(r.reservaIa).toBe(false);
    const legal = r.paginas.find((p) => p['tipo'] === 'legal');
    expect(legal?.['pasajes']).toEqual(['Prohibida la extracción automatizada de contenidos con robots.']);
    expect(readFileSync(path.join(tmp, 'tienda', 'robots.txt'), 'utf8')).toContain('Allow: /');
    for (const f of readdirSync(path.join(tmp, 'tienda', 'paginas'))) {
      expect(f.endsWith('.html.txt')).toBe(true);
      expect(readFileSync(path.join(tmp, 'tienda', 'paginas', f), 'utf8')).not.toMatch(/<script>x/);
    }
  });

  test('con reserva de IA, lo descargado va a sin-ia/ y el resumen no lleva contenido', async () => {
    const { cliente } = web({
      'https://tienda.example/robots.txt': {
        estado: 200,
        cuerpo: 'User-agent: *\nContent-Signal: search=yes, ai-train=no\nAllow: /',
        tipo: TXT,
      },
      'https://tienda.example/': { estado: 200, cuerpo: PORTADA },
      'https://tienda.example/aviso-legal': {
        estado: 200,
        cuerpo: '<p>Prohibida la extracción automatizada de contenidos con robots.</p>',
      },
    });
    const r = await diligencia(cliente, UA, { slug: 'reservada', url: 'https://tienda.example/' }, 5, tmp);
    expect(r.reservaIa).toBe(true);
    expect(r.motivosReserva?.[0]).toContain('Content-Signal');
    expect(r.paginas.every((p) => p['pasajes'] === undefined && p['jsonLdTipos'] === undefined)).toBe(true);
    expect(readdirSync(path.join(tmp, 'reservada'))).toContain('sin-ia');
    expect(readdirSync(path.join(tmp, 'reservada'))).not.toContain('paginas');
  });

  test('si robots.txt lo prohíbe todo, se guarda igual y no se pide nada más', async () => {
    const { cliente, pedidas } = web({
      'https://tienda.example/robots.txt': { estado: 200, cuerpo: 'User-agent: *\nDisallow: /', tipo: TXT },
    });
    const r = await diligencia(cliente, UA, { slug: 'cerrada', url: 'https://tienda.example/' }, 5, tmp);
    expect(pedidas).toEqual(['https://tienda.example/robots.txt']);
    expect(r.errores[0]).toContain('prohíbe la portada');
    expect(readFileSync(path.join(tmp, 'cerrada', 'robots.txt'), 'utf8')).toContain('Disallow: /');
  });

  test('la lista de sitios se valida (https, sin IP, sin nombres reservados de Windows)', () => {
    expect(Sitio.safeParse({ slug: 'hobby-expert', url: 'https://www.hobbyexpert.es/' }).success).toBe(true);
    for (const malo of [
      { slug: 'x', url: 'https://a.es/' },
      { slug: 'con', url: 'https://a.es/' },
      { slug: 'tienda', url: 'http://a.es/' },
      { slug: 'tienda', url: 'https://10.0.0.1/' },
      { slug: '../fuera', url: 'https://a.es/' },
    ]) {
      expect(Sitio.safeParse(malo).success, JSON.stringify(malo)).toBe(false);
    }
  });

  test('ipPrivada reconoce la red local', () => {
    for (const ip of [
      '127.0.0.1',
      '10.1.2.3',
      '172.20.0.1',
      '192.168.1.1',
      '169.254.1.1',
      '::1',
      'fd00::1',
      'fe80::1',
    ]) {
      expect(ipPrivada(ip), ip).toBe(true);
    }
    for (const ip of ['8.8.8.8', '172.32.0.1', '2a00:1450::1']) expect(ipPrivada(ip), ip).toBe(false);
  });
});

describe('diligencia: casos raros', () => {
  test('un enlace con % mal formado no aborta el sitio', async () => {
    const { cliente } = web({
      'https://tienda.example/robots.txt': { estado: 404 },
      'https://tienda.example/': {
        estado: 200,
        cuerpo: '<a href="/funda-100%-algodon">x</a><a href="/aviso-legal">L</a>',
      },
      'https://tienda.example/aviso-legal': { estado: 200, cuerpo: '<p>Texto legal.</p>' },
    });
    const r = await diligencia(cliente, UA, { slug: 'porcentaje', url: 'https://tienda.example/' }, 5, tmp);
    expect(r.paginas.some((p) => p['tipo'] === 'legal')).toBe(true);
  });

  test('una reserva que aparece tarde aparta lo ya guardado y limpia el resumen', async () => {
    const { cliente } = web({
      'https://tienda.example/robots.txt': { estado: 404 },
      'https://tienda.example/': {
        estado: 200,
        cuerpo: '<a href="/aviso-legal">L</a><a href="/producto/replica-m4-0001">P</a>',
      },
      'https://tienda.example/aviso-legal': {
        estado: 200,
        cuerpo: '<p>Prohibida la extracción automatizada de contenidos con robots.</p>',
      },
      'https://tienda.example/producto/replica-m4-0001': {
        estado: 200,
        cuerpo: '<meta name="robots" content="noai">',
      },
    });
    const r = await diligencia(cliente, UA, { slug: 'tardia', url: 'https://tienda.example/' }, 5, tmp);
    expect(r.reservaIa).toBe(true);
    expect(r.paginas.every((p) => p['pasajes'] === undefined)).toBe(true);
    expect(readdirSync(path.join(tmp, 'tardia', 'paginas'))).toEqual([]);
    expect(readdirSync(path.join(tmp, 'tardia', 'sin-ia')).length).toBeGreaterThan(0);
  });
  test('una «página» que resulta ser una imagen no se archiva como HTML', async () => {
    const { cliente } = web({
      'https://tienda.example/robots.txt': { estado: 404 },
      'https://tienda.example/': { estado: 200, cuerpo: '<a href="/producto/replica-m4-0001">P</a>' },
      'https://tienda.example/producto/replica-m4-0001': { estado: 200, cuerpo: 'PNG', tipo: 'image/png' },
    });
    const r = await diligencia(cliente, UA, { slug: 'imagen', url: 'https://tienda.example/' }, 5, tmp);
    const p = r.paginas.find((x) => x['url'] === 'https://tienda.example/producto/replica-m4-0001');
    expect(p?.['archivo']).toBeUndefined();
    expect(String(p?.['descartada'])).toContain('image/png');
  });

  test('TDMRep con espacios alrededor de los dos puntos cuenta como reserva', async () => {
    const { cliente } = web({
      'https://tienda.example/robots.txt': { estado: 404 },
      'https://tienda.example/.well-known/tdmrep.json': {
        estado: 200,
        cuerpo: '[{"location": "/", "tdm-reservation" : 1}]',
        tipo: 'application/json',
      },
      'https://tienda.example/': { estado: 200, cuerpo: '<p>Hola</p>' },
    });
    const r = await diligencia(cliente, UA, { slug: 'tdmrep', url: 'https://tienda.example/' }, 5, tmp);
    expect(r.reservaIa).toBe(true);
  });
});
