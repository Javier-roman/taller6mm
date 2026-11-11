# Piloto de fidelidad: Tokyo Marui M.W.S. (guía de fotos y medidas)

Réplica de Javi, en su casa. Las fotos y medidas propias son lo mejor que hay: son suyas, sin reserva de IA ni permisos, y se pueden usar para modelar. Las marcas («trades») de Tokyo Marui salen en las fotos, pero el modelo no las lleva (docs/05 §5). Las fotos se guardan en `assets-src/raw/tokyo-marui-mws/` (ignorado por git) y de ellas solo se sube a git un manifiesto.

## Antes de empezar
- Cargador fuera, **sin gas** y sin bolas en la recámara. Gafas puestas por si acaso.
- Dime la **variante exacta** (M4A1 MWS, CQB-R, Block 2…) y las **mejoras** que tiene (mira, culata, guardamanos, empuñadura). Cada pieza que no sea original se anota aparte.

## Fotos (móvil, cámara trasera, sin filtros ni retoque)
- **Luz**: difusa (día nublado junto a una ventana) y sin flash. **Fondo** liso y neutro (una sábana o cartulina).
- **Cámara**: perpendicular al centro de la réplica, a su altura, **desde lejos y con zoom 2×–3×** para reducir la perspectiva. Réplica apoyada o colgada, sin moverla entre fotos.
- **Escala en cada foto**: una regla de 30 cm o 1 m pegada al plano de la réplica. Lo mejor es una hoja con marcadores ArUco impresa (la preparo yo; se mide su lado real con la regla).
- Vistas, una foto de cada: **izquierda, derecha, arriba, abajo, frente (boca) y trasera (culata)**.
- **Detalles** (una foto cada uno, cerca y de frente): raíl superior, guardamanos, pistolete, culata en cada posición, boca y apagallamas, cargador (de lado y por debajo), selector y palanca de armado, mira y visor.
- Formato original (HEIC o JPG), todo en una carpeta. No las pases por apps que las recompriman.

## Medidas (calibre o regla, en mm; anota «no he podido» antes que estimar)
1. Longitud total con la culata cerrada y abierta en cada posición.
2. Longitud del cañón exterior y de la boca (rosca: ¿14 mm anti-horario?).
3. Guardamanos: longitud, diámetro o sección, y nº de ranuras del raíl.
4. Raíl superior: longitud y nº de ranuras.
5. Alto del cuerpo (receptor) y del conjunto con el cargador puesto.
6. Cargador: longitud, ancho y grosor.
7. Peso de la réplica (báscula de cocina) con y sin cargador.

## Qué hago yo con ello
- Ficha con cada cota y su **fuente y confianza** (medida propia = alta). Plano T0 con cotas y modelo T2 en Blender guiado por esas medidas, con piezas intercambiables.
- Compruebo contra la ficha oficial de Tokyo Marui (su web no tiene reserva de IA; leo primero sus condiciones, que están en japonés) y mido el solape de silueta (IoU) por vista.
- Los resultados y el coste real irán al informe del piloto.
