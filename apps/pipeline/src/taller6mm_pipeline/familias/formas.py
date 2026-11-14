"""Formas reales de la oleada 1: secciones lofteadas, perfiles curvos, sólidos de revolución y filetes.

Nada de cubitos: cada pieza se construye a partir de secciones redondeadas (superelipses) unidas con `loft`, perfiles
extruidos con curvas (`Spline`) o sólidos de revolución, y se les da un filete o biselado en las aristas vivas. Las
funciones son deterministas (mismos números, mismo sólido) y puras: no leen ni escriben nada.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from typing import Any

from build123d import Axis, Cylinder, Edge, Face, Line, Plane, Pos, Rot, Solid, Spline, Wire, extrude

PUNTOS_SECCION = 32


def superelipse(
    y: float,
    cx: float,
    b: float,
    a_pos: float,
    a_neg: float | None = None,
    *,
    cz: float = 0.0,
    n: float = 3.0,
    k: int = PUNTOS_SECCION,
) -> Wire:
    """Sección cerrada y lisa en el plano Y = `y`: ancho en X de `-a_neg` a `+a_pos` (alrededor de `cx`) y en Z `±b`.

    El exponente `n` pasa de la elipse (2) a casi un rectángulo de esquinas redondeadas (4+). Misma topología para
    todas las secciones, así que dos de ellas siempre se pueden unir con `loft`.
    """
    a_neg = a_pos if a_neg is None else a_neg
    puntos = []
    for i in range(k):
        t = 2 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)
        a = a_pos if c >= 0 else a_neg
        puntos.append(
            (
                cx + a * math.copysign(abs(c) ** (2 / n), c),
                y,
                cz + b * math.copysign(abs(s) ** (2 / n), s),
            )
        )
    return Wire([Spline(*puntos, periodic=True)])


def interpolar(nudos: Sequence[float], valores: Sequence[float], x: float) -> float:
    """Interpolación cúbica monótona (PCHIP) entre nudos crecientes: lisa y sin rebases entre dos datos."""
    n = len(nudos)
    h = [nudos[i + 1] - nudos[i] for i in range(n - 1)]
    d = [(valores[i + 1] - valores[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = max(0, min(n - 2, next((k for k in range(n - 1) if x <= nudos[k + 1]), n - 2)))
    t = (x - nudos[i]) / h[i]
    t2, t3 = t * t, t * t * t
    return (
        (2 * t3 - 3 * t2 + 1) * valores[i]
        + (t3 - 2 * t2 + t) * h[i] * m[i]
        + (-2 * t3 + 3 * t2) * valores[i + 1]
        + (t3 - t2) * h[i] * m[i + 1]
    )


def loftear(secciones: Sequence[Wire]) -> Any:
    """Sólido cerrado que atraviesa las secciones (con tapas planas en la primera y la última)."""
    return Solid.make_loft(list(secciones))


def extruir_perfil(
    contorno: Sequence[Edge | Line | Spline], ancho_mm: float, plano: Plane | None = None, *, centrado: bool = True
) -> Any:
    """Cara cerrada a partir de aristas encadenadas (líneas y splines) extruida `ancho_mm` en Z (centrada en Z = 0)."""
    cara = Face(Wire(list(contorno)))
    if plano is not None:
        cara = plano * cara
    return extrude(cara, amount=ancho_mm / 2, both=True) if centrado else extrude(cara, amount=ancho_mm)


def revolucion(perfil: Sequence[tuple[float, float]], *, suave: bool = False) -> Any:
    """Sólido de revolución alrededor del eje Y. `perfil`: puntos (radio, y) de abajo a arriba, con radio >= 0.

    Con `suave` la pared exterior es un spline que pasa por los puntos (cuerpos curvos); si no, una poligonal con
    aristas vivas (luego se redondean con `filetear`). Los extremos se cierran contra el eje.
    """
    pts = [(float(r), float(y)) for r, y in perfil]
    if suave:
        pared: list[Edge] = [Spline(*pts)]
    else:
        pared = [Line(a, b) for a, b in itertools.pairwise(pts)]
    base, cima = pts[0], pts[-1]
    cierre = [(0.0, cima[1]), (0.0, base[1])]
    cadena = [*pts, *(q for q in cierre if q != pts[-1])]
    if cadena[-1] != base:
        cadena.append(base)
    if suave:
        pared: list[Any] = [Spline(*pts)]
        cadena = [pts[-1], *(q for q in cierre if q != pts[-1]), base]
    else:
        pared = []
    segmentos = [Line(a, b) for a, b in itertools.pairwise(cadena) if a != b]
    cara = Face(Wire([*pared, *segmentos]))
    return Solid.revolve(cara, 360.0, Axis.Y)


def cilindro_en(eje: str, radio: float, largo: float, centro: tuple[float, float, float]) -> Any:
    """Cilindro de `largo` mm centrado en `centro` y con su eje a lo largo de X, Y o Z."""
    cuerpo = Cylinder(radio, largo)  # eje Z por defecto
    giro = {"x": Rot(0, 90, 0), "y": Rot(90, 0, 0), "z": Rot(0, 0, 0)}[eje]
    return Pos(*centro) * giro * cuerpo


def filetear(solido: Any, radio: float, aristas: Sequence[Edge] | None = None) -> Any:
    """Redondea aristas con `radio` mm. Si OCCT no puede (geometría tangente), devuelve el sólido sin tocar."""
    try:
        redondeado = solido.fillet(radio, list(aristas) if aristas is not None else solido.edges())
    except Exception:
        return solido
    return redondeado if redondeado.is_valid and redondeado.volume > 0 else solido


def biselar(solido: Any, distancia: float, aristas: Sequence[Edge] | None = None) -> Any:
    """Chaflán de `distancia` mm; mismo criterio que `filetear` si no se puede."""
    try:
        cortado = solido.chamfer(distancia, None, list(aristas) if aristas is not None else solido.edges())
    except Exception:
        return solido
    return cortado if cortado.is_valid and cortado.volume > 0 else solido
