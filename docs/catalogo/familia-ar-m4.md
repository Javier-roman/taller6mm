# Familia M4 / AR-15: mapa de elementos de réplicas de airsoft

> Generado a partir de `catalogo/ar-m4.json` (fuente de datos: ese JSON). Fecha de corte: 2026-11-13.

Este mapa lista **qué existe** en la familia M4/AR-15 de airsoft para planificar las oleadas de modelado (docs/05 §11). Es de **formas exteriores e interfaces de accesorios**: no contiene medidas de fabricación ni piezas reguladas, solo réplicas de airsoft (AEG, GBBR, HPA) y sus accesorios. Los nombres de marca son texto descriptivo, sin logos. **Ninguna cota está verificada**: todos los elementos están en estado `pendiente` hasta tener fuente, URL y fecha (principio 2).

**Total: 205 elementos en 13 zonas** (oleada 1: 85, oleada 2: 90, oleada 3: 30).

Leyenda. **Nivel**: fidelidad esperada (T0 ficha/silueta, T1 foto o plano re-iluminable, T2 modelo 3D fiel; docs/05 §2). **Oleada**: 1 = lo más repetido en el mercado, 2 = habitual, 3 = rara. **Interfaz**: id de `catalogo/interfaces.json`; los ids marcados con `*` son **propuestas nuevas** (ver al final). **Fuente de cotas**: FAB = ficha de fabricante de la réplica; CAT = ficha pública del fabricante de la pieza; STD = estándar público; MED = medición propia con calibre (docs/05 §7).

## Resumen por zona y oleada

| Zona | Oleada 1 | Oleada 2 | Oleada 3 | Total |
|---|---:|---:|---:|---:|
| A. Cuerpos y variantes de réplica | 11 | 14 | 4 | 29 |
| B1. Receptor superior (upper) | 5 | 6 | 1 | 12 |
| B2. Receptor inferior (lower) | 6 | 6 | 3 | 15 |
| B3. Pistoletes | 3 | 5 | 2 | 10 |
| B4. Culatas | 6 | 4 | 8 | 18 |
| B5. Tubos de culata | 3 | 3 | 1 | 7 |
| B6. Cañón exterior, bloque de gas y punto de mira | 4 | 9 | 0 | 13 |
| B7. Guardamanos | 15 | 9 | 3 | 27 |
| B8. Bocachas, silenciadores y simuladores | 6 | 9 | 2 | 17 |
| B9. Cargadores y pozo | 5 | 4 | 2 | 11 |
| B10. Miras mecánicas | 3 | 4 | 1 | 8 |
| B11. Ópticas y monturas | 7 | 9 | 2 | 18 |
| B12. Accesorios | 11 | 8 | 1 | 20 |
| **Total** | **85** | **90** | **30** | **205** |

## Orden de modelado de la oleada 1

Criterio: **lo que más réplicas del mercado comparten**. Primero lo que casi toda M4 tiene (receptor, cargador, pistolete, culata, guardamanos, bocacha) y, después, lo opcional. Las variantes completas de réplica se **componen** con estas piezas, no se modelan aparte.

| Orden | Zona | Elementos de oleada 1 | Por qué |
|---:|---|---:|---|
| 1 | B1. Receptor superior (upper) | 5 | Es la pieza que casi todas las réplicas M4 comparten y fija el raíl, la ventana y los puntos de montaje de lo demás. |
| 2 | B2. Receptor inferior (lower) | 6 | Va con el superior; define el pozo de cargador, el pistolete y el tubo de culata (las ranuras principales del banco). |
| 3 | B9. Cargadores y pozo | 5 | Un STANAG midcap/lowcap/highcap encaja en casi todas las AEG; el cargador de GBBR cubre la MWS de Javi. |
| 4 | B3. Pistoletes | 3 | Pocos modelos (A2, MOE, ergonómicos) cubren casi todo el mercado. |
| 5 | B5. Tubos de culata | 3 | Mil-spec y comercial: dos interfaces desbloquean todas las culatas. |
| 6 | B4. Culatas | 6 | CAR/6 posiciones y las tipo Magpul son lo más repetido en tiendas. |
| 7 | B7. Guardamanos | 15 | Longitudes (7, 9, 10, 12, 13,5) en M-LOK y quad rail: familias paramétricas, mucho SKU con poco modelado. |
| 8 | B8. Bocachas, silenciadores y simuladores | 6 | Apagallamas, frenos y silenciadores con la rosca de 14 mm: de las piezas más compradas. |
| 9 | B6. Cañón exterior, bloque de gas y punto de mira | 4 | Cañón exterior, bloque de gas y punto de mira: necesarios para el perfil de silueta completo. |
| 10 | B11. Ópticas y monturas | 7 | Red dot, holográfica y magnificador son los accesorios más montados. |
| 11 | B10. Miras mecánicas | 3 | BUIS y asa A2: completan el perfil de la réplica. |
| 12 | B12. Accesorios | 11 | Empuñaduras, linternas, láseres y anclajes de correa. |
| 13 | A. Cuerpos y variantes de réplica | 11 | Las variantes de réplica se componen con las piezas anteriores (base + piezas de serie, docs/05 §11.4): no se modelan antes. |

Dentro de cada zona, el orden es el de las tablas de abajo (los de oleada 1 primero). Piloto: la M.W.S. de Javi marca la primera combinación completa (cuerpo GBBR + pozo `pozo-gbbr-m4-mws`).

