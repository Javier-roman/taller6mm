# Fase 1 · Propuestas de La Armería (prototipos A y B)

- **Fechas**: 2026-11-01 (prototipos) y 2026-11-03 (correcciones de las revisiones) · **Autor**: Claude Code, a
  petición de Javi · **Estado**: para decidir. **Decide Javi.**
- **Ramas** (no se fusionan): [`spike/armeria-a-3d`](https://github.com/Javier-roman/taller6mm/tree/spike/armeria-a-3d)
  y [`spike/armeria-b-25d`](https://github.com/Javier-roman/taller6mm/tree/spike/armeria-b-25d), que parte de A y
  contiene los dos.
- **Base**: docs/02 §3 (La Armería) y §3.5 (enfoque técnico), la referencia principal ref-08 y la dirección del
  01-11-2026: tres estanterías (izquierda, centro y derecha) con zonas clicables que llevan a cada función.

## Resumen
- Dos prototipos completos y navegables de la misma sala: **A**, 3D en tiempo real con React Three Fiber, y **B**,
  2,5D re-iluminable con pases horneados y un compositor WebGL2 propio. Comparten interfaz, datos de ejemplo,
  director de luces y póster, así que la diferencia que ves es solo la técnica de render.
- Pasaron por `critico-diseno` y `auditor-rendimiento`. Corregí lo bloqueante y lo importante que era barato:
  réplicas que eran cajas, banco poco protagonista, ladrillo rojo, movimiento reducido en móvil, letra de los pases
  de B, sombras recalculadas en cada fotograma, caída al póster que no saltaba… Lo que queda está listado abajo.
- Los dos cumplen los presupuestos de peso de docs/02 §3.6 y pasan **axe sin fallos** en 12 casos. En escritorio
  van a **60 FPS**.
- **A** es la experiencia que pediste: la cámara entra en la zona y el cuerpo del compactus rueda. A cambio pesa
  **347 KB gz de JS** y en el móvil simulado es lento al arrancar (4,7 s enchufado; 18 s con batería).
- **B** pesa **83 KB gz de JS + 534 KB de imágenes**, arranca en **1–2,4 s** y en reposo se ve casi igual; pero su
  cámara es fija, «abrir» es un zoom que se pixela y en móvil se ve blando.
- Mi recomendación, no vinculante: **híbrido por niveles** (póster → B → A), como ya contemplaba docs/02 §3.5: A en
  escritorio y B, rehecho para móvil, en móvil. Antes del ADR, medir los dos en un Android medio real. **Decides tú.**

## Qué tienen en común
- **La sala** (ref-08): pared de ladrillo arena, suelo de hormigón con raíles que vienen hacia ti, tres filas de
  tubos LED y tres cuerpos de compactus verde oliva casi negro con su número (01–03) y su rótulo de cabecera:
  **CATÁLOGO**, **TALLER6MM** (la marca, grabada en Cinzel) y **MERCADO**.
- **Los ocho módulos acordados**, cada uno con su rótulo a plantilla y su dato marcado **DEMO**:

  | Estantería | Módulo (rótulo) | Lleva a | Dato de ejemplo | Llega en |
  |---|---|---|---|---|
  | Izquierda · Catálogo | Armero de réplicas (Armero): 12 ranuras numeradas, como en ref-08 | `/replicas` | 24 réplicas | Fase 2 |
  | | Almacén de accesorios (Accesorios): maletines rígidos y cajas | `/accesorios` | 186 accesorios · 8 tiendas | Fase 2 |
  | Centro · Taller | Vitrina de la comunidad (Vitrina): tira LED cálida y tres pedestales | `/comunidad` | Top de la semana | Fase 5 |
  | | **Banco de trabajo**, delante y protagonista: tapete con regla en mm, réplica y flexo | `/banco` | Monta tu réplica | Fase 3 |
  | Derecha · Mercado | Tablón de mercado (Tablón): corcho y monitor con bajadas fechadas | `/mercado` | 3 bajadas hoy | Fase 4 |
  | | Mostrador de tiendas (Tiendas) | `/tiendas` | 8 tiendas · hace 2 h | Fase 4 |
  | | Biblioteca de manuales (Manuales) | `/guias` | 12 guías | Fase 2 |
  | | Taquilla personal (Taquilla), con «INVITADO» a plantilla | `/taquilla` | Tus builds y alertas | Fase 5 |

- **Interacción** (docs/02 §3.2–3.3):
  - Intro de primera visita: negro, los tubos arrancan fila a fila con un parpadeo y la marca se «estampa». Dura
    2,9 s, se salta con Esc, clic o «Saltar intro» y se recuerda. Si la escena tarda más de 1,5 s en llegar, no
    hay intro: ya has visto la sala en el póster y no se apaga para volver a encenderse.
  - Al pasar por un módulo, su fila de tubos se enciende con parpadeo de arranque, el resto baja, el rótulo se
    ilumina y aparece una etiqueta con el dato **bajo** el rótulo. La **linterna-cursor** sigue al ratón.
  - Clic o Enter: panel de la zona con su ruta y la fase en que llega. En A, la cámara entra y el cuerpo rueda
    sobre sus raíles; en B, zoom sobre la imagen. Cabecera con el lema de la marca y la acción principal
    **«Monta tu réplica»**.
  - Teclado: un solo tabulador para la navegación; ←/→ (e Inicio/Fin) recorren los módulos, Enter abre y Esc vuelve.
  - Móvil: pasillo horizontal con scroll-snap que empieza en el banco; al deslizar, la cámara viaja por la sala y el
    módulo centrado se ilumina; tocar abre una hoja que ocupa como mucho el 45 % de la pantalla.
- **Accesibilidad**: navegación HTML siempre presente (la escena es una mejora progresiva). **axe (WCAG 2.2 AA)
  sin fallos** en A y B, en escritorio y móvil, con la escena, con una zona abierta y con el póster. Un test
  garantiza **≤ 3 destellos por segundo** (WCAG 2.3.1).
- **Movimiento reducido**: sin intro, sin parpadeos, sin deriva ni zooms; en móvil la cámara corta de zona a zona
  en vez de seguir al dedo. La escena queda **estática y re-iluminable**. docs/02 §3.4 dice «póster» y §4.4 dice
  «sin cámara ni parallax»: los prototipos siguen §4.4 (ver decisiones).
- **Póster**: render de la propia escena, WebP de **78 KB** (1920 px) y 29 KB (960 px), con el mismo recorte que
  la escena en escritorio. Es el primer pintado (LCP) y la «vista ligera»; sus zonas son enlaces colocados con CSS
  generado (la CSP no admite estilos en línea).
- **Luz**: la variante cálida («Taller abierto») se probó y se descartó: calentar toda la sala borraba el contraste
  entre los tubos fríos y el flexo cálido, que es el concepto. Queda **«Más luz»**, misma temperatura y más nivel,
  como ayuda de legibilidad.
- **Solo geometría propia y texturas procedurales**: nada se descarga y no hay licencias de terceros. Las réplicas
  son un perfil genérico propio extruido (culata, empuñadura, cargador curvo y óptica) que no copia ningún modelo.

## Prototipo A · 3D en tiempo real (React Three Fiber)
Cámara con deriva suave al mover el ratón; al abrir una estantería la cámara entra y **el cuerpo del compactus
rueda hacia delante**; al abrir el banco se ve el tapete desde arriba. Cuatro luces con sombra (tres filas de tubos
y el flexo), luz de vitrina, foco de acento, linterna, reflejos de entorno, bloom, AgX, viñeta y grano. Pinta **bajo
demanda**: en reposo no gasta GPU. El chunk 3D se pide después del primer pintado y solo si hay WebGL2.

| Escritorio (1440 × 900) | Móvil (390 × 844) |
|---|---|
| ![A en reposo](capturas/fase-1-propuestas/a-escritorio-reposo.jpg) | ![A móvil, banco](capturas/fase-1-propuestas/a-movil-reposo.jpg) |
| ![A con la linterna sobre el armero](capturas/fase-1-propuestas/a-escritorio-linterna.jpg) | ![A móvil, armero](capturas/fase-1-propuestas/a-movil-armero.jpg) |
| ![A con el armero abierto: el cuerpo rueda](capturas/fase-1-propuestas/a-escritorio-armero-abierto.jpg) | ![A móvil, tablón abierto](capturas/fase-1-propuestas/a-movil-tablon-abierto.jpg) |
| ![A con el banco abierto](capturas/fase-1-propuestas/a-escritorio-banco-abierto.jpg) | ![A móvil con movimiento reducido](capturas/fase-1-propuestas/a-movil-reducido.jpg) |
| ![A a mitad de la intro](capturas/fase-1-propuestas/a-escritorio-intro.jpg) | ![Póster en móvil](capturas/fase-1-propuestas/a-movil-poster.jpg) |
| ![A con «Más luz»](capturas/fase-1-propuestas/a-escritorio-mas-luz.jpg) | |
| ![A con movimiento reducido](capturas/fase-1-propuestas/a-escritorio-reducido.jpg) | |
| ![A en tableta (1024 × 768)](capturas/fase-1-propuestas/a-tableta-1024.jpg) | |
| ![Póster en escritorio](capturas/fase-1-propuestas/a-escritorio-poster.jpg) | |

## Prototipo B · 2,5D re-iluminable (pases horneados + WebGL2)
La misma sala se hornea desde el encuadre fijo del póster en **pases de luz sumables** (ambiente, tres filas de
tubos, luces cálidas y rótulos) más **albedo, normales y profundidad**: 9 WebP de 1920 × 1080 (534 KB). Un shader
de unas 150 líneas, sin three.js, suma los pases con el nivel que decide el director (el mismo de A), vuelve a
iluminar la zona activa, aplica la linterna sobre normales y profundidad, mueve la imagen con un parallax leve y
termina con AgX, viñeta y grano. Abrir una zona es un **zoom 2D** (apertura simulada).

> **Blender no está instalado** (pide permisos de administrador), así que los pases salen del rasterizador de
> three.js y no de Cycles: sin iluminación global ni oclusión ambiental. Con Cycles, B ganaría la calidad
> fotográfica que es su gran baza en docs/02 §3.5. `critico-diseno` apunta que existe una versión portátil de
> Blender en ZIP que no necesita instalador; usarla también requiere tu permiso.

| Escritorio (1440 × 900) | Móvil (390 × 844) |
|---|---|
| ![B en reposo](capturas/fase-1-propuestas/b-escritorio-reposo.jpg) | ![B móvil, banco](capturas/fase-1-propuestas/b-movil-reposo.jpg) |
| ![B con la linterna sobre el armero](capturas/fase-1-propuestas/b-escritorio-linterna.jpg) | ![B móvil, armero](capturas/fase-1-propuestas/b-movil-armero.jpg) |
| ![B con el armero abierto: zoom](capturas/fase-1-propuestas/b-escritorio-armero-abierto.jpg) | ![B móvil, tablón abierto](capturas/fase-1-propuestas/b-movil-tablon-abierto.jpg) |
| ![B con el banco abierto](capturas/fase-1-propuestas/b-escritorio-banco-abierto.jpg) | ![B móvil con movimiento reducido](capturas/fase-1-propuestas/b-movil-reducido.jpg) |
| ![B a mitad de la intro](capturas/fase-1-propuestas/b-escritorio-intro.jpg) | ![Póster en móvil](capturas/fase-1-propuestas/b-movil-poster.jpg) |
| ![B con «Más luz»](capturas/fase-1-propuestas/b-escritorio-mas-luz.jpg) | |
| ![B con movimiento reducido](capturas/fase-1-propuestas/b-escritorio-reducido.jpg) | |
| ![B en tableta (1024 × 768)](capturas/fase-1-propuestas/b-tableta-1024.jpg) | |
| ![Póster en escritorio](capturas/fase-1-propuestas/b-escritorio-poster.jpg) | |

## Medidas
Equipo de Javi: Windows 11, **Intel Arc integrada** (ANGLE · Direct3D 11), Edge 156 lanzado por Playwright, build
de producción servida en workerd en local y sin limitar la red. Escritorio: 1440 × 900, DPR 1, moviendo el ratón
8 s por la sala. Móvil simulado: 390 × 844, DPR 3, táctil y **CPU ×4 más lenta**, recorriendo el carrusel 8 s; la
GPU sigue siendo la del portátil. Hay dos tandas: la del **01-11, con el portátil enchufado** (antes de las
correcciones), y la del **03-11, con batería** (63 %, descargando), que limita la CPU y hunde el móvil simulado.
Las cifras de móvil son **orientativas**: falta un móvil medio real. Datos en bruto:
[medidas-a.json](capturas/fase-1-propuestas/medidas-a.json), [medidas-b.json](capturas/fase-1-propuestas/medidas-b.json)
y [axe.json](capturas/fase-1-propuestas/axe.json).

| | A · 3D | B · 2,5D | Presupuesto (docs/02 §3.6) |
|---|---|---|---|
| JS inicial (islas, gz) | 79 KB | 77 KB | ≤ 120 KB ✔ |
| Chunk 3D / compositor (gz) | **275 KB** (unos 1012 KB sin comprimir) | **5,7 KB** | ≤ 350 KB ✔ |
| JS total de la página (gz) | 347 KB | 83 KB | — |
| Assets de la escena | póster 78 KB (escena procedural) | 534 KB de pases (161 KB sin los de datos, en táctil) + póster 78 KB | ≤ 4 MB escritorio, ≤ 2 MB móvil ✔ |
| Fuentes (woff2, comunes) | 159 KB | 159 KB | — |
| FPS escritorio, p95 | 60 (17 ms) | 60 (17 ms) | 60 ✔ |
| FPS móvil simulado, enchufado (01-11) | 59 (p95 17 ms) | 60 (p95 17 ms) | ≥ 30 ✔ |
| FPS móvil simulado, batería (03-11) | **10** (p95 300 ms) | **19–20** (p95 117–167 ms) | ≥ 30 ✘ (orientativo) |
| Escena lista, escritorio | 2,7 s | 1,0 s | — |
| Escena lista, móvil enchufado / batería | 4,7 s / **18,4 s** | 1,9 s / 2,1–2,4 s | interactiva ≤ 4 s |
| Resolución de render en móvil (tras las correcciones) | DPR 1,25, sin sombras | DPR 1,5 (imagen de 1920 px) | — |
| LCP con el póster | sin medir con red 4G | sin medir con red 4G | ≤ 2,5 s p75 |

«Escena lista» es el tiempo desde la navegación hasta el primer fotograma de la escena, sin red lenta. El póster se
pinta antes. `auditor-rendimiento` repitió las medidas de la build del 01-11 con batería y salieron **peor** que las
del 03-11 (A: 4,7 FPS y 33 s; B: 13,4 FPS y 5,5 s): la caída se debe a la alimentación, no a los cambios. Con
batería las cifras ni siquiera son comparables entre sí, porque Windows y Edge cambian la prioridad del proceso.

Lo que midió además el auditor (build del 01-11, instrumentando WebGL):

| | A · 3D | B · 2,5D |
|---|---|---|
| Draw calls por fotograma | 866 en calidad alta (≈ 570 de 4 mapas de sombra); 117–155 en baja | 1 |
| Shaders | 15 programas y 1,2 s de compilación síncrona al arrancar | 1 programa, 33 ms |
| Bloqueo del hilo principal al arrancar (escritorio) | 1,5 s | 53–73 ms |
| Memoria de GPU | 160 MiB escritorio (DPR 1); ≈ 50 MiB móvil | 95 MiB (63 sin los pases de datos) |

Después de esas medidas apliqué sus arreglos baratos (sombras bajo demanda, MSAA ×2, DPR móvil 1,25, chunk en
paralelo a las fuentes, B «lista» solo con los pases, sin pases de datos en táctil…). **Falta volver a medir**: con
el portátil enchufado, N ≥ 5 por caso y, sobre todo, en un Android medio real.

## Revisión de diseño (critico-diseno)
Su conclusión: A y B son la misma sala; lo que los separa del «wow» es común: el contenido, la jerarquía de la luz y
la paleta. A gana en cuanto algo se mueve o se amplía; B solo puede jugar con la luz.

**Corregido** (en las dos ramas):
- Réplicas de verdad en vez de cajas: perfil propio extruido con bisel; armero de 12 ranuras numeradas.
- El banco como protagonista: adelantado, el flexo es la mancha más brillante, cámara más alta con picado, lema y
  botón latón «Monta tu réplica».
- Paleta y tipografía: ladrillo arena (el rojo chocaba con el oliva), marca en Cinzel, rótulos que no se queman.
- Linterna visible; etiqueta bajo el rótulo, sin tapar la cabecera; velo de cabecera y barra más densos.
- El póster y la escena con el mismo recorte (el fundido ya no salta); sin «encendido, apagón, encendido».
- Movimiento reducido en móvil (bloqueante); móvil empieza en el banco; hoja inferior al 45 %; banco abierto visto
  desde arriba.
- B: pases re-horneados con la letra correcta (bloqueante) y sin zoom en móvil.
- Bajadas del tablón con «comprobado hace X» y en verde de estado; datos con espacios de no separación.
- Capturas nuevas: estantería abierta, tableta a 1024 px y «Más luz».

**Pendiente** (anotado para la versión final):
- B en móvil sigue blando y recortado: necesitaría horneados verticales por zona (1080 × 1920) y pases a 3840 px.
- Coreografía con peso (curva «pesada» de 700 ms y asentamiento) y vídeo de 3–5 s de cada prototipo.
- Detalle de maletines y cajas, oclusión ambiental horneada en móvil, rótulos 3D más legibles a 1440 px, contador
  de posición en el carrusel y la vista ligera móvil sincronizada con el carrusel.

## Revisión de rendimiento (auditor-rendimiento)
Su conclusión: B es mucho más barato justo en lo que castiga a un móvil (CPU al arrancar, JS, draw calls y shaders) y
aguanta mejor con batería; sus puntos débiles son la memoria de GPU y la nitidez al ampliar. A cumple en escritorio
a un coste alto y en móvil incumple «interactiva en ≤ 4 s» incluso enchufado. Desde el rendimiento: **B en móvil**;
en escritorio caben los dos, y A solo con sus mejoras aplicadas; el híbrido por niveles encaja bien porque los pases
de B salen de la misma escena de A.

**Corregido** (en las dos ramas):
- A: mapas de sombra solo al empezar y mientras rueda un cuerpo (las luces no se mueven): ≈ −65 % de draw calls.
- A: MSAA ×2 (de 30 a 100 MiB menos de GPU), DPR móvil de vuelta a 1,25 y el chunk 3D en paralelo a las fuentes.
- B: «lista» solo cuando los pases están subidos (antes el póster se fundía a una sala negra); sin pases de datos en
  pantallas táctiles (−382 kB y −32 MiB de GPU); DPR móvil 1,5; uniformes cacheados.
- Los dos: caída al póster con menos de 30 FPS durante 2,5 s, contando los fotogramas largos (antes no saltaba ni a
  4,7 FPS, y B no la tenía); dejan de pintar 400 ms después de que el puntero se pare; el carrusel ya no fuerza un
  layout en cada scroll; rótulos a 512 × 128.

**Pendiente**:
- A: compilación asíncrona de shaders (`compileAsync`, de 0,8 a 1,2 s menos de bloqueo), texturas horneadas en la
  build en vez de pintadas en el hilo principal, lightmaps con dos luces dinámicas (flexo y linterna), geometría
  fusionada e instanciada (menos de 60 draw calls), degradación por pasos antes de caer al póster, detect-gpu y un
  nivel medio.
- B: subir un pase por fotograma, pases más baratos (profundidad R8, normales RG8, luz como irradiancia: de 9 a 4
  texturas) y recortes por estantería a 2× para abrir zonas sin pixelar.
- KTX2 y Meshopt chocan con la CSP actual (necesitan WASM y workers `blob:`): ADR y `revisor-seguridad` antes.
- Medición: Lighthouse de estas páginas con GPU (`pnpm lh` desactiva la GPU), Element Timing en el póster (Chromium
  no lo toma como LCP por cubrir toda la pantalla), INP, red 4G y N ≥ 5 con la alimentación anotada.

## Limitaciones de esta entrega
- **Sin Blender** (ver B). A tampoco usa lightmaps, que docs/02 §3.5 prevé para el A final: sus cifras son con
  todas las luces dinámicas, el peor caso.
- **Sin móvil real ni red 4G**: el móvil simulado solo limita la CPU y depende de si el portátil está enchufado.
- **Sin sonido** (opcional y apagado por defecto en docs/02) ni View Transitions (aún no hay secciones).
- **Sin detect-gpu**: la calidad inicial se decide por tipo de puntero y la caída al póster, por FPS medidos.
- El navegador del MCP de Playwright iba a ~1,5 FPS con la pantalla del equipo apagada; las medidas y capturas se
  hicieron con un Edge lanzado por Playwright (59–60 FPS de base).

## Recomendación (no vinculante)
Las dos revisiones coinciden en el diagnóstico y discrepan en el móvil: `critico-diseno` prefiere A en todo (es la
sala 3D que pediste y el B de hoy se ve peor en móvil); `auditor-rendimiento`, B en móvil (arranca de 2 a 4 veces
antes y gasta una fracción de CPU). Mi propuesta junta las dos:

1. **Híbrido por niveles**: póster (primer pintado y equipos sin WebGL2) → **B** (móvil y GPU modestas) → **A**
   (escritorio con GPU capaz). Es lo que ya admitía docs/02 §3.5, y mantener las dos técnicas cuesta menos de lo que
   parece: comparten interfaz, director de luces, zonas y escena, y los pases de B salen de A con un script.
2. **B rehecho para móvil** antes de darlo por bueno: horneados verticales por zona a 2×, solo pases de luz en táctil
   y, si lo autorizas, Cycles. Si aun así no convence, el nivel móvil sería A en calidad baja con sus mejoras.
3. **Medir antes del ADR-0002** en un Android medio real (y en el portátil enchufado, N ≥ 5): es lo único que valida
   el presupuesto de móvil.

Si prefieres una sola técnica: **A** si pesa más el «wow» (cámara que entra, compactus que rueda) y aceptas su coste
en móvil; **B** si pesan más la velocidad y la robustez, a cambio de una cámara fija.

## Decisiones que necesito de ti
1. **A, B o híbrido** (docs/02 §3.5 admite B en móvil y A en escritorio). Con tu elección escribo el ADR-0002.
2. **Luz**: «Cierre de taller» (penumbra) por defecto, con el interruptor «Más luz» a la vista o sin él.
3. **Movimiento reducido**: escena estática re-iluminable (lo que hacen los prototipos) o póster (lo que dice hoy
   docs/02 §3.4). Recomiendo la escena estática y corregir §3.4 para que no contradiga §4.4.
4. **Blender**: si eliges B o el híbrido, ¿lo instalas tú (o usamos la versión portátil) para hornear con Cycles?
5. **Prueba en un móvil medio real** antes del ADR: ¿tienes un Android de gama media a mano?

## Cómo verlo en tu equipo
```powershell
cd C:\dev\bancada
git switch spike/armeria-b-25d      # contiene A y B
pnpm install --frozen-lockfile
pnpm dev                            # http://127.0.0.1:4321/prototipos/armeria-a y /prototipos/armeria-b
```
Parámetros útiles: `?intro=1` (ver la intro otra vez), `?luz=mas-luz`, `?vista=ligera` (póster), `?calidad=baja`
y `?medir`. Scripts en `apps/web/scripts/prototipos/`: `capturas.mjs`, `medir.mjs`, `axe.mjs`, `poster.mjs`,
`hornear-b.mjs` y `zonas-poster.mjs`.
