---
name: informe-fase
description: Informe de cierre de fase contra los criterios de aceptación de docs/10-roadmap.md, con evidencias.
argument-hint: "[número de fase]"
---

Genera `docs/informes/fase-$ARGUMENTS.md` con:
1. Tabla con los criterios de aceptación de la fase (de `docs/10-roadmap.md` y del documento de su área), su estado (✅/⚠️/❌) y la evidencia: salida de tests, URL de preview, capturas, métricas de Lighthouse y tamaños de bundle.
2. Qué se ha construido, por área, y cómo probarlo en 5 pasos.
3. Decisiones tomadas (ADRs nuevos o cambiados) y deuda técnica registrada.
4. Riesgos y preguntas abiertas para Javi.
5. Propuesta de plan para la siguiente fase: rebanadas verticales y su orden.

Enseña a Javi un resumen de 10 líneas y la ruta del archivo.
