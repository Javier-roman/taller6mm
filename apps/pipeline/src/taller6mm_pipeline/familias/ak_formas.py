"""Utilidades de forma de la familia AK: secciones a lo largo de X, secciones sobre una espina curva y cortes.

Complementa a `formas.py` (que loftea a lo largo de Y). Aquí las piezas son largas en X (+X = boca), así que las
secciones se dibujan en planos X = const, o perpendiculares a una espina curva en el plano XY (cargador). Todo es puro
y determinista: mismos números, mismo sólido.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from build123d import Box, Cylinder, Edge, Plane, Pos, RectangleRounded, Rot, Solid, Spline, Wire

from taller6mm_pipeline.familias.formas import PUNTOS_SECCION, filetear, interpolar, loftear
from taller6mm_pipeline.ficha import Confianza, Cota

FECHA = "2026-11-15"
FUENTE_ESTIMADO_AK = (
    "estimado a ojo de las proporciones generales de la familia AK de airsoft (AKM, AK-74, AKS-74U, AK-105); sin "
    "fuente ni calibre (15-11-2026). Se sustituye por la ficha de un SKU o por medición con calibre."
)


def estimada(clave: str, valor_mm: float) -> Cota:
    """Cota de proporción general sin fuente verificable: siempre confianza BAJA, nunca un dato de SKU."""
    return Cota(clave, round(valor_mm, 4), FUENTE_ESTIMADO_AK, FECHA, Confianza.BAJA)


def _potencia(valor: float, n: float) -> float:
    return math.copysign(abs(valor) ** (2 / n), valor)


def seccion_x(
    x: float,
    y_arriba: float,
    y_abajo: float,
    semiancho: float,
    *,
    cz: float = 0.0,
    n: float = 4.0,
    k: int = PUNTOS_SECCION,
) -> Wire:
    """Sección cerrada y lisa en el plano X = `x`: de `y_abajo` a `y_arriba` en Y y `cz ± semiancho` en Z.

    El exponente `n` va de la elipse (2) a un rectángulo de esquinas redondeadas (4 o más).
    """
    cy, hy = (y_arriba + y_abajo) / 2, (y_arriba - y_abajo) / 2
    pts = []
    for i in range(k):
        t = 2 * math.pi * i / k
        pts.append((x, cy + hy * _potencia(math.sin(t), n), cz + semiancho * _potencia(math.cos(t), n)))
    return Wire([Spline(*pts, periodic=True)])


def seccion_x_redondeada(x: float, y_arriba: float, y_abajo: float, semiancho: float, radio: float, cz: float = 0.0) -> Wire:
    """Sección rectangular con esquinas de radio `radio` (líneas y arcos: sus lados planos salen planos, sin ondas)."""
    alto = y_arriba - y_abajo
    r = min(radio, alto / 2 * 0.98, semiancho * 0.98)
    plano = Plane(origin=(x, (y_arriba + y_abajo) / 2, cz), x_dir=(0, 0, 1), z_dir=(1, 0, 0))
    return (plano * RectangleRounded(2 * semiancho, alto, r)).wire()


def loft_x(
    x_ini: float,
    x_fin: float,
    nudos: Sequence[tuple[float, float, float, float]],
    *,
    n: float = 4.0,
    pasos: int = 14,
    cz: float = 0.0,
    reglado: bool = False,
    radio: float | None = None,
) -> Any:
    """Loft entre `x_ini` y `x_fin`: secciones PCHIP de `nudos` (x, y_arriba, y_abajo, semiancho).

    Con `reglado`, las secciones son exactamente los nudos y se unen con tramos rectos: sin las ondulaciones que
    da un spline entre secciones casi idénticas (cuerpos estampados, tapas).
    """
    if radio is not None:
        secs = [seccion_x_redondeada(q[0], q[1], q[2], q[3], radio, cz) for q in nudos]
        return Solid.make_loft(secs, ruled=True)
    if reglado:
        return Solid.make_loft([seccion_x(q[0], q[1], q[2], q[3], cz=cz, n=n) for q in nudos], ruled=True)
    xs = [q[0] for q in nudos]
    secciones = []
    for i in range(pasos + 1):
        x = x_ini + (x_fin - x_ini) * i / pasos
        arriba, abajo, ancho = (interpolar(xs, [q[j] for q in nudos], x) for j in (1, 2, 3))
        secciones.append(seccion_x(x, arriba, abajo, ancho, cz=cz, n=n))
    return loftear(secciones)


def seccion_curva(
    centro: tuple[float, float],
    tangente: tuple[float, float],
    semi_n: float,
    semiancho_z: float,
    *,
    n: float = 4.0,
    k: int = PUNTOS_SECCION,
) -> Wire:
    """Sección perpendicular a una espina en el plano XY: `semi_n` en la normal del plano y `semiancho_z` en Z."""
    tx, ty = tangente
    nx, ny = ty, -tx  # normal del plano XY perpendicular a la tangente
    pts = []
    for i in range(k):
        t = 2 * math.pi * i / k
        a, b = semi_n * _potencia(math.cos(t), n), semiancho_z * _potencia(math.sin(t), n)
        pts.append((centro[0] + a * nx, centro[1] + a * ny, b))
    return Wire([Spline(*pts, periodic=True)])


def cilindro_x(radio: float, x0: float, x1: float, y: float = 0.0, z: float = 0.0) -> Any:
    """Cilindro con el eje paralelo a X entre `x0` y `x1`."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(radio, x1 - x0)


