# Plan · Fase 0 «Cimientos» de Taller6mm

> **Estado**: aprobado por Javi el 31-10-2026. Paso 0 hecho ese mismo día: Node 26.13.0, pnpm 12.16.1, gitleaks 8.30.1, `gh` con permiso `workflow` y sesión sin privilegios (integridad S-1-16-8192). El avance se registra en `docs/informes/fase-0.md` al cerrar la fase.

## Contexto
Al redactar el plan, `C:\dev\bancada` solo contenía la especificación (`docs/`), la configuración de Claude Code (`.claude/`, `.mcp.json`) y los textos de arranque. No había git ni código, y la sesión corría como administrador (integridad S-1-16-12288), así que se planificó sin instalar ni ejecutar nada.

La Fase 0 deja los cimientos:
- stack validado con cifras;
- monorepo;
- calidad y seguridad automáticas;
- recursos de preview en Cloudflare;
- semilla del sistema de diseño;
- Claude Code verificado.

Fuera de alcance: La Armería y el configurador.

**Tus respuestas**: cuenta de Cloudflare actual · R2 activado (con método de pago) · repo público · Node 26 LTS · nombre **Taller6mm**.

---

## 1. Decisiones (qué · por qué · qué descarto)
| # | Decisión | Por qué | Descartado |
|---|---|---|---|
| 1 | **Nombre técnico `taller6mm`**: repo `Javier-roman/taller6mm`, paquetes `@taller6mm/*`, Workers `taller6mm-web` / `taller6mm-jobs` (+ `-preview`), bases `taller6mm-core/-mercado/-busqueda`. Marca «Taller6mm» en `brand.ts`. Código de build `T6M-XXXX-XXXX` (antes `BNC-`), bot `Taller6mmBot`. | Renombrar antes de crear recursos es gratis; después obliga a migrarlos. | Dejar BANCADA en la infraestructura. |
| 2 | **Astro 7.4 + @astrojs/cloudflare 14** (no Astro 6) | Estable desde el 22-6-2026: Vite 8, builds más rápidas y CSP con ámbitos (7.1). CLAUDE.md pide la última estable. El spike la valida igual. | Fijar Astro 6. |
| 3 | **Node 26.13.0 LTS** en `.node-version`, `engines` y CI | Tu elección; soporte hasta el 30-4-2029. | — |
| 4 | **pnpm 12.16.1** fijado con `packageManager`. En `pnpm-workspace.yaml`: `minimumReleaseAge` de 3 días en modo estricto, `trustPolicy: no-downgrade`, `allowBuilds` (lista blanca de scripts), `strictDepBuilds` y `blockExoticSubdeps` | Frena paquetes comprometidos recién publicados (ataques tipo Shai-Hulud). No entra nada con menos de 3 días, ni versiones que pierdan su procedencia firmada, ni scripts de instalación sin permiso. | Instalar siempre lo último. |
| 5 | **TypeScript 6.x**, no 7.0 | TS 7 (compilador en Go) aún no tiene API programática y `@astrojs/check` exige TS ≤ 6. Se revisa con TS 7.1. | TS 7 ya. |
| 6 | **Vitest 4.1**, no 5 | El pool de Workers (`@cloudflare/vitest-pool-workers` 0.23) solo admite Vitest ^4.1. | Dos versiones de Vitest en el monorepo. |
| 7 | **Biome 2.6** con su soporte experimental de `.astro` (lo decide el spike) | Una sola herramienta rápida. Plan B: Prettier con plugin de Astro, solo para `.astro`. | ESLint + Prettier en todo. |
| 8 | **Previews de Workers** por PR (`wrangler preview --name pr-<n>`) bajo el Worker persistente `taller6mm-web-preview`, borradas al cerrar el PR. `main` despliega el entorno `preview`. Producción, solo manual y con tu aprobación. | Es lo que Cloudflare recomienda en 2026 para PR (la versión con alias queda obsoleta) y aísla cada PR. | Un Worker por PR; URLs de versión con alias. |
| 9 | **Tokens de CI con permisos granulares** (modelo de autorización de Workers 2026): el de preview es Editor solo de los Workers y bases de preview; el de producción, solo de los de producción y solo accesible desde el entorno `production` de GitHub con tu aprobación. | Usas tu cuenta actual: así el CI no puede tocar nada más de ella. | Un token «Edit Workers» para toda la cuenta. |
| 10 | **Renovate** (app gratuita) + OSV-Scanner + `pnpm audit` en CI + alertas de Dependabot | El grafo de dependencias de GitHub aún no lee bien el lockfile de pnpm 12 (alertas incompletas). Renovate parte de `package.json`, respeta la edad mínima y cruza con OSV. Es lo que ya decía docs/08. | Solo Dependabot. |
| 11 | **gitleaks 8.30** en pre-commit (con lefthook, multiplataforma) y en CI | El secreto se para antes de entrar en el historial. El CI cubre a quien no tenga el hook. | secretlint. |
| 12 | **CSP**. Astro genera la política con hashes en `<meta>`. El middleware añade por cabecera lo que una meta no admite (`frame-ancestors 'none'`, `base-uri`, `object-src`, `form-action`) y además HSTS, nosniff, Referrer-Policy, Permissions-Policy, COOP y CORP. Los estáticos llevan las mismas cabeceras vía `public/_headers`, porque no pasan por el Worker. | Astro solo emite la CSP como meta. Consecuencia para la Fase 1: las transiciones serán las nativas del navegador, porque el `<ClientRouter />` de Astro no admite CSP. | `unsafe-inline`. |
| 13 | **`/sistema` prerenderizada; `/` en SSR** con consultas a D1. Astro con `session: false` (las sesiones las llevará Better Auth en D1, y así no hace falta un KV). Imágenes en modo `compile`. | `/sistema` no gasta CPU y saca Lighthouse alto. Sin recursos innecesarios. | Todo SSR. |
| 14 | **Tabla `meta` en cada base D1** con su propio nombre; la página de prueba la lee por cada binding. | Con tres bases, cruzar dos bindings es un fallo real y silencioso. | `SELECT 1`. |
| 15 | **Repo público blindado**: protección de main (PR, checks obligatorios, sin force-push), entornos `preview` y `production`, push protection de secretos, avisos privados de vulnerabilidades (contacto de `security.txt` sin exponer tu email), Actions con solo lectura por defecto, acciones fijadas por SHA y sin `pull_request_target`. | En un repo público estos controles son gratis. | — |
| 16 | **Lighthouse contra la preview omite solo la auditoría `is-crawlable`** | Las previews llevan `noindex` a propósito (Cloudflare lo añade en workers.dev) y bajaría SEO aunque la página esté bien. Un test comprueba que producción no lleva `noindex`. | Rebajar el umbral. |
| 17 | La carpeta local sigue siendo `C:\dev\bancada` durante la Fase 0 | Renombrarla corta `claude --continue` y la memoria del proyecto. Puedes renombrarla al cerrar la fase. | — |

