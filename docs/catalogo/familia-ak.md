# Familia AK de airsoft: cobertura de piezas generadas

> Generado a partir de `catalogo/ak-piezas.json` (fuente de datos: ese JSON). Fecha: 2026-11-17.

Piezas de las plataformas AK-47/AKM y AK-74 (con AKS-74U y AK-105, que en `plataformas.json` cuelgan de `ak74`) creadas por generador paramétrico (`apps/pipeline/src/taller6mm_pipeline/familias/ak_*.py`, registro propio `FAMILIAS_AK`). Solo airsoft y solo formas exteriores: sin internos, sin marcas ni logos ni leyendas.

## Estado y honestidad de los datos

- Todas las piezas son `es_demo`, **T0** y `publicable_3d = false`. Las vistas licenciadas que subirían el nivel no existen todavía.
- Ninguna cota es la medida de un SKU. Las proporciones de detalle (perfiles, ranuras, nervaduras, posición del pozo, bloque de gas, etc.) son **estimadas a ojo** y llevan confianza **baja** con su fuente («estimado… sin fuente ni calibre»). Se sustituyen por la ficha de un SKU o por calibre.
- Lo desconocido es `null` + bandera: una cota crítica sin dato (p. ej. la longitud del receptor) produce T0 sin malla.
- Mallas cerradas, GLB determinista, sockets `socket.*` (convención de ejes de `LEEME.md`). Las interfaces nuevas (`montaje-canon-ak`, `montaje-tapa-ak`, `montaje-guardamanos-ak`, `montaje-cubremano-ak`, `montaje-pistolete-ak`, `montaje-mira-trasera-ak`, `montaje-riel-lateral-ak`) son **propuestas** que aún no están en `catalogo/interfaces.json`; el resto (`pozo-ak`, `montaje-culata-ak`, `montaje-culata-ak-plegable-lateral`, `rosca-m14x1-ccw`, `picatinny-mil-std-1913`, `rail-11mm-cola-milano`) ya existen.
- Las piezas se miden con los mismos tres detectores que `tests/test_formas_reales.py` (relleno de la caja, triángulos y orientaciones de cara) en `tests/test_familias_ak.py`.

## Familias

| Familia | Qué modela | Parámetros (mm) |
|---|---|---|
| `ak.receptor` | Receptor estampado: cuna delantera, espiga, pozo, ventana de eyección, nervaduras, guardamonte y remaches | longitud, alto, ancho |
| `ak.tapa` | Tapa abombada con casquillo trasero, nervaduras y raíl Picatinny opcional | longitud, alto, ancho, nervaduras, raíl |
| `ak.guardamanos_inferior` | Guardamanos de madera (surcos y escotaduras de dedos) o polímero (estrías) con canal del cañón | longitud, ancho, alto, estilo |
| `ak.cubremano` | Cubre-mano superior con canal del tubo de gas y ventilación (ranuras, nervios o ninguna) | longitud, ancho, alto, ventilación |
| `ak.culata_fija` | Culata de madera (plancha, tornillos, estuche) o polímero (aligeramientos) | longitud, alto de plancha, ancho, material |
| `ak.culata_plegable` | Bastidor triangular lateral con zapata y bisagra; extendida o plegada a la izquierda | longitud, alto, grosor, posición |
| `ak.pistolete` | Pistolete por secciones lofteadas, baquelita o polímero estriado | altura, profundidad, ancho, inclinación, estilo |
| `ak.cargador` | Cargador curvo sobre espina circular, de acero (surcos) o polímero (estriado), con gancho y tetón | altura, profundidad, ancho, radio de curva, material |
| `ak.canon` | Cañón con bloque de gas, tubo de gas, varilla, base de mira con capucha u orejas, poste y tetón de bayoneta | longitud, diámetro, tramo roscado, mira |
| `ak.boca` | Freno oblicuo, dos cámaras, apagallamas en embudo y apagallamas ranurado (rosca M14 a izquierdas) | tipo, longitud, diámetro |
| `ak.mira_trasera` | Mira trasera de tangente: base, hoja inclinada con marcas y cursor con muesca en U | longitud, ancho, alto |
| `ak.riel_lateral` | Placa lateral con riel de cola de milano y ranuras para ópticas | longitud, alto, ranuras |

La «pistolera de mira» del encargo se ha interpretado como las bases de mira: mira trasera de tangente y riel lateral para ópticas (más la base del punto de mira dentro de `ak.canon`). Si se refería a otra cosa, se corrige en una pasada siguiente.

## Tanda de variantes (36)

