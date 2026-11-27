-- Índice de búsqueda del catálogo (docs/07 §3.3). Tabla virtual FTS5: por eso vive en `busqueda` y no
-- en `core` (D1 no exporta bases con tablas virtuales). Se reconstruye desde `core`; no es fuente de verdad.
-- `kind` y `entity_id` no se indexan: sirven para volver a la ficha. `is_demo` marca las filas de ejemplo.
CREATE VIRTUAL TABLE `search_catalog` USING fts5(
	`kind` UNINDEXED,
	`entity_id` UNINDEXED,
	`is_demo` UNINDEXED,
	`name`,
	`brand`,
	`model`,
	`aliases`,
	tokenize = "unicode61 remove_diacritics 2"
);