## 2. Lo desactualizado o mejorable en tus documentos (lo aplico en S0 y S6)
- **Versiones**:
  - Astro 6 → 7 (ADR-0001, CLAUDE.md, docs/07).
  - Node 22 → 26 (CLAUDE.md, CLAUDE.local.md, check-env).
  - Fijar TS 6 y Vitest 4.1 con su motivo.
  - Quitar el consejo de corepack: Node 25+ ya no lo incluye.
- **Cloudflare 2026**:
  - Previews por rama (docs/07 §7 y docs/08 §3).
  - Permisos granulares de tokens (docs/08 §6.2).
  - Queues gratis desde el 4-2-2026, con retención de 24 h.
  - R2 pide método de pago aunque no cobre (docs/07 §8).
- **Astro**:
  - CSP solo por meta, sin modo dev y sin `<ClientRouter />` (docs/02 §3.2, docs/08 §6.2).
  - `session: false`.
  - Los estáticos necesitan `_headers`.
- **Tokens de color** (docs/02 §4.1): dos fallan AA como texto sobre `--negro-pavonado`. `--estado-desconocido` da 4,13:1 y `--estado-error` 4,35:1, frente a un mínimo de 4,5:1. Propondré valores y los validará `critico-diseno`.
- **Claude Code**:
  - **Skills**: `revisar-ui`, `informe-fase` y `adr` llevan `disable-model-invocation: true`. Con eso Claude Code me bloquea ejecutarlas, y el flujo pactado lo necesita. Se lo quito a esas tres; lo mantengo en `nueva-tienda` y `nueva-replica`, que tocan webs externas.
  - **`guard-shell.mjs` tiene dos agujeros**. Primero, `Copy-Item .dev.vars .dev.vars.example` se permite: copia tus secretos a un archivo que sí se sube. Segundo, los comodines (`cat .dev.va*`) esquivan el patrón. Los cierro y añado tests.
  - **Reglas del hook**: como el entorno de Cloudflare se elige al compilar, cualquier `wrangler deploy` pedirá confirmación. Bloqueo `wrangler preview secret put`. `wrangler preview delete` pedirá confirmación.
  - **`.mcp.json`**: `@playwright/mcp@latest` con `npx -y` ejecuta cualquier versión nueva sin revisión. La fijo y añado `--isolated`.
  - **`check-env`**: comparará con `.node-version` y avisará si faltan pnpm o gitleaks.
