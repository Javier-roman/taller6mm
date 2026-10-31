import fc from 'fast-check';
import { describe, expect, test } from 'vitest';
import { confidenceLabel, fits, overallVerdict, VERDICTS, type Verdict, VerdictReportSchema } from './index.ts';

const verdict = fc.constantFrom(...VERDICTS);

describe('VerdictReport', () => {
  test('exige motivo, fuente y confianza', () => {
    const ok = VerdictReportSchema.safeParse({
      verdict: 'compatible_con_adaptador',
      reason: 'Bocacha de rosca a derechas (CW) y réplica a izquierdas (CCW): necesita adaptador.',
      source: { kind: 'estandar', reference: 'thread.14mm-ccw' },
      confidence: 0.9,
    });
    expect(ok.success).toBe(true);

    const sinMotivo = VerdictReportSchema.safeParse({
      verdict: 'compatible',
      reason: '   ',
      source: { kind: 'comunidad', reports: 3 },
      confidence: 0.6,
    });
    expect(sinMotivo.success).toBe(false);

    const comunidadSinInformes = VerdictReportSchema.safeParse({
      verdict: 'compatible',
      reason: 'Montado por la comunidad',
      source: { kind: 'comunidad', reports: 0 },
      confidence: 0.6,
    });
    expect(comunidadSinInformes.success).toBe(false);
  });

  test('la confianza va de 0 a 1 y tiene etiqueta', () => {
    expect(confidenceLabel(0.95)).toBe('alta');
    expect(confidenceLabel(0.8)).toBe('alta');
    expect(confidenceLabel(0.5)).toBe('media');
    expect(confidenceLabel(0.2)).toBe('baja');
    expect(() => confidenceLabel(1.2)).toThrow();
  });
});

describe('overallVerdict', () => {
  test('manda el peor veredicto', () => {
    expect(overallVerdict([])).toBe('compatible');
    expect(overallVerdict(['compatible', 'compatible_con_adaptador'])).toBe('compatible_con_adaptador');
    expect(overallVerdict(['requiere_modificacion', 'desconocido'])).toBe('desconocido');
    expect(overallVerdict(['desconocido', 'incompatible'])).toBe('incompatible');
  });

  test('propiedad: no depende del orden (docs/03 §5.3)', () => {
    fc.assert(
      fc.property(fc.array(verdict), (vs) => {
        const reversed = [...vs].reverse();
        const sorted = [...vs].sort();
        expect(overallVerdict(vs)).toBe(overallVerdict(reversed));
        expect(overallVerdict(vs)).toBe(overallVerdict(sorted));
      }),
    );
  });

  test('propiedad: un desconocido nunca se presenta como compatible', () => {
    fc.assert(
      fc.property(fc.array(verdict), (vs) => {
        expect(fits(overallVerdict([...vs, 'desconocido' as Verdict]))).toBe(false);
      }),
    );
  });

  test('propiedad: quitar piezas no empeora el estado global', () => {
    fc.assert(
      fc.property(fc.array(verdict, { minLength: 1 }), fc.nat(), (vs, i) => {
        const without = vs.filter((_, k) => k !== i % vs.length);
        const order = [
          'compatible',
          'compatible_con_adaptador',
          'requiere_modificacion',
          'desconocido',
          'incompatible',
        ];
        expect(order.indexOf(overallVerdict(without))).toBeLessThanOrEqual(order.indexOf(overallVerdict(vs)));
      }),
    );
  });
});
