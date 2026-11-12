# Catálogo maestro · Familias de piezas

> Generado a partir de `catalogo/familias.json`. Fecha de corte: 2026-11-11.

Cada familia agrupa piezas con los mismos parámetros y la misma interfaz de montaje. **Nivel esperado** es el nivel de fidelidad (docs/05) que se persigue al inicio según la prioridad de la pieza; no es el nivel real, que cada asset gana al validarse. Parámetros, marcas y niveles son del conocimiento general del sector y están **sin verificar por fuente** (estado `pendiente`). Marcas «(licencia)» son referencias del grupo B: solo texto, nunca sus fotos ni logos.

**Total: 83 familias.** `aplica_a` usa los ids de familia de plataforma de `docs/catalogo/plataformas.md` (`*` = todas).

## Cuerpos superiores e inferiores

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Cuerpo superior (upper receiver) AR (`cuerpo-superior-ar`) | longitud; forma de la ventana de eyección y del deflector; tipo de raíl superior; compatibilidad con hop-up y cañón interior; variante forjado/Gen2/Gen3 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | G&G, Cyma, Specna Arms, APS, VFC, Tokyo Marui, Krytac | ar15, ar10-dmr | T2 |
| Cuerpo inferior (lower receiver) AR (`cuerpo-inferior-ar`) | pozo de cargador; marcaje de selector; compatibilidad de pistolete y tubo de culata; cableado (frente/trasero); variante de gearbox | Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Tubo de culata M4 de AEG (cableado dentro); Gearbox Ver. 2; Gearbox Ver. 7 | G&G, Cyma, Specna Arms, APS, VFC, Tokyo Marui | ar15, ar10-dmr | T2 |
| Cuerpo / receptor AK (estampado o fresado) (`cuerpo-ak`) | longitud; versión (AKM/74/AK-12); raíl lateral o tapa; gearbox Ver.3 | Montaje de culata AK (fija, madera/polímero); Montaje de culata AK plegable lateral; Gearbox Ver. 3 | LCT, E&L, GHK, Cyma, Classic Army, Arcturus | ak | T2 |
| Cuerpo MP5 (rectas y A5/SD) (`cuerpo-mp5`) | longitud de cañón; tipo de guardamanos; punto de culata | Montaje de culata MP5 (A2/A3/SD) | Tokyo Marui, VFC, Cyma | mp5 | T2 |
| Cuerpo / armazón de pistola GBB (`cuerpo-pistola-gbb`) | modelo de pistola; tamaño de armazón (compact, full); cargador; ranuras de óptica; guardamanos con raíl | Rosca de boca 11 mm antihoraria; Raíl universal de pistola (tipo Glock); Corte de corredera para óptica (tipo Glock MOS) | Tokyo Marui, WE, KJW, VFC, KWA, Stark Arms, AW Custom | pistolas-gbb-co2 | T2 |

## Guardamanos

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Guardamanos quad Picatinny (tipo RIS/RAS) (`guardamanos-ar-quad`) | longitud (mm, pendiente por modelo); número de ranuras Picatinny; diámetro interior; sistema de fijación al cuerpo; compatibilidad con cañón exterior | Picatinny (MIL-STD-1913) | Cyma, G&G, Specna Arms, APS, Matrix, Madbull | ar15, ar10-dmr | T1 |
| Guardamanos free-float (monolítico o tubular) (`guardamanos-ar-freefloat`) | longitud; perfil (redondo/octogonal); sistema de raíl o ranuras; punto de fijación; tuerca de cañón | Picatinny (MIL-STD-1913); M-LOK; KeyMod | Daniel Defense, Noveske, Geissele, Krytac, VFC, Specna Arms | ar15, ar10-dmr | T1 |
| Guardamanos M-LOK (`guardamanos-mlok`) | longitud; número de ranuras M-LOK por cara; raíl superior; perfil de tubo | M-LOK; Picatinny (MIL-STD-1913) | Specna Arms, Cyma, G&G, VFC, Ares, Krytac, Tokyo Marui | ar15, ak, acr-masada, fn-scar | T1 |
| Guardamanos KeyMod (`guardamanos-keymod`) | longitud; número de orificios KeyMod; raíl superior | KeyMod; Picatinny (MIL-STD-1913) | Cyma, Matrix, Madbull, G&G | ar15, ak | T1 |
| Guardamanos Picatinny integral (tipo rail fore-end) (`guardamanos-picatinny-puro`) | longitud; cara de raíl por lado; diámetro interior | Picatinny (MIL-STD-1913) | Cyma, Matrix, King Arms, LCT | ar15, mp5, ak, g3 | T1 |
| Guardamanos tubular (redondo, tipo CAR/carbine) (`guardamanos-tubular`) | longitud; perfil; fijación | — | Cyma, G&G, Classic Army | ar15 | T1 |
| Guardamanos / guardamanos y cubre-cañón de AK (`guardamanos-ak`) | modelo; material (madera, polímero, metal); tipo de ranuras | Picatinny (MIL-STD-1913); M-LOK | LCT, E&L, Cyma, Zenitco, Magpul | ak | T1 |
| Guardamanos MP5 (A2, A3, SD, MP5K, KAC-style) (`guardamanos-mp5`) | longitud; tipo de ranuras; compatibilidad de cuerpo | Picatinny (MIL-STD-1913) | Cyma, King Arms, Tokyo Marui | mp5 | T1 |
| Guardamanos / rail de pistola (`guardamanos-pistola`) | modelo de pistola; ranura de raíl; longitud | Raíl universal de pistola (tipo Glock); Picatinny (MIL-STD-1913) | Cyma, WE, KJW, AW Custom | pistolas-gbb-co2 | T0 |

