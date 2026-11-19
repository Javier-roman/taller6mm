# apps/pipeline

Pipeline de assets 2D/3D de Taller6mm (docs/05): Python 3.12 con [uv](https://docs.astral.sh/uv/), pytest y ruff.

```bash
uv sync --frozen
uv run ruff check
uv run pytest
```

Desde la raíz, `pnpm verify` ejecuta estos pasos si `uv` está instalado; si no, los salta con un aviso y quedan cubiertos por el CI (job `verify`, en Ubuntu y en Windows, donde uv siempre está instalado). En Windows: `winget install --id astral-sh.uv --exact`.

Política de dependencias: `exclude-newer = "3 days"` en `pyproject.toml`, la misma edad mínima que pnpm.

## Puerta de realismo

- `taller6mm_pipeline.realismo.decidir_nivel(cotas=…, vistas=…, tiene_malla=…, malla=…)` devuelve el nivel publicable honesto (T0–T3), si el 3D es publicable y los motivos.
- T2 exige IoU de silueta ≥ 0,95 en ≥ 2 vistas con licencia publicable y cotas clave a ≤ 1 % o ≤ 2 mm; T3 además pide verificación física (el marco de familias nunca la da).
- Una vista con una sola pasada es T1; sin vistas, o con una malla que no pasa, es T0 y `publicable_3d = False`.
- Las fotos con licencia no publicable solo son referencia interna y no suben de nivel; una malla «caja» (volumen/bbox > 0,9 sin vaciados) se marca `sospechosa_de_cubo`.
- `explicar(decision)` da el texto «Nivel T0 porque…» para la Trastienda y el CI.

## Cuerpo base M4 (Blender)

`blender/m4_cuerpo.py` (Blender 5.2 sin interfaz; no entra en `pytest`) genera el receptor superior, el inferior, el pistolete y dos culatas a partir de una base CC BY 4.0 y de la foto propia de Javi, exporta los GLB con `socket.*` a `salida/m4-cuerpo/` y mide el IoU de silueta con `validacion.py` y la puerta de realismo. Procedencia y atribución en `catalogo/m4-cuerpo-base.json`; resultados en `docs/catalogo/m4-cuerpo-base.md`.

## Kit esencial M4 (Blender)

`blender/kit_esencial_m4.py` separa piezas sueltas (cargador, bocacha provisional, silenciador, red dot) de modelos CC ya descargados por el importador: quita mallas ajenas y todos los materiales del autor, orienta (+X boca, +Z arriba), escala por UNA cota con fuente (confianza baja) o de forma relativa, añade `socket.*` y exporta a `salida/kit-m4/`. `--modo vistas` dibuja dos vistas por pieza con los sockets marcados. `blender/kit_inspeccion.py` lista las mallas de un GLB. Procedencia y nivel en `catalogo/kit-esencial-m4.json` (`kit_esencial.py` y su test); el guardamanos M-LOK sale del generador paramétrico. Nada es publicable. La culata NIXO se descartó (marca real, brace de pistola, malla abierta) y queda como hueco: pendiente: culata telescópica tipo STR. La bocacha es provisional (no es una A2): hay que rehacerla con el generador paramétrico.

## Oleada 1 por generadores (`familias/oleada1.py`)

Pistoletes (A2, MOE, ergo), guardamanos por tipo (carabina, mid, RIS cuadrado, M-LOK), asa A2, BUIS, empuñadura vertical y palanca de armado, con sockets `socket.*` y GLB determinista. Registro en `catalogo/m4-oleada1-piezas.json` y cobertura en `docs/catalogo/familia-ar-m4.md`. Todo es `es_demo`, T0 sin vistas licenciadas y no publicable. `uv run python -m taller6mm_pipeline.familias.oleada1` regenera los GLB y el registro.

## Ensamblador de builds (`src/taller6mm_pipeline/ensamblador/`)

Encaja las piezas de un build del M4 por sus `socket.*`, calcula las transformaciones en mm, escribe un GLB único del conjunto y un informe JSON. Los builds viven en `catalogo/m4-builds.json` (M4A1 carabina, M4 CQB con RIS, M16A2 con asa): cada pieza es una familia con parámetros (o un GLB del kit) y cada montaje `hijo -> padre` nombra los dos sockets.

```bash
uv run python -m taller6mm_pipeline.ensamblador [--build m4a1-carabina]   # salida/ensamblador/<id>.glb + <id>.informe.json
blender --background --factory-startup --python blender/previsualizar.py -- --lista lista.json   # "mat": "auto", vistas izq y lado
```

- Modos de montaje: `opuestos` (los marcos de los dos sockets se enfrentan: normales opuestas, tangentes alineadas) y `coaxial` (solo la posición sobre el eje; para el bloque de gas sobre el cañón o una pieza sin socket). `deslizar_mm`, `posicion_riel_mm` (centro de la montura medido desde el extremo trasero del raíl, que se mide en la malla), `ranura_riel` (centro de una ranura Picatinny, para el taco de retroceso) y `alinear: origen_comun` ajustan la posición sobre la tangente.
- Veredicto por montaje (`reglas.py`): interfaz de `catalogo/interfaces.json` (incluye el sentido de la rosca), diámetro del collar del bloque de gas frente al cañón, rosca de la tuerca del tubo y que la montura quepa en el raíl. Cada uno lleva motivo, fuente y confianza; una cota desconocida da `sin_datos`, nunca un sí.
- Informe: `colisiones` (solapes por sondeo de 0,5 mm hacia dentro con paridad de rayos; las caras que se tocan no cuentan), `huecos_entre_piezas` (piezas montadas con holgura > 1 mm, precisión ~1 mm) y `huecos_de_datos` (piezas sin malla, sockets ausentes, GLB del kit que falta y cotas `null`).
- Las piezas sin malla (culata telescópica, cargador, red dot) entran como **marcador visual** naranja translúcido en el socket del padre: sus medidas son de dibujo (`es_cota: false`), no datos. Todo el conjunto es T0, `es_demo` y `publicable_3d = false`.
- Hallazgos de los generadores (no se editaron): el asa de armado integrada del receptor superior (`asa_armado`) solapa con la torre del inferior (el asa queda 7 mm sobre el eje y la torre llega a 15 mm), por eso los builds la desactivan; el guardamanos no toca el receptor (no hay tuerca de cañón modelada: hueco de 1 a 6,5 mm); el cañón lleva el tramo roscado a Ø15,6 mm frente al alojamiento Ø14 de la bocacha, así que se monta a tope.

## Bucle de calidad (`src/taller6mm_pipeline/calidad/`)

`uv run python -m taller6mm_pipeline.calidad.bucle [--familia …] [--hoja]` mide todas las piezas con la puerta de `catalogo/calidad-minimos.json`, escribe `assets-src/calidad/cola.json` (peor primero, con fallo y sugerencia) y un historial con alerta de regresión; con `--hoja` dibuja la hoja de contacto en `salida/calidad/`. Detalle y umbrales en `docs/05` §12; skill `/mejorar-piezas` y subagente `mejorador-escalador`.

## Escalera de calidad (`calidad/escalera.py`, `materiales/`)

`uv run python -m taller6mm_pipeline.calidad.escalera [--nivel N] [--familia canon|pistolete|mlok] [--hasta N] [--hoja]` sube cada pieza por cinco peldaños (N1 forma, N2 detalle fino, N3 materiales, N4 desgaste, N5 imagen viva) con métricas objetivas por nivel, cola del siguiente peldaño e historial con alerta de regresión. Los renders (Blender portátil, semilla fija) van a `assets-src/vistas/` (ignorada por git). Detalle en `docs/05` §13; skill `/escalar-piezas` y subagente `mejorador-escalador`.

## Importador de modelos CC (`src/taller6mm_pipeline/importador/`)

Busca modelos ya hechos con licencia abierta (CC0 / CC BY) para una pieza de `catalogo/ar-m4.json`, sin gastar tokens: lo repetitivo lo hace el script. Los términos por pieza están en `catalogo/importador-terminos.json`.

```bash
uv run python -m taller6mm_pipeline.importador meta                  # una vez: metadatos de Objaverse (~600 MB, ignorados)
uv run python -m taller6mm_pipeline.importador buscar --pieza red-dot # top 5 en JSON, sin red
uv run python -m taller6mm_pipeline.importador todo --pieza red-dot silenciador --hojas <carpeta>
```

`todo` busca (nombre, etiquetas, caras), **reverifica la licencia viva en Sketchfab** (1 s entre peticiones, User-Agent `Taller6mmBot`, sin credenciales; descarta borrados y NC/ND/SA), descarga como mucho 3 a `assets-src/raw/modelos-cc/`, mide con Blender (`C:\tools\blender\blender.exe`, un proceso a la vez), genera miniaturas y `<hojas>/<pieza>/hoja.png`, y registra todo en `catalogo/importador-manifiesto.json`. El veredicto «candidato»/«descartado» es solo automático: `publicable` es siempre `false` y el nivel lo decide `realismo.decidir_nivel`.

## Herramientas del piloto de fidelidad

Dependencia de ejecución: `numpy` (fijada). Módulos en `src/taller6mm_pipeline/`:

- `ficha.py`: `Ficha` y `Cota` (mm, fuente, fecha, confianza; lo desconocido es `None` + `desconocido=True`).
- `plano_t0.py`: `generar_plano_svg(ficha)` devuelve el plano T0 en SVG, determinista y con «sin dato» en las cotas `null`.
- `validacion.py`: `iou_silueta`, `binarizar` y `validar(siluetas, cotas)` aplican el criterio T2 (IoU ≥ 0,95 en ≥ 2 vistas; cotas ≤ 1 % o ≤ 2 mm).
- `informe.py`: `generar_informe_html(titulo, resultado, siluetas)` crea un HTML autocontenido con superposición, IoU, deslizador antes/después y tabla de cotas.

## Familias paramétricas (`src/taller6mm_pipeline/familias/`)

Generadores por código de piezas estándar (docs/05 §4 y §6.3): parámetros en mm → sólido con [build123d](https://build123d.readthedocs.io/) 0.13.0 (Apache-2.0, fijado) → GLB propio y determinista (escena en metros, nodo `pieza` y un nodo vacío `socket.<slotKey>` por anclaje, metadatos en `extras`).

| Familia (`id`) | Archivo | Estándar verificado | Cotas del SKU |
|---|---|---|---|
| `rail.picatinny` | `rail_picatinny.py` | MIL-STD-1913: ranura 5,23 mm, paso 10,01, profundidad 3,00, ancho 21,21, plano 15,67, apoyos a 45° | — (solo nº de ranuras) |
| `guardamanos.mlok` | `guardamanos_mlok.py` | M-LOK: ranura 32 × 7 mm, separación 8, radio 2,38 (confianza media) + Picatinny | longitud, diámetro, pared |
| `boca.bocacha`, `boca.silenciador` | `boca.py` | Rosca M14x1 a derechas (CW) o a izquierdas (CCW) | longitud, diámetros, ranuras |
| `culata.tubo` | `culata.py` | Tubo mil-spec 29,16 mm y comercial 29,67 mm; rosca 1 3/16"-16 | longitud, tramo roscado |
| `culata.telescopica` | `culata.py` | **Solo T0** (`motivo_sin_malla`): la forma del cuerpo no tiene cotas verificables | longitud, altura, ancho, pared |
| `cargador.m4` | `cargador_m4.py` | **Solo T0** (`motivo_sin_malla`): curvatura, labios y sección sin fuente pública | largo, ancho, altura |

```bash
uv run python -m taller6mm_pipeline.familias.muestras   # tanda de 40 variantes + informe.html en salida/ (ignorada por git)
```

```python
from taller6mm_pipeline.familias import FAMILIAS

pieza = FAMILIAS["rail.picatinny"].generar({"ranuras": 13})  # barrido: es_demo=True
pieza = FAMILIAS["guardamanos.mlok"].generar({"ranuras_mlok": 5}, ficha=ficha_del_sku)  # cotas del SKU desde la ficha
pieza.glb()
pieza.sha256()
pieza.metadatos()
pieza.ficha()
```

Reglas: las cotas de estándar viven en `estandares.py` con fuente, fecha y confianza; las de cada SKU llegan por una `Ficha` (la clave de la cota es la del parámetro). Si falta una cota crítica, la pieza sale **T0 sin malla** con el parámetro `null`; si falta una no crítica, esa parte no se modela y queda anotada. El `nivel` de cada pieza lo fija la **puerta de realismo** (`realismo.decidir_nivel`, llamada desde `Familia.generar`): sin vistas de referencia licenciadas, una malla es **T0 y `publicable_3d = False`** (queda como candidata), con una vista que pasa es T1 y con dos (IoU ≥ 0,95) y la caja envolvente dentro de tolerancia podría ser T2. **Ninguna familia da T3**: la verificación física (escaneo, CAD oficial o calibre) es externa y no se puede afirmar desde `generar`. Además, una pieza `es_demo`, con cotas pendientes (entran en la puerta como desconocidas), con simplificaciones declaradas (`notas`) o con cotas de confianza baja queda en **T1 como mucho y `publicable_3d = False`** (`_limitar` en `base.py`); por eso hoy ninguna familia llega a T2 y la comparación de la malla con los nominales del propio generador solo prueba coherencia interna, no fidelidad. Las vistas se pasan con `generar(params, vistas=[VistaIoU(...)])`; `construir` debe declarar `dimensiones_nominales_mm` (largo, alto, ancho esperados) y `vaciados` en su `Geometria`. Después queda el `revisor-fidelidad`. Los GLB salen sin optimizar (Meshopt, KTX2 y LODs los pone gltf-transform después). Una familia sin cotas verificables para una forma creíble declara `motivo_sin_malla` y **solo** produce T0 (parámetros, interfaz y cotas para el plano): mejor ninguna malla que una caja de juguete.

**Convención de ejes de los sockets** (fijada en `Socket` y en `rotation` del nodo glTF, probada en `tests/test_familias_sockets.py`): **+Z local = normal de montaje, hacia fuera de la pieza**; **+X local = eje del raíl o de la ranura** (dirección de deslizamiento); +Y local = Z × X. Ejemplos: `rail.top` tiene Z = +Y de la pieza y X = +X; `mlok.side.l` tiene Z = +Z; `mlok.side.r`, Z = −Z; `mlok.bottom`, Z = −Y.

Salud de la malla: `tests/test_familias_malla.py` exige para todas las familias malla cerrada (`Malla.aristas_abiertas() == 0`), volumen positivo y normales hacia fuera; `tests/test_familias_regresion.py` fija caja envolvente, volumen y triángulos por familia. Al renderizar piezas pequeñas en Blender, baja `clip_start` de la cámara (por defecto 0,1 m: recorta una bocacha de 45 mm y la muestra hueca y negra).

### Cómo añadir una familia

1. Verifica las cotas de estándar en una fuente pública y añádelas a `estandares.py` como `Cota` (valor en mm, URL, fecha, confianza). Lo que no puedas verificar va a `PENDIENTES` con valor `None`: no lo estimes.
2. Copia `boca.py` (con cotas opcionales) o `rail_picatinny.py` (con sockets); si no hay cotas para una forma creíble, copia `cargador_m4.py` (solo T0) a `familias/<nombre>.py` y crea una subclase de `Familia` con `id` (`grupo.nombre`, estable), `nombre`, `material`, `requiere`/`ofrece` (o `requiere_de`/`ofrece_de` si dependen de los parámetros) y `estandares`.
3. Declara `parametros` con `Parametro(clave, descripción, tipo, unidad, minimo, maximo)`. Marca `de_sku=True` lo que dependa del producto y `critico=False` lo que pueda faltar sin impedir la geometría. Las validaciones cruzadas van en `comprobar`.
4. Implementa `construir(p)`: sólido en mm con los ejes canónicos (+X boca, +Y arriba, +Z izquierda del tirador), origen en el punto de montaje (documéntalo en el docstring) y devuelve `Geometria(solido, sockets, cotas_derivadas, notas)`. Cada `Socket(slot_key, posicion_mm, interfaz, normal, tangente, extras)` usa las claves de ranura de docs/03 §3.1 y la convención de ejes de arriba. Anota en `notas` toda simplificación.
5. Regístrala en `FAMILIAS` (`familias/__init__.py`) y añade sus variantes a `tanda()` en `muestras.py`.
6. Escribe `tests/test_familias_<nombre>.py` con: cotas del estándar contra la fuente, dimensiones de la malla, parámetros fuera de rango, hash estable, nodos del GLB releído y el caso T0. Añade un caso a `CASOS` en `tests/test_familias_regresion.py`; la malla cerrada y los sockets se comprueban solos al estar en la tanda.
7. Si cambias la geometría de una familia ya publicada, sube su `version` (cambia el `id_variante`). Termina con `uv run ruff check`, `uv run ruff format` y `uv run pytest`.

## Pendiente (revisión de fidelidad)

- **Material del GLB** (`glb.py`): los factores PBR son fijos (negro 0,08, metálico 0, rugosidad 0,6) para cualquier material; un anodizado debería ser metálico y los polímeros no. Falta un mapa `material → PBR` propio de cada familia.
- **Optimización**: los GLB salen sin Meshopt ni LOD, y los más grandes (guardamanos largo, ≈ 264 KB) superan el presupuesto de 250 KB de accesorio (docs/05 §4); hay que pasarlos por gltf-transform.
- **M-LOK en superficie curva**: las ranuras se cortan rectas y planas en tubos redondos u octogonales; la ranura real se adapta a la pared curva.
- **Tubo de culata**: diámetro exterior y rosca son del SKU (el catálogo los deja pendientes); no se usan cifras de AR-15 reales.
- **Unión guardamanos-receptor**: `catalogo/interfaces.json` aún no tiene su id, así que `guardamanos.mlok` no declara `requiere`.

## Cuerpos, cañón, tubo y monturas del M4 (generadores)

`familias/canon.py`, `receptores.py`, `amortiguador.py` y `monturas.py` generan formas exteriores (sin internos) con `build123d`; `familias/oleada1_cuerpos.py` tiene su propia tanda (`FAMILIAS_CUERPOS`) y escribe los GLB en `salida/cuerpos-m4/` y el registro `catalogo/m4-oleada1-cuerpos.json`. Todo es `es_demo` (confianza baja), T0 y no publicable. `detalle.py` graba texto neutro con una fuente de puntos propia.

```bash
uv run python -m taller6mm_pipeline.familias.oleada1_cuerpos --registro ../../catalogo/m4-oleada1-cuerpos.json
```

## Familia AK (generadores)

`familias/ak_formas.py`, `ak_cuerpos.py` (receptor, tapa, pistolete, cargador curvo), `ak_madera.py` (guardamanos, cubre-mano, culatas fija y plegable) y `ak_canon.py` (cañón con bloque de gas y mira, bocas, mira trasera, riel lateral) tienen su registro propio `FAMILIAS_AK` en `ak_piezas.py`, que escribe los GLB en `salida/ak/` y el registro `catalogo/ak-piezas.json`. Todo es `es_demo`, T0 y no publicable; cobertura en `docs/catalogo/familia-ak.md`.

```bash
uv run python -m taller6mm_pipeline.familias.ak_piezas --registro ../../catalogo/ak-piezas.json
```