## A. Cuerpos y variantes de réplica

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Réplica M4A1 / M4 carabina AEG (`cuerpo-replica-m4a1-m4-carabina-aeg`) | longitud total con culata cerrada; longitud del cañón exterior; peso; formato de batería; tipo de gearbox (Ver. 2) | `picatinny-mil-std-1913`, `rosca-m14x1-ccw`, `tubo-culata-mil-spec`, `pozo-stanag-m4`, `gearbox-ver2` | — | T2 | 1 | FAB |
| Réplica M4 CQB / CQB-R AEG (`cuerpo-replica-m4-cqb-cqb-r-aeg`) | guardamanos corto con raíl; cañón corto (pendiente); culata CAR | `picatinny-mil-std-1913`, `rosca-m14x1-ccw`, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Réplica M4 RIS / RAS (M4A1 RIS) AEG (`cuerpo-replica-m4-ris-ras-m4a1-ris-aeg`) | guardamanos quad; longitud; peso | `picatinny-mil-std-1913`, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Réplica M16A2 AEG (`cuerpo-replica-m16a2-aeg`) | guardamanos A2; asa de transporte A2; culata fija A2 | `montaje-asa-a2`*, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Réplica Mk18 Mod 0 / Mod 1 AEG (`cuerpo-replica-mk18-mod-0-mod-1-aeg`) | guardamanos RAS corto; cañón corto; peso | `picatinny-mil-std-1913`, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Réplica M4 URX / estilo URX (`cuerpo-replica-m4-urx-estilo-urx`) | guardamanos M-LOK o KeyMod; longitud | `mlok`, `kmod`, `picatinny-mil-std-1913` | — | T2 | 1 | FAB |
| Réplica HK416 D10 / D14.5 AEG (`cuerpo-replica-hk416-d10-d14-5-aeg`) | guardamanos HK; pistón corto simulado; culata HK | `picatinny-mil-std-1913`, `mlok`, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| M.W.S. GBBR estándar (Tokyo Marui) (`cuerpo-m-w-s-gbbr-estandar-tokyo-marui`) | longitud; peso; cargador de gas; carcasa de recámara | `picatinny-mil-std-1913`, `rosca-m14x1-ccw`, `pozo-gbbr-m4-mws`* | — | T2 | 1 | FAB |
| M.W.S. M4A1 / URG-I / Mk18 (variantes Tokyo Marui) (`cuerpo-m-w-s-m4a1-urg-i-mk18-variantes-tokyo-marui`) | guardamanos; cañón exterior; mira | `pozo-gbbr-m4-mws`*, `picatinny-mil-std-1913` | — | T2 | 1 | FAB |
| Cuerpos de marcas conocidas: G&G / Cyma / Specna / APS / E&C (`cuerpo-cuerpos-de-marcas-conocidas-g-g-cyma-specna-aps-e-c`) | marca; grupo de gearbox; cargador; tolerancias de montaje | `picatinny-mil-std-1913`, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Cuerpos de marcas conocidas: VFC / Krytac / Classic Army / King Arms (`cuerpo-cuerpos-de-marcas-conocidas-vfc-krytac-classic-army-king-arms`) | marca; licencia (grupo B); grupo de gearbox | `picatinny-mil-std-1913`, `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Réplica M16A1 AEG (triangular, asa de transporte, culata fija) (`cuerpo-replica-m16a1-aeg-triangular-asa-de-transporte-culata-fija`) | longitud total; guardamanos triangular; mira trasera A1 | `montaje-asa-a2`*, `pozo-stanag-m4` | — | T2 | 2 | FAB |
| Réplica M16A4 / M16 flat-top AEG (`cuerpo-replica-m16a4-m16-flat-top-aeg`) | raíl superior largo; guardamanos RIS o A2 | `picatinny-mil-std-1913`, `pozo-stanag-m4` | — | T2 | 2 | FAB |
| Réplica M4 Block II / estilo Block II (`cuerpo-replica-m4-block-ii-estilo-block-ii`) | guardamanos moderno; culata de 6 posiciones | `mlok`, `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica HK416A5 / estilo URX (`cuerpo-replica-hk416a5-estilo-urx`) | guardamanos con raíl corto y M-LOK | `mlok`, `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica HK416 D10RS (`cuerpo-replica-hk416-d10rs`) | guardamanos RS; culata HK | `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica HK416 de 14.5 pulgadas (GBBR) (`cuerpo-replica-hk416-de-14-5-pulgadas-gbbr`) | longitud; peso; cargador de GBBR | `pozo-gbbr-m4-mws`* | — | T2 | 2 | FAB |
| Réplica Mk12 SPR / DMR estilo Mk12 (`cuerpo-replica-mk12-spr-dmr-estilo-mk12`) | cañón largo; óptica de bajo aumento; bípode | `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica SR-15 / Mk12 de cañón medio (`cuerpo-replica-sr-15-mk12-de-canon-medio`) | cañón medio; guardamanos free-float | `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica DMR / SPR de cañón largo (AEG) (`cuerpo-replica-dmr-spr-de-canon-largo-aeg`) | longitud de cañón; peso; gearbox reforzado | `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica AR-15 PDW / SBR de cañón muy corto (AEG) (`cuerpo-replica-ar-15-pdw-sbr-de-canon-muy-corto-aeg`) | cañón muy corto; culata mínima | `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica de estilo SIG MCX Virtus (`cuerpo-replica-de-estilo-sig-mcx-virtus`) | longitud; guardamanos M-LOK; culata plegable | `mlok`, `picatinny-mil-std-1913`, `pozo-mcx` | — | T2 | 2 | FAB |
| GBBR aftermarket tipo WA / WE / GHK (`cuerpo-gbbr-aftermarket-tipo-wa-we-ghk`) | compatibilidad de cargador; carcasa de recámara | `pozo-gbbr-m4-wa-ghk`*, `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Tokyo Marui NGRS (AEG de nueva generación) (`cuerpo-tokyo-marui-ngrs-aeg-de-nueva-generacion`) | gearbox NGRS; cargador; culata | `picatinny-mil-std-1913`, `pozo-stanag-m4` | — | T2 | 2 | FAB |
| Cuerpos de marcas conocidas: WE / KWA / GHK / Lancer / Evolution (`cuerpo-cuerpos-de-marcas-conocidas-we-kwa-ghk-lancer-evolution`) | marca; sistema de gas/AEG; compatibilidad | `picatinny-mil-std-1913` | — | T2 | 2 | FAB |
| Réplica pistol-style AR (sin culata, estilo pistolete AR) (`cuerpo-replica-pistol-style-ar-sin-culata-estilo-pistolete-ar`) | tubo de culata ausente; tirante o brazo estabilizador | `picatinny-mil-std-1913` | — | T2 | 3 | FAB |
| Réplica AR-10 / DMR 7,62 (estilo SR-25) (`cuerpo-replica-ar-10-dmr-7-62-estilo-sr-25`) | longitud; cargador de AR-10 de airsoft | `picatinny-mil-std-1913` | — | T2 | 3 | FAB |
| GBBR KWA / KSC-style (sistema propio) (`cuerpo-gbbr-kwa-ksc-style-sistema-propio`) | compatibilidad; cargador propio | `pozo-stanag-m4` | — | T2 | 3 | FAB |
| M4 HPA (réplica convertida a aire comprimido) (`cuerpo-m4-hpa-replica-convertida-a-aire-comprimido`) | línea de aire; regulador; cargador | `pozo-m4-hpa` | — | T2 | 3 | FAB |

## B1. Receptor superior (upper)

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Receptor superior A2 con asa de transporte (carry handle) integrada (`sup-receptor-superior-a2-con-asa-de-transporte-carry-handle-integrada`) | asa; ventana de eyección; cubierta; forward assist | `montaje-asa-a2`*, `union-superior-inferior-ar`* | `montaje-mira-trasera-a2`*, `tuerca-guardamanos-ar`* | T2 | 1 | FAB |
| Receptor superior flat-top (raíl superior Picatinny) (`sup-receptor-superior-flat-top-rail-superior-picatinny`) | longitud del raíl; forward assist; cubierta; ranura de eyección | `picatinny-mil-std-1913`, `union-superior-inferior-ar`* | `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | T2 | 1 | FAB |
| Receptor superior de cañón corto (CQB) (`sup-receptor-superior-de-canon-corto-cqb`) | longitud; extremo con raíl | `picatinny-mil-std-1913` | `tuerca-guardamanos-ar`* | T2 | 1 | FAB |
| Receptor superior GBBR estilo MWS (cerrojo, recámara y cubierta funcionales) (`sup-receptor-superior-gbbr-estilo-mws-cerrojo-recamara-y-cubierta-funcionales`) | forma de cubierta; recámara; cerrojo | `picatinny-mil-std-1913`, `union-superior-inferior-ar`* | `picatinny-mil-std-1913` | T2 | 1 | FAB |
| Receptor superior HK416 (forma y raíl propios) (`sup-receptor-superior-hk416-forma-y-rail-propios`) | raíl superior; ventana | `picatinny-mil-std-1913` | `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | T2 | 1 | FAB |
| Receptor superior A1 (sin forward assist, con asa fija) (`sup-receptor-superior-a1-sin-forward-assist-con-asa-fija`) | forma de la ventana de eyección; asa; ausencia de forward assist | `montaje-asa-a2`*, `union-superior-inferior-ar`* | `rosca-m14x1-ccw`, `tuerca-guardamanos-ar`* | T2 | 2 | FAB |
| Receptor superior flat-top con ventana de eyección ampliada (Gen 2 o forjado) (`sup-receptor-superior-flat-top-con-ventana-de-eyeccion-ampliada-gen-2-o-forjado`) | forma de la ventana de eyección; deflector; forma del refuerzo | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T2 | 2 | FAB |
| Receptor superior Gen 3 / Gen 4 / forjado de marca (variantes de réplica) (`sup-receptor-superior-gen-3-gen-4-forjado-de-marca-variantes-de-replica`) | ventana; hop-up; tolerancia de carcasa | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T2 | 2 | FAB |
| Cubierta de la ventana de eyección (dust cover) (`sup-cubierta-de-la-ventana-de-eyeccion-dust-cover`) | forma y abertura; resorte; bisagra | `ranura-cubierta-eyeccion`* | — | T1 | 2 | FAB |
| Asa de armado (charging handle) y palanca (`sup-asa-de-armado-charging-handle-y-palanca`) | forma del asa; palanca ambidiestra; funcional o fijo | `montaje-asa-carga-ar`* | — | T1 | 2 | FAB |
| Cubierta de hop-up / ventana de ajuste (`sup-cubierta-de-hop-up-ventana-de-ajuste`) | tipo de ventana; ruleta o palanca de ajuste | — | — | T1 | 2 | FAB |
| Forward assist (botón lateral) (`sup-forward-assist-boton-lateral`) | forma del botón; funcional o fijo | — | — | T1 | 3 | FAB |

## B2. Receptor inferior (lower)

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Receptor inferior AEG estándar (M4/M16, gearbox Ver. 2) (`inf-receptor-inferior-aeg-estandar-m4-m16-gearbox-ver-2`) | selector; gatillo; guardamonte; pozo de cargador; hueco para pistolete | `montaje-pistolete-ar`*, `tubo-culata-mil-spec`, `gearbox-ver2`, `pozo-stanag-m4`, `union-superior-inferior-ar`* | `pozo-stanag-m4`, `montaje-pistolete-ar`*, `tubo-culata-mil-spec`, `tubo-culata-comercial` | T2 | 1 | FAB |
| Receptor inferior AEG con pistolete adaptable (`inf-receptor-inferior-aeg-con-pistolete-adaptable`) | ranura del pistolete; tornillo; forma del cuello | `montaje-pistolete-ar`* | — | T2 | 1 | FAB |
| Receptor inferior GBBR estilo MWS (`inf-receptor-inferior-gbbr-estilo-mws`) | selector; seguro de cargador; pozo de cargador; compatibilidad de pistolete | `pozo-gbbr-m4-mws`*, `montaje-pistolete-ar`*, `tubo-culata-mil-spec` | `pozo-gbbr-m4-mws`*, `tubo-culata-mil-spec` | T2 | 1 | FAB |
| Receptor inferior estilo HK416 (`inf-receptor-inferior-estilo-hk416`) | selector ambidiestro; seguro de cargador; pistolete HK | `montaje-pistolete-ar`*, `pozo-stanag-m4` | `pozo-stanag-m4`, `tubo-culata-mil-spec` | T2 | 1 | FAB |
| Gatillo y guardamonte estándar (`inf-gatillo-y-guardamonte-estandar`) | tamaño de guardamonte; forma del gatillo | — | — | T1 | 1 | FAB |
| Pozo de cargador (magazine well) estándar (`inf-pozo-de-cargador-magazine-well-estandar`) | abertura; perfil del pozo | `pozo-stanag-m4` | `pozo-stanag-m4` | T2 | 1 | FAB |
| Receptor inferior ambidiestro (selector y seguro de cargador a ambos lados) (`inf-receptor-inferior-ambidiestro-selector-y-seguro-de-cargador-a-ambos-lados`) | selector doble; botón de cargador doble; placa | `pozo-stanag-m4` | — | T2 | 2 | FAB |
| Selector (palanca de modo) estándar (`inf-selector-palanca-de-modo-estandar`) | longitud; cierre; marcas | — | — | T1 | 2 | FAB |
| Selector ambidiestro / de palanca corta (`inf-selector-ambidiestro-de-palanca-corta`) | palancas; ángulo de recorrido | — | — | T1 | 2 | FAB |
| Guardamonte ampliado (para guantes) (`inf-guardamonte-ampliado-para-guantes`) | perfil; guarda | — | — | T1 | 2 | FAB |
| Pozo de cargador acampanado (flared, tipo Magpul) (`inf-pozo-de-cargador-acampanado-flared-tipo-magpul`) | abertura ampliada; perfil | `pozo-stanag-m4` | `pozo-stanag-m4` | T1 | 2 | FAB |
| Seguro de cargador (botón de expulsión) estándar (`inf-seguro-de-cargador-boton-de-expulsion-estandar`) | tamaño del botón; placa | — | — | T1 | 2 | FAB |
| Gatillo plano o curvo aftermarket (`inf-gatillo-plano-o-curvo-aftermarket`) | geometría | — | — | T1 | 3 | FAB |
| Seguro de cargador ambidiestro / ampliado (`inf-seguro-de-cargador-ambidiestro-ampliado`) | botón | — | — | T1 | 3 | FAB |
| Retén de cerrojo (bolt catch) exterior (`inf-reten-de-cerrojo-bolt-catch-exterior`) | palanca | — | — | T1 | 3 | FAB |

## B3. Pistoletes

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Pistolete A2 estándar de réplica AEG (`pist-pistolete-a2-estandar-de-replica-aeg`) | forma del cuello; tamaño; compartimento de cableado | `montaje-pistolete-ar`* | — | T1 | 1 | CAT |
| Pistolete MOE de polímero (`pist-pistolete-moe-de-polimero`) | textura; cuello; compartimento | `montaje-pistolete-ar`* | — | T1 | 1 | CAT |
| Pistolete de GBBR (MWS / compatible) (`pist-pistolete-de-gbbr-mws-compatible`) | forma; cuello; espacio para selector | `montaje-pistolete-ar`* | — | T1 | 1 | CAT |
| Pistolete A1 (triangular, ranurado) (`pist-pistolete-a1-triangular-ranurado`) | ranuras; perfil | `montaje-pistolete-ar`* | — | T1 | 2 | CAT |
| Pistolete MOE-K / de cuello corto (`pist-pistolete-moe-k-de-cuello-corto`) | ángulo; cuello; textura | `montaje-pistolete-ar`* | — | T1 | 2 | CAT |
| Pistolete ergonómico tipo A (ergo, ranuras laterales) (`pist-pistolete-ergonomico-tipo-a-ergo-ranuras-laterales`) | ranuras; perfil | `montaje-pistolete-ar`* | — | T1 | 2 | CAT |
| Pistolete ergonómico tipo B (ergo con apoyo del pulgar) (`pist-pistolete-ergonomico-tipo-b-ergo-con-apoyo-del-pulgar`) | perfil; apoyo | `montaje-pistolete-ar`* | — | T1 | 2 | CAT |
| Pistolete HK416 (original y de réplica) (`pist-pistolete-hk416-original-y-de-replica`) | forma; ranura; cuello | `montaje-pistolete-ar`* | — | T1 | 2 | CAT |
| Pistolete con compartimento de batería (`pist-pistolete-con-compartimento-de-bateria`) | volumen interior de referencia; tapa | `montaje-pistolete-ar`*, `montaje-culata-bateria-ar`* | — | T1 | 3 | CAT |
| Pistolete con cuello reducido o relleno (`pist-pistolete-con-cuello-reducido-o-relleno`) | ángulo; textura | `montaje-pistolete-ar`* | — | T1 | 3 | CAT |

## B4. Culatas

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Culata CAR (M4 de 6 posiciones, tipo M4 original) (`culata-culata-car-m4-de-6-posiciones-tipo-m4-original`) | longitud mín. y máx.; nº de posiciones; cantonera | `tubo-culata-mil-spec`, `tubo-culata-comercial` | — | T1 | 1 | CAT |
| Culata de 6 posiciones (tipo carabina, genérica) (`culata-culata-de-6-posiciones-tipo-carabina-generica`) | longitud mín.-máx.; nº de posiciones; cantonera | `tubo-culata-mil-spec`, `tubo-culata-comercial` | `montaje-culata-bateria-ar`*, `anclaje-correa-qd-socket` | T1 | 1 | CAT |
| Culata estilo Magpul CTR (`culata-culata-estilo-magpul-ctr`) | longitud; posición; cantonera; pestaña de mejilla | `tubo-culata-mil-spec` | `anclaje-correa-qd-socket` | T1 | 1 | CAT |
| Culata estilo Magpul MOE (`culata-culata-estilo-magpul-moe`) | longitud; cantonera; forma; compartimento | `tubo-culata-mil-spec` | `anclaje-correa-qd-socket` | T1 | 1 | CAT |
| Culata estilo Magpul STR (`culata-culata-estilo-magpul-str`) | longitud; pestaña; cantonera | `tubo-culata-mil-spec` | `anclaje-correa-qd-socket` | T1 | 1 | CAT |
| Culata HK416 (corredera propia) (`culata-culata-hk416-corredera-propia`) | longitud; perfil; cantonera | `tubo-culata-comercial` | `anclaje-correa-qd-socket` | T1 | 1 | CAT |
| Culata fija A2 (carabina larga, con compartimento) (`culata-culata-fija-a2-carabina-larga-con-compartimento`) | longitud; tipo de cantonera; compartimento | `tubo-culata-mil-spec` | — | T1 | 2 | CAT |
| Culata de 7 posiciones (`culata-culata-de-7-posiciones`) | longitud mín.-máx.; nº de posiciones | `tubo-culata-mil-spec`, `tubo-culata-comercial` | `montaje-culata-bateria-ar`* | T1 | 2 | CAT |
| Culata estilo Magpul ACS / ACS-L (`culata-culata-estilo-magpul-acs-acs-l`) | longitud; cantonera; posición | `tubo-culata-mil-spec` | `anclaje-correa-qd-socket` | T1 | 2 | CAT |
| Culata plegable lateral con adaptador AR (`culata-culata-plegable-lateral-con-adaptador-ar`) | longitud plegada y desplegada; bisagra; cantonera | `montaje-culata-plegable-ar`* | — | T1 | 2 | CAT |
| Culata fija A1 (más corta, sin compartimento) (`culata-culata-fija-a1-mas-corta-sin-compartimento`) | longitud; cantonera | `tubo-culata-mil-spec` | — | T1 | 3 | CAT |
| Culata plegable de bisagra estilo SIG MCX (`culata-culata-plegable-de-bisagra-estilo-sig-mcx`) | longitud; bisagra; cantonera | `montaje-culata-plegable-ar`* | — | T1 | 3 | CAT |
| Culata estilo Magpul PRS (apoyo para DMR) (`culata-culata-estilo-magpul-prs-apoyo-para-dmr`) | longitud; apoyo de mejilla; ajuste | `tubo-culata-mil-spec`, `tubo-culata-comercial` | — | T1 | 3 | CAT |
| Culata mínima de PDW / SBR (tipo cuchara o tirante) (`culata-culata-minima-de-pdw-sbr-tipo-cuchara-o-tirante`) | longitud; perfil | `tubo-culata-mil-spec` | — | T1 | 3 | CAT |
| Culata con tirante estabilizador (pistol brace) (`culata-culata-con-tirante-estabilizador-pistol-brace`) | longitud; perfil; ajuste | `tubo-culata-mil-spec`, `tubo-culata-comercial` | — | T1 | 3 | CAT |
| Cantonera de goma / de impacto (`culata-cantonera-de-goma-de-impacto`) | forma; material; anclaje | — | — | T1 | 3 | CAT |
| Apoyo de mejilla (cheek rest) adaptable (`culata-apoyo-de-mejilla-cheek-rest-adaptable`) | altura; forma; fijación | — | — | T1 | 3 | CAT |
| Adaptador de culata de otro sistema (a AR) (`culata-adaptador-de-culata-de-otro-sistema-a-ar`) | longitud; tipo de adaptador | `montaje-culata-plegable-ar`*, `tubo-culata-mil-spec` | — | T1 | 3 | CAT |

## B5. Tubos de culata

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Tubo de culata mil-spec (AR-15) (`tubo-tubo-de-culata-mil-spec-ar-15`) | longitud; diámetro; tipo de pasador | `tubo-culata-mil-spec` | `tubo-culata-mil-spec` | T1 | 1 | STD |
| Tubo de culata comercial (AR-15) (`tubo-tubo-de-culata-comercial-ar-15`) | longitud; diámetro; tipo de pasador | `tubo-culata-comercial` | `tubo-culata-comercial` | T1 | 1 | STD |
| Tubo de culata de AEG (cableado dentro) (`tubo-tubo-de-culata-de-aeg-cableado-dentro`) | longitud; pasaje de cable; tipo de rosca | `tubo-culata-airsoft-m4-ligero` | `tubo-culata-airsoft-m4-ligero` | T1 | 1 | FAB |
| Tubo de culata de GBBR (sin cableado, con tampón de retroceso) (`tubo-tubo-de-culata-de-gbbr-sin-cableado-con-tampon-de-retroceso`) | longitud; diámetro; tipo de pasador | `tubo-culata-mil-spec` | `tubo-culata-mil-spec` | T1 | 2 | FAB |
| Tubo de culata corto (CAR) con anillo y tuerca (`tubo-tubo-de-culata-corto-car-con-anillo-y-tuerca`) | longitud; anillo | `tubo-culata-mil-spec` | — | T1 | 2 | CAT |
| Tubo de culata de HK416 (propio) (`tubo-tubo-de-culata-de-hk416-propio`) | longitud; pasaje | `tubo-culata-comercial` | — | T1 | 2 | CAT |
| Anillo y tuerca del tubo de culata (castle nut y placa de retención) (`tubo-anillo-y-tuerca-del-tubo-de-culata-castle-nut-y-placa-de-retencion`) | forma; diámetro | `tubo-culata-mil-spec` | — | T1 | 3 | CAT |

## B6. Cañón exterior, bloque de gas y punto de mira

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Cañón exterior de M4A1 (perfil estándar con punto de mira) (`canon-canon-exterior-de-m4a1-perfil-estandar-con-punto-de-mira`) | longitud; diámetro; perfil | `montaje-bloque-gas-ar`*, `rosca-m14x1-ccw` | `rosca-m14x1-ccw`, `montaje-bloque-gas-ar`* | T1 | 1 | CAT |
| Cañón exterior CQB (corto) (`canon-canon-exterior-cqb-corto`) | longitud; diámetro | `montaje-bloque-gas-ar`* | `rosca-m14x1-ccw` | T1 | 1 | CAT |
| Bloque de gas bajo perfil (bajo guardamanos) (`canon-bloque-de-gas-bajo-perfil-bajo-guardamanos`) | forma; ancho | `montaje-bloque-gas-ar`* | — | T1 | 1 | CAT |
| Punto de mira de bloque de gas (tipo poste A2) (`canon-punto-de-mira-de-bloque-de-gas-tipo-poste-a2`) | altura; forma del poste | `montaje-bloque-gas-ar`* | — | T1 | 1 | CAT |
| Cañón exterior M16 con perfil A2 (pesado) (`canon-canon-exterior-m16-con-perfil-a2-pesado`) | longitud; diámetro del perfil | `montaje-bloque-gas-ar`* | `rosca-m14x1-ccw` | T1 | 2 | CAT |
| Cañón exterior largo (DMR / SPR) (`canon-canon-exterior-largo-dmr-spr`) | longitud; diámetro; perfil | `montaje-bloque-gas-ar`* | `rosca-m14x1-ccw` | T1 | 2 | CAT |
| Cañón exterior de HK416 (liso, tipo pistón) (`canon-canon-exterior-de-hk416-liso-tipo-piston`) | longitud; diámetro | `montaje-bloque-gas-ar`* | `rosca-m14x1-ccw` | T1 | 2 | CAT |
| Cañón exterior de GBBR (rosca de boca CCW) (`canon-canon-exterior-de-gbbr-rosca-de-boca-ccw`) | longitud; diámetro | `montaje-bloque-gas-ar`* | `rosca-m14x1-ccw` | T1 | 2 | CAT |
| Bloque de gas tipo A2 (con alojamiento de bayoneta) (`canon-bloque-de-gas-tipo-a2-con-alojamiento-de-bayoneta`) | forma del bloque; pasadores | `montaje-bloque-gas-ar`* | — | T1 | 2 | CAT |
| Bloque de gas con raíl (estilo Picatinny) (`canon-bloque-de-gas-con-rail-estilo-picatinny`) | longitud de raíl; forma | `montaje-bloque-gas-ar`*, `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Punto de mira abatible (flip-up) sobre bloque de gas (`canon-punto-de-mira-abatible-flip-up-sobre-bloque-de-gas`) | altura; forma | `montaje-bloque-gas-ar`*, `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Tuerca de cañón / delta ring estándar (`canon-tuerca-de-canon-delta-ring-estandar`) | diámetro; perfil | `tuerca-guardamanos-ar`* | `tuerca-guardamanos-ar`* | T1 | 2 | CAT |
| Adaptador de rosca de boca (CW <-> CCW) (`canon-adaptador-de-rosca-de-boca-cw-ccw`) | rosca de entrada; rosca de salida | `rosca-m14x1-ccw`, `rosca-m14x1-cw` | `rosca-m14x1-ccw`, `rosca-m14x1-cw` | T1 | 2 | STD |

## B7. Guardamanos

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Guardamanos A2 de dos mitades (con escudo térmico) (`gm-guardamanos-a2-de-dos-mitades-con-escudo-termico`) | longitud; perfil; fijación | `tuerca-guardamanos-ar`* | — | T1 | 1 | CAT |
| Guardamanos M4 CAR de dos mitades (corto con escudo) (`gm-guardamanos-m4-car-de-dos-mitades-corto-con-escudo`) | longitud; perfil | `tuerca-guardamanos-ar`* | — | T1 | 1 | CAT |
| Guardamanos M4 RIS (Rail Interface System) (`gm-guardamanos-m4-ris-rail-interface-system`) | longitud; nº de ranuras Picatinny | `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos quad rail de 7 pulgadas (`gm-guardamanos-quad-rail-de-7-pulgadas`) | longitud (pulgadas); ranuras | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos quad rail de 9 pulgadas (`gm-guardamanos-quad-rail-de-9-pulgadas`) | longitud (pulgadas); ranuras | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos quad rail de 10 pulgadas (`gm-guardamanos-quad-rail-de-10-pulgadas`) | longitud (pulgadas); ranuras | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos M-LOK de 7 pulgadas (`gm-guardamanos-m-lok-de-7-pulgadas`) | longitud; ranuras M-LOK por cara | `mlok`, `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos M-LOK de 9 pulgadas (`gm-guardamanos-m-lok-de-9-pulgadas`) | longitud; ranuras | `mlok`, `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos M-LOK de 10 pulgadas (`gm-guardamanos-m-lok-de-10-pulgadas`) | longitud; ranuras | `mlok`, `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos M-LOK de 12 pulgadas (`gm-guardamanos-m-lok-de-12-pulgadas`) | longitud; ranuras | `mlok`, `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos M-LOK de 13,5 pulgadas (`gm-guardamanos-m-lok-de-13-5-pulgadas`) | longitud; ranuras | `mlok`, `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos free-float octogonal (estilo Daniel Defense/Noveske) (`gm-guardamanos-free-float-octogonal-estilo-daniel-defense-noveske`) | longitud; perfil octogonal | `picatinny-mil-std-1913`, `mlok`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos HK416 de raíl largo (`gm-guardamanos-hk416-de-rail-largo`) | longitud; raíles; hueco para batería | `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos de Mk18 (RAS corto) (`gm-guardamanos-de-mk18-ras-corto`) | longitud; ranuras | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos de MWS (Tokyo Marui o compatible) (`gm-guardamanos-de-mws-tokyo-marui-o-compatible`) | longitud; tipo | `picatinny-mil-std-1913`, `mlok` | `mlok`, `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Guardamanos M4 RAS (con paneles de agarre) (`gm-guardamanos-m4-ras-con-paneles-de-agarre`) | longitud; paneles | `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos quad rail de 12 pulgadas (`gm-guardamanos-quad-rail-de-12-pulgadas`) | longitud (pulgadas); ranuras | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos M-LOK de 15 pulgadas (`gm-guardamanos-m-lok-de-15-pulgadas`) | longitud; ranuras | `mlok`, `picatinny-mil-std-1913`, `tuerca-guardamanos-ar`* | `mlok`, `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos KeyMod de 7 pulgadas (`gm-guardamanos-keymod-de-7-pulgadas`) | longitud; orificios | `kmod`, `picatinny-mil-std-1913` | `kmod`, `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos KeyMod de 10 pulgadas (`gm-guardamanos-keymod-de-10-pulgadas`) | longitud; orificios | `kmod`, `picatinny-mil-std-1913` | `kmod`, `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos KeyMod de 12 pulgadas (`gm-guardamanos-keymod-de-12-pulgadas`) | longitud; orificios | `kmod`, `picatinny-mil-std-1913` | `kmod`, `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos slim de tubo redondo con ranuras (`gm-guardamanos-slim-de-tubo-redondo-con-ranuras`) | longitud; perfil redondo | `mlok`, `tuerca-guardamanos-ar`* | `mlok` | T1 | 2 | CAT |
| Guardamanos HK416A5 / estilo URX (`gm-guardamanos-hk416a5-estilo-urx`) | longitud; ranuras M-LOK; raíl | `mlok`, `picatinny-mil-std-1913` | `mlok`, `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Guardamanos con hueco de batería (`gm-guardamanos-con-hueco-de-bateria`) | volumen de referencia; tapa | `montaje-culata-bateria-ar`* | — | T1 | 2 | CAT |
| Guardamanos quad rail de 15 pulgadas (`gm-guardamanos-quad-rail-de-15-pulgadas`) | longitud (pulgadas); ranuras | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 3 | CAT |
| Guardamanos KeyMod de 15 pulgadas (`gm-guardamanos-keymod-de-15-pulgadas`) | longitud; orificios | `kmod`, `picatinny-mil-std-1913` | `kmod`, `picatinny-mil-std-1913` | T1 | 3 | CAT |
| Guardamanos de Mk12 / SPR (free-float largo) (`gm-guardamanos-de-mk12-spr-free-float-largo`) | longitud; perfil | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 3 | CAT |

## B8. Bocachas, silenciadores y simuladores

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Bocacha A1 (cuatro ranuras, birdcage simple) (`boca-bocacha-a1-cuatro-ranuras-birdcage-simple`) | longitud; diámetro; rosca | `rosca-m14x1-ccw` | — | T1 | 1 | CAT |
| Bocacha A2 (compensador cerrado por abajo) (`boca-bocacha-a2-compensador-cerrado-por-abajo`) | longitud; diámetro; rosca | `rosca-m14x1-ccw` | — | T1 | 1 | CAT |
| Apagallamas de jaula (birdcage) (`boca-apagallamas-de-jaula-birdcage`) | longitud; diámetro; rosca | `rosca-m14x1-ccw` | — | T1 | 1 | CAT |
| Freno de boca (muzzle brake) estándar (`boca-freno-de-boca-muzzle-brake-estandar`) | longitud; diámetro; rosca | `rosca-m14x1-ccw` | — | T1 | 1 | CAT |
| Silenciador / simulador corto (cuerpo cilíndrico) (`boca-silenciador-simulador-corto-cuerpo-cilindrico`) | longitud; diámetro; rosca | `rosca-m14x1-ccw`, `rosca-m14x1-cw` | — | T1 | 1 | CAT |
| Silenciador / simulador medio (`boca-silenciador-simulador-medio`) | longitud; diámetro | `rosca-m14x1-ccw`, `rosca-m14x1-cw` | — | T1 | 1 | CAT |
| Bocacha A3 (A2 con puntas abiertas) (`boca-bocacha-a3-a2-con-puntas-abiertas`) | longitud; diámetro | `rosca-m14x1-ccw` | — | T1 | 2 | CAT |
| Apagallamas de rejilla (tipo bastón de tenedor) (`boca-apagallamas-de-rejilla-tipo-baston-de-tenedor`) | longitud; diámetro | `rosca-m14x1-ccw` | — | T1 | 2 | CAT |
| Apagallamas largo de cuatro pinzas (`boca-apagallamas-largo-de-cuatro-pinzas`) | longitud; diámetro | `rosca-m14x1-ccw` | — | T1 | 2 | CAT |
| Freno de boca cónico / de piña (`boca-freno-de-boca-conico-de-pina`) | longitud; diámetro | `rosca-m14x1-ccw` | — | T1 | 2 | CAT |
| Compensador de boca (sin supresión) (`boca-compensador-de-boca-sin-supresion`) | longitud; diámetro | `rosca-m14x1-ccw` | — | T1 | 2 | CAT |
| Bocacha con adaptador de silenciador (QD) (`boca-bocacha-con-adaptador-de-silenciador-qd`) | longitud; rosca; sistema QD | `rosca-m14x1-ccw`, `montaje-bocacha-qd`* | `montaje-bocacha-qd`* | T1 | 2 | CAT |
| Silenciador / simulador largo (`boca-silenciador-simulador-largo`) | longitud; diámetro | `rosca-m14x1-ccw`, `rosca-m14x1-cw` | — | T1 | 2 | CAT |
| Silenciador con interfaz QD (`boca-silenciador-con-interfaz-qd`) | longitud; diámetro; sistema QD | `montaje-bocacha-qd`* | — | T1 | 2 | CAT |
| Trazadora de boca (tracer) con rosca (`boca-trazadora-de-boca-tracer-con-rosca`) | longitud; diámetro; rosca | `rosca-m14x1-ccw` | — | T1 | 2 | CAT |
| Silenciador integral (cañón con silenciador de AEG/DMR) (`boca-silenciador-integral-canon-con-silenciador-de-aeg-dmr`) | longitud total; diámetro | `rosca-m14x1-ccw` | — | T1 | 3 | CAT |
| Simulador de supresor cerámico (airsoft) (`boca-simulador-de-supresor-ceramico-airsoft`) | longitud; diámetro | `rosca-m14x1-ccw` | — | T1 | 3 | CAT |

## B9. Cargadores y pozo

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Cargador STANAG midcap (120 a 150 bolas) (`carg-cargador-stanag-midcap-120-a-150-bolas`) | capacidad; longitud; ancho; perfil | `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Cargador STANAG lowcap (30 a 80 bolas) (`carg-cargador-stanag-lowcap-30-a-80-bolas`) | capacidad; longitud; perfil | `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Cargador STANAG highcap (300 a 500 bolas) (`carg-cargador-stanag-highcap-300-a-500-bolas`) | capacidad; longitud; perfil; ruleta | `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Cargador estilo Magpul PMAG (aspecto exterior) (`carg-cargador-estilo-magpul-pmag-aspecto-exterior`) | capacidad; longitud; curvatura | `pozo-stanag-m4` | — | T2 | 1 | FAB |
| Cargador de GBBR Tokyo Marui MWS (gas) (`carg-cargador-de-gbbr-tokyo-marui-mws-gas`) | capacidad; depósito de gas | `pozo-gbbr-m4-mws`* | — | T2 | 1 | FAB |
| Cargador STANAG highcap con rueda de carga (`carg-cargador-stanag-highcap-con-rueda-de-carga`) | capacidad; longitud; rueda | `pozo-stanag-m4` | — | T2 | 2 | FAB |
| Cargador metálico de muelle (STANAG lowcap de réplica) (`carg-cargador-metalico-de-muelle-stanag-lowcap-de-replica`) | capacidad; longitud | `pozo-stanag-m4` | — | T2 | 2 | FAB |
| Cargador de GBBR aftermarket (WA/WE-GHK) (`carg-cargador-de-gbbr-aftermarket-wa-we-ghk`) | capacidad; depósito de gas | `pozo-gbbr-m4-wa-ghk`* | — | T2 | 2 | FAB |
| Placa de pozo (magazine well) estilo MWS/STANAG (`carg-placa-de-pozo-magazine-well-estilo-mws-stanag`) | perfil; espesor | `pozo-stanag-m4` | — | T1 | 2 | FAB |
| Cargador HPA (sin muelle, con tubo de aire) (`carg-cargador-hpa-sin-muelle-con-tubo-de-aire`) | capacidad; conexión | `pozo-m4-hpa` | — | T2 | 3 | FAB |
| Acople de cargadores (coupler) (`carg-acople-de-cargadores-coupler`) | perfil; doble cargador | `pozo-stanag-m4` | — | T1 | 3 | FAB |

