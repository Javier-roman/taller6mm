# apps/pipeline

Pipeline de assets 2D/3D de Taller6mm (docs/05): Python 3.12 con [uv](https://docs.astral.sh/uv/), pytest y ruff.

```bash
uv sync --frozen
uv run ruff check
uv run pytest
```

Desde la raíz, `pnpm verify` ejecuta estos pasos si `uv` está instalado; si no, los salta con un aviso y quedan cubiertos por el CI (job `verify`, en Ubuntu y en Windows, donde uv siempre está instalado). En Windows: `winget install --id astral-sh.uv --exact`.

Política de dependencias: `exclude-newer = "3 days"` en `pyproject.toml`, la misma edad mínima que pnpm.
