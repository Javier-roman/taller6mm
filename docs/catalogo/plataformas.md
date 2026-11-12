# Catálogo maestro · Plataformas

> Generado a partir de `catalogo/plataformas.json` (fuente de datos: ese JSON). Fecha de corte: 2026-11-11.

Este documento lista las plataformas de réplicas de airsoft que Taller6mm debe cubrir, agrupadas por familia. **Fabricantes y variantes son conocimiento general del sector y están sin verificar por fuente** (estado `pendiente`); ninguna cota de plataforma está confirmada todavía. Los fabricantes del grupo A de `docs/fuentes/marcas.md` son la referencia para validarlos producto a producto con `/nueva-replica`. Las marcas con licencia (grupo B) solo aparecen como texto en la nota de licencia.

**Mecanismos**: AEG (eléctrica), GBB (pistola de gas con retroceso), GBBR (réplica larga de gas con retroceso), HPA (aire comprimido), muelle (spring, cerrojo manual), CO2 (cartucho de CO2), gas (sin retroceso).

**Total: 101 plataformas en 26 familias.** Interfaces referenciadas: ver `docs/catalogo/interfaces.md` (ids en kebab-case).

## M4 / AR-15 y derivados

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Colt M4A1 / M4 CQB (`m4a1`) | AEG, GBBR, HPA | Cyma, G&G, Specna Arms, APS, E&C, ICS, Classic Army, King Arms, VFC, Tokyo Marui (MWS, NGRS), WE, KWA, GHK, Krytac, Lancer Tactical, Evolution, Ares/Amoeba | M4A1 carbina, M4 CQB-R, Mk18 Mod 0/1, M4 RIS/RAS, URX, Block II | Picatinny (MIL-STD-1913); M-LOK; KeyMod; Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Tubo de culata M4 de AEG (cableado dentro); Anclaje de correa QD (socket / «sling swivel»); Anclaje de correa en Picatinny / M-LOK; Anclaje de linterna sobre Picatinny; Gearbox Ver. 2; Gearbox Ver. 7; Munición BB de 6 mm | pozo AR-15 / M4 (tipo STANAG) |
| Colt M16 (A1 / A2 / A4 / VN) (`m16`) | AEG, GBBR | Cyma, G&G, ICS, Classic Army, A&K, VFC, Tokyo Marui, WE, King Arms, E&C | M16A1, M16A2, M16A4, XM177, M16 Vietnam | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Anclaje de correa QD (socket / «sling swivel»); Gearbox Ver. 2 | pozo AR-15 / M4 (tipo STANAG) |
| HK416 / HK416A5 / M27 IAR (`hk416`) | AEG, GBBR, HPA | VFC (licencia Umarex/H&K), Umarex, Tokyo Marui (NGRS), G&G, Specna Arms, Cyma, Classic Army | D10RS, D14.5RS, D16.5RS, A5, M27 IAR, 416 pro | Picatinny (MIL-STD-1913); M-LOK; KeyMod; Rosca de boca 14 mm antihoraria (CCW); Anclaje de correa en Picatinny / M-LOK; Anclaje de linterna sobre Picatinny; Gearbox Ver. 2; Munición BB de 6 mm | pozo AR-15 / M4 (tipo STANAG) |
| Tokyo Marui M4 MWS (Modular Weapon System) (`mws`) | GBBR | Tokyo Marui, aftermarket (Angry Gun, Guns Modify, 5KU) | M4A1 MWS, URG-I, Mk18 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Anclaje de correa en Picatinny / M-LOK; Anclaje de linterna sobre Picatinny | pozo AR-15 / M4 (tipo STANAG) |
| Tokyo Marui Next Gen Recoil Shock (AR) (`tm-ngrs-ar`) | AEG (retroceso) | Tokyo Marui | MTR16, HK416 D, SOPMOD Block 3, Mk18 MOD1 | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW) | pozo AR-15 / M4 (tipo STANAG) |
| AR comerciales con licencia (Daniel Defense, Noveske, Knight's Armament) (`colt-licencia-modernos`) | AEG, GBBR | G&G, Cyma, VFC, Specna Arms, Ares, Krytac | DD M4A1 RIS II, Noveske Gen3, KAC SR-16 | Picatinny (MIL-STD-1913); M-LOK; KeyMod; Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Anclaje de correa en Picatinny / M-LOK | pozo AR-15 / M4 (tipo STANAG) |
| AR comerciales compactos (SBR, «AR pistola») (`ar15-comerciales-sbr`) | AEG, GBBR | Specna Arms, G&G, Cyma, E&C | pistola AR, SBR 10, 3, SBR 8" | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15) | pozo AR-15 / M4 (tipo STANAG) |

## AR-10 / SR-25 / Mk12 / DMR sobre AR

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| SR-25 / Mk11 / Mk12 / AR-10 / LR-300 / AR-308 (`sr25`) | AEG, GBBR | Cyma, G&G, VFC, KWA, Ares, A&K | SR-25, Mk12 SPR, Mk11 Mod 0, AR-10, DMR AR-15 (SPR) | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 5/8"-24; Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15) | pozo AR-15 / M4 (tipo STANAG) |

## AK y derivados

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| AKM / AK-47 (`akm`) | AEG, GBBR | Cyma, LCT, E&L, GHK, Classic Army, G&G, APS, Double Eagle, King Arms, Specna Arms | AKM, AKMS (plegable), AKMSU, Type 56 | Rosca de boca 14 mm antihoraria (CCW); Montaje de culata AK (fija, madera/polímero); Montaje de culata AK plegable lateral; Gearbox Ver. 3; Munición BB de 6 mm | pozo AK (cargador curvo) |
| AK-74 / AK-74M / AKS-74 / AKS-74U (`ak74`) | AEG, GBBR | LCT, E&L, GHK, Cyma, Classic Army, Specna Arms, G&G, APS | AK-74, AK-74M, AKS-74, AKS-74U (Krinkov), AK-105 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Montaje de culata AK (fija, madera/polímero); Montaje de culata AK plegable lateral; Gearbox Ver. 3 | pozo AK (cargador curvo) |
| AK-12 / AK-15 / AK-19 / AK-308 (`ak12`) | AEG, GBBR | Arcturus, LCT, E&L, GHK (AK-12), Cyma (AK-12), Specna Arms, Ares, King Arms, ICS | AK-12 (2015, 2017, 2023), AK-15, AK-19, AK-308, AK-308 Block II | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Montaje de culata AK plegable lateral; Gearbox Ver. 3 | pozo AK (cargador curvo) |
| RPK / RPK-74 / RPKS-74 (`rpk`) | AEG | LCT, Cyma, Classic Army, A&K | RPK, RPK-74, RPKS-74 | Rosca de boca 14 mm antihoraria (CCW); Montaje de culata AK (fija, madera/polímero); Montaje de culata AK plegable lateral; Gearbox Ver. 3 | pozo AK (cargador curvo) |
| AK modernos en chasis tácticos (AK + M-LOK, RS Regulate, Zenitco) (`ak-tacticos`) | AEG, GBBR | Specna Arms, E&L, LCT, Arcturus, Cyma | AK-74 RS, AK-105 Zenitco, AK-103 modernizado | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Montaje de culata AK plegable lateral | pozo AK (cargador curvo) |
| Galil / Vz. 58 / Zastava M70 (`galil-vz58`) | AEG, GBBR | Cyma, Echo1, Sentinel, A&K, GHK, Jing Gong | Galil ARM, Galil SAR, Vz. 58, M70 | Rosca de boca 14 mm antihoraria (CCW) | pozo Vz. 58 |

## MP5 y derivados

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| H&K MP5 (A2 / A3 / A4 / A5) (`mp5`) | AEG, GBBR, GBB | Cyma, Tokyo Marui (MP5 Next Gen), VFC, Classic Army, Jing Gong, Double Eagle, King Arms, G&G, A&K, KWA, Umarex (licencia) | MP5A2 (culata fija), MP5A3 (retráctil), MP5A4/A5 | Rosca de boca 14 mm antihoraria (CCW); Montaje de culata MP5 (A2/A3/SD); Gearbox Ver. 3 | pozo MP5 |
| MP5K / MP5K-PDW / MP5K-N (`mp5k`) | AEG, GBBR | Tokyo Marui, VFC, Cyma, Classic Army, KWA | MP5K, MP5K-PDW, MP5K-N | Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 12 mm antihoraria; Picatinny (MIL-STD-1913) | pozo MP5 |
| MP5SD (silenciado) (`mp5sd`) | AEG, GBBR | Cyma, Tokyo Marui, VFC, KWA | MP5SD2, SD3, SD5, SD6 | Montaje de culata MP5 (A2/A3/SD) | pozo MP5 |
| MP5 modernos (J, Navy, SMG con railes y guardamanos largos) (`mp5-lcc`) | AEG, GBBR | VFC, Tokyo Marui, Cyma, Classic Army | MP5J, MP5 Navy, MP5 SF/PDW | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Montaje de culata MP5 (A2/A3/SD) | pozo MP5 |

## G3 / HK51 / PSG-1

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| G3 / HK33 / HK51 / PSG-1 / MC51 (`g3`) | AEG, GBBR | Cyma, Classic Army, Jing Gong, LCT, G&G, Double Bell, Arcturus | G3A3, G3A4, G3SG/1, MSG-90, PSG-1 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Montaje de culata G3 | pozo G3 / HK51 / PSG-1 |

## G36

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| H&K G36 / G36C / G36K / G36KV / MG36 (`g36`) | AEG, GBBR | Jing Gong, Classic Army, Cyma, WE, VFC, ICS, Tokyo Marui (G36C), A&K, Ares, S&T | G36, G36K, G36C, G36KV, MG36 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Montaje de culata G36 | pozo G36 |

## PDW de HK (MP7, UMP)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| H&K MP7A1 / MP7A2 (`mp7`) | AEG, GBB, GBBR | Tokyo Marui (GBB y NGRS), VFC, KWA, Umarex, Double Bell, Cyma | MP7A1, MP7A2, MP7A1 con culata larga | Picatinny (MIL-STD-1913); Rosca de boca 11 mm antihoraria | pozo MP7 |
| H&K UMP / UMP9 / UMP45 (`ump`) | AEG, GBBR | Umarex (VFC), Tokyo Marui, Double Bell, Classic Army | UMP9, UMP45, UMP40 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 12 mm antihoraria | pozo UMP |

## SIG MPX / MCX / Rattler

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| SIG MPX / MPX-K / MPX-SD (`mpx`) | AEG, GBBR | Umarex (SIG Air), VFC, Cyma, G&G, KWA, Krytac | MPX, MPX-K, MPX-SD, MPX-PCC | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Rosca de boca 12 mm antihoraria | pozo MPX |
| SIG MCX / MCX Rattler / MCX Virtus / MCX SPEAR (`mcx`) | AEG, GBBR | SIG Air (Umarex), VFC, Krytac, G&G, Specna Arms, ICS | MCX, MCX Rattler, MCX Virtus, MCX SPEAR | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW) | pozo MCX / Rattler |

