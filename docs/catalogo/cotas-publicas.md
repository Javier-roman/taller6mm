# Cotas públicas de fabricantes de airsoft

Datos técnicos **publicados por el fabricante** (fichas de producto y manuales PDF de Tokyo Marui) y, donde no hay ficha del fabricante, cifras de tienda marcadas como tales. Consultados el **2026-11-17** con peticiones puntuales (una cada 3 s, User-Agent identificado; `tokyo-marui.co.jp` no tiene `robots.txt`, devuelve la portada). Complementa `docs/catalogo/cotas-airsoft.md` (cifras de tienda de la ronda del 12-11, todas con confianza baja o media): estas filas **suben a confianza alta** las que coinciden.

Reglas: lo que no se encontró queda como hueco, no se estima. Unidades en mm y g tal como las publica el fabricante. «Extracto» = el texto de la ficha salió en el resultado del buscador y no se abrió la página entera; el valor es el publicado, pero conviene reabrirla antes de fijar una cota definitiva.

## Réplicas completas (Tokyo Marui, ficha oficial)

| Producto (tipo) | Largo total (mm) | Largo con culata extendida (mm) | Cañón (mm) | Peso con cargador vacío (g) | Capacidad | Confianza | Fuente |
|---|---|---|---|---|---|---|---|
| M4A1 MWS (GBB) | 777 | 854 | 250 | 2.970 | 35+1 | alta | [ficha 409](https://www.tokyo-marui.co.jp/products/gas/machinegun/409) |
| M4A1 Carbine (GBB) | 777 | 854 | 250 | 2.950 | 35+1 | alta | [ficha 433](https://www.tokyo-marui.co.jp/products/gas/machinegun/433) |
| Mk18 Mod.1 (GBB) | 715 | 790 | 250 | 2.960 | 35+1 | alta | [ficha 479](https://www.tokyo-marui.co.jp/products/gas/machinegun/479) |
| M4A1 Carbine (AEG estándar) | 767 | 851 | 364 | 2.950 (con batería) | 68 | alta (extracto) | [ficha electric/standard/40](https://www.tokyo-marui.co.jp/products/electric/standard/40) |
| M4A1 Carbine (AEG next-gen) | 777 | 861 | 364 | 2.970 (con batería) | 82 | alta (extracto) | [ficha nextgeneration/202](https://www.tokyo-marui.co.jp/products/electric/nextgeneration/202) |
| CQB-R (AEG next-gen) | 705 | 780 | 275 | 3.370 (con batería) | 82 | alta (extracto) | [ficha nextgeneration/232](https://www.tokyo-marui.co.jp/products/electric/nextgeneration/232), [manual PDF](https://www.tokyo-marui.co.jp/pdf/p_pdfmanual_121217175827.pdf) |
| SOPMOD M4 (AEG next-gen) | 803 | 878 | 364 | 3.270 (con batería) | 82 | alta (extracto del manual) | [manual PDF](https://www.tokyo-marui.co.jp/pdf/p_pdfmanual_121217175827.pdf) |
| Hi-Capa 5.1 Government (GBB) | 222 | n/a | 112 | 894 | n/d en el extracto | alta (extracto) | [ficha blowback/55](https://www.tokyo-marui.co.jp/products/gas/blowback/55) |
| Hi-Capa 5.1 Gold Match (GBB) | 222 | n/a | 112 | 850 | n/d en el extracto | alta (extracto) | [ficha blowback/405](https://www.tokyo-marui.co.jp/products/gas/blowback/405) |
| Hi-Capa D.O.R (GBB) | 220 | n/a | 112 | 839 | 31+1 | alta | [ficha blowback/464](https://www.tokyo-marui.co.jp/products/gas/blowback/464) |
| Hi-Capa White D.O.R (GBB) | 220 | n/a | 112 | 839 | 31+1 | alta | [ficha blowback/513](https://www.tokyo-marui.co.jp/products/gas/blowback/513) |
| Hi-Capa 5.1R Black (GBB, serie R) | 222 | n/a | 33 (cifra publicada tal cual en el extracto; parece corta, a reabrir) | 865 | n/d en el extracto | media (extracto, cifra de cañón dudosa) | [ficha blowbackr/203](https://www.tokyo-marui.co.jp/products/gas/blowbackr/203) |
| Chisato (Hi-Capa de colección) | 210 | n/a | 74 | 784 | n/d en el extracto | alta (extracto) | [ficha blowback/510](https://www.tokyo-marui.co.jp/products/gas/blowback/510) |

Notas:
- La diferencia entre el cañón exterior de la fila 12-11 (355 mm, tienda) y esta ficha (250 mm para el MWS) es porque la ficha publica la **longitud del cañón interior** (`銃身長`). El 355 mm de la tienda era el exterior. **No son la misma cota**; en el modelo hay que llevar las dos con su nombre.
- El M4A1 MWS GBB y el M4A1 Carbine GBB comparten largo total (777/854 mm) y cañón (250 mm); la ficha del Carbine además dice que el cañón exterior es el de la versión inicial, más fino en la parte que entra en el guardamanos.
- Los pesos son con el cargador vacío puesto (y batería en los AEG).

## Interfaces con cota (texto de la ficha oficial)

| Interfaz | Valor | Confianza | Fuente |
|---|---|---|---|
| Ancho de los raíles Picatinny del R.A.S. | 20 mm («ピカティニー規格（20mm幅）») | alta | fichas [409](https://www.tokyo-marui.co.jp/products/gas/machinegun/409) y [479](https://www.tokyo-marui.co.jp/products/gas/machinegun/479) |
| Rosca de boca para silenciadores y otros dispositivos | 14 mm, paso a izquierdas («14mm逆ネジ») | alta | fichas 409, 433 y 479 |
| Caja de embalaje de la serie M4 GBB | 860 x 290 x 100 mm | alta | fichas 409, 433 y 479 |
| Estructura de la culata «enhanced stock» | 6 posiciones de longitud | alta | fichas 409 y 433 |

El diámetro de la rosca (14 mm) es el que publica el fabricante; el paso exacto no aparece en la ficha: queda `null`.

## Tubos y cañones interiores (no son ficha de fabricante)

| Producto | Cota | Confianza | Fuentes | Nota |
|---|---|---|---|---|
| Madbull Python / SteelBull, cañón interior de precisión | 6,03 mm de diámetro interior x 363 mm de largo, para M4/SR16/SG551 | media | [evike.com](https://www.evike.com/products/24373/Madbull-Airsoft-Black-Python-6.03mm-Tightbore-Inner-Barrel-for-AEGs-Length-363mm/), [ampedairsoft.com](https://ampedairsoft.com/inner-barrels-aeg/), [patrolbase.co.uk](https://www.patrolbase.co.uk/madbull-m4-barrel) | Tres tiendas coinciden; falta la ficha de madbull.com. Aluminio 7075-T6 anodizado (extracto de tienda). |
| Cañón interior estándar AEG M4 (Tokyo Marui) | 364 mm (next-gen) | alta | fichas anteriores | La longitud estándar de 363-364 mm coincide con el tubo de Madbull de 363 mm. |

## Huecos (no se inventa nada)

- **Cargadores**: Tokyo Marui publica capacidad y peso del conjunto, no alto, ancho ni grosor del cargador suelto. Siguen en `null` en `cotas-airsoft.md`. Hace falta medir un cargador propio con calibre.
- **Guardamanos**: ningún fabricante de airsoft consultado publica longitud real en mm ni nº de ranuras en su ficha. Solo el ancho Picatinny de 20 mm (arriba).
- **Mira (alza y punto de mira), pistoletes y culatas sueltas**: sin cotas oficiales localizadas. Las búsquedas del 17-11 (Specna Arms, Madbull, Prometheus, G&G, VFC, Krytac) no devolvieron fichas con dimensiones.
- **Siguiente paso**: repetir con G&G, VFC y Specna desde otra red, y localizar fichas de pistoletes y cañones en las webs oficiales de los fabricantes.
