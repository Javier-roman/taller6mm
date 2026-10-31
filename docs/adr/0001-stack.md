# ADR-0001 — Stack base: Astro 6 + islas React en Cloudflare Workers

- **Estado**: Propuesta (se valida con un prototipo en la Fase 0)
- **Fecha**: 2026-10-31
- **Decisores**: Javi (+ Claude Code)

## Contexto
Requisitos:
1. Experiencia 3D e interactiva muy rica (inicio y configurador).
2. Catálogo con miles de páginas rápidas e indexables (SEO).
3. Comunidad con cuentas.
4. Trabajos de ingesta y alertas.
5. Coste cercano a 0 €/mes **con uso comercial permitido** (afiliación).
6. Un solo desarrollador de nivel medio, asistido por Claude Code.

Hechos verificados en octubre de 2026 (revalidar en el prototipo):
- **Vercel Hobby** solo admite uso personal no comercial; el plan Pro cuesta 20 $/mes por usuario.
- **Cloudflare Workers, plan gratuito**:
  - 100.000 peticiones/día, 10 ms de CPU por invocación y Workers de hasta 3 MiB comprimidos (10 MiB en el plan de pago de 5 $/mes).
  - D1: 500 MB por base, 10 bases, 5 GB por cuenta, 5 M filas leídas y 100.000 escritas al día. Los límites diarios se aplican desde septiembre de 2026.
  - R2: 10 GB sin coste de salida.
  - Queues: 10.000 operaciones/día.
  - Durable Objects con SQLite disponibles en el plan gratuito.
  - Images: 5.000 transformaciones únicas/mes.
- **Next.js 16 en Workers** vía OpenNext funciona (la API de adaptadores es estable desde 16.2), pero su bundle suele superar los 3 MiB del plan gratuito.
- **Astro**: Cloudflare adquirió Astro en enero de 2026. Astro 6 (estable desde marzo de 2026) ejecuta `astro dev` dentro de workerd, con acceso local a D1, R2, KV y Durable Objects, y tiene CSP estable.
- **D1** soporta FTS5, pero no exporta bases que contengan tablas virtuales.

## Decisión
- **Web**: Astro 6 con salida `server` y adaptador de Cloudflare. Islas React 19 donde haya interactividad, y el 3D con React Three Fiber cargado como isla `client:only`.
- **Plataforma**: Cloudflare (Workers, D1 ×3, R2, Queues, Cron, Durable Objects, Turnstile, Web Analytics).
- **Datos**: Drizzle ORM con tres bases D1: `core`, `mercado` y `busqueda` (FTS5, reconstruible).
- **Auth**: Better Auth sobre D1.
- **Ingesta**: crawler Node (Crawlee) en GitHub Actions, que entrega lotes firmados al worker `jobs` (Hono).
- **Monorepo**: pnpm + Turborepo, TypeScript estricto, Biome, Vitest, Playwright.

## Alternativas consideradas
| Opción | Pros | Contras | Por qué no (por ahora) |
|---|---|---|---|
| Next.js 16 + OpenNext en Workers | Ecosistema enorme; RSC | El bundle supera 3 MiB, así que exige plan de pago; SSR más pesado para el límite de CPU | Coste y holgura |
| Next.js en Vercel | La mejor integración con Next | Hobby prohíbe el uso comercial; Pro cuesta 20 $/mes | Coste |
| React Router 7 en Workers | Nativo en Workers, ligero | Menos optimizado para contenido estático y SEO masivo que Astro | Astro encaja mejor con el catálogo |
| SvelteKit + Threlte | Muy ligero | Ecosistema 3D más pequeño que R3F/drei | Riesgo en la parte 3D |
| Postgres (Neon o Supabase) en lugar de D1 | SQL más rico | Otro proveedor; límites y pausas del plan gratuito; latencia desde el borde | Empezar simple; queda como vía de escalado con Hyperdrive |

## Consecuencias
**Positivas**:
- Páginas de catálogo muy ligeras y buen SEO.
- 3D aislado en islas.
- Desarrollo local igual que producción (workerd).
- Coste de 0 € al inicio.