## B10. Miras mecánicas

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Asa de transporte A2 con mira trasera integrada (`mira-asa-de-transporte-a2-con-mira-trasera-integrada`) | longitud; ruedas de deriva y elevación | `montaje-asa-a2`* | `montaje-mira-trasera-a2`* | T2 | 1 | FAB |
| BUIS trasera abatible (back-up iron sight) (`mira-buis-trasera-abatible-back-up-iron-sight`) | altura; apertura; fijación | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| BUIS delantera abatible (`mira-buis-delantera-abatible`) | altura; poste | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Asa de transporte desmontable con raíl (`mira-asa-de-transporte-desmontable-con-rail`) | longitud; altura; raíl | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Mira abatible de 45 grados (offset) (`mira-mira-abatible-de-45-grados-offset`) | altura; ángulo | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Mira trasera de apertura fija (tipo A1) (`mira-mira-trasera-de-apertura-fija-tipo-a1`) | apertura; altura | `montaje-flip-up-picatinny`* | — | T1 | 2 | CAT |
| Mira abatible de bloque de gas (frontal) (`mira-mira-abatible-de-bloque-de-gas-frontal`) | altura | `montaje-bloque-gas-ar`* | — | T1 | 2 | CAT |
| Mira de anillo (ghost ring) o apertura ancha (`mira-mira-de-anillo-ghost-ring-o-apertura-ancha`) | apertura; altura | `picatinny-mil-std-1913` | — | T1 | 3 | CAT |