- **Nombre**: BANCADA → Taller6mm en CLAUDE.md, docs, `.claude/`, LEEME y PROMPT_INICIAL.

## 3. Paso 0 · Lo que necesito de ti antes de empezar (unos 10 min)
1. Cierra esta sesión (está como administrador).
2. En una terminal **normal**:
   ```powershell
   winget install --id OpenJS.NodeJS.LTS --exact    # Node 26.13.0 (el instalador pedirá UAC: es normal)
   # cierra y abre la terminal para refrescar el PATH
   node -v                                          # v26.13.0 o superior
   npm install --global pnpm@12.16.1
   pnpm -v                                          # 12.16.1
   winget install --id Gitleaks.Gitleaks --exact
   gitleaks version
   gh auth refresh -h github.com -s workflow
   cd C:\dev\bancada
   claude --continue
   ```
3. Si no lo tienes, activa la verificación en dos pasos (2FA) en Cloudflare y en GitHub.

## 4. Rebanadas (en este orden)
Cada rebanada termina con `/verify`, commits pequeños (Conventional Commits) y la revisión del subagente de su área. Desde S2, todo entra por PR con CI verde y lo fusionas tú; el hook pide confirmación en `gh pr merge`.

### S0 · Arranque seguro (sin código de producto)
1. **Comprobaciones tras reiniciar**:
   - `check-env` sin aviso;
   - `cat .dev.vars` (Bash) y `Get-Content .dev.vars` (PowerShell) denegados por el hook;
   - tú ejecutas `/skills` y `/agents` y me dices qué ves.
2. **Renombrado** a Taller6mm.
3. **Arreglos de Claude Code** (§2):
   - `guard-shell.mjs` con tests (`node --test`, tabla de unos 40 comandos permitir/preguntar/denegar, incluidos los intentos de saltárselo);
   - `check-env.mjs`, skills, `.mcp.json` y reglas `deny` de lectura para `.dev.vars.*` y `.env.*` de entorno.
4. **Ficheros base**: `.editorconfig`, `.gitattributes` (LF) y `.node-version`.
5. **git y GitHub**:
   1. `git init -b main`.
   2. `git check-ignore` de las capturas, `CLAUDE.local.md` y `settings.local.json`.
   3. Escaneo `gitleaks dir`.
   4. Commits pequeños.
   5. `gh repo create Javier-roman/taller6mm --public --source . --push`. Es el **único push directo a main**.
   6. Ajustes de seguridad del repo y ruleset de main.
6. Copio este plan a `docs/informes/fase-0-plan.md`.
7. Revisión: `revisor-seguridad` (hooks y ajustes del repo).

### S1 · Spike del stack (ADR-0001), máximo una sesión
1. **Dónde**: rama `spike/0001-stack` (no se fusiona) y carpeta `spikes/0001-stack/`. Recursos: Worker `taller6mm-spike` y D1 `taller6mm-spike`.
2. **Qué se monta**:
   - Astro 7 + Cloudflare + React 19;
   - `/`: SSR con Drizzle 0.45 sobre D1;
   - `/3d`: isla `client:only` con R3F (pieza de latón iluminada, bloom, viñeta y tone mapping AgX);
   - Better Auth 1.7 con enlace mágico sobre D1 + Drizzle (emisor de prueba);
   - prueba de `wrangler preview` con la build de Astro.
