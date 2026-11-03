# Cómo colaborar en Taller6mm

Gracias por ayudar. Este documento resume cómo trabajamos; el detalle está en [CLAUDE.md](CLAUDE.md) y en
`docs/`. Si algo no encaja con lo que ves en el código, gana el código y se corrige el documento en el mismo PR.

## Antes de empezar
- Lee el documento del área que vas a tocar (tabla de [CLAUDE.md](CLAUDE.md) y [docs/00-INDICE.md](docs/00-INDICE.md)).
- Tarea no trivial: primero una propuesta corta (qué, por qué, alternativa descartada) y el OK de Javi.
- Decisión con impacto: un ADR en `docs/adr/` a partir de la [plantilla](docs/adr/0000-plantilla.md).
- **Pregunta antes de**: servicios de pago, cambiar un ADR aceptado, rastrear un dominio nuevo, peticiones
  `--live` a tiendas, desplegar a producción, migraciones remotas, borrar datos o añadir una dependencia de
  cliente de más de 30 KB gz.

## Ramas y commits
- Ramas `feat/…`, `fix/…`, `chore/…`, `docs/…` y `spike/…` (los spikes no se fusionan).
- **Nunca push directo a `main`**: está protegida (PR obligatorio, historial lineal, checks en verde y al día).
- Commits pequeños con [Conventional Commits](https://www.conventionalcommits.org/) **en inglés**:
  `feat(web): …`, `fix(db): …`, `docs(adr): …`.
- PR con descripción en español: qué cambia, por qué, cómo se ha probado y capturas si hay interfaz.
- PR apilados: antes de fusionar el de abajo, cambia la base del de arriba a `main`; integra `main` con merge
  (no rebase) y fusiona con squash comprobando la cabeza (`gh pr merge --squash --match-head-commit <sha>`).

## Convenciones de código
- TypeScript `strict` y sin `any` (usa `unknown` y Zod en los bordes). Lógica pura en `packages/*`; E/S en los bordes.
- Código, identificadores y commits en inglés; interfaz, documentación y comentarios de «por qué» en español de España.
- Unidades: longitudes en **mm** (`Millimeters`), dinero en **céntimos enteros** más moneda ISO 4217, fechas
  ISO 8601 en UTC.
- Color, tipografía, espaciado, radios, sombras y duraciones **solo desde los tokens** de `packages/ui`.
- Multiplataforma: los scripts de `package.json` no llevan sintaxis de bash (usa `.mjs`, `rimraf` o
  `cross-env`) y las rutas van con `node:path`. El CI pasa `verify` también en Windows.
- Migraciones: nunca se edita una ya aplicada; cambios aditivos; cada una con su test.
- Datos de ejemplo solo en seeds marcados `is_demo` y siempre señalados como DEMO en la interfaz.

## Calidad: definición de terminado
- [ ] `pnpm verify` en verde y e2e del flujo afectado en verde (`pnpm e2e`).
- [ ] Visto en el navegador a 390 y 1440 px, sin errores de consola.
- [ ] Teclado completo, contraste AA (axe) y `prefers-reduced-motion` respetado.
- [ ] Dentro de los presupuestos de rendimiento (`pnpm size`, Lighthouse; docs/08).
- [ ] Validación de entradas, autorización y límite de ritmo en todo endpoint nuevo.
- [ ] Revisión del área sin bloqueantes: diseño, seguridad, ingesta, fidelidad o rendimiento.
- [ ] Docs y ADR al día; ningún TODO sin issue.

**Interfaz**: el diseño es lo más importante del proyecto. En cada hito visual se presentan capturas a 390 y
1440 px revisadas, y no se fusiona sin el OK explícito de Javi.

## Dependencias y cadena de suministro
- Versiones exactas en el catálogo de `pnpm-workspace.yaml`; Renovate las actualiza.
- Nada publicado hace menos de 3 días, sin perder la procedencia firmada y sin scripts de instalación fuera de
  la lista blanca (lo comprueban tests en `scripts/`).
- En GitHub Actions, solo acciones de GitHub fijadas por SHA completo y permisos mínimos por job.

## Secretos y seguridad
- Secretos solo en `.dev.vars` (ignorado) y `wrangler secret`; nunca en el código, en issues ni en chats.
- gitleaks corre en el pre-commit y en el CI; GitHub bloquea secretos en los push.
- Vulnerabilidades: [SECURITY.md](SECURITY.md), por aviso privado. Nunca en un issue público.

## Assets y contenido
- Solo geometría y texturas propias o con licencia compatible (CC0 o cedidas). Las fotos de terceros son
  referencia interna: no se publican ni se proyectan como textura. Sin logos ni marcajes sin permiso.
- **Solo airsoft**: nada de armas de fuego reales, munición real ni piezas reguladas.
