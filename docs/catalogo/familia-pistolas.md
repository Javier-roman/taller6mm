# Familia de pistolas de airsoft: Hi-Capa y Glock

> Generado a partir de `catalogo/pistolas-piezas.json` (fuente de datos: ese JSON). Fecha: 2026-11-19.

Piezas de las plataformas `hi-capa` y `glock-17` de `catalogo/plataformas.json`, creadas por generador paramétrico
(`apps/pipeline/src/taller6mm_pipeline/familias/pistola_*.py` y `pistolas_piezas.py`, registro propio `FAMILIAS_PISTOLA`).
Solo airsoft y solo formas exteriores: sin mecánica interna, sin marcas, logos ni leyendas. **El revólver queda fuera
del alcance** (decisión del 18-11-2026: de momento solo cuatro familias pulidas: pistolas, M4 y AK).

## Estado y honestidad de los datos

- Todas las piezas son `es_demo`, **T0** y `publicable_3d = false`: no hay vistas licenciadas que las suban de nivel.
- Ninguna cota es la medida de un SKU. Las proporciones (perfiles, guarda, mandos, texturizado) son **estimadas a ojo**
  y llevan confianza **baja** con su fuente. Lo desconocido es `null` + bandera.
- Cota con fuente: el largo total de la Hi-Capa 5.1 (222 mm), la rosca de boca de 14 mm a izquierdas y el cañón interior de
  112 mm salen de la ficha oficial de Tokyo Marui (`docs/catalogo/cotas-publicas.md`, confianza alta). El largo total
  se anota como referencia del arma completa; no se aplica a ninguna pieza suelta.
- Las interfaces nuevas (`riel-corredera-pistola`, `cola-milano-mira-pistola`, `montaje-empunadura-lateral-1911`,
  `alojamiento-canon-pistola`) son **propuestas** que aún no están en `catalogo/interfaces.json`; `pozo-glock-gbb`,
  `pozo-hi-capa`, `rail-pistola-glock-universal` y `rosca-m14x1-ccw` ya existen.
- Mallas cerradas (0 aristas abiertas), GLB determinista, sockets `socket.*`.

## Familias

| Familia | Qué modela | Parámetros (mm) |
|---|---|---|
| `armazon.pistola` (`glock`) | Armazón de polímero: cubrecañón con riel de accesorios, agarre inclinado con punteado, ranuras de dedos y marcas dorsales, guarda cuadrada, gatillo con seguro, palanca de retenida, botón del cargador, palanca de desmontaje y pasadores | largo, alto del agarre, profundidad, ancho, inclinación, textura |
| `armazon.pistola` (`hicapa`) | Marco metálico de doble columna estilo 1911: guarda cuadrada, gatillo aligerado, martillo de anilla, seguro de empuñadura con cola de castor, seguro manual ambidiestro, retenida, botón y cuatro casquillos por lado para las cachas | los mismos |
| `cacha.hicapa` | Cacha lateral (izquierda o derecha) con rebaje del pulgar, dorso abombado, rejilla de agarre de ranuras redondas y taladros de tornillo | alto, profundidad, ancho, inclinación, lado |
| `corredera.pistola` (`polimero`) | Corredera tipo Glock: bisel frontal y de costados, ventana de eyección, serrados traseros y frontales, colas de milano de las miras, alojamiento del cañón y del percutor | largo, ancho, alto, ventana, serrados |
| `corredera.pistola` (`clasico`) | Corredera tipo Hi-Capa: lomo redondeado, ventana, serrados, colas de milano y alojamiento del cañón con rosca | los mismos |
| `canon.pistola` | Cañón exterior con capó de recámara, collares y tramo roscado de boca de 14 mm a izquierdas | longitud, diámetro, rosca, tramo roscado |
| `mira.pistola` | Mira trasera (ventana en U, regulable con tornillo de deriva) o delantera (poste con rampa) con cola de milano | lado, tipo, alto, ancho |
| `cargador.gas_pistola` | Cargador de gas de cuerpo hueco, labios de alimentación, tubo, muesca de retenida, ventanas y base con válvula de carga; Glock con tope de polímero | estilo, capacidad, altura, profundidad, ancho |

El armazón de los dos estilos está en una sola familia (`armazon.pistola`) con el parámetro `estilo`; las dos corredera,
igual. Los cargadores de gas no son intercambiables entre estilos (`pozo-glock-gbb` frente a `pozo-hi-capa`).

## Tanda de piezas (14)

