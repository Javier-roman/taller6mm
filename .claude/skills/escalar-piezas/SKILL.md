---
name: escalar-piezas
description: Lanza la escalera de calidad de piezas 3D (N1 forma a N5 imagen viva, con métricas objetivas por nivel, cola de trabajo e historial con alerta de regresión) y, si se pide, el subagente mejorador-escalador que eleva la cola sin parar hasta el techo del nivel.
argument-hint: "[nivel 1-5] [grupo: canon|pistolete|mlok] [hasta N]"
disable-model-invocation: true
---

Argumentos: $ARGUMENTS. Detalle en `docs/05-assets-y-fidelidad.md` («Escalera de calidad») y umbrales en `catalogo/escalera-niveles.json`.

1. Mide: `cd apps/pipeline && uv run python -m taller6mm_pipeline.calidad.escalera [--nivel N] [--familia <grupo>] [--hasta N]`. Determinista y sin gastar tokens. Con `--hasta 2` no usa Blender (segundos); N3-N5 dibujan con el Blender portátil de `C:\tools\blender` (varios minutos la primera vez, después usa la caché por hash).
2. Lee `assets-src/calidad/escalera-cola.json` (ignorada por git): cuántas piezas superan cada nivel, la cola del siguiente peldaño (peor primero), las regresiones y los avisos. Dale a Javi el resumen en pocas líneas.
3. Si hay piezas por debajo del techo y no se pidió solo medir, lanza el subagente `mejorador-escalador` (Sonnet) con el nivel y el grupo pedidos. No hagas tú la mejora.
4. Cierra con `uv run python -m taller6mm_pipeline.calidad.escalera --hoja` y pasa `assets-src/vistas/hoja-escalera.png` (filas por familia, columnas N1 → N5) al revisor visual antes de dar nada por bueno. Los renders anteriores quedan en `assets-src/vistas/<grupo>/previo/` para el antes/después.
5. Si imprime `REGRESION`, no sigas: arréglala primero (`--estricto` devuelve el código 2).

Todo es apariencia interna: texturas procedurales propias, sin fotos de terceros ni logos; las piezas siguen en T0 y `publicable_3d=false`.
