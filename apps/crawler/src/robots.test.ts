import { describe, expect, test } from 'vitest';
import { analizarRobots, evaluar, prohibeIa } from './robots.ts';

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

  test('un grupo con nuestro nombre sustituye al de *', () => {
    const r = analizarRobots('User-agent: *\nDisallow: /\n\nUser-agent: Taller6mmBot\nAllow: /\nCrawl-delay: 12');
    expect(evaluar(r, BOT, '/x').permitido).toBe(true);
    expect(evaluar(r, BOT, '/x').crawlDelay).toBe(12);
    expect(evaluar(r, 'OtroBot/1.0', '/x').permitido).toBe(false);
  });

  test('varios User-agent seguidos comparten grupo; Disallow vacío no prohíbe', () => {
    const r = analizarRobots('User-agent: GPTBot\nUser-agent: *\nDisallow:\n# comentario\nDisallow: /privado # fin');
    expect(r.grupos).toHaveLength(1);
    expect(evaluar(r, BOT, '/privado/x').permitido).toBe(false);
    expect(evaluar(r, BOT, '/publico').permitido).toBe(true);
  });

  test('lee Content-Signal (formato de contentsignals.org) y detecta la prohibición de IA', () => {
    const r = analizarRobots(
      '# As a condition of accessing this website...\nUser-Agent: *\nContent-Signal: search=yes, ai-train=no\nAllow: /\n',
    );
    const e = evaluar(r, BOT, '/');
    expect(e.senales).toEqual({ search: 'yes', 'ai-train': 'no' });
    expect(prohibeIa(e.senales)).toBe(true);
    expect(prohibeIa({ search: 'yes', 'ai-input': 'yes', 'ai-train': 'yes' })).toBe(false);
    expect(prohibeIa({ 'ai-input': 'no' })).toBe(true);
  });

  test('las señales de * valen aunque tengamos grupo propio', () => {
    const r = analizarRobots('User-agent: *\nContent-Signal: ai-input=no\n\nUser-agent: taller6mmbot\nAllow: /');
    expect(evaluar(r, BOT, '/').senales).toEqual({ 'ai-input': 'no' });
  });

  test('ignora basura y BOM; sin robots, todo permitido y sin señales', () => {
    const r = analizarRobots('﻿esto no es robots\n<html>');
    expect(evaluar(r, BOT, '/lo-que-sea')).toEqual({ permitido: true, regla: null, crawlDelay: null, senales: {} });
  });
});
