# 02 · Experiencia y diseño

## 1. Concepto: "herencia de armero, precisión táctica"
Clásico y moderno a la vez:
- **Clásico**: madera de nogal, latón, grabados finos, cuero, rótulos pintados a plantilla, la luz cálida de un flexo sobre el banco.
- **Moderno**: aluminio anodizado, tipografía técnica, datos precisos, HUD discreto, luz fría de tubo LED.

Sensación objetivo: entras a oscuras en una armería premium, las luces se encienden y todo está en su sitio y es real. Calma, precisión y deseo.

No es un videojuego: es un taller de verdad, en digital. De los videojuegos tomamos la **claridad de interacción**, no su estética ni sus "estadísticas".

## 2. Referencias
Detalle en `docs/referencias/LEEME.md`. En resumen tomamos:
- los nodos "+" de ranura con líneas guía (ref-01);
- la vista despiece (ref-02);
- las tarjetas de equipamiento (ref-03);
- las etiquetas con línea a cada pieza y el panel de datos reales (ref-04);
- el panel perforado (ref-05) y el modo inspección (ref-06);
- la atmósfera de banco de taller (ref-07);
- las estanterías móviles numeradas, los maletines, el ladrillo, los raíles del suelo y la luz cenital fría (ref-08), que es la **referencia principal del inicio**.

## 3. La Armería (inicio)
### 3.1 La escena
Una sala de armería en penumbra con **estanterías móviles tipo compactus** (como ref-08) sobre raíles en un suelo de hormigón, pared de ladrillo y tubos LED en el techo, apagados al entrar. Al fondo, el banco de trabajo con un flexo cálido.

Cada **módulo de estantería** es una zona de la web, y su contenido físico la representa:

| Módulo | Qué se ve | Lleva a | Dato vivo en el rótulo |
|---|---|---|---|
| Banco de trabajo (centro, protagonista) | Tapete, réplica a medio montar, herramientas, flexo | `/banco` | "Continúa tu build" o "Monta tu réplica" |
| Armero de réplicas | Ranuras numeradas con réplicas en vertical | `/replicas` | Nº de réplicas en catálogo |
| Almacén de accesorios | Cajas, fundas y maletines rígidos etiquetados | `/accesorios` | Nº de accesorios y de tiendas |
| Vitrina de la comunidad | Vitrina iluminada con las 3 builds top de la semana | `/comunidad` | "Top de la semana" |
| Tablón de mercado | Corcho con notas y un monitor con bajadas de precio | `/mercado` | Últimas bajadas y vueltas a stock |
| Mostrador de tiendas | Mostrador con fichas de tiendas | `/tiendas` | Nº de tiendas y frescura de sus datos |
| Biblioteca de manuales | Estante de manuales y carpetas | `/guias` | Guías y normativa |
| Taquilla personal | Taquilla metálica con tu apodo a plantilla | `/taquilla` | Tus builds, favoritos y alertas |

El contenido de cada módulo **es real**: miniaturas de builds reales, siluetas de réplicas del catálogo y contadores vivos. El inicio funciona como un panel, no como un decorado.

### 3.2 Interacción en escritorio
- **Primera visita**: pantalla negra, zumbido y parpadeo de los tubos que se encienden fila a fila, aparece la sala y el logo se "estampa" en el rótulo. Dura 3 s como máximo, se puede saltar (Esc, clic o "Saltar") y se recuerda en `localStorage`. En visitas siguientes las luces ya están encendidas.
- **Linterna-cursor**: un haz suave sigue al ratón y revela detalle. La sala está en penumbra, nunca a oscuras: el texto siempre es legible.
- **Hover sobre un módulo**: su tubo se enciende con parpadeo de arranque, el rótulo a plantilla se ilumina y aparece el dato vivo. El resto de la sala baja un poco.
- **Clic**: los módulos del compactus **se desplazan sobre sus raíles** para abrir el pasillo del elegido. La cámara avanza (unos 700 ms, GSAP) y un fundido con View Transitions lleva a la sección. Serán las transiciones nativas del navegador entre documentos (CSS `@view-transition`), no el `<ClientRouter />` de Astro, que no admite la CSP con hashes. Al volver, la cámara se restaura en ese pasillo.
- **Teclado**: ← y → recorren módulos, Enter entra y Esc vuelve. El foco visible es el propio rótulo iluminado. Hay enlace "Saltar al contenido".
- **Sonido** (opcional, apagado por defecto, interruptor persistente): zumbido de tubos, clic metálico, rodar de raíles. Sonidos CC0 o propios.