## B11. Ópticas y monturas

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Red dot compacta estilo Aimpoint Micro (tubular, con montura) (`opt-red-dot-compacta-estilo-aimpoint-micro-tubular-con-montura`) | longitud; diámetro de tubo; montaje | `huella-aimpoint-micro`*, `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Red dot estilo Aimpoint CompM4 / T1 (con anillos) (`opt-red-dot-estilo-aimpoint-compm4-t1-con-anillos`) | longitud; diámetro; anillos | `anillo-optica-30mm`, `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Red dot cerrada estilo Holosun / Vortex (`opt-red-dot-cerrada-estilo-holosun-vortex`) | longitud; altura; ancho | `huella-holosun-k`, `huella-t1-micro`, `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Holográfica estilo EOTech 552 / 553 (`opt-holografica-estilo-eotech-552-553`) | longitud; ancho; altura | `huella-eotech-xps`*, `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Holográfica estilo EOTech EXPS / XPS (`opt-holografica-estilo-eotech-exps-xps`) | longitud; ancho; altura | `huella-eotech-xps`*, `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Magnificador 3x (en raíl, abatible) (`opt-magnificador-3x-en-rail-abatible`) | longitud; altura; ancho | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Montura de elevación (riser / QD) de red dot (`opt-montura-de-elevacion-riser-qd-de-red-dot`) | altura de elevación; QD | `picatinny-mil-std-1913` | `huella-aimpoint-micro`*, `huella-t1-micro` | T1 | 1 | CAT |
| Red dot de montaje en raíl (micro, estilo RMR) (`opt-red-dot-de-montaje-en-rail-micro-estilo-rmr`) | longitud; altura | `huella-rmr`, `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Holográfica de montaje en raíl con palanca (`opt-holografica-de-montaje-en-rail-con-palanca`) | longitud; altura | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| LPVO 1-4x / 1-6x (tubo de 30 mm) (`opt-lpvo-1-4x-1-6x-tubo-de-30-mm`) | longitud; diámetro de objetivo; tubo de 30 mm | `anillo-optica-30mm`, `montaje-lpvo-30mm`* | — | T1 | 2 | CAT |
| LPVO 1-8x / 1-10x (`opt-lpvo-1-8x-1-10x`) | longitud; objetivo; tubo | `anillo-optica-30mm`, `montaje-lpvo-30mm`* | — | T1 | 2 | CAT |
| Mira telescópica 3-9x (tubo de 25,4 mm) (`opt-mira-telescopica-3-9x-tubo-de-25-4-mm`) | longitud; objetivo; tubo de 25,4 mm | `anillo-optica-25-4mm` | — | T1 | 2 | CAT |
| Magnificador 4x o 5x (`opt-magnificador-4x-o-5x`) | longitud; altura | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Montura de pivote para magnificador (flip to side) (`opt-montura-de-pivote-para-magnificador-flip-to-side`) | ángulo; altura | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Montura desplazada (offset 45 grados) de red dot (`opt-montura-desplazada-offset-45-grados-de-red-dot`) | ángulo; altura | `picatinny-mil-std-1913` | `huella-rmr` | T1 | 2 | CAT |
| Montura cantilever para LPVO (`opt-montura-cantilever-para-lpvo`) | longitud; altura | `picatinny-mil-std-1913` | `anillo-optica-30mm` | T1 | 2 | CAT |
| Mira telescópica 3-9x (tubo de 30 mm) (`opt-mira-telescopica-3-9x-tubo-de-30-mm`) | longitud; objetivo | `anillo-optica-30mm` | — | T1 | 3 | CAT |
| Visor térmico de simulación (clip-on) (`opt-visor-termico-de-simulacion-clip-on`) | longitud; ancho; altura | `picatinny-mil-std-1913` | — | T1 | 3 | CAT |