## Cañones exteriores, interiores y adaptadores

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Cañón exterior (outer barrel) (`canon-exterior`) | longitud visible (mm); diámetro exterior; tipo de rosca de boca; marcaje en el cañón; compatibilidad con guardamanos | Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 14 mm horaria (CW); Rosca de boca 1/2"-28; Rosca de boca 5/8"-24 | Cyma, G&G, Specna Arms, Madbull, Matrix, Angry Gun | ar15, ak, mp5, g3, g36 | T1 |
| Cañón de precisión (inner barrel) (`canon-interno`) | longitud; diámetro interior; material; compatibilidad con hop-up y gearbox | Gearbox Ver. 2; Gearbox Ver. 3; Munición BB de 6 mm | Prometheus, PDI, Maple Leaf, EdGi, Madbull, Lambda Defence | * | T0 |
| Adaptador de rosca (CW a CCW, 12 mm a 14 mm) (`adaptador-rosca`) | roscas de entrada y salida; longitud; marcaje | Rosca de boca 14 mm horaria (CW); Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 11 mm antihoraria; Rosca de boca 12 mm antihoraria | Matrix, Madbull, Lancer Tactical, Action Army | * | T0 |

## Bocachas, apagallamas y silenciadores

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Apagallamas / flash hider (`apagallamas`) | forma (A2, Surefire, Vortex, cónico); longitud; rosca de montaje | Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 14 mm horaria (CW); Rosca de boca 1/2"-28 | Specna Arms, Cyma, Matrix, Madbull, Surefire (licencia), Angry Gun | * | T1 |
| Freno de boca / compensador (`freno-boca`) | forma (perforaciones, cámaras); longitud; rosca | Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 14 mm horaria (CW); Rosca de boca 1/2"-28; Rosca de boca 5/8"-24 | Specna Arms, Madbull, Strike Industries (licencia), Matrix | * | T1 |
| Silenciador / supresor (tubo) (`silenciador`) | longitud; diámetro; rosca; forma (recto, cónico, tipo OSS); si lleva trazadora | Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 14 mm horaria (CW); Rosca de boca 11 mm antihoraria; Rosca de boca 12 mm antihoraria; Rosca de boca 1/2"-28; Rosca de boca 5/8"-24 | Madbull, Matrix, Specna Arms, Angry Gun, Cyma, Fox 2, SilencerCo (licencia) | * | T1 |
| Trazadora / cronómetro de boca (`trazadora`) | tubo; rosca; autonomía; tipo de bolas | Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 14 mm horaria (CW) | Acetech, Xcortech, Nuprol, Madbull | * | T0 |