**Negativas y riesgos**:
- El estado compartido entre islas obliga a usar nanostores.
- El límite de 10 ms de CPU exige caché agresiva y lógica ligera en las rutas SSR.
- D1 obliga a un diseño frugal de escrituras.
- Cada consulta entre bases se compone en el servicio, porque no hay JOIN entre ellas.

## Validación (prototipo de la Fase 0)
- [ ] Isla R3F con postprocesado desplegada en el plan gratuito; chunk 3D ≤ 350 KB gz.
- [ ] Worker web comprimido muy por debajo de 3 MiB (objetivo: ≤ 1,5 MiB, para tener margen).
- [ ] Ruta SSR con consulta a D1 dentro del límite de CPU, medido con observabilidad de Workers.
- [ ] Better Auth funcionando con D1 y Drizzle.
- [ ] Biome con `.astro` aceptable. Si no, alternativa documentada (Prettier con su plugin de Astro + ESLint).

## Resultados en la nube
Medido el 31-10-2026 por Claude Code en un contenedor Linux en la nube, **sin cuenta de Cloudflare**: todo en local con workerd, D1 local y `wrangler deploy --dry-run`. Código, scripts y evidencias en la rama `spike/0001-stack` (carpeta `spikes/0001-stack/`, PR en borrador que no se fusiona).

Versiones probadas (con la política del plan: nada con menos de 3 días publicado): Astro 7.4.3, `@astrojs/cloudflare` 14.4.3, React 19.3.1, wrangler 4.154.0, Drizzle 0.45.4, Better Auth 1.7.14, three 0.186.1, R3F 9.8.2, `@react-three/postprocessing` 3.2.2, Biome 2.6.3, TypeScript 6.0.3, Node 26.13.0 y pnpm 12.16.1.

| Medida | Resultado | Límite u objetivo | Veredicto |
|---|---|---|---|
| Worker comprimido (`wrangler deploy --dry-run --outdir`) | 505,6 KiB gzip (2.200 KiB sin comprimir, sin minificar; minificado ≈ 312 KiB) | Límite 3 MiB; objetivo ≤ 1,5 MiB | ✅ 16 % del límite |
| Source maps (wrangler los sube aparte) | 958,6 KiB gzip, fuera de «Total Upload» | Confirmar que no cuentan para el límite | ⚠️ por verificar |
| Arranque del Worker (`wrangler check startup`, CPU local) | 44,7 a 83,6 ms de CPU activa | Orientativo (límite de arranque: 1 s) | ✅ |
| 1.ª petición de cada isolate (CPU local con perfilador, orientativo) | `/` anónimo 38–63 ms tras cargar Better Auth solo con cookie (antes 72–108 ms); `/api/auth/get-session` 39–61 ms; en caliente ≈ 11 ms | Límite de CPU: 10 ms por invocación | ⚠️ riesgo en frío |
| Chunk 3D de la escena (`/3d`, gzip -9) | 268,9 KB (brotli 221,0 KB) | ≤ 350 KB gz | ✅ 77 % |
| Isla 3D con el runtime de React | 338,0 KB gzip (97 % del presupuesto) | ≤ 350 KB gz | ✅ sin margen para los cargadores glTF/KTX2 de la Fase 1 (≈ 45 KB) |
| Momento de carga del chunk 3D | `client:only` lo pide antes del primer pintado | Después del primer pintado (docs/02 §3.6) | ❌ se corrige en la Fase 1 |
| Biome en `.astro`, modo por defecto | 4 avisos, los 4 falsos positivos (`noUnusedVariables` y `noUnusedImports` de lo que usa la plantilla) | 0 | ❌ |
| Biome en `.astro` con `html.experimentalFullSupportEnabled` | 0 avisos en lint y formato | 0 | ✅ (experimental) |
| Better Auth: enlace mágico sobre D1 + Drizzle (`transaction: false`) | 10/10 pasos: alta, enlace (emisor de prueba en D1), verificación, cookie, sesión con y sin caché, SSR con sesión y enlace de un solo uso | Todo verde | ✅ |
| Better Auth con `transaction: true` | La verificación del enlace da 500: D1 rechaza `BEGIN` | — | ❌ (esperado) |
| D1: `BEGIN` crudo y `db.transaction()` de Drizzle | Rechazados, igual que en producción | — | ❌ |
| D1: `db.batch()` con una sentencia que falla | Atómico: no queda ninguna fila | — | ✅ |
| `/3d` en Chromium (WebGL2) a 1440 y 390 px | Renderiza sin errores de consola (la auditoría encontró y se corrigió un bucle de redimensionado del canvas) | Sin errores | ✅ |

