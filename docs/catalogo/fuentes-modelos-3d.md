# Fuentes de modelos 3D gratuitos para el cuerpo y la forma exterior

> Investigación del 2026-11-13. Solo se ha leído y documentado: no se ha descargado ningún modelo ni archivo. Esto es un estudio de viabilidad, no asesoramiento jurídico: antes de publicar cualquier asset hay que validar con un abogado de propiedad intelectual (docs/09 y docs/05 §5).

## Resumen ejecutivo

1. **Ninguna fuente gratuita da un cuerpo de réplica de airsoft con medidas fiables.** Lo que hay es arte de videojuego (CC0 o CC-BY) hecho a ojo, y los modelos de armas reales no son la réplica: cambian cotas y piezas.
2. **Las fuentes de uso real son pocas.** OpenGameArt, Quaternius (CC0), itch.io (packs CC0) y un puñado de modelos de Sketchfab con CC0 o CC-BY. Smithsonian es CC0 sin condiciones, pero apenas tiene armas modernas.
3. **Descartadas para este fin**: Thingiverse, Printables, Cults3D, MyMiniFactory y GrabCAD (orientadas a imprimir, licencias por modelo y a menudo NC o de uso privado, y vetan o vigilan armas); TurboSquid gratis, CGTrader y Free3D (licencias de tienda que prohíben redistribuir el archivo).
4. **Recomendación honesta**: usar estos modelos solo como **base de proporción y de mallado exterior** (T0 a T2), nunca como fuente de medidas. Las cotas salen de las fichas y del catálogo propio; el modelo se escala, se corrige y se valida con la puerta de realismo. La vía más limpia sigue siendo modelar la forma propia en Blender con cotas públicas y usar los CC0 como referencia de volumen.
5. **Riesgo principal**: una etiqueta CC0 no prueba que el subidor tuviera derechos (modelos sacados de juegos). Hay que archivar licencia, URL y fecha, y revisar cada modelo uno a uno.

## Tabla comparativa

| Fuente | Licencias útiles | Redistribuir archivo a usuarios | API o descarga masiva | Armas modernas útiles | Veredicto |
|---|---|---|---|---|---|
| Sketchfab | CC0, CC-BY (por modelo); resto no | Sí, con CC0/CC-BY y atribución | Sí (Download API, con inicio de sesión del usuario final) | Pocas; muchas son NC o ND | Usar con filtro estricto de licencia |
| OpenGameArt | CC0, CC-BY (por modelo) | Sí, según la licencia de cada modelo | Sin API pública verificada; descarga masiva no | Varias (AK, M16, M4A1, Glock) | La mejor fuente práctica |
| itch.io (packs) | CC0 si el autor lo declara | Sí, si es CC0 | No | Algunos packs (1911, MP5, AK) | Útil, revisar página a página |
| Quaternius (vía OpenGameArt) | CC0 | Sí | No | 40 armas estilizadas | Útil como volumen, no como medida |
| Smithsonian 3D | CC0 (los marcados) | Sí | Descarga por objeto; sin API verificada | Armas históricas, no modernas | Poco útil para plataformas modernas |
| BlenderKit | CC0 y «Royalty Free» | CC0 sí; Royalty Free no | API para el complemento de Blender | Variable | Solo lo marcado CC0 |
| Wikimedia Commons | Libres (CC0, CC-BY, CC-BY-SA, dominio público) | Según cada archivo | API de MediaWiki | Casi nada (solo STL) | Marginal |
| Blend Swap | CC0, CC-BY, otras | Según cada modelo | No verificado | Algo | Marginal; comprobar que sigue activa |
| Poly Pizza | CC0, CC-BY | Sí | Sí (API con clave gratuita, según guías de terceros) | Estilo low-poly, sin armas reales verificadas | Sin hallazgos útiles |
| GrabCAD | Sin licencia abierta; uso privado | No | No | Piezas CAD, a menudo internos | Descartada |
| Thingiverse | Por modelo (CC) | Según CC, pero prohíbe armas de fuego | API con OAuth | Prohibidas por política | Descartada (tipo de contenido) |
| Printables | Por modelo (CC y otras) | Según licencia | No verificado | Contenido para imprimir | Descartada (tipo de contenido) |
| Cults3D | Por modelo; por defecto uso privado | Normalmente no | No verificado | Contenido para imprimir | Descartada |
| MyMiniFactory | Tienda de uso personal no comercial | No | No verificado | Contenido para imprimir | Descartada |
| TurboSquid (gratis) | Licencia gratuita no comercial | No | No | Abundantes | Descartada |
| CGTrader (gratis) | Licencia propia o CC por modelo | No como archivo suelto | No | Abundantes | Descartada salvo CC0/CC-BY expreso |
| Free3D | Licencias propias, uso personal | No verificado | No | Variable | Descartada |
| Open3DLab | No se encontró información | Desconocido | Desconocido | Desconocido | Sin datos |

