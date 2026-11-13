# Fuentes 3D profundas: modelos ya hechos de M4/AR-15 y accesorios

> Investigación del 2026-11-13. Complementa `docs/catalogo/fuentes-modelos-3d.md` (lo obvio ya está allí: OpenGameArt, Quaternius, Sketchfab, itch.io, Thingiverse...). Aquí solo lo que se encontró escarbando. Esto no es asesoramiento jurídico: antes de publicar cualquier asset hay que validar con un abogado de propiedad intelectual (docs/09, docs/05 §5).

## Resumen ejecutivo

1. **Sí existe lo que buscábamos: el dataset Objaverse 1.0 (Hugging Face) es un espejo de unos 700.000 modelos de Sketchfab con licencia CC-BY y 3.465 CC0, con metadatos descargables sin cuenta.** Cribando solo por nombre y etiquetas salen unos 575 candidatos CC-BY de M4/AR-15/M16, accesorios y similares (cero CC0 de armas). Es la mina más rica que he encontrado.
2. **Evaluados 8 modelos con render propio: 5 sirven como base de forma y 3 como referencia.** El mejor fusil completo es «AR-15 style rifle» de SpatialNeglect (30.394 triángulos, CC BY 4.0, 12 mallas separadas); el mejor kit de accesorios, «M4A4 carbine pbr» de javadbayat (supresores, miras, empuñaduras, culatas, cargadores despiezados).
3. **Trampa grave: las licencias de Objaverse son una foto de 2022.** De 8 modelos mirados en la API viva de Sketchfab, uno ha pasado a NC-ND, otro a NC y dos han sido borrados. Hay que **reverificar la ficha viva el día de la descarga** y archivarla.
4. **Procedencia y marcas**: muchos modelos sacados de juegos llevan la etiqueta CC-BY puesta por quien los subió (uno de los candidatos dice «Credit: TastyTony»); casi todos llevan logotipos o rotulado en malla o textura. Son una **base de forma (T0 a T2)**, nunca fuente de cotas ni activos publicables sin limpiar y sin revisión legal. Los modelos de Sketchfab tampoco se descargan por API sin inicio de sesión del usuario (ver el doc anterior); la vía sin cuenta es la copia de Objaverse.
5. **Recomendación honesta**: usar 2 o 3 de estos fusiles como volumen de partida y como contraste visual del modelado propio, y el kit de javadbayat para el catálogo de accesorios; el modelado propio con cotas públicas sigue siendo la vía limpia para fidelidad 1:1. No hay nada CC0 de calidad.

## Tabla de fuentes

| Fuente | Licencia verificada de los assets | M4/AR-15 y accesorios exteriores | Calidad | Veredicto |
|---|---|---|---|---|
| Objaverse 1.0 (HF `allenai/objaverse`) | Por objeto: CC-BY 704.846, CC0 3.465, BY-SA 15.399, BY-NC 24.326, BY-NC-SA 50.723 (de 798.759). El dataset en sí es ODC-By | Unos 575 CC-BY por nombre/etiqueta (M4, M16, AR-15, supresores, miras, empuñaduras); 0 CC0 de armas | Muy variable, de 1.000 a 1,4 M de triángulos; etiquetas viejas | Mejor mina; reverificar cada ficha |
| Sketchfab (API de búsqueda pública) | CC BY por modelo; muchos listados | Decenas por término, p. ej. 21 «m4a1» y 21 «ar-15» descargables CC-BY | Igual que arriba | Útil para encontrar; la descarga requiere sesión |
| Poly Pizza | CC BY 3.0 (ficha de «M4 Carbine»); robots pide `Crawl-delay: 10` | «M4» (Kristian M) y «M4 Carbine» (AdamKokrito), dos supresores («suppressor», «silencer»), mira | Muy baja (1.164 triángulos) | Solo siluetas T0 |
| itch.io, «PSX style M4A1» de Plewr | CC0 declarada en la ficha, GLB de 1,8 MB, «sin IA generativa» | M4A1 estilo PS1 | Baja; no descargado | Silueta T0; ficha sin recuento de polígonos |
| Summer Engine (tienda de assets) | Fichas «CC0 1.0», autor goldenranger915, «Handmade» | Una M4A1 de 0,86 m | No evaluada (sin enlace directo al archivo) | Pendiente; tienda nueva, comprobar términos |
| GitHub (repos) | Por repositorio; casi todo código | Solo `petroulacl/fps-asset-kit` (CC0 según su README, 20 armas «flat»), copias de OpenGameArt | Estilizada | Sin aportación nueva |
| ABC dataset (CAD de Onshape) | «El copyright pertenece a sus creadores», remite a los términos de Onshape; sin licencia abierta | CAD de piezas, no de réplicas; incluye mecanismos | CAD | Descartada |

## Candidatos evaluados (8, renders en el scratchpad de la sesión)

Los binarios están en `assets-src/raw/modelos-cc/` (ignorada por git). El manifiesto es `catalogo/modelos-cc-2.json`, con URL, autor, licencia, atribución, sha256 y triángulos. Renderizado con Blender 5.2 (Cycles, 32 muestras, CPU), vista lateral y en perspectiva.