## FN SCAR

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| FN SCAR-L (Mk16) (`scar-l`) | AEG, GBBR | VFC, Tokyo Marui, Cyma, G&G, King Arms, S&T, Classic Army, Ares | SCAR-L STD, SCAR-L CQC, SCAR-L Mk16 Mod 0 | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW) | pozo SCAR-L |
| FN SCAR-H (Mk17) (`scar-h`) | AEG, GBBR | VFC, Tokyo Marui (NGRS), Cyma, G&G, King Arms, S&T, WE, Classic Army | SCAR-H STD, SCAR-H CQC, SCAR-H TPR, Mk17 | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW) | pozo SCAR-H |
| FN SCAR-SC / SCAR-PDW (`scar-sc`) | AEG, GBBR | VFC, Cyma, Specna Arms | SCAR-SC, SCAR-PDW | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo SCAR-L |

## ACR / Masada

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Bushmaster ACR / Remington ACR (`acr`) | AEG, GBBR | Cyma, Magpul PTS (Masada), ICS, King Arms, Classic Army, Tokyo Marui | ACR, ACR-E, ACR-C | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW) | pozo ACR / Masada |
| Magpul Masada / Magpul PTS Masada / Masada ACR (`masada`) | AEG | Magpul PTS, Cyma, ICS | Masada, Masada Compact | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW) | pozo ACR / Masada |

