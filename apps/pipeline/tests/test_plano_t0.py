import xml.etree.ElementTree as ET

import pytest

from taller6mm_pipeline.ficha import Confianza, Cota, Ficha
from taller6mm_pipeline.plano_t0 import escala_px_por_mm, generar_plano_svg

FECHA = "2026-11-11"


def _ficha() -> Ficha:
    return Ficha(
        "demo",
        "Réplica <demo> & co",
        (
            Cota("longitud_total", 777.0, "fuente", FECHA, Confianza.MEDIA),
            Cota("canon_interno", 250.0, "fuente", FECHA, Confianza.BAJA),
            Cota("canon_externo", None, "sin confirmar", FECHA, desconocido=True),
        ),
    )


def test_svg_determinista() -> None:
    assert generar_plano_svg(_ficha()) == generar_plano_svg(_ficha())


def test_svg_valido_y_con_cotas() -> None:
    svg = generar_plano_svg(_ficha())
    ET.fromstring(svg)  # noqa: S314 (SVG propio) XML bien formado (el título se escapa)
    assert "777 mm" in svg
    assert "250 mm" in svg
    assert svg.count("sin dato") == 1
    assert 'data-cota="canon_externo" data-estado="sin-dato"' in svg


def test_escala_proporcional_a_mm_reales() -> None:
    ficha = _ficha()
    escala = escala_px_por_mm(ficha)
    svg = generar_plano_svg(ficha)
    assert escala == pytest.approx(900 / 777)
    assert f'width="{250 * escala:.2f}"' in svg
    assert escala_px_por_mm(Ficha("x", "y")) == 1.0
