# Cuaderno de lecciones del pipeline

Memoria compartida entre agentes: **qué falló, por qué y qué hacer**. Léelo antes de empezar. Al cerrar una tanda, añade una entrada nueva arriba (fecha, qué pasó, qué hacer). Sin relleno: una lección, un párrafo.

## Montajes completos (nov-2026)
- **La caché del ensamblador no ve los cambios del generador.** `salida/ensamblador/cache` se indexa por `id_variante` (parámetros), no por el código: tras tocar un generador, borra la carpeta o medirás la pieza vieja. Fue la causa de «mis arreglos no hacen nada».
- **Piezas macizas contra huecos: asiento, no solape.** Los generadores dibujan las zonas de asiento hundidas (cola de milano de las miras, raíles de la corredera, tubo dentro de la culata, collar del bloque de gas) y con mallas macizas eso son colisiones. *Qué hacer:* en el generador, un alojamiento real (`culata.telescopica_*` con `incluir_tubo=false` lleva cilindro y quilla de alojamiento) o holgura de 0,4-0,6 mm (las mordazas de `tanda3_comun` ya no se hunden en el raíl); en el montaje, `insertar_mm` (entra en un hueco), `desplazar_mm` (ajuste en ejes del conjunto) y `ventana_hueco_mm` (cuando el contacto real queda lejos del socket). Las pistolas se «asientan» por pasos de 0,25 mm (`pistola_montaje.asentar`).
- **La tangente del socket no siempre es el eje de avance.** En los sockets de guardamanos del AK la tangente es vertical (+Y), así que `deslizar_mm` mueve la pieza hacia arriba. Usa `desplazar_mm: [dx, dy, dz]`.
- **El sondeo de colisiones es de 0,5 mm hacia dentro.** Dos superficies que se tocan en una arista (esquina del fondo de una ranura contra una mordaza) dan falsos solapes de 0,5 mm; con 0,4-0,6 mm de holgura desaparecen. Si un solape no cuadra con el dibujo, mira el `bbox` de los puntos dentro (script de depuración con `colisiones.muestrear` y `dentro_de`).
- **El hueco entre piezas se mide en una ventana de 30 mm alrededor del socket.** Una funda (culata) o una pieza larga que toca lejos del socket da `inf` o un falso hueco: `ventana_hueco_mm`. Con 6000 puntos una cara plana grande daba huecos de 3 mm falsos: ahora son 40000 puntos y un árbol k-d.
- **Cada tipo de pieza pide su propio dato.** El cargador AK mide 46,5 mm de ancho aunque el parámetro diga 43,2 (labios): comprueba el bbox de la sección antes de meterlo en un pozo de 45 mm.
- **Ids por material.** El asignador decide por familia y por id: dos fusiles con la misma pieza `guardamanos` no pueden tener uno madera y otro polímero. Ids como `guardamanos-madera` / `guardamanos-polimero` (patrones `*madera*`, `*polimero*`).

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
