# Réplicas ilustrativas (modelos de licencia abierta retexturizados y ajustados a siluetas)

> Estado a 26-11-2026. Registro: `catalogo/replicas-ilustrativas.json` (con su test). Código: `apps/pipeline/blender/replicas_cc.py` (Blender, Cycles) y `apps/pipeline/src/taller6mm_pipeline/replicas_cc.py` (Python: trabajos, IoU de silueta, variante papel, comparación y hoja de contacto). Esto no es asesoramiento jurídico (docs/09).

## Por qué

Las réplicas paramétricas montadas se rechazaron («parecen juguete malo del chino»; `critico-diseno` las puntuó 3-4 sobre 10). Para La Armería y la vista 2D se usan **modelos completos de licencia abierta con forma real**, retexturizados con los materiales y la luz propios y, en los fusiles, **deformados por zonas para que su silueta lateral se ajuste a la de una foto de referencia**. Son **ilustrativos**: nivel T0, medidas sin verificar, no son la réplica exacta de ninguna marca. Las piezas paramétricas siguen sirviendo para el configurador modular, no para la imagen de portada de las baldas.

Decisión de Javi (26-11-2026, ADR-0011 en preparación): ya no se calibra la escala al milímetro de cada réplica; la escala es **relativa, con bandera**, y las proporciones salen de las siluetas. Lo desconocido sigue siendo `null` con bandera.

## Los cinco modelos

| Id | Modelo base | Autor y licencia | Triángulos | IoU de silueta (ajustado) |
|---|---|---|---|---|
| `glock-locarem` | High Poly Glock-18 (No-Textures), OpenGameArt | locarem, CC0 | 27.676 | 0,70 (sin ajuste; foto de una Glock 19X, otro modelo) |
| `pistola-1911-solid3ddd` | Colt Pistol M1911A1 Game Asset, Sketchfab (copia Objaverse) | solid3DDD, CC BY 4.0 | 15.060 | 0,62 (sin ajuste; foto de una Hi-Capa con visor; 0,83 con la mejor traslación) |
| `akm-lamoot` | High-poly AK-47, OpenGameArt | Lamoot, CC0 | 30.730 | **0,86** (0,68 antes del ajuste) |
| `ak105-lamoot` | el mismo AK-47 de Lamoot, sin la culata de madera | Lamoot, CC0 | 30.730 + piezas propias | **0,82** (0,70 antes) |
| `mk18-mrm0lten` | M4A1 Carbine, Sketchfab (copia Objaverse) | MrM0lten, CC BY 4.0 | 20.995 | **0,74** (0,49 antes) |

- **No hay Hi-Capa de licencia abierta.** Se buscó (Sketchfab, API pública) y no hay ninguna con forma aprovechable (la única, «HI-CAPA STAND», es un soporte). Se usa una **1911**, la plataforma de la que deriva. De trece candidatos se compararon en Workbench y se renderizaron tres; la elegida es la única con detalle real (tornillos de cachas, seguro, ventana de expulsión).
- Atribución CC BY archivada en el registro (`fuente.atribucion`). CC0 no la exige; se archiva igualmente.
- Rótulo de escala («Escala tomada de»): AKM, AK-105 y Mk18, de la silueta de la foto (calibrada con la longitud nominal de la plataforma, o la ficha de Tokyo Marui en el Mk18); 1911, la cota citada de la Hi-Capa 5.1 (222 mm); Glock, convención sin cita (200 mm). `longitud_mm_verificada` es `null` en todos.

## Ajuste a la silueta de la foto (fusiles)

Referencia: `catalogo/siluetas-referencia.json` (contornos en mm medidos sobre fotos de referencia internas; las fotos no se publican ni se usan como textura).

1. **Medida**: máscara lateral ortográfica del modelo (Workbench, alfa) frente al contorno de la foto (unión de partes menos huecos), alineadas por la esquina superior izquierda. `taller6mm_pipeline.replicas_cc` modo `silueta` + `iou`; el contorno se vuelca con `overlay` en rojo (foto) y verde (modelo).
2. **Corrección por zonas** (`render.ajuste` en el registro): un mapa lineal a tramos del eje de la boca (culata, cajón, guardamanos, cañón) y una transformación afín de la altura interpolada entre anclas; las zonas con pendiente 1 (cajón) conservan tornillos y estrías. El cargador y el pistolete se mueven como sólidos rígidos (traslación, giro, escala propios).
3. **Optimización** (`ajustar`): descenso de coordenadas sobre el IoU con penalización de escalas y pendientes y con anclas atadas por zona (sin atar, el cañón del Mk18 salía inclinado).
4. **AK-105**: se borra la culata maciza; la culata ajustable y su tubo salen extruidos del contorno de la foto (pieza plana, por eso su IoU es 1 por construcción) y el freno de boca es una pieza de revolución con el perfil de la foto. Guardamanos y pistolete en polímero.
5. **Mk18**: se quita el asa de transporte (no existe en la foto), culata y guardamanos con acabado arena como en la foto.

