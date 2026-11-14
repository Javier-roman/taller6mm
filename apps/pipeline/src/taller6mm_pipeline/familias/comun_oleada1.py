"""Utilidades de las familias de la oleada 1 del M4: texto de cotas con dato o sin él y extrusión de perfiles.

Las medidas de estas familias son parámetros de barrido (sin SKU verificado): la pieza sale `es_demo`, con cotas de
confianza baja y tope T1 (ver `base._limitar`). Si una cota crítica llega como `None`, la pieza es T0 sin malla.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from build123d import Plane, Polygon, extrude

from taller6mm_pipeline.familias.base import Valor


def mm(p: Mapping[str, Valor], clave: str) -> str:
    """`123 mm` o `sin dato` (lo desconocido nunca se rellena)."""
    v = p.get(clave)
    return "sin dato" if v is None else f"{float(v):g} mm"


def prisma(puntos: Sequence[tuple[float, float]], ancho_mm: float) -> Any:
    """Perfil (X, Y) extruido en Z, centrado en Z=0 (ancho total `ancho_mm`)."""
    return extrude(Plane.XY * Polygon(*puntos, align=None), amount=ancho_mm / 2, both=True)


def caja_de(puntos: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    """(x mínimo, x máximo, y mínimo, y máximo) de un perfil."""
    xs, ys = [q[0] for q in puntos], [q[1] for q in puntos]
    return min(xs), max(xs), min(ys), max(ys)