def cilindro_z(radio: float, largo: float, x: float, y: float, z: float = 0.0) -> Any:
    """Cilindro con el eje paralelo a Z centrado en (x, y, z)."""
    return Pos(x, y, z) * Cylinder(radio, largo)


def cilindro_y(radio: float, largo: float, x: float, y: float, z: float = 0.0) -> Any:
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radio, largo)


def caja_redonda(
    x0: float, x1: float, y0: float, y1: float, z0: float, z1: float, radio: float, *, ejes: str = "z"
) -> Any:
    """Caja con las aristas del eje `ejes` redondeadas con `radio` (para bolsillos y ranuras con esquinas suaves)."""
    caja = Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
    if radio <= 0:
        return caja
    eje = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[ejes]
    aristas = [
        e
        for e in caja.edges()
        if abs((e.end_point() - e.start_point()).X) * (eje[0] == 0) < 1e-6
        and abs((e.end_point() - e.start_point()).Y) * (eje[1] == 0) < 1e-6
        and abs((e.end_point() - e.start_point()).Z) * (eje[2] == 0) < 1e-6
    ]
    return filetear(caja, radio, aristas)


def remache(x: float, y: float, z: float, lado: int, radio: float = 2.4) -> Any:
    """Cabeza de remache abombada sobre una cara lateral (`lado` = ±1 en Z): casquete esférico + cuello."""
    from build123d import Sphere

    cabeza = Sphere(radio) - Pos(0, 0, -radio * 0.9) * Box(radio * 4, radio * 4, radio * 1.8)
    giro = Rot(0, 0, 0) if lado > 0 else Rot(180, 0, 0)
    return Pos(x, y, z) * giro * cabeza


def aristas_paralelas(solido: Any, eje: str) -> list[Edge]:
    """Aristas rectas paralelas al eje X, Y o Z."""
    v = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[eje]
    salida = []
    for e in solido.edges():
        d = e.end_point() - e.start_point()
        largo = math.sqrt(d.X**2 + d.Y**2 + d.Z**2)
        if largo > 1e-6 and abs(abs(d.X * v[0] + d.Y * v[1] + d.Z * v[2]) / largo - 1.0) < 1e-6:
            salida.append(e)
    return salida


def plano_en_x(x: float) -> Plane:
    return Plane(origin=(x, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
