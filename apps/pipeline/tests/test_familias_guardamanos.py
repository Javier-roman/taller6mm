"""Guardamanos M-LOK: cotas de la ranura contra la especificación citada, sockets, T0 sin dato y ficha."""

import numpy as np
import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.guardamanos_mlok import centros_mlok_mm, ranuras_rail_que_caben
from taller6mm_pipeline.ficha import Confianza, Cota, Ficha

GUARDAMANOS = FAMILIAS["guardamanos.mlok"]
BASE = {"longitud": 254.0, "diametro_exterior": 40.0, "grosor_pared": 2.5, "ranuras_mlok": 5}


def test_cotas_mlok_de_la_especificacion_citada() -> None:
    assert e.MLOK_LARGO_RANURA.valor_mm == 32.0
    assert e.MLOK_ANCHO_RANURA.valor_mm == 7.0
    assert e.MLOK_SEPARACION.valor_mm == 8.0
    assert e.MLOK_RADIO_ESQUINA.valor_mm == 2.38
    assert e.MLOK_PASO_MM == 40.0
    for cota in e.MLOK:
        assert "M-LOK" in cota.fuente
        assert cota.confianza is Confianza.MEDIA  # la fuente pública da valores aproximados


def test_las_ranuras_mlok_de_la_malla_miden_32_por_7_a_paso_40() -> None:
    # Octogonal y sin raíl: la cara izquierda (+Z) es plana, en z = radio.
    pieza = GUARDAMANOS.generar({**BASE, "seccion": "octogonal", "rail_superior": False})
    v = pieza.malla.vertices
    cara = v[np.isclose(v[:, 2], 20.0, atol=1e-3)]
    centros = centros_mlok_mm(254.0, 5)
    np.testing.assert_allclose(np.diff(centros), 40.0, atol=1e-3)
    for x in centros:
        borde = cara[(np.abs(cara[:, 0] - x) < 19.9) & (np.abs(cara[:, 1]) < 3.6)]
        assert np.ptp(borde[:, 0]) == pytest.approx(32.0, abs=0.01)
        assert np.ptp(borde[:, 1]) == pytest.approx(7.0, abs=0.01)
        assert float(borde[:, 0].mean()) == pytest.approx(x, abs=0.5)
    assert pieza.malla.dimensiones_mm == pytest.approx((254.0, 40.0, 40.0), abs=1e-3)


def test_sockets_y_nodos_del_glb() -> None:
    pieza = GUARDAMANOS.generar(BASE)
    doc, _ = leer_glb(pieza.glb())
    nombres = [n["name"] for n in doc["nodes"]]
    assert len(nombres) == 1 + 1 + 3 * 5  # pieza + raíl superior + 3 caras x 5 ranuras
    assert nombres[0] == "pieza"
    assert "socket.rail.top" in nombres
    assert {"socket.mlok.side.l.1", "socket.mlok.side.r.5", "socket.mlok.bottom.3"} <= set(nombres)
    assert "socket.mlok.top.1" not in nombres
    rail = doc["nodes"][nombres.index("socket.rail.top")]
    assert rail["extras"]["ranuras"] == ranuras_rail_que_caben(254.0) == 24
    assert rail["translation"][1] == pytest.approx((20.0 + e.PICATINNY_ALTURA.valor_mm) / 1000)
    izquierda = doc["nodes"][nombres.index("socket.mlok.side.l.1")]
    assert izquierda["translation"] == pytest.approx([centros_mlok_mm(254.0, 5)[0] / 1000, 0.0, 0.020])
    sin_rail = GUARDAMANOS.generar({**BASE, "rail_superior": False})
    assert len(sin_rail.sockets) == 4 * 5
    assert sin_rail.malla.dimensiones_mm == pytest.approx((254.0, 40.0, 40.0), abs=1e-3)


@pytest.mark.parametrize(
    "cambio",
    [
        {"longitud": 99.0},
        {"longitud": 451.0},
        {"diametro_exterior": 29.0},
        {"grosor_pared": 6.0},
        {"ranuras_mlok": 0},
        {"ranuras_mlok": 7},  # 7 ranuras piden 288 mm y solo hay 254
        {"seccion": "cuadrada"},
        {"rail_superior": "si"},
    ],
)
def test_parametros_fuera_de_rango(cambio: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        GUARDAMANOS.generar({**BASE, **cambio})


def test_determinismo() -> None:
    assert GUARDAMANOS.generar(BASE).sha256() == GUARDAMANOS.generar(dict(reversed(BASE.items()))).sha256()


def test_cota_desconocida_da_t0_sin_malla_y_nunca_un_valor_inventado() -> None:
    pieza = GUARDAMANOS.generar({**BASE, "longitud": None})
    assert pieza.nivel == "T0"
    assert pieza.malla is None
    assert pieza.pendientes == ("longitud",)
    cota = pieza.ficha().cota("longitud")
    assert cota.valor_mm is None
    assert cota.desconocido is True
    with pytest.raises(ValueError, match="T0"):
        pieza.glb()


def test_las_cotas_del_sku_salen_de_la_ficha_con_su_fuente() -> None:
    ficha = Ficha(
        "sku-de-prueba",
        "Guardamanos de prueba",
        (
            Cota("longitud", 254.0, "https://example.com/ficha", "2026-11-11", Confianza.ALTA),
            Cota("diametro_exterior", 40.0, "https://example.com/ficha", "2026-11-11", Confianza.MEDIA),
            Cota("grosor_pared", None, "el fabricante no lo publica", "2026-11-11", desconocido=True),
        ),
    )
    pieza = GUARDAMANOS.generar({"ranuras_mlok": 5}, ficha=ficha)
    assert pieza.es_demo is False
    assert pieza.nivel == "T0"  # falta el grosor de pared
    assert pieza.pendientes == ("grosor_pared",)
    assert pieza.ficha().cota("longitud").fuente == "https://example.com/ficha"
    assert pieza.ficha().cota("grosor_pared").fuente == "el fabricante no lo publica"

    completa = Ficha(
        ficha.id, ficha.nombre, (*ficha.cotas[:2], Cota("grosor_pared", 2.5, "calibre", "2026-11-11", "media"))
    )
    pieza = GUARDAMANOS.generar({"ranuras_mlok": 5}, ficha=completa)
    assert pieza.nivel == "T2_candidato"
    assert pieza.es_demo is False
    assert np.array_equal(pieza.malla.vertices, GUARDAMANOS.generar(BASE).malla.vertices)  # misma geometría
