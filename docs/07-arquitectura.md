# 07 · Arquitectura

La decisión base está en `docs/adr/0001-stack.md` (Astro 6 + islas React en Cloudflare Workers). Este documento describe el sistema.

## 1. Vista general
```
                   Usuarios (navegador / PWA)
                            │ HTTPS
               ┌────────────▼─────────────┐
               │ Cloudflare: CDN, WAF,    │
               │ Turnstile, Web Analytics │
               └────────────┬─────────────┘
          ┌─────────────────▼─────────────────┐      ┌────────────────────────┐
          │ Worker web (Astro 6, SSR)         │─────▶│ R2 · assets públicos   │
          │ páginas · API v1 · Actions ·      │      │ modelos, sprites, OG   │
          │ Trastienda                        │      └────────────────────────┘
          └──┬──────────────┬──────────────┬──┘
             │ D1           │ D1           │ D1
           core          mercado      busqueda (FTS5)
             ▲              ▲              ▲ reindexado
          ┌──┴──────────────┴──────────────┴──┐  cola  ┌─────────────────────────┐
          │ Worker jobs (Hono)                │◀───────│ POST /internal/ingest   │
          │ cron · colas · alertas · rankings │        └───────────▲─────────────┘
          │ Durable Objects (contadores,      │                    │ lotes firmados
          │ límites de ritmo)                 │        ┌───────────┴─────────────┐
          └──┬────────────────────────────────┘        │ Crawler (Crawlee) en    │
             │ email / push                            │ GitHub Actions          │
             ▼                                         └─────────────────────────┘
       Resend · Web Push

  Pipeline de assets (Python + Blender, local o GPU) ──▶ R2 + API de la Trastienda
```

## 2. Componentes
| Componente | Responsabilidad | Tecnología |
|---|---|---|
| `apps/web` | Páginas públicas (SSR + caché), islas interactivas, API pública v1, Actions, Trastienda | Astro 6, React 19, R3F, Tailwind v4 |
| `apps/jobs` | Ingesta firmada, consumidores de cola, cron (rankings, alertas, archivo, salud), Durable Objects (contadores, límites de ritmo) | Worker con Hono |
| `apps/crawler` | Descubrir, descargar, extraer, normalizar, clasificar, emparejar y enviar lotes | Node 22, Crawlee, transformers.js |
| `apps/pipeline` | Assets T0–T3 y validación de fidelidad | Python 3.12 (uv), Blender, gltf-transform |
| `packages/compat` | Motor de compatibilidad | TS puro |
| `packages/market` | Normalización, emparejado, precio puesto en casa, optimizador | TS puro + HiGHS (WASM) |
| `packages/db` | Esquemas, migraciones, seeds y repositorios | Drizzle + D1 |
| `packages/domain` | Tipos y contratos compartidos | Zod 4 |
| `packages/ui` | Tokens, marca y componentes | React + CSS variables |

## 3. Datos
### 3.1 Base `core`
- **Catálogo**: `brands`, `platforms`, `categories` (árbol), `interfaces` (estándares de montaje con medidas y equivalencias), `products`, `variants`, `slots`, `mounts`, `adapters`, `compat_overrides`, `dimensions`, `assets`.
- **Comunidad**: usuarios y sesiones (Better Auth), `profiles`, `builds`, `build_versions`, `collections`, `collection_items`, `likes`, `comments`, `reviews`, `review_votes`, `compat_reports`, `follows`.
- **Moderación y sistema**: `reports`, `moderation_actions`, `notifications`, `watchlists`, `rankings` (materializado), `audit_log`.

Detalle de las tablas del catálogo:
| Tabla | Qué guarda |
|---|---|
| `products` | Tipo (réplica, accesorio, pieza o consumible), marca, modelo, plataforma, `specs` JSON validado por el esquema de su categoría, estado |
| `variants` | Color, versión, GTIN y MPN |
| `slots` | Ranuras de un producto: clave, interfaz aceptada, geometría en mm, cardinalidad |
| `mounts` | Cómo se monta una pieza: interfaz requerida, ancla, huella en el raíl |
| `adapters` | Interfaz A → interfaz B |
| `dimensions` | Cotas con fuente, confianza y evidencia |
| `assets` | Nivel, vista, ficheros en R2 por LOD, anclajes, licencia, procedencia, validación, estado |

### 3.2 Base `mercado`
`shops`, `sources`, `crawl_runs`, `listings` (dato bruto por URL), `offers` (vista actual de cada listado emparejado), `price_events`, `match_queue`, `radar_items`, `fx_rates`, `optouts`.

### 3.3 Base `busqueda`
Tablas FTS5 con `tokenize = "unicode61 remove_diacritics 2"` para productos, builds y guías. Se reconstruyen desde `core` por cron o por eventos. Va separada porque **D1 no exporta bases con tablas virtuales**, y `core` y `mercado` tienen que poder exportarse para las copias.