3. **Qué se mide**:
   - tamaño del Worker comprimido (límite 3 MiB, objetivo ≤ 1,5 MiB) y tiempo de arranque;
   - CPU p50/p95/p99 de `/` y de `/api/auth/get-session` sobre unas 200 peticiones (con `wrangler tail` o Workers Logs), frente al límite de 10 ms;
   - chunk 3D comprimido (≤ 350 KB);
   - Biome sobre `.astro` (falsos positivos);
   - Better Auth: alta, sesión y transacciones en D1;
   - Previews con la build de Astro.
4. **Resultado**: ADR-0001 pasa a **Aceptada**, con la tabla de cifras y Astro 7, Node 26, TS 6 y Vitest 4.1. Si algo bloquea, **paro** y te propongo la alternativa con los datos.
5. **Tú**: `pnpm exec wrangler login` (OAuth en el navegador). Al final, dos comandos de borrado del spike; el hook me impide borrar recursos.
6. Revisión: `auditor-rendimiento` (método y cifras).

### S2 · Monorepo y calidad (PR 1)
1. **Base**:
   - estructura exacta de CLAUDE.md;
   - pnpm workspaces con catálogos, Turborepo 2.11, TS 6 estricto en `packages/config`, Biome;
   - scripts `dev`, `build`, `verify`, `e2e`, `lh`, `size`, `db:migrate:local`, `db:seed:local` y `db:reset:local`, todos multiplataforma (`.mjs`, sin sintaxis de bash).
2. **Cada paquete compila y tiene su test**:
   - `domain`: `Millimeters` (precisión 0,1), `Cents` (enteros), `CurrencyCode` (ISO 4217) y `Money`, con Zod 4 y fast-check;
   - `compat`: tipos de veredicto, fuente y confianza (docs/03 §5.1);
   - `market`: disponibilidad schema.org → enum común (docs/04 §5);
   - `db`: Drizzle y migración `0000_meta` por base, con un test que la aplica desde cero en workerd;
   - `ui`: tokens;
   - `jobs`: Hono `/health` con el pool de Workers;
   - `crawler`: User-Agent identificado;
   - `pipeline`: Python 3.12 + uv + pytest, solo en CI hasta que instales uv.
3. **Local**: lefthook con pre-commit de gitleaks y Biome.
4. **CI v1** (GitHub Actions):
   1. instalación congelada;
   2. lint, typecheck, test, build y size;
   3. gitleaks, OSV-Scanner, Semgrep CE y `pnpm audit`.

   Más un job de `verify` en `windows-latest`, porque desarrollas en Windows. Permisos mínimos por job.
5. **Renovate**: edad mínima de 3 días, grupos, digests de acciones; retiene Vitest 5 y TS 7.
6. **Tú**: instalar la app de Renovate solo en este repo y fusionar el PR. Después hago obligatorios los checks en la protección de main.
7. Revisión: `revisor-seguridad` (cadena de suministro y workflows).

### S3 · Cloudflare y página de prueba (PR 2)
1. **Configuración**: `wrangler.jsonc` en `web` y `jobs`, con entornos `preview` y `production`, bloque `previews`, `observability` y `wrangler types`.
2. **Recursos de preview** (los creo yo con wrangler):
   - D1 `taller6mm-{core,mercado,busqueda}-preview`;
   - R2 privados `taller6mm-assets-preview` y `taller6mm-uploads-preview`;
   - cola `taller6mm-ingest-preview` con su cola de mensajes fallidos.

   Producción queda solo configurada: sus recursos se crean con tu permiso en la fase de lanzamiento.
3. **Página `/`** (SSR): nombre, entorno, commit y estado de cada binding (nombre en `meta` y migraciones de cada D1, R2 y cola), con la hora de comprobación.
4. **CI**:
   - job `preview`, solo para PR del propio repo: migraciones aditivas a las bases de preview → `wrangler preview --name pr-<n>` → URL comentada en el PR;
   - borrado de la preview al cerrar el PR;
   - `main` despliega el entorno `preview` (web y jobs).
5. **Tú**:
   1. Activas R2 en el panel.
   2. Creas dos tokens granulares (te doy la receta exacta).
   3. Los guardas con `gh secret set CLOUDFLARE_API_TOKEN --env preview` y `--env production`. Yo no los veo.
6. **Verificación**: capturas con el MCP de Playwright (Edge) de `/` en local y en la preview, a 390 y 1440 px.
7. Revisión: `revisor-seguridad` (bindings y tokens con mínimo privilegio).

