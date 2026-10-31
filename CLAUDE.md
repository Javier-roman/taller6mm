# Taller6mm — taller virtual de airsoft

> Nombre del proyecto desde el 31-10-2026 (antes, nombre en clave BANCADA). La marca visible vive en un solo sitio, `packages/ui/src/brand.ts`; los identificadores técnicos usan `taller6mm` (repo, paquetes `@taller6mm/*`, Workers, bases de datos). La carpeta local sigue siendo `C:\dev\bancada` hasta cerrar la Fase 0.

Web donde cualquier jugador elige **su réplica exacta**, la monta en un banco de trabajo virtual con **todos los accesorios del mercado** representados con **fidelidad 1:1**, sabe **qué encaja y por qué**, ve **dónde comprar** cada pieza (stock y precio en tiendas de España y del extranjero) y **comparte** sus builds con la comunidad.

Responsable de producto: Javi (desarrollo web de nivel medio, estudiante de ciberseguridad). Idioma de trabajo: español. El perfil de su equipo (Windows 11, herramientas, GPU) está en `CLAUDE.local.md`, que no se sube al repo.

## Dónde está cada cosa
La especificación está en `docs/` y **no se importa aquí** para no gastar contexto. Antes de trabajar en un área, lee su documento:

| Área | Documento |
|---|---|
| Índice y glosario de airsoft | `docs/00-INDICE.md` |
| Visión, usuarios, alcance, métricas | `docs/01-vision-y-producto.md` |
| Dirección de arte, La Armería (inicio), sistema de diseño | `docs/02-experiencia-y-diseno.md` |
| El Banco (configurador) y motor de compatibilidad | `docs/03-el-banco-configurador.md` |
| Mercado: fuentes, rastreo, emparejado, precios, alertas | `docs/04-mercado-e-ingesta.md` |
| Assets 2D/3D y fidelidad 1:1 | `docs/05-assets-y-fidelidad.md` |
| Comunidad, rankings, moderación | `docs/06-comunidad.md` |
| Arquitectura, datos, APIs, costes | `docs/07-arquitectura.md` |
| Calidad, seguridad, operación | `docs/08-calidad-seguridad-operacion.md` |
| Legal y cumplimiento | `docs/09-legal-y-cumplimiento.md` |
| Fases y criterios de aceptación | `docs/10-roadmap.md` |
| Decisiones de arquitectura | `docs/adr/` |
| Tiendas y marcas elegidas por Javi | `docs/fuentes/` |
| Capturas de referencia visual | `docs/referencias/` (míralas con Read) |

## Principios no negociables
1. **Fidelidad 1:1.** Réplicas y accesorios con proporciones y medidas reales en mm. Si un asset no alcanza un nivel, se muestra con su nivel real (T0–T3, docs/05); nunca se disfraza.
2. **Datos honestos.** Precio y stock siempre con la fecha de la última comprobación. Lo desconocido es `null` + bandera, nunca un valor inventado. Datos de ejemplo solo en seeds marcados `is_demo`, jamás en producción. Nada de estadísticas de videojuego (daño, precisión).
3. **Compatibilidad explicable.** Cada veredicto lleva motivo, fuente y confianza.
4. **Ingesta respetuosa y legal.** robots.txt (incluidas las líneas `Content-Signal`), ritmo bajo, User-Agent identificado, opt-out inmediato, sin login, sin evadir bloqueos ni CAPTCHAs. Primero feeds y APIs oficiales.
5. **Assets con licencia.** Solo se publica lo propio o lo cedido. Las fotos de terceros son referencia interna: nunca se publican ni se proyectan como textura. Sin logos ni marcajes ("trades") salvo permiso de la marca.
6. **Solo airsoft.** Nunca armas de fuego reales, munición real ni piezas reguladas.
7. **Rendimiento y accesibilidad son requisitos** (presupuestos en docs/08, WCAG 2.2 AA).
8. **Seguridad por defecto** (OWASP ASVS 5.0 nivel 2) y privacidad por diseño (RGPD).
9. **Coste ~0 €/mes**: planes gratuitos; ningún servicio de pago sin preguntar.
10. **El "wow" nunca rompe la función**: toda experiencia visual tiene alternativa ligera y accesible.

## Stack (detalle, cifras y alternativas en `docs/adr/0001-stack.md`)
- **Web**: Astro 6 (salida `server`, adaptador Cloudflare) + islas **React 19**; Tailwind CSS v4 con tokens en CSS variables; nanostores entre islas.
- **3D**: three.js + React Three Fiber + drei + postprocessing; GSAP para cinemáticas; glTF con Meshopt y texturas KTX2.
- **Plataforma**: Cloudflare Workers, D1 (tres bases: `core`, `mercado`, `busqueda`), R2, Queues, Cron, Durable Objects, Turnstile.
- **Datos**: Drizzle ORM + drizzle-kit; Zod 4 en todos los contratos.
- **Auth**: Better Auth (enlace mágico, Google, Discord, passkeys).
- **Ingesta**: Node + Crawlee en GitHub Actions → API interna firmada (HMAC) del worker `jobs`.
- **Assets**: Python 3.12 + uv, Blender sin interfaz, gltf-transform.
- **Calidad**: Biome, TypeScript estricto, Vitest (+ pool de Workers), Playwright + axe, fast-check, Lighthouse CI.