### 3.3 Móvil
- Pasillo horizontal: deslizas entre módulos (scroll-snap), el central se ilumina y tocas para entrar.
- Parallax con giroscopio solo si el usuario lo activa (iOS pide permiso). Por defecto, parallax al arrastrar.
- Calidad automática según la GPU (detect-gpu + PerformanceMonitor): menor resolución de render y sin postprocesado caro.

### 3.4 Alternativa ligera y SEO
- Sin WebGL, con `prefers-reduced-motion`, en modo ahorro de datos o con GPU débil se muestra un **póster estático** (render de la escena) con zonas HTML clicables encima. Mismas rutas y mismos datos vivos.
- La navegación real es HTML semántico (`<nav>` con enlaces) y siempre está presente. La escena 3D es una mejora progresiva.

### 3.5 Enfoque técnico (prototipos en la Fase 1)
| Opción | Cómo | Pros | Contras |
|---|---|---|---|
| A · 3D en tiempo real | R3F; geometría procedimental y texturas PBR CC0; iluminación horneada en Blender (lightmaps) y pocas luces dinámicas; postprocesado (bloom, viñeta, grano, tone mapping AgX) | Cámara libre; apertura real de los módulos | Más peso y más GPU |
| B · 2.5D re-iluminable | Render en Blender (Cycles) con un pase de luz por grupo de tubos, más mapas de normales y profundidad; un shader suma los pases y aplica la linterna sobre las normales | Calidad fotográfica con coste mínimo; ideal en móvil | Cámara limitada (parallax); apertura simulada |

Construir un prototipo mínimo de cada una (1 módulo + banco), medir FPS en móvil medio, peso y calidad percibida por Javi, y decidir con un ADR. Vale un **híbrido**: B en móvil y A en escritorio.

Assets de la escena: geometría propia o procedimental (estanterías, maletines y raíles son geometría simple) y texturas CC0 (Poly Haven, ambientCG). **Nunca** assets de videojuegos.

### 3.6 Presupuesto del inicio
- LCP ≤ 2,5 s (p75, móvil 4G) con el póster; escena interactiva en ≤ 4 s.
- JS inicial ≤ 120 KB gz sin el chunk 3D; chunk 3D ≤ 350 KB gz, cargado después del primer pintado.
- Assets de la escena ≤ 4 MB en escritorio y ≤ 2 MB en móvil (KTX2, Meshopt).
- 60 FPS en escritorio medio; ≥ 30 FPS en móvil medio, o se cae al póster.

## 4. Sistema de diseño
### 4.1 Color (tokens con nombre de acabado)
| Token | Hex | Uso |
|---|---|---|
| `--negro-pavonado` | #0B0C0E | Fondo base |
| `--carbon` | #121417 | Superficies |
| `--grafito` | #1C1F23 | Paneles elevados |
| `--acero` | #2A2F35 | Bordes y divisores |
| `--niebla` | #9AA3AD | Texto secundario |
| `--hueso` | #E8E4DC | Texto principal |
| `--laton` | #B8925A | Acento principal (premium, clásico) |
| `--laton-claro` | #D9B77E | Hover y realce del acento |
| `--fde` | #A08A6A | Acento secundario (Flat Dark Earth) |
| `--verde-ranger` | #4B5A3F | Acento terciario |
| `--naranja-senal` | #E75A31 | Interacción activa, ranura seleccionada y anillo de foco (antes #E4572E) |
| `--estado-ok` | #3FA66B | En stock / compatible |
| `--estado-aviso` | #E0A526 | Pocas unidades / con adaptador |
| `--estado-error` | #E65850 | Agotado / incompatible (antes #D2453F) |
| `--estado-desconocido` | #7F8894 | Sin datos (antes #6B7480) |

