# Recetas de modelado paramétrico (leer antes de crear o mejorar una pieza)

Objetivo: que cada agente **reutilice** lo que ya funciona en lugar de redescubrirlo (gasta tokens y repite errores). Todo lo de aquí existe en el código de `apps/pipeline/src/taller6mm_pipeline/familias/`; antes de usar una receta, abre la función citada y copia su firma real. Las lecciones aprendidas están en `cuaderno-lecciones.md`.

## Reglas de oro
1. **Nada de cubitos.** Una pieza se construye con secciones lofteadas, perfiles curvos o revolución, y se le dan filetes. La prueba `tests/test_formas_reales.py` y la puerta de calidad (`calidad/bucle`) fallan si es un bloque.
2. **Usa `familias/formas.py` primero.** Es puro y determinista.
3. **Mallas cerradas (0 aristas abiertas)** y GLB determinista: mismos números, mismos bytes.
4. **Datos honestos.** Cotas con fuente y confianza; lo desconocido es `null` + bandera; `es_demo` si es un valor de barrido. Sin fotos/cotas propias, T0 y `publicable_3d=false`.
5. **Solo formas exteriores de airsoft.** Sin internos de armas reales, sin logos ni marcajes.

## Catálogo de ayudantes (existen hoy)
| Necesito… | Usa | Dónde |
|---|---|---|
| Sección lisa y redondeada (elipse a rectángulo redondeado) | `superelipse(y, cx, b, a_pos, a_neg=None, cz=0, n=3, k=32)` | `formas.py` |
| Unir secciones en un cuerpo (empuñadura, culata, mango) | `loftear([sec1, sec2, …])` (misma topología) | `formas.py` |
| Cambio suave de un parámetro a lo largo de la pieza | `interpolar(nudos, valores, x)` (PCHIP, sin rebases) | `formas.py` |
| Perfil curvo extruido (asa, guardamonte, silueta lateral) | `extruir_perfil(contorno, ancho_mm, plano=None, centrado=True)` | `formas.py` |
| Cañón, tubo, bocacha, mando, tambor | `revolucion([(radio, y), …], suave=False)` (eje Y) | `formas.py` |
| Cilindro orientado a X, Y o Z | `cilindro_en(eje, radio, largo, centro)` | `formas.py` |
| Redondear aristas | `filetear(solido, radio, aristas=None)` (si OCCT no puede, devuelve el sólido sin tocar) | `formas.py` |
| Chaflán | `biselar(solido, distancia, aristas=None)` | `formas.py` |
| Estrías de agarre circulares | `estriado(eje, centro, radio, largo, n, hondo)` | `tanda3_comun.py` |
| Ranura con perfil (M-LOK, corte lateral) | `ranura_perfil(largo, ancho, alto)` | `tanda3_comun.py` |
| Ranura radial | `ranura_radial(x0, x1, ancho, alto)` | `formas_tanda3.py` |
| Texto grabado neutro (letras sin marca) | `grabar(...)` | `detalle.py` |
| Rail Picatinny de 20 mm | `rail_picatinny.py` (no lo reinventes) | `rail_picatinny.py` |
| Hexágono (cabeza de tornillo, tuerca) | `_hexagono_x(radio_circ, x0, x1)` | `bocas_m4.py` |
| Nervaduras de cantonera | `_estrias_cantonera(...)` | `culatas_m4.py` |

Familias por tipo de pieza: M4 (`oleada1*.py`, `receptores.py`, `canon.py`, `amortiguador.py`, `monturas.py`, `empunaduras.py`, `miras.py`, `accesorios_ar.py`, `tanda3*.py`, `culatas_m4.py`, `bocas_m4.py`, `cargador_m4.py`, `guardamanos_*.py`), AK (`ak_*.py`), pistolas (rama de pistolas). Cada familia tiene su registro `FAMILIAS_*` y su JSON en `catalogo/`.

## Recetas
### Empuñadura o mango (forma orgánica, no un bloque)
1. 4 a 6 secciones con `superelipse` en distintas Y (ancho y fondo cambian con la altura; `n` entre 2,5 y 3,5).
2. `loftear(secciones)` y `filetear` de 1 a 3 mm en las aristas de los extremos.
3. Relieve de agarre: estrías con `estriado` o ranuras `ranura_perfil` **restadas** con solape real (ver lección sobre tangentes).
4. Taladro del tornillo de fijación como cilindro restado (`cilindro_en`).

### Tubo, cañón, bocacha, mando (revolución)
`revolucion([(r0,y0),(r1,y1),…])` con los escalones del perfil; rosca de 14 mm CCW como anillos en V con una ranura de alivio (sin hélice, anótalo en las notas de la pieza); `filetear` 0,3-1 mm en los bordes.

### Silueta lateral (asa de transporte, guardamonte, culata plegable)
`extruir_perfil` con `Line` y `Spline` encadenados; ancho en Z; rebajes y huecos restados; filete en las aristas vivas.

### Tornillería y detalle fino
Cabeza hexagonal con `_hexagono_x` + hueco hexagonal restado; ranuras de partición como cortes finos (≈0,2-0,4 mm) con solape; texto neutro con `grabar`. Sin logos.

### Pieza desde una foto de referencia (silueta real)
Detalle y método en `familia-siluetas.md`. En corto: `fotos/silueta.py` saca el contorno de una foto con fondo claro, se parte
en regiones y se guarda como números en `catalogo/siluetas-referencia.json`; `siluetas_motor.construir` extruye cada parte
(`Spec`: ancho estimado en Z y radio) con redondeo por prisma, o la revoluciona si es redonda; los detalles (serrados,
nervaduras, hoyuelos, ranuras) se restan con `siluetas_modelos`. **No uses `filetear` sobre estos contornos** (se cuelga) ni el
eje PCA en piezas en L (`eje="x"`).

### Sockets
Cada pieza declara `socket.*` con posición y orientación en mm; el ensamblador los casa por interfaz (rosca, diámetro, raíl). Si no encaja, es un **hueco anotado**, no una cota inventada.

## Cómo comprobar (en este orden)
1. `uv run python -m taller6mm_pipeline.calidad.bucle --familia <familia>` (puerta de calidad) y `uv run pytest -q <tu test>`.
2. `uv run python -m taller6mm_pipeline.calidad.escalera --familia <familia>` para los niveles de materiales e imagen.
3. Render con `blender/previsualizar.py` y **mirarlo tú**: pieza al 80 % del cuadro, 3/4 y lateral.
4. `ruff`, `biome` y hooks de pre-commit **siempre activos**. Commit WIP cada pocos pasos.
