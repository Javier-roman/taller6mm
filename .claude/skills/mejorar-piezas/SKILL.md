---
name: mejorar-piezas
description: Lanza el bucle de calidad de piezas 3D (puerta medible, cola de trabajo y hoja de contacto) y, si se pide, el subagente mejorador-escalador hasta que las piezas pasen los mínimos.
argument-hint: "[familia o id opcional] [máx. rondas opcional]"
disable-model-invocation: true
---

Argumentos: $ARGUMENTS. Detalle y umbrales en `docs/05-assets-y-fidelidad.md` (sección «Bucle de calidad») y `catalogo/calidad-minimos.json`.

1. Mide: `cd apps/pipeline && uv run python -m taller6mm_pipeline.calidad.bucle [--familia <f>] [--id <patrón>]`. Es determinista y no gasta tokens. Tarda ~1 minuto (genera las piezas y reensambla los builds; `--sin-ensamblajes` lo acorta).
2. Lee `assets-src/calidad/cola.json` (ignorada por git): cuántas pasan, la cola ordenada de peor a mejor, las regresiones y los huecos de fuentes (p. ej. el kit sin GLB). Dale a Javi el resumen en pocas líneas.
3. Si hay piezas sin pasar y no se pidió solo medir, lanza el subagente `mejorador-escalador` (Sonnet) con la familia y el máximo de rondas pedidos (5 por defecto). No hagas tú la mejora.
4. Cierra con `uv run python -m taller6mm_pipeline.calidad.bucle --hoja` (Blender portátil en `C:\tools\blender`) y pasa la hoja de contacto (`apps/pipeline/salida/calidad/hoja.html`, `hoja-NN.png`) al revisor visual (`revisor-fidelidad`) antes de dar nada por bueno.
5. Si el bucle imprime `REGRESION`, no sigas: arréglala primero.

Las piezas de ramas sin fusionar (tanda 3, AK, pistolas) se incluyen con `--glb <carpeta>` o añadiendo su familia a `catalogo/calidad-minimos.json` cuando se fusionen.