## Bullpups (AUG, FAMAS, Tavor, L85, Bren 2, P90…)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Steyr AUG A1 / A2 / A3 / HBAR (`aug`) | AEG, GBBR | Jing Gong, Classic Army, Tokyo Marui (AUG A3), KWA, A&K, Double Eagle, G&G, ICS | AUG A1, AUG A2, AUG A3, AUG HBAR, AUG Para | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo AUG |
| FN P90 / P90 TR / PS90 (`p90`) | AEG, GBBR | Tokyo Marui, Cyma, Classic Army, Jing Gong, A&K, G&G | P90, P90 TR, PS90, P90 USG | Picatinny (MIL-STD-1913); Rosca de boca 12 mm antihoraria | pozo P90 |
| FAMAS F1 / G2 (`famas`) | AEG | Tokyo Marui, Cyma, Classic Army, Cybergun, Jing Gong | FAMAS F1, FAMAS G2, FELIN | Rosca de boca 14 mm antihoraria (CCW) | pozo FAMAS |
| IWI Tavor TAR-21 / X95 / CTAR-21 (`tavor`) | AEG, GBBR | Cyma, ICS, Tokyo Marui, Ares, Classic Army, G&G | TAR-21, CTAR-21, MTAR-21, X95 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo Tavor TAR-21 |
| CZ BREN 2 / BREN 805 (`bren2`) | AEG | Arcturus, Ares, Specna Arms, ICS | BREN 2, BREN 805, BREN 2 BR | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo Bren 2 |
| L85 / SA80 (A1, A2, A3) (`l85`) | AEG | Classic Army, Cyma, G&G, Jing Gong, King Arms, WE | L85A1, L85A2, L85A3, L22 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo L85 / SA80 |