### S4 · Seguridad base (PR 3)
1. **Cabeceras**:
   - `apps/web/src/middleware.ts` y `public/_headers` con las cabeceras de docs/08 §6.2;
   - `security.csp` y `checkOrigin` de Astro;
   - `X-Robots-Tag: noindex` fuera de producción;
   - tests unitarios y e2e de las cabeceras.
2. **Divulgación**:
   - `SECURITY.md`;
   - `public/.well-known/security.txt` (RFC 9116), con un test que falla si `Expires` caduca en menos de 30 días;
   - `.dev.vars.example` por app.
3. **`docs/seguridad/modelo-amenazas.md`**:
   - activos y fronteras de confianza;
   - **STRIDE por componente**: web, jobs, crawler, pipeline, D1/R2/colas, CI/CD y cadena de suministro, y tu puesto con Claude Code y MCP, incluida la inyección de instrucciones desde páginas web;
   - mitigaciones con fase y referencia ASVS, y riesgos residuales.
4. **OWASP ZAP baseline**: workflow semanal contra el entorno preview.
5. Revisión: `revisor-seguridad`; corrijo críticos y altos.

### S5 · Semilla del sistema de diseño (PR 4)
1. **`packages/ui`**:
   - tokens de docs/02 §4 como variables CSS, export TS y `@theme` de Tailwind v4;
   - `brand.ts`;
   - fuentes autoalojadas con Fontsource: Cinzel, Big Shoulders Stencil, Archivo variable (eje de anchura) y JetBrains Mono, en latino extendido, precargando solo Archivo y Cinzel.
2. **Contraste**: test automático AA de cada par texto/fondo declarado, con los dos valores corregidos.
3. **Componentes React**, sin JS en cliente salvo que haga falta:
   - Botón (latón, acero, fantasma, peligro), Placa, Rótulo plantilla, Insignia de fidelidad T0–T3 y Barra de dato;
   - estados hover, foco, activo, deshabilitado, carga y error;
   - `prefers-reduced-motion` respetado.
4. **`/sistema`** prerenderizada con todos los tokens y componentes.
5. **CI**:
   - e2e con Playwright + axe (teclado, movimiento reducido);
   - Lighthouse CI móvil contra la preview, con 3 ejecuciones y ≥ 0,95 en las cuatro categorías en `/sistema`;
   - size-limit con presupuestos.
6. Revisión: `/revisar-ui /sistema` (capturas a 390, 834 y 1440 px y con movimiento reducido; `critico-diseno`) y `auditor-rendimiento`. Te enseño el antes y el después.

### S6 · Documentación, verificación final y cierre (PR 5, el «PR de ejemplo»)
1. `README.md` (puesta en marcha en 5 pasos), `CONTRIBUTING.md` (ramas, commits y definición de terminado) y `CHANGELOG.md`.
2. CLAUDE.md y docs al día (§2). Nuevo ADR-0008 «Entornos, previews y despliegue».
3. Clon limpio en una carpeta temporal: `pnpm install && pnpm verify`.
4. Tabla de verificación de Claude Code con evidencias: hooks, check-env, formateador, skills, subagentes y MCP.
5. PR 5 con el CI completo en verde y la URL de preview (`/` y `/sistema`).
6. Ejecuto `/informe-fase 0`, te enseño el resumen y **me detengo**.

## 5. Riesgos y plan B
| Riesgo | Se ve en | Plan B |
|---|---|---|
| Worker > 3 MiB o arranque lento (React SSR + Better Auth) | S1 | Sacar la autenticación a otro Worker y recortar dependencias. Último recurso, Workers Paid (5 $/mes), con tu OK. |
| CPU SSR > 10 ms | S1 | Prerender y caché en el borde; trabajo pesado a `jobs` o al cliente. |
| `wrangler preview` no encaja con la build de Astro | S1 | Versiones con alias (`--preview-alias`) o un Worker por PR. |
| Biome con `.astro` | S1 | Prettier con plugin de Astro solo para `.astro`. |
| Better Auth y las transacciones de D1 | S1 | Desactivar las transacciones del adaptador o usar Kysely con D1. |
| Herramienta incompatible con Node 26 | S2 | Node 24 LTS. |
| Lighthouse < 95 en móvil | S5 | Menos fuentes precargadas, subconjuntos, CSS crítico. |
| Ruido de Lighthouse en CI | S5 | Mediana de 3 ejecuciones. |
| Sorpresas de Windows (rutas, CRLF, shims) | S2 | `.gitattributes` con LF, scripts `.mjs` y job de CI en `windows-latest`. |
| Coste de R2 | Siempre | Buckets privados, sin acceso público; el uso se revisa en cada informe. |
| Algo sensible en el repo público | Siempre | gitleaks, push protection y revisión antes de cada push. |

