# Diligencia debida · primera pasada (05-11-2026)

Primera pasada en vivo de `apps/crawler/src/diligencia.ts` con permiso de Javi: las 10 tiendas de `candidatas.md` y 12 webs oficiales de marcas del grupo A (`marcas.md`). Como máximo, robots.txt, `/.well-known/tdmrep.json`, la portada, los sitemaps y 5 páginas de muestra por web, a una petición cada 3–10 s por sitio. Lo descargado está en `assets-src/raw/diligencia/<slug>/` (ignorado por git). Las webs con reserva de IA guardan sus páginas en `sin-ia/`, que nadie procesa con IA (tampoco Claude Code). Solo se ha leído `resumen.json`.

Los veredictos son **provisionales**. Faltan las condiciones de uso de la mayoría y el contacto de cada tienda. Ninguna web pasa a `apta` sin permiso escrito.

## Lo que ha impedido ver 9 webs: la red, no las webs
Desde la red en la que trabajaba Javi ese día, un cortafuegos **Fortinet** intercepta el TLS de varias webs de airsoft. Probablemente las clasifica como «armas» y sirve su propio certificado (`O=Fortinet, CN=FG7H1GTB25001769`) en lugar del real. El cliente las rechaza (`UNABLE_TO_VERIFY_LEAF_SIGNATURE`), que es lo correcto: **nunca** se desactiva la verificación TLS ni se instala la CA del cortafuegos (docs/04 §3). Estas webs se repetirán desde otra red (casa de Javi) o desde el CI:
Airsoft Estartit, Taiwangun, G&G, VFC, LCT, Specna Arms, Umarex, Classic Army y KWA.

## Tiendas
| Tienda | robots.txt | Reserva de IA | Qué pasó | Veredicto provisional |
|---|---|---|---|---|
| Hobby Expert | responde **429** | — | Nos limita desde el primer acceso: la web nos bloquea | `solo-con-permiso` |
| Airsoft Gandia | 200 · `Crawl-delay: 5` | no | Portada y sitemap: **403** (cortafuegos de la web contra bots) | `solo-con-permiso` |
| Airsoft Quimera | 200 | no | Portada y sitemap: **403** | `solo-con-permiso` |
| Airsoft Estartit | — | — | TLS interceptado por la red | pendiente (repetir) |
| Airsoft Yecla | 200 | no | PrestaShop · fichas con `Product` y `Offer` en JSON-LD (precio y stock estructurados) · condiciones aún sin localizar | `apta-solo-datos` si sus condiciones no lo impiden |
| VSGUN | 200 | no | Portada y sitemap: **403** | `solo-con-permiso` |
| Ranger | 200 | **sí**: veta GPTBot, CCBot, ClaudeBot y Bytespider | Portada: **403** | `solo-con-permiso`; sus fotos, nunca por IA |
| Full Metal | 200 | **sí**: `Content-Signal: search=yes, ai-train=no, use=reference` y vetos a bots de IA | PrestaShop · las páginas están en `sin-ia/`: sus condiciones las tiene que leer Javi o un humano · `airsoft.fullmetal.es` es otro host, no aprobado | pendiente de lectura humana; fotos, nunca por IA |
| Taiwangun | — | — | TLS interceptado por la red | pendiente (repetir) |
| Evike Europe | 200 | no | Magento · sus condiciones **prohíben reproducir** contenido, «en cualquier forma». Solo autorizan extractos por sus feeds RSS | datos: pendiente (mirar el RSS); imágenes: `prohibido` |

## Marcas (grupo A)
| Marca | Web | Qué pasó | Nota |
|---|---|---|---|
| Tokyo Marui | tokyo-marui.co.jp | Sin robots.txt (404 = sin restricciones) · sin reserva de IA · alguna ficha con `Product` en JSON-LD | Fichas oficiales útiles para cotas. Condiciones en japonés, pendientes de leer |
| ASG | actionsportgames.com | Sin reserva de IA · sin datos estructurados | Las muestras salieron de noticias, no de productos: falta elegir mejor las fichas |
| ICS | icsbb.com | **Reserva de IA** (`ai-train=no` y vetos a bots de IA) | Su sitemap mezcla imágenes con productos (corregido en el cliente) |
| G&G | guay2.com | TLS interceptado | Repetir |
| VFC | vfc.com.tw | TLS interceptado | El certificado cubre `vfc.com.tw`, no `www.vfc.com.tw` |
| LCT · Specna Arms · Umarex · Classic Army | — | TLS interceptado | Repetir |
| KWA | store.kwausa.com | TLS interceptado | `www.kwa-usa.com` redirige a su tienda oficial, `store.kwausa.com` |
| JG Works · ARES | jgworks.hk · ares-amoeba.com | El dominio no resuelve | Verificar el dominio oficial antes de repetir |

## Conclusiones para el frente de fidelidad
- **Fotos de tiendas españolas**: de las 8 tiendas que respondieron, ninguna está libre para recoger fotos sin pedir permiso. Cinco nos bloquean (403/429), una prohíbe reproducir y dos tienen reserva de IA. Las fotos de referencia del piloto tienen que salir de **fichas oficiales de fabricantes** sin reserva (Tokyo Marui, ASG…), de permisos escritos o de fotos propias (la réplica de Javi).
- **Datos de precio**: Airsoft Yecla es la mejor candidata inmediata (JSON-LD completo, sin reserva). El resto pasa por pedir un feed o permiso.
- **Siguiente paso**: repetir las 9 webs desde otra red, localizar condiciones y contacto de cada tienda, y preparar los emails de permiso (los envía Javi).
