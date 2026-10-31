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

## Criterios de aceptación (Fase 7)
- [ ] Puerta de licencias implementada: no se puede publicar un asset sin licencia publicable.
- [ ] T0 generado para todo el catálogo semilla.
- [ ] Al menos 5 réplicas en T2 con informe de validación (IoU ≥ 0,95 en 2 vistas y cotas dentro de tolerancia), aprobadas por `revisor-fidelidad` y por Javi.
- [ ] Piezas estándar paramétricas (Picatinny, M-LOK, rosca de 14 mm) con cotas verificadas.
- [ ] Insignias de fidelidad visibles en el configurador y en las fichas.