| Id | Familia | Plataforma | Caja (mm) | Triángulos | Nota |
|---|---|---|---|---:|---|
| `receptor-akm` | `ak.receptor` | akm | 398 × 72 × 42 | 9106 | Receptor estampado con ventana y nervaduras. |
| `receptor-ak74` | `ak.receptor` | ak74 | 398 × 72 × 42 | 9106 | Mismo cuerpo estampado; difiere en la tapa y el cañón. |
| `receptor-corto-aks74u` | `ak.receptor` | ak74 | 318 × 72 × 42 | 9116 | Receptor acortado del carabina compacta. |
| `receptor-liso` | `ak.receptor` | akm, ak74 | 398 × 72 × 42 | 7320 | Sin ventana ni nervaduras. |
| `tapa-akm` | `ak.tapa` | akm | 295 × 19 × 36 | 2106 | Tapa abombada con dos nervaduras. |
| `tapa-ak74` | `ak.tapa` | ak74 | 295 × 19 × 36 | 2790 | Tapa con cuatro nervaduras transversales. |
| `tapa-corta-aks74u` | `ak.tapa` | ak74 | 235 × 19 × 36 | 1344 | Tapa corta sin nervaduras. |
| `tapa-con-rail` | `ak.tapa` | akm, ak74 | 295 × 27 × 36 | 2526 | Tapa con raíl Picatinny superior. |
| `guardamanos-madera-akm` | `ak.guardamanos_inferior` | akm | 190 × 35 × 40 | 1698 | Madera con tres surcos de agarre. |
| `guardamanos-polimero-ak74` | `ak.guardamanos_inferior` | ak74 | 190 × 35 × 40 | 2046 | Polímero con estrías laterales. |
| `guardamanos-corto-aks74u` | `ak.guardamanos_inferior` | ak74 | 120 × 35 × 40 | 1852 | Guardamanos corto. |
| `guardamanos-ak105` | `ak.guardamanos_inferior` | ak74 | 160 × 35 × 40 | 1990 | Longitud intermedia. |
| `cubremano-nervios-akm` | `ak.cubremano` | akm | 180 × 26 × 36 | 1534 | Nervios transversales (madera). |
| `cubremano-ranuras-ak74` | `ak.cubremano` | ak74 | 180 × 26 × 36 | 4744 | Dos filas de ranuras de ventilación. |
| `cubremano-corto-aks74u` | `ak.cubremano` | ak74 | 110 × 26 × 36 | 3324 | Cubre-mano corto ventilado. |
| `cubremano-liso` | `ak.cubremano` | akm, ak74 | 160 × 26 × 36 | 988 | Sin cortes. |
| `culata-fija-madera-akm` | `ak.culata_fija` | akm | 321 × 136 × 38 | 2082 | Madera con plancha. |
| `culata-fija-polimero-ak74` | `ak.culata_fija` | ak74 | 321 × 136 × 38 | 2576 | Polímero con aligeramientos laterales. |
| `culata-ak-plegable-extendida` | `ak.culata_plegable` | ak74 | 310 × 128 × 45 | 1024 | Bastidor triangular lateral extendido. |
| `culata-ak-plegable-plegada` | `ak.culata_plegable` | ak74 | 312 × 128 × 76 | 1188 | Plegada contra el lado izquierdo. |
| `pistolete-bakelita` | `ak.pistolete` | akm | 75 × 100 × 32 | 2794 | Dos surcos laterales. |
| `pistolete-polimero` | `ak.pistolete` | ak74 | 75 × 100 × 32 | 4210 | Estriado fino lateral. |
| `cargador-acero` | `ak.cargador` | akm, ak74 | 126 × 246 × 30 | 2074 | Surcos prensados. |
| `cargador-polimero` | `ak.cargador` | ak74 | 126 × 246 × 30 | 1896 | Estriado fino. |
| `cargador-corto-acero` | `ak.cargador` | akm, ak74 | 88 × 175 × 30 | 1762 | Capacidad media, mismo pozo. |
| `canon-akm` | `ak.canon` | akm | 370 × 56 × 23 | 2356 | Mira con capucha circular. |
| `canon-ak74` | `ak.canon` | ak74 | 370 × 55 × 23 | 2356 | Mira con dos orejas laterales. |
| `canon-ak105` | `ak.canon` | ak74 | 270 × 55 × 23 | 2356 | Cañón intermedio. |
| `canon-corto-aks74u` | `ak.canon` | ak74 | 160 × 55 × 23 | 2356 | Cañón corto con bloque de gas adelantado. |
| `boca-oblicuo-akm` | `ak.boca` | akm | 40 × 21 × 21 | 1144 | Corte oblicuo con lumbrera superior. |
| `boca-dos-camaras-ak74` | `ak.boca` | ak74 | 58 × 23 × 23 | 4324 | Dos cámaras con ventanas y orificios. |
| `boca-embudo-aks74u` | `ak.boca` | ak74 | 42 × 25 × 25 | 1418 | Apagallamas en embudo con cuatro ranuras. |
| `boca-ranurado-ak105` | `ak.boca` | ak74 | 34 × 20 × 20 | 1110 | Apagallamas ranurado de seis lumbreras. |
| `mira-trasera-tangente` | `ak.mira_trasera` | akm, ak74 | 64 × 33 × 24 | 1304 | Hoja con marcas y cursor en U. |
| `riel-lateral-6` | `ak.riel_lateral` | akm, ak74 | 180 × 46 × 12 | 14032 | Placa con cola de milano y seis ranuras. |
| `riel-lateral-corto` | `ak.riel_lateral` | ak74 | 120 × 40 × 12 | 10552 | Versión corta. |

## Regenerar

```bash
cd apps/pipeline
uv run python -m taller6mm_pipeline.familias.ak_piezas --registro ../../catalogo/ak-piezas.json
```

Los GLB salen en `apps/pipeline/salida/ak/` (ignorada por git). Previsualización: `blender/previsualizar.py` (material procedural propio; no es una foto ni se publica).

## Pendiente

- Cotas reales por SKU (receptor, cargador, guardamanos) con ficha de fabricante o calibre; vistas licenciadas para subir de T0.
- Dar de alta en `interfaces.json` las siete interfaces propuestas.
- Mapa de elementos AK (`ak.json`) equivalente a `ar-m4.json`, para enlazar `elemento`.
- Pulir la mira trasera y el cañón (biselados finos) y optimizar los GLB (Meshopt) antes de cualquier publicación.
