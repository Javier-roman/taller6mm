# 05 · Assets 2D/3D y fidelidad 1:1

> Requisito de Javi: "para mí es muy importante la similitud de las réplicas con las originales; tiene que ser similar o, si puede ser, igual".

## 1. Por qué la fidelidad es la columna vertebral
- Es lo que el usuario viene a ver: **su** réplica con **sus** piezas.
- El motor de compatibilidad trabaja en mm. Un modelo con medidas aproximadas daría veredictos falsos.
- Por eso las réplicas **no se deforman** como en algunos videojuegos: proporciones y medidas reales. Lo que sí se evita es **copiar** material ajeno y reproducir **logos o marcajes** (docs/09).

## 2. Niveles de fidelidad (visibles para el usuario)
| Nivel | Insignia | Qué es | Exigencia para publicar |
|---|---|---|---|
| T0 | Plano técnico | Silueta vectorial a escala con cotas, estética de plano de taller | Medidas clave de la ficha del fabricante; silueta trazada desde referencias |
| T1 | Foto licenciada | Recorte de una foto **con licencia** (propia, de la comunidad o cedida por tienda o marca), calibrado a escala y con mapa de normales | IoU de silueta ≥ 0,95 en su vista; error de longitud total ≤ 1 % |
| T2 | Modelo fiel | Modelo 3D propio, calibrado a las medidas, con materiales PBR propios | IoU ≥ 0,95 en al menos 2 vistas; cotas clave con error ≤ 1 % o ≤ 2 mm; anclajes verificados |
| T3 | Escaneado y verificado | Fotogrametría o escaneo de una unidad real, o CAD oficial con licencia | Cotas clave ≤ 0,5 mm, verificadas con calibre; revisión humana |

La insignia acompaña siempre al render: el usuario sabe qué está viendo. Objetivo: las 100 réplicas más buscadas en T2 o superior, y sus accesorios más montados en T1 o superior.

## 3. Fuentes de verdad dimensional
Cada cota guarda:
- `valor_mm`;
- `fuente`: `fabricante`, `estandar`, `medido_comunidad`, `escaneo` o `estimado`;
- `confianza`;
- evidencia: una URL o una foto con calibre o cinta métrica.

Los estándares (Picatinny, M-LOK, roscas, tubos buffer) viven en la tabla `interfaces` con su referencia.

La primera fuente de cada ficha es la **web oficial del fabricante de la réplica** (grupo A de `docs/fuentes/marcas.md`): fichas, manuales y despieces. Las marcas de armas reales (grupo B) solo sirven como referencia secundaria de medidas en réplicas con licencia 1:1; manda siempre la ficha del fabricante de la réplica.

## 4. Convenciones técnicas
- Datos en **mm**; escena en metros (1 unidad = 1 m).
- **Ejes**: +X hacia la boca de cañón, +Y hacia arriba, +Z a la izquierda del tirador (regla de la mano derecha).
- **Origen**: punto de referencia de cada plataforma (p. ej. el inicio del raíl superior del receptor), documentado por plataforma.
- **Vistas estándar**: `izquierda` (cámara en +Z) y `derecha` (cámara en −Z). Nunca se espeja una pieza asimétrica para fabricar la otra vista.
- **Anclajes**: nodos vacíos `socket.<slotKey>` en el glTF, y coordenadas equivalentes en metadatos para T0 y T1.
- **LODs y presupuestos**:
  - LOD0 para escritorio y LOD1 para móvil;
  - réplica: ≤ 1,5 MB en LOD0, ≤ 600 KB en LOD1 y ≤ 60.000 triángulos en LOD0;
  - accesorio: ≤ 250 KB.
- **Formato**: glTF 2.0 binario, Meshopt y texturas KTX2 (Basis), optimizado con gltf-transform.
- **Materiales**: con nombre de la biblioteca (`mat.anodizado_negro`, `mat.polimero_fde`…). Los colores de variante se cambian por parámetro, no con una textura nueva.

