# Prompt inicial para Claude Code

**Cómo usarlo**: abre Claude Code en la carpeta del proyecto (con todo este kit dentro) y pega como primer mensaje el bloque que va entre las dos líneas `=====`.

=====
Hola. Vas a ser el equipo técnico completo (arquitectura, frontend, 3D, datos, seguridad y QA) de **Taller6mm** (antes BANCADA), un taller virtual de airsoft. El usuario elige su réplica exacta, la monta con todos los accesorios del mercado con **fidelidad 1:1**, sabe qué encaja y por qué, ve dónde comprar cada pieza (stock y precio en tiendas de España y del extranjero) y comparte sus builds con la comunidad. El inicio es una armería premium en penumbra cuyas estanterías son las secciones de la web.

Quiero un trabajo profesional: no solo la idea, también todo lo que hay detrás (pruebas, seguridad, operación, legal), con un coste de mantenimiento cercano a 0 €. Para mí es clave que las réplicas virtuales sean iguales, o casi, a las reales.

## 1. Lee antes de hacer nada
1. `CLAUDE.md` (reglas permanentes del proyecto) y `CLAUDE.local.md` (mi equipo: Windows 11, herramientas y GPU).
2. Todos los documentos de `docs/` en orden (00 → 10) y `docs/adr/`.
3. Las 8 capturas de `docs/referencias/` (míralas con Read) y su `LEEME.md`.
4. Las listas de `docs/fuentes/`: las tiendas y las marcas que he elegido yo. En la Fase 0 no se rastrea nada; se usarán a partir de la Fase 2 (marcas) y de la Fase 4 (tiendas).
5. La configuración preparada en `.claude/` (skills, subagentes, reglas por ruta, hooks) y `.mcp.json`.

No ejecutes `/init`: `CLAUDE.md` ya existe y está pensado así.

## 2. Cómo vamos a trabajar
- Esta sesión es **solo la Fase 0 · Cimientos** (`docs/10-roadmap.md`). No empieces La Armería ni el configurador.
- Antes de planificar, hazme con la herramienta de preguntas (máximo 5, cada una con una opción recomendada) **solo** lo que bloquee y no esté ya en `CLAUDE.local.md`. Por ejemplo: si tengo cuenta de Cloudflare, repositorio público o privado y si seguimos con el nombre "BANCADA".
- Luego trabaja en **modo plan**: dame el plan de la Fase 0 con rebanadas, orden, riesgos y lo que necesitas de mí. Espera mi OK.
- Lo que no bloquee, decídelo tú con criterio, déjalo escrito (ADR si tiene impacto) y sigue.
- Usa `/verify` antes de cada commit y pasa los subagentes de `.claude/agents/` al cerrar cada rebanada de su área.
- Verifica la documentación **actual** (2026) de cada herramienta antes de usarla. Si algo de mis documentos está desactualizado o es mejorable, dímelo y propón el cambio.
- Nunca manejes mis credenciales. Cuando haga falta iniciar sesión (wrangler, gh), dime el comando exacto y lo ejecuto yo.
- Explícame cada decisión importante en 2-3 líneas: tengo nivel medio de web y estudio ciberseguridad, así que la seguridad puedes contármela con detalle.

## 3. Alcance de la Fase 0
### 3.1 Prototipo de validación del stack (como máximo una sesión)
Valida `docs/adr/0001-stack.md` con un prototipo mínimo desechable:
- Astro 6 con el adaptador de Cloudflare, una isla React con React Three Fiber (un objeto iluminado con postprocesado), una consulta a D1 y un despliegue a un Worker de preview en el plan gratuito.
- Mide y anota: tamaño del Worker comprimido (límite gratuito de 3 MiB), tiempo de CPU de una ruta SSR (límite gratuito de 10 ms por invocación), tamaño del chunk 3D, soporte de Biome para `.astro`, y Better Auth con D1 y Drizzle.
- Si algo bloquea, para y propón la alternativa del ADR con los datos medidos. Si todo va bien, pasa el ADR a **Aceptada** con las cifras.

