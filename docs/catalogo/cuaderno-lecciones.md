# Cuaderno de lecciones del pipeline

Memoria compartida entre agentes: **qué falló, por qué y qué hacer**. Léelo antes de empezar. Al cerrar una tanda, añade una entrada nueva arriba (fecha, qué pasó, qué hacer). Sin relleno: una lección, un párrafo.

## Modelos de licencia abierta como imagen de portada (25-11-2026)
- **La puerta de calidad mide forma, no parecido.** Las réplicas paramétricas pasaban todos los umbrales y a Javi le parecían juguetes. *Qué hacer:* para la imagen de las baldas y la 2D, partir de un modelo completo CC0/CC BY con forma real y retexturizarlo (`docs/catalogo/replicas-ilustrativas.md`); mirar siempre un render a 100 % antes de dar nada por bueno.
- **Pistola 1911: elige por el detalle, no por el recuento de triángulos.** De seis 1911 CC BY, la de 15 mil triángulos con tornillos de cachas y ventana de expulsión superó a la de 40 mil (638 partes sueltas desordenadas) y a la de 8 mil (corredera con un pliegue en la boca). *Qué hacer:* miniatura en Workbench de todos los candidatos en una hoja, antes de limpiar ninguno.
- **Las partes sueltas ya vienen con nombre.** `separate(type='LOOSE')` conserva el nombre de la malla de origen: en el AK-47 bastan cuatro nombres (culata, pistolete y dos guardamanos) para separar la madera; en el M4A1, «Stock», «Magazine» y una caja normalizada para el pistolete. No hace falta cortar geometría.
- **Metal negro que sale gris o que desaparece.** Con `metálico = 1` y mundo oscuro el metal negro no refleja nada y queda como un recorte; con polímero a su lado, el polímero sale 3 veces más claro. *Qué hacer:* metálico 0,4-0,6 y rugosidad 0,3-0,4 en el metal, polímero con albedo 0,006-0,01 lineal y exposición de -1,6 EV con AgX; ajustar mirando una hoja con los cuatro modelos juntos.
- **Encuadrar con la caja de la pieza deja el arma al 55 %.** Las esquinas de la caja se proyectan más lejos que la silueta. *Qué hacer:* ajustar distancia y centrado con los vértices (`encuadrar_vertices` en `replicas_cc.py`) y, para px/mm común por clase, fijar el ancho del cuadro en mm en vez de encuadrar cada pieza.
- **Cycles en CPU a 1800 x 1200 y 160 muestras tarda unos 3 minutos por vista.** Itera a 1200 x 800 y 48 muestras (≈20 s) y deja el render final en segundo plano.
## Siluetas desde fotos de referencia (nov-2026)
- **Los filetes de OCCT se cuelgan con contornos medidos.** Un contorno de foto simplificado (100-300 segmentos) hace que `fillet` falle o no termine nunca, aunque la extrusión sea válida. *Qué hacer:* no filetear; intersecar la extrusión con un prisma de sección redondeada (`silueta_solidos.prisma_redondeado`), que es rápido y siempre cierra. Une los tramos entre esquinas duras en un solo `Spline` para tener pocas caras.
- **El eje del prisma de redondeo importa.** Con el eje mayor (PCA) en una pieza en L (armazón de pistola, guardamonte) el prisma gira y corta un triángulo del sólido. *Qué hacer:* `eje="x"` en piezas en L y PCA solo en piezas alargadas (receptor, culata, cargador, empuñadura).
- **Una captura de tienda con fondo blanco basta para un contorno, no para un 3/4.** Las vistas en perspectiva no dan silueta ortogonal: se usan solo para proporciones cualitativas. *Qué hacer:* pedir lateral puro (o dos a 90°) y dejar la réplica sin construir si no llega.
- **Partir la máscara con regiones y color.** Cada pieza sale de `máscara ∩ polígono de región` (px de la foto), con `quita_a` para piezas separadas y un criterio de color para madera/oscuro; el cierre morfológico de 4 px evita contornos con ruido de veta. Con ruido de captura, la tolerancia de Douglas-Peucker no baja de 1,3 px (sale solo el ruido del JPEG).
- **El IoU contra la foto es circular.** El contorno se extruye de la propia foto: el IoU mide la fidelidad del proceso (≥ 0,90), no una verificación independiente. Decláralo siempre junto a la cifra.
- **La escala por longitud total incluye accesorios.** La caja de la silueta entera cambia si el montaje tiene boca larga o culata extensible; calibrar entre fotos distintas con «la misma pieza» solo vale si se define igual en las dos (el receptor del AKM incluía el cuello delantero y el del AK-105 no). *Qué hacer:* calibre por longitud publicada y bandera; comprobar la coherencia con otra cota.
- **Cámara ortográfica de Blender.** El alto de la pieza es el eje Z de Blender (el glTF pasa de Y arriba a Z arriba): encuadrar con `dim.z`, no con `dim.y`.
- **JSON generados y Biome.** El hook de pre-commit formatea JSON con tabulaciones: ejecuta `pnpm exec biome format --write` sobre el archivo generado antes de hacer commit.