Límites honestos: el Mk18 tiene el guardamanos más fino que el RIS de la foto (el IoU es 0,74); el AK-105 conserva la tapa redondeada del cajón en vez del raíl plano; la culata del AK-105 es una pieza plana con bisel y se nota de cerca.

## Cómo se hizo el resto

1. **Licencia en vivo antes de descargar**: ficha de OpenGameArt y API pública de Sketchfab. Descarga a ritmo bajo con el User-Agent identificado. Los hashes coinciden con los manifiestos previos.
2. **Limpieza** (`listar`): sin texturas, materiales ni UV; partes sueltas separadas; internos y munición borrados por reglas.
3. **Zonas de material** por nombre de malla o caja normalizada; las cachas de la 1911 se acotan por rectas en el plano.
4. **Materiales** de la biblioteca propia (bases CC0 de `catalogo/materiales-cc0.json`): metal negro neutro sin rayas, desgaste gris en aristas (sonda de bordes: 0,1-3 % de la silueta con mezcla mayor del 10 %), polímeros `#0E0E0E`-`#161616` rugosos, madera `#5A2E1C` con barniz difuso, nogal cuadriculado en la 1911 (relieve procedural a 20 LPI aprox.) con veta a lo largo de la empuñadura, acabado arena en la culata y el guardamanos del Mk18.
5. **Luz de tres puntos** (clave `luz`): principal de área a 45°/35° respecto a la cámara, relleno a un tercio, dos tiras de contorno detrás y arriba (2x, no 1,5x), una tercera baja y trasera, panel de reflejo, mundo 0,025-0,055, AgX «Medium High Contrast», fondo transparente. Ajustes por pieza en `render.luz_ajuste` (relleno y contornos).
6. **Render** a 1800 x 1200, 160 muestras, OIDN, lente 90-100 mm: `lateral` (cámara a -Y: boca a la derecha, lado derecho), `lateral-izq` (cámara a +Y: lado izquierdo real, boca a la izquierda) y `tres-cuartos` (encuadre por silueta al 80 %).
7. **Variante sobre papel** (`papel`): cada vista recortada y compuesta sobre `#D7D4CC` con sombra suave, arma al 80 % del cuadro (`<vista>-papel.png`).
8. **Comparación con la foto** (`comparar`): hoja interna con la foto (volteada si hace falta) junto a la vista sobre papel, en `assets-src/vistas/replicas-cc/_comparacion/` (ignorada por git; la foto nunca se publica).
9. **Hoja de contacto** (`hoja`): una oscura y una sobre papel, con el rótulo «ILUSTRATIVA T0, medidas sin verificar» y «Escala tomada de».

## Sobre «lado izquierdo, boca a la derecha»

Con la boca a la derecha del cuadro se ve el lado **derecho** del arma. El lado izquierdo real queda con la boca a la izquierda. Para no mostrar un arma especular falsa se entregan las dos vistas; el tres cuartos de las pistolas enseña el lado derecho en la 1911 y el izquierdo en la Glock (el de las estrías de la corredera). Las siluetas de referencia están volcadas a «boca a la derecha» y se comparan con la vista lateral.

## Reglas que se cumplen

- Solo CC0, CC BY y dominio público; nada de SA, NC ni ND. Sin marcajes ni logos: se descartan todas las texturas; en los renders a 100 % no se lee texto en la geometría (falta revisión humana).
- Solo la forma exterior de airsoft; nada de internos de armas reales.
- `publicable: false` en todos hasta que un humano revise la procedencia (docs/05 §5). Las fotos de referencia son uso interno.
- Cada imagen debe llevar el aviso «Imagen ilustrativa: forma genérica de un modelo 3D de licencia abierta, sin medidas verificadas. No es la réplica exacta de ninguna marca» (`aviso` en el registro).

## Reproducir

```
python -I -c "import sys; sys.path.insert(0, 'apps/pipeline/src'); from taller6mm_pipeline import replicas_cc; replicas_cc.main()" -- <modo> <id|todos> [opciones]
```

Modos: `listar`, `debug`, `render [res=1200x800] [muestras=48] [sufijo=-t1] [vistas=...]`, `sonda`, `silueta [largo=mm]`, `iou ref=<id de silueta>`, `ajustar ref=<id de silueta> [rondas=7]`, `papel`, `comparar` y `hoja`. Los binarios van en `assets-src/raw/modelos-cc/` y los renders en `assets-src/vistas/replicas-cc/`; las dos están ignoradas por git.

## Revisión de `critico-diseno`

Primera tanda (25-11-2026): M4A1 6,5 · 1911 6 · AK 5,5 · Glock 5, tras aplicar sus arreglos de la primera pasada (eran 6, 4,5, 5 y 3,5). Techo de 6-7 con geometría gratuita: la pieza protagonista de cada balda saldrá del frente de fidelidad, no de aquí. La Glock queda **no recomendada como pieza principal** (formas blandas, guardamonte con el disparador fundido, hoyuelo de la empuñadura en el modelo original). Segunda tanda: ver el PR.
