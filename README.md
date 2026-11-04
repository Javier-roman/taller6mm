# Taller6mm

Taller virtual de airsoft: eliges **tu réplica exacta**, la montas en un banco de trabajo virtual con los
accesorios del mercado representados **a escala 1:1**, ves **qué encaja y por qué**, **dónde comprar** cada
pieza (stock y precio con su fecha de comprobación) y **compartes** tus builds.

> **Estado (04-11-2026)**: Fase 0 «Cimientos» en cierre. Fusionado: arranque seguro (S0), monorepo y CI (S2),
> Cloudflare de preview y previews por PR (S3, ADR-0008), seguridad base (S4), semilla del sistema de diseño
> (S5) y esta documentación (S6). Propuestas del inicio (La Armería, Fase 1) en el
> [PR #10](https://github.com/Javier-roman/taller6mm/pull/10) y en las ramas `spike/armeria-a-3d` y
> `spike/armeria-b-25d`, pendientes de decisión.

## Puesta en marcha en 5 pasos
Funciona igual en Windows 11 (PowerShell o Git Bash), macOS y Linux. En Windows, usa una terminal **normal**
(nunca «Ejecutar como administrador») y una carpeta **fuera de OneDrive**.

1. **Requisitos**: Node 26.13 o superior (fijado en `.node-version`), pnpm 12.16.1, git y
   [gitleaks](https://github.com/gitleaks/gitleaks) (lo usa el pre-commit).
   ```powershell
   npm install --global pnpm@12.16.1
   ```
2. **Clonar e instalar** (el lockfile manda; también instala los hooks de lefthook):
   ```powershell
   git clone https://github.com/Javier-roman/taller6mm.git
   cd taller6mm
   pnpm install --frozen-lockfile
   ```
3. **Bases de datos locales** (D1 en workerd, con datos de ejemplo marcados `is_demo`):
   ```powershell
   pnpm db:reset:local
   ```
4. **Arrancar** y abrir <http://127.0.0.1:4321> (y `/sistema`, el sistema de diseño vivo):
   ```powershell
   pnpm dev
   ```
5. **Comprobar** antes de cada commit (lint, tipos, tests, build y tests de `.claude`):
   ```powershell
   pnpm verify
   ```

## Comandos
| Comando | Qué hace |
|---|---|
| `pnpm dev` | Servidor de desarrollo de la web (Astro en workerd) |
| `pnpm build` | Build de todo el monorepo |
| `pnpm verify` | Puerta de calidad: Biome, TypeScript, Vitest, build y tests de la configuración |
| `pnpm e2e` | Playwright + axe contra la build servida en workerd, a 390 y 1440 px (requiere `pnpm build`) |
| `pnpm lh` | Lighthouse móvil en local |
| `pnpm size` | Presupuestos de tamaño (JS, CSS y fuentes) |
| `pnpm db:migrate:local` · `db:seed:local` · `db:reset:local` | Bases D1 locales. Lo remoto, solo a mano y con permiso |

## Estructura
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

## Stack
Astro 7 (salida `server`, Cloudflare Workers) con islas React 19 · Tailwind CSS v4 sobre tokens propios ·
three.js y React Three Fiber para el 3D · Cloudflare Workers, D1, R2 y Queues · Drizzle ORM y Zod 4 ·
Biome, TypeScript estricto, Vitest, Playwright + axe y Lighthouse. Motivos y cifras en
[ADR-0001](docs/adr/0001-stack.md).

## Documentación
- Índice y glosario: [docs/00-INDICE.md](docs/00-INDICE.md). Cada área (visión, diseño, configurador, mercado,
  assets, comunidad, arquitectura, calidad, legal y roadmap) tiene su documento en `docs/`.
- Decisiones: [docs/adr/](docs/adr/). Informes de fase y capturas: [docs/informes/](docs/informes/).
- Operación: [docs/runbooks/](docs/runbooks/).
- Cómo colaborar: [CONTRIBUTING.md](CONTRIBUTING.md). Cambios: [CHANGELOG.md](CHANGELOG.md).
- El proyecto se desarrolla con Claude Code: su memoria es [CLAUDE.md](CLAUDE.md) y el kit de arranque,
  [LEEME.md](LEEME.md).

## Principios
Fidelidad 1:1 con medidas reales en mm · datos honestos (precio y stock siempre con fecha; lo desconocido es
`null`, nunca inventado) · compatibilidad explicable · ingesta respetuosa y legal · solo assets propios o con
licencia · **solo airsoft** · rendimiento y accesibilidad (WCAG 2.2 AA) como requisitos · seguridad por defecto
(OWASP ASVS 5.0 nivel 2) y RGPD · coste ~0 €/mes. Detalle en [CLAUDE.md](CLAUDE.md).

## Seguridad
Para avisar de una vulnerabilidad, sigue [SECURITY.md](SECURITY.md) (avisos privados de GitHub). No abras un
issue público.

## Licencia
Pendiente de decidir (docs/09-legal-y-cumplimiento.md). Mientras tanto, el código es público para consulta y
no se concede ninguna licencia de uso.
