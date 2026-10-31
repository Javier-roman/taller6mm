---
name: revisar-ui
description: Revisión visual y de experiencia de una ruta con capturas reales, contrastada con la dirección de arte de Taller6mm. Corrige lo bloqueante y lo importante.
argument-hint: "[ruta, p. ej. / o /banco]"
---

Revisa la ruta `$ARGUMENTS` (si está vacía, `/`).

1. Comprueba que el servidor de desarrollo está en marcha y usa el MCP de Playwright.
2. Haz capturas a 390×844, 834×1194 y 1440×900, más una con `prefers-reduced-motion: reduce`. Guárdalas en `docs/informes/capturas/<fecha>-<ruta>/`.
3. Delega el análisis al subagente `critico-diseno` y pásale las capturas, la ruta y las secciones relevantes de `docs/02-experiencia-y-diseno.md`.
4. Pasa axe (WCAG 2.2 AA) y revisa la consola.
5. Aplica las correcciones de severidad **bloqueante** e **importante**. Deja listadas las de **pulido**.
6. Repite las capturas y entrega el antes y el después con un resumen de 3-5 líneas.
