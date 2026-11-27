# Plan C2: esquema de datos y semillas del catálogo

Rebanada C2 de la Fase 2 (`docs/10-roadmap.md`). Sin compatibilidad, sin endpoints, sin cambios en `apps/web`. Decisiones en `docs/adr/0012-esquema-core-catalogo.md`.

## Tablas de `core` (migración `0001_catalogo`)
| Tabla | Para qué |
|---|---|
| `brands` | Marcas (limpiadas de los `fabricantes` del catálogo) |
| `platform_families`, `platforms` | Plataformas (M4, AK…) con su familia, mecanismos, variantes y pozo de cargador |
| `platform_interfaces`, `platform_brands` | Interfaces que expone y fabricantes de cada plataforma |
| `replicas` | Modelo de un fabricante sobre una plataforma, con nivel T0–T3 (vacía: no se inventan) |
| `categories`, `part_families` | Taxonomía de piezas y familias con parámetros y nivel esperado |
| `part_family_platform_families`, `part_family_interfaces` | A qué plataformas sirven y qué interfaces manejan (rol `unspecified`) |
| `parts`, `part_interfaces` | Piezas concretas, con lo que ofrecen y requieren |
| `interfaces` | Estándares (Picatinny, rosca 14 mm CW/CCW, M-LOK, STANAG…) con estado y fuente |
| `dimensions` | Cotas con fuente, confianza y fecha; desconocida = `NULL` + `pending` |
| `assets` | Referencia a nivel y licencia (clave R2 opcional), nunca binarios |

`busqueda`: migración `0001_catalogo_fts` con la tabla FTS5 `search_catalog` (nombre, marca, modelo, alias).

## Cumplimiento de la arquitectura
- Drizzle + drizzle-kit sobre D1; migraciones aditivas (la `0000_meta` no se toca; el test comprueba que sigue primera y sin cambios).
- Zod 4 en `packages/domain/src/catalog.ts` (cotas, activos, nivel) y en `packages/db/src/seed/sources.ts` (formato de los JSON).
- Longitudes en mm (la geometría usa `Millimeters`; las cotas de interfaces conservan 0,01 mm); fechas ISO 8601 en UTC (solo día en las consultas); dinero no aparece aún (es de `mercado`).
- `is_demo` en todo lo sembrado; la semilla solo borra y reinserta lo `is_demo`.

## Semillas
`pnpm db:seed:local` → `scripts/db-seed.mjs` (valida, genera `packages/db/seeds/<base>/0001_catalogo.sql`) → `wrangler d1 execute --local`. Recuento actual: 101 plataformas, 83 familias de piezas, 110 interfaces (19 `proposed`), 140 piezas con su activo, 248 cotas, 457 filas de búsqueda. 664 cotas de piezas sin fuente (parámetros de barrido y estimaciones) no se siembran.

## Fuera de alcance
`mercado`, comunidad, auditoría, endpoints, fichas SSR, trastienda y motor de compatibilidad.
