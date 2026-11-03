# ADR-0008 — Entornos, previews y despliegue

- **Estado**: Propuesta
- **Fecha**: 2026-11-01 (revisada el 2026-11-03 con la revisión de seguridad de S3)
- **Decisores**: Javi (+ Claude Code)

## Contexto
- El plan de la Fase 0 (decisiones 8 y 9; S3) pide una preview por PR, que `main` despliegue el entorno
  `preview` y que producción solo se despliegue a mano con la aprobación de Javi (docs/07 §7, docs/08 §3).
- **Worker Previews** de Cloudflare (beta abierta; Wrangler ≥ 4.135, usamos 4.154.0): `wrangler preview --name <n>`
  crea o actualiza una Preview del Worker y `wrangler preview delete` la borra. Las Previews **no heredan** la
  configuración del Worker: toman sus bindings del bloque `previews`. En `workers.dev` llevan
  `X-Robots-Tag: noindex` y son públicas salvo con Cloudflare Access. Plan gratuito: 100 Previews por Worker y
  100 despliegues por Preview. Las colas y los crons no apuntan a Previews.
  (developers.cloudflare.com/workers/previews/, …/examples/ y …/configuration/, consultados el 01-11-2026).
- **Autorización granular**: un token puede ser **Editor** de un Worker concreto sin poder crear ni borrar
  recursos; crear un Worker exige **Admin**. Desplegar un Worker con bindings de D1 **no** pide permisos de D1;
  aplicar migraciones, sí. La documentación no garantiza permisos por base de D1
  (developers.cloudflare.com/workers/authorization/, 01-11-2026).
- El adaptador de Cloudflare de Astro elige el entorno **al compilar** (`CLOUDFLARE_ENV`) y genera
  `dist/server/wrangler.json` ya resuelto, que usan `wrangler deploy` y `wrangler preview`.
- En `pull_request`, GitHub ejecuta el workflow **del PR**: cualquiera que pueda empujar una rama (Javi, Renovate
  o un agente tras una inyección de instrucciones) puede cambiarlo, y cualquier paso de un job puede leer los
  secretos de ese job. La condición «no es un fork» y un interruptor por variable no son fronteras de seguridad
  (revisor-seguridad, 03-11-2026).

## Decisión
1. **Tres entornos** por Worker: `local` (nivel superior de `wrangler.jsonc`, cerrado: `workers_dev` y
   `preview_urls` en `false`), `preview` (`taller6mm-web-preview`, `taller6mm-jobs-preview` y bases `*-preview`
   con datos de demo) y `production` (`taller6mm-web`, `taller6mm-jobs`), configurado y **cerrado** hasta el
   lanzamiento: sin `workers.dev`, sin URLs de versión y sin rutas.
2. **Aislamiento por cuenta**: la cuenta de preview solo tiene Taller6mm (si la actual tiene otros proyectos, se
   usa una nueva) y **producción vivirá en otra cuenta de Cloudflare**. Dentro de una cuenta, un Editor de un
   Worker puede enlazar cualquier base o bucket de esa cuenta: el token no basta para aislar.
3. **Previews de PR en dos fases**:
   - `previews.yml` (`pull_request`) solo construye, **sin secretos ni entorno**, y sube la build como artefacto.
   - `previews-desplegar.yml` (`workflow_run`, definición siempre de `main`) no ejecuta código del PR: descarga el
     artefacto, valida su configuración contra la de `main` (`scripts/validar-preview.mjs`: mismo Worker, mismas
     variables y bases, ningún otro binding, ruta ni cron), lo sube como Preview `pr-<n>`, pasa el humo (tres
     bases en orden y `noindex` en `/` y `/sistema`) y comenta la URL desde un job aparte. Al cerrar el PR la
     borra, y un recolector diario borra las que se escapen.
4. **Migraciones solo desde `main`** (`desplegar-preview.yml`), en serie y sin cancelación. Las Previews de PR
   usan el esquema de `main`. Un test rechaza SQL destructivo en `packages/db/migrations` salvo excepción anotada.
5. **Tokens por uso, en entornos de GitHub restringidos a `main`**: `preview` (Editor de los dos Workers de
   preview y D1 de sus bases, para `main`) y `preview-pr` (Editor solo de `taller6mm-web-preview`, **sin D1**, para
   las Previews). El token solo está en el `env` de los pasos de wrangler. La primera creación de cada Worker la
   hace la sesión de Javi, que cierra con `wrangler logout`. Receta: docs/runbooks/cloudflare-s3.md.