## Culatas y tubos de culata

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Culata telescópica (6-pos, 7-pos) (`culata-telescopica`) | longitud mínima y máxima (mm, pendiente por modelo); tubo de culata soportado (mil-spec/comercial); anclaje de correa | Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Anclaje de correa QD (socket / «sling swivel») | Magpul, B5 Systems, Cyma, G&G, Specna Arms, Matrix, Ace | ar15, ar10-dmr | T1 |
| Culata fija (A2, madera, polímero) (`culata-fija`) | longitud; material; anclaje | Tubo de culata mil-spec (AR-15); Montaje de culata AK (fija, madera/polímero); Montaje de culata MP5 (A2/A3/SD); Montaje de culata G3 | Cyma, Magpul, LCT, E&L, Classic Army | ar15, ak, mp5, g3 | T1 |
| Culata plegable (lateral, bajo el cuerpo, tipo AK/MP5) (`culata-plegable`) | longitud plegada y desplegada; mecanismo; interfaz | Montaje de culata AK plegable lateral; Tubo de culata mil-spec (AR-15) | Cyma, LCT, A&K, Matrix, G&G | ar15, ak, mp5 | T1 |
| Culata y chasis (francotirador, DMR) (`culata-chasis`) | compatibilidad con cuerpo; ajustes de mejilla y cantonera; interfaz de chasis | Montaje de culata VSR-10 / L96; Raíl de cola de milano de 11 mm; Picatinny (MIL-STD-1913) | Action Army, Silverback, Maple Leaf, KJ Works, A&K | francotirador-muelle, clasicas-dmr, ar10-dmr | T1 |
| Tubo de culata (`tubo-culata`) | tipo (mil-spec/comercial); longitud; cableado interior; compatibilidad con cuerpo inferior | Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Tubo de culata M4 de AEG (cableado dentro) | Cyma, G&G, Specna Arms, Matrix | ar15 | T1 |
| Adaptador de culata (AR a AK, AR a MP5, AR a otras) (`adaptador-culata`) | plataforma de origen y destino; longitud | Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Montaje de culata AK (fija, madera/polímero); Montaje de culata MP5 (A2/A3/SD) | Cyma, Matrix, King Arms | ak, mp5, g3 | T0 |
| Cantonera y apoyo de mejilla (`cantonera-mejilla`) | compatibilidad de culata; longitud/altura | — | Magpul, B5 Systems, Cyma | ar15, francotirador-muelle | T0 |

## Pistoletes

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Pistolete (grip) AR (`pistolete-ar`) | compatibilidad con cuerpo inferior; ángulo; tornillería | Gearbox Ver. 2 | Magpul, Cyma, G&G, Specna Arms, Strike Industries (licencia) | ar15, ar10-dmr | T1 |
| Pistolete AK (`pistolete-ak`) | compatibilidad con receptor; material | Gearbox Ver. 3 | LCT, E&L, Cyma | ak | T1 |

## Empuñaduras, bípodes y correas

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Empuñadura vertical (`empunadura-vertical`) | altura; interfaz (Picatinny, M-LOK, KeyMod); anclaje | Picatinny (MIL-STD-1913); M-LOK; KeyMod | Magpul, Cyma, G&G, Specna Arms, Strike Industries (licencia), BCM (licencia) | * | T1 |
| Empuñadura angular (AFG) (`empunadura-angular`) | ángulo; altura; interfaz | Picatinny (MIL-STD-1913); M-LOK; KeyMod | Magpul, Cyma, Specna Arms, Strike Industries (licencia) | * | T1 |
| Empuñadura con bípode (`empunadura-bipode`) | altura; interfaz; patas (longitud) | Picatinny (MIL-STD-1913); M-LOK | Cyma, G&G, Specna Arms, Magpul | * | T1 |
| Bípode (`bipode`) | interfaz; altura plegada y desplegada; patas | Picatinny (MIL-STD-1913); M-LOK | Harris (licencia), Cyma, Magpul, Atlas | * | T1 |
| Tope de mano / hand stop (`apoyo-mano`) | interfaz; ángulo | Picatinny (MIL-STD-1913); M-LOK; KeyMod | Magpul, Strike Industries (licencia), Cyma | * | T0 |
| Anclaje de correa y adaptadores QD (`anclaje-correa`) | tipo QD; interfaz; posición | Anclaje de correa QD (socket / «sling swivel»); Anclaje de correa en Picatinny / M-LOK | Magpul, Blue Force Gear, Cyma, G&G | * | T0 |
| Correa (sling) 1, 2 y 3 puntos (`correa`) | puntos de anclaje; ancho; ajuste | Anclaje de correa QD (socket / «sling swivel») | Magpul, Blue Force Gear, Condor, Cyma | * | T0 |

