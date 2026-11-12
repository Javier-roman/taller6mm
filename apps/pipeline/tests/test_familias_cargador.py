"""Cargador de M4: familia solo T0 (sin cotas verificables no hay malla); la capacidad no se vuelve medidas."""

import pytest

from taller6mm_pipeline.familias import FAMILIAS, ParametroInvalidoError
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.plano_t0 import generar_plano_svg

CARGADOR = FAMILIAS["cargador.m4"]
COTAS = {"largo": 60.0, "ancho": 22.0, "altura": 180.0}


def test_solo_con_la_capacidad_sale_t0_con_las_cotas_pendientes() -> None:
    pieza = CARGADOR.generar({"capacidad": 120})
    assert pieza.nivel == "T0"
    assert pieza.malla is None
    assert pieza.pendientes == ("largo", "ancho", "altura", "geometria")
    assert all(pieza.ficha().cota(k).desconocido for k in ("largo", "ancho", "altura"))
    assert pieza.metadatos()["parametros"]["largo"] is None
    # Las cotas exteriores figuran como pendientes en los estándares: no hay fuente pública.
    assert any(c.clave == "cargador_m4.dimensiones_exteriores" and c.valor_mm is None for c in e.PENDIENTES)


def test_ni_con_las_cotas_del_sku_se_fabrica_una_caja() -> None:
    pieza = CARGADOR.generar({"capacidad": 120, **COTAS})
    assert pieza.nivel == "T0"  # nunca T2_candidato: una caja recta no es un cargador
    assert pieza.malla is None
    assert pieza.pendientes == ("geometria",)
    assert "STANAG 4179" in pieza.notas[0]
    assert pieza.requiere == ("cargador.m4.aeg",)
    with pytest.raises(ValueError, match="T0"):
        pieza.glb()
    # Las cotas sí sirven para el plano T0.
    svg = generar_plano_svg(pieza.ficha())
    assert 'data-cota="altura"' in svg
    assert "180 mm" in svg


def test_la_capacidad_cambia_el_id() -> None:
    a, b = CARGADOR.generar({"capacidad": 120, **COTAS}), CARGADOR.generar({"capacidad": 300, **COTAS})
    assert a.id_variante != b.id_variante
    assert a.id_variante == CARGADOR.generar({"capacidad": 120, **COTAS}).id_variante


@pytest.mark.parametrize("cambio", [{"capacidad": 10}, {"capacidad": 601}, {"sistema": "hpa"}, {"altura": 301.0}])
def test_fuera_de_rango(cambio: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        CARGADOR.generar({"capacidad": 120, **COTAS, **cambio})
