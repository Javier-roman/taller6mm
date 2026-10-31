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

## Disparadores de revisión
- El prototipo incumple algún punto de validación.
- El uso supera el 50 % de algún límite gratuito de forma sostenida: valorar Workers Paid.
- D1 se queda corto en consultas o en tamaño: valorar Postgres vía Hyperdrive.
- Aparece una necesidad de producto que Astro con islas resuelve mal.
