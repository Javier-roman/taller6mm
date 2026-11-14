"""Familia: empuñadura de pistola (pistolete) del AR-15/M4 de airsoft, estilo A2, MOE o ergonómico.

Origen: centro de la cara de montaje (donde el pistolete toca el receptor inferior). El pistolete cuelga hacia -Y y se
inclina hacia atrás (-X). Alto, profundidad, ancho e inclinación son cotas del SKU: sin ellas, la pieza sale T0 y sin
malla. Las ranuras de los dedos, el repecho y la panza trasera son simplificaciones de silueta, no cotas medidas. El
interior (compartimento, tornillo y cuello de unión) no se modela: es macizo.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from build123d import Box, Pos

from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import caja_de, mm, prisma

INTERFAZ_MONTAJE = "montaje-pistolete-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
PERFILES = ("a2", "moe", "ergo")
# Rasgos de silueta por perfil: (ranuras de dedos, hondo de ranura mm, panza trasera mm, repecho mm, repisa del pulgar)
_RASGOS = {
    "a2": (3, 2.0, 3.0, 4.0, False),
    "moe": (0, 0.0, 5.0, 0.0, False),
    "ergo": (3, 2.5, 6.0, 0.0, True),
}
_MUESTRAS = 24


def _perfil(p: Mapping[str, Valor]) -> list[tuple[float, float]]:
    alto, prof = float(p["altura"]), float(p["profundidad"])
    desplaza = alto * math.tan(math.radians(float(p["inclinacion"])))
    ranuras, hondo, panza, repecho, _ = _RASGOS[str(p["perfil"])]
    estrecha = 0.08 * prof  # el pistolete se afina hacia abajo

    def delantero(u: float) -> float:
        x = prof / 2 - desplaza * u - estrecha * u
        for k in range(ranuras):
            centro = 0.28 + 0.2 * k
            x += hondo * max(0.0, 1.0 - abs(u - centro) / 0.07)  # ranura triangular
        return x

    def trasero(u: float) -> float:
        x = -prof / 2 - desplaza * u
        if 0.12 <= u <= 0.88:
            x -= panza * math.sin(math.pi * (u - 0.12) / 0.76)
        return x

    us = [i / _MUESTRAS for i in range(_MUESTRAS + 1)]
    trasera = [(round(trasero(u), 4), round(-u * alto, 4)) for u in us]
    frontal = [(round(delantero(u), 4), round(-u * alto, 4)) for u in reversed(us)]
    if repecho:  # repisa del dedo meñique, abajo y hacia delante
        y0 = -0.86 * alto
        frontal = [(x + repecho, y) if y <= y0 else (x, y) for x, y in frontal]
    return [*trasera, *frontal]


class EmpunaduraPistolete(Familia):
    id = "empunadura.pistolete"
    nombre = "Pistolete AR"
    requiere = (INTERFAZ_MONTAJE,)
    ofrece = ()
    material = "mat.polimero_negro"
    parametros = (
        Parametro(
            "altura", "Altura del pistolete (de la cara de montaje a la base)", float, "mm", 60, 140, de_sku=True
        ),
        Parametro("profundidad", "Profundidad delante-detrás en la cara de montaje", float, "mm", 20, 60, de_sku=True),
        Parametro("ancho", "Ancho lateral máximo del cuerpo", float, "mm", 20, 50, de_sku=True),
        Parametro(
            "inclinacion", "Inclinación hacia atrás respecto a la vertical", float, "grados", 10, 40, de_sku=True
        ),
        Parametro("perfil", "Estilo de silueta", str, opciones=PERFILES, por_defecto="a2"),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Pistolete AR {str(p['perfil']).upper()} de {mm(p, 'altura')} de alto y {mm(p, 'ancho')} de ancho"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        ancho, perfil, alto = float(p["ancho"]), str(p["perfil"]), float(p["altura"])
        puntos = _perfil(p)
        cuerpo = prisma(puntos, ancho)
        ancho_total = ancho
        notas = [
            "Silueta de ranuras de los dedos, repecho y panza trasera simplificada y de proporciones estimadas.",
            "El interior (compartimento, tornillo, cuello de unión al receptor) no se modela: es macizo.",
        ]
        if _RASGOS[perfil][4]:  # repisa del pulgar a cada lado (estilo ergonómico)
            x_ref = next(x for x, y in puntos if y <= -0.18 * alto)
            repisa = Box(16.0, 12.0, 3.0)
            for lado in (1, -1):
                cuerpo = cuerpo + Pos(x_ref + 10.0, -0.18 * alto, lado * (ancho / 2 + 1.0)) * repisa
            ancho_total = ancho + 4.0
            notas.append("Repisa del pulgar (16 x 12 x 3 mm) estimada, sin cota de ningún SKU.")
        x0, x1, y0, y1 = caja_de(puntos)
        socket = Socket(
            "montaje-pistolete", (0.0, 0.0, 0.0), INTERFAZ_MONTAJE, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {"perfil": perfil}
        )
        return Geometria(
            cuerpo, (socket,), (), tuple(notas), (x1 - x0, y1 - y0, ancho_total), vaciados=_RASGOS[perfil][0]
        )
