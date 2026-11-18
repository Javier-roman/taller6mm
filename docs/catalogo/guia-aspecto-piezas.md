# Guía de aspecto de las piezas: cómo se ve una pieza viva

Para el «escalador de calidad» (`apps/pipeline/.../calidad`) y para quien escriba materiales. Hoy los modelos 3D se ven planos: poco detalle, poco contraste y sin textura. Esta guía fija **reglas concretas y medibles**. No toca `calidad/escalera.py` ni `materiales/`: solo da los números que esos módulos pueden consumir.

Cómo leerla. Cada cifra lleva una etiqueta de origen:
- **[medido]**: calculado en esta investigación sobre los mapas 1K de `catalogo/materiales-cc0.json` (albedo y rugosidad medios con Pillow). Es un dato de partida, no una norma.
- **[ficha]**: lo dice la ficha del fabricante (`docs/catalogo/cotas-publicas.md`).
- **[foto]**: observado en las fotos de `catalogo/referencias-cc.json` (campo `observaciones`).
- **[convención]**: práctica habitual de materiales PBR y estudio de producto, **no verificada aquí contra una fuente citada**. El escalador debe tratarla como hipótesis y ajustarla con renders.

Todo lo medible se calcula sobre un render de la pieza con iluminación de estudio fija (sección 7), no sobre la geometría.

## 1. Biblioteca base: qué material para cada acabado

Origen: `assets-src/materiales-cc0/` (CC0; ignorada por git). Los nombres `mat.*` son los de `docs/05 §8`. «Albedo» en sRGB 0-255 y entre paréntesis su valor lineal aproximado.

| Material de la biblioteca | Base CC0 (1K) | Albedo medio [medido] | Rugosidad media [medido] | Metálico [medido] | Rol |
|---|---|---|---|---|---|
| `mat.anodizado_negro` | ambientCG Metal027 | 46,45,53 (0,027) | 0,65 | 1,0 | cuerpos mate de óptica, guardamanos, receptores |
| `mat.parkerizado` | ambientCG Metal038 | 96,97,98 (0,117) | 0,37 | 1,0 | acero gris con microrrayado: cañón exterior, tornillería de acero |
| `mat.acero_pavonado` | ambientCG Metal063 | 111,110,107 (0,156) | 0,13 | 0,96 | acero oscuro y brillante: pistolas, correderas |
| `mat.aluminio_desgaste` | ambientCG Metal050C | 245,246,245 (0,91) | 0,24 | 1,0 | aristas desgastadas que dejan ver metal desnudo |
| `mat.polimero_grano` | ambientCG Plastic012A | 44,43,41 (0,025) | 0,40 | 0 | empuñaduras, cuerpos y cargadores de polímero |
| `mat.goma` | ambientCG Rubber004 | 42,43,50 (0,023) | 0,59 | 0 | culatines, fundas, almohadillas |
| `mat.nogal` / `mat.madera_oscura` | Poly Haven walnut_veneer, dark_wood; ambientCG Wood051 | Wood051: 65,52,46 (0,053 / 0,034 / 0,027) | 0,54 | 0 | culatas y guardamanos de madera (AK) |
| máscara de desgaste de pintura | ambientCG PaintedMetal004 | (no se usa su color rojo) | 0,15 | 0,09 | solo la forma de los desconchones, como máscara |
| máscara de suciedad | ambientCG Fingerprints006, SurfaceImperfections013 | 11 / 29 | 0,007 / n/d | n/d | huellas y arañazos sobre vidrio y lentes: se mezcla en la rugosidad, no en el color |

Vidrio y lentes: ninguna biblioteca CC0 consultada trae un «vidrio» listo (en PBR el vidrio es un parámetro, no una textura). Regla: transmisión alta, rugosidad base 0,02-0,05 [convención] y la máscara de suciedad de arriba para romper el reflejo.

Se descartó el color de **PaintedMetal004** (rojo, 247,61,60) y de las otras bases de color llamativo: de la biblioteca se toma la **estructura** (grano, rayado, desconchones) y el color lo fija el material propio. La textura final siempre sale de la biblioteca, nunca de una foto (regla de `.claude/rules/assets.md`).

## 2. Albedo y rugosidad: rangos admitidos

1. Un negro no es 0. El albedo de un material negro debe quedar entre sRGB 30 y 55 (lineal 0,013-0,038) [convención]; los negros medidos arriba (42-46) caen dentro. Un negro puro (<20) hace desaparecer la forma y es la causa nº 1 del aspecto plano: el escalador lo marca como fallo.
2. Ningún albedo sin metal supera sRGB 240 (lineal 0,87) [convención]. Los metales desnudos sí pueden llegar a 245 (aluminio, medido).
3. Rugosidad por familia de acabado (media del mapa, ±0,10 de tolerancia):
   - pavonado 0,13 [medido]; aluminio con desgaste 0,24 [medido]; parkerizado 0,37 [medido];
   - polímero 0,40 [medido]; goma 0,59 [medido]; anodizado mate 0,65 [medido]; madera 0,54 [medido].
