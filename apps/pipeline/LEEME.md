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
- T2 exige IoU de silueta ≥ 0,95 en ≥ 2 vistas con licencia publicable y cotas clave a ≤ 1 % o ≤ 2 mm; T3 además pide verificación física.
- Una vista con una sola pasada es T1; sin vistas, o con una malla que no pasa, es T0 y `publicable_3d = False`.
- Las fotos con licencia no publicable solo son referencia interna y no suben de nivel; una malla «caja» (volumen/bbox > 0,9 sin vaciados) se marca `sospechosa_de_cubo`.
- `explicar(decision)` da el texto «Nivel T0 porque…» para la Trastienda y el CI.

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

Reglas: las cotas de estándar viven en `estandares.py` con fuente, fecha y confianza; las de cada SKU llegan por una `Ficha` (la clave de la cota es la del parámetro). Si falta una cota crítica, la pieza sale **T0 sin malla** con el parámetro `null`; si falta una no crítica, esa parte no se modela y queda anotada. El `nivel` de cada pieza lo fija la **puerta de realismo** (`realismo.decidir_nivel`, llamada desde `Familia.generar`): sin vistas de referencia licenciadas, una malla es **T0 y `publicable_3d = False`** (queda como candidata), con una vista que pasa es T1, con dos (IoU ≥ 0,95) y la caja envolvente dentro de tolerancia es T2, y solo `verificado_fisicamente=True` da T3. Las vistas se pasan con `generar(params, vistas=[VistaIoU(...)])`; `construir` debe declarar `dimensiones_nominales_mm` (largo, alto, ancho esperados) y `vaciados` en su `Geometria`. Después queda el `revisor-fidelidad`. Los GLB salen sin optimizar (Meshopt, KTX2 y LODs los pone gltf-transform después). Una familia sin cotas verificables para una forma creíble declara `motivo_sin_malla` y **solo** produce T0 (parámetros, interfaz y cotas para el plano): mejor ninguna malla que una caja de juguete.

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
