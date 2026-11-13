# Cotas de airsoft (plataforma M4/AR-15)

Datos de `catalogo/cotas-airsoft.json`, consultados el **2026-11-12**. Solo réplicas de airsoft y accesorios. Lo desconocido es `null`. Estado `citado` = con fuente pero no es ficha del fabricante.

> Las cifras de tienda proceden de resultados de búsqueda y no de la ficha oficial. Hay que contrastarlas antes de fijar una cota. Los datos de ejemplo siguen prohibidos en producción.

## Resumen

- Cotas con valor: **35** de 53 filas. Alta: **0**. Media: **7**. Baja: **28**.
- Huecos (`null`): **18**.

### Qué falta

- **Ninguna cota de confianza alta.** Tokyo Marui devolvió 404 en la ficha probada, varias webs de fabricante dieron fallo de TLS o 429 y no se evadió ninguno. Siguiente paso: repetir desde otra red o desde el CI y localizar las fichas oficiales (Tokyo Marui, G&G, VFC, Specna Arms).
- Guardamanos M-LOK: faltan 7, 9, 10, 12 y 15 in, y el nº de ranuras de todos.
- Culatas: faltan mil-spec y tipo STR de réplica (las cifras halladas eran de la pieza real y no se usan).
- Cargadores: faltan alto, ancho y grosor de AEG y GBB de M4 con cota consistente.
- Réplicas: faltan Cyma CM.516, E&C EC-101 e ICS (reserva de IA, no consultada).

## Guardamanos M-LOK, cañón y culatas

