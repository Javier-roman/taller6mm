"""Marco de familias y raíl Picatinny: cotas contra MIL-STD-1913, rangos, determinismo y GLB."""

import numpy as np
import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.glb import leer_glb, leer_posiciones_m
from taller6mm_pipeline.familias.rail_picatinny import centros_ranuras_mm, longitud_rail_mm

RAIL = FAMILIAS["rail.picatinny"]


def test_cotas_del_estandar_mil_std_1913() -> None:
    # Valores en pulgadas de la norma, convertidos a mm (1 in = 25,4 mm).
    assert e.PICATINNY_ANCHO_RANURA.valor_mm == pytest.approx(0.206 * 25.4, abs=1e-4)  # 5,23 mm
    assert e.PICATINNY_PASO.valor_mm == pytest.approx(0.394 * 25.4, abs=1e-4)  # 10,01 mm
    assert e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm == pytest.approx(0.118 * 25.4, abs=1e-4)  # 3,00 mm
    assert e.PICATINNY_ANCHO.valor_mm == pytest.approx(0.835 * 25.4, abs=1e-4)  # 21,21 mm
    assert e.PICATINNY_ANCHO_PLANO.valor_mm == pytest.approx(0.617 * 25.4, abs=1e-4)  # 15,67 mm
    for cota in e.PICATINNY:
        assert "MIL-STD-1913" in cota.fuente
        assert cota.confianza is not None


def test_la_malla_del_rail_mide_lo_que_dice_el_estandar() -> None:
    pieza = RAIL.generar({"ranuras": 13})
    largo, alto, ancho = pieza.malla.dimensiones_mm
    assert largo == pytest.approx(longitud_rail_mm(13), abs=1e-3)
    assert ancho == pytest.approx(e.PICATINNY_ANCHO.valor_mm, abs=1e-3)
    assert alto == pytest.approx(e.PICATINNY_ALTURA.valor_mm, abs=1e-3)
    v = pieza.malla.vertices
    # Plano superior: los vértices más altos abarcan justo el ancho del plano.
    arriba = v[np.isclose(v[:, 1], alto, atol=1e-3)]
    assert np.ptp(arriba[:, 2]) == pytest.approx(e.PICATINNY_ANCHO_PLANO.valor_mm, abs=1e-3)
    # Fondo de las ranuras: a la profundidad del estándar, y cada ranura con su ancho y su paso.
    fondo = alto - e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm
    xs = np.unique(np.round(v[np.isclose(v[:, 1], fondo, atol=1e-3)][:, 0], 3))
    assert len(xs) == 2 * 13
    np.testing.assert_allclose(xs[1::2] - xs[0::2], e.PICATINNY_ANCHO_RANURA.valor_mm, atol=2e-3)
    np.testing.assert_allclose(np.diff(xs[0::2]), e.PICATINNY_PASO.valor_mm, atol=2e-3)
    np.testing.assert_allclose((xs[0::2] + xs[1::2]) / 2, centros_ranuras_mm(13), atol=2e-3)


@pytest.mark.parametrize("ranuras", [1, 61, 2.5, "13", None, True])
def test_parametros_fuera_de_rango_o_de_tipo(ranuras: object) -> None:
    with pytest.raises(ParametroInvalidoError):
        RAIL.generar({"ranuras": ranuras})


def test_parametro_desconocido() -> None:
    with pytest.raises(ParametroInvalidoError, match="desconocidos"):
        RAIL.generar({"ranuras": 5, "color": "rojo"})


def test_id_y_hash_deterministas() -> None:
    a, b = RAIL.generar({"ranuras": 7}), RAIL.generar({"ranuras": 7.0})
    assert a.id_variante == b.id_variante
    assert a.id_variante.startswith("rail.picatinny@v2-")
    assert a.glb() == b.glb()
    assert a.sha256() == b.sha256()
    assert RAIL.generar({"ranuras": 8}).sha256() != a.sha256()


def test_glb_se_vuelve_a_leer_con_sus_nodos_y_en_metros() -> None:
    pieza = RAIL.generar({"ranuras": 5})
    doc, _ = leer_glb(pieza.glb())
    nombres = [n["name"] for n in doc["nodes"]]
    assert nombres == ["pieza", "socket.rail.top"]
    socket = doc["nodes"][1]
    assert "mesh" not in socket
    assert socket["translation"] == pytest.approx([0.0, e.PICATINNY_ALTURA.valor_mm / 1000, 0.0])
    assert socket["extras"]["interfaz"] == "picatinny"
    assert socket["extras"]["ranuras"] == 5
    extras = doc["nodes"][0]["extras"]
    assert extras["nivel"] == "T2_candidato"
    assert extras["es_demo"] is True
    assert all(c["fuente"] for c in extras["cotas"])
    pos = leer_posiciones_m(pieza.glb())
    assert len(pos) == len(pieza.malla.vertices)
    assert float(np.ptp(pos[:, 0])) == pytest.approx(longitud_rail_mm(5) / 1000, abs=1e-6)
    assert doc["materials"][0]["name"] == "mat.anodizado_negro"
