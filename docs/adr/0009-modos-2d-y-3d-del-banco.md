# ADR-0009 — El Banco con dos modos, 2D con profundidad y 3D, sin mezclarlos

- **Estado**: Propuesta (19-11-2026). Pendiente del OK de Javi al plan de la primera rebanada.
- **Fecha**: 2026-11-19
- **Decisores**: Javi (+ Claude Code)

## Contexto
- El 3D del pipeline (piezas paramétricas, materiales, luz) avanza despacio: hoy hay cientos de piezas T0 con medidas de demostración, ninguna con nivel T2, y llevarlas todas a una calidad publicable es trabajo de meses. Javi prefiere avanzar con calma y paciencia: el proyecto lleva tiempo, sin un plazo fijo (memoria `ritmo-un-ano-calma`).
- Javi no quiere abandonar el 3D, pero quiere un MVP que se pueda ver antes: alternar entre una **vista 2D con perspectivas y profundidad** y la **vista 3D**, e ir sumando 3D poco a poco.
- Mezclar piezas 2D y 3D en una misma escena «se nota mucho» (Javi, 19-11-2026): la luz, los materiales y la perspectiva no coinciden.
- `docs/03 §8` permitía mezclar niveles de fidelidad en un build. Esta decisión lo limita a la mezcla **dentro de un mismo modo**.
- Las fotos de terceros no se pueden publicar ni proyectar como textura (principio 5). La exploración del 19-11-2026 no encontró un canal ya hecho para fotos publicables de réplicas; Javi aportará fotos propias, con calma (memoria `fotos-las-saca-javi`).

## Decisión
1. **Dos modos de vista, y cada build se muestra entero en uno solo:**
   - **2D con profundidad**: la réplica se ve como imagen desde varias perspectivas (frontal, 3/4, lateral, cenital…), con paralaje y mapa de profundidad al moverse. Es el modo por defecto y la alternativa ligera y accesible (principio 10).
   - **3D**: modelo glTF que se gira libremente.
2. **Nunca se mezclan 2D y 3D en una escena.** Un interruptor siempre visible cambia **todo el build** de un modo al otro. El modo 3D solo se ofrece cuando **todas** las piezas del build tienen modelo 3D; si falta alguna, el interruptor se desactiva y dice cuáles faltan.
3. **El 3D se incorpora de forma incremental y no se abandona nunca.** Sigue siendo una línea de trabajo permanente del pipeline (familias, calidad, materiales y luz). Cada pieza que alcanza la calidad de publicación enriquece ambos modos.
4. **Una sola fuente para las dos vistas:** las vistas 2D se **renderizan desde los modelos 3D** con el mismo pipeline (Blender, materiales PBR y presets de luz), por pieza y por ángulo, con máscara y profundidad, y se componen en pantalla ancladas por los `socket.*`. Así toda mejora del 3D mejora el 2D.
5. **Las fotos reales solo entran por vías con derechos:** fotos propias de Javi (con cesión al proyecto), CC0/CC-BY verificadas, o permisos y feeds de tiendas y marcas. Sirven para medir y trazar (T0 → T2) y, cuando haya derechos, para vistas 2D fotográficas; mientras tanto, la 2D la dan los renders propios. Logos y marcajes: solo referencia interna salvo permiso.
6. **Todo se etiqueta con su nivel real** (T0–T3) y con «provisional» donde toque (principio 1). Nunca un visor de forma gris sin avisar: la web enseña el resultado final con materiales y luz (memoria `web-muestra-resultado-final`).

## Alternativas consideradas
| Opción | Pros | Contras | Por qué no |
|---|---|---|---|
| Todo 3D desde el MVP | Una sola tecnología, máximo «wow» | Depende de tener todas las piezas pulidas; meses de espera; pesado en móvil | Retrasa mucho el MVP |
| 2D con fotos de terceros | Aspecto fotográfico inmediato | Copyright; sin canal legal encontrado | Incumple el principio 5 |
| Mezclar 2D y 3D en la escena | Cada pieza usa lo que tiene | Luz, materiales y perspectiva no encajan: se ve un collage | Decisión de Javi |
| 2D solo, sin 3D | Simple, ligero | Pierde el diferencial y el trabajo hecho | Javi quiere seguir con el 3D |

## Consecuencias
- **Positivas**: MVP viable antes; alternativa ligera y accesible integrada; el trabajo 3D no se pierde y alimenta el 2D; sin collage visual.
- **Negativas y riesgos**: hay que renderizar cada pieza desde N ángulos y mantenerlas sincronizadas con el 3D (coste de render y de almacenamiento); el modo 3D puede tardar en estar disponible para muchas réplicas; los montajes 2D exigen buen anclaje por sockets en cada ángulo.
- **Trabajo generado**: renderizador de vistas por ángulo con máscara y profundidad; compositor 2D con paralaje; interruptor y estado «piezas sin 3D»; actualizar `docs/03 §8` y el roadmap; zona de entrada de fotos propias (`docs/fuentes/guia-fotos.md`).

## Validación
- Una réplica M4 completa con 2D por ángulos y 3D, con el interruptor, y el OK visual de Javi a capturas de escritorio y móvil.
- Presupuestos de docs/08 cumplidos en ambos modos; Lighthouse móvil ≥ 90 en modo 2D.
- Ningún build mezcla modos (test de integración).

## Disparadores de revisión
- Si el coste de render o de almacenamiento de las vistas 2D se dispara.
- Si se consiguen fotos con derechos en volumen suficiente para vistas fotográficas.
- Si todas las piezas de las cuatro familias alcanzan la calidad de publicación (el 3D podría pasar a ser el modo por defecto).