## Reglas de lectura

- Solo **mallas visuales exteriores**. Se descarta cualquier archivo que sea un receptor imprimible, un armazón, un plano de fabricación o un modelo con mecanismo interno. Esa regla es dura y manda sobre la licencia.
- Aceptadas: CC0, dominio público y CC-BY (con atribución archivada). No: CC-BY-SA, NC, ND, ni licencias de tienda «royalty free» (prohíben redistribuir el archivo y suelen exigir que no se pueda extraer del producto).
- Un visor 3D que sirve el .glb al navegador **es redistribuir el archivo**: cualquier usuario puede descargarlo. Por eso «royalty free» no basta.

## Fuentes, una por una

### Sketchfab
- **Licencias**: cada modelo declara la suya. Las descargables gratis son Creative Commons; CC0 sin crédito, CC-BY con crédito. Hay etiquetas NoAI propias de Sketchfab, que son reglas de sus términos y no de la licencia CC. Un modelo «CC0» puede figurar como CC-BY por limitación de la web: el «Firearms kit #10 CC0» (autor britdawgmasterfunk) lo explica en su descripción.
- **Redistribución y derivados**: la CC0 y la CC-BY permiten ambas, con atribución en CC-BY. Los modelos de la tienda (de pago) no se pueden redistribuir sueltos.
- **API**: Download API con la condición de que el usuario final inicie sesión en Sketchfab, muestre licencia y autor y cite a Sketchfab. No sirve para nuestro caso de «guardamos el archivo en R2 y lo servimos»; habría que contratar con ellos o descargar a mano modelo a modelo y archivar la licencia. No encontré cláusula explícita sobre almacenamiento en caché ni descarga masiva en la página de guías; no se asume permiso.
- **Útil** (verificado en la ficha):
  - «Firearms kit #10 (CC0)», britdawgmasterfunk, licencia real CC-BY 4.0, 1,3 M de triángulos, rifles y subfusiles con accesorios (miras, empuñaduras, cargadores, bocachas, culatas, guardamanos). URL: https://sketchfab.com/3d-models/firearms-kit--10-cc0-386f0582c28d4dff96da967f42ba20f7. No consta si es solo exterior; con 1,3 M de triángulos habrá que decimar y revisar a mano que no traiga internos.
  - «M4 CQB weapon», unas 5.500 triángulos, pero CC-BY-NC-ND: **no sirve**.
- **Riesgos**: modelos subidos a Sketchfab sacados de juegos con la etiqueta CC cambiada; marcajes en la malla; el volumen NC y ND es mayoritario en armas.
- Términos: https://sketchfab.com/developers/download-api/guidelines y https://sketchfab.com/developers/terms. Consulta: 2026-11-13.

