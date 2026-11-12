# apps/pipeline

Pipeline de assets 2D/3D de Taller6mm (docs/05): Python 3.12 con [uv](https://docs.astral.sh/uv/), pytest y ruff.

```bash
uv sync --frozen
uv run ruff check
uv run pytest
```

Desde la raíz, `pnpm verify` ejecuta estos pasos si `uv` está instalado; si no, los salta con un aviso y quedan cubiertos por el CI (job `verify`, en Ubuntu y en Windows, donde uv siempre está instalado). En Windows: `winget install --id astral-sh.uv --exact`.

Política de dependencias: `exclude-newer = "3 days"` en `pyproject.toml`, la misma edad mínima que pnpm.

## Herramientas del piloto de fidelidad

Dependencia de ejecución: `numpy` (fijada). Módulos en `src/taller6mm_pipeline/`:

- `ficha.py`: `Ficha` y `Cota` (mm, fuente, fecha, confianza; lo desconocido es `None` + `desconocido=True`).
- `plano_t0.py`: `generar_plano_svg(ficha)` devuelve el plano T0 en SVG, determinista y con «sin dato» en las cotas `null`.
- `validacion.py`: `iou_silueta`, `binarizar` y `validar(siluetas, cotas)` aplican el criterio T2 (IoU ≥ 0,95 en ≥ 2 vistas; cotas ≤ 1 % o ≤ 2 mm).
- `informe.py`: `generar_informe_html(titulo, resultado, siluetas)` crea un HTML autocontenido con superposición, IoU, deslizador antes/después y tabla de cotas.