## B12. Accesorios

| Elemento | Parámetros | Usa | Ofrece | Nivel | Oleada | Fuente |
|---|---|---|---|---|---:|---|
| Empuñadura vertical (foregrip) de poste (`acc-empunadura-vertical-foregrip-de-poste`) | longitud; diámetro; textura | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Empuñadura angular (angled foregrip) (`acc-empunadura-angular-angled-foregrip`) | ángulo; longitud; perfil | `picatinny-mil-std-1913`, `mlok` | — | T1 | 1 | CAT |
| Linterna de mano (cuerpo cilíndrico) (`acc-linterna-de-mano-cuerpo-cilindrico`) | longitud; diámetro; montura | `anclaje-linterna-picatinny`, `anclaje-linterna-scout` | — | T1 | 1 | CAT |
| Linterna con cola de interruptor / cable (`acc-linterna-con-cola-de-interruptor-cable`) | longitud; diámetro; interruptor | `anclaje-linterna-picatinny` | — | T1 | 1 | CAT |
| Módulo láser (rojo/verde) simulado o real de airsoft (`acc-modulo-laser-rojo-verde-simulado-o-real-de-airsoft`) | longitud; ancho | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Módulo combinado láser y linterna (`acc-modulo-combinado-laser-y-linterna`) | longitud; ancho; altura | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Punto de anclaje de correa (QD socket en culata o receptor) (`acc-punto-de-anclaje-de-correa-qd-socket-en-culata-o-receptor`) | ojal; perfil | `anclaje-correa-qd-socket` | `anclaje-correa-qd-socket` | T1 | 1 | CAT |
| Anclaje de correa en raíl (QD Picatinny) (`acc-anclaje-de-correa-en-rail-qd-picatinny`) | ojal; ancho | `anclaje-correa-qd-picatinny`, `picatinny-mil-std-1913` | `anclaje-correa-qd-picatinny` | T1 | 1 | CAT |
| Correa de dos puntos (`acc-correa-de-dos-puntos`) | longitud; ancho | `anclaje-correa-qd-socket`, `anclaje-correa-qd-picatinny` | — | T1 | 1 | CAT |
| Segmento de raíl Picatinny corto (`acc-segmento-de-rail-picatinny-corto`) | longitud; ranuras | `picatinny-mil-std-1913`, `mlok` | `picatinny-mil-std-1913` | T1 | 1 | CAT |
| Protector de raíl (rail cover) (`acc-protector-de-rail-rail-cover`) | longitud; perfil | `picatinny-mil-std-1913` | — | T1 | 1 | CAT |
| Empuñadura vertical con bípode (`acc-empunadura-vertical-con-bipode`) | longitud; patas; diámetro | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Apoyo de mano (hand stop) (`acc-apoyo-de-mano-hand-stop`) | longitud; ancho | `picatinny-mil-std-1913`, `mlok` | — | T1 | 2 | CAT |
| Interruptor remoto (pressure switch) (`acc-interruptor-remoto-pressure-switch`) | longitud; cable | `picatinny-mil-std-1913`, `mlok` | — | T1 | 2 | CAT |
| Bípode de patas abatibles (`acc-bipode-de-patas-abatibles`) | longitud; patas; montura | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Bípode de montaje en raíl rápido (`acc-bipode-de-montaje-en-rail-rapido`) | longitud; patas | `picatinny-mil-std-1913` | — | T1 | 2 | CAT |
| Correa de un punto (`acc-correa-de-un-punto`) | longitud; ancho | `anclaje-correa-qd-socket` | — | T1 | 2 | CAT |
| Soporte offset 45 grados (`acc-soporte-offset-45-grados`) | ángulo; altura | `picatinny-mil-std-1913` | `picatinny-mil-std-1913` | T1 | 2 | CAT |
| Batería (volumen de referencia: stick, mini, cuadrada) (`acc-bateria-volumen-de-referencia-stick-mini-cuadrada`) | tipo; capacidad; conector; volumen | `conector-bateria-mini-tamiya`, `conector-bateria-tamiya`, `conector-bateria-deans` | — | T0 | 2 | FAB |
| Contrapeso / peso de culata (`acc-contrapeso-peso-de-culata`) | longitud; peso | `tubo-culata-mil-spec` | — | T1 | 3 | CAT |

