"""Las piezas de la oleada 1 que tienen que parecer reales no pueden ser cubitos (bloques con un par de cortes).

Tres señales independientes de la malla teselada: relleno de la caja envolvente, nº de triángulos y variedad de
orientaciones de las caras. Una caja o una caja achaflanada fallan las tres, así que el detector se prueba a sí mismo.
"""

import numpy as np
import pytest
from build123d import Box, Cylinder, Pos

from taller6mm_pipeline.familias.malla import Malla, teselar
from taller6mm_pipeline.familias.oleada1 import VARIANTES, Variante, generar

FAMILIAS_REALES = {
    "empunadura.pistolete",
    "mira.asa_a2",
    "mira.buis",
    "accesorio.empunadura_vertical",
    "sup.palanca_armado",
}
CASOS = [pytest.param(v, id=v.id) for v in VARIANTES if v.familia in FAMILIAS_REALES]
RELLENO_MAXIMO = 0.65  # volumen / caja envolvente: un bloque macizo ronda 0,9-1,0
TRIANGULOS_MINIMOS = 1500  # una caja son 12; una pieza con filetes y huecos, miles
ORIENTACIONES_MINIMAS = 300  # normales de cara distintas (a 0,1 de resolución): una caja achaflanada tiene ~26


def metricas(malla: Malla) -> dict[str, float]:
    a, b, c = (malla.vertices[malla.triangulos[:, i]] for i in range(3))
    cruz = np.cross(b - a, c - a)
    normales = cruz / np.maximum(np.linalg.norm(cruz, axis=1, keepdims=True), 1e-12)
    x, y, z = malla.dimensiones_mm
    return {
        "relleno": malla.volumen_mm3 / (x * y * z),
        "triangulos": float(len(malla.triangulos)),
        "orientaciones": float(len({tuple(np.round(n, 1)) for n in normales})),
    }


def parece_cubito(malla: Malla) -> list[str]:
    m = metricas(malla)
    motivos = []
    if m["relleno"] > RELLENO_MAXIMO:
        motivos.append(f"relleno de la caja {m['relleno']:.2f} > {RELLENO_MAXIMO}")
    if m["triangulos"] < TRIANGULOS_MINIMOS:
        motivos.append(f"{m['triangulos']:.0f} triángulos < {TRIANGULOS_MINIMOS}")
    if m["orientaciones"] < ORIENTACIONES_MINIMAS:
        motivos.append(f"{m['orientaciones']:.0f} orientaciones de cara < {ORIENTACIONES_MINIMAS}")
    return motivos


@pytest.mark.parametrize("v", CASOS)
def test_la_pieza_no_es_un_cubito(v: Variante) -> None:
    pieza = generar(v)
    assert pieza.malla is not None
    assert parece_cubito(pieza.malla) == []
    assert pieza.malla.aristas_abiertas() == 0


def test_el_detector_caza_cajas_y_bloques_con_cortes() -> None:
    caja = Box(30, 20, 10)
    biselada = caja.chamfer(2, None, caja.edges())
    con_agujero = Box(40, 30, 20) - Pos(0, 0, 0) * Cylinder(6, 20)
    for solido in (caja, biselada, con_agujero):
        assert len(parece_cubito(teselar(solido, 0.05, 0.35))) >= 2


def test_las_variantes_de_las_cinco_familias_estan_cubiertas() -> None:
    assert {p.values[0].familia for p in CASOS} == FAMILIAS_REALES