### 3.4 Identificadores y tipos
- IDs ULID o UUIDv7 en texto.
- Dinero en céntimos enteros + moneda.
- mm en REAL con 0,1 de precisión.
- Fechas ISO 8601 en UTC.
- JSON validado con Zod al leer y al escribir.

## 4. APIs
- **Pública** `/api/v1/*`: lecturas de productos, ofertas, builds y búsqueda, con caché en el borde. Esquemas Zod con OpenAPI generado.
- **Mutaciones**: Astro Actions con validación Zod, CSRF y límites de ritmo.
- **Interna** (`jobs`): `/internal/ingest` (firma HMAC), `/internal/reindex` y webhooks (Resend).
- **Trastienda** `/trastienda/*`: rol `staff` con passkey o 2FA. Opcionalmente, detrás de Cloudflare Access (Zero Trust) como segunda capa.

## 5. Caché y rendimiento
- **Catálogo y fichas**: SSR con caché en el borde (TTL corto + `stale-while-revalidate`) e invalidación por clave cuando cambian el producto o sus ofertas.
- **Ofertas en la ficha**: isla que pide `/api/v1/offers?product=` con un TTL de minutos.
- **Assets**: en R2, tras un dominio propio, con caché larga e inmutable (nombre de fichero con hash).
- **Imágenes de usuario**: los originales van a un bucket privado y solo se sirven variantes transformadas (Cloudflare Images con `metadata=none`).

## 6. Trabajos programados (cron en `jobs`)
| Frecuencia | Trabajo |
|---|---|
| 15 min | Ranking de tendencia; volcado de contadores de los Durable Objects a D1 |
| 1 h | Salud de fuentes; reintentos de la cola |
| Diario | Rankings largos; tipos de cambio del BCE; reindexado completo de la búsqueda; resumen de alertas; limpieza de referencias internas caducadas |
| Semanal | Exportación de `core` y `mercado` a R2 (copia); resumen de novedades |
| Mensual | Archivo de `price_events` antiguos en R2 |

## 7. Entornos
- **Local**: `astro dev` en workerd con D1, R2, KV y Durable Objects locales, y seeds de demo.
- **Preview**: un despliegue por PR con bases de preview y datos de demo.
- **Producción**: despliegue desde `main` tras CI verde y aprobación de Javi. Las migraciones remotas son manuales y con confirmación.

## 8. Costes
Planes gratuitos verificados en octubre de 2026; revalidar antes de cada fase.

| Recurso | Límite gratuito | Uso previsto al inicio | Válvula |
|---|---|---|---|
| Workers | 100.000 peticiones/día; 10 ms de CPU por invocación; 3 MiB por Worker | Bajo, con caché en el borde | Workers Paid (5 $/mes) |
| D1 | 500 MB por base, 10 bases, 5 GB en total; 5 M filas leídas y 100.000 escritas al día | Catálogo y comunidad pequeños; solo cambios de mercado | Paid; Postgres vía Hyperdrive |
| R2 | 10 GB; sin coste de salida | Modelos y sprites | Unos 0,015 $/GB al mes |
| Queues | 10.000 operaciones/día | Lotes grandes y pocos mensajes | Paid |
| Durable Objects | Disponibles con SQLite en el plan gratuito | Contadores y límites de ritmo | Paid |
| Images | 5.000 transformaciones únicas/mes | Fotos de usuarios | Pago por uso |
| GitHub Actions | Ilimitado en repos públicos; 2.000 min/mes en privados | Crawler y CI | Runner propio (gratuito) |
| Email (Resend) | Plan gratuito con límite mensual y diario (verificar) | Alertas agrupadas | Plan de pago o alternativa |
| Dominio | — | — | Unos 10–15 €/año |

Objetivo: 0 € al inicio y 5 $/mes cuando el tráfico lo pida.

## 9. Escalado
Por orden, solo cuando haga falta:
1. Workers Paid.
2. Réplicas de lectura de D1.
3. Postgres (Neon o Supabase) vía Hyperdrive, si D1 se queda corto.
4. Motor de búsqueda dedicado, si FTS5 no basta.
5. Crawler en un runner propio.

## 10. ADRs previstos
| ADR | Tema | Estado |
|---|---|---|
| 0001 | Stack | Propuesta |
| 0002 | Enfoque técnico del inicio (prototipos A/B) | Pendiente |
| 0003 | Esquema de compatibilidad | Pendiente |
| 0004 | Estrategia de caché | Pendiente |
| 0005 | Autenticación | Pendiente |
| 0006 | Modelos de IA del pipeline | Pendiente |
| 0007 | Emparejado | Pendiente |

## Criterios de aceptación
- [ ] El diagrama y las tablas reflejan lo implementado al cierre de cada fase.
- [ ] Cada base de D1 tiene migraciones reproducibles desde cero y seeds de demo.
- [ ] El uso diario de cada recurso gratuito se mide y queda por debajo del 50 % del límite.
