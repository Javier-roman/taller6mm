"""Materiales de la escalera frente a la guía de aspecto (docs/catalogo/guia-aspecto-piezas.md) y la base CC0."""

from __future__ import annotations

from pathlib import Path

import pytest

from taller6mm_pipeline.materiales import biblioteca, cc0


def test_la_rugosidad_de_la_receta_sigue_lo_medido_en_la_base_cc0() -> None:
    """Guía §2.3: rugosidad media de cada acabado a ±0,10 de lo medido en su mapa 1K CC0."""
    comprobados = 0
    for mid, mat in biblioteca.MATERIALES.items():
        base = cc0.catalogo().get(mat.get("cc0", {}).get("id", ""), {})
        medida = base.get("medidas", {}).get("rugosidad_media")
        if medida is None or mat.get("tipo") == "vidrio":
            continue
        comprobados += 1
        assert abs(mat["rugosidad"]["media"] - medida) <= 0.1, mid
    assert comprobados >= 5


def test_un_material_negro_cae_en_el_rango_de_albedo_de_la_guia() -> None:
    """Guía §2.1: el albedo de un negro está entre sRGB 30 y 55 (un negro puro hace desaparecer la forma)."""
    negros = [m for m in biblioteca.MATERIALES.values() if m.get("negro")]
    assert len(negros) >= 3
    for mat in negros:
        srgb = 255 * (sum(mat["color"]) / 3) ** (1 / 2.2)
        assert 30 <= srgb <= 55, (mat["nombre"], srgb)


def test_los_metales_son_metalicos_y_los_no_metales_no() -> None:
    for mid, mat in biblioteca.MATERIALES.items():
        if mat["tipo"] == "metal":
            assert mat["metalico"] >= 0.95, mid
        elif mat["tipo"] in ("polimero", "madera", "vidrio"):
            assert mat["metalico"] == 0.0, mid


def test_las_bases_cc0_se_resuelven_o_caen_a_procedural_sin_inventar() -> None:
    assert cc0.resolver(None) is None
    assert cc0.resolver({"id": "no-existe"}) is None
    r = cc0.resolver(biblioteca.MATERIALES["parkerizado"]["cc0"])
    assert r is None or (Path(r["mapas"]["rugosidad"]).exists() and r["rug_media_tex"] == pytest.approx(0.366))
    assert cc0.catalogo()["acg-metal038"]["carpeta"].startswith("assets-src/materiales-cc0/")


def test_cada_material_declara_una_base_cc0_del_catalogo() -> None:
    for mid, mat in biblioteca.MATERIALES.items():
        assert mat["cc0"]["id"] in cc0.catalogo(), mid