## Modelado y mallas
- **Aristas abiertas por contactos tangentes (nov-2026).** Un solape casi nulo entre dos sólidos (placa que sobresale un 2 %, letras que se tocan por una esquina, ranura tangente al taladro) deja la malla abierta, y puede pasar en Linux y no en Windows (coma flotante). *Qué hacer:* solape claro (varios mm; en grabado, ≥0,04 mm de solape entre celdas) y cortes que **entren** en el sólido. No relajes el test.
- **`filetear` falla en silencio.** Si OCCT no puede, devuelve el sólido sin tocar. *Qué hacer:* comprueba que el filete se ha aplicado (volumen o aristas) cuando el detalle importa.
- **Sombreado ondulado en lofts.** Causa probable (hipótesis, sin confirmar): secciones que cambian demasiado de forma o de topología. *Qué hacer:* misma topología y mismo `k` en todas las secciones; cambia los parámetros con `interpolar` (PCHIP); menos secciones y filete final.
- **Cubitos.** Teselar una cara plana no cuenta. Mínimos de la puerta: relleno de caja ≤ 0,65, ≥ 1500 triángulos (3000 en cañón y receptores), ≥ 300 orientaciones de cara. *Qué hacer:* geometría real (curvatura, filetes, cortes).
- **Piezas casi idénticas.** Varios cargadores (30/120/300/GBBR/AK) salieron iguales porque solo cambiaba la escala. *Qué hacer:* que cada tipo cambie perfil, ancho, base y nervaduras; comprueba lado a lado.
- **Medidas no inventadas.** Sin cota con fuente: `null` + bandera + `es_demo`. Las cotas públicas verificadas están en `cotas-publicas.md`.

## Materiales, luz y web
- **El GLB sin materiales se ve gris en la web.** El anodizado, el polímero y el desgaste solo existían en el render de Blender. *Qué hacer:* exportar los materiales PBR dentro del GLB y enseñar siempre el resultado final (ver memoria «la web muestra el resultado final»).
- **Luz demasiado reluciente.** Reflejos de espejo en metal anodizado. *Qué hacer:* preset `mate_suave` por defecto y rugosidad no menor que la medida en `materiales-cc0.json`.
- **Umbrales N3-N5 blandos.** Casi todo daba 93-100 porque se calibraron con las propias recetas. *Qué hacer:* calibrar contra medidas reales; justificar cada umbral.
- **Texturas CC0.** Solo como estructura interna (rugosidad/relieve), nunca fotos de terceros como textura, y nada se publica.

## Fuentes y modelos
- **Sketchfab/Objaverse.** Buscar «culata» o «guardamanos» devuelve fusiles completos. Reverificar la licencia en la API en vivo; solo CC0/CC-BY. Separar partes por nombre de malla/nodo.
- **IA imagen→3D.** TRELLIS no cabe en la GPU gratuita de Kaggle y Hunyuan3D 2.1 excluye la UE: descartado salvo decisión nueva y presupuesto.

## Trabajo con agentes y Git
- **Guardar el progreso.** Commit WIP cada pocos pasos con los hooks activos; los cortes por el límite de 5 h son frecuentes. **Nunca** desactives los hooks (el clasificador lo deniega).
- **Ramas WIP viejas retroceden main.** Una rama antigua puede traer versiones antiguas de archivos. *Qué hacer:* `git merge origin/main` y revisar `git diff origin/main --stat` antes del PR.
- **No pisarse.** Antes de editar un generador: `git log -3 -- <archivo>` y `git status`. Un agente por zona.
- **`gh pr merge --delete-branch`** puede fallar al borrar la rama local si `main` está en otro worktree; la fusión sí ocurre.
- **Squash y «update-branch».** Tras cada fusión el resto de PR quedan «BEHIND»; actualiza la rama y repite el CI (≈11 min en `verify`).
- **Escapes en `sed`.** Para cambios con caracteres especiales usa Edit, no sed.
- **`curl … | python`** lo bloquea el hook; usa `WebFetch` o guarda a archivo y revísalo.
- **Blender se mata por memoria.** Renderiza de uno en uno y reintenta solo el lote que falló.
- **Semgrep.** No uses `shell=True` ni `urllib` sin esquema fijo; usa `shlex.split`.
- **Vulnerabilidades de dependencias.** Hasta el deploy, OSV y pnpm audit avisan sin bloquear (issue #52). No pares a preguntar.

## Pendiente de aprender
- Medir cuánto se parece una pieza a una réplica real con fotos ortogonales y regla (T2). Hoy todo es T0.
- Cuánto cuesta en tokens una tanda completa, para dimensionar cuántos agentes caben por franja de 5 h.