## 5. Puerta de licencias (sin excepciones)
| `license_status` | ¿Publicable? | ¿Uso con IA? | Notas |
|---|---|---|---|
| `propio` | Sí | Sí | Fotos, escaneos y modelos hechos por el proyecto |
| `comunidad_licenciado` | Sí | Sí | Subidas de usuarios con licencia no exclusiva según los términos |
| `cedido_tienda` / `cedido_marca` | Sí, según el acuerdo | Según el acuerdo | Permiso escrito archivado |
| `cc0` / `cc_by` | Sí, con atribución si aplica | Sí | Guardar licencia y enlace |
| `referencia_interna` | **No** | Solo si la fuente no tiene opt-out de TDM o IA | Fotos de tiendas sin permiso: solo para medir y modelar; bucket privado; retención limitada (90 días) |
| `prohibido` | No | No | Fuentes con opt-out o con condiciones que lo impiden |

Reglas:
- **Nunca** se publica un píxel de una foto de terceros sin permiso.
- **Nunca** se proyecta una foto ajena como textura: las texturas salen de la biblioteca de materiales propia.
- Logos y marcajes ("trades") no se reproducen sin permiso de la marca. Los modelos prevén "zonas de calcomanía" para cuando lo haya.

> Aviso: usar internamente fotos de terceros para medir y generar geometría es una zona que hay que validar con un abogado de propiedad intelectual antes de producción (docs/09). La vía 100 % limpia es usar solo fuentes con permiso.

## 6. Pipelines
### 6.1 T0 · Plano técnico (rápido, cubre todo el catálogo)
1. Medidas de la ficha.
2. Contorno: segmentación con SAM 2 (Apache-2.0) sobre una referencia y vectorización.
3. Limpieza y escala.
4. SVG con cotas, rótulos a plantilla y estilo de plano de taller.

Si la segmentación falla, se puede trazar a mano en la Trastienda.

### 6.2 T1 · Foto licenciada re-iluminable
1. Foto licenciada: vista lateral, fondo liso y objeto de escala.
2. Recorte con **BiRefNet** (MIT).
3. Corrección de rotación y perspectiva (eje del cañón horizontal).
4. Escala px/mm a partir de una cota conocida.
5. Normalización de color.
6. Mapa de normales y profundidad con **Depth Anything V2 Small** (Apache-2.0; las variantes Base, Large y Giant son no comerciales).
7. Anotación de anclajes, validación y publicación.

Nota: RMBG-2.0 (BRIA) es **no comercial** salvo que se compre licencia. No usar.

### 6.3 T2 · Modelo 3D fiel
1. Referencias multivista (licenciadas o `referencia_interna`) y cotas.
2. **Borrador con IA de imagen a 3D**:
   - opción principal: TRELLIS.2 (MIT);
   - alternativas: SAM 3D Objects (licencia SAM, que permite uso comercial con restricciones de uso) y Stable Fast 3D / SPAR3D (Stability Community License, gratuita por debajo de 1 M$ de ingresos anuales);
   - **no usar Hunyuan3D 2.x**: su licencia excluye la UE.
3. **Blender sin interfaz** (scripts Python): escala a cotas reales, alineación a los ejes canónicos, remallado o decimado, simetrías y limpieza.
4. **Piezas estándar paramétricas**: raíles, ranuras M-LOK, roscas, tubos y tornillería se **generan por código** con medidas exactas (Blender Python, o build123d/CadQuery con licencia Apache-2.0) y sustituyen a lo que generó la IA. La IA solo aporta formas orgánicas (pistoletes, culatas, receptores), siempre calibradas.
5. UVs, materiales de la biblioteca, horneado de AO y anclajes `socket.*`.
6. Exportación glTF y optimización con gltf-transform (Meshopt, KTX2, LODs).
7. **Validación automática**:
   - render ortográfico en las mismas vistas que las referencias;
   - máscara e **IoU de silueta** por vista;
   - comparación de cotas clave;
   - informe HTML con superposición y deslizador antes/después.
8. Revisión: subagente `revisor-fidelidad` y aprobación humana en la Trastienda.

**Puerta de realismo** (`apps/pipeline/src/taller6mm_pipeline/realismo.py`): ningún modelo 3D se publica como «fiel» sin IoU ≥ 0,95 en ≥ 2 vistas licenciadas y cotas clave a ≤ 1 % o ≤ 2 mm; si no, baja a T1/T0 y no se publica como 3D.

### 6.4 T3 · Escaneado y verificado
- **Fotogrametría**:
  1. Entre 80 y 150 fotos alrededor de la réplica, con luz difusa y una **hoja de marcadores ArUco impresa**, que da escala y pose automáticas.
  2. Reconstrucción con Meshroom/AliceVision (MPL-2.0) o COLMAP (BSD) para obtener la malla.
  3. La misma limpieza que en T2.