## Cargadores, baterías y suministro de aire

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Cargador M4 mid-cap (120–150 bolas) (`cargador-ar-midcap`) | plataforma (M4); capacidad; sistema de alimentación (muelle, ruleta) | — | Cyma, G&G, Specna Arms, Magpul PTS (licencia), Tokyo Marui, ICS | ar15 | T1 |
| Cargador M4 hi-cap (300+ bolas) (`cargador-ar-hicap`) | plataforma; capacidad; sistema | — | Cyma, G&G, Specna Arms, Magpul PTS (licencia) | ar15 | T1 |
| Cargador M4 low-cap (realcap, 30 bolas) (`cargador-ar-lowcap`) | plataforma; capacidad (30–45 bolas) | — | Magpul PTS (licencia), Specna Arms, Cyma | ar15 | T1 |
| Cargador GBBR (gas) de M4 / MCX / HK416 (`cargador-gbbr`) | plataforma; capacidad; presión de gas; válvula | — | Tokyo Marui, WE, VFC, KWA, GHK | ar15, sig-mpx-mcx | T1 |
| Cargador AK (74/47/12) (`cargador-ak`) | plataforma; capacidad; tipo | — | LCT, E&L, Cyma, Arcturus, Magpul (licencia), Specna Arms | ak | T1 |
| Cargador MP5 (`cargador-mp5`) | plataforma; capacidad; tipo curvo/recto | — | Cyma, Tokyo Marui, Classic Army | mp5 | T1 |
| Cargador G3 / G36 (`cargador-g3-g36`) | plataforma; capacidad; tipo | — | Cyma, Classic Army, Jing Gong | g3, g36 | T1 |
| Cargador de pistola GBB / CO2 (`cargador-pistola-gbb`) | plataforma; capacidad (bolas); tipo de gas/CO2; válvula | — | Tokyo Marui, WE, KJW, VFC, KWA, AW Custom | pistolas-gbb-co2 | T1 |
| Cargador subfusil (MP7, MPX, Vector, UMP, Scorpion, P90…) (`cargador-subfusil`) | plataforma; capacidad | — | Tokyo Marui, KWA, Cyma, Specna Arms | pdw-hk, sig-mpx-mcx, subfusiles, bullpup-moderno, cz-scorpion | T1 |
| Cargador / caja de munición de ametralladora (`cargador-mg`) | plataforma; capacidad; tipo caja o cinta | — | A&K, Classic Army, Cyma, Ares | ametralladoras | T1 |
| Cargador VSR-10 / L96 / M24 (`cargador-francotirador`) | plataforma; capacidad | — | Tokyo Marui, Maple Leaf, Well, Cyma | francotirador-muelle | T0 |
| Cartuchos de escopeta (shells) (`cargador-escopeta`) | tipo (3 bolas, 6 bolas, 30 bolas); plataforma | — | APS, Cyma, Tokyo Marui, Madbull, King Arms | escopetas | T0 |
| Batería (LiPo, NiMH) (`bateria`) | formato (stick, mini, nunchuck, brick); capacidad (mAh); tensión; conector | Conector Mini Tamiya; Conector Tamiya grande; Conector Deans (T) | Gens Ace, Turnigy, Nuprol, Specna Arms, Cyma | * | T0 |
| Botella y regulador HPA (`regulador-hpa`) | tipo; presión de salida; conector | — | Wolverine, Polarstar, Gate, Mancraft | hpa | T0 |

## Miras mecánicas

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Mira mecánica delantera (FSB, plegable, tipo A2) (`mira-mecanica-delantera`) | altura; interfaz; plegable o fija; elevación | Picatinny (MIL-STD-1913) | Cyma, G&G, Magpul, Troy, KAC (licencia) | ar15, ak, mp5 | T1 |
| Mira mecánica trasera (BUIS, MBUS, aperture) (`mira-mecanica-trasera`) | altura; interfaz; plegable o fija; apertura | Picatinny (MIL-STD-1913) | Cyma, G&G, Magpul, Troy | ar15, ak, mp5 | T1 |
| Mira AK (poste y alza) (`mira-guia-ak`) | tipo de alza; guardamanos soporte | — | LCT, E&L, Cyma | ak | T0 |