### OpenGameArt
- **Licencias**: CC0, CC-BY 3.0/4.0 y algunas CC-BY-SA y GPL; cada subida elige la suya y se puede etiquetar mal (hay casos de descripción CC-BY con licencia CC0 marcada).
- **Redistribución y derivados**: sí, según la licencia de cada modelo.
- **API o masiva**: no encontré API pública ni permiso de descarga masiva; la web bloquea lectura automática simple (403). Descarga manual, modelo a modelo, y guardar la ficha.
- **Útil** (todos CC0 según su ficha; fecha de la ficha entre paréntesis):
  - **Low-Poly M4A1**, MallNinjaMax (2021): 106 vértices, 167 triángulos, .blend + FBX; cargador separado. URL: https://opengameart.org/content/low-poly-m4a1. Demasiado simple para fidelidad 1:1; sirve de silueta T0.
  - **High-poly AK-47**, Lamoot (2010): .blend y .obj, unos 150.000 polígonos según un comentario. URL: https://opengameart.org/content/high-poly-ak-47. Fecha antigua; no consta si lleva internos.
  - **High Poly Glock-18 (No-Textures)**, locarem (2018): .obj, unos 15.000 vértices según un comentario. URL: https://opengameart.org/content/high-poly-glock-18-no-textures. Es una G18 (selectora), y Glock es marca: usar solo la forma.
  - **M16 Assault Rifle**, DeadDog (2015): .blend, sin recuento. URL: https://opengameart.org/content/m16-assualt-rifle.
  - **Low Poly Guns Pack**, Quaternius (2021): 40 armas, FBX, OBJ y Blend. URL: https://opengameart.org/content/low-poly-guns-pack. Estilizadas.
  - Colección de referencia (CC0, con M16, Micro Uzi, Sten, Lee-Enfield, escopetas): https://opengameart.org/content/cc0-3d-weapons.
- **Hay CC-BY que no entra por separado**: «Ultimate Low Poly Guns» (CC-BY 4.0) se puede usar con atribución, pero no es CC0.
- **Riesgos**: procedencia sin verificar; calidad desigual; texturas con marcajes.
- Términos: https://opengameart.org/content/faq. Consulta: 2026-11-13 (la página de FAQ no se abrió; la licencia de cada modelo se leyó en su ficha).

### itch.io (packs de autores)
- **Licencias**: las declara cada autor en su página.
- **Útil**: «Classic Weapons Pack», Stein Games, CC0, FBX con PNG, «sin logos ni marcas registradas» según el autor, alta poligonización sin LOD. Anuncia AK, MAC-10, MP5, M700, 1911, TEC-9, M14, pero varias figuran como «movidas a Fab», así que el contenido actual es incierto. URL: https://stein-indie.itch.io/classic-weapons-pack. Otros packs CC0 (chilly_durango «Low Poly Gun Models», gintoki1234 «12 Low Poly Guns») salieron en búsquedas pero no se abrieron: sin verificar.
- **Riesgos**: los packs que pasan a Fab quedan bajo licencia de tienda de Epic, que no es CC0.
- Términos: la licencia es la de cada página. Consulta: 2026-11-13.

### Smithsonian 3D
- **Licencias**: los objetos marcados «CC0» están en dominio público a efectos de copyright, aptos para uso comercial sin atribución; los marcados «usage conditions» no. CC0 no cubre derechos de terceros (marcas, retratos).
- **Descarga**: por objeto desde 3d.si.edu (OBJ o glTF). No verificada una API pública para 3D.
- **Útil**: de museo, escaneado, armas históricas. No encontré plataformas modernas M4/AK/MP5. Utilidad baja para este fin. «David Livingstone's gun» salió en búsqueda sin poder comprobar licencia.
- **Riesgos**: escaneos con textura fotográfica (referencia, no publicar sin revisión), sin relación con réplicas de airsoft.
- Términos: https://www.si.edu/termsofuse y https://www.si.edu/openaccess/faq. Consulta: 2026-11-13 (no se leyó el texto de términos completo).

### BlenderKit
- **Licencias**: «Royalty Free» y CC0. Royalty Free no permite revender el modelo tal cual ni en pack; la condición real para nosotros es que servir el archivo extraíble a usuarios es redistribuirlo. CC0 sí.
- **API**: el complemento de Blender usa su API; el uso masivo no está permitido por defecto y no lo he verificado.
- **Útil**: filtrar por CC0. No se comprobó ningún modelo concreto de arma.
- Términos: https://www.blendkit.com/docs/licenses/ (la dirección antigua redirige). Consulta: 2026-11-13.

