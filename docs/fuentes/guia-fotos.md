# Guía de fotos propias de réplicas

Las fotos que hace Javi son la vía más limpia para medir y trazar réplicas (T0 → T2) y, con su cesión, para vistas 2D publicables (ADR-0009). Esta guía dice cómo hacerlas y dónde dejarlas. **No hay prisa:** el 3D y los renders propios avanzan sin ellas.

## Dónde dejarlas
`assets-src/raw/_entrada/<marca-modelo>/` (carpeta ignorada por git, nada se sube). Una carpeta por réplica; los nombres de archivo dan igual. Hay una carpeta `EJEMPLO-marca-modelo` de muestra. Cuando haya fotos nuevas, basta decir «hay fotos nuevas».

Revisión automática: `cd apps/pipeline && uv run python -m taller6mm_pipeline.fotos.inventario`. Avisa de resolución baja, desenfoque, ubicación GPS en los metadatos y duplicados, y escribe `inventario.json` junto a las fotos. No modifica ni sube nada.

## Cómo hacerlas
1. **Fondo liso** (cartulina blanca o gris) y **luz suave y difusa** (una ventana; sin flash ni sombras duras).
2. **Vista lateral pura**, el móvil a la altura del centro de la réplica y a ~1 m o más, sin inclinar: es la foto que más sirve para medir.
3. **Regla o medida conocida** (regla de 30 cm o tarjeta bancaria de 85,6 mm) **en el mismo plano** que la pieza.
4. **Más ángulos**: frontal, trasera, arriba, abajo y 3/4 por ambos lados.
5. **Primeros planos**: boca del cañón, guardamanos, receptor, culata, cargador y mira.
6. **Piezas sueltas** si se pueden desmontar: cargador, guardamanos, bocacha, culata.
7. **La caja o la ficha** con marca y modelo exactos.
8. Resolución: la del móvil sin recortar (mínimo ~1500 px en el lado largo). Quita la ubicación GPS si la tienes activada en la cámara.

## Prioridad (las cuatro familias)
Una M4 AEG (la Tokyo Marui M.W.S. ya cuenta), una AK, una Hi-Capa y una Glock.

## Derechos y marcas
- Las fotos hechas por Javi son suyas. Para publicarlas (vistas 2D, modo foto) hace falta una **cesión de derechos al proyecto**; redactarla y revisarla con un abogado antes del lanzamiento (docs/09).
- Logos y marcajes registrados: las fotos con marcas visibles son **referencia interna**. Para publicar, hay que difuminarlos o quitar el marcaje (principio 5).
- Nunca se proyectan fotos como textura de un modelo.
