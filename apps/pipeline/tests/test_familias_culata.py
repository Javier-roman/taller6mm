"""Tubo de culata y culata telescópica: diámetros contra las fichas citadas, socket, rangos y determinismo."""

import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.glb import leer_glb

TUBO = FAMILIAS["culata.tubo"]
CULATA = FAMILIAS["culata.telescopica"]
CUL = {"longitud": 180.0, "altura": 120.0, "ancho": 40.0, "pared": 3.0}


def test_diametros_del_tubo() -> None:
    assert e.TUBO_DIAMETRO_MILSPEC.valor_mm == pytest.approx(1.148 * 25.4, abs=1e-4)  # 29,16 mm
    assert e.TUBO_DIAMETRO_COMERCIAL.valor_mm == pytest.approx(1.168 * 25.4, abs=1e-4)  # 29,67 mm
    assert e.TUBO_ROSCA_DIAMETRO.valor_mm == pytest.approx(30.1625, abs=1e-4)  # 1 3/16 in
    assert e.TUBO_ROSCA_PASO.valor_mm == pytest.approx(1.5875, abs=1e-4)  # 16 hilos por pulgada


@pytest.mark.parametrize(("especificacion", "diametro"), [("milspec", 29.1592), ("comercial", 29.6672)])
def test_tubo_mide_su_diametro_y_ofrece_el_socket_de_culata(especificacion: str, diametro: float) -> None:
    pieza = TUBO.generar({"especificacion": especificacion, "longitud": 184.15})
    assert pieza.malla.dimensiones_mm == pytest.approx((184.15, diametro, diametro), abs=0.02)
    assert pieza.malla.caja_mm[1][0] == 0.0  # va hacia -X desde el receptor
    assert pieza.ofrece == (f"tubo_culata.{especificacion}",)
    assert pieza.pendientes == ("longitud_rosca",)
    doc, _ = leer_glb(pieza.glb())
    assert [n["name"] for n in doc["nodes"]] == ["pieza", "socket.stock"]
    assert doc["nodes"][1]["translation"] == pytest.approx([-0.18415, 0.0, 0.0])
    assert doc["nodes"][1]["extras"]["interfaz"] == f"tubo_culata.{especificacion}"


def test_tubo_con_tramo_roscado() -> None:
    pieza = TUBO.generar({"longitud": 184.15, "longitud_rosca": 20.0})
    assert pieza.malla.dimensiones_mm[1] == pytest.approx(e.TUBO_ROSCA_DIAMETRO.valor_mm, abs=0.02)
    assert pieza.pendientes == ()


def test_culata_encaja_en_su_tubo() -> None:
    pieza = CULATA.generar(CUL)
    assert pieza.requiere == ("tubo_culata.milspec",)
    assert CULATA.generar({**CUL, "especificacion": "comercial"}).requiere == ("tubo_culata.comercial",)
    assert pieza.id_variante != CULATA.generar({**CUL, "especificacion": "comercial"}).id_variante


def test_culata_es_solo_t0_aunque_tenga_todas_las_cotas() -> None:
    pieza = CULATA.generar(CUL)
    assert pieza.nivel == "T0"  # un trapecio macizo no es una culata: sin forma verificada no hay malla
    assert pieza.malla is None
    assert pieza.pendientes == ("geometria",)
    assert "Sin malla" in pieza.notas[0]
    assert pieza.ficha().cota("longitud").valor_mm == 180.0
    with pytest.raises(ValueError, match="T0"):
        pieza.glb()


@pytest.mark.parametrize(
    "cambio", [{"longitud": 99.0}, {"altura": 200.0}, {"ancho": 33.0}, {"pared": 0.5}, {"especificacion": "ak"}]
)
def test_culata_fuera_de_rango(cambio: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        CULATA.generar({**CUL, **cambio})


def test_tubo_fuera_de_rango_y_sin_longitud() -> None:
    with pytest.raises(ParametroInvalidoError):
        TUBO.generar({"longitud": 301.0})
    assert TUBO.generar({"longitud": None}).nivel == "T0"
    assert CULATA.generar({**CUL, "altura": None}).nivel == "T0"