## SIG 55x / 516

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| SIG SG 550 / 551 / 552 / 553 / 556 (`sig-552`) | AEG, GBBR | Cyma, Classic Army, G&G, A&K, VFC, Swiss Arms | SG 550, SG 551, SG 552, SG 553, SG 556 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo SIG 55x / 516 |
| SIG SG 516 / SIG 716 (`sig-516`) | AEG, GBBR | Cyma, Classic Army, VFC, G&G, SIG Air, Specna Arms | SIG 516, SIG 516 Patrol, SIG 716 | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15) | pozo AR-15 / M4 (tipo STANAG) |

## VSS / AS VAL

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| VSS Vintorez (`ruso-vss`) | AEG, GBBR | LCT, Cyma, G&G, Specna Arms, Arcturus, E&L | VSS, VSS con óptica integrada | Rosca de boca 14 mm antihoraria (CCW) | pozo VSS / AS VAL |
| AS VAL (`asval`) | AEG, GBBR | LCT, Cyma, G&G, Specna Arms, Arcturus, E&L | AS VAL, SR-3 Vikhr | Rosca de boca 14 mm antihoraria (CCW) | pozo VSS / AS VAL |

## Honey Badger y PDW afines

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| AAC Honey Badger / Honey Badger PDW (`honey-badger`) | AEG, GBBR | Cyma, Krytac, G&G, King Arms, VFC, Specna Arms, Ares | Honey Badger SBR, Honey Badger PDW | Picatinny (MIL-STD-1913); M-LOK | pozo AR-15 / M4 (tipo STANAG) |

## CZ Scorpion EVO

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| CZ Scorpion EVO 3 A1 / S1 / Micro (`scorpion-evo`) | AEG, GBB | ASG, Cyma, G&G, Specna Arms | EVO 3 A1, EVO 3 S1, Scorpion Micro | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo Scorpion EVO |

## Subfusiles (Uzi, Vector, MP9, MAC-10…)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| IMI Uzi / Mini Uzi / Micro Uzi (`uzi`) | AEG, GBB, CO2 | Cyma, Tokyo Marui (NGRS?), KWC, Classic Army, Jing Gong, Echo1, Umarex (CO2) | Uzi, Mini Uzi, Micro Uzi, Pro | Rosca de boca 12 mm antihoraria | pozo Uzi |
| KRISS Vector (Gen I / II) (`vector`) | AEG, GBBR | Tokyo Marui, KWA, Cyma, Krytac, VFC, G&G, ICS | Vector SMG, Vector SDP-E, Gen II | Picatinny (MIL-STD-1913) | pozo KRISS Vector |
| B&T MP9 / TP9 / MP9-N (`mp9`) | AEG, GBB | KWA, Cyma, Cybergun, Umarex | MP9, TP9, MP9-N | Picatinny (MIL-STD-1913) | pozo MP9 / TP9 |
| MAC-10 / MAC-11 / Cobray (`mac10`) | AEG, GBB | Cyma, Classic Army, Jing Gong, Echo1, KWC | MAC-10, MAC-11 | Rosca de boca 12 mm antihoraria | pozo MAC-10 / Ingram |
| PP-19 Bizon / PP-19-01 Vityaz (`bizon`) | AEG, GBB | Cyma, E&L, LCT, G&G, Arcturus | PP-19, PP-19-01 | Picatinny (MIL-STD-1913) | pozo PP-19 Bizon |
| Sterling L2A3 / L34A1 (`sterling`) | AEG | Cyma, Classic Army, King Arms | L2A3, L34A1 (silenciado) | Rosca de boca 14 mm antihoraria (CCW) | — |