## Cobertura de la oleada 1 por generadores paramétricos

Registro: `catalogo/m4-oleada1-piezas.json` (generado con `python -m taller6mm_pipeline.familias.oleada1`; código en `apps/pipeline/src/taller6mm_pipeline/familias/`: `empunaduras.py`, `guardamanos_variantes.py`, `miras.py`, `accesorios_ar.py`). Cubre **19 de los 85 elementos de la oleada 1** (pistoletes A2 y MOE, guardamanos de carabina, mid, RIS, quad y M-LOK, asa A2, BUIS trasera y delantera, empuñaduras vertical y angular) y 2 de la oleada 2 de adelanto (pistolete ergonómico tipo A y palanca de armado).

Estado honesto: todas son piezas **candidatas de demostración** (`es_demo`): las medidas son parámetros de barrido de confianza baja, sin ficha de SKU; sin vistas licenciadas son T0 y `publicable_3d = false` (tope T1). Los elementos siguen en `pendiente` en el mapa: tener geometría no verifica sus cotas. Las siluetas (ranuras de dedos, juntas, aros) son simplificaciones declaradas en las notas de cada pieza.

| Elemento | Oleada | Pieza | Familia |
|---|---:|---|---|
| Pistolete A2 estándar de réplica AEG (`pist-pistolete-a2-estandar-de-replica-aeg`) | 1 | `pist-a2` | `empunadura.pistolete` |
| Pistolete MOE de polímero (`pist-pistolete-moe-de-polimero`) | 1 | `pist-moe` | `empunadura.pistolete` |
| Pistolete ergonómico tipo A (ergo, ranuras laterales) (`pist-pistolete-ergonomico-tipo-a-ergo-ranuras-laterales`) | 2 | `pist-ergo` | `empunadura.pistolete` |
| Guardamanos A2 de dos mitades (con escudo térmico) (`gm-guardamanos-a2-de-dos-mitades-con-escudo-termico`) | 1 | `gm-a2-mid` | `guardamanos.variantes` |
| Guardamanos M4 CAR de dos mitades (corto con escudo) (`gm-guardamanos-m4-car-de-dos-mitades-corto-con-escudo`) | 1 | `gm-carabina` | `guardamanos.variantes` |
| Guardamanos M4 RIS (Rail Interface System) (`gm-guardamanos-m4-ris-rail-interface-system`) | 1 | `gm-ris-m4` | `guardamanos.variantes` |
| Guardamanos de Mk18 (RAS corto) (`gm-guardamanos-de-mk18-ras-corto`) | 1 | `gm-ris-mk18` | `guardamanos.variantes` |
| Guardamanos quad rail de 7 pulgadas (`gm-guardamanos-quad-rail-de-7-pulgadas`) | 1 | `gm-quad-7` | `guardamanos.variantes` |
| Guardamanos quad rail de 9 pulgadas (`gm-guardamanos-quad-rail-de-9-pulgadas`) | 1 | `gm-quad-9` | `guardamanos.variantes` |
| Guardamanos quad rail de 10 pulgadas (`gm-guardamanos-quad-rail-de-10-pulgadas`) | 1 | `gm-quad-10` | `guardamanos.variantes` |
| Guardamanos M-LOK de 7 pulgadas (`gm-guardamanos-m-lok-de-7-pulgadas`) | 1 | `gm-mlok-7` | `guardamanos.variantes` |
| Guardamanos M-LOK de 9 pulgadas (`gm-guardamanos-m-lok-de-9-pulgadas`) | 1 | `gm-mlok-9` | `guardamanos.variantes` |
| Guardamanos M-LOK de 10 pulgadas (`gm-guardamanos-m-lok-de-10-pulgadas`) | 1 | `gm-mlok-10` | `guardamanos.variantes` |
| Guardamanos M-LOK de 12 pulgadas (`gm-guardamanos-m-lok-de-12-pulgadas`) | 1 | `gm-mlok-12` | `guardamanos.variantes` |
| Guardamanos M-LOK de 13,5 pulgadas (`gm-guardamanos-m-lok-de-13-5-pulgadas`) | 1 | `gm-mlok-13-5` | `guardamanos.variantes` |
| (extra, sin elemento propio) | - | `gm-mlok-15` | `guardamanos.variantes` |
| Asa de transporte A2 con mira trasera integrada (`mira-asa-de-transporte-a2-con-mira-trasera-integrada`) | 1 | `mira-asa-a2` | `mira.asa_a2` |
| BUIS trasera abatible (back-up iron sight) (`mira-buis-trasera-abatible-back-up-iron-sight`) | 1 | `mira-buis-trasera` | `mira.buis` |
| BUIS delantera abatible (`mira-buis-delantera-abatible`) | 1 | `mira-buis-delantera` | `mira.buis` |
| (extra, sin elemento propio) | - | `mira-buis-trasera-abatida` | `mira.buis` |
| Empuñadura vertical (foregrip) de poste (`acc-empunadura-vertical-foregrip-de-poste`) | 1 | `acc-vertical-poste` | `accesorio.empunadura_vertical` |
| Empuñadura angular (angled foregrip) (`acc-empunadura-angular-angled-foregrip`) | 1 | `acc-vertical-angular` | `accesorio.empunadura_vertical` |
| Asa de armado (charging handle) y palanca (`sup-asa-de-armado-charging-handle-y-palanca`) | 2 | `sup-palanca-armado` | `sup.palanca_armado` |

## Cobertura de la oleada 1: cuerpos, cañón, tubo y monturas (generadores paramétricos)

Registro: `catalogo/m4-oleada1-cuerpos.json` (`python -m taller6mm_pipeline.familias.oleada1_cuerpos --registro catalogo/m4-oleada1-cuerpos.json`; código en `apps/pipeline/src/taller6mm_pipeline/familias/`: `canon.py`, `receptores.py`, `amortiguador.py`, `monturas.py`, `detalle.py`). Cubre **12 elementos de la oleada 1** y 7 de la oleada 2 de adelanto: cañón exterior (carabina, CQB, mid, A2 pesado y largo; perfil ligero o pesado), bloque de gas (bajo perfil, A2 con mira y raíl), receptor superior (A3 plano y A2 con asa; ventana de eyección con tapa cerrada o abierta, refuerzo de forja, empuñadura de armado y forward assist), receptor inferior (pozo de cargador, guardamonte, selector con ranura y leyenda neutra, botón de cargador, torre del tubo), tubo de amortiguador (carabina con quilla y rifle), bloqueo (tuerca de castillo y placa) y monturas de óptica (elevador de red dot y anillos de 25,4, 30 y 34 mm).

Estado honesto: solo **formas exteriores**, sin internos (gearbox, cerrojo, muelles). Todo es **candidato de demostración** (`es_demo`): las medidas son parámetros de barrido y las proporciones de detalle son estimadas, ambas de confianza baja, sin ficha de SKU; sin vistas licenciadas son T0 y `publicable_3d = false` (tope T1). Los datos desconocidos van como `null` con bandera (p. ej. separación de tornillos de la huella, paso de la quilla). El texto grabado usa una fuente de puntos propia y solo letras neutras (sin marcas ni logos). Las interfaces `*` (p. ej. `montaje-bloque-gas-ar`) siguen siendo propuestas. Los elementos siguen en `pendiente`: tener geometría no verifica sus cotas.

