# Réplicas ilustrativas (modelos de licencia abierta retexturizados)

> Estado a 25-11-2026. Registro: `catalogo/replicas-ilustrativas.json` (con su test). Código: `apps/pipeline/blender/replicas_cc.py` (Blender, Cycles) y `apps/pipeline/src/taller6mm_pipeline/replicas_cc.py` (Python, prepara los trabajos y la hoja de contacto). Esto no es asesoramiento jurídico (docs/09).

## Por qué

Las réplicas paramétricas montadas se rechazaron («parecen juguete malo del chino»; `critico-diseno` las puntuó 3-4 sobre 10). Para La Armería y la vista 2D se usan **modelos completos de licencia abierta con forma real**, retexturizados con los materiales y la luz propios. Son **ilustrativos**: nivel T0, medidas sin verificar, no son la réplica exacta de ninguna marca. Las piezas paramétricas siguen sirviendo para el configurador modular, no para la imagen de portada de las baldas.

## Los cuatro modelos

| Id | Modelo base | Autor y licencia | Triángulos limpios | Escala de render |
|---|---|---|---|---|
| `glock-locarem` | High Poly Glock-18 (No-Textures), OpenGameArt | locarem, CC0 | 27.676 | 200 mm, **convención** sin cita |
| `ak47-lamoot` | High-poly AK-47, OpenGameArt | Lamoot, CC0 | 30.730 | 880 mm, **convención** sin cita |
| `m4a1-mrm0lten` | M4A1 Carbine, Sketchfab (copia Objaverse) | MrM0lten, CC BY 4.0 | 20.995 | 777 mm, **citada** (TM M4A1 MWS) |
| `pistola-1911-solid3ddd` | Colt Pistol M1911A1 Game Asset, Sketchfab (copia Objaverse) | solid3DDD, CC BY 4.0 | 15.060 | 222 mm, **citada** (TM Hi-Capa 5.1) |

- **No hay Hi-Capa.** Se buscó (Sketchfab, API pública) y no hay ninguna de licencia abierta con forma aprovechable (la única, «HI-CAPA STAND», es un soporte). Se usa una **1911**, la plataforma de la que deriva. Se compararon en Workbench trece candidatos y se renderizaron dos 1911 más (Foxx Assets, descartada por una corrugación en la boca de la corredera, y 8sianDude, con 638 partes sueltas desordenadas); la elegida es la única con detalle real (tornillos de cachas, palanca de seguridad, ventana de expulsión). Su silueta tiene algo de facetado en el martillo y el guardamonte.
- Las cotas citadas salen de `docs/catalogo/cotas-publicas.md`, pero el modelo **no es esa réplica**: la longitud del modelo queda `null` (sin verificar) y con bandera. Las dos escalas «convención» existen solo para que los px/mm sean comunes dentro de cada clase (fusiles: 1,64 px/mm; pistolas: 6,43 px/mm).
- Atribución CC BY archivada en el registro (`fuente.atribucion`). CC0 no la exige; se archiva igualmente.

## Cómo se hizo

1. **Licencia en vivo antes de descargar**: ficha de OpenGameArt (`License(s): CC0`) y API pública de Sketchfab (`license.slug`). Descarga a ritmo bajo con el User-Agent identificado (`taller6mm_pipeline.importador.red`). Los hashes de OpenGameArt coinciden con `catalogo/modelos-cc.json`; el del M4A1, con `catalogo/importador-manifiesto.json`.
2. **Limpieza** (`replicas_cc.py`, modo `listar`): se descartan texturas, materiales y UV del archivo, se separan las partes sueltas y se borran por reglas los internos y la munición (Glock: bloques y barra del disparador; M4A1: balas). Solo queda la forma exterior.
3. **Zonas de material** por nombre de malla o por caja normalizada (u atrás-boca, v abajo-arriba, w lado): metal, polímero y, en el AK, madera.
4. **Materiales** de la biblioteca propia (`materiales/biblioteca.py`, bases CC0 de `catalogo/materiales-cc0.json`) con las correcciones de `critico-diseno` del 24-11-2026: metal negro neutro sin rayas, desgaste solo en aristas y de color gris (no blanco), polímeros oscuros (`#101010`-`#161616`, rugosidad 0,6-0,65), madera del AK `#50291A` con veta fina y barniz 0,3, fosfatado en el cañón del M4A1, y cachas de nogal cuadriculadas (relieve procedural en rombos de 1,5 mm) en la 1911, aplicadas por caras exteriores del armazón.
5. **Luz de tres puntos** (`catalogo/replicas-ilustrativas.json`, clave `luz`): principal de área a 45° de azimut y 35° de elevación respecto a la cámara, relleno a un cuarto, dos tiras de contorno detrás y arriba (2x la principal, no 1,5x: su superficie es pequeña), una tercera tira baja y trasera para que las empuñaduras no se pierdan sobre el fondo, panel de reflejo junto a la cámara, mundo 0,025-0,055, AgX «Medium High Contrast», **fondo transparente**.
6. **Render** a 1800 x 1200, 160 muestras, OIDN, lente 90-100 mm: `lateral` (cámara a -Y: boca a la derecha), `lateral-izq` (cámara a +Y: boca a la izquierda) y `tres-cuartos` (37° de azimut, 17° de elevación, encuadre por silueta al 80 %).

