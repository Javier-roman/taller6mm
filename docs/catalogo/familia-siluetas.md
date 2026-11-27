# Réplicas guiadas por silueta (plan T2 de docs/05)

Modelado a partir del **contorno medido** de una foto de referencia, en lugar de inventar la forma. Desde el 25-11-2026 cubre
AKM, AK-105, Mk18 Mod.1, Hi-Capa (visor reflex) y Glock 19X. Todo es **T0, `publicable_3d=false`, confianza media** (contorno)
y **baja** (anchos en Z y relieves), con `es_demo=false` solo para lo medido.

## Reglas de las fotos
Las capturas de tienda que aporta Javi viven en `assets-src/raw/_entrada/` (ignorada por git) y son **referencia interna**
(principio 5): no se copian al repo, no se publican, no se proyectan como textura y no se suben a ningún servicio. En git solo
van **números derivados**, con la fuente «medido en foto de referencia interna (aportada por Javi)»: contornos en mm,
proporciones, colores medianos y polígonos de partición. No se reproducen logos ni rótulos.

## Cadena
1. `fotos/silueta.py` (numpy + Pillow, determinista): máscara por distancia al color del borde, componentes conexas,
   rellenado de agujeros pequeños, trazado de aristas de píxel con agujeros, media móvil, Douglas-Peucker y calibre.
2. `fotos/replicas_silueta.py` y `fotos/replicas_fusiles.py`: por réplica, calibre (cota pública), **partición manual en
   regiones** (corredera, armazón, cachas, cargador, alzas / receptor, guardamanos, culata…; con criterio de color para la
   madera y `quita_a` para piezas separadas), proporciones, detalles medidos y colores → `catalogo/siluetas-referencia.json`.
3. `familias/siluetas_modelos.py` + `siluetas_motor.py`: cada parte es el contorno extruido con su ancho en Z (estimado) y
   un redondeo por prisma (`silueta_solidos.py`; los filetes de OCCT no sirven aquí, ver cuaderno), o un sólido de
   **revolución** si es redonda (cañón, tubo de gases, bocacha). Encima: serrados, ventana, cañón a ras, nervaduras del
   cargador, agujeros M-LOK/RIS, hoyuelos de agarre, tornillos.
4. `siluetas_generar.py`: GLB por parte, `escena.json` (partes + paleta) e **IoU** de la silueta del modelo contra la máscara
   de la foto. El IoU es circular (el contorno sale de la misma foto): mide el proceso, no una verificación independiente.
5. `planos_silueta.py`: **plano T0 en SVG** a partir de los mismos contornos (2D y 3D coinciden), estética «Plano de cotas»
   (ADR-0010), cotas de largo, alto y pieza principal, colores como variables CSS. Sin píxeles de la foto. Salida en
   `assets-src/vistas/planos-silueta/` + `indice.json` (viewBox, largo, alto, nivel).
6. `blender/renderizar_silueta.py`: lateral ortogonal (lado izquierdo, boca a la derecha) y tres cuartos, fondo transparente,
   luz de `catalogo/iluminacion-presets.json` (`mate_suave`: clave, relleno, tiras de contorno, sombrero), materiales con el
   albedo medido. Salida en `assets-src/vistas/replicas-silueta/` (ignorada).

## Secciones transversales (no son prismas de grosor constante)
Cada `Spec` puede llevar `planta` (ancho en Z según la posición a lo largo de X o de Y): culatas que se estrechan hacia el
cuello, empuñaduras que se afinan hacia abajo, guardamanos que adelgazan. Además: guardamanos RIS con **cuatro raíles**
(`rail_picatinny.solido_rail`) y raíl superior en el AK-105, apagallamas con seis ranuras, brocal del pozo del cargador,
cachas de la Hi-Capa integradas en el armazón con relieve de escamas. Los anchos son estimaciones (confianza baja).

## Colores (medidos)
La mediana de un rectángulo del objeto da el color con la luz de la foto y se guarda como `rgb_medido`. El albedo aplicado
(`rgb`, con su nota) depende del modo: polímero negro neutro común #1E1F21; metal pintado #242527 con especular; madera del AKM
barniz #5A2E1C con veta procedural y capa de barniz; Glock 19X en coyote (se conserva el valor medido y el tono se lleva a
33 grados porque el medido es un balance de blancos cálido); el resto, color medido × 0,8. Se guardan ambos valores. La
rugosidad sale de la guía de aspecto (metal pintado 0,4-0,45, polímero 0,5-0,55, madera barnizada 0,5).

## Calibre y límites
| Réplica | Calibre | Confianza |
|---|---|---|
| Mk18 Mod.1 | 715 mm, ficha oficial Tokyo Marui (culata recogida) | alta |
| Hi-Capa (visor reflex) | 222 mm de la Hi-Capa 5.1 (ficha TM); no hay ficha del SKU | media-baja |
| Glock 19X | 189 mm (7,44 in), tabla técnica oficial de GLOCK (eu.glock.com, consultada el 26-11-2026); la altura con cargador sale a 139 mm, igual que la cifra oficial (comprobación cruzada) | alta |
| AKM | 880 mm nominal de la plataforma; sin ficha del SKU | baja |
| AK-105 | 943 mm nominal de la plataforma (culata extendida); el montaje de la foto puede diferir un 8 % | baja |

- El ancho en Z no se ve en una foto lateral: es una estimación por pieza (`ancho_z_mm` en cada GLB y en el registro).
- El SA-F14 y el MCX Spear solo tienen fotos en 3/4: **no se construyen** (la silueta no es ortogonal); sirven de
  referencia cualitativa. La P226 se deja como referencia extra, sin modelar.
- Las ranuras M-LOK del AK-105 y los orificios del guardamanos del Mk18 siguen la cadencia vista, no una medida.

## Variantes derivadas (`catalogo/variantes-derivadas.json`, `siluetas_variantes.py`)
Una plataforma = **zona fija** (contorno real del receptor/armazón) + **zonas variables** (longitud de cañón y guardamanos o
de corredera, color; en el futuro culata, cargador, óptica con sockets). Una variante es **DERIVADA de la base X**: se estira
el tramo delantero hasta una longitud total publicada (ficha oficial si existe; si no, dato de la plataforma y bandera) y/o
se cambia el color tomando otro valor medido en la misma foto. Siempre T0, confianza baja-media, `es_demo=true`, nunca la
medida de una réplica concreta. Un receptor o sistema distinto (otro fabricante) exige su propia silueta de referencia.
Por plataforma se generan tres variantes de prueba (AK: carabina corta, guardamanos largo, todo negro; M4: longitud CQB-R,
carabina, todo negro; Hi-Capa: longitud Chisato, D.O.R, metal claro; Glock: compacta, estándar, negra).

## Añadir una réplica
1. Foto lateral casi ortogonal en `assets-src/raw/_entrada/<réplica>/`.
2. Definir `Replica` (regiones, calibre con fuente, muestras de color, detalles) en `replicas_*.py`; correr
   `uv run python -m taller6mm_pipeline.fotos.replicas_silueta --entrada <ruta>` y revisar la superposición.
3. Añadir su función en `siluetas_modelos.MODELOS` con sus `Spec`; `siluetas_generar`; renders; plano.
4. Formatear el JSON con Biome y pasar `pytest tests/test_siluetas_modelos.py` y `catalogo/siluetas.test.mjs`.
