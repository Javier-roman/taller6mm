"""Familia: guardamanos tubular con ranuras M-LOK y raíl Picatinny superior opcional.

Origen: centro de la cara trasera, sobre el eje del cañón. El guardamanos avanza hacia +X. Las ranuras M-LOK
van centradas a lo largo, en las caras izquierda (+Z), derecha (-Z) e inferior (-Y); sin raíl superior,
también en la cara superior (+Y). Longitud, diámetro y pared son cotas del SKU: sin ellas, la pieza sale T0.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Circle, Plane, Pos, RectangleRounded, RegularPolygon, Rot, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.rail_picatinny import NOTA_PERFIL, longitud_rail_mm, solido_rail

MARGEN_EXTREMO_MM = e.MLOK_SEPARACION.valor_mm  # material mínimo entre la última ranura y el borde
# Giro alrededor de X que lleva el eje +Z (el de extrusión de la ranura) a la normal de cada cara.
_CARAS = {"side.l": 0.0, "side.r": 180.0, "bottom": 90.0, "top": -90.0}
_NORMALES = {"side.l": (0, 0, 1), "side.r": (0, 0, -1), "bottom": (0, -1, 0), "top": (0, 1, 0)}


def longitud_ocupada_mlok_mm(ranuras: int) -> float:
    """Tramo que ocupan N ranuras M-LOK seguidas (N x 32 mm + (N - 1) x 8 mm)."""
    return ranuras * e.MLOK_PASO_MM - e.MLOK_SEPARACION.valor_mm


def centros_mlok_mm(longitud_mm: float, ranuras: int) -> list[float]:
    """Posición X del centro de cada ranura, con el conjunto centrado en la longitud."""
    inicio = (longitud_mm - longitud_ocupada_mlok_mm(ranuras)) / 2 + e.MLOK_LARGO_RANURA.valor_mm / 2
    return [round(inicio + i * e.MLOK_PASO_MM, 4) for i in range(ranuras)]


def ranuras_rail_que_caben(longitud_mm: float) -> int:
    paso, ranura = e.PICATINNY_PASO.valor_mm, e.PICATINNY_ANCHO_RANURA.valor_mm
    return int((longitud_mm - (paso - ranura) + 1e-6) // paso)


class GuardamanosMlok(Familia):
    id = "guardamanos.mlok"
    version = 2  # v2: el raíl superior llega a ras del extremo y los sockets llevan orientación
    nombre = "Guardamanos M-LOK"
    requiere = ("guardamanos.ar15",)
    ofrece = ("mlok", "picatinny")
    estandares = (*e.MLOK, *e.PICATINNY)
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", minimo=100, maximo=450, de_sku=True),
        Parametro(
            "diametro_exterior", "Diámetro exterior (entre caras si es octogonal)", float, "mm", 30, 60, de_sku=True
        ),
        Parametro("grosor_pared", "Grosor de la pared", float, "mm", minimo=1.5, maximo=5, de_sku=True),
        Parametro("seccion", "Forma de la sección", str, opciones=("redonda", "octogonal"), por_defecto="redonda"),
        Parametro("ranuras_mlok", "Ranuras M-LOK por cara", int, "ud", minimo=1, maximo=10),
        Parametro("rail_superior", "Raíl Picatinny superior a todo lo largo", bool, por_defecto=True),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if p["longitud"] is None:
            return
        necesario = longitud_ocupada_mlok_mm(int(p["ranuras_mlok"])) + 2 * MARGEN_EXTREMO_MM
        if necesario > float(p["longitud"]):
            raise ParametroInvalidoError(
                f"ranuras_mlok: {p['ranuras_mlok']} ranuras piden {necesario:.0f} mm y hay {p['longitud']} mm"
            )

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        rail = "con raíl superior" if p["rail_superior"] else "sin raíl superior"
        return f"Guardamanos M-LOK {p['seccion']} de {largo}, {p['ranuras_mlok']} ranuras por cara, {rail}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, radio, pared = float(p["longitud"]), float(p["diametro_exterior"]) / 2, float(p["grosor_pared"])
        n_mlok, con_rail = int(p["ranuras_mlok"]), bool(p["rail_superior"])

        if p["seccion"] == "octogonal":
            exterior: Any = RegularPolygon(radio, 8, major_radius=False, rotation=22.5)
            interior: Any = RegularPolygon(radio - pared, 8, major_radius=False, rotation=22.5)
        else:
            exterior, interior = Circle(radio), Circle(radio - pared)
        cuerpo = extrude(Plane.YZ * (exterior - interior), largo)

        sockets: list[Socket] = []
        notas = ["La unión al receptor (tuerca de cañón) no se modela: depende del SKU."]
        caras = ["side.l", "side.r", "bottom"]
        if con_rail:
            n_rail = ranuras_rail_que_caben(largo)
            # El raíl se apoya en la tangente superior del tubo; su cuello baja hasta la mitad de la pared.
            y_base = math.sqrt((radio - pared / 2) ** 2 - (e.PICATINNY_ANCHO_PLANO.valor_mm / 2) ** 2)
            y_alto = radio + e.PICATINNY_ALTURA.valor_mm
            cuerpo = cuerpo + Pos(0, y_base, 0) * solido_rail(n_rail, y_alto - y_base, largo)
            sockets.append(
                Socket(
                    "rail.top",
                    (0.0, round(y_alto, 4), 0.0),
                    "picatinny",
                    (0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0),
                    {
                        "longitud_mm": longitud_rail_mm(n_rail),
                        "paso_mm": e.PICATINNY_PASO.valor_mm,
                        "ranuras": n_rail,
                    },
                )
            )
            notas.append(NOTA_PERFIL)
        else:
            caras.append("top")

        ranura = extrude(
            RectangleRounded(e.MLOK_LARGO_RANURA.valor_mm, e.MLOK_ANCHO_RANURA.valor_mm, e.MLOK_RADIO_ESQUINA.valor_mm),
            radio + 1,
        )
        centros = centros_mlok_mm(largo, n_mlok)
        cuerpo = cuerpo - [Pos(x, 0, 0) * Rot(_CARAS[c], 0, 0) * ranura for c in caras for x in centros]
        for cara in caras:
            nx, ny, nz = _NORMALES[cara]
            for i, x in enumerate(centros, start=1):
                sockets.append(
                    Socket(
                        f"mlok.{cara}.{i}",
                        (x, ny * radio, nz * radio),
                        "mlok",
                        (float(nx), float(ny), float(nz)),
                        (1.0, 0.0, 0.0),
                        {"largo_ranura_mm": e.MLOK_LARGO_RANURA.valor_mm},
                    )
                )
        alto = 2 * radio + (e.PICATINNY_ALTURA.valor_mm if con_rail else 0.0)
        vaciados = 1 + len(caras) * n_mlok  # el hueco del cañón y las ranuras M-LOK
        return Geometria(cuerpo, tuple(sockets), (), tuple(notas), (largo, alto, 2 * radio), vaciados)
