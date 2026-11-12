"""Familia: sección de raíl Picatinny (MIL-STD-1913) de N ranuras.

Origen: extremo trasero del raíl, sobre su base y centrado. El raíl avanza hacia +X; la cara superior mira a +Y.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Align, Box, Plane, Polygon, Pos, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.ficha import Confianza, Cota

NOTA_PERFIL = (
    "Perfil simplificado bajo las superficies de apoyo: el cuello tiene el ancho del plano superior y el canto "
    "es una arista viva (ancho del cuello y altura del canto sin verificar)."
)


def longitud_rail_mm(ranuras: int) -> float:
    """Longitud de N ranuras al paso del estándar, con un diente completo en cada extremo (cota derivada)."""
    paso, ranura = e.PICATINNY_PASO.valor_mm, e.PICATINNY_ANCHO_RANURA.valor_mm
    return round(ranuras * paso + (paso - ranura), 4)


def centros_ranuras_mm(ranuras: int) -> list[float]:
    """Posición X del centro de cada ranura, desde el extremo trasero."""
    paso, ranura = e.PICATINNY_PASO.valor_mm, e.PICATINNY_ANCHO_RANURA.valor_mm
    return [round((paso - ranura) + ranura / 2 + i * paso, 4) for i in range(ranuras)]


def perfil_picatinny(altura_mm: float | None = None) -> Any:
    """Sección del raíl (cara en el plano YZ, base en Y=0): plano superior, apoyos a 45° y cuello recto."""
    alto = e.PICATINNY_ALTURA.valor_mm if altura_mm is None else altura_mm
    ancho, plano = e.PICATINNY_ANCHO.valor_mm, e.PICATINNY_ANCHO_PLANO.valor_mm
    bisel = (ancho - plano) / 2  # a 45°, el bisel mide lo mismo en horizontal y en vertical
    puntos = [
        (0.0, -plano / 2),
        (alto - 2 * bisel, -plano / 2),
        (alto - bisel, -ancho / 2),
        (alto, -plano / 2),
        (alto, plano / 2),
        (alto - bisel, ancho / 2),
        (alto - 2 * bisel, plano / 2),
        (0.0, plano / 2),
    ]
    # Plane.YZ: X local = Y global (altura), Y local = Z global (lateral); la normal es +X.
    return Plane.YZ * Polygon(*puntos, align=None)


def solido_rail(ranuras: int, altura_mm: float | None = None, longitud_mm: float | None = None) -> Any:
    """Raíl de N ranuras con el origen en su extremo trasero y la base en Y=0.

    Con `longitud_mm`, el perfil llega hasta esa longitud (el tramo que sobra tras la última ranura queda
    como un diente más largo), para que el raíl de un guardamanos acabe a ras de su extremo.
    """
    alto = e.PICATINNY_ALTURA.valor_mm if altura_mm is None else altura_mm
    cuerpo = extrude(perfil_picatinny(alto), longitud_rail_mm(ranuras) if longitud_mm is None else longitud_mm)
    ancho_r, prof = e.PICATINNY_ANCHO_RANURA.valor_mm, e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm
    corte = Box(ancho_r, prof + 1, e.PICATINNY_ANCHO.valor_mm + 2, align=(Align.CENTER, Align.MIN, Align.CENTER))
    return cuerpo - [Pos(x, alto - prof, 0) * corte for x in centros_ranuras_mm(ranuras)]


class RailPicatinny(Familia):
    id = "rail.picatinny"
    version = 2  # v2: los sockets llevan orientación
    nombre = "Raíl Picatinny"
    requiere = ("mlok",)
    ofrece = ("picatinny",)
    estandares = e.PICATINNY
    parametros = (Parametro("ranuras", "Número de ranuras transversales", int, "ud", minimo=2, maximo=60),)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Raíl Picatinny de {p['ranuras']} ranuras"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        n = int(p["ranuras"])
        largo = longitud_rail_mm(n)
        socket = Socket(
            "rail.top",
            (0.0, e.PICATINNY_ALTURA.valor_mm, 0.0),
            "picatinny",
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
            {"longitud_mm": largo, "paso_mm": e.PICATINNY_PASO.valor_mm, "ranuras": n},
        )
        derivada = Cota(
            "longitud", largo, "derivada: N x paso + un diente (paso - ancho de ranura)", e.FECHA, Confianza.MEDIA
        )
        nominales = (largo, e.PICATINNY_ALTURA.valor_mm, e.PICATINNY_ANCHO.valor_mm)
        return Geometria(solido_rail(n), (socket,), (derivada,), (NOTA_PERFIL,), nominales, vaciados=n)