| Producto | Parámetro | Valor | Confianza | Fuentes | Nota |
|---|---|---|---|---|---|
| Guardamanos M-LOK de réplica, nominal 7 in | longitud real | null | null | - | Sin dato público fiable de longitud real en mm ni de nº de ranuras. |
| Guardamanos M-LOK de réplica, nominal 9 in | longitud real | null | null | - | Hay listados de 9 in (Airsoft Artisan 9,3 in, ARES Octarms, Matrix) sin cifra en mm en lo consultado. |
| Guardamanos M-LOK de réplica, nominal 10 in | longitud real | null | null | - | Sin dato en mm. |
| Guardamanos M-LOK de réplica, nominal 12 in | longitud real | null | null | - | Sin dato en mm. |
| Angry Gun TR-style M-LOK, nominal 13 in | longitud real | 325 mm | baja | [redwolfairsoft.com](https://www.redwolfairsoft.com/angry-gun-tr-style-m-lok-handguard-rail-for-aeg-gbb-ptw-airsoft-m4-series-13-inch-black.html) | Una sola tienda; incluye calzos de tuerca de cañón. Nº de ranuras: null. |
| Airsoft Artisan MK16 M-LOK, nominal 13,5 in | longitud real | 343 mm | baja | [redwolfairsoft.com](https://www.redwolfairsoft.com/airsoft-artisan-mk16-13-5-inch-m-lok-handguard-rail-for-m4-m16-series-aeg-gbb-ptw-black.html) | 13,5 in = 342,9 mm, coherente con el nominal. Una sola tienda. Nº de ranuras: null. |
| Guardamanos M-LOK de réplica, nominal 15 in | longitud real | null | null | - | Sin dato en mm. |
| Guardamanos M-LOK de réplica (todas las tallas) | número de ranuras | null | null | - | Ninguna fuente consultada da el nº de ranuras ni el paso entre ellas. |
| Tokyo Marui M4A1 MWS (GBB) | cañón exterior | 355 mm | baja | [patrolbase.co.uk](https://www.patrolbase.co.uk/tokyo-marui-m4a1-mws-zet-system-gbbr) | Una tienda («355mm outer barrel, 180mm front RIS»). Un listado dio 381 mm y parece cifra del arma real; descartado. |
| Tokyo Marui M4A1 MWS (GBB) | longitud del guardamanos RIS delantero | 180 mm | baja | [patrolbase.co.uk](https://www.patrolbase.co.uk/tokyo-marui-m4a1-mws-zet-system-gbbr) | Misma tienda y cita que el cañón exterior. |
| Tokyo Marui M4A1 MWS (GBB) | cañón interior | 250 mm | media | [octagonairsoft.com](https://www.octagonairsoft.com/product-page/tokyo-marui-m4a1-mws-gbb-airsoft), [airsoftmania.eu](https://airsoftmania.eu/products/tokyo-marui-m4a1-mws-gas-blowback-rifle) | Dos tiendas coinciden; otras dan 230, 245 o 260 mm. Falta la ficha oficial de Tokyo Marui. |
| VFC VR16 M105 (carabina de 10 in) | cañón exterior | 254 mm | baja | [airsoftgi.com](https://airsoftgi.com/product/VFC-VR16-M105-M4-Carbine-AEG-Airsoft-Rifle-Black-17692) | Cifra nominal «10 inch» del listado, convertida (10 in = 254 mm); no es una medida. |
| PTS Magpul CTR (pieza de airsoft, con espaciador) | longitud cerrada | 197 mm | baja | [combatsportsupply.com](https://combatsportsupply.com/?p=26329) | 7,75 in. Una tienda. Las piezas PTS difieren algo de las reales. |
| PTS Magpul CTR (pieza de airsoft, con espaciador) | longitud abierta | 281 mm | baja | [combatsportsupply.com](https://combatsportsupply.com/?p=26329) | 11,05 in. Una tienda. |
| Culata tipo Magpul STR (réplica de airsoft) | longitud cerrada | null | null | - | Solo se encontraron cifras de la pieza real; no se usan (solo airsoft). Falta una ficha de réplica. |
| Culata tipo Magpul STR (réplica de airsoft) | longitud abierta | null | null | - | Igual que la cerrada. |
| Culata telescópica mil-spec (réplica de airsoft) | longitud cerrada | null | null | - | No hay cifra aislada de la culata de réplica; solo longitudes totales de réplica. |
| Culata telescópica mil-spec (réplica de airsoft) | longitud abierta | null | null | - | Igual que la cerrada. |

## Cargadores

| Producto | Parámetro | Valor | Confianza | Fuentes | Nota |
|---|---|---|---|---|---|
| Tokyo Marui M4A1 MWS (GBB), cargador metálico | capacidad | 35 bolas | media | [patrolbase.co.uk](https://www.patrolbase.co.uk/tokyo-marui-m4a1-mws-zet-system-gbbr), [octagonairsoft.com](https://www.octagonairsoft.com/product-page/tokyo-marui-m4a1-mws-gbb-airsoft) | Dos tiendas coinciden en 35 bolas. Alto/ancho/grosor: null. |
| Tokyo Marui M4A1 MWS (GBB), cargador metálico | alto | null | null | - | Sin dato público. |
| Tokyo Marui M4A1 MWS (GBB), cargador metálico | ancho | null | null | - | Sin dato público. |
| Tokyo Marui M4A1 MWS (GBB), cargador metálico | grosor | null | null | - | Sin dato público. |
| G&G 105 bolas (polímero), boca del cargador | frente-atrás en la boca | 63.8 mm | baja | [evike.com](https://www.evike.com/products/20017/reviews) | Medida de un comprador en una reseña. Tubo de alimentación Ø9,2 mm, 4,9 mm sobre la boca. |
| G&G 105 bolas (polímero), boca del cargador | lado a lado en la boca | 22.75 mm | baja | [evike.com](https://www.evike.com/products/20017/reviews) | Misma reseña. |
| G&G polímero 105 bolas | capacidad | 105 bolas | baja | [evike.com](https://www.evike.com/products/20017/reviews) | Dato del nombre del producto. |
| Novritsch M4 mid-cap Gen2 225 bolas | alto | 190 mm | baja | [us.novritsch.com](https://us.novritsch.com/product/m4-mid-cap-magazine-gen2-225bbs/) | Listado «3,15 × 1 × 7,5 in»; 7,5 in = 190 mm. Los ejes de 80 y 25 mm no vienen etiquetados; ancho y grosor: null. |
| Novritsch M4 mid-cap Gen2 225 bolas | capacidad | 225 bolas | baja | [us.novritsch.com](https://us.novritsch.com/product/m4-mid-cap-magazine-gen2-225bbs/) | Dato del nombre del producto. |
| Tornado M4/M16 150 bolas (largo) | longitud | 200 mm | baja | [atom-airsoft.fi](https://atom-airsoft.fi/en-bg/products/tornado-m4-m16-pitka-mid-cap-lipas-150-kuulaa-musta) | «Aproximadamente 20 cm». Una tienda. |
| Cargador AEG M4 estándar | alto | null | null | - | Sin cota consistente de fabricante; solo medidas sueltas de reseñas. |
| Cargador AEG M4 estándar | ancho | null | null | - | Sin cota consistente de fabricante; solo medidas sueltas de reseñas. |
| Cargador AEG M4 estándar | grosor | null | null | - | Sin cota consistente de fabricante; solo medidas sueltas de reseñas. |

## Silenciadores y rosca

| Producto | Parámetro | Valor | Confianza | Fuentes | Nota |
|---|---|---|---|---|---|
| Réplicas de silenciador para AEG M4 (rosca estándar) | rosca del cañón exterior | 14 mm (CCW) | media | [patrolbase.co.uk](https://www.patrolbase.co.uk/cyma-mock-silencer-for-14mm-ccw), [airsoft-legends.nl](https://www.airsoft-legends.nl/en/go/product/77135270), [airsoftjunkiez.com](https://airsoftjunkiez.com/knights-armament-kac-mock-silencer-556-qdc-airsoft-full-size-14-mm-ccw) | Tres listados coinciden en M14 a izquierdas (CCW). Algunas réplicas usan M14 CW. |
| CYMA mock suppressor 14 mm CCW | diámetro | 35 mm | baja | [patrolbase.co.uk](https://www.patrolbase.co.uk/cyma-mock-silencer-for-14mm-ccw) | Listado «130 mm x 35 mm». |
| CYMA mock suppressor 14 mm CCW | longitud | 130 mm | baja | [patrolbase.co.uk](https://www.patrolbase.co.uk/cyma-mock-silencer-for-14mm-ccw) | Misma tienda. El listado recomienda trazadoras de Ø máx. 28 mm. |
| Madbull Gemtech G5 | diámetro | 38 mm | baja | [airsoft-legends.nl](https://www.airsoft-legends.nl/en/go/product/77135270) | Una tienda. |
| Madbull Gemtech G5 | longitud | 175 mm | baja | [airsoft-legends.nl](https://www.airsoft-legends.nl/en/go/product/77135270) | Una tienda. |
| Tac 9 / WAU Force AC-543B F35x145 | diámetro | 35 mm | baja | [airsoftgi.com](https://airsoftgi.com/product/Tac-9-AC-543B-F35X145mm-WAU-Force-Airsoft-Silencer-Black-34275) | Deducido del nombre «F35X145mm». |
| Tac 9 / WAU Force AC-543B F35x145 | longitud | 145 mm | baja | [airsoftgi.com](https://airsoftgi.com/product/Tac-9-AC-543B-F35X145mm-WAU-Force-Airsoft-Silencer-Black-34275) | Deducido del nombre. |

## Longitudes totales de réplicas

| Producto | Parámetro | Valor | Confianza | Fuentes | Nota |
|---|---|---|---|---|---|
| Tokyo Marui M4A1 MWS (GBB) | longitud total, culata cerrada | 777 mm | media | [everydayairsoft.com](https://everydayairsoft.com/tokyo-marui-m4a1-mws-review), [airsoftmania.eu](https://airsoftmania.eu/products/tokyo-marui-m4a1-mws-gas-blowback-rifle), [krale.shop](https://www.krale.shop/uk/tokyo-marui-m4a1-mws/) | Varias tiendas dan 777; Everyday Airsoft redondea a 775. |
| Tokyo Marui M4A1 MWS (GBB) | longitud total, culata abierta | 854 mm | media | [everydayairsoft.com](https://everydayairsoft.com/tokyo-marui-m4a1-mws-review), [airsoftmania.eu](https://airsoftmania.eu/products/tokyo-marui-m4a1-mws-gas-blowback-rifle), [krale.shop](https://www.krale.shop/uk/tokyo-marui-m4a1-mws/) | Varias tiendas dan 854; Everyday Airsoft redondea a 860. |
| G&G CM16 Raider (corto) | longitud total | 776 mm | baja | [camouflage.ca](https://www.camouflage.ca/cm16-raider-cqb-airsoft-rifle) | No indica culata abierta o cerrada. Cañón interior 357 mm. |
| G&G CM16 Raider L | longitud total (rango por culata) | 785-889 mm | media | [airsoftextreme.com](https://www.airsoftextreme.com/cm16-raider-l-19223730.html), [mirtactical.com](https://mirtactical.com/airsoft/cm16-raider-l-airsoft-aeg/) | Dos tiendas dan 30,9-34,85 in (785-885 mm) y 31-35 in (787-889 mm). |
| G&G CM16 Raider 2.0 (M-LOK) | longitud total, culata cerrada | 711 mm | baja | [triggerairsoft.com](https://triggerairsoft.com/collections/aeg/products/g-g-cm16-raider-2-0-dst) | 28 in. Una tienda. |
| G&G CM16 Raider 2.0 (M-LOK) | longitud total, culata abierta | 812 mm | baja | [triggerairsoft.com](https://triggerairsoft.com/collections/aeg/products/g-g-cm16-raider-2-0-dst) | 32 in. Una tienda. |
| Specna Arms SA-C03 CORE | longitud total | 880 mm | baja | [camouflage.ca](https://www.camouflage.ca/specna-arms-core-sa-c03-airsoft-rifle) | «88 cm / 34,6 in»; no dice si es culata abierta. Otras tiendas dan 800-880 mm. Cañón interior 363 mm. |
| Specna Arms PDW CORE M-LOK Carbine | cañón interior | 275 mm | baja | [foxairsoft.com](https://www.foxairsoft.com/specna-arms-pdw-core-m-lok-carbine-chaos-bronze/) | Una tienda; guardamanos M-LOK con licencia RRA según ella. |
| VFC Avalon VR16 Saber Carbine M-LOK | longitud total (rango por culata) | 800-890 mm | media | [evike.com](https://www.evike.com/products/69876/Elite-Force-VFC-Avalon-Gen2-VR16-Saber-Carbine-M4-AEG-Rifle-w-M-LOK-Handguard/), [airsoftjunkiez.com](https://www.airsoftjunkiez.com/vfc-avalon-gen2-vr16-saber-carbine-m4-aeg-rifle-w-m-lok-handguard-bronze-gen-3-2024-update/) | Dos tiendas coinciden. Cañón interior ~363 mm. |
| VFC Avalon VR16 Saber CQB M-LOK | longitud total (rango por culata) | 680-750 mm | baja | [evike.com](https://www.evike.com/products/69873/Elite-Force-VFC-Avalon-Gen2-VR16-Saber-CQB-M4-AEG-Rifle/), [airsoftjunkiez.com](https://www.airsoftjunkiez.com/vfc-avalon-gen2-vr16-saber-cqb-m4-aeg-rifle-black-gen-3-2024-update/) | No se pudo confirmar que cada tienda aportase la cifra; cañón interior ~255 mm. |
| CYMA CM515 SR-16 | longitud total | 790 mm | baja | [airsoftzone.com](https://www.airsoftzone.com/en/p/cm515-sr-16-118334/) | 79 cm; cañón interior 380 mm. Es el CM515, no el CM.516. |
| E&C EC-601 Adasaurus (corto) | longitud total (rango por culata) | 720-800 mm | baja | [airsoft-guns.eu](https://www.airsoft-guns.eu/p/m4-adasaurus-short-e-c-ec-601) | Cañón interior 270 mm. |
| E&C EC-312 (KeyMod 13 in) | longitud total (rango por culata) | 800-880 mm | baja | [evike.com](https://www.evike.com/products/117701/E-and-C-Airsoft-M4-Airsoft-AEG-Rifle-Model-13.5-UX-Black/) | Cañón interior 363 mm. |
| ICS (M4) | longitud total | null | null | - | ICS tiene reserva de IA (diligencia 05-11-2026): no se consulta. |
| Todas las réplicas | ficha oficial del fabricante | null | null | - | Ninguna cifra procede de ficha oficial: Tokyo Marui dio 404 y varias webs fallo de TLS o 429; no se evadió ninguno. |

## Fotos de licencia abierta

Una referencia: *Ca m15a4.jpg* (Classic Army M15A4 SPC, dominio público, autor AlecMoody, Wikimedia Commons), 1024x851, en `assets-src/raw/referencias-cc/` (ignorada por git). Manifiesto en `catalogo/referencias-cc.json`. Baja resolución: sirve de referencia de proporciones, no de textura.
