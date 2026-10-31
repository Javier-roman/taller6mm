---
name: verify
description: Puerta de calidad de Taller6mm. Úsala antes de cada commit y antes de dar por terminada cualquier tarea. Ejecuta las comprobaciones estáticas y los tests, y verifica el cambio en la app en marcha.
---

# Verificar el cambio

1. Ejecuta `pnpm verify` (lint + typecheck + tests unitarios + build). Si falla, corrige la causa y repite. Nunca desactives reglas, tests ni tipos para que pase.
2. Según lo que toque el cambio:
   - **Interfaz** (`apps/web/**`, `packages/ui/**`):
     1. Levanta `pnpm --filter @taller6mm/web dev` en segundo plano.
     2. Abre las rutas afectadas con el MCP de Playwright a 390×844 y a 1440×900 y haz capturas.
     3. Comprueba que la consola no tiene errores y que el resultado respeta `docs/02-experiencia-y-diseno.md`.
     4. Prueba el teclado (Tab, Enter, Esc) y `prefers-reduced-motion`.
   - **Motor de compatibilidad**: `pnpm --filter @taller6mm/compat test`, incluidos los builds de oro.
   - **Ingesta**: los tests con fixtures de la fuente afectada. Nunca peticiones `--live`.
   - **Datos y migraciones**: aplica en local desde cero (`pnpm db:reset:local`) y ejecuta sus tests.
   - **Assets**: la validación de fidelidad del asset afectado.
3. Si añadiste dependencias de cliente, revisa el tamaño con `pnpm size`.
4. Resume en 3-5 líneas qué comprobaste, el resultado y lo que no pudiste verificar (y por qué).

Si alguno de estos comandos aún no existe, créalo en el paquete correspondiente siguiendo `CLAUDE.md`.
