# ADR-0002 — Enfoque técnico del inicio (La Armería): póster, 2,5D y 3D por niveles

- **Estado**: Propuesta (OK visual de Javi el 11-11-2026 con una condición: sin haces de luz visibles; falta mostrarle el resultado y medir)
- **Fecha**: 2026-11-10
- **Decisores**: Javi (+ Claude Code)

## Contexto
El inicio es una sala en penumbra con tres cuerpos de compactus y ocho módulos clicables (docs/02 §3). Se construyeron dos prototipos (PR #10; segunda ronda en la rama `spike/armeria-f1`): **A**, 3D en tiempo real con React Three Fiber, y **B**, 2,5D con pases de luz horneados y un compositor WebGL2 propio. Datos medidos (informe `docs/informes/fase-1-propuestas.md`, 01 y 03-11-2026, portátil Windows 11 con GPU Intel Arc integrada):

| | A | B |
|---|---|---|
| JS total de la página (gz) | 347 KB | 83 KB |
| FPS escritorio, p95 | 60 | 60 |
| FPS móvil simulado enchufado | 59 | 60 |
| FPS móvil simulado con batería | **10** | **19–20** |
| Assets | póster 78 KB | 534 KB de pases (1920 px) + póster |

Decisiones de Javi (05-11-2026): híbrido (póster de base, B en móvil y A en escritorio), penumbra por defecto con «Más luz» visible, movimiento reducido con escena estática re-iluminable, y luz de B horneada con Cycles (Blender portátil). Las siluetas de réplicas son **provisionales** hasta tener modelos reales (frente de fidelidad).

## Decisión
1. **Tres niveles**: póster (primer pintado, vista ligera y SEO), luego **B** en móvil y **A** en escritorio con WebGL2. Cada nivel cae al anterior si falla o va lento.
2. **Penumbra por defecto** y botón **«Más luz»** siempre visible, misma temperatura de luz y más nivel. **Luz indirecta, sin haces visibles** (Javi, 11-11-2026): los conos de luz y la bruma volumétrica se quitaron porque daban aspecto de videojuego indie; la sala simula la realidad, así que los tubos iluminan paredes, suelo y muebles y el aire no se ve.
3. **Movimiento reducido** (`prefers-reduced-motion`): escena **estática re-iluminable** (linterna y «Más luz» siguen funcionando), sin viaje de cámara ni parallax. Esto **corrige docs/02 §3.4**, que decía «póster estático».
4. **Luz horneada con Cycles** (Blender portátil, `scripts/prototipos/hornear-b-cycles.*`) para B y para el póster, que sale de la composición de B para que póster, vista ligera y B sean la misma sala. Los pases de luz van a 2560 × 1440 para que el móvil recortado se vea nítido.
5. **Mismos datos vivos y mismas rutas** en los tres niveles; todo valor de diseño sale de los tokens de `packages/ui`.
6. **Seguridad**: la CSP actual vale para estos prototipos (sin WASM ni workers `blob:`). Si el 3D final usa texturas KTX2 y geometría Meshopt, se amplía la CSP **solo en `/`** (WASM y workers `blob:`), con revisión de `revisor-seguridad`.

## Alternativas consideradas
| Opción | Pros | Contras | Por qué no |
|---|---|---|---|
| Solo A (3D en todos los equipos) | La experiencia buscada, cámara que entra | 347 KB de JS y 10 FPS en móvil con batería | No cumple ≥ 30 FPS en móvil |
| Solo B (2,5D en todos) | Ligero y rápido, buena luz con Cycles | Sin cámara libre ni cuerpo que rueda en escritorio | Pierde el «wow» donde sobra potencia |
| Póster estático sin escena | Mínimo peso | No re-ilumina ni responde | Con movimiento reducido se pierde la penumbra viva |
| **Híbrido por niveles (elegida)** | Cada equipo recibe lo que aguanta; el wow no rompe la función | Tres caminos que mantener y coherentes entre sí | — |

## Consecuencias
- **Positivas**: primer pintado rápido, móvil ligero, escritorio con 3D completo, accesible con movimiento reducido.
- **Negativas**: mantener la misma sala en tres formas (A, B, póster) y volver a hornear B cuando cambie la escena (unos 22 min en CPU).
- **Trabajo**: lightmaps de A con Blender (pendientes), horneado vertical propio para móvil, medición en un móvil real (iPhone 15 Pro Max de Javi; Android de gama media pendiente).

## Validación
- Presupuestos de docs/02 §3.6 y docs/08: JS inicial ≤ 120 KB gz, assets ≤ 4 MB escritorio y ≤ 2 MB móvil, ≥ 30 FPS en móvil de gama media, LCP ≤ 2,5 s p75.
- axe sin fallos, teclado completo, capturas a 390 y 1440 px revisadas por `critico-diseno` y OK de Javi en cada hito.

## Disparadores de revisión
- Un móvil de gama media real no llega a 30 FPS con B.
- Los modelos reales de réplicas cambian el presupuesto de la escena.
- WebGPU está disponible en el 90 % de los equipos objetivo y simplifica A.