- **O bien** un CAD oficial cedido por la marca, con licencia escrita.
- Verificación de cotas con calibre, con fotos como evidencia.

## 7. Programa de escaneo comunitario y de tiendas
- **Comunidad**: guía paso a paso (vale un móvil), hoja de marcadores descargable, subida con licencia según los términos, crédito visible ("Escaneado por @usuario"), insignias y reputación.
- **Tiendas** colaboradoras de Barcelona y del resto de España: sesiones de escaneo de su stock a cambio de visibilidad.
- **Marcas**: kits de prensa, CAD o renders oficiales, con insignia "Oficial".

## 8. Biblioteca de materiales PBR propia
Anodizado negro mate · anodizado FDE · Cerakote (FDE, OD, gris y negro) · polímero texturizado (negro, FDE y OD) · acero parkerizado · acero pavonado · aluminio mecanizado · goma · nogal (AK) · contrachapado laminado · cristal de óptica con tratamiento · tela y Cordura (fundas) · latón.

Base: texturas CC0 (Poly Haven, ambientCG) ajustadas a mano y validadas con un render de referencia común.

Materia prima CC0 ya descargada y registrada en `catalogo/materiales-cc0.json` (12 materiales a 1K, en `assets-src/materiales-cc0/`, ignorada por git). Reglas de aspecto medibles en `docs/catalogo/guia-aspecto-piezas.md`.

## 9. Herramientas (Trastienda → Estudio de assets)
- Subida de referencias con licencia.
- Lanzador de trabajos del pipeline.
- Anotador de anclajes (clic sobre la vista).
- Comparador de superposición.
- Aprobación y cambio de nivel.
- Historial de versiones.
- Renders giratorios automáticos para regresión visual.

## 10. Cómputo y coste
- **CPU** (T0 y T1): en local o en GitHub Actions.
- **GPU** (T2), por orden de preferencia:
  1. la GPU local, si Javi tiene una;
  2. cuadernos gratuitos (Kaggle o Colab, unos 16 GB). Bastan para modelos ligeros, pero TRELLIS.2 recomienda unos 24 GB;
  3. una GPU alquilada por horas (céntimos por modelo).
- Cuadernos reproducibles en `apps/pipeline/notebooks/`.
- Registro de modelos de IA, con licencia, enlace y fecha de verificación, en `apps/pipeline/MODELOS.md`.

## 11. Escala: miles de réplicas y accesorios combinables (decisión de Javi, 11-11-2026)

> Objetivo de Javi: poder montar una réplica real con muchísimas opciones, con miles de réplicas y miles de accesorios, como en la vida real, y no un par de decenas.

### 11.1 Principio: modelar piezas e interfaces, no combinaciones
- No se modela cada combinación. Con N plataformas y M accesorios, las combinaciones se **componen**, no se fabrican una a una.
- Se modelan **piezas** (una culata, un guardamanos, un silenciador) y **interfaces** (la ranura, la rosca, el pozo de cargador) que las unen.
- Quién decide si encaja: el motor de compatibilidad (docs/03). El build es un árbol: réplica → ranuras → piezas → ranuras.
- Cada pieza lleva nodos `socket.<slotKey>` en el glTF (§4). Ahí se engancha lo que va debajo.

### 11.2 Registro de interfaces estándar
Cada interfaz se guarda en la tabla `interfaces` (§3) con sus cotas y su fuente. **Ninguna cota está verificada todavía**: cada una se confirma con fuente, una a una, antes de usarla.

| Interfaz | Cotas | Fuente y confianza |
|---|---|---|
| Picatinny | pendiente de verificar | pendiente |
| M-LOK | pendiente de verificar | pendiente |
| KeyMod | pendiente de verificar | pendiente |
| Rosca de boca 14 mm, horaria | pendiente de verificar | pendiente |
| Rosca de boca 14 mm, antihoraria | pendiente de verificar | pendiente |
| Pozos de cargador, por plataforma | pendiente de verificar | pendiente |
| Tubo de culata (mil-spec y comercial) | pendiente de verificar | pendiente |
| Montura de óptica | pendiente de verificar | pendiente |
| Otras (se añaden según el piloto) | pendiente | pendiente |