## Sobre «lado izquierdo, boca a la derecha»

Con la boca a la derecha del cuadro se ve el **lado derecho** del arma (ventana de expulsión del M4A1 y de la 1911, selector del AK). El lado **izquierdo** real queda con la boca a la izquierda. Para no mostrar un arma especular falsa, se entregan las dos vistas (`lateral` y `lateral-izq`); el tres cuartos de las pistolas enseña el lado derecho en la 1911 y el izquierdo en la Glock (es el que lleva las estrías de la corredera).

## Reglas que se cumplen

- Solo CC0, CC BY y dominio público; nada de SA, NC ni ND.
- Sin marcajes ni logos: se descartan todas las texturas; en los renders a 100 % no se lee texto en la geometría (falta revisión humana).
- Solo la forma exterior de airsoft; nada de internos de armas reales.
- `publicable: false` en todos hasta que un humano revise la procedencia (docs/05 §5): una etiqueta CC no prueba que el subidor tuviera los derechos (fichas de 2010, 2018, 2021 y modelos subidos a Sketchfab).
- Cada imagen debe llevar el aviso «Imagen ilustrativa: forma genérica de un modelo 3D de licencia abierta, sin medidas verificadas. No es la réplica exacta de ninguna marca» (`aviso` en el registro).

## Reproducir

```
python -I -c "import sys; sys.path.insert(0, 'apps/pipeline/src'); from taller6mm_pipeline import replicas_cc; replicas_cc.main()" -- render todos
```

Modos: `listar <id>` (partes y coordenadas), `debug <id>` (zonas en colores), `render <id|todos> [res=1200x800] [muestras=48] [sufijo=-t1] [vistas=lateral,tres-cuartos]`, `sonda <id>` (desgaste en aristas) y `hoja` (hoja de contacto). Los binarios van en `assets-src/raw/modelos-cc/` y los renders en `assets-src/vistas/replicas-cc/`; las dos están ignoradas por git.

## Revisión de `critico-diseno` (25-11-2026) y estado

Notas honestas antes de la segunda pasada de materiales y luz: M4A1 6, AK 5, 1911 4,5, Glock 3,5. Arreglos aplicados después: tres cuartos de la Glock por el lado izquierdo, armazón y empuñadura de la Glock más oscuros con punteado, madera del AK con veta fina y color uniforme, M4A1 con tres acabados (anodizado, polímero y fosfatado), cachas de nogal cuadriculadas en la 1911, tiras de contorno mayores y tercera tira baja. El crítico avisa de un techo de 6-7 con geometría gratuita: la pieza protagonista de cada balda saldrá del frente de fidelidad, no de aquí. La Glock queda **no recomendada como pieza principal** (formas blandas, guardamonte con el disparador fundido, hoyuelo en la empuñadura del modelo original, sin ventana de expulsión).

## Escala entre clases

Cada clase tiene su propio px/mm (fusiles 1,64; pistolas 6,43), anotado en `salidas.px_por_mm_lateral` del registro. Si un pistola y un fusil comparten balda, la web debe componerlos con esos factores: las dos escalas «convención» (AK 880 mm, Glock 200 mm) no están verificadas.