Reglas:
- Contraste mínimo AA (4,5:1 en texto normal).
- El color nunca es el único portador de significado: cada estado lleva icono y texto.
- Son valores iniciales: `critico-diseno` los valida con capturas y se ajustan en la Fase 1.
- Tres valores se corrigieron en la Fase 0 porque no llegaban a AA como texto. Se mantuvo la misma tinta en OKLCH y se subió solo la luz:
  - `--estado-error`: de 4,35:1 a 4,63:1 en la peor superficie;
  - `--estado-desconocido`: de 4,13:1 a 4,61:1;
  - `--naranja-senal`: de 4,49:1 a 4,65:1 sobre grafito.
- La fuente única es `packages/ui/src/tokens.ts`. Un test comprueba AA en cada par texto/fondo declarado (`contrast.ts`).

### 4.2 Tipografía
Todas con licencia OFL y **autoalojadas** con Fontsource; nada de cargarlas desde servidores de Google, por RGPD.
- **Grabado** (marca, nombres de zona en grande): Cinzel, capitales de inscripción que evocan el grabado de armero.
- **Rótulo** (etiquetas de zona, chips, rótulos de estantería): Big Shoulders Stencil, plantilla industrial.
- **Interfaz**: Archivo, variable con eje de anchura (condensada para datos densos, normal para lectura).
- **Datos** (medidas, precios, códigos): JetBrains Mono con cifras tabulares.

Escala modular 1,25 (12/14/16/20/25/31/39/49/61 px). Interlineado 1,5 en cuerpo y 1,1 en titulares. Subconjunto latino extendido; precarga solo Archivo y la fuente del titular del inicio. Si el resultado no convence, evaluar alternativas con la skill de diseño de interfaces.

### 4.3 Espacio, forma y profundidad
- Rejilla de 4 px; espaciados 4/8/12/16/24/32/48/64/96.
- Radios pequeños (2–4 px): industrial y preciso. Sin "pastillas" redondas salvo avatares.
- Paneles: fondo `--grafito` con ruido sutil (≤ 3 % de opacidad), borde de 1 px `--acero`, brillo interior superior de 1 px y sombras largas y suaves. En `packages/ui`:
  - el ruido (`--textura-ruido`) es grano gris de contraste completo en una capa al 3 %;
  - el brillo es el filo de 1 px (`--sombra-placa`) más una luz cenital muy suave en el tercio superior (`--brillo-placa`), como la de los tubos del techo sobre una chapa;
  - el primer ajuste, grano solo blanco al 1,5 % de media y filo al 6 %, no se percibía en pantalla.
- Luces de la sala como tokens:
  - `--luz-cenital`: fría, la de los tubos;
  - `--luz-flexo`: cálida, la del banco.

  Las usan las cabeceras y las heredará La Armería.
- Texturas permitidas, siempre muy sutiles: aluminio cepillado, Cordura y papel kraft (etiquetas).

### 4.4 Movimiento
- Duraciones: 120 ms (micro), 200 ms (componentes), 320 ms (paneles), 600–800 ms (cámara y escena).
- Curvas: "mecánica" `cubic-bezier(0.2, 0.8, 0.2, 1)` y "pesada" `cubic-bezier(0.7, 0, 0.2, 1)` (raíles, cajones).
- Movimiento con propósito: el cajón se desliza como un cajón, el maletín se abre por su cierre, la pieza "encaja" con un rebote de 2 px y un clic.
- Con `prefers-reduced-motion`: fundidos de ≤ 120 ms, sin cámara ni parallax.

