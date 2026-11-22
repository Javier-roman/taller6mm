# Plan de construcción de la Fase 1 (La Armería real)

11-11-2026 · **Borrador para el OK de Javi.** Nada de esto está aprobado todavía.

## 1. Punto de partida

- **ADR-0002 aceptado** (`docs/adr/0002-enfoque-tecnico-del-inicio.md`). Define:
  - Tres niveles de la escena, cada uno cae al anterior: póster → B (móvil) → A (escritorio).
  - Penumbra por defecto, con el botón «Más luz».
  - Con movimiento reducido, la escena es estática y se puede re-iluminar.
  - Luz indirecta, sin haces de luz visibles.
- **Prioridad: escritorio.** El pulido del móvil queda aplazado.
- **Prototipos validados** en la rama `spike/armeria-f1`. La rama **no se fusiona**; sirve solo de fuente de código.

| Nivel | Peso (gzip) | Imágenes | Rendimiento medido |
|---|---|---|---|
| A (escritorio, three.js) | 349 KB de JS | — | 60 FPS en escritorio |
| B (móvil) | unos 88 KB de JS | unos 830 KB | 60 FPS en escritorio |

- Medición: portátil con Intel Arc integrada, enchufado, 11-11-2026. **Pendiente: medición en móvil real.**
- Las siluetas de las réplicas son **provisionales**.
- Los datos son **DEMO** (`is_demo`).

## 2. Rebanadas

Cada rebanada se entrega en PR pequeño y pasa por:

- Capturas a 390 px y 1440 px.
- Revisión de `critico-diseno` y de `auditor-rendimiento`.
- `pnpm verify` en verde.
- OK de Javi.

| Rebanada | Contenido | Notas |
|---|---|---|
| **S1** · Escena base | Promover el código del spike a `apps/web`. Selector de nivel con caída automática (sin WebGL, FPS bajos o `webglcontextlost` → nivel anterior). Póster como `<img>` en el HTML inicial, con la isla 3D hidratada en `client:idle`. Movimiento reducido. «Más luz». Colores fijos de `Sala.tsx` pasados a tokens de `packages/ui`. | Validar la CSP aquí. WASM y KTX2 solo en `/`. Revisión de `revisor-seguridad`. Preferencias («Más luz», intro vista) en `localStorage`, con alternativa si no está disponible. |
| **S2** · Módulos | Ocho módulos clicables con datos de demo y su hoja de contenido. | Árbol DOM accesible y teclado desde el principio, no al final. |
| **S3** · Interacción | Intro de primera visita. Linterna con una abstracción común para puntero y táctil. Apertura del compactus. | Siempre con alternativa ligera. |
| **S4** · Calidad visual | axe (WCAG 2.2 AA). Regresión visual con capturas en CI. Lightmaps de A con Blender. | Regresión: render por software determinista, tolerancia y animaciones paradas en un fotograma fijo. Los lightmaps son **aplazables** si no mejoran la imagen. |
| **S5** · Sistema | Componentes base completos en `/sistema`. | — |

## 3. Riesgos y mitigación

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | Regresión visual poco estable por la GPU | Render por software determinista, tolerancia y fotograma fijo (S4). |
| 2 | La CSP bloquea WASM o KTX2 | Validar en S1. |
| 3 | Peso de JS | Cualquier dependencia de cliente de más de 30 KB gz necesita el OK de Javi. Afecta a three, React Three Fiber, drei, postprocessing y GSAP. Se cargan con `import()` solo en el nivel A. El nivel B no importa three.js. |
| 4 | LCP y CLS por activos pesados | Los pases horneados (unos 1,2 MB con todas las variantes) irán a R2 con `Cache-Control` inmutable, o a `public/`. **Decisión pendiente.** |
| 5 | Pérdida de contexto WebGL o FPS bajos | Medición inicial y caída automática al nivel anterior (S1). |

## 4. Decisiones que necesitan a Javi

1. Aprobar las dependencias de cliente de la sección 3, riesgo 3.
2. Dónde viven los pases horneados: en el repo o en R2. **Pendiente.**
3. Si el código del spike se promueve tal cual o se reescribe limpio. **Pendiente.**
4. Si los lightmaps de A son prioritarios (S4). **Pendiente.**

## 5. Fuera de alcance por ahora

- Pulido del móvil: encuadre del Banco y tubo del armero en el nivel B móvil. Medición en móvil real.
- Telemetría del selector de nivel. Si se hace, será anónima y conforme al RGPD.

## 6. Decisiones de Javi del 22-11-2026 (actualizan este plan)

- **Se reescribe limpio** en `apps/web` a partir del prototipo (`spike/armeria-f1` sigue sin fusionarse) y se **aprueban las
  dependencias de cliente** de la sección 3 (three.js y R3F; el nivel B no importa three.js).
- **Los pases horneados y el póster viven en R2**, servidos por un binding de solo lectura del Worker de la web (`VISTAS`) en
  `/assets/armeria/<hash>/…` con `Cache-Control` inmutable, sin bucket público. En local, desde `public/assets/armeria/`
  (`pnpm --filter @taller6mm/web vistas:local`). Los binarios están en `assets-src/vistas/armeria/` (fuera de git).
- **Solo escritorio por ahora.** El móvil se aparca (sin recortes por módulo, sin carrusel, sin medir en móvil). Niveles:
  póster → B → A, con caída automática; B es el respaldo de A en escritorio.
- **Sin siluetas de réplicas en la escena.** Javi: «quedan terriblemente mal». Hasta que haya réplicas reales (otro trabajo en cola)
  la sala se hornea y se pinta con baldas, ranuras, ganchos y peanas **vacías pero resueltas**. Los huecos son **sockets**
  (`src/components/armeria/sockets.ts`): 12 ranuras del armero, 3 peanas de la vitrina y el tapete del banco, cada uno con su
  caja en metros y `replicaId: null`. De ahí salen el rectángulo del hueco sobre el póster y el nivel B (CSS generado) y un
  marcador `socket.<id>` (convención de docs/05) en la escena 3D. Colocar una réplica real = poner su `replicaId` y pintar su imagen dentro de ese
  rectángulo, sin volver a hornear.
- **El póster sale de la sala sin siluetas**, compuesto con el mismo compositor que el nivel B (`nivel-b/compositor.ts`), y
  «Más luz» tiene su propio póster horneado (`poster-mas-luz-*.webp`), no un filtro.

### Orden real de los sub-pasos (cambia respecto a la sección 2 por lo anterior)
1. **S1.0** (PR aparte, #65): binding R2, ruta del Worker, validador de Previews y `/estado`.
2. **S1.1** esqueleto y póster: incluye la sala 3D sin siluetas, el horno (three.js → glTF → Blender/Cycles), el compositor del
   póster y los sockets, porque el póster depende de ellos. Isla `client:idle` con póster y navegación HTML.
3. **S1.2** nivel B (2,5D) sobre ese compositor; **S1.3** nivel A (3D) cargado con `import()`; **S1.4** selector con caída
   automática, «Más luz» y movimiento reducido; **S1.5** CSP solo en `/` para WASM y KTX2.