## Escopetas

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Remington M870 (Police, Breacher, Tactical) (`m870`) | muelle, gas, CO2, HPA | Cyma, Tokyo Marui, A&K, G&G, Jing Gong, APS, Bolt, Specna Arms, Elite Force, Umarex, S&T, King Arms | M870 Standard, M870 Breacher, M870 Tactical, M870 CQB | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo Escopeta (cartuchos) |
| Benelli M4 Super 90 / M1014 (`m4-super90`) | muelle, gas, HPA | G&G, A&K, APS, King Arms, Echo1, Specna Arms, Ares | M4 Super 90, M1014, M3 Super 90 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo Escopeta (cartuchos) |
| Mossberg M500 / M590 (`mossberg`) | muelle, gas, CO2 | Cyma, Echo1, Umarex, A&K, APS | M500, M590A1, Shockwave | Picatinny (MIL-STD-1913) | pozo Escopeta (cartuchos) |
| Franchi SPAS-12 / SPAS-15 (`spas12`) | muelle, gas, CO2 | Cyma, A&K, King Arms, Bolt, Echo1 | SPAS-12, SPAS-15 | Picatinny (MIL-STD-1913) | pozo Escopeta (cartuchos) |
| Kel-Tec KSG / KSG-25 (`ksg`) | muelle, gas, HPA | G&G, Cyma, Echo1, APS | KSG, KSG-25, KS7 | Picatinny (MIL-STD-1913) | pozo Escopeta (cartuchos) |
| Saiga-12 / AK-12 SG (`saiga12`) | AEG, gas | Cyma, Echo1, A&K, Specna Arms | Saiga-12, Saiga-12K | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo Escopeta (cartuchos) |

## Francotiradores de muelle (VSR, L96, M24…)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Tokyo Marui VSR-10 (Pro / G-Spec) (`vsr10`) | muelle | Tokyo Marui, Maple Leaf, PDI, Action Army, Modify, SRC, Silverback (ensamblaje propio), KJW | VSR-10 Pro, G-Spec, Real Shock | Picatinny (MIL-STD-1913); Raíl de cola de milano de 11 mm; Rosca de boca 14 mm antihoraria (CCW); Montaje de culata VSR-10 / L96 | — |
| Clones VSR-10 / MB (MB01-MB16, SSG) (`mb-vsr-clones`) | muelle | Well, Cyma, Double Eagle, JG, Snow Wolf, Action Army, ASG | MB01, MB03, MB04, MB07, MB08, MB12, MB13, MB14, MB15, MB16 | Picatinny (MIL-STD-1913); Raíl de cola de milano de 11 mm; Rosca de boca 14 mm antihoraria (CCW); Montaje de culata VSR-10 / L96 | — |
| L96 AWS / Accuracy International (L96A1, AW) (`l96`) | muelle, gas | Tokyo Marui, Well, Cyma, A&K, Snow Wolf, ASG, Double Eagle | L96 AWS, L96A1, L96 con chasis, AWM | Picatinny (MIL-STD-1913); Raíl de cola de milano de 11 mm; Rosca de boca 14 mm antihoraria (CCW); Montaje de culata VSR-10 / L96 | — |
| Remington M24 / M40A3 / M40A5 (`m24-m40`) | muelle, gas | Cyma, Well, ASG, Tokyo Marui (M40A5), A&K, Snow Wolf, Double Eagle, Echo1 | M24, M40A3, M40A5, M700 | Picatinny (MIL-STD-1913); Raíl de cola de milano de 11 mm; Rosca de boca 14 mm antihoraria (CCW); Montaje de culata VSR-10 / L96 | — |
| Arctic Warfare AWM / AW / SSG24 (`awm`) | muelle, gas, HPA | Cyma, Ares, Well, ASG, KJ Works, Wolverine, S&T | AWM, AW, AW .338 (M-LOK), ASG SSG24 | Picatinny (MIL-STD-1913); Raíl de cola de milano de 11 mm; Rosca de boca 14 mm antihoraria (CCW) | — |

