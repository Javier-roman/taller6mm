"""Utilidades de forma de la tanda 3 (culatas y bocachas): secciones en planos X = const, ranuras radiales y anillos.

Complementan a `formas.py` (que loftea en planos Y = const, pensado para piezas que crecen hacia arriba): las culatas
y las bocas crecen a lo largo de X, así que aquí las secciones viven en planos perpendiculares al eje del cañón. Todo
es puro y determinista.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from build123d import Box, Plane, Pos, Rot, Spline, Torus, Wire

from taller6mm_pipeline.familias.formas import (
    PUNTOS_SECCION,
    cilindro_en,
    extruir_perfil,
    interpolar,
    loftear,
    revolucion,
)

__all__ = [
    "anillo_en_x",
    "cilindro_en",
    "cuerpo_por_secciones",
    "estadio_en_z",
    "ranura_radial",
    "revolucion_x",
    "seccion_x",
    "torus_xy",
    "ventana_radial",
]


def seccion_x(
    x: float,
    cy: float,
    cz: float,
    hy_pos: float,
    hy_neg: float,
    hz_pos: float,
    hz_neg: float | None = None,
    *,
    n: float = 3.0,
    k: int = PUNTOS_SECCION,
) -> Wire:
    """Sección cerrada y lisa en el plano X = `x`: de `-hy_neg` a `+hy_pos` en Y y de `-hz_neg` a `+hz_pos` en Z.

    Superelipse (exponente `n`: 2 = elipse, 4 = casi rectángulo de esquinas redondeadas). Misma topología siempre,
    así que cualquier par de secciones se puede unir con `loft`.
    """
    hz_neg = hz_pos if hz_neg is None else hz_neg
    puntos = []
    for i in range(k):
        t = 2 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)  # c va a Z (izquierda +), s va a Y (arriba +)
        hz = hz_pos if c >= 0 else hz_neg
        hy = hy_pos if s >= 0 else hy_neg
        puntos.append(
            (
                x,
                cy + hy * math.copysign(abs(s) ** (2 / n), s),
                cz + hz * math.copysign(abs(c) ** (2 / n), c),
            )
        )
    return Wire([Spline(*puntos, periodic=True)])


def cuerpo_por_secciones(x_frente: float, largo: float, tabla: Sequence[Sequence[float]], muestras: int = 14) -> Any:
    """Sólido lofteado hacia atrás (-X) desde `x_frente`.

    Cada fila: (fracción del largo 0..1, hy_pos, hy_neg, hz_pos, hz_neg, n, cy, cz). La primera y la última fila
    cierran el sólido con tapas planas. Se remuestrea con interpolación monótona (PCHIP) en `muestras` secciones
    para que la superficie salga lisa y sin ondas.
    """
    fs = [float(fila[0]) for fila in tabla]
    secciones = []
    for i in range(muestras):
        f = fs[0] + (fs[-1] - fs[0]) * i / (muestras - 1)
        hp, hn, zp, zn, n, cy, cz = (interpolar(fs, [float(fila[c]) for fila in tabla], f) for c in range(1, 8))
        secciones.append(seccion_x(x_frente - f * largo, cy, cz, hp, hn, zp, zn, n=n))
    return loftear(secciones)


def ranura_radial(x0: float, x1: float, ancho: float, alto: float) -> Any:
    """Cortador en forma de ranura: arranca en `x0` con el fondo redondeado, llega a `x1` y sube de Y = 0 a `alto`.

    Ancho `ancho` en Z (centrado). Para tallarla en otra posición angular se gira con `Rot(grados, 0, 0)`.
    """
    r = ancho / 2
    signo = 1.0 if x1 >= x0 else -1.0  # admite también ranuras que avanzan hacia -X (culatas)
    cuerpo = Pos((x0 + signo * r + x1) / 2, alto / 2, 0) * Box(abs(x1 - x0) - r, alto, ancho)
    fondo = cilindro_en("y", r, alto, (x0 + signo * r, alto / 2, 0))
    return cuerpo + fondo


def ventana_radial(x0: float, x1: float, ancho: float, alto: float) -> Any:
    """Como `ranura_radial` pero con los dos extremos redondeados (una ventana cerrada, no una ranura abierta)."""
    r = ancho / 2
    return ranura_radial(x0, x1, ancho, alto) + cilindro_en("y", r, alto, (x1 - r, alto / 2, 0))


def revolucion_x(perfil: Sequence[tuple[float, float]]) -> Any:
    """Sólido de revolución alrededor del eje X. `perfil`: puntos (radio, x) de atrás hacia delante, radio >= 0."""
    return Rot(0, 0, -90) * revolucion(perfil)


def estadio_en_z(centro_x: float, centro_y: float, largo: float, alto: float, grueso: float, cz: float = 0.0) -> Any:
    """Agujero pasante (a lo largo de Z) con forma de estadio (rectángulo con los extremos semicirculares)."""
    r = alto / 2
    recto = max(largo - alto, 0.01)
    cuerpo = Pos(centro_x, centro_y, cz) * Box(recto, alto, grueso)
    return (
        cuerpo
        + cilindro_en("z", r, grueso, (centro_x - recto / 2, centro_y, cz))
        + cilindro_en("z", r, grueso, (centro_x + recto / 2, centro_y, cz))
    )


def anillo_en_x(r_ext: float, r_int: float, x0: float, x1: float) -> Any:
    """Anillo (tubo corto) con el eje en X, de `x0` a `x1`."""
    largo = x1 - x0
    centro = ((x0 + x1) / 2, 0.0, 0.0)
    return cilindro_en("x", r_ext, largo, centro) - cilindro_en("x", r_int, largo + 2, centro)


def torus_xy(centro: tuple[float, float, float], mayor: float, menor: float) -> Any:
    """Toro con el aro tumbado en el plano XY (eje en Z): una anilla de correa."""
    return Pos(*centro) * Torus(mayor, menor)


def plano_xy_extruido(contorno: Sequence[Any], grueso: float, cz: float = 0.0) -> Any:
    """Perfil lateral (X, Y) extruido `grueso` mm en Z y centrado en `cz`."""
    return Pos(0, 0, cz) * extruir_perfil(list(contorno), grueso, Plane.XY)


def girar_x(solido: Any, grados: float) -> Any:
    """Gira el sólido alrededor del eje X (el del cañón)."""
    return Rot(grados, 0, 0) * solido
