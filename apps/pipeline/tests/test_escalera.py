"""Escalera de calidad: asignador de materiales, métricas por nivel, niveles consecutivos, cola y regresión."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from build123d import Box, Cylinder, Pos

from taller6mm_pipeline.calidad import detalle_fino, escalera, imagen
from taller6mm_pipeline.calidad.entrada import PiezaCalidad
from taller6mm_pipeline.familias.malla import teselar
from taller6mm_pipeline.materiales import asignador, biblioteca

CFG = escalera.cargar_niveles()


def test_el_catalogo_de_materiales_es_valido_y_procedural() -> None:
    assert asignador.validar_catalogo() == []
    texto = json.dumps(biblioteca.MATERIALES).lower()
    assert not any(ext in texto for ext in (".png", ".jpg", ".exr", ".tif"))


def test_una_referencia_a_imagen_se_rechaza() -> None:
    mat = {**biblioteca.MATERIALES["goma"], "textura": "foto-de-tercero.jpg"}
    assert any("imagen" in e for e in biblioteca.validar("goma", mat))


@pytest.mark.parametrize(
    ("familia", "id_", "material"),
    [
        ("canon.exterior", "canon-carabina-ligero", "parkerizado"),
        ("canon.exterior", "canon-a2-pesado", "acero_pavonado"),
        ("empunadura.pistolete", "pist-moe", "polimero_grano"),
        ("guardamanos.variantes", "gm-mlok-9", "anodizado_negro"),
        ("guardamanos.variantes", "gm-carabina", "polimero_grano"),
        ("mira.buis", "mira-buis-trasera", "anodizado_negro"),
    ],
)
def test_el_asignador_elige_el_material_por_id_y_familia(familia: str, id_: str, material: str) -> None:
    a = asignador.asignar(familia, id_)
    assert a.material_id == material
    assert a.cubierta


def test_una_familia_sin_regla_cae_al_defecto_y_no_cuenta_como_cubierta() -> None:
    a = asignador.asignar("inventada.rara", "x-1")
    assert not a.cubierta
    assert a.material_id == asignador.cargar()["defecto"]


def test_la_variacion_entre_piezas_es_determinista_y_distinta() -> None:
    a1, a2 = (
        asignador.asignar("canon.exterior", "canon-cqb-corto"),
        asignador.asignar("canon.exterior", "canon-mid-ligero"),
    )
    assert a1.variacion == asignador.asignar("canon.exterior", "canon-cqb-corto").variacion
    assert a1.variacion != a2.variacion
    assert a1.semilla == asignador.semilla_de("canon-cqb-corto")


def _malla(solido: object) -> tuple[np.ndarray, np.ndarray]:
    m = teselar(solido, 0.05, 0.35)
    return m.vertices, m.triangulos.astype(np.int64)


def test_n2_un_cilindro_liso_no_tiene_detalle_fino_y_uno_con_ranuras_si_periodicidad() -> None:
    liso = detalle_fino.medir(*_malla(Cylinder(10, 120, rotation=(0, 90, 0))))
    ranurado = Cylinder(10, 120, rotation=(0, 90, 0))
    for i in range(20):
        ranurado = ranurado - Pos(-54 + i * 5.5, 0, 0) * Cylinder(10.5, 1.0, rotation=(0, 90, 0)).cut(
            Cylinder(9.0, 1.2, rotation=(0, 90, 0))
        )
    estriado = detalle_fino.medir(*_malla(ranurado))
    assert liso["rasgos_pequenos"] == 0
    assert estriado["periodicidad"] > liso["periodicidad"]
    assert estriado["escalones_100mm"] > liso["escalones_100mm"]


def test_n2_es_determinista() -> None:
    v, t = _malla(Box(30, 20, 10) - Pos(0, 0, 0) * Cylinder(4, 20))
    assert detalle_fino.medir(v, t) == detalle_fino.medir(v, t)


def test_los_criterios_puntuan_y_la_bandera_no_penaliza() -> None:
    perfecto = {c["clave"]: c.get("min", c.get("max")) for c in CFG["niveles"]["3"]["criterios"]}
    r = escalera.evaluar_criterios(CFG, 3, "canon", perfecto)
    assert r.puntuacion == 100.0
    assert r.pasa
    r2 = escalera.evaluar_criterios(CFG, 3, "canon", {"rug_std": 0.0})
    assert not r2.pasa
    assert any(c["estado"] == "bandera" for c in r2.criterios)
    assert escalera.evaluar_criterios(CFG, 3, "canon", {"vacia": True}).pasa is False


def test_las_sobrescrituras_por_grupo_cambian_el_umbral() -> None:
    m = {
        "area_fina_frac": 1.0,
        "transiciones_finas_cm2": 100.0,
        "viva_frac": 0.0,
        "periodicidad": 0.2,
        "escalones_100mm": 100.0,
        "rasgos_pequenos": 6.0,
    }
    canon = escalera.evaluar_criterios(CFG, 2, "canon", m)
    pist = escalera.evaluar_criterios(CFG, 2, "pistolete", m)
    assert canon.puntuacion != pist.puntuacion  # el cañón admite 6 rasgos; el pistolete exige 8


def test_la_forma_de_los_umbrales_es_coherente() -> None:
    for n, nv in CFG["niveles"].items():
        assert 0 < nv["umbral"] <= nv["techo"] <= 100, n
        for c in nv["criterios"]:
            assert ("min" in c) != ("max" in c), c["id"]
            assert c["peso"] > 0
            assert c["motivo"] and c["sugerencia"]


def test_imagen_mascara_y_erosion() -> None:
    m = np.zeros((40, 40), dtype=bool)
    m[10:30, 10:30] = True
    assert imagen.erosionar(m, 2).sum() == 16 * 16


def test_imagen_n3_distingue_textura_plana_de_texturada() -> None:
    rng = np.random.default_rng(1)
    m = np.ones((60, 60), dtype=bool)
    plano = np.full((60, 60, 3), 0.5)
    rugoso = np.clip(0.5 + rng.normal(0, 0.05, (60, 60, 3)), 0, 1)
    a = imagen.medir_n3(plano, plano, m, 0.5)
    b = imagen.medir_n3(rugoso, rugoso, m, 0.5)
    assert a["rug_std"] == 0.0
    assert b["rug_std"] > 0.03
    assert b["rug_alta_frecuencia"] > a["rug_alta_frecuencia"]


def test_circulo_de_confusion_es_cero_en_el_foco_y_crece_fuera() -> None:
    meta = {"lente_mm": 70.0, "fstop": 5.6, "foco_m": 1.0, "sensor_mm": 36.0, "res": [960, 720]}
    c = imagen.coc_px(np.array([1.0, 0.8, 1.3]), meta)
    assert c[0] == pytest.approx(0.0, abs=1e-9)
    assert c[1] > 0
    assert c[2] > 0


def _pieza(id_: str, niveles: dict[int, tuple[float, bool]]) -> escalera.PiezaEscalera:
    cal = PiezaCalidad(id_, "t", "canon.exterior", np.zeros((3, 3)), np.zeros((1, 3), dtype=np.int64), (), (), {})
    p = escalera.PiezaEscalera(id_, "canon.exterior", "canon", asignador.asignar("canon.exterior", id_), cal)
    for n, (punt, pasa) in niveles.items():
        p.niveles[n] = escalera.NivelResultado(n, punt, pasa, 95.0)
    return p


def test_el_nivel_actual_no_se_salta_peldanos() -> None:
    assert _pieza("a", {1: (90, True), 2: (80, True), 3: (50, False), 4: (99, True)}).nivel_actual == 2
    assert _pieza("b", {1: (50, False), 2: (99, True)}).nivel_actual == 0
    assert _pieza("c", {n: (99, True) for n in escalera.NIVELES}).nivel_actual == 5


def test_regresion_por_caida_o_por_dejar_de_pasar() -> None:
    p = _pieza("x", {1: (90, True), 2: (70, False), 3: (80, True)})
    anterior = {
        "piezas": {
            "x": {
                "1": {"puntuacion": 90, "pasa": True},
                "2": {"puntuacion": 80, "pasa": True},
                "3": {"puntuacion": 85, "pasa": True},
            }
        }
    }
    regs = escalera.regresiones(anterior, [p])
    assert {(r["nivel"], r["paso_a_no_pasa"]) for r in regs} == {(2, True), (3, False)}
    assert escalera.regresiones(None, [p]) == []


def test_la_variacion_de_conjunto_pide_tres_piezas_del_mismo_material() -> None:
    ps = []
    for i, rug in enumerate((0.40, 0.42, 0.44)):
        p = _pieza(f"canon-p{i}", {4: (80, True)})
        p.niveles[4].metricas = {"rug_media": rug}
        ps.append(p)
    v = escalera.variacion_conjunto(ps)
    assert all(x is not None and x > 0 for x in v.values())
    assert escalera.variacion_conjunto(ps[:2]) == {"canon-p0": None, "canon-p1": None}


def test_cli_hasta_n2_escribe_cola_e_historial_y_detecta_regresion(tmp_path: Path) -> None:
    cola, hist = tmp_path / "cola.json", tmp_path / "hist.json"
    args = ["--hasta", "2", "--id", "pist-a2", "--cola", str(cola), "--historial", str(hist)]
    assert escalera.main(args) == 0
    doc = json.loads(cola.read_text(encoding="utf-8"))
    assert doc["esquema"] == escalera.ESQUEMA_COLA
    assert doc["resumen"]["n1"]["evaluadas"] == 1
    h = json.loads(hist.read_text(encoding="utf-8"))
    h["ejecuciones"][0]["piezas"]["pist-a2"]["2"] = {"puntuacion": 99.0, "pasa": True}  # simula un nivel mejor antes
    hist.write_text(json.dumps(h), encoding="utf-8")
    assert escalera.main([*args, "--estricto"]) == 2