| Elemento | Oleada | Pieza | Familia |
|---|---:|---|---|
| Cañón exterior de M4A1 (perfil estándar con punto de mira) (`canon-canon-exterior-de-m4a1-perfil-estandar-con-punto-de-mira`) | 1 | `canon-carabina-ligero` | `canon.exterior` |
| Cañón exterior CQB (corto) (`canon-canon-exterior-cqb-corto`) | 1 | `canon-cqb-corto` | `canon.exterior` |
| (extra, sin elemento propio) | - | `canon-mid-ligero` | `canon.exterior` |
| Cañón exterior M16 con perfil A2 (pesado) (`canon-canon-exterior-m16-con-perfil-a2-pesado`) | 2 | `canon-a2-pesado` | `canon.exterior` |
| Cañón exterior largo (DMR / SPR) (`canon-canon-exterior-largo-dmr-spr`) | 2 | `canon-largo-pesado` | `canon.exterior` |
| Bloque de gas bajo perfil (bajo guardamanos) (`canon-bloque-de-gas-bajo-perfil-bajo-guardamanos`) | 1 | `bloque-gas-bajo-perfil` | `canon.bloque_gas` |
| Bloque de gas tipo A2 (con alojamiento de bayoneta) (`canon-bloque-de-gas-tipo-a2-con-alojamiento-de-bayoneta`) | 2 | `bloque-gas-a2-mira` | `canon.bloque_gas` |
| Bloque de gas con raíl (estilo Picatinny) (`canon-bloque-de-gas-con-rail-estilo-picatinny`) | 2 | `bloque-gas-rail` | `canon.bloque_gas` |
| Receptor superior flat-top (raíl superior Picatinny) (`sup-receptor-superior-flat-top-rail-superior-picatinny`) | 1 | `receptor-superior-a3` | `receptor.superior` |
| Receptor superior flat-top con ventana de eyección ampliada (Gen 2 o forjado) (`sup-receptor-superior-flat-top-con-ventana-de-eyeccion-ampliada-gen-2-o-forjado`) | 2 | `receptor-superior-a3-forjado` | `receptor.superior` |
| Receptor superior A2 con asa de transporte (carry handle) integrada (`sup-receptor-superior-a2-con-asa-de-transporte-carry-handle-integrada`) | 1 | `receptor-superior-a2-asa` | `receptor.superior` |
| Receptor superior de cañón corto (CQB) (`sup-receptor-superior-de-canon-corto-cqb`) | 1 | `receptor-superior-cqb` | `receptor.superior` |
| Receptor inferior AEG estándar (M4/M16, gearbox Ver. 2) (`inf-receptor-inferior-aeg-estandar-m4-m16-gearbox-ver-2`) | 1 | `receptor-inferior-estandar` | `receptor.inferior` |
| Receptor inferior AEG con pistolete adaptable (`inf-receptor-inferior-aeg-con-pistolete-adaptable`) | 1 | `receptor-inferior-ambidiestro` | `receptor.inferior` |
| Tubo de culata mil-spec (AR-15) (`tubo-tubo-de-culata-mil-spec-ar-15`) | 1 | `tubo-amortiguador-carabina` | `amortiguador.tubo` |
| Tubo de culata comercial (AR-15) (`tubo-tubo-de-culata-comercial-ar-15`) | 1 | `tubo-amortiguador-rifle` | `amortiguador.tubo` |
| Anillo y tuerca del tubo de culata (castle nut y placa de retención) (`tubo-anillo-y-tuerca-del-tubo-de-culata-castle-nut-y-placa-de-retencion`) | 3 | `bloqueo-tubo` | `amortiguador.bloqueo` |
| Montura de elevación (riser / QD) de red dot (`opt-montura-de-elevacion-riser-qd-de-red-dot`) | 1 | `montura-riser-t1` | `montura.riser` |
| (extra, sin elemento propio) | - | `montura-riser-rmr` | `montura.riser` |
| Red dot estilo Aimpoint CompM4 / T1 (con anillos) (`opt-red-dot-estilo-aimpoint-compm4-t1-con-anillos`) | 1 | `montura-anillos-30` | `montura.anillos` |
| Montura cantilever para LPVO (`opt-montura-cantilever-para-lpvo`) | 2 | `montura-anillos-34` | `montura.anillos` |

## Cobertura de la tanda 3: ópticas, accesorios, guardamanos, pistolete GBBR y cargadores (generadores paramétricos)

Registro: `catalogo/m4-tanda3.json` (`uv run python -m taller6mm_pipeline.familias.tanda3 --registro ../../catalogo/m4-tanda3.json`, desde `apps/pipeline`; código en `apps/pipeline/src/taller6mm_pipeline/familias/`: `tanda3_opticas.py`, `tanda3_opticas_largas.py`, `tanda3_accesorios.py`, `tanda3_cuerpos.py`, `tanda3_comun.py` y el registro `tanda3.py`). Cubre **18 elementos de la oleada 1**, 4 de la oleada 2 y 1 de la oleada 3, más 6 piezas extra sin elemento propio en el mapa (visor nocturno, tres tapas de lente, bípode plegado y torre de mira delantera). Los elementos de la lista pueden figurar también en otros registros (por ejemplo el red dot de 30 mm, cuya montura con anillos es `montura-anillos-30`, o el cargador de 30 bolas del kit esencial, que viene de un modelo CC-BY): aquí son alternativas generadas por código.

Piezas: red dot tubular (micro y de 30 mm), holográfica abierta (grande y compacta), mira telescópica con torretas (1-4x de tubo de 30 mm y 3-9x de 25,4 y 30 mm), magnificador con pivote, visor nocturno monocular (solo carcasa), tapas abatibles de lente (objetivo cerrada y abatida, ocular), linterna (con y sin puerto de cable), láser y módulo combinado, bípodes (patas desplegadas, plegadas y base de montaje rápido), mira delantera tipo A2 (torre con collarín y poste suelto), guardamanos estilo HK416, free-float octogonal y estilo MWS, pistolete de GBBR y cargadores (30, 120 y 300 bolas de AEG y 30 bolas de GBBR).

Estado honesto: solo **formas exteriores**, sin internos. Todo es **candidato de demostración** (`es_demo`): las medidas son parámetros de barrido y las proporciones de detalle son estimadas, ambas de confianza baja, sin ficha de SKU; sin vistas licenciadas son T0 y `publicable_3d = false` (tope T1). Sin marcas ni leyendas grabadas. Los tubos de las ópticas, las linternas y los guardamanos son huecos, con las lentes de cristal planas rehundidas: no hay óptica, emisor ni cañón interior. La prueba `apps/pipeline/tests/test_familias_tanda3.py` aplica a cada pieza la prueba anti-cubitos de `test_formas_reales.py` (relleno de la caja, triángulos y orientaciones de cara), exige malla cerrada y comprueba que los sockets usan interfaces conocidas.

Cotas: las de los parámetros llevan como fuente «parámetro de barrido» y las de detalle, «estimado a ojo»; todas con confianza baja. Las del raíl Picatinny vienen de `estandares.py` (ancho de confianza baja). Lo que depende de un SKU y no se conoce (por ejemplo una longitud sin dato) se registra como `null` con bandera y la pieza sale T0 sin malla.

**Cargadores.** Se reutiliza la familia `CargadorM4` (`cargador_m4.py`, sin editarla) como clase base: la nueva `cargador.m4_forma` hereda los parámetros y la interfaz `pozo-stanag-m4` y sí genera malla, pero es una silueta curva estimada (el plano del STANAG 4179 no es público): nunca pasa de T1 ni se publica, y la familia original sigue siendo T0 sin malla. La capacidad en bolas no se convierte en medidas. El **cargador de una sola bola no se ha generado**: no hay un elemento en el mapa que lo defina y `CargadorM4` exige al menos 20 bolas.

**Pistolete GBBR.** Variante de `EmpunaduraPistolete` con rebajes dorsales y mejilla del pulgar; la diferencia real de interfaz con el de AEG no tiene fuente y no se modela.

| Elemento | Oleada | Pieza | Familia |
|---|---:|---|---|
| Red dot compacta estilo Aimpoint Micro (tubular, con montura) (`opt-red-dot-compacta-estilo-aimpoint-micro-tubular-con-montura`) | 1 | `opt-red-dot-micro` | `optica.red_dot_tubular` |
| Red dot estilo Aimpoint CompM4 / T1 (con anillos) (`opt-red-dot-estilo-aimpoint-compm4-t1-con-anillos`) | 1 | `opt-red-dot-30` | `optica.red_dot_tubular` |
| Holográfica estilo EOTech 552 / 553 (`opt-holografica-estilo-eotech-552-553`) | 1 | `opt-holo-grande` | `optica.holografica_abierta` |
| Holográfica estilo EOTech EXPS / XPS (`opt-holografica-estilo-eotech-exps-xps`) | 1 | `opt-holo-compacta` | `optica.holografica_abierta` |
| LPVO 1-4x / 1-6x (tubo de 30 mm) (`opt-lpvo-1-4x-1-6x-tubo-de-30-mm`) | 2 | `opt-lpvo-1-4x` | `optica.telescopica` |
| Mira telescópica 3-9x (tubo de 25,4 mm) (`opt-mira-telescopica-3-9x-tubo-de-25-4-mm`) | 2 | `opt-telescopica-3-9x` | `optica.telescopica` |
| Mira telescópica 3-9x (tubo de 30 mm) (`opt-mira-telescopica-3-9x-tubo-de-30-mm`) | 3 | `opt-telescopica-3-9x-30` | `optica.telescopica` |
| Magnificador 3x (en raíl, abatible) (`opt-magnificador-3x-en-rail-abatible`) | 1 | `opt-magnificador` | `optica.magnificador` |
| (extra, sin elemento propio) | - | `opt-visor-nocturno` | `optica.visor_nocturno` |
| (extra, sin elemento propio) | - | `tapa-objetivo-cerrada` | `optica.tapa_lente_abatible` |
| (extra, sin elemento propio) | - | `tapa-objetivo-abierta` | `optica.tapa_lente_abatible` |
| (extra, sin elemento propio) | - | `tapa-ocular-cerrada` | `optica.tapa_lente_abatible` |
| Linterna de mano (cuerpo cilíndrico) (`acc-linterna-de-mano-cuerpo-cilindrico`) | 1 | `acc-linterna-tactica` | `accesorio.luz_laser_tactico` |
| Linterna con cola de interruptor / cable (`acc-linterna-con-cola-de-interruptor-cable`) | 1 | `acc-linterna-cable` | `accesorio.luz_laser_tactico` |
| Módulo láser (rojo/verde) simulado o real de airsoft (`acc-modulo-laser-rojo-verde-simulado-o-real-de-airsoft`) | 1 | `acc-laser` | `accesorio.luz_laser_tactico` |
| Módulo combinado láser y linterna (`acc-modulo-combinado-laser-y-linterna`) | 1 | `acc-luz-laser` | `accesorio.luz_laser_tactico` |
| Bípode de patas abatibles (`acc-bipode-de-patas-abatibles`) | 2 | `acc-bipode-desplegado` | `accesorio.bipode` |
| (extra, sin elemento propio) | - | `acc-bipode-plegado` | `accesorio.bipode` |
| Bípode de montaje en raíl rápido (`acc-bipode-de-montaje-en-rail-rapido`) | 2 | `acc-bipode-rapido` | `accesorio.bipode` |
| (extra, sin elemento propio) | - | `mira-delantera-torre-a2` | `mira.delantera_a2` |
| Punto de mira de bloque de gas (tipo poste A2) (`canon-punto-de-mira-de-bloque-de-gas-tipo-poste-a2`) | 1 | `mira-delantera-poste-a2` | `mira.delantera_a2` |
| Guardamanos HK416 de raíl largo (`gm-guardamanos-hk416-de-rail-largo`) | 1 | `gm-hk416` | `guardamanos.tanda3` |
| Guardamanos free-float octogonal (estilo Daniel Defense/Noveske) (`gm-guardamanos-free-float-octogonal-estilo-daniel-defense-noveske`) | 1 | `gm-octogonal` | `guardamanos.tanda3` |
| Guardamanos de MWS (Tokyo Marui o compatible) (`gm-guardamanos-de-mws-tokyo-marui-o-compatible`) | 1 | `gm-mws` | `guardamanos.tanda3` |
| Pistolete de GBBR (MWS / compatible) (`pist-pistolete-de-gbbr-mws-compatible`) | 1 | `pist-gbbr` | `empunadura.pistolete_gbbr` |
| Cargador STANAG lowcap (30 a 80 bolas) (`carg-cargador-stanag-lowcap-30-a-80-bolas`) | 1 | `carg-30` | `cargador.m4_forma` |
| Cargador STANAG midcap (120 a 150 bolas) (`carg-cargador-stanag-midcap-120-a-150-bolas`) | 1 | `carg-120` | `cargador.m4_forma` |
| Cargador STANAG highcap (300 a 500 bolas) (`carg-cargador-stanag-highcap-300-a-500-bolas`) | 1 | `carg-300` | `cargador.m4_forma` |
| Cargador de GBBR Tokyo Marui MWS (gas) (`carg-cargador-de-gbbr-tokyo-marui-mws-gas`) | 1 | `carg-gbb-30` | `cargador.m4_forma` |

