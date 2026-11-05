# Tiendas candidatas (lista de Javi)

Tiendas de las que Javi quiere obtener datos (precio, stock) y fotos de réplicas y accesorios. Claude Code las procesa **una a una** con la skill `/nueva-tienda`, en el orden de la tabla, y anota aquí el resultado. Son las **fuentes prioritarias** de la Fase 4.

URLs limpias: se han quitado los parámetros de seguimiento de Google (`srsltid`).

## Qué pasa con cada tienda
1. **Diligencia debida**: robots.txt (incluidas las líneas `Content-Signal`), condiciones de uso, si envía réplicas a España, si tiene feed oficial o programa de afiliación, y contacto.
2. **Veredicto**:
   - `apta`: datos y fotos, porque hay permiso escrito.
   - `apta-solo-datos`: precio, stock y enlace; las fotos solo como `referencia_interna`, para medir y modelar, nunca publicadas.
   - `solo-con-permiso`: no se toca hasta tener permiso escrito.
   - `excluida`: con el motivo anotado.
3. **Email de contacto** para pedir permiso de imágenes y un feed oficial (plantilla en la skill).
4. **Parser con fixtures** y estado `pendiente_revision`. Javi aprueba antes de programar cualquier rastreo.

Reglas completas: `docs/04-mercado-e-ingesta.md` §3 y `docs/05-assets-y-fidelidad.md` §5.

## Lista
| # | Tienda | URL | País | Notas | Veredicto | Imágenes | Estado |
|---|---|---|---|---|---|---|---|
| 1 | Hobby Expert | https://www.hobbyexpert.es/ | ES | | solo-con-permiso (429) | — | diligencia 05-11 |
| 2 | Airsoft Gandia | https://tienda.airsoftgandia.com/ | ES | | solo-con-permiso (403) | — | diligencia 05-11 |
| 3 | Airsoft Quimera | https://www.airsoftquimera.com/ | ES | | solo-con-permiso (403) | — | diligencia 05-11 |
| 4 | Airsoft Estartit | https://airsoftestartit.com/es/tienda-online-airsoft-y-ropa-militar.html | ES | Vende también ropa militar: fuera del configurador por ahora |  |  | repetir (TLS interceptado por la red) |
| 5 | Airsoft Yecla | https://airsoftyecla.es/ | ES | | apta-solo-datos (provisional, faltan condiciones) | referencia_interna (provisional) | diligencia 05-11 |
| 6 | VSGUN | https://vsgun.com/ | ES | | solo-con-permiso (403) | — | diligencia 05-11 |
| 7 | Ranger | https://www.rangertienda.com/ | ES | | solo-con-permiso (403) | nunca por IA (reserva) | diligencia 05-11 |
| 8 | Full Metal | https://fullmetal.es/es/ | ES | | pendiente de lectura humana (reserva de IA) | nunca por IA (reserva) | diligencia 05-11 |
| 9 | Taiwangun | https://www.taiwangun.com/es | PL (UE) | Catálogo muy grande: priorizar feed o afiliación |  |  | repetir (TLS interceptado por la red) |
| 10 | Evike Europe | https://evike-europe.com/es/ | UE | Comprobar país de envío y si comparte catálogo con Evike (EE. UU.) | datos pendientes (RSS) | prohibido (condiciones) | diligencia 05-11 |

Detalle y motivos de la primera pasada: [`diligencia-2026-11-05.md`](diligencia-2026-11-05.md).

## Cómo añadir más
Añade una fila con la URL de la portada o de la categoría que interese, y en notas lo que sepas (envía a España, buenas fotos de un modelo concreto…).