Consecuencias para la Fase 0 (se aplican en S2 y siguientes):
1. **Better Auth con `transaction: false`** (valor por defecto del adaptador Drizzle). Funciona porque consume los tokens con un único `DELETE … RETURNING`. Las escrituras múltiples propias van con `db.batch()`. No hace falta Kysely. Se usa `better-auth/minimal`.
2. **Biome con `html.experimentalFullSupportEnabled: true`**. En modo por defecto da falsos positivos, y `--write --unsafe` renombra variables que usa la plantilla y rompe la página. Plan B: desactivar esas dos reglas solo en `*.astro`; si no basta, Prettier con su plugin de Astro solo para `.astro`.
3. El Worker cabe con mucho margen, así que no hace falta sacar la autenticación a otro Worker.
4. Las pruebas locales de la build se hacen con `wrangler dev`, que lee la misma configuración que `wrangler deploy`. `astro preview` no respeta el entorno elegido al compilar.
5. **La CPU en frío es el riesgo real del plan gratuito**, no el tamaño. Better Auth (≈ 1 MB sin minificar) se evalúa en la primera petición de cada isolate que lo importa. Mitigaciones: importarlo solo en las rutas que lo necesitan y solo si hay cookie de sesión (ya en el spike), minificar el SSR, quitar `react-dom/server` del Worker si ninguna isla lo necesita, y caché en el borde para el HTML anónimo. Si aun así la CPU en frío supera los 10 ms de forma habitual: plan B del plan (autenticación en otro Worker) o Workers Paid, con el OK de Javi.
6. **3D en la Fase 1**: chunk después del primer pintado (directiva de cliente propia y póster para quien no tenga WebGL2, pida movimiento reducido o ahorre datos), `extend` selectivo de three (−54 KB gz medidos) y cargadores glTF/KTX2 bajo demanda.

Revisión de `auditor-rendimiento`: reproduce las cifras de tamaño, corrige el método (frío frente a caliente, source maps, gzip-6) y las conclusiones de arriba ya lo reflejan. Detalle en el PR del spike.

## Pendiente en local
Lo que necesita la cuenta de Cloudflare de Javi. Pasos exactos en `spikes/0001-stack/LEEME.md` de la rama del spike.
1. **Despliegue en el plan gratuito**: `wrangler login`, crear la D1 `taller6mm-spike`, migraciones remotas, `wrangler deploy` y comprobar `/`, `/3d` y el flujo de autenticación.
2. **CPU p50/p95/p99** frente al límite de 10 ms, separando **frío** (1.ª petición de cada isolate, tras cada despliegue) y **caliente** (unas 200 peticiones por escenario con calentamiento). Escenarios: `/` y `/api/auth/get-session` anónimos, con cookie completa y solo con el token, más la petición de enlace mágico. Con `wrangler tail --format json`, `scripts/load.mjs` y `scripts/cpu-from-tail.mjs` (el middleware del spike etiqueta isolate, número de petición y escenario).
3. **Source maps**: confirmar en el panel o en la respuesta del despliegue que no cuentan para el límite de 3 MiB.
4. **Previews**: `wrangler preview --name pr-1` con la build de Astro.

La ADR sigue en **Propuesta** hasta tener la CPU. Al aceptarla: Decisión con Astro 7, Node 26, TypeScript 6 y Vitest 4.1, la tabla de CPU añadida a esta sección y las casillas de Validación marcadas.

## Disparadores de revisión
- El prototipo incumple algún punto de validación.
- El uso supera el 50 % de algún límite gratuito de forma sostenida: valorar Workers Paid.
- D1 se queda corto en consultas o en tamaño: valorar Postgres vía Hyperdrive.
- Aparece una necesidad de producto que Astro con islas resuelve mal.
