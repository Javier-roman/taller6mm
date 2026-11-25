"""Réplicas largas (AKM, AK-105, Mk18) aportadas por Javi: partición de la silueta de la foto lateral en partes.

Misma idea que `replicas_silueta` (solo se guardan números: contornos en mm, colores, proporciones). Las fotos tienen la
boca a la izquierda: se vuelcan para dejarla a la derecha (vista del lado izquierdo del arma). Origen: cara trasera del
receptor (x = 0) y su borde inferior (y = 0); las culatas quedan en x negativa.

Calibre: el Mk18 con la longitud de la ficha de Tokyo Marui (715 mm, culata recogida, confianza alta); el AKM con la
longitud nominal de la plataforma (sin ficha del SKU: confianza baja); el AK-105 de la foto es un montaje con culata y
guardamanos modernos y boca larga, sin ficha: se calibra con el receptor, que es el mismo AK (escala relativa, con
bandera) a partir del AKM.
"""

from __future__ import annotations

from taller6mm_pipeline.fotos.replicas_silueta import Region, Replica

R = Region

AKM = Replica(
    id="akm-lateral-izq",
    carpeta="akm",
    archivo="Captura de pantalla 2026-11-25 111331.png",
    nombre="AKM de culata y guardamanos de madera (lado derecho volcado a lado izquierdo, boca a la derecha)",
    longitud_mm=880.0,
    longitud_fuente="longitud nominal de la plataforma AKM (880 mm, dato público de la plataforma, no ficha del SKU)",
    longitud_confianza="baja",
    umbral=45.0,
    espejo=True,
    regiones={
        "freno": R([(10, 238), (55, 238), (55, 278), (10, 278)]),
        "base_alza": R([(55, 190), (100, 190), (100, 282), (55, 282)]),
        "canon": R([(100, 246), (300, 246), (300, 285), (100, 285)]),
        "tubo_gases": R([(165, 212), (297, 212), (297, 247), (165, 247)]),
        "guardamanos_sup": R([(293, 205), (432, 205), (432, 247), (293, 247)], criterio="madera", eps_px=2.5),
        "guardamanos_inf": R([(297, 247), (490, 247), (490, 310), (297, 310)], criterio="madera", eps_px=2.5),
        "mira_trasera": R([(430, 196), (520, 196), (520, 238), (430, 238)], quita_a=("receptor",)),
        "receptor": R([(425, 216), (790, 216), (790, 304), (425, 304)], criterio="no_madera"),
        "culata": R([(783, 255), (1062, 255), (1062, 372), (783, 372)], criterio="madera", eps_px=4.0),
        "empunadura": R([(693, 306), (790, 306), (790, 440), (693, 440)], criterio="no_madera"),
        "cargador": R([(445, 303), (612, 303), (612, 512), (445, 512)]),
        "guardamonte": R([(612, 296), (702, 296), (702, 354), (612, 354)]),
    },
    origen_region="receptor",
    muestras={
        "madera": (840, 280, 1000, 330),
        "metal_negro": (520, 250, 700, 285),
        "empunadura": (710, 360, 760, 420),
        "cargador": (480, 380, 560, 440),
    },
    grip_filas=(330, 420),
    grip_x_max=800,
    notas=["Boca a la izquierda en la foto original: volcada. Cargador curvo medido de la silueta."],
)

AK105 = Replica(
    id="ak105-lateral-izq",
    carpeta="ak 105",
    archivo="Captura de pantalla 2026-11-25 111100.png",
    nombre="AK-105 con guardamanos M-LOK, boca larga y culata ajustable (lado derecho volcado, boca a la derecha)",
    longitud_mm=943.0,
    longitud_fuente="longitud nominal de la plataforma AK-105 con culata extendida (943 mm, dato público de la "
    "plataforma, no ficha del SKU); el montaje de la foto puede diferir hasta un 8 %; el receptor medido sale a "
    "276 mm frente a 258 mm en el AKM (misma pieza): coherente",
    longitud_confianza="baja",
    umbral=45.0,
    espejo=True,
    regiones={
        "boca": R([(15, 200), (133, 200), (133, 262), (15, 262)]),
        "alza_delantera": R([(130, 165), (160, 165), (160, 215), (130, 215)], quita_a=("guardamanos",)),
        "guardamanos": R([(133, 175), (458, 175), (458, 272), (133, 272)]),
        "receptor": R([(455, 190), (760, 190), (760, 282), (455, 282)]),
        "tubo_culata": R([(760, 226), (850, 226), (850, 272), (760, 272)]),
        "culata": R([(835, 230), (1058, 230), (1058, 382), (835, 382)]),
        "empunadura": R([(676, 285), (780, 285), (780, 410), (676, 410)]),
        "cargador": R([(440, 282), (592, 282), (592, 485), (440, 485)]),
        "guardamonte": R([(592, 283), (690, 283), (690, 325), (592, 325)]),
    },
    origen_region="receptor",
    muestras={
        "polimero": (880, 300, 960, 340),
        "metal_negro": (520, 215, 700, 250),
        "empunadura": (700, 330, 740, 380),
        "cargador": (480, 340, 540, 420),
    },
    grip_filas=(300, 400),
    grip_x_max=800,
    notas=["Montaje moderno sobre receptor AK: guardamanos M-LOK, boca larga y culata ajustable."],
)

MK18 = Replica(
    id="mk18-mod1-lateral-izq",
    carpeta="mk18",
    archivo="Captura de pantalla 2026-11-25 111547.png",
    nombre="Mk18 Mod.1 GBB con guardamanos de raíles (lado derecho volcado, boca a la derecha)",
    longitud_mm=715.0,
    longitud_fuente="largo total del Mk18 Mod.1 GBB, ficha oficial de Tokyo Marui con la culata recogida "
    "(docs/catalogo/cotas-publicas.md, ficha 479)",
    longitud_confianza="alta",
    umbral=45.0,
    espejo=True,
    regiones={
        "boca": R([(15, 215), (112, 215), (112, 255), (15, 255)]),
        "alza_delantera": R([(125, 135), (160, 135), (160, 200), (125, 200)], quita_a=("guardamanos",)),
        "guardamanos": R([(108, 190), (445, 190), (445, 275), (108, 275)]),
        "alza_trasera": R([(598, 135), (655, 135), (655, 200), (598, 200)], quita_a=("receptor_sup",)),
        "receptor_sup": R([(440, 190), (718, 190), (718, 258), (440, 258)]),
        "receptor_inf": R([(440, 258), (665, 258), (665, 335), (440, 335)]),
        "cargador": R([(432, 335), (548, 335), (548, 490), (432, 490)]),
        "empunadura": R([(600, 305), (742, 305), (742, 442), (600, 442)]),
        "culata": R([(712, 205), (978, 205), (978, 390), (712, 390)]),
    },
    origen_region="receptor_sup",
    muestras={
        "receptor": (480, 215, 640, 245),
        "guardamanos": (150, 215, 380, 235),
        "culata": (780, 225, 940, 260),
        "empunadura": (640, 380, 690, 420),
    },
    grip_filas=(330, 420),
    grip_x_max=760,
    notas=["Receptores negros y guardamanos y culata de color arena: dos acabados en la misma réplica."],
)

REPLICAS = (AKM, AK105, MK18)
