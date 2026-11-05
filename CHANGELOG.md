# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Fechas en ISO 8601. Aún no hay
versiones publicadas: todo va en «Sin publicar», agrupado por fase.

## [Sin publicar]

### Herramientas de IA (2026-11-05)
- Reparto de modelos de Claude Code: sesión `opusplan` con esfuerzo medio, asesor en Opus, subagentes y skills
  con su modelo y esfuerzo, y el nuevo subagente `documentador` (`docs/ia/modelos.md`).
- Gemini como ayudante con Antigravity CLI (`agy` 1.4.12 por winget): `scripts/gemini.mjs`, skill `/gemini`
  y subagente `delegado-gemini`, en solo lectura y sin secretos; regla del hook guardián contra modos inseguros.
- `pnpm ia:uso`: tokens por modelo y día a partir de los registros locales (solo contadores), con línea base.
- CLAUDE.md: resumen del reparto de modelos y reglas para instalar herramientas.

### Fase 1 · Propuestas de La Armería (en curso, sin fusionar)
- Prototipo A, 3D en tiempo real con React Three Fiber (rama `spike/armeria-a-3d`).
- Prototipo B, 2,5D re-iluminable con pases horneados y WebGL2 (rama `spike/armeria-b-25d`).
- Informe comparativo con capturas, pesos, FPS y revisiones (`docs/informes/fase-1-propuestas.md`).

### Fase 0 · Cimientos
#### Añadido
- **S6 · Documentación** (#9, 2026-11-04): README con la puesta en marcha en 5 pasos, CONTRIBUTING (ramas,
  commits y definición de terminado), este registro de cambios, CLAUDE.md al stack real (Astro 7, Node 26,
  pnpm 12, TypeScript 6 y Vitest 4.1) y docs/07 y docs/08 al día.
- **S3 · Cloudflare de preview y previews por PR** (#8, 2026-11-04):
  - Entornos `preview` y `production` (configurado y cerrado) en `wrangler.jsonc`.
  - Recursos de preview: tres bases D1, la cola de ingesta con su cola de mensajes fallidos y los Workers
    `taller6mm-web-preview` y `taller6mm-jobs-preview`.
  - Página de estado `/` con cada binding.
  - Una Preview por PR (Worker Previews): se construye sin secretos y se despliega desde `main` con
    `workflow_run`, solo con el código del PR y la configuración de `main`.
  - Recolector diario y ZAP semanal contra la preview.
  - Receta de activación en `docs/runbooks/cloudflare-s3.md` y **ADR-0008 aceptado**.
  - Pendiente: los buckets R2, porque falta activar R2 en la cuenta.

#### Seguridad
- Tres revisiones de `revisor-seguridad` sobre S3. La Preview de un PR ya no usa la configuración que trae el
  propio PR (A1, alto). El alcance real de los tokens del CI, que es toda la cuenta, queda como riesgo
  aceptado en el ADR-0008 (M1). Pendientes en #11 y #12.
- **S5 · Sistema de diseño** (#7, 2026-11-01): tokens de color, tipografía, espacio, sombras, luces y
  movimiento en `packages/ui`; fuentes autoalojadas; componentes Botón, Placa, Rótulo, Insignia de fidelidad,
  Barra de dato y Cargador; página `/sistema`; e2e con axe y presupuestos de tamaño.
- **S4 · Seguridad base** (#6): cabeceras y CSP con hashes, `security.txt`, `SECURITY.md` y modelo de amenazas
  STRIDE.
- **S2 · Monorepo y calidad** (#5): pnpm + Turborepo, paquetes base con tests, Biome, TypeScript estricto,
  Vitest, lefthook con gitleaks, CI v1 (también en Windows), OSV-Scanner, Semgrep y Renovate.
- **ADR-0001** (#3 y #9): cifras del spike del stack en la nube y, el 03-11, en Cloudflare (505 KiB gz, arranque de 20 ms, CPU p99 de 4 ms en caliente; riesgo en frío vigilado). **Aceptada.**
- **S0 · Arranque seguro** (#1, #4): renombrado a Taller6mm, guardián de comandos con tests, MCP de Playwright
  multiplataforma, ajustes de seguridad del repositorio y plan de la Fase 0.

#### Cambiado
- `--naranja-senal` pasa a `#E75A31` y `--estado-error` y `--estado-desconocido` se aclaran para cumplir AA
  como texto (S5).
