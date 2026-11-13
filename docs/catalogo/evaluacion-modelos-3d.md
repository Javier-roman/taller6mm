# Evaluación de modelos 3D de licencia abierta (base de forma exterior)

> Evaluación del 2026-11-13 con descarga y render reales. Manifiesto con hashes y licencias en `catalogo/modelos-cc.json`. Los archivos viven en `assets-src/raw/modelos-cc/` (ignorada por git). Solo se descargó lo de las cuatro fichas de OpenGameArt, una vez por archivo y a ritmo bajo. Esto no es asesoramiento jurídico (docs/09).

## Método

- Licencia leída en la ficha pública antes de descargar: las cuatro dicen **CC0**. Autor, URL y fecha en el manifiesto.
- Importación en Blender 5.2 portátil, sin interfaz. Recuento de triángulos y caja envolvente (bbox) medidos sobre la malla evaluada.
- Render Cycles de 32 muestras en CPU, fondo gris neutro, material gris único (para juzgar la forma, no la textura): lateral ortográfico, perspectiva y **corte longitudinal por el centro** para ver si hay interiores. Las imágenes están en el directorio temporal de sesión, no en el repo.
- Comparación de proporciones solo con `cotas-airsoft.json` (rama `feat/cotas-publicas`): TM M4A1 MWS, longitud cerrada 777 mm y guardamanos RIS 180 mm, ambas «citado» con una sola fuente. No hay cota de alto de ninguna réplica, ni datos de AK o pistolas: eso es «sin dato».
- Las unidades de los archivos no están documentadas: las medidas son relativas y no son milímetros.

## Resultados

| Modelo (autor, CC0) | Formato | Triángulos | Caja (long. × alto × ancho, uds.) | Long./alto | Interiores | Marcajes | Veredicto |
|---|---|---|---|---|---|---|---|
| Low-Poly M4A1 (MallNinjaMax) | FBX, BLEND, PNG | 167 | 0,84 × 0,31 × 0,06 | 2,72 | No, mallas macizas | Textura con emblema de caballo, rótulos y una botella dibujada | **Cubito/descartado** |
| High-poly AK-47 (Lamoot) | OBJ (y BLEND en la ficha) | 30.730 | 8,80 × 2,61 × 0,71 | 3,38 | No, cascarón hueco | Sin textura; sellos en relieve sin texto | **Válido como base de forma** |
| High Poly Glock-18 sin texturas (locarem) | OBJ | 30.648 | 8,84 × 5,29 × 0,93 | 1,67 | Parcial: cañón, cargador y barra del disparador dentro | Sin textura ni texto | **Válido como base de forma** (quitando internos) |
| Low Poly Guns Pack (Quaternius), medido AssaultRifle2_1 | FBX, OBJ, BLEND | 1.930 (rifles: 1.220 a 1.930) | 5,17 × 1,79 × 0,35 | 2,89 | No | Sin texturas | **Solo referencia de volumen** |

## Proporciones frente a una M4 de airsoft

| Dato | TM M4A1 MWS (cotas) | Low-Poly M4A1 | Quaternius AssaultRifle2_1 |
|---|---|---|---|
| Guardamanos / longitud total | 180 / 777 = 0,23 | ~0,22 (sobre render, aprox.) | ~0,22 (sobre render, aprox.) |
| Longitud / alto | sin dato (no hay alto) | 2,72 | 2,89 |
| Longitud total en mm | 777 (culata cerrada) | sin escala real | sin escala real |

La proporción guardamanos/cuerpo coincide a ojo en ambas M4, pero con una sola cota citada de una tienda y medida en píxeles no es evidencia: no autoriza ninguna cota. Para AK y pistola, sin dato.

## Veredicto por modelo

- **Low-Poly M4A1: cubito/descartado.** Con 167 triángulos la culata es una cuña, el receptor y el cargador son bloques, no hay raíl ni detalle, y el guardamanos es un tubo liso. Exactamente lo que Javi no quiere. Además su textura lleva marcajes de terceros: no se publicaría.
- **High-poly AK-47: válido como base de forma.** Silueta correcta y relieve real: cargador curvo acanalado, guardamanos con ranuras, mira, palanca de montaje, gatillo, culata de madera con remates. 30,7 mil triángulos es manejable. Reservas: es un AK-47 real (no una réplica de airsoft concreta; las cotas de la réplica mandan), la fecha es antigua (2010) y hay que revisar procedencia.
- **High Poly Glock-18 sin texturas: válido como base de forma.** Superficies limpias, gatillo, guardamonte, estrías y fondo del cargador bien resueltos. Reservas: lleva cañón, cargador y barra del disparador dentro (hay que borrarlos), es la variante con selector y Glock es marca: se usa solo la forma.
- **Low Poly Guns Pack: solo referencia de volumen.** Rifles reconocibles (raíl, guardamanos con aros, mira, culata telescópica) pero facetados, con menos de 2.000 triángulos. Sirve para comparar volumen y proporción, no como malla 1:1. Los 40 modelos son de la misma familia de estilo; solo se midieron 12 (9 rifles, subfusil, pistola, francotirador) y se miró el render de dos.

## Condiciones antes de usar cualquiera

1. Procedencia: CC0 no prueba que el subidor tuviera los derechos (fichas de 2010 y 2018). Archivar capturas de la ficha y que lo revise un humano (docs/05 §5).
2. Escalar con una cota de la réplica concreta y contrastar con `cotas-airsoft.json`; si no hay cota, no se fija.
3. Borrar internos y marcajes; texturas solo de la biblioteca PBR propia.
4. Pasar la puerta de realismo (`apps/pipeline/.../realismo.py`) y el revisor de fidelidad antes de publicar. Nivel resultante: como mucho T1/T2, declarado tal cual.
5. Son modelos de armas reales: solo se usa la forma exterior para réplicas de airsoft, nunca como pieza regulada (principio 6).
