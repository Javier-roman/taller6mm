# 00 · Índice de la especificación

Versión 1 · 31-10-2026 · Responsable: Javi

## Cómo leer esto
- `CLAUDE.md` (raíz) resume reglas y stack; estos documentos son el detalle.
- Cada documento termina con **criterios de aceptación** comprobables.
- Si dos documentos chocan, manda este orden: 09 (legal) > 08 (seguridad) > 01 (principios) > el resto. Si detectas un choque, dilo y propón un ADR.

| # | Documento | Contenido |
|---|---|---|
| 01 | `01-vision-y-producto.md` | Problema, usuarios, propuesta de valor, alcance, métricas, riesgos |
| 02 | `02-experiencia-y-diseno.md` | Dirección de arte, La Armería (inicio), sistema de diseño, accesibilidad |
| 03 | `03-el-banco-configurador.md` | Configurador, ranuras, motor de compatibilidad, lista de la compra, render |
| 04 | `04-mercado-e-ingesta.md` | Fuentes, rastreo ético, emparejado, precios, stock, alertas, radar |
| 05 | `05-assets-y-fidelidad.md` | Niveles de fidelidad, pipeline foto → 2D/3D, licencias, validación |
| 06 | `06-comunidad.md` | Builds públicas, rankings, reseñas, reputación, moderación |
| 07 | `07-arquitectura.md` | Componentes, datos, APIs, caché, trabajos, entornos, costes |
| 08 | `08-calidad-seguridad-operacion.md` | Pruebas, CI, presupuestos, seguridad, privacidad, observabilidad |
| 09 | `09-legal-y-cumplimiento.md` | RGPD, LSSI, DSA, propiedad intelectual, normativa de réplicas |
| 10 | `10-roadmap.md` | Fases, entregables y criterios de aceptación |
| — | `adr/` | Decisiones de arquitectura |
| — | `referencias/` | Capturas de referencia y qué tomar de cada una |
| — | `fuentes/` | Tiendas (`candidatas.md`) y marcas (`marcas.md`) elegidas por Javi, con su estado |

## Vocabulario del producto
| Término | Significado |
|---|---|
| La Armería | Inicio: escena navegable de estanterías; cada módulo es una sección |
| El Banco | Configurador |
| Build | Montaje guardado de una réplica (árbol de piezas) |
| Ranura (slot) | Punto de montaje con una interfaz y una geometría en mm |
| Interfaz | Estándar físico de montaje (p. ej. `rail.picatinny`, `thread.14mm-ccw`) |
| Ficha | Página de producto |
| Listado | Producto tal como aparece en una tienda (dato bruto) |
| Oferta | Listado emparejado con un producto del catálogo, con precio y stock |
| Vitrina | Comunidad |
| Tablón | Mercado: novedades, bajadas de precio, vuelta a stock |
| Taquilla | Zona personal del usuario |
| Trastienda | Panel de administración |
| T0–T3 | Niveles de fidelidad de un asset (docs/05) |

## Glosario de airsoft (para escribir bien la interfaz y el modelo de datos)
| Término | Significado |
|---|---|
| Réplica | Lo que se usa en airsoft. En la interfaz decimos "réplica", nunca "arma" |
| AEG | Réplica eléctrica: motor, caja de cambios (gearbox) y batería. La más común |
| Gearbox | Caja de cambios de una AEG. Su versión (p. ej. V2 en la familia M4/AR, V3 en AK y G36) decide qué internos son compatibles |
| GBB / GBBR | Réplica de gas con retroceso (pistola / fusil). Cargadores específicos |
| HPA | Sistema de aire a alta presión con motor neumático |
| Muelle / cerrojo | Réplica de un disparo por amartillado; habitual en francotirador (plataforma tipo VSR-10 muy extendida) |
| CO2 | Propulsión por cápsula, común en pistolas |
| Hop-up | Mecanismo que imprime efecto de retroceso (backspin) a la bola; incluye goma y "nub" |
| Cañón interno | Longitud y diámetro interior (p. ej. 6,01 mm "tightbore"); afectan a la configuración interna |
| Guardamanos | Handguard; aporta raíles o puntos de montaje |
| Raíl Picatinny (MIL-STD-1913) | Estándar de raíl con ranuras transversales (a menudo llamado "de 20 mm"). Weaver es parecido pero no idéntico |
| Cola de milano 11 mm | Raíl estrecho (dovetail) presente en algunas réplicas |
| M-LOK / KeyMod | Sistemas de montaje directo en el guardamanos mediante ranuras u orificios |
| Bocacha | Apagallamas o freno que se rosca en el cañón externo. Rosca más común en airsoft: 14 mm a izquierdas (CCW, "14 mm −"); algunas marcas usan 14 mm a derechas (CW, "+") |
| Silenciador / tracer | En airsoft, estético o con unidad trazadora para bolas fosforescentes |
| Culata | Fija, retráctil o plegable. Tubo buffer mil-spec y comercial tienen diámetros distintos y no son intercambiables |
| Pistolete | Grip. En AEG M4 aloja el motor, así que no es intercambiable con los de GBB |
| Cargador | Low-cap, mid-cap o hi-cap; compatibilidad por plataforma y a veces por marca |
| Batería | LiPo 7,4 V u 11,1 V; formatos stick, nunchuck/butterfly o brick; conectores Tamiya, T-Dean, XT30 |
| MOSFET / ETU | Control electrónico del disparo |
| FPS / julios | Energía de salida; cada campo fija sus límites por tipo de réplica |
| Trades | Marcajes y grabados de marca en la réplica |
| Upgrade | Mejora interna o externa |
| CQB, bosque, milsim, speedsoft | Estilos y escenarios de juego |
