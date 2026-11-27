# ADR-0012 — Esquema del catálogo en `core`: ids estables, cotas con CHECK y semillas is_demo

- **Estado**: Propuesta (pendiente del OK de Javi al fusionar el PR de la rebanada C2)
- **Fecha**: 2026-11-27
- **Decisores**: Javi (+ Claude Code)

## Contexto
- La Fase 2 necesita el esquema de catálogo en D1 (`docs/07 §3.1`) antes de las fichas, la búsqueda y la trastienda. El catálogo existente vive en `catalogo/*.json` (101 plataformas, 83 familias de piezas, 89 interfaces, cotas de airsoft y piezas generadas).
- ADR-0011: las medidas en mm solo se muestran con fuente; el nivel de cada pieza es siempre visible; lo desconocido es `null` + bandera.
- El motor de compatibilidad está aparcado: este esquema solo guarda los datos que necesitará (interfaces que ofrece y requiere cada pieza), sin veredictos.

## Decisión
1. **Ids de texto estables (slugs) en el catálogo de referencia** (marcas, plataformas, interfaces, familias, categorías): son los del JSON, legibles en URLs y revisables en diffs. Los ids ULID/UUIDv7 de `docs/07 §3.4` se usan para lo que crean los usuarios y el sistema (builds, comentarios, auditoría, y réplicas y piezas dadas de alta por la trastienda).
2. **Las reglas de honestidad las impone la base con `CHECK`**, además de Zod en `@taller6mm/domain`:
   - una cota (`dimensions`) con `status = 'pending'` lleva todo `NULL` y `sources = []`; una conocida lleva valor (o rango), fuente (lista JSON de URLs https), confianza y fecha de consulta;
   - lo `verified` (interfaces, plataformas, familias) exige URL, fecha y confianza;
   - un activo (`assets`) con licencia `third-party-reference` o `is_demo = 1` nunca es `publishable`; pertenece a una pieza o a una réplica, nunca a ambas ni a ninguna;
   - el nivel (`level`) es `T0`–`T3`, por defecto `T0`; la etiqueta visible (ilustrativa, aproximada, verificada) se **deriva** en `domain` (`fidelityLabel`), no se duplica en columna.
3. **`dimensions` es polimórfica** (`subject_type` + `subject_id`, única por sujeto y clave). Guarda el valor tal como se publicó (hasta 0,01 mm en las interfaces, que vienen de pulgadas), sin redondear a 0,1 mm: `Millimeters` se mantiene para la geometría y la escena.
4. **Qué ofrece y qué requiere**: `part_interfaces` (rol `offers`/`requires`). Las familias del catálogo no distinguen el sentido, así que `part_family_interfaces` usa el rol `unspecified` en vez de suponerlo.
5. **Búsqueda**: tabla virtual FTS5 `search_catalog` en `busqueda` (migración SQL a mano: Drizzle no describe tablas virtuales), con `unicode61 remove_diacritics 2`. Es un índice reconstruible, nunca fuente de verdad.
6. **Semillas** (`pnpm db:seed:local`): `scripts/db-seed.mjs` lee `catalogo/*.json`, valida con Zod y genera SQL en `packages/db/seeds/` (ignorado por git). Todo con `is_demo = 1`; cada ejecución borra antes solo lo `is_demo` y vuelve a insertar. Reglas al importar:
   - solo entra como cota con valor la que trae URL https de fuente; los parámetros de barrido y las estimaciones «a ojo» de las piezas no son cotas y no se siembran (se cuentan en el informe de la semilla);
   - lo desconocido entra como cota `pending`;
   - las interfaces que citan las piezas pero no tienen ficha se crean como `proposed`, sin fuente ni cotas;
   - no se inventan réplicas: la tabla `replicas` queda vacía hasta que haya un modelo de fabricante con fuente (`/nueva-replica`); las 15 cotas de réplicas de `cotas-airsoft.json` esperan a esas filas.
7. Fuera de esta rebanada: `mercado`, comunidad, moderación, auditoría, endpoints y compatibilidad.

## Alternativas consideradas
| Opción | Pros | Contras | Por qué no |
|---|---|---|---|
| ULID para todo el catálogo | Un solo criterio de ids | Ids ilegibles; cada reimportación cambiaría referencias | Los slugs ya son estables y únicos en el JSON |
| Una tabla de cotas por tipo de sujeto | FK reales | Cinco tablas casi iguales | La validación de existencia se hace en la semilla y en la capa de datos |
| Columna `fidelity_label` además de `level` | Consulta directa | Dos fuentes de verdad que pueden discrepar | Se deriva en una función pura |
| Sembrar las cotas estimadas con `confidence = low` | Más datos | Rompe el principio 2: son valores sin fuente | Se quedan como parámetros del generador |
| Sembrar réplicas desde `variantes` | Tabla poblada | `variantes` no son modelos de fabricante | No se inventa |

## Consecuencias
- **Positivas**: la base rechaza datos deshonestos aunque falle el código; el catálogo de ejemplo se carga en un comando y es reproducible.
- **Negativas**: las migraciones con `CHECK` son más rígidas (cambiarlos exige recrear la tabla en SQLite). `dimensions` no tiene FK al sujeto.
- **Trabajo generado**: dar de alta réplicas con fuente; decidir el sentido de las interfaces por familia cuando se reabra la compatibilidad; ficha para las 19 interfaces `proposed`.

## Validación
- `pnpm --filter @taller6mm/db test`: migraciones desde cero, rechazo de cotas sin fuente, de activos de terceros publicables y de niveles fuera de T0–T3; semillas idempotentes, todo `is_demo`, cotas desconocidas con `NULL` + `pending`, sin huérfanos ni violaciones de FK, y búsqueda FTS5 sin acentos.

## Disparadores de revisión
- Si D1 admite `ALTER TABLE ... ADD CONSTRAINT` o la rigidez de los `CHECK` estorba.
- Si aparecen fuentes por réplica que exijan cotas por variante.
- Si el motor de compatibilidad necesita el sentido de las interfaces por familia.