**Coste previsto de la Fase 0: 0 €.**

## 6. Verificación: criterios de aceptación → evidencia
| Criterio | Evidencia en el informe |
|---|---|
| `pnpm install && pnpm verify` verde en un clon limpio | Salida del comando en una carpeta temporal |
| PR con CI completo verde y preview funcionando (`/` y `/sistema`) | Enlaces al PR, a los checks y a la URL, más capturas con el MCP de Playwright |
| Lighthouse móvil de `/sistema` ≥ 95 en las 4 categorías | Informe de LHCI (artefacto del CI) |
| ADR-0001 aceptado con cifras | `docs/adr/0001-stack.md` |
| Hooks, skills, subagentes y MCP verificados | Tabla con pruebas: denegaciones del hook, aviso de entorno, formateador, `/skills`, `/agents` y captura |
| gitleaks limpio y modelo de amenazas | Job de CI y `docs/seguridad/modelo-amenazas.md` |

## 7. Lo que harás tú, en orden
1. **Paso 0**: instalaciones y reinicio (§3).
2. **S0**: ejecutar `/skills` y `/agents` y contarme qué aparece.
3. **S1**: `wrangler login`. Al final, dos comandos de borrado.
4. **S2**: instalar la app de Renovate y fusionar el PR.
5. **S3**: activar R2, crear dos tokens y ejecutar dos `gh secret set`.
6. **S5**: mirar las capturas de `/sistema` y darme tu opinión.
7. **S6**: leer el informe y darme el OK para la Fase 1.

## Fuentes verificadas (31-10-2026)
- **Versiones**: consultadas en el registro de npm (astro 7.4.4, @astrojs/cloudflare 14.4.3, wrangler 4.156.0, pnpm 12.16.1, vitest 5.0.5, @cloudflare/vitest-pool-workers 0.23.0, typescript 7.0.2, @astrojs/check 0.9.12, biome 2.6.4, drizzle-orm 0.45.4, better-auth 1.7.14, turbo 2.11.10), [pnpm releases](https://github.com/pnpm/pnpm/releases) y [calendario de Node](https://github.com/nodejs/Release).
- **Astro**: [Astro 7](https://astro.build/blog/astro-7/), [adaptador de Cloudflare](https://docs.astro.build/en/guides/integrations-guide/cloudflare/) y [CSP en la referencia de configuración](https://docs.astro.build/en/reference/configuration-reference/).
- **Cloudflare**:
  - [Previews](https://developers.cloudflare.com/workers/previews/), [comparativa de flujos](https://developers.cloudflare.com/workers/previews/compare-workflows/) y [ejemplos de CI](https://developers.cloudflare.com/workers/previews/examples/);
  - [autorización granular](https://developers.cloudflare.com/workers/authorization/);
  - [límites de Workers](https://developers.cloudflare.com/workers/platform/limits/);
  - [Queues en el plan gratuito](https://developers.cloudflare.com/changelog/post/2026-02-04-queues-free-plan/);
  - método de pago de R2: [guía de terceros](https://tech-insider.org/how-to-set-up-cloudflare-r2-2026/). La documentación oficial no lo aclara; se confirma al activarlo.
- **GitHub**: [entornos y revisores obligatorios](https://docs.github.com/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment) y [Dependabot con pnpm 12](https://github.blog/changelog/2025-01-09-dependabot-now-supports-npm-12-pnpm-11-and-12-and-bun-1-4/).
- **Herramientas**:
  - [Biome y Astro](https://biomejs.dev/internals/language-support/);
  - [TypeScript 7](https://infoq.com/news/2026/08/typescript-7-released/);
  - [Playwright MCP](https://github.com/microsoft/playwright-mcp);
  - [gitleaks](https://github.com/gitleaks/gitleaks).
- **Claude Code**: [quién invoca una skill](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill), [hooks en forma exec con `args`](https://code.claude.com/docs/en/hooks) y [reglas por ruta](https://code.claude.com/docs/en/memory#path-specific-rules).