### 4.5 Componentes base (en `packages/ui`)
- **Estructura**: Placa (panel), Cajón (panel lateral, hoja inferior en móvil), Maletín (modal), Pestañas, Tostada, Tooltip, Avatar y Fila desplazable (`.t6-fila-desplazable`). La Fila desplazable va en una sola fila con scroll horizontal hasta escritorio y en varias filas desde 1280 px; como menú fijo, varias filas en tablet taparían media pantalla. Sirve para menús de secciones y, en la Fase 1, para el pasillo de La Armería en móvil.
- **Acciones**: Botón (latón, acero, fantasma, peligro); deslizador tipo raíl (rango de precio con una "montura" como tirador).
- **Rotulación**: Rótulo plantilla, Chip e insignia, **Insignia de fidelidad T0–T3**, Valoración.
- **Datos**:
  - **Barra de dato**: como las de los gunsmith, pero con datos reales y su escala.
  - **Etiqueta de precio**: precio, tienda, "comprobado hace X" y estado de stock.
  - **Punto de stock**.
- **Configurador**:
  - **Nodo de ranura**: "+" con línea guía.
  - **Ficha de pieza**: miniatura, nombre, "desde X €", nº de tiendas y compatibilidad.
- **Indicador de carga** (Cargador): un cargador visto de lado, con su labio, que se llena con 5 bolas de 6 mm una a una, con la curva «pesada». Con movimiento reducido, lleno y quieto.
- **Fecha de comprobación**: toda Barra de dato de precio o stock lleva «Comprobado hace X» (`<time datetime>` en UTC) o «Sin fecha de comprobación». El tipo del componente no compila sin ella.

Una página viva, `/sistema`, muestra todos los tokens y componentes con sus estados: hover, foco, activo, deshabilitado, carga y error.

### 4.6 Iconografía e imagen
Lucide como base, más un set propio a plantilla para piezas (bocacha, óptica, culata, pistolete, cargador, raíl…). Las fotos de usuarios van siempre en marco de "placa" con su crédito.

### 4.7 Voz y tono
Español de España, cercano y experto, con vocabulario de airsoft correcto (glosario en docs/00). Hablamos de **réplicas, partidas, campos y equipos**; nunca de matar ni de violencia. Los mensajes de error ayudan. Por ejemplo: "Esta bocacha es de rosca a derechas (CW) y tu réplica es a izquierdas (CCW). Necesitas un adaptador: 3 tiendas desde 8,95 €."

## 5. Accesibilidad (WCAG 2.2 AA)
- Todo operable por teclado, incluido el configurador (con un modo lista equivalente). Foco siempre visible y orden lógico.
- Objetivos táctiles ≥ 44 × 44 px. Arrastrar siempre tiene alternativa sin arrastre (criterio 2.5.7).
- Textos alternativos útiles; el 3D va acompañado de una descripción textual del build.
- Nada parpadea más de 3 veces por segundo: el parpadeo de los tubos se diseña por debajo y desaparece con movimiento reducido.
- `lang="es"`, landmarks, encabezados jerárquicos y mensajes de estado con `aria-live`.

## 6. Responsive
Puntos de corte: 390 (móvil), 834 (tablet), 1280 y 1440 (escritorio), 1920+ (amplio). En móvil, el configurador muestra la réplica arriba, las ranuras como lista desplegable y los cajones como hojas inferiores.

## Criterios de aceptación
- [ ] `/sistema` muestra tokens y componentes con todos sus estados, validado por `critico-diseno` sin bloqueantes.
- [ ] La Armería cumple los presupuestos de §3.6, y la alternativa ligera es equivalente en navegación y datos.
- [ ] Javi aprueba la dirección de arte con capturas a 390 y 1440 px ("wow" en la primera visita).
- [ ] axe sin errores, navegación completa por teclado y movimiento reducido respetado.
