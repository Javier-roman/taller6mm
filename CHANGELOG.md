# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Fechas en ISO 8601. Aún no hay
versiones publicadas: todo va en «Sin publicar», agrupado por fase.

## [Sin publicar]

### Fase 1 · Propuestas de La Armería (en curso, sin fusionar)
- Prototipo A, 3D en tiempo real con React Three Fiber (rama `spike/armeria-a-3d`).
- Prototipo B, 2,5D re-iluminable con pases horneados y WebGL2 (rama `spike/armeria-b-25d`).
- Informe comparativo con capturas, pesos, FPS y revisiones (`docs/informes/fase-1-propuestas.md`).

### Fase 0 · Cimientos
#### En revisión
- S3: entornos `preview` y `production` en `wrangler.jsonc`, previews por PR con Worker Previews, receta de
  activación de Cloudflare y ADR-0008 (PR en borrador; sin recursos creados).
- S6: README, CONTRIBUTING y este registro de cambios.

#### Añadido
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