### Wikimedia Commons (modelos 3D)
- **Formato**: Commons solo admite .stl; texturado y glTF no. No hallé categoría útil de armas modernas.
- **Licencias**: libres, incluidas CC-BY-SA (no la admitimos). Por archivo.
- **Útil**: marginal. Término: https://commons.wikimedia.org/wiki/Commons:3D. Consulta: 2026-11-13 (resultados de espejo; verificar en el sitio oficial).

### Blend Swap
- Biblioteca de .blend con CC0, CC-BY y otras. En las búsquedas no salió ninguna página verificable de armas, así que no cito ejemplos. No consta que el sitio siga activo y mantenido: comprobar antes de depender de él. Consulta: 2026-11-13.

### Poly Pizza
- Según guías de terceros: unos 10.000 modelos low-poly, sobre todo CC0 y CC-BY, API con clave gratuita. No salió ninguna arma real verificada. Sin hallazgos útiles. Términos: https://poly.pizza/docs. Consulta: 2026-11-13 (no abierto; datos de terceros).

### GrabCAD (Community)
- Descartada. Su ayuda dice que los modelos son «generalmente para uso privado»; el uso comercial exige permiso explícito del autor, y si no responde, no se puede usar. Las condiciones del sitio permiten uso propio y no comercial. Tampoco hay licencia abierta ni derecho a redistribuir. Además el contenido son piezas CAD con mecanismos.
- Términos: https://help.grabcad.com/article/246-how-can-models-be-used-and-shared y https://grabcad.com/terms. Consulta: 2026-11-13.

### Thingiverse
- Descartada por tipo de contenido. Cada «cosa» lleva licencia CC por modelo, pero el sitio prohíbe subir armas de fuego, sus componentes y accesorios letales, con detección automática. Lo que haya de armas es o está retirado o es justo lo que no admitimos (archivos para imprimir). No se verificó el texto de los términos de la API. Consulta: 2026-11-13. Términos: https://www.thingiverse.com/legal/terms-of-service.

### Printables
- Descartada por tipo de contenido. El modelo es de licencias elegidas por el autor (CC, GNU, BSD, Apache, CERN OHL, licencia de uso comercial); sus términos prohíben archivos que sirvan de instrucciones para fabricar objetos restringidos por ley y no hablan de armas por nombre. Archivos pensados para imprimir.
- Términos: https://www.prusa3d.com/page/printables-com-terms-of-service_231249/. Consulta: 2026-11-13.

### Cults3D
- Descartada. Cada diseño lleva su licencia; por defecto es de uso privado, y hay licencias NC. Contenido para imprimir. No encontré su política de armas. Licencias: https://cults3d.com/en/licenses. Consulta: 2026-11-13 (páginas leídas solo en otros idiomas).

### MyMiniFactory
- Descartada. Los archivos de la tienda son de uso personal no comercial estricto. Sin política de armas localizada. Términos: https://www.myminifactory.com/pages/object-licensing. Consulta: 2026-11-13.

### TurboSquid (gratis)
- Descartada. Los modelos gratuitos son de uso no comercial y no se pueden mejorar a licencia comercial; sus licencias prohíben poner el modelo a disposición de usuarios finales. Prohíbe los modelos de armas de fuego imprimibles. Términos: https://www.turbosquid.com/licensing y https://www.turbosquid.com/help/en/articles/9937531-turbosquid-s-policy-on-mature-and-other-prohibited-content. Consulta: 2026-11-13.

### CGTrader (gratis)
- Descartada, salvo un modelo con CC0 o CC-BY declarada y comprobada. La licencia estándar permite usar el modelo dentro de un producto, no redistribuirlo como archivo suelto. Es habitual que un modelo gratuito diga «editorial» o lleve propiedad intelectual representada. Términos: https://help.cgtrader.com/hc/en-us/articles/360015122437-Can-I-commercially-use-a-free-model. Consulta: 2026-11-13.

