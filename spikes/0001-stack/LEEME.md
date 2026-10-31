# Spike S1 · Validación del stack (ADR-0001)

> **Desechable: no se fusiona.** Vive en la rama `spike/0001-stack` para dejar constancia del método y de las cifras. Medido en la nube (contenedor Linux de Claude Code) el 31-10-2026, sin cuenta de Cloudflare: todo en local con workerd, D1 local y `wrangler deploy --dry-run`.

## Qué monta
| Pieza | Cómo |
|---|---|
| Web | Astro 7.4.3 con salida `server`, `@astrojs/cloudflare` 14.4.3 y React 19.3.1 (`@astrojs/react` 7.1.2). `session: false` (sin KV) e imágenes en modo `compile` (sin binding de Images). |
| `/` (SSR) | Lee la tabla `meta` de D1 con Drizzle 0.45.4 y la sesión de Better Auth. |
| `/3d` (estática) | Isla `client:only="react"` con R3F 9.8.2: bocacha de latón (perfil de torno en mm), entorno procedural `RoomEnvironment` (sin descargas externas), bloom, viñeta y tone mapping AgX con `@react-three/postprocessing` 3.2.2. |
| Autenticación | Better Auth 1.7.14 (`better-auth/minimal`) con enlace mágico sobre D1 + Drizzle. **Emisor de prueba**: el enlace se guarda en la tabla `test_outbox` en vez de enviarse. |
| Calidad | Biome 2.6.3, TypeScript 6.0.3 y `astro check`. |
| Dependencias | pnpm 12.16.1 con la política del plan: `minimumReleaseAge` de 3 días (estricto), `trustPolicy: no-downgrade`, `strictDepBuilds`, `blockExoticSubdeps` y `allowBuilds` (solo esbuild y workerd). |

## Resultados (31-10-2026, Node 26.13.0, Linux x64)
| Medida | Resultado | Límite u objetivo | Veredicto |
|---|---|---|---|
| Worker comprimido (`wrangler deploy --dry-run --outdir`) | **505 KiB gzip** (2.196 KiB sin comprimir, sin minificar) | Límite 3 MiB; objetivo ≤ 1,5 MiB | ✅ 16 % del límite |
| Arranque del Worker (`wrangler check startup`, CPU local) | 44,7 ms de CPU activa (ventana de 92,6 ms) | Orientativo (límite de arranque de Cloudflare: 1 s) | ✅ |
| Chunk 3D de la escena (gzip -9) | **268,9 KB** (brotli 221,0 KB) | ≤ 350 KB gz | ✅ 77 % |
| Isla 3D completa con el runtime de React | 338,0 KB gzip (brotli 280,8 KB) | ≤ 350 KB gz | ✅ (justo) |
| Biome en `.astro`, modo por defecto | 4 avisos, **4 falsos positivos** (`noUnusedVariables`/`noUnusedImports` de lo que usa la plantilla) | 0 | ❌ |
| Biome en `.astro`, `html.experimentalFullSupportEnabled` | **0 avisos** en lint y formato | 0 | ✅ (experimental) |
| Better Auth, enlace mágico con `transaction: false` | **10/10 pasos**: alta, enlace en D1, verificación, cookie, sesión (con y sin caché de cookie), SSR con sesión, enlace de un solo uso | Todo verde | ✅ |
| Better Auth con `transaction: true` | La verificación del enlace devuelve **500**: D1 rechaza `BEGIN` | — | ❌ (esperado) |
| D1 local: `BEGIN` crudo / `db.transaction()` de Drizzle | Rechazados (`D1_ERROR: To execute a transaction, please use the state.storage.transaction()…`) | — | ❌ (igual que en producción) |
| D1 local: `db.batch()` de Drizzle con una sentencia que falla | **Atómico**: no queda ninguna fila | — | ✅ |
| `/3d` en Chromium (WebGL2 por software) a 1440 y 390 px | Renderiza; sin errores de consola (1 aviso: `THREE.Clock` obsoleto, viene de R3F 9.8 con three 0.186) | Sin errores | ✅ |

Evidencias en esta carpeta: `measure-results.json`, `auth-results.json`, `auth-results-tx.json`, `d1-tx-results.json` y `capturas/`.

### Qué pesa en el Worker
Sin minificar: el chunk de Better Auth ≈ 993 KiB, `entry.mjs` (runtime de Astro y renderizador de React) ≈ 782 KiB, esquemas Zod ≈ 179 KiB. Hay margen de sobra; si hiciera falta, minificar el SSR o sacar la autenticación a otro Worker (plan B del plan).

## Decisiones que salen del spike
1. **Better Auth sobre D1 con `transaction: false`** (el valor por defecto del adaptador Drizzle). D1 no admite transacciones interactivas; Better Auth funciona porque consume los tokens con un único `DELETE … RETURNING`, que es atómico. Las escrituras múltiples propias irán con `db.batch()`, que sí es atómico. No hace falta Kysely.
2. **Biome con `html.experimentalFullSupportEnabled: true`** para `.astro`. En modo por defecto da falsos positivos y, con `--write --unsafe`, renombra variables que usa la plantilla (rompe la página). Plan B si el modo experimental falla con más archivos: desactivar `noUnusedVariables` y `noUnusedImports` solo en `*.astro`, y si no basta, Prettier con su plugin de Astro solo para `.astro`.
3. **`better-auth/minimal`**: deja fuera Kysely y los adaptadores que no usamos.
4. **Entorno 3D sin HDRI externos** (`RoomEnvironment` + PMREM): no obliga a abrir la CSP a CDNs.
5. **Probar con `wrangler dev`, no con `astro preview`**: `wrangler dev` lee la misma configuración redirigida que `wrangler deploy` (`dist/server/wrangler.json`) y respeta el entorno elegido al compilar.

## Pendiente en local (Javi, con su cuenta)
1. `pnpm exec wrangler login`.
2. `pnpm exec wrangler d1 create taller6mm-spike` y copia el `database_id` en `wrangler.jsonc`.
3. `pnpm exec wrangler d1 migrations apply DB --remote` (pide confirmación).
4. `pnpm build` y `pnpm exec wrangler deploy` (plan gratuito).
5. CPU: en una terminal, `pnpm exec wrangler tail --format json > tail.ndjson`; en otra, `node scripts/load.mjs --base https://taller6mm-spike.<tu-subdominio>.workers.dev --n 200`. Corta el tail y ejecuta `node scripts/cpu-from-tail.mjs tail.ndjson` → p50/p95/p99 de CPU por ruta frente al límite de 10 ms.
6. Previews: `pnpm exec wrangler preview --name pr-1` con esta build y anotar si funciona.
7. Al terminar, borrar el Worker y la base (el hook impide que Claude borre recursos).

## Reproducir en local (Windows, macOS o Linux)
```bash
cd spikes/0001-stack
pnpm install
pnpm db:migrate:local
pnpm build
pnpm measure
pnpm auth:flow
```
`pnpm d1:tx` repite la sonda de transacciones. Para la variante con transacciones: `CLOUDFLARE_ENV=tx pnpm build` (en PowerShell, `$env:CLOUDFLARE_ENV="tx"; pnpm build`) y después `pnpm auth:flow:tx`. Antes de medir, cierra cualquier servidor en el puerto 4321: el script se niega a medir otro.