6. **Producción nunca sale de estos workflows**: tendrá uno manual (`workflow_dispatch`) en el entorno
   `production` de GitHub, con Javi como revisor obligatorio, solo desde `main` y con migraciones a mano.
7. **Bindings mínimos**: solo D1 hasta que llegue el código que use R2 o la cola (Fases 3–5).
8. Wrangler sale del lockfile de `main` (`pnpm exec wrangler`); nada de acciones de terceros. Tests de política
   en `scripts/supply-chain.test.mjs`: sin secretos ni entorno en workflows de PR, `--remote` solo desde `main` y
   `concurrency` en todo job con entorno.
9. En `jobs`, el consumidor de la cola y el cron se declaran con sus manejadores (Fase 4): un solo cron cada 15 min
   por entorno y el manejador decide qué trabajos tocan (docs/07 §6).

## Alternativas consideradas
| Opción | Pros | Contras | Por qué no |
|---|---|---|---|
| Desplegar la Preview en el mismo job de `pull_request` (primera versión de S3) | Sencillo | El código del PR y sus dependencias corren con el token | Revisión de seguridad: ALTA |
| Un Worker por PR (`taller6mm-web-pr-12`) | Aislamiento de Worker | El token tendría que crear y borrar Workers (Admin) | Rompe el mínimo privilegio |
| Alias de versión (`wrangler versions upload --preview-alias`) | Maduro | Cloudflare recomienda Previews para PR; mezcla código de PR con las versiones del Worker | Obsoleto para este uso |
| Revisor obligatorio en el entorno de las Previews | Control humano | Cada push de un PR esperaría a Javi | Lo cubre el `workflow_run` sin fricción; queda como plan B |
| Producción en la misma cuenta | Un login | Un token o una Preview de preview podría enlazar datos de producción | Aislamiento |
| `cloudflare/wrangler-action` | Cómodo | Acción de terceros: la política del repo no la admite | Cadena de suministro |
| Una base D1 por PR | Datos aislados | Crear y borrar bases exige Admin | Complejidad; con migraciones solo desde `main` basta |

## Consecuencias
- **Positivas**: 0 €/mes; preview de cada PR en unos minutos; ningún job que ejecute código de un PR tiene
  secretos; el token de PR no toca D1 ni el Worker de producción; producción inalcanzable hasta el lanzamiento.
- **Negativas y riesgos residuales**:
  - Las Previews son **públicas** (`noindex` no es privacidad), sirven código sin revisar (también de bots) y
    comparten `<cuenta>.workers.dev` y las cuotas gratuitas de la cuenta: un abuso puede agotar las 100.000
    peticiones diarias o atraer denuncias. Antes de la Fase 2: Cloudflare Access en las Previews, cookies
    `__Host-` y nada de OAuth real ni login de staff en preview.
  - `preview_urls: true` en el Worker de preview publica también las URLs de versión de cada despliegue de `main`.
  - Si el panel no permite D1 por base, el token de `main` tendrá D1 de todo el producto: lo acota la cuenta
    dedicada (decisión 2).
  - Comprobado el 03-11 con una build local `CLOUDFLARE_ENV=preview`: `dist/server/wrangler.json` conserva el bloque
    `previews` y el validador la acepta. Falta ver en la primera ejecución real que `wrangler preview` lo aplica; si
    no, el humo lo detecta (las tres bases deben responder).
  - Worker Previews está en beta abierta.
- **Trabajo que genera**: la receta de Javi (unos 20 min), los ids `PENDIENTE_*`, el workflow de producción, los e2e
  y Lighthouse contra la preview y Access para las Previews.

## Validación
- Pruebas negativas con el token de PR antes de encender: `d1 execute` contra la base canario y contra una base de
  preview falla con 403.
- Primer PR tras activar: la build no recibe secretos, la Preview se despliega desde `workflow_run`, el humo pasa y
  la Preview se borra al cerrar.
- Un PR que cambie `previews-desplegar.yml` o `wrangler.jsonc` no altera lo que se despliega (lo ejecuta `main`).
- Tiempo hasta la Preview < 6 min y coste 0 € en el informe de cada fase.

## Disparadores de revisión
- Antes de crear recursos de producción (cuenta propia, token, workflow manual).
- Antes de que haya inicio de sesión o datos reales en preview (Fase 2): Access y cookies.
- Worker Previews sale de beta o cambia su CLI o sus límites.
- D1 permite permisos por base.
- Hace falta aislar datos por PR.
