import { describe, expect, test } from 'vitest';
import { type MetaReader, readAllBases, readBaseStatus } from './status.ts';

const fakeDb = (rows: Array<{ key: string; value: string }> | Error): MetaReader => ({
  prepare: () => ({
    all: async <T>() => {
      if (rows instanceof Error) throw rows;
      return { results: rows as T[] };
    },
  }),
});

describe('readBaseStatus', () => {
  test('ok cuando la base se identifica con su nombre', async () => {
    const s = await readBaseStatus(
      'core',
      fakeDb([
        { key: 'base', value: 'core' },
        { key: 'migracion', value: '0000_meta' },
      ]),
    );
    expect(s).toEqual({ base: 'core', binding: 'CORE', state: 'ok', reportedName: 'core', migration: '0000_meta' });
  });

  test('detecta un binding cruzado', async () => {
    const s = await readBaseStatus('core', fakeDb([{ key: 'base', value: 'mercado' }]));
    expect(s.state).toBe('cruzada');
    expect(s.reportedName).toBe('mercado');
  });

  test('distingue una base sin migrar de un error cualquiera, sin filtrar el mensaje', async () => {
    expect((await readBaseStatus('mercado', fakeDb(new Error('D1_ERROR: no such table: meta')))).state).toBe(
      'sin_migrar',
    );
    const other = await readBaseStatus('busqueda', fakeDb(new Error('detalle interno')));
    expect(other.state).toBe('error');
    expect(JSON.stringify(other)).not.toContain('detalle interno');
  });
});

describe('readAllBases', () => {
  test('lee las tres bases en orden', async () => {
    const db = (name: string) => fakeDb([{ key: 'base', value: name }]);
    const all = await readAllBases({ CORE: db('core'), MERCADO: db('mercado'), BUSQUEDA: db('busqueda') });
    expect(all.map((s) => [s.base, s.state])).toEqual([
      ['core', 'ok'],
      ['mercado', 'ok'],
      ['busqueda', 'ok'],
    ]);
  });
});
