"""Utilidades compartidas por las familias de pistolas de airsoft (GBB, AEP y gas/CO2).

Ejes comunes de toda pistola (los de las demás familias): +X boca, +Y arriba, +Z izquierda del tirador. Origen
común del conjunto: el eje del cañón (Y = 0) en la cara trasera de la corredera (X = 0). Así el armazón, la corredera,
el cañón y las miras encajan por identidad y los sockets sólo dicen dónde se tocan. Los cargadores se construyen
con su propio eje (+Y a lo largo del cargador, origen en el centro de su cara superior) y se colocan con el socket.

Las proporciones son de barrido (genéricas, de un tamaño «completo» y otro «compacto»): ninguna es la medida de un
SKU. Por eso todas las cotas salen con confianza baja y las piezas no pasan de T1.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from build123d import Compound, Edge, Line, Pos, Sphere, Spline, Wire

from taller6mm_pipeline.familias.formas import PUNTOS_SECCION
from taller6mm_pipeline.ficha import Confianza, Cota

FECHA = "2026-11-15"
FUENTE_ESTIMADO = (
    "estimado a ojo de las proporciones generales de una pistola de airsoft de tamaño completo o compacto; sin "
    "fuente ni calibre (15-11-2026). Se sustituye por la ficha de un SKU o por medición con calibre."
)
# Plano sobre el que apoya la corredera en el armazón (Y de la cara inferior de la corredera), en mm.
PLANO_CORREDERA_Y = -11.0
INTERFAZ_RIEL_CORREDERA = "riel-corredera-pistola"  # propuesta: aún no está en interfaces.json
INTERFAZ_MIRA_PISTOLA = "cola-milano-mira-pistola"  # propuesta
INTERFAZ_CAJA_EMPUNADURA = "montaje-empunadura-lateral-1911"  # propuesta
INTERFAZ_SEGURO_EMPUNADURA = "montaje-seguro-empunadura-1911"  # propuesta
INTERFAZ_CANON_PISTOLA = "alojamiento-canon-pistola"  # propuesta
INTERFACES_PROPUESTAS = (
    INTERFAZ_RIEL_CORREDERA,
    INTERFAZ_MIRA_PISTOLA,
    INTERFAZ_CAJA_EMPUNADURA,
    INTERFAZ_SEGURO_EMPUNADURA,
    INTERFAZ_CANON_PISTOLA,
)


def estimada(clave: str, valor_mm: float) -> Cota:
    return Cota(clave, round(valor_mm, 4), FUENTE_ESTIMADO, FECHA, Confianza.BAJA)


def seccion_x(x: float, y_sup: float, y_inf: float, semi: float, n: float = 5.0, *, k: int = PUNTOS_SECCION) -> Wire:
    """Sección cerrada y lisa en el plano X = `x`: de `y_inf` a `y_sup` en Y y de `-semi` a `+semi` en Z.

    El exponente `n` va de la elipse (2) a un rectángulo de esquinas redondeadas (5-7). Todas las secciones tienen
    la misma topología, así que se pueden unir con `loft` a lo largo de X.
    """
    cy, b = (y_sup + y_inf) / 2, (y_sup - y_inf) / 2
    puntos = []
    for i in range(k):
        t = 2 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)
        puntos.append(
            (
                x,
                cy + b * math.copysign(abs(s) ** (2 / n), s),
                semi * math.copysign(abs(c) ** (2 / n), c),
            )
        )
    return Wire([Spline(*puntos, periodic=True)])


def contorno(tramos: Sequence[tuple[str, Sequence[tuple[float, float]]]], *, cerrar: bool = True) -> list[Edge]:
    """Cadena de aristas en el plano XY. Cada tramo es `("l", puntos)` (poligonal) o `("s", puntos)` (spline) y
    arranca en el último punto del anterior; el primer tramo trae su punto de partida como primer punto."""
    aristas: list[Edge] = []
    actual: tuple[float, float] | None = None
    primero: tuple[float, float] | None = None
    for tipo, pts in tramos:
        pts = [(float(a), float(b)) for a, b in pts]
        if actual is None:
            primero, actual, pts = pts[0], pts[0], pts[1:]
        if tipo == "l":
            for q in pts:
                aristas.append(Line(actual, q))
                actual = q
        else:
            aristas.append(Spline(actual, *pts))
            actual = pts[-1]
    if cerrar and primero is not None and actual is not None and actual != primero:
        aristas.append(Line(actual, primero))
    return aristas


def spline_cerrada(puntos: Sequence[tuple[float, float]]) -> list[Edge]:
    """Contorno liso y cerrado (spline periódico) por los puntos del plano XY."""
    return [Spline(*[(float(a), float(b)) for a, b in puntos], periodic=True)]


def hoyuelos(puntos: Sequence[tuple[float, float, float]], radio: float) -> Any:
    """Compuesto de esferas para restar de una sola vez (punteado del agarre)."""
    return Compound([Pos(*p) * Sphere(radio) for p in puntos])


def hexagonal(
    x0: float, x1: float, y0: float, y1: float, paso: float, *, x_desde_ejes: bool = False
) -> list[tuple[float, float]]:
    """Rejilla hexagonal de puntos (x, y) dentro del rectángulo: base del punteado y del moleteado."""
    pts: list[tuple[float, float]] = []
    fila, y = 0, y0
    alto = paso * math.sqrt(3) / 2
    while y <= y1:
        x = x0 + (paso / 2 if fila % 2 else 0.0)
        while x <= x1:
            pts.append((x, y))
            x += paso
        y += alto
        fila += 1
    return pts


def hendiduras_v(
    ancho: float, fondo: float, pasos: Sequence[float], y0: float, y1: float, z_cara: float, lado: int
) -> list[Any]:
    """Cuchillas en V (verticales) para serrar una cara lateral de una corredera: cada una entra `fondo` mm."""
    from build123d import Plane, Polygon, extrude

    cortes = []
    for x in pasos:
        v = Polygon(
            (x - ancho / 2, z_cara + lado * 0.2),
            (x, z_cara - lado * fondo),
            (x + ancho / 2, z_cara + lado * 0.2),
            align=None,
        )
        # El polígono está en (x, z): se levanta al plano XZ y se extruye a lo largo de Y.
        cara = Plane.XZ * v
        cortes.append(Pos(0, y1, 0) * extrude(cara, amount=y1 - y0))
    return cortes


def loft_recto(secciones: Sequence[Wire]) -> Any:
    """Loft reglado (tramos rectos entre secciones): sin rebases entre secciones muy juntas, a diferencia del liso."""
    from build123d import Solid

    return Solid.make_loft(list(secciones), ruled=True)


def filas_suaves(
    largo: float,
    y_sup: float,
    y_inf: float,
    semi: float,
    n_cuerpo: float,
    tras: tuple[float, float, float, float],
    dela: tuple[float, float, float, float],
    *,
    pasos: int = 7,
) -> list[tuple[float, float, float, float, float]]:
    """Secciones `(x, y_sup, y_inf, semi, n)` de un cuerpo largo con el extremo trasero y el delantero rebajados.

    `tras` y `dela` son `(rebaje de y_sup, rebaje de y_inf, rebaje de semi, longitud de la zona)` en mm. El rebaje
    decae con una curva cuadrática desde el extremo hasta el cuerpo, y la sección se redondea (`n` baja) en el borde.
    """
    filas: list[tuple[float, float, float, float, float]] = []
    zt, zd = tras[3], dela[3]
    for i in range(pasos + 1):  # extremo trasero: de x = 0 al cuerpo
        t = i / pasos
        d = (1 - t) ** 2
        filas.append((zt * t, y_sup - tras[0] * d, y_inf + tras[1] * d, semi - tras[2] * d, n_cuerpo - 1.4 * d))
    filas.append((largo * 0.5, y_sup, y_inf, semi, n_cuerpo))
    for i in range(pasos + 1):  # extremo delantero: del cuerpo a x = largo
        t = i / pasos
        d = t**2
        fila = (largo - zd + zd * t, y_sup - dela[0] * d, y_inf + dela[1] * d, semi - dela[2] * d, n_cuerpo - 1.6 * d)
        filas.append(fila)
    return filas
