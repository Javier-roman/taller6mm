import { describe, expect, test } from 'vitest';
import pkg from '../package.json' with { type: 'json' };
import { buildUserAgent } from './user-agent.ts';

describe('buildUserAgent', () => {
  test('identifica al bot, su versión y la página de exclusión', () => {
    expect(buildUserAgent({ infoUrl: 'https://taller6mm.example/bot' })).toBe(
      `Taller6mmBot/${pkg.version} (+https://taller6mm.example/bot)`,
    );
    expect(buildUserAgent({ version: '1.2.3', infoUrl: 'https://taller6mm.example/bot' })).toBe(
      'Taller6mmBot/1.2.3 (+https://taller6mm.example/bot)',
    );
  });

  test.each([
    ['http://taller6mm.example/bot', 'https'],
    ['https://taller6mm.example/', '/bot'],
    ['https://taller6mm.example/bot?utm=x', '/bot'],
    ['https://user:pass@taller6mm.example/bot', '/bot'],
    ['no es una url', 'no válida'],
  ])('rechaza %s', (infoUrl, message) => {
    expect(() => buildUserAgent({ infoUrl })).toThrow(message);
  });

  test('rechaza versiones que no son semver', () => {
    expect(() => buildUserAgent({ version: 'latest', infoUrl: 'https://taller6mm.example/bot' })).toThrow('Versión');
  });
});
