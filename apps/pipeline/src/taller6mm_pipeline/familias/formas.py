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

from build123d import (
    Axis,
    Box,
    Cylinder,
    Edge,
    Face,
    Line,
    Plane,
    Polygon,
    Pos,
    Rot,
    Solid,
    Spline,
    Wire,
    extrude,
    revolve,
)

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


# --- Detalle fino de piezas torneadas (eje X): rosca en anillos, moleteado, planos de llave y taladros de cara. ---

# Altura del filete de una rosca métrica ISO (perfil básico ISO 68-1): 5/8 de H, con H = 0,866 x paso.
ALTURA_FILETE_ISO = 0.5413


def revolucion_x(perfil: Sequence[tuple[float, float]]) -> Any:
    """Sólido de revolución alrededor del eje X. `perfil`: polígono cerrado de puntos (x, radio), con radio >= 0.

    Un solo sólido con todos sus escalones, chaflanes, gargantas y dientes de rosca: sale de una pieza, sin booleanas
    tangentes. Para una pieza hueca, el polígono recorre la pared exterior y vuelve por la interior.
    """
    limpio = [q for q, anterior in zip(perfil, [perfil[-1], *perfil[:-1]], strict=True) if q != anterior]
    return revolve(Plane.XY * Polygon(*limpio, align=None), axis=Axis.X)


def dientes_rosca(x0: float, x1: float, r_raiz: float, r_cresta: float, paso: float) -> list[tuple[float, float]]:
    """Puntos (x, radio) de una rosca en V hecha de anillos (sin hélice) entre `x0` y `x1`; empieza y acaba en la raíz.

    Vale para rosca exterior (cresta > raíz) o interior (cresta < raíz) y en los dos sentidos de X. El paso se
    ajusta para que quepa un número entero de filetes.
    """
    n = max(1, round(abs(x1 - x0) / paso))
    d = (x1 - x0) / n
    puntos = [(x0, r_raiz)]
    for i in range(n):
        xa = x0 + i * d
        puntos += [(xa + 0.42 * d, r_cresta), (xa + 0.58 * d, r_cresta), (xa + d, r_raiz)]
    return puntos


def estrias_x(radio: float, x0: float, x1: float, n: int, hondo: float, *, fase: float = 0.0) -> list[Any]:
    """Herramientas de corte de un moleteado recto: `n` estrías en V a lo largo de X sobre un cilindro de `radio`."""
    medio = 0.5 * math.tau * radio / n * 0.62  # media anchura de la estría en la superficie
    cuna = extrude(
        Plane.YZ * Polygon((radio - hondo, 0.0), (radio + 0.4, medio * 1.6), (radio + 0.4, -medio * 1.6), align=None),
        x1 - x0,
    )
    return [Rot(fase + 360.0 * k / n, 0, 0) * Pos(x0, 0, 0) * cuna for k in range(n)]


def planos_llave_x(radio: float, x0: float, x1: float, entre_caras: float, n: int = 2) -> list[Any]:
    """Herramientas de corte de `n` planos de llave (caras planas repartidas) en un cilindro de eje X."""
    alto = radio + 1.0 - entre_caras / 2
    caja = Pos((x0 + x1) / 2, entre_caras / 2 + alto / 2, 0) * Box(x1 - x0, alto, 2 * radio + 2)
    return [Rot(360.0 * k / n, 0, 0) * caja for k in range(n)]


def taladros_cara_x(x: float, radio_circulo: float, n: int, diametro: float, hondo: float) -> list[Any]:
    """Herramientas de corte: `n` taladros ciegos repartidos en una cara perpendicular a X (para llave de pivotes).

    `hondo` > 0 taladra hacia -X desde `x`; < 0, hacia +X.
    """
    broca = Pos(x - hondo / 2, radio_circulo, 0) * Rot(0, 90, 0) * Cylinder(diametro / 2, abs(hondo) + 0.02)
    return [Rot(360.0 * k / n, 0, 0) * broca for k in range(n)]


def ranura_oblonga(largo: float, ancho: float, alto: float) -> Any:
    """Prisma oblongo (extremos semicirculares) de `largo` en X y `ancho` en Z, extruido `alto` hacia +Y desde Y = 0.

    Centrado en X y en Z: es la herramienta de una ventana fresada (ranura de apagallamas, aligeramiento).
    """
    recto = max(largo - ancho, 0.01)
    caja = Pos(0, alto / 2, 0) * Box(recto, alto, ancho)
    for lado in (1, -1):
        caja = caja + Pos(lado * recto / 2, alto / 2, 0) * Rot(90, 0, 0) * Cylinder(ancho / 2, alto)
    return caja