## Ópticas y monturas

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Red dot (reflex) (`red-dot`) | tamaño de ventana; altura sobre el raíl; huella; peso; retícula; tipo de montura | Picatinny (MIL-STD-1913); Huella Trijicon RMR; Huella Aimpoint Micro T-1; Huella Leupold DeltaPoint Pro; Huella Holosun K / 407K | Aimpoint, Holosun, EOTech, Trijicon, Vortex, Sig Sauer, Ares, Evolution Gear, Walther, ACRO | * | T1 |
| Mira holográfica (`holografica`) | altura; tamaño de ventana; forma; peso; interfaz | Picatinny (MIL-STD-1913) | EOTech, Holosun, Vortex, Evolution Gear | * | T1 |
| LPVO (óptica 1-6x, 1-8x, 1-10x) (`lpvo`) | rango de aumento; tubo (30/34 mm); altura; longitud; interfaz; peso | Anillo de óptica de 30 mm; Anillo de óptica de 34 mm; Picatinny (MIL-STD-1913) | Vortex, Primary Arms, Swampfox, Nightforce (licencia), Trijicon (licencia), Evolution Gear | * | T1 |
| Mira telescópica de largo alcance (`mira-telescopica`) | aumento; objetivo; tubo (25,4/30/34 mm); longitud; retícula | Anillo de óptica de 25,4 mm (1 in); Anillo de óptica de 30 mm; Anillo de óptica de 34 mm; Raíl de cola de milano de 11 mm; Picatinny (MIL-STD-1913) | Vortex, Swiss Arms, Cyma, Bushnell, Hawke, UTG | francotirador-muelle, francotirador-gas-aeg, ar10-dmr | T1 |
| Magnificador (3x, 5x) (`magnificador`) | aumento; altura; interfaz; plegable lateral | Picatinny (MIL-STD-1913) | Vortex, EOTech, Holosun, Evolution Gear | * | T1 |
| Montura (riser) de óptica (`montura-optica`) | altura; diámetro de tubo; interfaz; offset | Picatinny (MIL-STD-1913); Anillo de óptica de 25,4 mm (1 in); Anillo de óptica de 30 mm; Anillo de óptica de 34 mm; Raíl de cola de milano de 11 mm | Magpul, Larue (licencia), Vortex, Cyma, G&G | * | T1 |
| Placa de adaptación de red dot de pistola (`adaptador-red-dot-pistola`) | huella origen; huella destino; modelo de pistola | Huella Trijicon RMR; Huella Aimpoint Micro T-1; Huella Leupold DeltaPoint Pro; Huella Holosun K / 407K; Corte de corredera para óptica (tipo Glock MOS) | AW Custom, Guns Modify, 5KU, Holosun | pistolas-gbb-co2 | T0 |
| Visor nocturno y térmico (de juego) (`visor-nocturno-termico`) | montaje; tipo | Picatinny (MIL-STD-1913) | Evolution Gear, Holosun, Acetech | * | T0 |

## Linternas, láseres y accesorios de raíl

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Linterna táctica (`linterna`) | diámetro y longitud; interfaz (Picatinny, M-LOK, scout); lúmenes; peso | Anclaje de linterna sobre Picatinny; Picatinny (MIL-STD-1913); M-LOK | Surefire, Streamlight, Cloud Defensive, Nitecore, Ares, Cyma | * | T1 |
| Láser rojo, verde o IR (aprobado para airsoft) (`laser`) | longitud; interfaz; clase de láser; peso | Picatinny (MIL-STD-1913); M-LOK | Crimson Trace, Holosun, Cyma, Evolution Gear | * | T0 |
| Módulo combinado láser + linterna (`modulo-laser-linterna`) | longitud; interfaz; peso | Picatinny (MIL-STD-1913); M-LOK | Surefire, Streamlight, Cyma, Ares | * | T1 |
| Interruptor remoto de presión (`interruptor-remoto`) | cable; interfaz | Picatinny (MIL-STD-1913); M-LOK | Surefire, Cyma, Ares | * | T0 |
| Protector de raíl / cubreraíl (`protector-rail`) | longitud; interfaz; material | Picatinny (MIL-STD-1913); M-LOK | Magpul, Cyma, BCM (licencia) | * | T0 |
| Segmento de raíl Picatinny / adaptador M-LOK (`segmento-rail`) | longitud; número de ranuras; interfaz | Picatinny (MIL-STD-1913); M-LOK; KeyMod | Magpul, Cyma, Madbull, Strike Industries (licencia) | * | T0 |
| Montura lateral (offset) para mira de reserva (`soporte-offset`) | ángulo; altura; interfaz | Picatinny (MIL-STD-1913) | Cyma, Evolution Gear, Magpul | * | T0 |
| Contrapeso / extensión de pistolete (`peso-contrapeso`) | peso; interfaz | Picatinny (MIL-STD-1913); M-LOK | Cyma, Specna Arms | * | T0 |

