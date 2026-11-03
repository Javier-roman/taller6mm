# ADR-0008 — Entornos, previews y despliegue

- **Estado**: Aceptada (2026-11-03, al fusionar el PR #8)
- **Fecha**: 2026-11-01 (revisada el 2026-11-03 con las dos revisiones de seguridad de S3)
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
  (developers.cloudflare.com/workers/authorization/, 01-11-2026). **En la práctica**, al crear los tokens el
  03-11-2026 el formulario de tokens personalizados solo ofreció permisos de **toda la cuenta**
  («Workers Scripts: Edit» y «D1: Edit»), sin elegir Workers ni bases.
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
2. **Aislamiento por cuenta, como requisito duro**: la cuenta de preview solo tiene Taller6mm (comprobado el 03-11:
   la cuenta de Javi estaba vacía), **producción vivirá siempre en otra cuenta de Cloudflare** y en esta **nunca
   habrá datos reales**, solo de demo. Dentro de una cuenta, un Editor de Workers puede enlazar cualquier base o
   bucket, y los tokens alcanzan toda la cuenta (decisión 5): lo que aísla es la cuenta, no el token.
3. **Previews de PR en dos fases**:
   - `previews.yml` (`pull_request`) solo construye, **sin secretos ni entorno**, y sube la build como artefacto.
   - `previews-desplegar.yml` (`workflow_run`, definición siempre de `main`) no ejecuta código del PR y trata el
     artefacto como un dato. `scripts/preparar-preview.mjs` copia de él solo los módulos (`.mjs`, `.js`), sus mapas
     y los estáticos a una carpeta limpia, sin archivos ocultos ni enlaces y con cada `sourceMappingURL` dentro de su
     carpeta, y escribe la configuración **de `main`** (`configuracionPreview`). La configuración del artefacto
     **no se usa nunca**: claves como `base_dir`, `rules`, `alias` o `build` decidirían qué archivos del runner se
     suben o qué se ejecuta junto al token (revisor-seguridad, 03-11-2026, A1). Solo se compara con la de `main`
     (`scripts/validar-preview.mjs`) para avisar de que la Preview no sería fiel. Después lo sube como Preview
     `pr-<n>`, pasa el humo (tres bases en orden y `noindex` en `/` y `/sistema`) y comenta la URL desde un job
     aparte. Al cerrar el PR la borra, y un recolector diario borra las que se escapen.
4. **Migraciones solo desde `main`** (`desplegar-preview.yml`), en serie y sin cancelación. Las Previews de PR
   usan el esquema de `main`. Un test rechaza SQL destructivo en `packages/db/migrations` salvo excepción anotada.
5. **Tokens por uso, en entornos de GitHub restringidos a `main`**: `preview` («Workers Scripts: Edit» y
   «D1: Edit», para `main`) y `preview-pr` («Workers Scripts: Edit», **sin D1**, para las Previews). **Los dos
   alcanzan toda la cuenta**, porque el panel no dejó acotarlos. Con el de PR se podría crear, cambiar o borrar
   cualquier Worker de la cuenta y enlazar cualquiera de sus bases; «sin D1» solo cierra la API de D1
   (migraciones, exportar o borrar bases). Javi lo **acepta como riesgo** (03-11-2026) mientras la cuenta solo
   tenga la preview de Taller6mm (decisión 2). El token solo está en el `env` de los pasos de wrangler, en jobs que
   no ejecutan código del PR. Se rehacen acotados por Worker en cuanto Cloudflare lo permita (issue #11). La
   primera creación de cada Worker la hace la sesión de Javi, que cierra con `wrangler logout`. Receta:
   docs/runbooks/cloudflare-s3.md.
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
| Desplegar con la configuración del artefacto tras validarla con una lista de claves (segunda versión) | Sin copias | Varias claves admitidas (`base_dir`, `rules`, `alias`…) deciden qué archivos del runner se suben con el token | Segunda revisión de seguridad: ALTA (A1) |
| Un Worker por PR (`taller6mm-web-pr-12`) | Aislamiento de Worker | El token tendría que crear y borrar Workers (Admin) | Rompe el mínimo privilegio |
| Alias de versión (`wrangler versions upload --preview-alias`) | Maduro | Cloudflare recomienda Previews para PR; mezcla código de PR con las versiones del Worker | Obsoleto para este uso |
| Revisor obligatorio en el entorno de las Previews | Control humano | Cada push de un PR esperaría a Javi | Lo cubre el `workflow_run` sin fricción; queda como plan B |
| Producción en la misma cuenta | Un login | Un token o una Preview de preview podría enlazar datos de producción | Aislamiento |
| `cloudflare/wrangler-action` | Cómodo | Acción de terceros: la política del repo no la admite | Cadena de suministro |
| Una base D1 por PR | Datos aislados | Crear y borrar bases exige Admin | Complejidad; con migraciones solo desde `main` basta |

## Consecuencias
- **Positivas**: 0 €/mes; preview de cada PR en unos minutos; ningún job que ejecute código de un PR tiene
  secretos; un PR no decide qué se sube ni con qué bindings; el token de PR no tiene la API de D1; producción vive
  en otra cuenta y es inalcanzable hasta el lanzamiento.
- **Negativas y riesgos residuales**:
  - Las Previews son **públicas** (`noindex` no es privacidad), sirven código sin revisar (también de bots) y
    comparten `<cuenta>.workers.dev` y las cuotas gratuitas de la cuenta: un abuso puede agotar las 100.000
    peticiones diarias o atraer denuncias. Antes de la Fase 2: Cloudflare Access en las Previews, cookies
    `__Host-` y nada de OAuth real ni login de staff en preview.
  - `preview_urls: true` en el Worker de preview publica también las URLs de versión de cada despliegue de `main`
    (issue #11, B3).
  - **Tokens de toda la cuenta** (decisión 5, riesgo aceptado): un token de `preview-pr` filtrado permitiría alojar
    cualquier Worker en el `workers.dev` de la cuenta, abrir `taller6mm-jobs-preview` o enlazar cualquier base. Lo
    acotan la cuenta dedicada sin datos reales, que el token solo exista en jobs sin código del PR, su caducidad de
    6 meses y los Audit Logs. Siguen en la issue #11: separar la build del despliegue en `main` (M3) y atar el
    número de PR al artefacto (B1).
  - El **subdominio de `workers.dev`** de la cuenta identifica a Javi y aparece en las URLs públicas de las Previews,
    en los comentarios del bot y en los informes de ZAP. Javi lo acepta (03-11-2026). Si un día se cambia, cambian
    todas las URLs y hay que actualizar `ZAP_TARGET_URL`.
  - Comprobado el 03-11: la build con `CLOUDFLARE_ENV=preview` conserva el bloque `previews` y `wrangler preview` lo
    aplica. Con el Worker del spike, una Preview sin ese bloque nacía sin bindings y daba 500; con él, respondía 200
    leyendo D1. La configuración que escribe `preparar-preview` sube lo mismo que la de Astro: `wrangler deploy
    --dry-run` da una salida idéntica (los mismos 11 módulos y estáticos, 1203,51 KiB y las tres bases), y la Preview
    `pr-8` desplegada con ella pasó el humo. El humo lo sigue vigilando en cada PR.
  - Worker Previews está en beta abierta.
- **Trabajo que genera**: la receta de Javi (unos 20 min), los ids `PENDIENTE_*`, el workflow de producción, los e2e
  y Lighthouse contra la preview y Access para las Previews.

## Validación
- Pruebas negativas con el token de PR antes de encender: `d1 execute` contra la base canario y contra una base de
  preview falla con 403. Prueban que ese token no tiene la API de D1, no que esté acotado a unas bases: con tokens
  de toda la cuenta, el de `main` sí alcanza la canario.
- `scripts/preparar-preview.test.mjs` y `scripts/validar-preview.test.mjs`: la configuración desplegada sale de
  `main` y se rechazan `.env`, `.dev.vars`, archivos ocultos, otros tipos de archivo, enlaces simbólicos, mapas fuera
  de su carpeta, `base_dir`, `build`, `alias`, `define`, `rules`, `no_bundle: false`, `secrets` y `account_id`.
- Primer PR tras activar: la build no recibe secretos, la Preview se despliega desde `workflow_run`, el humo pasa y
  la Preview se borra al cerrar.
- Un PR que cambie `previews-desplegar.yml` o `wrangler.jsonc` no altera lo que se despliega (lo ejecuta `main`).
- Tiempo hasta la Preview < 6 min y coste 0 € en el informe de cada fase.

## Disparadores de revisión
- Antes de crear recursos de producción (cuenta propia, token, workflow manual).
- Antes de que haya inicio de sesión o datos reales en preview (Fase 2): Access y cookies.
- Worker Previews sale de beta o cambia su CLI o sus límites.
- Cloudflare permite acotar los tokens por Worker o por base: se rehacen los dos (issue #11).
- Una versión nueva de `@astrojs/cloudflare` cambia el `wrangler.json` que genera: `validar-preview` falla en
  `previews.yml` y se revisan a la vez `configuracionPreview`, la muestra de los tests y la lista de claves.
- Hace falta aislar datos por PR.
