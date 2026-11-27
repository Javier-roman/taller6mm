// Formato de los archivos de `catalogo/` (claves en español, tal como los escriben los agentes y Javi).
// Se validan con Zod antes de sembrar: un archivo que cambie de forma rompe la semilla, no la ensucia.
import { z } from 'zod';

const SpanishConfidence = z.enum(['alta', 'media', 'baja']);
const Estado = z.enum(['verificado', 'pendiente']);
const Fecha = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const Fuente = z.object({ url: z.string(), fecha_consulta: Fecha }).nullable();

export const InterfacesFileSchema = z.object({
  interfaces: z.array(
    z.object({
      id: z.string(),
      nombre: z.string(),
      tipo: z.string(),
      descripcion: z.string(),
      cotas: z.array(
        z.object({
          nombre: z.string(),
          valor: z.number(),
          unidad: z.enum(['mm', 'in']),
          fuente: z.string(),
          fecha_consulta: Fecha,
          confianza: SpanishConfidence,
          nota: z.string().nullish(),
        }),
      ),
      estado: Estado,
      fuente: Fuente,
      confianza: SpanishConfidence.nullable(),
      notas: z.string().nullable(),
    }),
  ),
});

export const PlataformasFileSchema = z.object({
  familias: z.array(z.object({ id: z.string(), nombre: z.string() })),
  plataformas: z.array(
    z.object({
      id: z.string(),
      nombre: z.string(),
      familia: z.string(),
      mecanismos: z.array(z.string()),
      fabricantes: z.array(z.string()),
      variantes: z.array(z.string()),
      interfaces: z.array(z.string()),
      pozo_cargador: z.string().nullable(),
      estado: Estado,
      fuente: Fuente,
      confianza: SpanishConfidence.nullable(),
      notas: z.string().nullable(),
    }),
  ),
});

export const FamiliasFileSchema = z.object({
  familias: z.array(
    z.object({
      id: z.string(),
      nombre: z.string(),
      grupo: z.string(),
      parametros: z.array(z.string()),
      interfaces: z.array(z.string()),
      aplica_a: z.array(z.string()),
      marcas_ejemplo: z.array(z.string()),
      nivel_esperado: z.enum(['T0', 'T1', 'T2', 'T3']),
      estado: Estado,
      fuente: Fuente,
      confianza: SpanishConfidence.nullable(),
      notas: z.string().nullable(),
    }),
  ),
});

export const CotasFileSchema = z.object({
  cotas: z.array(
    z.object({
      id: z.string(),
      ambito: z.enum(['pieza', 'replica']),
      familia: z.string().nullable(),
      producto: z.string(),
      parametro: z.string(),
      valor: z.number().nullable(),
      valor_min: z.number().nullable(),
      valor_max: z.number().nullable(),
      unidad: z.string(),
      fuentes: z.array(z.string()),
      fecha_consulta: Fecha.nullable(),
      confianza: SpanishConfidence.nullable(),
      estado: z.enum(['citado', 'pendiente']),
      nota: z.string().nullable(),
    }),
  ),
});

/** Piezas generadas (m4-tanda3, ak-piezas, pistolas-piezas, m4-oleada1-*): misma forma en todos. */
export const PiezasFileSchema = z.object({
  generado: Fecha,
  interfaces_nuevas: z.array(z.object({ id: z.string(), descripcion: z.string(), estado: z.string() })).default([]),
  piezas: z.array(
    z.object({
      id: z.string(),
      elemento: z.string().nullable(),
      familia: z.string(),
      sha256_glb: z.string().nullable(),
      parametros: z.record(z.string(), z.unknown()),
      cotas: z.array(
        z.object({
          clave: z.string(),
          valor_mm: z.number().nullable(),
          fuente: z.string(),
          fecha: Fecha.optional(),
          confianza: SpanishConfidence.nullable(),
          desconocido: z.boolean(),
        }),
      ),
      pendientes: z.array(z.unknown()).default([]),
      requiere: z.array(z.string()),
      ofrece: z.array(z.string()),
      nivel_puerta: z.enum(['T0', 'T1', 'T2', 'T3']).nullish(),
      publicable_3d: z.boolean(),
      publicable: z.boolean(),
      nivel_nota: z.string().nullish(),
      es_demo: z.boolean(),
      license_status: z.string(),
      licencia_texto: z.string().nullish(),
    }),
  ),
});

export type InterfacesFile = z.infer<typeof InterfacesFileSchema>;
export type PlataformasFile = z.infer<typeof PlataformasFileSchema>;
export type FamiliasFile = z.infer<typeof FamiliasFileSchema>;
export type CotasFile = z.infer<typeof CotasFileSchema>;
export type PiezasFile = z.infer<typeof PiezasFileSchema>;

/** Archivos ya leídos (JSON sin validar), indexados por nombre. */
export interface RawCatalog {
  interfaces: unknown;
  plataformas: unknown;
  familias: unknown;
  cotas: unknown;
  /** nombre del archivo (sin .json) → contenido */
  piezas: Record<string, unknown>;
}