## Francotiradores AEG, gas y DMR (SVD, Mk12, AWM…)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Dragunov SVD / SVD-S / SVU (`svd`) | AEG, GBBR, muelle | Cyma, LCT, A&K, G&G, Arcturus, E&L, Ares | SVD, SVD-S, SVU, SV-98 | Rosca de boca 14 mm antihoraria (CCW) | pozo AK (cargador curvo) |
| Barrett M82A1 / M107 / M95 (`barrett-m82`) | muelle, AEG, gas | Snow Wolf, Cyma, Double Eagle, S&T, ASG | M82A1, M107, M95, M99 | Picatinny (MIL-STD-1913) | — |

## Ametralladoras ligeras y medias

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| FN M249 SAW / Minimi (Para, Mk46, Mk48) (`m249`) | AEG, GBBR, HPA | A&K, Classic Army, Cyma, Ares (Amoeba), G&G, ICS | M249 SAW, Para, Para M249 PIP, Mk46, Mk48 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo M249 / Mk46 (caja) |
| Mk46 / Mk48 Mod 0 (`mk46`) | AEG, HPA | A&K, Classic Army, G&G, Ares, ICS | Mk46 Mod 0, Mk48 Mod 0 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo M249 / Mk46 (caja) |
| PKM / PKP Pecheneg / PK-S (`pkm`) | AEG | A&K, LCT, Arcturus, Classic Army | PKM, PKP Pecheneg, PKMS | Rosca de boca 14 mm antihoraria (CCW) | pozo PKM (caja) |
| MG42 / MG3 (`mg42`) | AEG, GBB | A&K, Cyma, S&T, Bolt, King Arms | MG42, MG3, MG34 | Rosca de boca 14 mm antihoraria (CCW) | pozo MG42 (cinta) |
| M60 / M60E4 (`m60`) | AEG | A&K, Classic Army | M60, M60E4 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo M249 / Mk46 (caja) |
| RPD / RPK-16 (`rpd`) | AEG | A&K, LCT, Arcturus | RPD, RPK-16 | Rosca de boca 14 mm antihoraria (CCW) | pozo AK (cargador curvo) |

