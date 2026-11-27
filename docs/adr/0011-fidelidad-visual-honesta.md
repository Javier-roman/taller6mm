# ADR-0011 — Fidelidad visual honesta: proporciones reales, medidas solo con fuente

- **Estado**: Aceptada (26-11-2026). Javi: «lo de las medidas va a ser complicado cumplir o imposible, mejor dejarlo» y, al ver la reformulación, «perfe, así de proporcional».
- **Fecha**: 2026-11-26
- **Decisores**: Javi (+ Claude Code)

## Contexto
- El principio 1 de CLAUDE.md decía «Fidelidad 1:1: réplicas y accesorios con proporciones y medidas reales en mm». Medir cada réplica concreta al milímetro exige ficha del fabricante, medición física o CAD cedido, y no los tenemos para casi ninguna réplica.
- Lo que sí funciona hoy es partir de referencias visuales (fotos aportadas por Javi, modelos de licencia abierta) y de cotas públicas puntuales; las réplicas salen con proporciones creíbles pero con medidas sin verificar (`es_demo`, `null` + bandera).
- El motor de compatibilidad no necesita el largo total de cada réplica: necesita las **interfaces estándar** (Picatinny, rosca de 14 mm CW/CCW, M-LOK, STANAG, etc.), que son públicas.

## Decisión
1. **Se abandona la medida exacta en mm de cada réplica concreta como requisito.** Ya no se persigue ni se promete.
2. **Fidelidad visual honesta**: las réplicas se muestran con proporciones reales sacadas de referencia (fotos, fichas públicas, modelos abiertos). Las medidas en mm se muestran solo cuando hay fuente citada.
3. **Lo desconocido sigue siendo `null` + bandera, nunca un valor inventado** (principio 2 intacto). Escala relativa con bandera cuando no hay cota.
4. **El nivel de cada pieza es siempre visible** y honesto: ilustrativa, aproximada o verificada (T0–T3 de docs/05). Nunca se disfraza.
5. **Las interfaces estándar siguen siendo exactas** y son la base del motor de compatibilidad (principio 3: motivo, fuente y confianza).
6. **Las variantes derivadas** de una réplica base (color, longitud de cañón o guardamanos, culata, cargador) se etiquetan «derivada de X» con confianza baja o media; un cuerpo distinto exige su propia referencia.

## Alternativas consideradas
| Opción | Pros | Contras | Por qué no |
|---|---|---|---|
| Mantener 1:1 en mm para todo | Máxima fidelidad prometida | Inviable sin fichas ni escaneos; bloquea el catálogo | Decisión de Javi |
| Abandonar también la honestidad del nivel | Más fácil | Pierde confianza y rompe el principio 2 | No negociable |
| 1:1 solo para unas pocas réplicas premium | Compromiso | Dos listones distintos; sigue exigiendo medición | Se podrá volver a ella por réplica cuando haya datos |

## Consecuencias
- **Positivas**: se desbloquea el catálogo con réplicas visualmente fieles y honestas; los agentes dejan de gastar esfuerzo en calibrar al milímetro; el modelado guiado por foto y los modelos abiertos pasan a ser la vía principal.
- **Negativas**: el mensaje de producto «fidelidad 1:1» (docs/01) debe reformularse: de «exacta» a «fiel y honesta». Menos promesa de precisión para el milsim exigente.
- **Trabajo generado**: reformular el principio 1 en CLAUDE.md, docs/01 y docs/05; mantener el etiquetado de nivel y la bandera de medida desconocida.

## Validación
- Ninguna ficha ni pieza muestra una medida sin fuente; todas muestran su nivel.
- El motor de compatibilidad sigue pasando sus pruebas con interfaces estándar, sin depender del largo total.

## Disparadores de revisión
- Si se consiguen fichas, escaneos o CAD cedidos para réplicas concretas (volver a T2/T3 por réplica).
- Si el mensaje comercial exige precisión que el producto no puede garantizar.
