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