### 11.3 Familias paramétricas
- **Familia** = generador por código (Blender Python o build123d/CadQuery, §6.3) + parámetros.
- **SKU** = familia + parámetros + acabado + fuente y confianza.
- La idea es que pocos cientos de familias den miles de SKU. Esto es una hipótesis: **pendiente de confirmar con el piloto**.

Parámetros típicos (los de cada familia se fijan al crearla):

| Familia (ejemplos) | Parámetros |
|---|---|
| Guardamanos M-LOK | longitud, diámetro, nº de ranuras, rosca, peso |
| Silenciador o apagallamas | longitud, diámetro, rosca, peso |
| Cañón exterior | longitud, diámetro, rosca, peso |
| Culata y tubo | longitud, tipo de tubo, peso |
| Cargador, por plataforma | pendiente de definir |
| Carcasa de miras, por modelo | pendiente de definir |

### 11.4 Plataformas base
- Una base por plataforma **y mecanismo**. AEG, GBB y otros cambian el cargador y el receptor, así que no valen igual.
- Orden previsto:
  1. familia M4/AR-15, con la Tokyo Marui M.W.S. de Javi como piloto;
  2. AK, MP5, MP7, pistolas (Glock, 1911), MPX, MCX, SCAR, etc.
- Una réplica concreta = base + parámetros + piezas de serie.

### 11.5 Niveles honestos
- Casi todo el catálogo sale en **T0 o T1**: ficha con cotas y silueta.
- **T2** solo con fotos licenciadas, medidas con calibre o CAD cedido.
- La web muestra el nivel real de cada pieza (principio de fidelidad, §1 y §2). Nunca se disfraza.

### 11.6 Alimentación en volumen
Fuentes, por orden de preferencia:
- fichas de fabricantes (grupo A de `docs/fuentes/marcas.md`);
- feeds con permiso de tiendas;
- comunidad, con la hoja de marcadores ArUco (§7);
- CAD o renders cedidos.

Los parámetros se extraen de las fichas, cada uno con su fuente y su confianza. Herramientas previstas en `apps/pipeline`: extracción desde ficha, plano T0 y validación IoU. **Estado de implementación: pendiente de confirmar.**

### 11.7 Piloto
- La M.W.S. de Javi es la **primera base M4**.
- Sus accesorios (culata, guardamanos M-LOK, miras rojas y silenciador) son **familias**, no modelos sueltos.
- El piloto servirá para medir el coste real por familia.

### 11.8 Cuellos de botella
- Tiempo de modelado por familia: **pendiente de medir**.
- Verificación de cotas (§3).
- Licencias de las fotos (§5).
- Coste por familia: **pendiente de medir** en el piloto.

### 11.9 Opción aparcada: IA de imagen a 3D para borradores
- Idea: generar borradores de piezas con IA de imagen a 3D (§6.3).
- Necesita una **GPU alquilada por horas**. Antes de usarla se pregunta a Javi por el coste (§10).
- **No puede usarse sobre fotos con reserva de IA**: las que llevan `Content-Signal` con `ai-train=no` o `ai-input=no`.
- **Sin decidir.**

## 12. Bucle de calidad (puerta medible por pieza)

Las piezas generadas necesitaban muchas mejoras y nadie las medía. El módulo `apps/pipeline/src/taller6mm_pipeline/calidad/` pasa cada pieza (GLB + ficha) por una puerta automática, escribe una cola de trabajo y deja una hoja de contacto para el juicio visual. Solo scripts y numpy: determinista (semilla fija `20261117`), sin IA y sin gastar tokens.

```bash
cd apps/pipeline
uv run python -m taller6mm_pipeline.calidad.bucle [--familia receptor] [--id 'gm-*'] [--max-iteraciones 3 --mejorador "<cmd>"] [--hoja] [--sin-ensamblajes] [--glb <carpeta>]
```

Entradas: las variantes de `oleada1` y `oleada1_cuerpos` (generadas en proceso, así que se ve siempre el código actual), los GLB de `salida/kit-m4/` si existen (se generan con Blender desde modelos CC que no viven en git: si faltan, el bucle los apunta como hueco y no inventa nada), los builds de `catalogo/m4-builds.json` reensamblados y cualquier carpeta pasada con `--glb` (así entran tanda 3, AK o pistolas cuando se fusionen). Salidas: `assets-src/calidad/cola.json` y `historial.json` (ignorados por git) y, en `apps/pipeline/salida/calidad/`, un `informes/<id>.json` por pieza, `tabla.md` y, con `--hoja`, `hoja.html` y `hoja-NN.png` (de peor a mejor; 3/4 y lateral con la pieza al 80 % del cuadro, material PBR procedural de `blender/previsualizar.py`).