## Pistolas GBB, CO2 y muelle

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Glock 17 (Gen 3 / Gen 4 / Gen 5) (`glock-17`) | GBB, CO2, muelle | Tokyo Marui, VFC (Umarex), KWA, WE, Stark Arms, Umarex, Cybergun, Cyma, HFC, KJ Works, Novritsch | G17, G18C, G19, G22, G23, G26 (compacta), G34, G45 | Rosca de boca 11 mm antihoraria; Raíl universal de pistola (tipo Glock); Corte de corredera para óptica (tipo Glock MOS); Munición BB de 6 mm | pozo Glock (GBB) |
| Glock en chasis aftermarket (Gen 3 / Gen 5) (`glock-kits`) | GBB | AW Custom, Guns Modify, 5KU, Wolverine | chasis y correderas aftermarket | Rosca de boca 11 mm antihoraria; Raíl universal de pistola (tipo Glock); Corte de corredera para óptica (tipo Glock MOS) | pozo Glock (GBB) |
| Colt 1911 (GI / MEU / Commander / Rail) (`p1911`) | GBB, CO2, muelle | Tokyo Marui, KWA, WE, VFC, Umarex, Cybergun, Springfield (licencia), AW Custom, Army Armament, G&G | M1911A1, MEU, Rail, Commander, Government | Rosca de boca 11 mm antihoraria | pozo 1911 (GBB) |
| Hi-Capa / 5.1 / 4.3 / 7.0 / Tokyo Marui (`hi-capa`) | GBB, CO2 | Tokyo Marui, WE, AW Custom, KJW, Stark Arms, Army Armament | Hi-Capa 5.1, 4.3, 3.8, 7.0, Dual Stainless | Rosca de boca 11 mm antihoraria; Raíl universal de pistola (tipo Glock); Corte de corredera para óptica (tipo Glock MOS) | pozo Hi-Capa 5.1 / 4.3 / 7.0 (GBB) |
| Beretta M9 / 92FS / 92A1 / M9A3 (`m9`) | GBB, CO2, muelle | Tokyo Marui, WE, KWC, Umarex (VFC), KJW, Cybergun, Taiwan Gun Works | M9, 92FS, 92A1, M9A3, Elite IA | Rosca de boca 11 mm antihoraria | pozo Beretta M9 / 92 (GBB) |
| SIG P226 / P229 / P220 (`p226`) | GBB, CO2, muelle | Tokyo Marui, WE, KJW, KWA, VFC, Umarex, Cybergun | P226 Rail, P226 E2, P229, P220 | Rosca de boca 11 mm antihoraria | pozo SIG P226 / P229 / P320 (GBB) |
| SIG P320 / M17 / M18 (`p320`) | GBB, CO2 | VFC, SIG Air, KWA | P320 Full, P320 Compact, M17, M18 | Corte de corredera para óptica (tipo Glock MOS); Rosca de boca 11 mm antihoraria | pozo SIG P226 / P229 / P320 (GBB) |
| CZ 75 / SP-01 / Shadow 2 / P-09 (`cz75`) | GBB, CO2 | KJW, KWC, ASG, Cybergun, WE, Army Armament | CZ 75, SP-01 Tactical, Shadow 2, P-09 | Rosca de boca 11 mm antihoraria | pozo CZ 75 / Shadow 2 / P-09 |
| H&K USP / USP Compact / USP Tactical / P30 (`usp`) | GBB, CO2 | Tokyo Marui, KWA, VFC, Umarex, WE | USP, USP Compact, USP Tactical, P30 | Rosca de boca 11 mm antihoraria | pozo HK USP / USP Compact |
| Desert Eagle (.357 / .44 / .50 AE) (`deagle`) | GBB, CO2, muelle | Cyma, Tokyo Marui, WE, KWC, Cybergun, Magnum Research (licencia) | Mark XIX, L6, L5, Desert Eagle Ultra | Picatinny (MIL-STD-1913) | pozo Desert Eagle |
| Walther P99 / PPQ / PPK / P38 / PDP (`walther`) | GBB, CO2, muelle | Umarex, KWC, Cybergun, VFC, WE | P99, PPQ, PPK, PDP, P38 | Rosca de boca 11 mm antihoraria | pozo Walther P99 / PPQ |
| S&W M&P / Springfield XD(M) / XDM / Hellcat (`mp-xdm`) | GBB, CO2 | Cybergun, Tokyo Marui, VFC, KWA, WE, KJW, Springfield | M&P9, M&P9 Shield, XD(M) 3.8, XDM 4.5, XD(S) | Rosca de boca 11 mm antihoraria | pozo S&W M&P / Springfield XD(M) |
| FN Five-seveN / FN 509 (`five-seven`) | GBB, CO2 | Tokyo Marui, WE, Cybergun, VFC | Five-seveN, FN 509 | Rosca de boca 11 mm antihoraria | pozo FN Five-seveN |
| Staccato 2011 / STI (`staccato`) | GBB, CO2 | Tokyo Marui, AW Custom, Army Armament | Staccato P, Staccato C, Staccato XC | Rosca de boca 11 mm antihoraria; Corte de corredera para óptica (tipo Glock MOS) | pozo Hi-Capa 5.1 / 4.3 / 7.0 (GBB) |

## Revólveres

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Colt SAA «Peacemaker» (Single Action Army) (`peacemaker`) | gas, CO2 | Tanaka, Umarex, Bolt, King Arms, HFC | Peacemaker 4, 75", 5, 5", 7, 5" | Rosca de boca 14 mm antihoraria (CCW) | pozo Revólver (cartuchos o speedloader) |
| Colt Python / King Cobra / Anaconda (`python`) | gas, CO2 | Tanaka, Umarex, King Arms, HFC | Python 4", 6", 8", King Cobra | Rosca de boca 14 mm antihoraria (CCW) | pozo Revólver (cartuchos o speedloader) |
| S&W Model 29 / 627 / M&P 340 (`sw-m29`) | gas, CO2 | Tanaka, Umarex, Crosman, Cybergun | Model 29, 627, M&P 340 | Rosca de boca 14 mm antihoraria (CCW) | pozo Revólver (cartuchos o speedloader) |
| Webley Mk VI / Mk IV (`webley`) | CO2, gas | Webley & Scott (Umarex), HFC | Webley Mk VI, Webley Mk IV | Rosca de boca 14 mm antihoraria (CCW) | pozo Revólver (cartuchos o speedloader) |
| Dan Wesson 715 / ASG Dan Wesson (`dan-wesson`) | CO2 | ASG, Umarex | 715 2, 5", 4", 6", 8" | Rosca de boca 14 mm antihoraria (CCW) | pozo Revólver (cartuchos o speedloader) |

