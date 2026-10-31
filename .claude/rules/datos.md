---
paths:
  - "packages/db/**"
---

# Reglas de datos (D1)
- Tres bases: `core` (catálogo, usuarios, comunidad), `mercado` (fuentes, listados, ofertas, eventos de precio) y `busqueda` (índices FTS5 reconstruibles). No hay JOIN entre bases: se compone en el servicio.
- Las tablas virtuales (FTS5) van solo en `busqueda`, porque D1 no exporta bases con tablas virtuales y `core` y `mercado` deben poder exportarse para las copias.
- Migraciones con drizzle-kit, siempre aditivas; nunca se edita una ya aplicada. Cada migración tiene un test que la aplica desde cero.
- Presupuesto del plan gratuito: 100.000 filas escritas y 5 M leídas al día; desde septiembre de 2026 las consultas fallan al superarlo. Por tanto:
  - nunca una fila por visita: los contadores van en Durable Objects con volcado periódico;
  - un índice para cada consulta frecuente;
  - `batch()` para escrituras múltiples.
- Dinero en céntimos enteros + moneda; longitudes en mm; fechas ISO 8601 en UTC; IDs de texto ordenables (ULID o UUIDv7).
- Los datos de ejemplo llevan `is_demo = 1` y nunca llegan a producción.