### 12.1 Criterios y por qué

Los umbrales viven en `catalogo/calidad-minimos.json`: un `defecto` y sobrescrituras por familia (guardamanos, empuñadura, óptica, receptor, cañón…). Una pieza **pasa** si cumple el mínimo de todos los criterios y su puntuación llega a 75. La puntuación (0-100) es la media ponderada de la fracción que cumple cada criterio; lo desconocido (una cota `null`, una familia sin mapeo de cotas) es una `bandera` que no puntúa ni penaliza, y su peso se reparte entre lo medible.

| Criterio (peso) | Mínimo por defecto | Por qué |
|---|---|---|
| Malla cerrada (15, duro) | 0 aristas abiertas | Sin malla estanca no hay volumen, ni colisiones, ni impresión. |
| Relleno de la caja (8, duro) | volumen / caja ≤ 0,65 | Un bloque macizo ronda 0,9-1,0: es el «cubito». Misma cifra que `test_formas_reales`. |
| Nº de triángulos (8, duro) | ≥ 1500 (3000 en cañón y receptores) | Una caja son 12; una pieza con filetes y huecos, miles. |
| Orientaciones de cara (6) | ≥ 300 normales distintas (a 0,1) | Una caja achaflanada tiene ~26: mide la variedad de superficie. |
| Transiciones suaves (7) | ≥ 2 aristas de 4°-60° por cm² | Proxy de filetes y curvatura: densidad de detalle sobre el área. |
| Aristas vivas (7) | ≤ 45 % de la longitud de arista con diedro > 60° | Lo real tiene filetes; lo de juguete, esquinas vivas. |
| Silueta en 3 vistas (12) | no rectangular ≥ 0,2 (0,1 en cañón y tubo) | `max(1 − relleno, complejidad − 1)` medio en XY, XZ y ZY: 0 es un rectángulo puro. |
| Escala (4, duro) | dimensión mayor entre 3 y 1500 mm | Caza errores de unidad. |
| Cotas vs ficha (10, duro) | ±1 % o ±2 mm (`realismo.cota_ok`) | Solo con mapeo explícito clave→eje por familia; sin él, bandera. |
| Sockets (10, duro) | `sockets_requeridos` de la familia presentes y a ≤ 40 mm de la caja | Sin sockets no se puede ensamblar. |
| Eje largo (4) | el de la familia (+X boca, +Y arriba, +Z derecha) | Ejes canónicos (§4). |
| Simetría (4) | centro de masa a ≤ 3 % (5 % en curvas) del centro de la caja | Lo lateral debe estar centrado en Z. |
| Componentes (5) | ≤ 6 (24 en la BUIS, que lleva piezas móviles) | Caza flotantes y uniones mal hechas. |

Los umbrales se calibraron sobre las piezas actuales: no certifican realismo (eso es el IoU de §6.3 y el `revisor-fidelidad`), solo dejan fuera lo evidentemente pobre y dan al `mejorador-piezas` objetivos concretos. Un umbral que parezca injusto para una familia se cambia en el JSON con su motivo, nunca desactivando el criterio.

**Ensamblajes**: pasan si no hay colisiones entre piezas montadas, ni huecos físicos de más de 1 mm entre piezas que deben tocarse, ni montajes incompatibles, sin datos o sin colocar (los huecos de datos se listan como banderas).

### 12.2 Bucle y regresiones

Cada ejecución añade una entrada a `historial.json` (puntuación y estado de cada pieza). Si una pieza baja más de 1 punto o pasa de «pasa» a «no pasa» respecto a la última ejecución que la contenía, el bucle imprime `REGRESION` y la anota en la cola (`--estricto` devuelve el código 2). La cola va de peor a mejor (fallos duros primero) con el fallo principal, la sugerencia concreta y el archivo del generador. El subagente `mejorador-piezas` (Sonnet) toma el primero, lo mejora, vuelve a medir y repite hasta pasar o llegar al máximo de rondas; la skill `/mejorar-piezas` lo lanza. La hoja de contacto es para el revisor visual: la puerta mide, no juzga el parecido.

