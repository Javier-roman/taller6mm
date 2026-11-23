"""Presets de iluminación: formato estable para el visor web y brillo acotado por las medidas CC0."""

from __future__ import annotations

import math

import pytest

from taller6mm_pipeline.materiales import biblioteca, iluminacion


def test_hay_tres_presets_y_el_defecto_es_mate_suave() -> None:
    cfg = iluminacion.cargar()
    assert cfg["defecto"] == "mate_suave"
    assert set(cfg["presets"]) == {"mate_suave", "estudio_contraste", "dramatica_penumbra"}
    assert iluminacion.resolver()["preset"] == "mate_suave"


def test_formato_de_cada_preset_para_el_visor() -> None:
    for nombre, p in iluminacion.cargar()["presets"].items():
        assert {"exposicion_ev", "tono", "mundo", "suelo", "luces", "rugosidad_delta"} <= set(p), nombre
        assert any(luz["id"] == "clave" for luz in p["luces"]), nombre
        for luz in p["luces"]:
            assert len(luz["dir"]) == 3 and len(luz["color"]) == 3 and luz["energia_d2"] > 0 and luz["tam_d"] > 0


def test_mate_suave_es_mas_difusa_y_con_contraluz_mas_tenue_que_el_estudio_de_contraste() -> None:
    mate, duro = iluminacion.resolver("mate_suave"), iluminacion.resolver("estudio_contraste")

    def luz(plan: dict, i: str) -> dict:
        return next(x for x in plan["luces"] if x["id"] == i)

    assert luz(mate, "clave")["tam_d"] > luz(duro, "clave")["tam_d"] * 1.4  # softbox grande
    assert luz(mate, "contra-a")["relativa"] < luz(duro, "contra-a")["relativa"] * 0.6  # contraluz tenue
    assert mate["suelo"]["rugosidad"] > duro["suelo"]["rugosidad"]  # el suelo no refleja


def test_el_brillo_global_se_acota_y_mueve_la_exposicion() -> None:
    cfg = iluminacion.cargar()["brillo"]["global"]
    assert iluminacion.resolver(brillo=99)["brillo"] == cfg["max"]
    assert iluminacion.resolver(brillo=0)["brillo"] == cfg["min"]
    base = iluminacion.resolver("mate_suave")["exposicion_ev"]
    assert iluminacion.resolver("mate_suave", brillo=1.0)["exposicion_ev"] == base
    assert math.isclose(
        iluminacion.resolver("mate_suave", brillo=1.5)["exposicion_ev"] - base, math.log2(1.5), abs_tol=1e-3
    )


@pytest.mark.parametrize("brillo", [0.5, 1.0, 1.5])
@pytest.mark.parametrize("preset", ["mate_suave", "estudio_contraste", "dramatica_penumbra"])
def test_la_rugosidad_nunca_sale_de_la_banda_medida(preset: str, brillo: float) -> None:
    """El anodizado real no es un espejo: ±0,10 sobre la rugosidad medida en la base CC0, con cualquier brillo."""
    por_material = {m: 1.4 for m in biblioteca.MATERIALES} if brillo >= 1.0 else {m: 0.6 for m in biblioteca.MATERIALES}
    plan = iluminacion.resolver(preset, brillo, por_material)
    for mid, spec in biblioteca.MATERIALES.items():
        lo, hi = iluminacion.banda_rugosidad(mid, spec)
        r = iluminacion.rugosidad_final(mid, spec, plan)
        assert lo - 1e-9 <= r <= hi + 1e-9, (mid, r, lo, hi)


def test_mate_suave_baja_el_brillo_del_pavonado_sin_llegar_a_mate() -> None:
    plan = iluminacion.resolver("mate_suave")
    spec = biblioteca.MATERIALES["acero_pavonado"]
    r = iluminacion.rugosidad_final("acero_pavonado", spec, plan)
    assert r > spec["rugosidad"]["media"]
    assert r < 0.3


def test_un_preset_o_un_brillo_malo_se_rechaza() -> None:
    with pytest.raises(ValueError):
        iluminacion.resolver("no_existe")
    with pytest.raises(ValueError):
        iluminacion.parsear_brillo_material(["sin_igual"])
    assert iluminacion.parsear_brillo_material(["goma=0.8"]) == {"goma": 0.8}
