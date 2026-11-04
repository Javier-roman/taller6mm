# Informe de cierre · Fase 0 «Cimientos»

- **Fecha**: 2026-11-04
- **Estado**: criterios de aceptación cumplidos. Queda **un entregable parcial**: los buckets R2, porque R2 no está activado en la cuenta (issue #15).
- **Plan**: [`fase-0-plan.md`](fase-0-plan.md) · **Roadmap**: [docs/10](../10-roadmap.md#fase-0--cimientos)
- **PR fusionados**: #1, #3, #4, #5, #6, #7, #8, #9, #13 y #14. El #13 entró en `main` como `5f90880`, pero GitHub lo marca como «cerrado» por un 502 (§4). **Abiertos a propósito**: #2 (spike S1, no se fusiona) y #10 (propuestas de la Fase 1, a la espera de Javi).

## 1. Criterios de aceptación

### Aceptación (docs/10)
| Criterio | Estado | Evidencia |
|---|---|---|
| En un clon limpio, `pnpm install && pnpm verify` en verde | ✅ | Clon de `main` (`d411dbe`) en una carpeta temporal de Windows 11 con Node 26.13.0 y pnpm 12.16.1. `pnpm install --frozen-lockfile` tarda 32 s. `pnpm verify` tarda 28 s: Biome, 19 de 19 tareas de Turborepo (typecheck, tests y build, **0 en caché**) y 323 tests de `.claude` y de política (318 pasan y 5 se saltan en Windows; se ejecutan en el CI de Linux) |
| Un PR con CI verde y URL de preview | ✅ | **PR #9**: los 7 checks en verde (verify en Ubuntu y en Windows, e2e con Playwright y axe, gitleaks, OSV y `pnpm audit`, Semgrep y la build de la Preview). El bot comentó «Preview de este PR: `https://pr-9-taller6mm-web-preview.<subdominio>.workers.dev`». La Preview se desplegó con `workflow_run` desde `main` y pasó el humo: tres bases en orden y `noindex` en `/` y `/sistema`. Capturas en [`capturas/2026-11-04-pr-9`](capturas/2026-11-04-pr-9), sin errores de consola. Al fusionar, el CI la borró: `pr-9: borrada` y HTTP 404 |
| `/sistema` con Lighthouse móvil ≥ 95 | ✅ | Mediana de 3 ejecuciones contra la preview (03-11): **98 / 100 / 100 / 100** (rendimiento, accesibilidad, buenas prácticas y SEO). LCP 2,3 s · TBT 0 ms · CLS 0,001. `/`: 100 en las cuatro. Capturas de `/sistema` en [`capturas/2026-11-03-preview`](capturas/2026-11-03-preview) |
| Hooks, skills, subagentes y MCP comprobados | ✅ | Tabla del §1.3 |
| Sin secretos en el repo | ✅ | gitleaks 8.30.1 sobre **92 commits de todas las ramas**, sin fugas (04-11). Además: job «secretos (gitleaks)» en cada PR, pre-commit con lefthook y push protection de GitHub |

### Entregables (docs/10)
| Entregable | Estado | Evidencia |
|---|---|---|
| Monorepo y ADR-0001 validado con un prototipo | ✅ | Spike S1 (rama `spike/0001-stack`, PR #2). [ADR-0001](../adr/0001-stack.md) **aceptado** con cifras en Cloudflare: Worker de 505 KiB gz, arranque de 20 ms y CPU en caliente con p50/p95/p99 de 1/3/4 ms en `/` y de 1/2/3 ms en `get-session` |
| `pnpm verify` y CI completo | ✅ | Los 7 checks de arriba en cada PR, con verify también en `windows-latest`. Renovate con edad mínima de 3 días |
| Seguridad base: cabeceras, gitleaks y modelo de amenazas | ✅ | S4 (#6): cabeceras, CSP con hashes, `security.txt` y `SECURITY.md`. [Modelo de amenazas](../seguridad/modelo-amenazas.md) al día a 04-11 tras las tres revisiones de S3. ZAP semanal contra la preview |
| Recursos de Cloudflare de preview | ⚠️ | Listos: D1 `taller6mm-{core,mercado,busqueda}-preview` y la canario, la cola `taller6mm-ingest-preview` con su cola de mensajes fallidos y los Workers `taller6mm-web-preview` y `taller6mm-jobs-preview`, que `main` despliega solo (`d411dbe`, en verde). **Pendiente**: los buckets R2 `taller6mm-{assets,uploads}-preview`. R2 no está activado en la cuenta (`code: 10042`), issue #15. No bloquea: ningún código usa R2 todavía |
| Tokens de diseño y `/sistema` semilla | ✅ | S5 (#7): tokens, fuentes autoalojadas, componentes y `/sistema` prerenderizada |
| Configuración de Claude Code verificada | ✅ | §1.3 |

### 1.2 Presupuestos (docs/08)
| Medida | Valor | Límite |
|---|---|---|
| JS de cliente (todas las islas) | 68,07 kB gz | 120 kB |
| CSS global | 8,97 kB gz | 15 kB |
| Fuentes woff2 | 354,6 kB | 400 kB |
| Worker `web` (preview) | 1203,51 KiB, 279,77 KiB gz | 3 MiB (plan gratuito) |
| Worker `jobs` | 58,91 KiB, 14,84 KiB gz | 3 MiB |
| CPU de `/` en frío (ADR-0001) | 16–26 ms | 10 ms · ⚠️ riesgo aceptado y vigilado |

### 1.3 Verificación de Claude Code
| Pieza | Qué se comprobó | Evidencia | Estado |
|---|---|---|---|
| Hook `guard-shell` (PreToolUse, Bash y PowerShell) | Deniega leer, copiar o mostrar secretos, meter secretos (`wrangler secret put`, `gh secret set`) y borrar recursos de Cloudflare. Pide confirmación en `wrangler deploy`, `wrangler preview delete`, operaciones sobre bases remotas, push a `main` y `gh pr merge` | 112 tests (`.claude/hooks/guard-shell.test.mjs`), incluidos intentos de saltárselo (comodines, `Copy-Item` a `.example`). En vivo, el 03 y el 04-11 denegó varias búsquedas con patrones que podían tocar archivos de secretos (`.env`, `.*`) y un comando con `gh secret set`: los secretos los metió Javi. Los borrados del spike los ejecutó Javi, como manda la regla | ✅ |
| Hook `guard-mcp` (PreToolUse, MCP de Playwright) | Limita el navegador del MCP | 21 tests (`.claude/hooks/guard-mcp.test.mjs`) | ✅ |
| Hook `check-env` (SessionStart) | Avisa de sesión elevada, de OneDrive, de un Node distinto de `.node-version` y de que falten pnpm o gitleaks | Sin avisos en esta sesión: terminal normal, Node 26.13.0, pnpm 12.16.1 y gitleaks 8.30.1 | ✅ |
| Hook `format` (PostToolUse, Write y Edit) | Formatea con Biome y devuelve los avisos del linter | En vivo el 03-11: reformateó `scripts/preparar-preview.mjs` y avisó de dos variables sin usar, que se corrigieron en el acto | ✅ |
| Skills | `verify`, `revisar-ui`, `adr` e `informe-fase` las puede invocar el agente; `nueva-tienda` y `nueva-replica`, solo Javi (tocan webs externas) | `/revisar-ui /sistema` en S5, `/verify` antes de cada commit con código y `/informe-fase 0` para este informe | ✅ |
| Subagentes | `revisor-seguridad`, `critico-diseno` y `auditor-rendimiento` usados. `ingeniero-ingesta` y `revisor-fidelidad`, definidos para las Fases 4 y 7 | Tres revisiones de seguridad de S3 (la segunda encontró el alto A1 y la tercera no halló críticos ni altos) y la de S4. `critico-diseno` y `auditor-rendimiento` en S5 y en las propuestas de la Fase 1 | ✅ |
| MCP de Playwright | Lanzador multiplataforma, versión fijada, navegador y orígenes acotados | `node .claude/mcp/playwright.mjs --print`: `@playwright/mcp` 0.0.83 (dependencia del repo), `--browser msedge` y `--config .claude/playwright-mcp.json` (perfil aislado y `allowedOrigins` solo de localhost). Capturas locales a 390 y 1440 px. Las de la preview remota se hicieron con Edge lanzado por Playwright, porque el MCP no admite orígenes externos (es intencionado) | ✅ |
| MCP de documentación de Claude Code | Consulta de la documentación oficial | Usado para hooks y skills durante la fase | ✅ |
| Tests de configuración | Todo lo anterior en `pnpm verify` | 195 tests en `.claude/**/*.test.mjs` (194 pasan y 1 se salta en Windows) | ✅ |

## 2. Qué se ha construido
- **Base y calidad** (S2, #5):
  - Monorepo con pnpm 12 y Turborepo: paquetes `domain`, `compat`, `market`, `db`, `ui` y `config`, y apps `web`, `jobs`, `crawler` y `pipeline`.
  - Biome, TypeScript 6 estricto, Vitest 4.1 con el pool de Workers, Playwright con axe y size-limit.
  - lefthook (Biome y gitleaks).
  - CI en Ubuntu y en Windows, con OSV, `pnpm audit`, Semgrep y Renovate.
- **Stack validado** (S1, #3 y #9): Astro 7, React 19, R3F, Drizzle sobre D1 y Better Auth, medidos en Cloudflare (ADR-0001).
- **Seguridad** (S0 #1 y #4, S4 #6, S3):
  - Guardián de comandos y cabeceras con CSP por hashes.
  - Modelo de amenazas STRIDE y ZAP semanal.
  - Protección de `main` y entornos de GitHub restringidos a `main`.
  - Tres revisiones de seguridad de S3.
- **Cloudflare y previews** (S3, #8, #13 y #14):
  - Entornos `preview` y `production`; producción configurada y cerrada.
  - Recursos de preview y página de estado `/`.
  - Una Preview por PR en dos fases: build sin secretos y despliegue con `workflow_run` desde `main`, **solo con el código del PR y la configuración de `main`**.
  - Borrado al cerrar el PR, recolector diario y receta de activación ([runbook](../runbooks/cloudflare-s3.md)).
- **Sistema de diseño** (S5, #7): tokens, fuentes, componentes (Botón, Placa, Rótulo, Insignia de fidelidad, Barra de dato y Cargador) y `/sistema`.
- **Documentación** (S6, #9): README, CONTRIBUTING, CHANGELOG, CLAUDE.md, docs/07 y docs/08 al día con el stack real.

**Cómo probarlo en 5 pasos**
1. `git clone https://github.com/Javier-roman/taller6mm.git` y, dentro, `pnpm install --frozen-lockfile` (Node 26.13, pnpm 12.16).
2. `pnpm verify` → «verify en verde».
3. `pnpm db:migrate:local` y `pnpm dev` → `http://localhost:4321/sistema` (y `/` con el estado de las tres bases).
4. `pnpm e2e` (Playwright y axe) y `pnpm lh` (Lighthouse).
5. Abre un PR contra `main`: CI en verde y el bot comenta la URL `pr-<n>`. Al cerrarlo, la Preview se borra.

## 3. Decisiones y deuda técnica
- **[ADR-0001](../adr/0001-stack.md) · Stack**: aceptado el 03-11. Astro 7, Node 26, pnpm 12, TypeScript 6 y Vitest 4.1, con las cifras en Cloudflare; el riesgo de la CPU en frío queda vigilado y con plan B.
- **[ADR-0008](../adr/0008-entornos-previews-despliegue.md) · Entornos, previews y despliegue**: aceptado el 04-11, al fusionar el #8. Lo más importante que salió por el camino:
  - La Preview de un PR se sube con la configuración de `main`, nunca con la del artefacto (A1, alto, segunda revisión).
  - El número del PR va atado a su commit y se busca por rama, porque GitHub no lo da en el evento de un PR cerrado (#13 y #14).
  - La API de Previews **solo acepta el permiso «Workers» del modelo nuevo (Admin)**, no el clásico «Workers Scripts». Comprobado el 04-11: con «Workers Scripts» y D1 respondía «No access».
- **Decisiones del plan**: las 17 de [`fase-0-plan.md`](fase-0-plan.md) (nombre técnico, Node 26, pnpm con edad mínima, CSP, previews, tokens…).
- **Deuda registrada**:
  - **#11**: endurecimientos de S3. Separar la build del despliegue (M3), la segunda mitad del recolector (B2), versiones antiguas vivas (B3), cuotas de `/` (B5), ajustes de GitHub (B6), límites del artefacto y volver a acotar los tokens (probar «Workers: Editor» y un Worker concreto).
  - **#12**: dependencias de Semgrep con avisos moderados (solo CI).
  - **#15**: R2 y sus buckets.

## 4. Riesgos y preguntas abiertas para Javi
1. **`wrangler logout` (hoy)**: la sesión OAuth de wrangler en tu equipo es la credencial más amplia de todas. Ejecuta `pnpm --filter @taller6mm/web exec wrangler logout`.
2. **R2**: completar el alta en el panel (issue #15). Después creo los dos buckets privados.
3. **Tokens del CI de toda la cuenta** (riesgo aceptado, ADR-0008). El de PR tiene «Workers: Admin». Requisito duro: esta cuenta nunca tendrá datos reales y producción irá en otra cuenta.
4. **Previews públicas**: `noindex` no es privacidad. Hay que poner Cloudflare Access antes de la Fase 2, cuando llegue el inicio de sesión.
5. **CPU en frío por encima de 10 ms** (ADR-0001): vigilado, con plan B (sacar la autenticación a otro Worker o Workers Paid, con tu OK).
6. **Subdominio de `workers.dev`**: identifica la cuenta y aparece en las URLs públicas. Lo aceptaste el 03-11.
7. **GitHub inestable el 04-11**: dos 502 al fusionar. Uno dejó el #13 «cerrado» aunque su squash entró en `main` (`5f90880`); quedó documentado en el PR.
8. **¿Cerramos el PR #2 (spike S1)?** Su rama se conserva como referencia del ADR-0001.
9. **Fase 1**: espero tus decisiones sobre las propuestas A y B (PR #10).

## 5. Propuesta para la Fase 1 (pendiente de tus decisiones)
Rebanadas verticales, en este orden. Cada una con capturas a 390 y 1440 px, `critico-diseno`, `auditor-rendimiento` y tu OK:
1. **ADR-0002 · La Armería**: lo que elijas entre A (3D en tiempo real) y B (2,5D re-iluminable) del PR #10, con sus presupuestos (docs/02 §3.6). Si hace falta ampliar la CSP solo en `/` (wasm, `blob:`), va con su ADR.
2. **Escena base con las tres estanterías** (izquierda, centro y derecha), con póster alternativo y movimiento reducido desde el primer día.
3. **Los 8 módulos clicables** con datos de demo (`is_demo`), cada uno con su zona hacia su función.
4. **Intro de primera visita, linterna y apertura del compactus**, siempre con su alternativa ligera.
5. **Teclado y móvil completos**, axe sin errores y regresión visual en verde.
6. **Componentes base completos en `/sistema`**.

## Anexo · Renombrar la carpeta a `C:\dev\taller6mm`
Hazlo con **Claude Code cerrado**, en una terminal **normal** de PowerShell:
1. Cierra todo lo que use la carpeta: Claude Code, terminales abiertas en ella, VS Code, `pnpm dev` y el Edge del MCP. Comprueba con `git status` en `C:\dev\bancada` que no queda nada sin subir.
2. `Move-Item C:\dev\bancada C:\dev\taller6mm`
3. Mueve también la memoria y las sesiones de Claude Code, para que `claude --continue` siga funcionando:
   `Move-Item "$env:USERPROFILE\.claude\projects\C--dev-bancada" "$env:USERPROFILE\.claude\projects\C--dev-taller6mm"`
4. `cd C:\dev\taller6mm; pnpm install --frozen-lockfile`. En Windows, pnpm enlaza `node_modules` con rutas absolutas y hay que rehacerlas; además reinstala los hooks de lefthook.
5. `git worktree prune; git status`. Tiene que salir limpio.
6. Abre `claude` en `C:\dev\taller6mm` y pídeme que actualice las menciones de la ruta: CLAUDE.md (línea 3), LEEME.md, `docs/runbooks/cloudflare-s3.md` y tu CLAUDE.local.md. El plan de la Fase 0 es histórico y se queda como está.
7. Opcional: borra `C:\dev\bancada-spike` (un worktree antiguo del spike, ya desregistrado) y `%TEMP%\claude\C--dev-bancada` (archivos temporales de las sesiones).
