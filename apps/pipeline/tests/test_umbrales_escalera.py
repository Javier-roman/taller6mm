"""Umbrales endurecidos de N3-N5: cada criterio explica su cifra y los topes de brillo existen."""

from __future__ import annotations

from taller6mm_pipeline.calidad import escalera


def test_cada_criterio_de_n3_a_n5_lleva_su_justificacion() -> None:
    cfg = escalera.cargar_niveles()
    for n in ("3", "4", "5"):
        for c in cfg["niveles"][n]["criterios"]:
            assert len(c.get("justificacion", "")) > 40, (n, c["id"])


def test_n5_penaliza_el_exceso_de_brillo_y_de_contraluz() -> None:
    ids = {c["id"] for c in escalera.cargar_niveles()["niveles"]["5"]["criterios"]}
    assert {"reflejos_max", "contraluz_max"} <= ids


def test_un_render_que_reluce_no_pasa_n5() -> None:
    cfg = escalera.cargar_niveles()
    bueno = {
        "contraste": 0.5,
        "reflejos": 0.03,
        "contraluz": 1.9,
        "coc_max_px": 8,
        "foco_nitido": 0.2,
        "ruido": 0.003,
        "denoise": 1,
        "muestras": 96,
    }
    reluciente = {**bueno, "reflejos": 0.3, "contraluz": 3.2, "ruido": 0.018}
    r_bueno = escalera.evaluar_criterios(cfg, 5, "x", bueno)
    r_mal = escalera.evaluar_criterios(cfg, 5, "x", reluciente)
    assert r_bueno.pasa and r_bueno.puntuacion >= 99
    assert r_mal.puntuacion < r_bueno.puntuacion - 15
    assert not r_mal.pasa


def test_los_umbrales_son_mas_duros_que_antes() -> None:
    cfg = escalera.cargar_niveles()["niveles"]
    assert (cfg["3"]["umbral"], cfg["4"]["umbral"], cfg["5"]["umbral"]) == (85, 82, 85)