4. **Variación**: la rugosidad nunca es constante. Desviación típica del mapa entre 0,04 y 0,12 [convención] (los mapas medidos tienen variación de grano visible). Un material con desviación <0,02 se rechaza: es lo que da aspecto de plástico de juguete.
5. Los metales llevan `metalness` ≈ 1 y los no metales ≈ 0; los valores intermedios solo se admiten en bordes de transición (desgaste de pintura sobre metal: PaintedMetal004 mide 0,09 de media, es decir, casi todo no metálico con islas metálicas).

## 3. Contraste entre materiales dentro de una pieza

Las fotos de referencia dicen que casi todo es negro sobre negro: el contraste real lo da el **brillo**, no el tono [foto: Aimpoint, PMAG, CP99, USP]. Por tanto:

1. **Contraste de brillo**: entre dos materiales adyacentes (p. ej. corredera y armazón, tubo de óptica y tapa) la rugosidad media debe diferir ≥ 0,20 [convención] (en la CP99, la corredera satinada frente al armazón mate; en el ACOG, tapa de objetivo más brillante que el tubo).
2. **Contraste de tono**: en el render con luz de estudio, la luminancia media (L* de CIELAB) de dos zonas de materiales distintos debe diferir ΔL* ≥ 6 [convención]. Si solo difiere el brillo, debe cumplirse la regla 1.
3. **Acentos**: cada pieza compleja lleva al menos 1 acento de tono claro o de color (marcaje grabado, fibra óptica, punto de mira, tapa de gas, tornillería de acero) [foto]. Una pieza 100 % monocroma se marca como «plana».
4. Los marcajes (texto, logotipos) son bajorrelieve de 0,05-0,15 mm [convención] **sin logos ni nombres de marca**: la guía de materiales usa texto genérico o ninguno.

## 4. Aristas, bordes y líneas de partición

1. **Chaflán o filete en toda arista exterior** (ya lo vigila el escalador con `filetes` y `aristas_vivas`; aquí se concreta el tamaño): polímero 0,3-0,6 mm; metal mecanizado 0,2-0,4 mm; perillas y moleteados 0,2 mm [convención]. En un raíl Picatinny (20 mm de ancho [ficha]) el chaflán va en las crestas de las ranuras, no en el fondo.
2. **Brillo de arista**: las aristas desgastadas son más claras y más lisas que la cara (visible en los PMAG y en la CP99: aristas más claras por roce [foto]). Regla: en una pieza de acabado anodizado, cerakote o pavonado, el 10-25 % de la longitud de aristas expuestas (esquinas y cantos que sobresalen) lleva el material de desgaste (`mat.aluminio_desgaste` o `mat.parkerizado`) con albedo ≥ +40 sRGB sobre la cara [convención]. Los polímeros solo aclaran un 5-10 %.
3. **Líneas de partición** (`particion` en las referencias): toda unión entre dos piezas físicas distintas (tubo-torreta-base de óptica, corredera-armazón, cuerpo-labios de cargador) lleva un surco de 0,15-0,30 mm de ancho y 0,2-0,5 mm de profundidad [convención]. No se funden en un solo cuerpo liso.
4. **Tornillería**: los tornillos visibles en las fotos (base de ACOG y CompM4, cachas de USP, armazón de CP99 [foto]) se modelan como cilindros con cabeza de ø 2-4 mm, material `mat.parkerizado`. Una óptica de aumentos sin tornillos visibles en la base se marca como incompleta.
5. **Moleteado y agarre**: perillas y torretas llevan moleteado real (diamante o recto) con paso 0,5-1,0 mm [convención] como geometría o como mapa de normales; la empuñadura de pistola, punteado en relieve de ø 1,0-1,5 mm y altura 0,2-0,3 mm [foto: CP99; medida de convención]. Las paredes del cargador de polímero, paneles rehundidos de 0,3-0,6 mm de profundidad [foto: PMAG].

## 5. Desgaste y suciedad en cavidades

Se aplican con máscaras procedurales (AO + curvatura) sobre los materiales de la sección 1; nunca como foto.

1. **Suciedad en cavidades**: la oclusión ambiental modula el albedo en un 15-30 % (oscurece) y sube la rugosidad en +0,05-0,15 dentro de ranuras, roscas y bajo la ventana de recuento [convención].
2. **Desgaste de pintura**: máscara tipo PaintedMetal004 con cobertura total del 2-6 % de la superficie de una pieza usada y 0 % en una pieza «nueva» (la web debe poder alternar nueva/usada) [convención].
3. **Huellas y manchas**: sobre vidrio, lentes y superficies brillantes, máscara de Fingerprints006 / SurfaceImperfections013 con intensidad de rugosidad +0,05-0,20 [convención].
4. **Marcas de uso**: no más de 3 rayones largos visibles por cara a 1 m de distancia de cámara. El resto va dentro del mapa de normales para no romper la silueta.
5. **Prohibido**: óxido y roña por defecto. Las piezas de airsoft se muestran limpias y con desgaste leve; el desgaste fuerte es una opción del usuario.

## 6. Tolerancias de color entre piezas de un mismo conjunto

