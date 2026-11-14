# Cuerpo base M4/AR-15 (oleada 1): receptores, pistolete y culata

> Informe del 13-11-2026. Datos: `catalogo/m4-cuerpo-base.json`. Generador: `apps/pipeline/blender/m4_cuerpo.py`.
> Solo airsoft y solo forma exterior: sin mecanismo, sin cotas de mecanizado, sin logos ni números de serie.

## Qué hay

Cinco piezas en GLB (escena en metros, nodo `pieza` y nodos `socket.*`), en `apps/pipeline/salida/m4-cuerpo/` (ignorada por git):

| Pieza | Origen | Triángulos | Sockets | IoU (vista derecha) | Nivel |
|---|---|---:|---|---:|---|
| Receptor superior | Base CC BY | 3.397 | `rail.top`, `handguard`, `lower` | 0,905 (zona de receptores) | T0 |
| Receptor inferior | Base CC BY | 2.406 | `grip`, `stock_tube`, `magazine` | 0,905 (zona de receptores) | T0 |
| Pistolete tipo A2 | Base CC BY | 281 | — | 0,902 | T0 |
| Culata CAR genérica | Base CC BY | 861 | — | 0,645 | T0 |
| Culata de la réplica de Javi | Propia, desde cero | 2.148 | `sling.qd` | 0,968 | T1 candidata |

**IoU del conjunto** (receptores + pistolete + culata, con el visor, el guardamanos y el soporte de pared enmascarados): **0,931** con la culata propia y 0,797 con la CAR. Receptores y pistolete solos: 0,907.

El nivel lo fija `realismo.decidir_nivel` y **ninguna pieza es publicable como 3D**: hay una sola vista licenciada (hacen falta dos con IoU ≥ 0,95) y ninguna cota de fabricante.

## Cómo se hizo

- **Base de forma.** Receptores, pistolete y culata CAR salen de «AR-15 style rifle» de SpatialNeglect, CC BY 4.0 (<https://sketchfab.com/3d-models/ar-15-style-rifle-50d33435445e439c95e3b36e9d4bd798>). La licencia se reverificó el 13-11-2026 en la API pública de Sketchfab. Las piezas derivadas heredan la atribución, que va en `extras` de cada GLB y en el manifiesto.
- **Limpieza.** Se borran el portacerrojo, las balas, la óptica, el GPS, el cargador, la correa, el cañón y el guardamanos. Se borran todas las texturas: los rótulos ficticios del autor iban en ellas. La malla no trae texto en relieve ni número de serie (visto en los renders derecho e izquierdo).
- **Raíl.** Los dientes de la base no cumplen el paso Picatinny (16 mm tras escalar). Se sustituyen por un raíl generado con las cotas de `familias/estandares.py`.
- **Culata propia.** Ningún modelo CC descargado trae la culata que monta la réplica de Javi. Se modela desde cero con el perfil trazado sobre su foto. Por eso partir de cero da aquí mejor parecido (0,968 frente a 0,645).
- **Calibración.** Solo se mueve el registro foto-modelo y un giro de −2,7° del pistolete. La forma de la base no se deforma.

## Escala: confianza baja

Una sola cota con fuente: el paso del raíl Picatinny (10,0076 mm). En la foto, el raíl del receptor mide 16,58 px por paso, es decir, 1,657 px/mm.

La foto **no es ortogonal**: el raíl del guardamanos da 18,6 px por paso, el silenciador se ve un 1,7 % más grande cada 100 px y la escala vertical ajustada es un 7 % mayor que la horizontal. Eso encaja con unos 20° de guiñada. La escala absoluta puede errar un ±10 %; las proporciones entre piezas son las de la base.

## Qué se parece y qué no

- **Se parece:** contorno de los receptores, raíl, alojamiento del botón de empuje, deflector, ventana de eyección con su tapa, pasadores, botón del cargador, guardamonte, cuello del pistolete y perfil completo de la culata propia.
- **No se parece:** el guardamonte de la base es angular y el de la foto es recto; el fondo del pozo de cargador queda tapado por el soporte de pared; la tapa de la ventana está abierta en la base y cerrada en la foto; la palanca de carga de Javi es ambidiestra.
- **Culata propia:** el perfil es fiel a la foto, pero los anchos son estimados y el volumen queda más de bloque que los receptores. Su IoU sale de la misma foto con la que se trazó: no es una comprobación independiente.

## Qué falta

1. Una foto lateral ortogonal con regla y otra vista (trasera o superior) con licencia publicable de cada pieza, para llegar a dos vistas.
2. Cotas con calibre de la réplica de Javi (longitud del receptor, alto del pozo, ancho de la culata).
3. Vista izquierda: selector y retén del cerrojo solo están como los trae la base.
4. Cerrar la tapa de la ventana y enderezar el guardamonte.
5. Revisión de `revisor-fidelidad` y OK de Javi.

## Aviso sobre los ejes

`docs/05` §4 dice «+X boca, +Y arriba, +Z a la izquierda del tirador (mano derecha)». Con +X hacia la boca y +Y arriba, un sistema a derechas deja **+Z a la derecha**. Los GLB salen así, sin espejar: la ventana de eyección queda en +Z. Hay que corregir el texto de `docs/05` o decidir otra convención.

## Reproducir

```bash
blender --background --python apps/pipeline/blender/m4_cuerpo.py -- --renders <carpeta>
```

Opciones: `--ajustar` (reajusta el registro), `--sin-cycles` (solo silueta e IoU), `--culata car` (monta la culata CAR). Salen los renders lateral derecho, lateral izquierdo, perspectiva y trasera (Cycles, 32 muestras, CPU), la superposición `m4_cuerpo_comparacion.png` y `m4_cuerpo_medidas.json`.