Usa siempre las últimas versiones estables y **verifica la documentación actual** antes de usar una API que aún no se haya usado en este repo.

## Estructura del monorepo
```
apps/web          Astro: web pública + /trastienda (admin)
apps/jobs         Worker (Hono): cron, colas, API interna de ingesta, alertas
apps/crawler      Node + Crawlee (GitHub Actions / local)
apps/pipeline     Python: fotos → 2D/3D, Blender, validación de fidelidad
packages/db       Drizzle: esquemas core/mercado/busqueda, migraciones, seeds
packages/domain   Tipos y esquemas Zod compartidos
packages/compat   Motor de compatibilidad (TS puro, sin E/S)
packages/market   Normalización, emparejado, precio puesto en casa, optimizador
packages/ui       Tokens de diseño, marca, componentes React
packages/config   tsconfig y Biome compartidos
assets-src        Manifiestos de assets fuente (los binarios viven en R2 privado)
docs              Especificación, ADRs, informes de fase, runbooks, referencias
```

## Comandos (los crea la Fase 0; mantenlos al día)
- `pnpm dev` · `pnpm build` · `pnpm verify` (lint + typecheck + test + build) · `pnpm e2e` · `pnpm lh` · `pnpm size`
- `pnpm db:migrate:local` · `pnpm db:seed:local` · `pnpm db:reset:local`. Lo remoto, solo con permiso explícito.
- `pnpm --filter @taller6mm/crawler crawl --source <id>` trabaja contra fixtures; `--live` solo con permiso de Javi.

## Convenciones
- Código, identificadores y commits en inglés. Interfaz, documentación y comentarios de "por qué" en español (es-ES).
- TypeScript `strict`, sin `any` (usa `unknown` + Zod). Lógica pura en `packages/*`; entrada/salida en los bordes.
- Unidades: longitudes en **mm** (tipo `Millimeters`), dinero en **céntimos enteros** + moneda ISO 4217, fechas ISO 8601 en UTC.
- Color, tipografía, espaciado, radios, sombras y duraciones **solo desde tokens** de `packages/ui`.
- Conventional Commits pequeños. Ramas `feat/…`, `fix/…`, `chore/…`. PR con CI verde. Nunca push directo a `main`.
- Migraciones: nunca editar una ya aplicada; cambios aditivos; cada una con su test.
- Secretos solo en `.dev.vars` (ignorado) y `wrangler secret`. Nunca leerlos, copiarlos ni imprimirlos.
- **Multiplataforma**: Javi desarrolla en Windows 11 (PowerShell y Git Bash). Los scripts de `package.json` no llevan sintaxis de bash: nada de `rm -rf`, `cp` ni `VAR=x comando`. Usa scripts `.mjs`, `rimraf` o `cross-env`. Rutas siempre con `node:path`.

## Cómo trabajamos
- Tarea no trivial → **modo plan** primero: propuesta, OK de Javi, implementación en rebanadas verticales.
- Decisión con impacto → ADR (`/adr`). Cambio de comportamiento → actualiza el doc de `docs/` en el mismo PR.
- **Pregunta antes de**: contratar o activar servicios de pago, cambiar un ADR aceptado, dar de alta un dominio para rastrear, cualquier petición `--live` a tiendas, desplegar a producción, migraciones remotas, borrar datos, añadir una dependencia de cliente de más de 30 KB gz.
- Skills: `/verify` (antes de cada commit), `/revisar-ui <ruta>`, `/nueva-tienda`, `/nueva-replica`, `/adr`, `/informe-fase <n>`.
- Subagentes: `critico-diseno`, `revisor-seguridad`, `ingeniero-ingesta`, `revisor-fidelidad`, `auditor-rendimiento`. Pásalos al cerrar cada rebanada de su área.
- **Mira lo que construyes**: usa el MCP de Playwright (capturas a 390 px y 1440 px) antes de dar algo por bueno.
- **El diseño es lo más importante para Javi.** En cada hito visual, para y enséñale capturas en escritorio y móvil, pasadas antes por `critico-diseno`. No continúes ni fusiones sin su OK explícito. Antes de construir La Armería (Fase 1), presenta varias propuestas con capturas basadas en `docs/referencias/` y espera a que elija.
- Explica a Javi cada decisión importante en 2-3 líneas: qué, por qué y qué alternativa descartaste. Sin jerga innecesaria.
- Nunca manejes credenciales de Javi: si hace falta iniciar sesión (wrangler, gh), dale el comando y lo ejecuta él.
- **Nunca con privilegios de administrador**: si el aviso de inicio (`check-env`) detecta una sesión elevada, no instales dependencias ni ejecutes scripts. Pide a Javi que reinicie Claude Code desde una terminal normal.

## Definición de terminado
- [ ] `pnpm verify` en verde y e2e del flujo afectado en verde
- [ ] Visto en navegador (capturas), sin errores de consola
- [ ] Teclado completo, contraste AA, `prefers-reduced-motion` respetado
- [ ] Dentro de los presupuestos de rendimiento (docs/08)
- [ ] Validación de entradas, autorización y límite de ritmo en todo endpoint nuevo
- [ ] Revisión del subagente del área sin bloqueantes
- [ ] Docs y ADR actualizados; ningún TODO sin issue