## 13. Escalera de calidad (de «pasa la puerta» a «imagen viva»)

La puerta de §12 solo mide forma. La escalera añade cuatro peldaños por encima, que se superan **uno a uno**: el nivel de una pieza es el último superado sin saltarse ninguno, y la cola de trabajo es siempre el siguiente peldaño. Todo es determinista (semilla `20261117`, Cycles con semilla fija) y no gasta tokens.

```bash
cd apps/pipeline
uv run python -m taller6mm_pipeline.calidad.escalera [--nivel N] [--familia canon|pistolete|mlok|todas] [--hasta N] [--id 'gm-*'] [--hoja] [--sin-render] [--forzar] [--imagenes] [--estricto]
```

Por defecto trabaja con las tres familias mejor posicionadas hoy: cañones exteriores (`canon.exterior`), pistoletes (`empunadura.pistolete`) y guardamanos M-LOK (`gm-mlok-*`). Con `--hasta 2` no usa Blender (segundos). Salidas: `assets-src/calidad/escalera-cola.json` y `escalera-historial.json` (la regresión de un nivel, más de 1 punto o pasar de «supera» a «no supera», se imprime como `REGRESION` y `--estricto` devuelve el código 2) y, en `assets-src/vistas/` (ignorada por git, nada se publica), las vistas `<grupo>/<id>.nN.png`, las sondas de medida, `previo/` (el render anterior, para el antes/después), `hoja-escalera.png` (una fila por familia, columnas N1 → N5) e `informe-escalera.md`.

| Nivel | Qué eleva | Métricas objetivas (umbrales en `catalogo/escalera-niveles.json`) |
|---|---|---|
| **N1 Forma** | La puerta de §12 (umbral 75) | Malla cerrada, relleno, triángulos, silueta, cotas, sockets… |
| **N2 Detalle fino** | Roscas, tornillos, líneas de partición, chaflanes con radio real, relieve de agarre | Área en triángulos ≤ 1,5 mm; transiciones finas por cm²; aristas vivas ≤ 25 %; periodicidad axial (autocorrelación del perfil: roscas, estrías); escalones del perfil por 100 mm; rasgos pequeños (grupos conectados de 1,5-15 mm: tornillos, rebajes) |
| **N3 Materiales** | Biblioteca PBR procedural propia asignada por familia | Cobertura de materiales; desviación de la rugosidad y CV del albedo (sonda de emisión); error frente a la receta; energía de alta frecuencia de la textura |
| **N4 Desgaste y contraste** | Bordes pulidos por uso, roce metálico en aristas, suciedad en cavidades por oclusión, variación entre piezas del conjunto | Cobertura y contraste del roce en aristas; cobertura de suciedad (oclusión ambiental); no-uniformidad por bloques; aumento de la varianza de rugosidad frente a N3; variación entre piezas del mismo conjunto y material |
| **N5 Imagen viva** | Estudio con contraluz, reflejos, profundidad de campo, Cycles con denoiser OIDN | Contraste (P98-P2); reflejos; contraluz (P90 del contorno / interior); círculo de confusión por la lente fina a partir de la sonda de profundidad; fracción enfocada; ruido residual; muestras y denoiser |

Cada nivel puntúa 0-100 con la media ponderada de la fracción que cumple cada criterio (lo sin dato es bandera, no penaliza). `umbral` = se supera el peldaño; `techo` = hasta donde sigue elevando el agente. Las cifras de N3-N5 salen de **sondas**: renders de emisión pura, sin gestión de color (8 bits «Raw»), del albedo, la rugosidad, la máscara de aristas, la de suciedad, la silueta y la profundidad, con la misma cámara que el render final. Miden la receta, no la estética.

