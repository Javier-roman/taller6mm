# 01 · Visión y producto

## 1. El problema
Hoy, para montar una réplica a tu gusto tienes que:
- visitar 10 tiendas en España (y a veces del extranjero) para ver quién tiene stock de cada pieza;
- adivinar si un accesorio encaja en tu modelo concreto (roscas, raíles, cargadores, baterías…);
- imaginar cómo quedará, porque nadie te deja verlo antes de comprar.

No existe un sitio que junte **ver**, **saber** y **comprar mejor** para el airsoft.

## 2. La propuesta: un taller virtual de airsoft
1. **Ver**: en El Banco eliges tu réplica exacta y la montas pieza a pieza con representación fiel 1:1, en 2D y 3D.
2. **Saber**: la compatibilidad está explicada. Qué encaja, qué necesita adaptador, qué requiere modificación, qué no encaja y por qué.
3. **Comprar mejor**: cada pieza muestra sus ofertas reales en tiendas de España y del extranjero, con precio, stock y fecha de comprobación. También el coste puesto en casa y la combinación de tiendas más barata.
4. **Compartir**: la comunidad publica sus builds, se inspira, valora y opina.

Frase guía: *"Todo el mercado del airsoft en tu banco de trabajo."*

## 3. Para quién
| Perfil | Qué necesita | Qué le enamora |
|---|---|---|
| Novato | Elegir su primera réplica y lo básico sin equivocarse | Builds recomendadas por presupuesto; compatibilidad clara; "lo tienes por X € en 2 tiendas" |
| Jugador habitual | Mejorar su réplica y encontrar stock | Montar su modelo exacto; alertas de stock y precio; comparar tiendas |
| Milsim / coleccionista | Realismo extremo | Fidelidad 1:1; variantes y colores exactos; modo foto |
| Tiendas | Visibilidad y tráfico cualificado | Programa de tiendas: feed oficial, insignia de stock verificado, estadísticas |
| Equipos y clubes (futuro) | Uniformar equipo | Colecciones compartidas |

## 4. Mapa de funcionalidades
### Núcleo (MVP público)
- La Armería: inicio navegable con "wow" a primera vista.
- Catálogo de réplicas y accesorios con fichas, filtros y búsqueda.
- El Banco: configurador 2.5D fiel, con compatibilidad y estadísticas honestas.
- Ofertas por pieza (5–10 tiendas iniciales), historial de precios y fecha de comprobación.
- Lista de la compra agrupada por tiendas, con enlaces.
- Cuentas, builds guardadas y publicadas, favoritos, me gusta, comentarios y rankings.
- Alertas de stock y precio.

### Después
- 3D completo en el configurador para las réplicas más populares, modo foto y vista despiece.
- Optimizador multi-tienda y precio puesto en casa desde el extranjero.
- Radar de novedades del mercado.
- Internos (upgrades) con compatibilidad por gearbox.
- Programas de escaneo comunitario y de tiendas y marcas.
- Catalán e inglés; PWA instalable.

### Fuera de alcance (por ahora)
- Vender o cobrar: no somos tienda.
- Segunda mano entre particulares.
- Apps nativas.
- Cualquier contenido de armas de fuego reales.

## 5. Principios de producto
1. **Fidelidad 1:1** (docs/05): lo que ves es tu réplica, a escala real. No se deforman los diseños. Lo que se evita es copiar material ajeno y reproducir logos.
2. **Honestidad radical**: datos con fecha y fuente; lo desconocido se muestra como desconocido. Nada de estadísticas inventadas tipo videojuego.
3. **El usuario primero, las tiendas también**: tráfico justo, enlaces directos, sin trucos; patrocinios siempre etiquetados.
4. **Rápido aunque sea espectacular**.
5. **Comunidad sana**: es un deporte y una afición; nada de glorificar la violencia.

## 6. Métricas de éxito
| Tipo | Métrica | Objetivo inicial |
|---|---|---|
| Norte | Builds creadas por semana con al menos 3 piezas montadas | Crecimiento mes a mes |
| Activación | Visitas nuevas que montan ≥ 1 pieza en su primera sesión | ≥ 25 % |
| Retención | Usuarios con cuenta que vuelven en 30 días | ≥ 30 % |
| Valor para tiendas | Clics salientes a tiendas por semana; % de ofertas con stock confirmado | Crecimiento; ≥ 90 % |
| Frescura | Mediana de antigüedad de ofertas de productos "calientes" / resto | < 12 h / < 48 h |
| Cobertura | % de las 100 réplicas más buscadas con ficha completa; % en T2 o superior | 100 % / ≥ 50 % al lanzar |
| Calidad técnica | Core Web Vitals "buenos" en p75 móvil | Todas las páginas |

## 7. Sostenibilidad
Coste objetivo: 0–5 €/mes más el dominio. Ingresos posibles cuando haya tráfico, siempre identificados:
- afiliación;
- patrocinios etiquetados de tiendas;
- programa de tiendas con estadísticas;
- donaciones;
- más adelante, funciones premium (alertas ilimitadas, más builds privadas).

Antes de monetizar, revisar fiscalidad y forma jurídica (docs/09 §7).

## 8. Riesgos principales
| Riesgo | Mitigación |
|---|---|
| Legal: rastreo, imágenes, marcas | Reglas en código (docs/04 y 09), permiso primero, programa de tiendas, revisión de un abogado antes del lanzamiento |
| Datos de compatibilidad incompletos | Estándares + verificación comunitaria + "desconocido" honesto |
| Producción de assets lenta | Niveles T0 → T3, piezas estándar paramétricas, comunidad y marcas |
| Alcance desbordado | Fases con criterios de aceptación; nada fuera de fase sin ADR |
| Límites de los planes gratuitos | Diseño frugal (escrituras mínimas, caché); plan de pago de Workers a 5 $/mes como válvula |

## Criterios de aceptación
- [ ] Cada fase del roadmap se traza a una o más funcionalidades de este documento.
- [ ] Las métricas de §6 se pueden medir desde la Fase 5 (eventos definidos y sin datos personales).