| Id | Familia | Plataforma | Caja (mm) | Triángulos | Nota |
|---|---|---|---|---:|---|
| `armazon-glock` | `armazon.pistola` | glock-17 | 202 × 105 × 30 | 79316 | Polímero con punteado, riel y guarda. |
| `armazon-hicapa` | `armazon.pistola` | hi-capa | 150 × 112 × 28 | 3948 | Marco metálico de doble columna. |
| `cacha-hicapa-izq` | `cacha.hicapa` | hi-capa | 74 × 92 × 5 | 14658 | Rejilla de agarre. |
| `cacha-hicapa-der` | `cacha.hicapa` | hi-capa | 74 × 92 × 5 | 14664 | Rejilla de agarre. |
| `corredera-glock` | `corredera.pistola` | glock-17 | 186 × 30 × 26 | 3248 | Serrados, ventana y bisel. |
| `corredera-hicapa` | `corredera.pistola` | hi-capa | 207 × 29 × 26 | 3302 | Silueta clásica con serrado. |
| `canon-glock` | `canon.pistola` | glock-17 | 166 × 21 × 15 | 3066 | Rosca de boca de 14 mm a izquierdas. |
| `canon-hicapa` | `canon.pistola` | hi-capa | 187 × 21 × 15 | 3066 | Rosca de boca de 14 mm a izquierdas. |
| `mira-trasera-glock` | `mira.pistola` | glock-17 | 7 × 8 × 13 | 410 | Ventana en U. |
| `mira-delantera-glock` | `mira.pistola` | glock-17 | 7 × 7 × 10 | 392 | Poste con rampa. |
| `mira-trasera-hicapa` | `mira.pistola` | hi-capa | 11 × 8 × 15 | 680 | Regulable con tornillo de deriva. |
| `mira-delantera-hicapa` | `mira.pistola` | hi-capa | 7 × 7 × 10 | 392 | Poste con rampa. |
| `cargador-glock` | `cargador.gas_pistola` | glock-17 | 37 × 93 × 23 | 9826 | Cargador de gas con tope de base y válvula. |
| `cargador-hicapa` | `cargador.gas_pistola` | hi-capa | 44 × 93 × 21 | 7878 | Cargador de gas de doble columna con válvula. |

## Montajes completos (2)

Cada montaje se compone con `pistola_montaje.montar(build)`: todas las piezas comparten el origen de pistola (cara trasera
de la corredera, eje del cañón), así que el armazón, la corredera, el cañón y las cachas entran por identidad; las miras se
trasladan a los sockets `mira_trasera` y `mira_delantera` de la corredera, y el cargador se gira la inclinación del agarre y
se traslada al socket `cargador` del armazón. Cada unión comprueba que la pieza pida una interfaz que el padre ofrezca.

| Id | Nombre | Piezas | Caja (mm) | Todo encaja |
|---|---|---:|---|---|
| `hicapa-5-1` | Hi-Capa 5.1 (armazón doble columna con cachas) | 8 | 245 × 159 × 33 | sí |
| `glock-17-gbb` | Glock 17 GBB (armazón de polímero) | 6 | 229 × 152 × 30 | sí |

## Cobertura de plataformas

| Plataforma | Piezas propias | Montaje | Pendiente |
|---|---|---|---|
| `hi-capa` | armazón de doble columna, 2 cachas, corredera clásica, cañón con rosca de 14 mm CCW, 2 miras, cargador de gas | `hicapa-5-1` | cachas con la forma real de cada SKU, martillo y seguros con cotas, malla de la boca de la corredera |
| `glock-17` | armazón de polímero, corredera, cañón con rosca de 14 mm CCW, 2 miras, cargador de gas | `glock-17-gbb` | texturas reales del agarre, tope de cargador con cota, mira de fibra óptica |

## Límites visibles

- Todo es forma exterior: no hay mecánica interna ni piezas móviles (la corredera no retrocede).
- La inclinación y las proporciones son de barrido: ni la Hi-Capa ni la Glock coinciden aún con una réplica concreta.
- Los GLB no se publican; el color y el acabado salen de la biblioteca de materiales propia (`docs/05`).
- La puerta de calidad exige mínimos distintos por familia en `catalogo/calidad-minimos.json`: las miras son piezas
  pequeñas de caras planas, las cachas son placas finas (dos de las tres vistas son rectángulos) y la corredera es un
  prisma hueco con pocas superficies curvas; sus mínimos de silueta u orientaciones son más bajos, como los de
  `canon.exterior` y `amortiguador.tubo`.
