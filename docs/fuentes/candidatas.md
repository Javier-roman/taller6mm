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
| 1 | Hobby Expert | https://www.hobbyexpert.es/ | ES | | | | pendiente |
| 2 | Airsoft Gandia | https://tienda.airsoftgandia.com/ | ES | | | | pendiente |
| 3 | Airsoft Quimera | https://www.airsoftquimera.com/ | ES | | | | pendiente |
| 4 | Airsoft Estartit | https://airsoftestartit.com/es/tienda-online-airsoft-y-ropa-militar.html | ES | Vende también ropa militar: fuera del configurador por ahora | | | pendiente |
| 5 | Airsoft Yecla | https://airsoftyecla.es/ | ES | | | | pendiente |
| 6 | VSGUN | https://vsgun.com/ | ES | | | | pendiente |
| 7 | Ranger | https://www.rangertienda.com/ | ES | | | | pendiente |
| 8 | Full Metal | https://fullmetal.es/es/ | ES | | | | pendiente |
| 9 | Taiwangun | https://www.taiwangun.com/es | PL (UE) | Catálogo muy grande: priorizar feed o afiliación | | | pendiente |
| 10 | Evike Europe | https://evike-europe.com/es/ | UE | Comprobar país de envío y si comparte catálogo con Evike (EE. UU.) | | | pendiente |

## Cómo añadir más
Añade una fila con la URL de la portada o de la categoría que interese, y en notas lo que sepas (envía a España, buenas fotos de un modelo concreto…).
