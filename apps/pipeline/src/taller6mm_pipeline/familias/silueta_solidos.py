"""De un contorno medido (mm) a un sólido de build123d: aristas rectas en las esquinas y splines en las curvas.

El contorno sale de `fotos/silueta.py` (números, nunca píxeles). Un polígono de cientos de segmentos cortos no se
puede filetear con OCCT; por eso los vértices del Douglas-Peucker se agrupan: entre dos esquinas duras (giro mayor que
`esquina_deg`) pasa un único `Spline`, y los tramos casi rectos son `Line`. Así la pieza tiene pocas caras y admite
filetes de verdad.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from build123d import Face, Line, Plane, Pos, Spline, Wire, extrude

from taller6mm_pipeline.familias.formas import filetear
from taller6mm_pipeline.fotos import silueta as sil

Punto = tuple[float, float]


def _giro(a: Punto, b: Punto, c: Punto) -> float:
    """Ángulo de giro en `b` (grados, 0 = recto)."""
    v1, v2 = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    c_ = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(c_))


def aristas_desde_poligono(pts: Sequence[Punto], esquina_deg: float = 32.0) -> list[Any]:
    """Aristas encadenadas (cerradas) de un polígono: `Line` entre esquinas duras, `Spline` por las curvas."""
    n = len(pts)
    duras = [i for i in range(n) if _giro(pts[i - 1], pts[i], pts[(i + 1) % n]) > esquina_deg]
    if not duras:  # todo es curva: spline periódico
        return [Spline(*pts, periodic=True)]
    aristas: list[Any] = []
    for k, i in enumerate(duras):
        j = duras[(k + 1) % len(duras)]
        tramo = [pts[(i + t) % n] for t in range(((j - i) % n or n) + 1)]
        if len(tramo) == 2:
            aristas.append(Line(*tramo))
        else:
            aristas.append(Spline(*tramo))
    return aristas


def cara_con_huecos(ext: Sequence[Punto], huecos: Sequence[Sequence[Punto]] = (), esquina_deg: float = 32.0) -> Face:
    cara = Face(Wire(aristas_desde_poligono(ext, esquina_deg)))
    for h in huecos:
        cara = cara - Face(Wire(aristas_desde_poligono(h, esquina_deg)))
    return cara


def extruir_contorno(
    ext: Sequence[Punto],
    huecos: Sequence[Sequence[Punto]],
    ancho_mm: float,
    *,
    radio: float = 0.0,
    esquina_deg: float = 32.0,
    z_centro: float = 0.0,
) -> Any:
    """Sólido del contorno (plano XY) extruido `ancho_mm` en Z, centrado en `z_centro`, con filete `radio` en las
    aristas de las dos caras grandes (los cantos de la silueta). Si OCCT no puede, prueba radios menores."""
    cara = cara_con_huecos(ext, huecos, esquina_deg)
    cuerpo = extrude(cara, amount=ancho_mm / 2, both=True)
    cuerpo = Pos(0, 0, z_centro) * cuerpo
    if radio > 0:
        cantos = [e for e in cuerpo.edges() if abs(e.center().Z - z_centro) > ancho_mm / 2 - 1e-6]
        for r in (radio, radio * 0.7, radio * 0.5, radio * 0.3):
            f = filetear(cuerpo, r, cantos)
            if f is not cuerpo:
                return f
    return cuerpo


def mm_desde_foto(pts_px: Sequence[Punto], mm_por_px: float, origen_px: Punto) -> list[Punto]:
    return sil.a_mm(pts_px, mm_por_px, origen_px)


__all__ = ["Plane", "aristas_desde_poligono", "cara_con_huecos", "extruir_contorno", "mm_desde_foto"]