## Pistolas: correderas, cañones y accesorios

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Corredera de pistola (`corredera-pistola`) | modelo; material; marcaje; corte para óptica; cañón compatible | Rosca de boca 11 mm antihoraria; Corte de corredera para óptica (tipo Glock MOS) | AW Custom, Guns Modify, 5KU, Tokyo Marui, WE, KJW, Cowcow | pistolas-gbb-co2 | T1 |
| Cañón exterior de pistola (`canon-pistola`) | longitud; rosca (11/12/14 mm); diámetro | Rosca de boca 11 mm antihoraria; Rosca de boca 12 mm antihoraria; Rosca de boca 14 mm antihoraria (CCW) | AW Custom, Guns Modify, Cowcow, Madbull | pistolas-gbb-co2 | T1 |
| Silenciador / compensador de pistola (`silenciador-pistola`) | rosca; longitud; diámetro | Rosca de boca 11 mm antihoraria; Rosca de boca 12 mm antihoraria; Rosca de boca 14 mm antihoraria (CCW) | Madbull, Angry Gun, Cowcow, Acetech | pistolas-gbb-co2 | T1 |
| Empuñadura / panel lateral de pistola (`empunadura-pistola`) | modelo; material; ancho | — | Magpul, Hogue, Cowcow, Guns Modify | pistolas-gbb-co2 | T0 |
| Kit de conversión (carabina de pistola, chasis) (`kit-conversion-pistola`) | modelo; interfaz | Rosca de boca 11 mm antihoraria | AW Custom, CAA Tactical | pistolas-gbb-co2 | T0 |

## Kits y piezas internas

| Familia | Parámetros | Interfaz | Marcas (ejemplo) | Aplica a | Nivel |
|---|---|---|---|---|---|
| Kit externo (cuerpo + guardamanos + culata) (`kit-externo`) | plataforma; versión; contenido | — | Cyma, G&G, Specna Arms, King Arms, Madbull | * | T1 |
| Kit de mejora interna (gearbox, motor, hop-up) (`kit-upgrade-interno`) | plataforma; gearbox; compatibilidad | Gearbox Ver. 2; Gearbox Ver. 3; Gearbox Ver. 7 | SHS, Lonex, Prometheus, ZCI, Modify, Maple Leaf, Gate | * | T0 |
| Gearbox (Ver. 2, 3, 7) (`gearbox`) | versión; compatibilidad de cuerpo; engranajes; muelle | Gearbox Ver. 2; Gearbox Ver. 3; Gearbox Ver. 7 | SHS, Lonex, Modify, Prometheus, ZCI, Cyma, G&G | ar15, ak, mp5 | T0 |
| Motor eléctrico (`motor`) | tipo (short, long, high torque); velocidad; compatibilidad | Gearbox Ver. 2; Gearbox Ver. 3; Gearbox Ver. 7 | Cyma, G&G, SHS, Lonex, Prometheus, Modify | * | T0 |
| Hop-up (gomas, cámara) (`hop-up`) | plataforma; tipo de goma; dureza; compatibilidad de cañón | Gearbox Ver. 2; Gearbox Ver. 3 | Maple Leaf, Madbull, Prometheus, PDI, EdGi | * | T0 |
| MOSFET / ETU (`mosfet`) | compatibilidad de gearbox; modo; cableado | Gearbox Ver. 2; Gearbox Ver. 3; Gearbox Ver. 7 | Gate, Wolverine, Perun | * | T0 |
| Cilindro, pistón, muelle (pistón de muelle) (`cilindro-piston`) | compatibilidad; rigidez; material | Gearbox Ver. 2; Gearbox Ver. 3 | SHS, Lonex, Prometheus, Modify, Maple Leaf | * | T0 |
| Cerrojo y nozzle GBB (conversión) (`bolt-nozzle-gbb`) | plataforma; tipo | Rosca de boca 11 mm antihoraria | Guns Modify, AW Custom, 5KU, WE | pistolas-gbb-co2, ar15 | T0 |