| Modelo | Autor | Licencia | Tris | Veredicto |
|---|---|---|---|---|
| AR-15 style rifle | SpatialNeglect | CC BY 4.0 | 30.394 | **Válido como base de forma** |
| AR-15 | Se_Oscar_Ya | CC BY 4.0 | 60.412 | **Válido como base de forma** |
| M16A2/M4/AR-15-automatic rifle | Drus | CC BY 4.0 | 67.596 | **Válido como base de forma** |
| M4A4 carbine pbr (kit) | javadbayat | CC BY 4.0 | 75.658 | **Válido como base de forma** (accesorios) |
| AAC M4-2000 Rifle Suppressor | Motion. | CC BY 4.0 | 45.056 | **Válido como base de forma** (supresor genérico) |
| ACOG Scope | GC_3D_ART | CC BY 4.0 | 71.178 | Solo referencia |
| Daniel Defence vertical foregrip | NIXO | CC BY 4.0 | 73.198 | Solo referencia |
| M4 Carbine | AdamKokrito (Poly Pizza) | CC BY 3.0 | 1.164 | Solo referencia |

- **SpatialNeglect AR-15**: carabina tipo M4 completa con guardamanos redondo, cargador, culata y ACOG; proporciones muy creíbles. Trae mallas de cerrojo, portacerrojo, asistente de cierre, cinturón de balas y GPS: hay que **borrar todo lo interno** (regla de solo exterior). El ACOG lleva logotipo en la textura; la ficha dice que los logos reales se sustituyeron por ficticios.
- **Se_Oscar_Ya AR-15**: fusil con guardamanos de carriles, supresor, mira de punto rojo con magnificador, empuñaduras y culata moderna; una sola malla y limpia, hay que partirla en piezas a mano. Marcas visibles en la textura.
- **Drus M16A2/M4**: 67 mallas separables (cañón, guardamanos, asa de transporte, culata, cargador). Bayoneta y visor que se descartan; contiene piezas de mecanismo y rotulado estarcido.
- **javadbayat kit**: el único que da todo un catálogo de accesorios despiezado (culatas tipo brace, dos supresores, cuatro miras, tres empuñaduras, bípode, cargadores de 30 y de tambor). 55 MB y texturas oxidadas inservibles; rotulado de marcas.
- **Motion. supresor**: tubo liso, una malla limpia sin texto; el nombre del modelo cita un producto, que no se reutiliza.
- **ACOG y empuñadura DD**: calidad alta pero con logotipo grabado en la geometría; quitarlo exige remodelar, así que sirven de referencia de volumen.
- **AdamKokrito**: silueta facetada correcta pero sin detalle; sirve de comprobación de escala, no de base.

## Descartadas o no aprovechables

| Fuente / modelo | Motivo |
|---|---|
| Kelisei Ventura «M4 Carbine with Attachment Set» | CC-BY en Objaverse, **CC BY-NC-ND en la ficha viva**: licencia cambiada |
| Lokeig «AR15 Rifle» | CC-BY en Objaverse, **CC BY-NC** hoy |
| Erik «M4 Carbine Texturless», Rebel «EOTECH Holosight» | Borrados de Sketchfab (404): licencia no reverificable |
| Objaverse BY-SA (15.399), BY-NC y BY-NC-SA | Licencias no admitidas (SA, NC) |
| Objaverse-XL | No explorado a fondo: es de 10 M de objetos de varias fuentes (parquet con columna de licencia, sin nombres); el espejo de Sketchfab ya está cubierto por Objaverse 1.0 |
| ABC dataset | Sin licencia abierta; CAD de piezas con mecanismos |
| `guillaumef/gun-silencer`, `HYBRIDARMORY/MOSQUITO` (GitHub) | Archivos para imprimir (GPL y «other»), no mallas visuales |
| Juegos de código abierto (Xonotic, Unvanquished, OpenArena, Warsow, Cube 2, Tremulous) | **No verificado en esta pasada**: de memoria sus assets son GPL o CC-BY-SA (no admitidas) y sin M4/AR-15 modernos. Confirmar antes de descartar de forma definitiva |
| Kenney, Poly Haven, ambientCG | **No verificado**: de memoria no tienen fusiles tipo AR-15 (Kenney tiene pistolas láser estilizadas CC0) |
| Fusion 360 Gallery | **No verificado**: de memoria es de investigación no comercial; la página de licencia dio 404 |
| Internet Archive, Zenodo, Smithsonian, Commons 3D (pistas de Gemini) | No se profundizó: sin hallazgos nuevos; sin confirmar |

## Cómo seguir

1. **Elegir 2 o 3 fusiles** (SpatialNeglect, Se_Oscar_Ya y Drus) y pasarlos por la puerta de realismo y la limpieza: borrar internos, balas, bayoneta, visor y texto. Archivar la ficha viva (captura) con fecha.
2. **Despiezar el kit de javadbayat** y alinear cada accesorio con `catalogo/interfaces.json`.
3. **Volver a Objaverse** con un script de criba solo de metadatos (ya hay 575 candidatos por nombre) y filtrar por triángulos (5.000 a 80.000), un autor con varios modelos de calidad y la ficha viva en CC-BY. Ritmo bajo y User-Agent identificado.
4. **Pendiente**: confirmar las fuentes marcadas «no verificado» (juegos libres, Kenney, Poly Haven, Fusion 360) y los términos de Summer Engine.
5. **Legal**: preguntar a un abogado si servir un `.glb` CC-BY que viene de un juego (aunque el autor lo haya subido con CC-BY) tiene riesgo de marca o de procedencia; mientras tanto, nada sale del repositorio privado de assets.
