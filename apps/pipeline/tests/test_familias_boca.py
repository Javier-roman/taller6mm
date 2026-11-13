"""Bocacha y silenciador: rosca de 14 mm contra la designación citada, rangos, determinismo y GLB."""

import numpy as np
import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.glb import leer_glb

SILENCIADOR = FAMILIAS["boca.silenciador"]
BOCACHA = FAMILIAS["boca.bocacha"]
SIL = {"longitud": 150.0, "diametro": 35.0, "diametro_paso": 10.0, "profundidad_rosca": 12.0}
BOC = {**SIL, "longitud": 45.0, "diametro": 22.0, "ranuras": 4, "ancho_ranura": 3.0, "longitud_ranura": 20.0}


def test_rosca_de_boca_m14x1() -> None:
    assert e.ROSCA_14_DIAMETRO.valor_mm == 14.0
    assert e.ROSCA_14_PASO.valor_mm == 1.0
    assert "M14x1" in e.ROSCA_14_DIAMETRO.fuente
    assert SILENCIADOR.generar(SIL).requiere == ("rosca-m14x1-ccw",)  # por defecto, CCW (a izquierdas)
    assert SILENCIADOR.generar({**SIL, "rosca": "14mm_cw"}).requiere == ("rosca-m14x1-cw",)
    assert SILENCIADOR.generar(SIL).sha256() != SILENCIADOR.generar({**SIL, "rosca": "14mm_cw"}).sha256()


def test_silenciador_mide_lo_pedido_y_tiene_alojamiento_de_14_mm() -> None:
    pieza = SILENCIADOR.generar(SIL)
    assert pieza.malla.dimensiones_mm == pytest.approx((150.0, 35.0, 35.0), abs=0.05)
    v = pieza.malla.vertices
    radios = np.hypot(v[:, 1], v[:, 2])
    # Vértices del fondo del alojamiento roscado (x = 12): del radio del paso (5) al de la rosca (7).
    fondo = radios[np.isclose(v[:, 0], 12.0, atol=1e-3)]
    assert fondo.max() == pytest.approx(e.ROSCA_14_DIAMETRO.valor_mm / 2, abs=1e-3)
    assert fondo.min() == pytest.approx(5.0, abs=1e-3)
    doc, _ = leer_glb(pieza.glb())
    assert [n["name"] for n in doc["nodes"]] == ["pieza"]  # no ofrece anclajes


def test_bocacha_con_ranuras_y_sin_cotas_de_ranura() -> None:
    completa = BOCACHA.generar(BOC)
    assert completa.malla.dimensiones_mm == pytest.approx((45.0, 22.0, 22.0), abs=0.05)
    assert completa.pendientes == ()
    lisa = BOCACHA.generar({"longitud": 45.0, "diametro": 22.0, "ranuras": 4})
    assert lisa.malla is not None  # las cotas que faltan no son críticas: se modela sin ellas y se avisa
    assert lisa.pendientes == ("diametro_paso", "profundidad_rosca", "ancho_ranura", "longitud_ranura")
    assert any("no se modelan" in n for n in lisa.notas)
    assert len(lisa.malla.triangulos) < len(completa.malla.triangulos)


@pytest.mark.parametrize(
    "cambio",
    [
        {"longitud": 5.0},
        {"diametro": 15.0},
        {"diametro_paso": 36.0},  # mayor que el exterior
        {"profundidad_rosca": 46.0},
        {"rosca": "12mm_ccw"},
        {"ranuras": 9},
        {"longitud_ranura": 45.0},
    ],
)
def test_parametros_fuera_de_rango(cambio: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        BOCACHA.generar({**BOC, **cambio})


def test_sin_longitud_es_t0_y_el_hash_es_estable() -> None:
    assert SILENCIADOR.generar({**SIL, "longitud": None}).nivel == "T0"
    assert BOCACHA.generar(BOC).sha256() == BOCACHA.generar(BOC).sha256()