### 3.2 Monorepo y herramientas
- Estructura exacta de `CLAUDE.md` (apps/* y packages/*), pnpm workspaces + Turborepo, TypeScript estricto, Node 22+ fijado, Biome y `.editorconfig`.
- Scripts raíz: `dev`, `build`, `verify`, `e2e`, `lh`, `size` y `db:*`.
- Cada paquete compila y tiene un test de ejemplo. `packages/domain` arranca con los tipos de unidades (`Millimeters`, `Cents`, `CurrencyCode`).

### 3.3 Calidad automática
- Vitest (con el pool de Workers donde aplique), Playwright + axe, fast-check, size-limit y Lighthouse CI.
- GitHub Actions: CI completo en cada PR (docs/08 §3) y despliegue de preview por PR; producción solo manual y protegida.
- Renovate o Dependabot, gitleaks (CI y pre-commit), OSV-Scanner y Semgrep CE.

### 3.4 Seguridad base
- Middleware de cabeceras: CSP estricta con el soporte de Astro 6, HSTS y el resto de docs/08 §6.2.
- `SECURITY.md`, `/.well-known/security.txt` y `.dev.vars.example`.
- `docs/seguridad/modelo-amenazas.md` inicial (STRIDE por componente).

### 3.5 Cloudflare
- Configuración de wrangler por app con entornos `preview` y `production`.
- Recursos de preview: D1 `core`, `mercado` y `busqueda`; R2 para assets públicos y para subidas privadas; cola de ingesta.
- Página de prueba desplegada en preview.

### 3.6 Claude Code
Comprueba que funciona todo lo preparado:
- El hook guardián: prueba que bloquea `cat .dev.vars` en Bash y `Get-Content .dev.vars` en PowerShell.
- El aviso de entorno al iniciar sesión (`check-env`).
- El formateador tras editar.
- Las skills (`/skills`) y los subagentes (`/agents`).
- El MCP de Playwright: haz una captura de la página de prueba.

Corrige lo que no cuadre con la documentación actual de Claude Code.

### 3.7 Semilla del sistema de diseño
- Tokens de `docs/02` §4 en `packages/ui` (CSS variables + export TS), fuentes autoalojadas.
- Página `/sistema` con los tokens y los componentes Botón, Placa, Rótulo plantilla, Insignia de fidelidad y Barra de dato, con todos sus estados.
- Revísala con `/revisar-ui /sistema`.

### 3.8 Documentación
`README.md` (puesta en marcha en 5 pasos), `CONTRIBUTING.md` (ramas, commits, definición de terminado) y `CHANGELOG.md`.

## 4. Criterios de aceptación de la Fase 0
- [ ] En un clon limpio, `pnpm install && pnpm verify` termina en verde.
- [ ] Un PR de ejemplo con el CI completo en verde y su URL de preview funcionando (`/` y `/sistema`).
- [ ] Lighthouse móvil de `/sistema` ≥ 95 en las cuatro categorías.
- [ ] ADR-0001 aceptado (o sustituido) con las cifras del prototipo.
- [ ] Hooks, skills, subagentes y MCP verificados.
- [ ] gitleaks limpio y modelo de amenazas inicial escrito.

## 5. Al terminar
Ejecuta `/informe-fase 0`, enséñame el resumen y **detente**. No empieces la Fase 1 sin mi OK.
=====

## Para las siguientes fases (copiar y adaptar)

**Arrancar una fase**
> Lee `docs/10-roadmap.md`, el documento de la fase y `docs/informes/fase-<N-1>.md`. Empieza la **Fase N** en modo plan: rebanadas verticales, orden, riesgos y lo que necesitas de mí. Espera mi OK. Al terminar, `/informe-fase N` y detente.

**Corregir el rumbo**
> Para. Esto no cumple <qué>. Relee <documento y sección>. Propón 2 alternativas con pros y contras antes de tocar código.

**Más "wow"**
> Pasa `/revisar-ui <ruta>` y aplica las 3 mejoras de mayor impacto que proponga `critico-diseno`. Enséñame antes y después.

**Fidelidad de una réplica**
> Pasa `revisor-fidelidad` sobre <réplica>, enséñame la superposición contra las referencias y dime qué falta para subirla al siguiente nivel.

**Revisión de seguridad**
> Pasa `revisor-seguridad` sobre todo lo cambiado en esta fase y corrige los hallazgos críticos y altos.
