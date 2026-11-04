import { describe, expect, test } from 'vitest';
import {
  analizarRobots,
  botsIaVetados,
  casa,
  evaluar,
  MAX_ROBOTS,
  normalizarRuta,
  prohibeIa,
  reservaIa,
} from './robots.ts';

const BOT = 'Taller6mmBot/0.1.0 (+https://taller6mm.example/bot)';

describe('robots.txt', () => {
  test('la regla más específica gana y, a igualdad, Allow', () => {
    const r = analizarRobots(`
User-agent: *
Disallow: /carrito
Disallow: /productos/
Allow: /productos/fusiles
Allow: /a
Disallow: /a
`);
    expect(evaluar(r, BOT, '/carrito/1').permitido).toBe(false);
    expect(evaluar(r, BOT, '/productos/pistolas').permitido).toBe(false);
    expect(evaluar(r, BOT, '/productos/fusiles/m4').permitido).toBe(true);
    expect(evaluar(r, BOT, '/a').permitido).toBe(true);
    expect(evaluar(r, BOT, '/otra').regla).toBeNull();
  });

  test('comodines * y $', () => {
    const r = analizarRobots('User-agent: *\nDisallow: /*?orderby=\nDisallow: /*.pdf$');
    expect(evaluar(r, BOT, '/categoria?orderby=precio').permitido).toBe(false);
    expect(evaluar(r, BOT, '/manual.pdf').permitido).toBe(false);
    expect(evaluar(r, BOT, '/manual.pdf?v=2').permitido).toBe(true);
  });

  test('un grupo con nuestro token sustituye al de *', () => {
    const r = analizarRobots('User-agent: *\nDisallow: /\n\nUser-agent: Taller6mmBot\nAllow: /\nCrawl-delay: 12');
    expect(evaluar(r, BOT, '/x').permitido).toBe(true);
    expect(evaluar(r, BOT, '/x').crawlDelay).toBe(12);
    expect(evaluar(r, 'OtroBot/1.0', '/x').permitido).toBe(false);
  });

  test('el token se compara exacto: un User-agent vacío o «bot» no nos sacan del grupo *', () => {
    for (const ua of ['', 'bot', 'taller', 'mm']) {
      const r = analizarRobots(`User-agent: *\nDisallow: /\n\nUser-agent: ${ua}\nAllow: /`);
      expect(evaluar(r, BOT, '/x').permitido, ua).toBe(false);
    }
  });

  test('varios User-agent seguidos comparten grupo; Sitemap no lo parte; Disallow vacío no prohíbe', () => {
    const r = analizarRobots(
      'User-agent: GPTBot\nSitemap: https://t.example/s.xml\nUser-agent: *\nDisallow:\nDisallow: /privado # fin',
    );
    expect(r.grupos).toHaveLength(1);
    expect(evaluar(r, BOT, '/privado/x').permitido).toBe(false);
    expect(evaluar(r, BOT, '/publico').permitido).toBe(true);
  });

  test('rutas con tildes: la regla en claro bloquea la ruta codificada', () => {
    const r = analizarRobots('User-agent: *\nDisallow: /categoría\nDisallow: /a%c3%b1o');
    expect(evaluar(r, BOT, '/categor%C3%ADa/fusiles').permitido).toBe(false);
    expect(evaluar(r, BOT, '/año').permitido).toBe(false);
    expect(normalizarRuta('/café%2fx')).toBe('/caf%C3%A9%2Fx');
  });

  test('lee Content-Signal (formato de contentsignals.org) y detecta la prohibición de IA', () => {
    const r = analizarRobots(
      '# As a condition of accessing this website...\nUser-Agent: *\nContent-Signal: search=yes, ai-train=no\nAllow: /\n',
    );
    const e = evaluar(r, BOT, '/');
    expect(e.senales).toEqual({ search: 'yes', 'ai-train': 'no' });
    expect(prohibeIa(e.senales)).toBe(true);
    expect(prohibeIa({ search: 'yes', 'ai-input': 'yes', 'ai-train': 'yes' })).toBe(false);
    expect(r.lineasReserva).toEqual(['Content-Signal: search=yes, ai-train=no']);
  });

  test('una Content-Signal que no se entiende entera cuenta como reserva', () => {
    const r = analizarRobots('User-agent: *\nContent-Signal: ai-train=no; search=yes\nAllow: /');
    expect(r.reservaDudosa).toBe(true);
    expect(reservaIa(r, BOT).reserva).toBe(true);
  });

  test('Content-Usage y vetos a bots de IA también son reservas', () => {
    expect(reservaIa(analizarRobots('Content-Usage: train-ai=n'), BOT).reserva).toBe(true);
    const vetos = analizarRobots('User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /');
    expect(botsIaVetados(vetos)).toEqual(['gptbot']);
    expect(reservaIa(vetos, BOT).motivos[0]).toContain('gptbot');
    expect(reservaIa(analizarRobots('User-agent: *\nAllow: /'), BOT)).toEqual({ reserva: false, motivos: [] });
  });

  test('ignora basura y BOM; sin robots, todo permitido y sin señales', () => {
    const r = analizarRobots('﻿esto no es robots\n<html>');
    expect(evaluar(r, BOT, '/lo-que-sea')).toEqual({ permitido: true, regla: null, crawlDelay: null, senales: {} });
  });
});

describe('robots.txt: robustez', () => {
  test('patrones con muchos comodines no tardan (sin retroceso exponencial)', () => {
    const r = analizarRobots(`User-agent: *\nDisallow: /${'*a'.repeat(30)}x`);
    const t0 = performance.now();
    expect(evaluar(r, BOT, `/${'a'.repeat(200)}`).permitido).toBe(true);
    expect(performance.now() - t0).toBeLessThan(50);
  });

  test('corta robots.txt enormes y reglas absurdas', () => {
    const largo = analizarRobots(`User-agent: *\n${'#'.repeat(MAX_ROBOTS)}\nDisallow: /`);
    expect(evaluar(largo, BOT, '/').permitido).toBe(true);
    const regla = analizarRobots(`User-agent: *\nDisallow: /${'x'.repeat(5000)}`);
    expect(regla.grupos[0]?.reglas).toEqual([]);
  });

  test('casa() con prefijos, comodines y $', () => {
    expect(casa('/a', '/abc')).toBe(true);
    expect(casa('/a$', '/abc')).toBe(false);
    expect(casa('/*.pdf$', '/x/y.pdf')).toBe(true);
    expect(casa('/p*s/', '/productos/m4')).toBe(true);
    expect(casa('/p*z', '/productos')).toBe(false);
    expect(casa('/', '/')).toBe(true);
  });
});