Interfaces nuevas propuestas por esta tanda (solo en el registro `catalogo/m4-tanda3.json`, sin tocar `interfaces.json` ni `ar-m4.json`):

| Id | Descripción |
|---|---|
| `montaje-tapa-lente` | Collarín de una tapa abatible sobre el casquillo del objetivo o del ocular (según su diámetro) |
| `optica.eje` | Eje óptico de una óptica de tubo (punto y dirección de visión, para alinear tapas y más) |

## Cobertura de la tanda 3: culatas y bocachas (generadores paramétricos)

Registro: `catalogo/m4-tanda3-culatas.json` (`python -m taller6mm_pipeline.familias.tanda3_culatas --registro catalogo/m4-tanda3-culatas.json`; código en `apps/pipeline/src/taller6mm_pipeline/familias/`: `culatas_m4.py`, `bocas_m4.py`, `formas_tanda3.py`, `tanda3_culatas.py`). Cubre **17 piezas** con formas reales (lofts por secciones, revolución, ventanas y ranuras con el fondo redondo; nada de cajas). Las culatas de estilo polímero y el brace son **formas genéricas**, sin marcas ni copia de un producto; el brace no va ligado a ningún arma real.

Estado honesto: todas son candidatas de demostración (`es_demo`): medidas de barrido de confianza baja, sin ficha de SKU; sin vistas licenciadas son T0 y `publicable_3d = false`. La hélice de la rosca no se modela (la «rosca falsa» son anillos en V con el paso de 1 mm). Rosca de boca siempre de 14 mm (CW o CCW). Los GLB viven en `apps/pipeline/salida/` (ignorada por git).

| Elemento | Pieza | Familia |
|---|---|---|
| Culata de 6 posiciones (tipo carabina, genérica) (`culata-culata-de-6-posiciones-tipo-carabina-generica`) | `culata-6pos-cerrada` | `culata.telescopica_6pos` |
| Culata CAR (M4 de 6 posiciones, tipo M4 original) (`culata-culata-car-m4-de-6-posiciones-tipo-m4-original`) | `culata-6pos-extendida` | `culata.telescopica_6pos` |
| Culata estilo Magpul STR (`culata-culata-estilo-magpul-str`) | `culata-polimero-str` | `culata.telescopica_polimero` |
| Culata estilo Magpul CTR (`culata-culata-estilo-magpul-ctr`) | `culata-polimero-ctr` | `culata.telescopica_polimero` |
| Culata estilo Magpul MOE (`culata-culata-estilo-magpul-moe`) | `culata-polimero-moe` | `culata.telescopica_polimero` |
| Culata fija A2 (carabina larga, con compartimento) (`culata-culata-fija-a2-carabina-larga-con-compartimento`) | `culata-fija-a2` | `culata.fija_a2` |
| Culata plegable lateral con adaptador AR (`culata-culata-plegable-lateral-con-adaptador-ar`) | `culata-plegable-desplegada` | `culata.plegable_lateral` |
| (extra, sin elemento propio) | `culata-plegable-plegada` | `culata.plegable_lateral` |
| Culata mínima de PDW / SBR (tipo cuchara o tirante) (`culata-culata-minima-de-pdw-sbr-tipo-cuchara-o-tirante`) | `culata-skeleton` | `culata.skeleton` |
| Culata con tirante estabilizador (pistol brace) (`culata-culata-con-tirante-estabilizador-pistol-brace`) | `culata-brace-pistola` | `culata.brace_pistola` |
| Apagallamas de jaula (birdcage) (`boca-apagallamas-de-jaula-birdcage`) | `boca-jaula-a1` | `boca.jaula_a1` |
| Compensador de boca (sin supresión) (`boca-compensador-de-boca-sin-supresion`) | `boca-compensador-2` | `boca.compensador_camaras` |
| (extra, sin elemento propio) | `boca-compensador-3` | `boca.compensador_camaras` |
| Freno de boca (muzzle brake) estándar (`boca-freno-de-boca-muzzle-brake-estandar`) | `boca-cuna-freno` | `boca.cuna_freno` |
| Bocacha con adaptador de silenciador (QD) (`boca-bocacha-con-adaptador-de-silenciador-qd`) | `boca-adaptador-silenciador` | `boca.adaptador_silenciador` |
| (extra, sin elemento propio) | `boca-rosca-falsa` | `boca.rosca_falsa` |
| (extra, sin elemento propio) | `boca-tapon-rosca` | `boca.tapon_rosca` |

## Interfaces nuevas propuestas (`*`)

No existen aún en `catalogo/interfaces.json` (no se ha tocado). Se proponen para añadirlas en un PR aparte, con cotas pendientes.

| Id | Descripción |
|---|---|
| `montaje-asa-a2` | Asa de transporte A2 integrada en el receptor superior (cuerpo del asa y alojamiento de la mira trasera) |
| `union-superior-inferior-ar` | Unión superior/inferior de la réplica AR (pasadores o tornillos de unión y su posición; cambia entre AEG y GBBR) |
| `tuerca-guardamanos-ar` | Fijación del guardamanos al receptor superior (tuerca de cañón, delta ring o tornillos) |
| `montaje-pistolete-ar` | Fijación del pistolete al receptor inferior (tornillo y forma del cuello; distinta en AEG y GBBR) |
| `montaje-bloque-gas-ar` | Alojamiento del bloque de gas y punto de mira sobre el cañón exterior (A2 con alojamiento de bayoneta, bajo perfil, con raíl) |
| `montaje-mira-trasera-a2` | Alojamiento de la mira trasera del asa A2 (ruedas de elevación y deriva) |
| `montaje-bocacha-qd` | Montaje rápido de silenciador o apagallamas sobre bocacha o adaptador (QD; compatibilidad cruzada limitada) |
| `montaje-culata-plegable-ar` | Bisagra o adaptador de culata plegable al tubo de culata o al receptor inferior |
| `montaje-culata-bateria-ar` | Hueco de batería en culata, tubo o guardamanos (solo como referencia de compatibilidad, sin cotas de fabricación) |
| `pozo-gbbr-m4-mws` | Pozo de cargador de GBBR tipo Tokyo Marui MWS y compatibles (cargador de gas; no intercambiable con cargadores de AEG) |
| `pozo-gbbr-m4-wa-ghk` | Pozo de cargador de GBBR estilo WA/WE-GHK (compatibilidad cruzada por confirmar) |
| `huella-aimpoint-micro` | Huella de montura de red dot estilo Aimpoint Micro (marca solo como texto descriptivo) |
| `huella-eotech-xps` | Huella de montura de holográfica estilo EOTech XPS/EXPS (marca solo como texto descriptivo) |
| `montaje-lpvo-30mm` | Montaje LPVO de tubo de 30 mm (anillos o cantilever; ver anillo-optica-30mm) |
| `montaje-flip-up-picatinny` | Mira abatible sobre raíl Picatinny (altura de la línea de mira sobre el raíl) |
| `montaje-asa-carga-ar` | Alojamiento del asa de armado (charging handle) y su palanca en el receptor superior |
| `ranura-cubierta-eyeccion` | Bisagra y alojamiento de la cubierta de la ventana de eyección |

## Qué falta para cerrar el mapa

- Verificar cada elemento con su fuente (ficha de fabricante de grupo A, estándar o medición con calibre) antes de modelarlo.
- Confirmar la compatibilidad cruzada de cargadores de GBBR (MWS frente a WA/WE-GHK) y de los montajes QD de silenciador.
- Ampliar con la oleada de marcas concretas cuando el emparejador de mercado (docs/04) devuelva los modelos reales más vendidos.
