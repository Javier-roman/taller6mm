"""Cargador de M4: sin cotas verificadas sale T0; la capacidad nunca se convierte en medidas."""

import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.glb import leer_glb

CARGADOR = FAMILIAS["cargador.m4"]
COTAS = {"largo": 60.0, "ancho": 22.0, "altura": 180.0}


def test_solo_con_la_capacidad_sale_t0_con_las_tres_cotas_pendientes() -> None:
    pieza = CARGADOR.generar({"capacidad": 120})
    assert pieza.nivel == "T0"
    assert pieza.malla is None
    assert pieza.pendientes == ("largo", "ancho", "altura")
    assert all(pieza.ficha().cota(k).desconocido for k in pieza.pendientes)
    assert pieza.metadatos()["parametros"]["largo"] is None
    # Las cotas exteriores figuran como pendientes en los estándares: no hay fuente pública.
    assert any(c.clave == "cargador_m4.dimensiones_exteriores" and c.valor_mm is None for c in e.PENDIENTES)


def test_con_cotas_del_sku_mide_lo_pedido() -> None:
    pieza = CARGADOR.generar({"capacidad": 120, **COTAS})
    assert pieza.malla.dimensiones_mm == pytest.approx((60.0, 180.0, 22.0), abs=1e-3)
    assert pieza.malla.caja_mm[1][1] == 0.0  # cuelga hacia -Y desde el brocal
    assert pieza.requiere == ("cargador.m4.aeg",)
    doc, _ = leer_glb(pieza.glb())
    assert [n["name"] for n in doc["nodes"]] == ["pieza"]
    assert doc["materials"][0]["name"] == "mat.polimero_negro"


def test_la_capacidad_cambia_el_id_pero_no_la_geometria() -> None:
    a, b = CARGADOR.generar({"capacidad": 120, **COTAS}), CARGADOR.generar({"capacidad": 300, **COTAS})
    assert a.id_variante != b.id_variante
    assert (a.malla.vertices == b.malla.vertices).all()
    assert a.sha256() == CARGADOR.generar({"capacidad": 120, **COTAS}).sha256()


@pytest.mark.parametrize("cambio", [{"capacidad": 10}, {"capacidad": 601}, {"sistema": "hpa"}, {"altura": 301.0}])
def test_fuera_de_rango(cambio: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        CARGADOR.generar({"capacidad": 120, **COTAS, **cambio})