**Materiales** (`apps/pipeline/src/taller6mm_pipeline/materiales/biblioteca.py`): anodizado negro mate con micro-rayas, parkerizado, polímero con grano, madera con veta, acero pavonado, goma y vidrio de lente. Los números (albedo, rugosidad media, metalicidad) salen de `docs/catalogo/guia-aspecto-piezas.md` §1-§2, medidos sobre los mapas 1K CC0 de `catalogo/materiales-cc0.json` (ambientCG Metal027, Metal038, Metal063, Plastic012A, Rubber004, Wood051); el desgaste y la suciedad siguen la §5 y son hipótesis `[convención]`. **De la base CC0 solo se toma la estructura** (variación de rugosidad, relieve y modulación de luminancia, proyectados en caja sobre coordenadas de objeto, sin UV); el color y el brillo medio los fija la receta propia. `materiales/cc0.py` resuelve los mapas de `assets-src/materiales-cc0/` (también desde el repo principal si se trabaja en un worktree, o con la variable `TALLER6MM_CC0`); si no están en disco, el material cae a su receta procedural (ruido, Voronoi, onda) y N3 lo anota (`textura_cc0 = 0`). Las texturas CC0 son solo biblioteca interna del render: nunca se publican ni se proyectan fotos de terceros, y `biblioteca.validar` rechaza cualquier ruta de imagen. El **asignador** (`materiales/asignador.py`, catálogo `catalogo/materiales-piezas.json`) resuelve por patrón de id, familia exacta, familia con `*` y prefijo; lo que cae al defecto cuenta como no cubierto. La variación entre piezas del mismo conjunto sale del CRC32 del id, así que es reproducible.

**Render** (`apps/pipeline/blender/escalera_render.py`, Blender portátil de `C:\tools\blender`): N1 arcilla gris; N2 arcilla con oclusión y realce de aristas para ver el detalle; N3 PBR; N4 con desgaste y suciedad; N5 con estudio (guía §7: fondo gris medio, clave, relleno 3:1, dos tiras de contraluz, suelo semirreflectante, f/5,6) y Cycles con denoiser. Cada familia tiene además un render de conjunto N5 con todas sus piezas bajo la misma luz. Las vistas se cachean por hash del GLB, de la receta, de los mapas CC0 y del script.

**Reglas**: la apariencia no cambia el nivel de fidelidad (todo sigue en T0 y `publicable_3d=false`, §1); las fotos de terceros nunca son textura; un umbral injusto se cambia en el JSON con su motivo, nunca desactivando el criterio. El subagente `escalador-calidad` (Sonnet) y la skill `/escalar-piezas` toman la cola del siguiente peldaño y la elevan sin parar hasta el techo: en N1 y N2 editan el generador de la familia; en N3-N5, solo la biblioteca, el catálogo y el script de render.

**Huecos conocidos**: el ensamblaje de un build entero (N5 «piezas coherentes») se mide hoy por la variación entre piezas de un mismo material y por el render de conjunto de cada familia; el build completo espera a que el kit M4 esté disponible en local. Faltan el HDRI de estudio CC0 de la guía §7 (se usa un entorno procedural con cajas de luz), el contraste entre materiales adyacentes (§3, solo hay piezas de un material) y la luz rasante de control (§7.4). N2 mide si el detalle fino existe, no si es el correcto (eso es el `revisor-fidelidad`).

## Criterios de aceptación (Fase 7)
- [ ] Puerta de licencias implementada: no se puede publicar un asset sin licencia publicable.
- [ ] T0 generado para todo el catálogo semilla.
- [ ] Al menos 5 réplicas en T2 con informe de validación (IoU ≥ 0,95 en 2 vistas y cotas dentro de tolerancia), aprobadas por `revisor-fidelidad` y por Javi.
- [ ] Piezas estándar paramétricas (Picatinny, M-LOK, rosca de 14 mm) con cotas verificadas.
- [ ] Insignias de fidelidad visibles en el configurador y en las fichas.

## Anexo A · Idea original aparcada: el vaciado de cada réplica

La idea original era **vaciar** cada réplica y cada accesorio uno a uno: escanearlo o modelarlo a 1:1 con niveles T2 o T3.

- **Ventaja**: máxima fidelidad.
- **Problema**: coste alto por pieza. No escala a miles de réplicas y accesorios (§11).
- **Estado**: aparcada. Se conserva por si un día vuelve.

Cuándo tendría sentido:
- CAD cedido por marcas (§6.4);
- escaneo en tiendas colaboradoras (§7);
- presupuesto para escáner o GPU (§10). **Importe: pendiente de decidir.**

Qué se reutilizaría:
- las mismas herramientas de validación: IoU de silueta y comparación de cotas (§6.3, paso 7);
- los mismos niveles T2 y T3 (§2);
- las familias paramétricas y el registro de interfaces (§11) como esqueleto.