Los fabricantes reales **no** hacen coincidir todas las piezas al 100 %: Tokyo Marui anuncia que en el Mk18 Mod.1 reproduce «la diferencia de tono del FDE entre cada pieza» y que el guardamanos metálico logra su color con alumita, mientras el receptor lleva Cerakote [ficha: tokyo-marui.co.jp/products/gas/machinegun/479].

1. **Misma familia de color y mismo material** (p. ej. dos piezas de polímero FDE de un mismo kit): ΔE00 ≤ 2,0 entre sus albedos medios [convención].
2. **Misma familia de color, material distinto** (guardamanos anodizado FDE frente a receptor Cerakote FDE): ΔE00 entre 2,5 y 6,0, y la pieza metálica ligeramente más saturada y más oscura [ficha + convención]. Menos de 2,5 parece un error de textura; más de 6 parece otro color.
3. **Familias de color distintas** (negro frente a FDE): son decisiones del usuario; el escalador no las compara.
4. **Negros entre fabricantes**: tono del negro dentro de ±8 sRGB entre piezas de la misma réplica [convención]; la diferencia debe venir sobre todo del brillo (regla 3.1).
5. El color de variante se cambia con un parámetro del material, no con una textura nueva (`docs/05`, sección de formato y materiales): las tolerancias se cumplen sobre el parámetro.

## 7. Iluminación de estudio para medir y para el visor

Un solo estudio fijo para todas las piezas, de modo que las medidas sean comparables (el escalador ya renderiza 3/4 y lateral con la pieza al 80 % del cuadro).

1. **Entorno**: mapa HDRI de estudio neutro CC0 de Poly Haven (hay que elegirlo: no está verificado aquí cuál) más tres luces: principal a 45° por encima y delante, relleno al lado opuesto con relación 3:1 con la principal, y contraluz suave para marcar siluetas oscuras [convención].
2. **Fondo**: gris neutro medio (sRGB ~ 118, lineal ~ 0,18) para no ocultar ni piezas negras ni claras; nunca negro ni blanco [convención].
3. **Tono y exposición fijos** (sin autoexposición) para que ΔL* sea comparable entre renders.
4. **Luz rasante de control**: un tercer render con la principal casi paralela a la superficie (80-85° respecto a la normal) revela bajorrelieves y marcajes: en él, cada marcaje y panel de agarre debe cambiar la luminancia local ≥ 8 % respecto a la cara vecina [convención]. Es el equivalente de la foto del PMAG sobre nieve.
5. **Reflejos**: la pieza metálica necesita entorno que reflejar; sin HDRI, un metal con metalness 1 se ve negro plano. Esa es otra causa típica del aspecto plano actual.

## 8. Qué mide el escalador y con qué umbral

Métricas que se pueden calcular de un render y de los datos de materiales; los umbrales son los de arriba y deben calibrarse con la hoja de contacto antes de volverse puerta.

| Métrica | Umbral propuesto | Sección |
|---|---|---|
| Albedo de un material «negro» entre sRGB 30 y 55 | fallo si <30 o >55 | 2.1 |
| Albedo sin metal ≤ sRGB 240 | fallo si >240 | 2.2 |
| Desviación típica del mapa de rugosidad | fallo si <0,02; aviso si <0,04 | 2.4 |
| Diferencia de rugosidad media entre materiales adyacentes | ≥ 0,20 | 3.1 |
| ΔL* entre zonas de materiales distintos | ≥ 6 | 3.2 |
| Acentos por pieza compleja | ≥ 1 | 3.3 |
| Filete en aristas expuestas | polímero 0,3-0,6 mm, metal 0,2-0,4 mm | 4.1 |
| Fracción de aristas con material de desgaste | 10-25 % (metal), 5-10 % (polímero) | 4.2 |
| Líneas de partición presentes en uniones de piezas | surco 0,15-0,30 mm | 4.3 |
| ΔE00 entre piezas del mismo material y color | ≤ 2,0 | 6.1 |
| ΔE00 entre material distinto y misma familia de color | 2,5 a 6,0 | 6.2 |
| Cambio de luminancia con luz rasante en marcajes y paneles | ≥ 8 % | 7.4 |

## 9. Límites y trabajo pendiente

- Las bases CC0 son fotografías de materiales de uso general (suelos, metal industrial). No hay una textura de anodizado o de Cerakote «de arma»; los materiales finales se ajustan a mano y se validan con el render común (`docs/05 §8`).
- Las observaciones de piezas salen de **6 fotos nuevas** y de las 30 anteriores; sirven para decidir qué detalle poner, no para copiar formas. Dos de ellas son cargadores de polímero de arma real (solo referencia de grano y paneles) y dos son pistolas de aire de Umarex, no airsoft de 6 mm.
- Los números marcados **[convención]** son hipótesis de partida. Tras ejecutar el escalador sobre la hoja de contacto, hay que sustituirlos por los percentiles reales de las piezas buenas.
- Falta una foto CC0/CC-BY de un guardamanos, de una empuñadura de réplica AEG y de un bípode de airsoft: Commons no ofrece ninguna con licencia admitida (ver `docs/catalogo/referencias-cc.md`).
