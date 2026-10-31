---
name: nueva-replica
description: Alta de una réplica o accesorio en el catálogo con ficha técnica citada, ranuras con geometría en mm y asset T0. Nunca inventa datos.
argument-hint: "[marca] [modelo] [variante opcional]"
disable-model-invocation: true
---

Producto: $ARGUMENTS. Sigue `docs/03` (ranuras), `docs/05` (fidelidad) y el esquema Zod de su categoría en `packages/domain`.

1. Empieza por la web oficial del fabricante de la réplica (grupo A de `docs/fuentes/marcas.md`), con la misma diligencia que `/nueva-tienda`. Añade al menos 2 fuentes independientes (tiendas de `docs/fuentes/candidatas.md`, manual). Cita la URL y la fecha de cada dato. Si la réplica tiene licencia de una marca real (grupo B), regístrala como `licencia_oficial`, solo en texto y sin logos.
2. Rellena, según aplique:
   - plataforma y sistema (AEG, GBB, HPA, muelle o CO2) y versión de gearbox;
   - longitud con la culata plegada y extendida, y peso;
   - longitud del cañón interno y rosca de bocacha (14 mm CCW, CW…);
   - raíles (tipo, longitud y posición);
   - tipo de cargador y alojamiento de batería;
   - materiales y colores.
3. Define las ranuras (`slots`) con su interfaz y su geometría en mm desde el origen canónico. Cada valor lleva `source` y `confidence` (`fabricante`, `medido` o `estimado`). Lo desconocido va a `null`, con bandera para que lo complete la comunidad.
4. Genera el asset T0 (plano técnico) y deja el producto en `borrador`.
5. Entrega la ficha, los huecos de datos y la lista de fotos y medidas que hay que pedir a la comunidad para subirlo a T1 o T2.
