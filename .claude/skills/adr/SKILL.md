---
name: adr
description: Crea un registro de decisión de arquitectura (ADR) numerado a partir de la plantilla del proyecto.
argument-hint: "[título de la decisión]"
---

1. Busca el siguiente número libre en `docs/adr/` (formato `NNNN-titulo-en-kebab.md`).
2. Copia `docs/adr/0000-plantilla.md` y rellénala para: $ARGUMENTS. Incluye alternativas reales con sus pros y contras, datos verificados (con fecha y fuente) y disparadores de revisión.
3. Déjalo en estado `Propuesta`, enlázalo desde la tabla de ADRs de `docs/07-arquitectura.md` y pide el OK de Javi para pasarlo a `Aceptada`.