## Clásicas y DMR (M14, FAL, G3…)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| M14 EBR / Mk14 Mod 0 / DMR M14 (`mk14-ebr`) | AEG, GBBR | Cyma, G&G, Classic Army, King Arms, Echo1 | M14 EBR-RI, M14 SOCOM, EBR chasis Sage | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15) | pozo M14 |
| M14 / M1A / Mk14 clásico (`m14`) | AEG, GBBR | Cyma, G&G, Classic Army, King Arms, E&L, Echo1 | M14, M1A, Mk14 | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo M14 |
| FN FAL / L1A1 / SLR / G1 (`fal`) | AEG, GBBR | Cyma, Classic Army, G&G, King Arms, Echo1, Jing Gong | FAL, L1A1, G1, FAL Para (Fal Para) | Picatinny (MIL-STD-1913); Rosca de boca 14 mm antihoraria (CCW) | pozo FAL |

## Réplicas históricas (Kar98, Garand, Thompson…)

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Thompson M1928 / M1A1 (`thompson`) | AEG, GBB, CO2 | Cyma, Classic Army, Jing Gong, Bolt, KWA, Umarex | M1928, M1A1, M1927 | Rosca de boca 14 mm antihoraria (CCW) | — |
| MP40 / MP38 (`mp40`) | AEG, GBB | Cyma, Jing Gong, Classic Army, Umarex, Bolt, WE | MP40, MP38 | Rosca de boca 14 mm antihoraria (CCW) | — |
| Mauser Kar98k / M98 / SSG-24 (`kar98`) | muelle, gas | Cyma, Bolt, Classic Army, King Arms, S&T, Tokyo Marui (Kar98k gas) | Kar98k, G98, M98, Mauser | Rosca de boca 14 mm antihoraria (CCW) | — |
| Mosin-Nagant M91/30 (`mosin`) | muelle | S&T, King Arms, Bolt, Double Bell, Cyma | M91/30, M44, SVT-40 | Rosca de boca 14 mm antihoraria (CCW) | — |
| Springfield M1903 / M1 Garand (`m1903`) | muelle, gas | S&T, Bolt, G&P, Cyma | M1903A3, M1 Garand | Rosca de boca 14 mm antihoraria (CCW) | — |
| M1 Carbine / M2 Carbine (`m1-carbine`) | AEG, gas | Marushin, Tokyo Marui, King Arms, Bolt | M1, M1A1, M2 | Rosca de boca 14 mm antihoraria (CCW) | — |
| SKS / Type 56 carbine (`sks`) | AEG, gas, muelle | Cyma, S&T, King Arms, Echo1 | SKS, Type 56, SKS-D | Rosca de boca 14 mm antihoraria (CCW) | — |
| StG 44 / MP44 (`stg44`) | AEG | Cyma, S&T, Echo1, Classic Army | StG 44, MP44 | Rosca de boca 14 mm antihoraria (CCW) | — |
| Lee-Enfield No. 4 / SMLE (`lee-enfield`) | muelle | S&T, Bolt, Zinn, Marushin | SMLE, No. 4, No. 4 T | Rosca de boca 14 mm antihoraria (CCW) | — |
| Winchester 1873 / 1894 / Henry (palanca) (`winchester`) | gas, CO2 | Umarex, Marushin, Maruzen, Bolt | Winchester 1873, Henry, 1894 | Rosca de boca 14 mm antihoraria (CCW) | — |

## Lanzagranadas

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| M203 / M320 / lanzagranadas de 40 mm (`m203`) | gas, mecánica | TAGInn, Cyma, G&G, Evolution, ICS, Bolt | M203, M320, GP-25, GP-34 | Picatinny (MIL-STD-1913); M-LOK | — |

## Plataformas HPA

| Plataforma | Mecanismos | Fabricantes de réplicas | Variantes de cuerpo | Interfaces | Pozo de cargador |
|---|---|---|---|---|---|
| Plataforma HPA AR (Wolverine, Mancraft) (`m4-hpa`) | HPA | Wolverine Airsoft, Mancraft, Polarstar, Gate, PolarStar (módulo) | Gen 2 / 3 / MTW, Mancraft AR, PolarStar F2 | Picatinny (MIL-STD-1913); M-LOK; Rosca de boca 14 mm antihoraria (CCW); Tubo de culata mil-spec (AR-15); Tubo de culata comercial (AR-15); Rosca de boca 1/2"-28 | pozo M4 HPA (chasis Wolverine) |
| Conversiones HPA de AEG existentes (`hpa-conversion`) | HPA | Wolverine, Polarstar, Gate, Mancraft | motor HPA en gearbox Ver.2/3 | Rosca de boca 14 mm antihoraria (CCW) | — |

