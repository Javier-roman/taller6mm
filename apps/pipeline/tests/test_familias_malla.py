"""Salud de la malla de TODAS las familias: cerrada (watertight), caras y normales hacia fuera."""

from functools import cache

import numpy as np
import pytest

from taller6mm_pipeline.familias import FAMILIAS, Pieza
from taller6mm_pipeline.familias.malla import Malla
from taller6mm_pipeline.familias.muestras import tanda

VARIANTES = list(tanda())


@cache
def pieza(indice: int) -> Pieza:
    familia, params = VARIANTES[indice]
    return FAMILIAS[familia].generar(params)


def _ids() -> list[str]:
    return [f"{i:02d}-{familia}" for i, (familia, _) in enumerate(VARIANTES)]


def test_la_tanda_tiene_malla_de_todas_las_familias_con_geometria() -> None:
    con_malla = {VARIANTES[i][0] for i in range(len(VARIANTES)) if pieza(i).malla is not None}
    assert con_malla == {f.id for f in FAMILIAS.values() if f.motivo_sin_malla is None}


@pytest.mark.parametrize("indice", range(len(VARIANTES)), ids=_ids())
def test_malla_cerrada_con_caras_y_normales_hacia_fuera(indice: int) -> None:
    malla = pieza(indice).malla
    if malla is None:
        pytest.skip("variante T0: sin malla")
    # Cerrada: cada arista la comparten exactamente dos triángulos, recorrida en sentidos opuestos.
    assert malla.aristas_abiertas() == 0
    # Caras hacia fuera: el volumen con signo es positivo.
    assert malla.volumen_mm3 > 0
    # Las normales de vértice son unitarias y apuntan al mismo lado que la cara de cada triángulo.
    np.testing.assert_allclose(np.linalg.norm(malla.normales, axis=1), 1.0, atol=1e-3)
    a, b, c = (malla.vertices[malla.triangulos[:, i]] for i in range(3))
    cara = np.cross(b - a, c - a)
    cara /= np.linalg.norm(cara, axis=1, keepdims=True)
    for i in range(3):
        assert np.einsum("ij,ij->i", cara, malla.normales[malla.triangulos[:, i]]).min() > 0.5
    assert malla.normales_hacia_fuera() == 1.0


def test_los_detectores_ven_una_malla_rota() -> None:
    malla = pieza(0).malla
    abierta = Malla(malla.vertices, malla.normales, malla.triangulos[1:])  # falta un triángulo
    assert abierta.aristas_abiertas() > 0
    invertida = Malla(malla.vertices, malla.normales, malla.triangulos[:, ::-1])  # caras del revés
    assert invertida.volumen_mm3 < 0
    assert invertida.normales_hacia_fuera() == 0.0
    una_del_reves = malla.triangulos.copy()
    una_del_reves[0] = una_del_reves[0][::-1]
    assert Malla(malla.vertices, malla.normales, una_del_reves).aristas_abiertas() > 0
