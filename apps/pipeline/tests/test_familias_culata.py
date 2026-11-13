"""Tubo de culata y culata telescópica: diámetros contra las fichas citadas, socket, rangos y determinismo."""

import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias.glb import leer_glb

TUBO = FAMILIAS["culata.tubo"]
CULATA = FAMILIAS["culata.telescopica"]
CUL = {"longitud": 180.0, "altura": 120.0, "ancho": 40.0, "pared": 3.0, "diametro_tubo": 29.0}


TUBO_P = {"longitud": 184.15, "diametro": 29.0}  # parámetros de barrido: el diámetro real es del SKU


@pytest.mark.parametrize(
    ("especificacion", "interfaz"), [("milspec", "tubo-culata-mil-spec"), ("comercial", "tubo-culata-comercial")]
)
def test_tubo_mide_su_diametro_y_ofrece_el_socket_de_culata(especificacion: str, interfaz: str) -> None:
    pieza = TUBO.generar({**TUBO_P, "especificacion": especificacion})
    assert pieza.malla.dimensiones_mm == pytest.approx((184.15, 29.0, 29.0), abs=0.02)
    assert pieza.malla.caja_mm[1][0] == 0.0  # va hacia -X desde el receptor
    assert pieza.ofrece == (interfaz,)
    assert pieza.requiere == ()  # no se exige una rosca concreta a todo tubo
    assert pieza.pendientes == ("longitud_rosca", "diametro_rosca")
    doc, _ = leer_glb(pieza.glb())
    assert [n["name"] for n in doc["nodes"]] == ["pieza", "socket.stock"]
    assert doc["nodes"][1]["translation"] == pytest.approx([-0.18415, 0.0, 0.0])
    assert doc["nodes"][1]["extras"]["interfaz"] == interfaz


def test_tubo_con_tramo_roscado() -> None:
    pieza = TUBO.generar({**TUBO_P, "longitud_rosca": 20.0, "diametro_rosca": 30.0})
    assert pieza.malla.dimensiones_mm[1] == pytest.approx(30.0, abs=0.02)
    assert pieza.pendientes == ()


def test_el_diametro_del_tubo_es_del_sku_y_sin_el_no_hay_malla() -> None:
    pieza = TUBO.generar({"longitud": 184.15, "diametro": None})
    assert pieza.nivel == "T0" and pieza.malla is None
    assert "diametro" in pieza.pendientes


def test_culata_encaja_en_su_tubo() -> None:
    pieza = CULATA.generar(CUL)
    assert pieza.requiere == ("tubo-culata-mil-spec",)
    assert CULATA.generar({**CUL, "especificacion": "comercial"}).requiere == ("tubo-culata-comercial",)
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
        TUBO.generar({**TUBO_P, "longitud": 301.0})
    assert TUBO.generar({**TUBO_P, "longitud": None}).nivel == "T0"
    assert CULATA.generar({**CUL, "altura": None}).nivel == "T0"