### Free3D
- Descartada. Licencias propias de uso personal o «royalty free» sin derecho a pasar el archivo original. La web de términos devolvió 403 y no se pudo leer: https://free3d.com/terms-conditions. Consulta: 2026-11-13.

### Open3DLab
- No se encontró información de licencias ni de política. No se puede recomendar sin leer sus términos.

### Candidatas que no estaban en la lista
- **Fab (Epic)**: absorbe packs de otras tiendas; sus licencias son de tienda, no CC0. Descartada para redistribuir.
- **Kenney** y **Quaternius** directamente: CC0; sin armas reales. Quaternius ya aparece vía OpenGameArt.

## Cómo calibrar un modelo de forma a las medidas de una réplica de airsoft

Un modelo de arma real no es la réplica de airsoft: cambian longitudes, grosores y piezas (cañón exterior, punta naranja, hop-up, guardamanos, culata en réplicas de resorte y eléctricas). Por eso el modelo gratuito es una **base de forma**, nunca la fuente de las cotas. El nivel resultante se declara tal como es (T0 a T2, docs/05 §2).

1. **Verificar licencia y procedencia.** Abrir la ficha, copiar licencia, autor, URL y fecha a un manifiesto en `assets-src/` con estado `cc0` o `cc_by` (docs/05 §5). Si hay duda sobre si el autor tenía derechos (modelo calcado de un juego), se descarta.
2. **Comprobar que es solo exterior.** Revisar a mano que la malla no trae mecanismo interno, receptor completo ni piezas funcionales. Si las trae, se borran o se descarta el modelo entero.
3. **Escalar con una cota conocida.** Fijar la longitud total (o la del cañón, o la del cargador) de la ficha de la réplica concreta, en mm, y escalar de forma uniforme. Anotar la cota usada.
4. **Comparar con el resto de cotas.** Contrastar con `catalogo/cotas-airsoft.json`. **Ese archivo todavía no existe en el repositorio** (en `catalogo/` solo hay `plataformas.json`, `familias.json` e `interfaces.json`); hay que crearlo antes de esta fase, con cada cota y su fuente. Las desviaciones se corrigen con edición no uniforme del mallado en las zonas afectadas, no estirando todo el modelo.
5. **Quitar marcas y números de serie.** Eliminar logos, marcajes («trades») y números de serie de la geometría y de las texturas. No se proyecta ninguna textura ajena: se aplican los materiales PBR propios (docs/05 §8). Se dejan «zonas de calcomanía» para cuando haya permiso de la marca.
6. **Fijar las interfaces.** Alinear los puntos de unión (carril, rosca del cañón, cargador) con el registro de interfaces (docs/05 §11.2) para que las piezas encajen sin fusionar combinaciones.
7. **Validar con la puerta de realismo** (`apps/pipeline/src/taller6mm_pipeline/realismo.py`). Debe dar un nivel publicable honesto y no aceptar cubos ni mallas de relleno. Si no alcanza el nivel, se publica con el nivel real o no se publica.
8. **Registrar la atribución.** Si es CC-BY, guardar el texto de crédito y mostrarlo en la ficha del modelo.

## Riesgos transversales

- **Procedencia**: una etiqueta CC0 o CC-BY no sustituye comprobar quién es el autor. Archivar capturas de la ficha el día de la descarga.
- **Marcas**: las formas de M4, AK, Glock o 1911 son corrientes, pero los nombres y logos son de marca; se usa nombre genérico de plataforma salvo permiso.
- **Medidas**: ningún modelo gratuito trae cotas contrastadas; las cotas vienen de fichas y del catálogo propio.
- **Cambios de licencia**: las fichas pueden editarse y los packs pueden pasar a tiendas; guardar la licencia vigente el día de la descarga.
- **Seguridad**: cualquier archivo con receptor, planos o mecanismo se rechaza aunque su licencia sea abierta.
