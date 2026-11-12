"""Regresión visual ligera: por familia, la caja envolvente sale de los parámetros, y el volumen y el número de
triángulos no cambian sin querer. Si cambias la geometría a propósito, sube `version` y actualiza la tabla.
"""

import math

import pytest

from taller6mm_pipeline.familias import FAMILIAS
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.rail_picatinny import longitud_rail_mm

ALTO_RAIL = e.PICATINNY_ALTURA.valor_mm
ANCHO_RAIL = e.PICATINNY_ANCHO.valor_mm
D_MILSPEC = e.TUBO_DIAMETRO_MILSPEC.valor_mm
D_ROSCA = e.TUBO_ROSCA_DIAMETRO.valor_mm

# (familia, parámetros, caja esperada (mín, máx) en mm deducida de los parámetros, volumen mm³, triángulos)
CASOS = [
    (
        "rail.picatinny",
        {"ranuras": 13},
        ((0, 0, -ANCHO_RAIL / 2), (longitud_rail_mm(13), ALTO_RAIL, ANCHO_RAIL / 2)),
        17972.3,
        340,
    ),
    (
        "guardamanos.mlok",
        {"longitud": 150.0, "diametro_exterior": 40.0, "grosor_pared": 2.5, "ranuras_mlok": 3},
        ((0, -20, -20), (150, 20 + ALTO_RAIL, 20)),
        60794.2,
        2612,
    ),
    (
        "guardamanos.mlok",
        {
            "longitud": 425.0,
            "diametro_exterior": 40.0,
            "grosor_pared": 2.5,
            "ranuras_mlok": 10,
            "seccion": "octogonal",
            "rail_superior": False,
        },
        ((0, -20, -20), (425, 20, 20)),
        110127.1,
        6624,
    ),
    (
        "boca.silenciador",
        {"longitud": 150.0, "diametro": 35.0, "diametro_paso": 10.0, "profundidad_rosca": 12.0},
        ((0, -17.5, -17.5), (150, 17.5, 17.5)),
        130963.8,
        432,
    ),
    (
        "boca.bocacha",
        {
            "longitud": 45.0,
            "diametro": 22.0,
            "diametro_paso": 9.0,
            "profundidad_rosca": 12.0,
            "ranuras": 4,
            "ancho_ranura": 3.0,
            "longitud_ranura": 20.0,
        },
        ((0, -11, -11), (45, 11, 11)),
        11538.5,
        498,
    ),
    (
        "culata.tubo",
        {"longitud": 184.15, "longitud_rosca": 20.0},
        ((-184.15, -D_ROSCA / 2, -D_ROSCA / 2), (0, D_ROSCA / 2, D_ROSCA / 2)),
        123280.4,
        284,
    ),
]


@pytest.mark.parametrize(("familia", "params", "caja", "volumen", "triangulos"), CASOS, ids=[c[0] for c in CASOS])
def test_caja_volumen_y_triangulos(
    familia: str, params: dict[str, object], caja: tuple, volumen: float, triangulos: int
) -> None:
    malla = FAMILIAS[familia].generar(params).malla
    minimos, maximos = malla.caja_mm
    assert minimos == pytest.approx(caja[0], abs=0.01)  # 0,01 mm: flecha del teselado en las curvas
    assert maximos == pytest.approx(caja[1], abs=0.01)
    assert malla.volumen_mm3 == pytest.approx(volumen, rel=1e-4)
    assert len(malla.triangulos) == triangulos
    assert malla.aristas_abiertas() == 0


def test_los_volumenes_cuadran_con_el_calculo_a_mano() -> None:
    """El volumen de la malla se parece al analítico (algo menor: el teselado inscribe polígonos en los círculos)."""
    silenciador = FAMILIAS["boca.silenciador"].generar(CASOS[3][1]).malla.volumen_mm3
    analitico = math.pi * (17.5**2 * 150 - 5**2 * 150 - (7**2 - 5**2) * 12)
    assert silenciador == pytest.approx(analitico, rel=0.01)
    assert silenciador < analitico

    bocacha = FAMILIAS["boca.bocacha"].generar(CASOS[4][1]).malla.volumen_mm3
    cuerpo = math.pi * (11**2 * 45 - 4.5**2 * 45 - (7**2 - 4.5**2) * 12)
    ranuras = 4 * 20 * 3 * (11 - 4.5)  # cuatro ranuras de 20 x 3 mm a través de la pared (aprox. prismática)
    assert bocacha == pytest.approx(cuerpo - ranuras, rel=0.02)

    tubo = FAMILIAS["culata.tubo"].generar({"longitud": 184.15}).malla.volumen_mm3
    assert tubo == pytest.approx(math.pi * (D_MILSPEC / 2) ** 2 * 184.15, rel=0.01)

    # Raíl: área del perfil por longitud, menos N ranuras de ancho x profundidad x ancho del plano superior.
    bisel = (ANCHO_RAIL - e.PICATINNY_ANCHO_PLANO.valor_mm) / 2
    plano = e.PICATINNY_ANCHO_PLANO.valor_mm
    area = plano * ALTO_RAIL + 2 * bisel * bisel  # rectángulo del cuello + dos triángulos de apoyo
    prof, ancho_r = e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm, e.PICATINNY_ANCHO_RANURA.valor_mm
    # La ranura (3,00 mm) baja más que el bisel superior (2,77 mm): corta también parte de los apoyos.
    resto = prof - bisel
    corte = plano * prof + bisel * bisel + 2 * (resto * bisel - resto * resto / 2)
    rail = FAMILIAS["rail.picatinny"].generar({"ranuras": 13}).malla.volumen_mm3
    assert rail == pytest.approx(area * longitud_rail_mm(13) - 13 * ancho_r * corte, rel=1e-3)
