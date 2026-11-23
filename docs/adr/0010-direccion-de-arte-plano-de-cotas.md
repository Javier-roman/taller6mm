# ADR-0010 — Dirección de arte «Plano de cotas»

- **Estado**: Propuesta (pendiente del OK visual de Javi sobre el PR de la rebanada S5)
- **Fecha**: 2026-11-22
- **Decisores**: Javi (+ Claude Code, con el prototipo de `critico-diseno`)

## Contexto
- La dirección de arte original (docs/02 §1 y §4, Fase 0) era «herencia de armero»: pavonado y grafito, Cinzel,
  Big Shoulders Stencil, tornillos en las placas y ruido de metal. Al construir los componentes de `/sistema` (S5) se
  vio que compite con lo que hace único al producto: datos medidos, con fuente y fecha.
- Se prepararon tres prototipos estáticos a 1440 px (`docs/informes/propuestas-sistema/`): **A · Plano de cotas**,
  **B · Latón y nogal** y **C · Compactus**. Javi eligió la **A** el 22-11-2026, con tres ajustes obligatorios:
  1. recuadros y paneles del fondo con más impacto y mejor marcados (más diferencia de tono entre tinta y lámina,
     marco más definido y sombra interior sutil);
  2. bordes más marcados (trazo y borde de control con más contraste, esquinas de registro más visibles);
  3. más contraste general, **sin saturar**: nada de neón ni brillos, con el latón y la señal naranja contenidos.

## Decisión
Adoptar la dirección **A «Plano de cotas» — «Todo se mide, nada se inventa»**:
- **Color**: tinta `#080C0F` (fondo), lámina `#15212A` y lámina alta `#1F303B`, trazo `#3D525E`, borde de control
  `#8CA3AD`, cota `#9CC3D0`, texto `#EFEBE1` / `#AFBCC3`, latón `#C29A5B` / `#DDBB82` con texto `#15110B`, señal
  `#F27346`, papel `#D7D4CC` con tinta `#1B2226` (para renders y planos) y kraft `#C9AE84` (portaetiquetas de
  precio). Estados: `#4DB27B`, `#E2A82B`, `#F0736B`, `#8C96A1`. Respecto al prototipo, tinta, lámina y trazos se
  separaron más (ajustes 1 y 2) y el texto subió de luz (ajuste 3). Cada par texto/fondo y cada borde de componente
  los comprueba el test de contraste (`contrast.ts`): AA en las tres superficies.
- **Nombres de token**: se **conservan** (`negro-pavonado` = tinta, `carbon` = lámina, `grafito` = lámina alta,
  `acero` = trazo, `hueso`, `niebla`, `naranja-senal`…) para no romper clases ni código existente (La Armería los
  usa). Se añaden `trazo-fuerte`, `cota`, `papel`, `tinta-papel`, `sobre-laton` y `kraft`. Cambiar los nombres a
  los del prototipo es un renombrado mecánico que se puede hacer en otro PR si Javi lo prefiere.
- **Tipografía**: **IBM Plex Sans Condensed** (400/500/600/700) para interfaz, titulares y rótulos, e **IBM Plex
  Mono** (400/500/600) para medidas, precios, códigos y cotas. OFL, autoalojadas con Fontsource, solo woff2 latinos.
  Sustituyen a Cinzel, Big Shoulders Stencil, Archivo y JetBrains Mono (se quitan del catálogo de pnpm).
- **Superficies**: retícula de 16 px (menor) y 80 px (mayor) sobre la tinta; **radio 0** en paneles y marcas y **2 px**
  en controles; marcas de registro en las esquinas (arriba a la izquierda y abajo a la derecha) de placas y, al pasar,
  de botones de línea; cajetín de plano y círculos de detalle en cabeceras de sección; sombra interior sutil.
- **Insignia de fidelidad T0–T3**: un cuadrito que se va llenando (vacío y discontinuo, un tercio, dos tercios, lleno),
  más el código y el nombre. El nivel nunca va solo en color.
- **Imágenes**: los renders propios (N5) viven sobre una lámina de papel. **Cuando una pieza no tiene render** se
  muestra un **plano T0 en SVG** con las cotas reales de la ficha (`PlanoPieza`): solo la envolvente a escala y solo
  en vista ortogonal; sin medidas, la lámina dice «Sin medidas verificadas». Se acabó el «Sin imagen».
- **Del B se toma** solo la luz de tubo en lo activo (el rótulo iluminado) y el portaetiquetas de kraft para las
  etiquetas de precio.

## Alternativas descartadas
- **B · Latón y nogal**: cálida y premium, pero con madera, serifa y texturas de taller se parece a una tienda de
  réplicas clásica, y su calidez resta peso a los datos. Se queda con la luz de tubo y el kraft.
- **C · Compactus**: muy funcional (estantería metálica y cajones), pero obliga a una maqueta más literal que
  limita el configurador y las tablas densas.
- **Mantener «herencia de armero»**: no se descartó por feo, sino porque el ruido, los tornillos y las capitales
  decorativas no apoyan la promesa de fidelidad 1:1 y datos honestos.

## Consecuencias
- Cambian `tokens.ts` (y `tokens.css`/`theme.css` generados), `fonts.ts`, `fuentes.css` y el CSS de componentes. Los
  componentes y sus API no cambian salvo `InsigniaFidelidad` (sin icono por nivel) y `FichaPieza` (acepta `medidas`
  para el plano T0).
- La retícula se pinta en `body`. Las vistas que no la quieran (p. ej. el lienzo 3D de La Armería) deben cubrirla con
  su propio fondo.
- docs/02 §1, §4.1–§4.3 se actualizan en el mismo PR. Las capturas de `docs/referencias/` siguen siendo referencia
  de atmósfera para La Armería, no de estilo de interfaz.
- Dos fuentes en vez de cuatro: menos peso (solo se precargan 400 y 600) y una sola familia que mantener.
- Pendiente de la dirección: el móvil (aparcado el 22-11-2026), el renombrado de tokens y el resto de componentes
  del configurador (Cajón, Nodo de ranura, Deslizador), que se rehacen en este estilo cuando se construyan.
- Si Javi no da su OK, se revierte el PR: los nombres de token estables hacen que sea un cambio de valores.
