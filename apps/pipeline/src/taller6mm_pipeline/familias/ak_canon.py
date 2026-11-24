"""Familia AK de airsoft: cañón con bloque de gas y mira, freno de boca / apagallamas, mira trasera y riel lateral.

Ejes canónicos: +X boca, +Y arriba, +Z izquierda del tirador. Solo formas exteriores; proporciones estimadas
(confianza baja): son piezas `es_demo`, T0 y no publicables. Sin marcajes ni logos.

- Cañón: origen en el centro de la cara por la que sale del receptor; avanza hacia +X.
- Freno de boca: origen en el centro de su cara trasera (la de la rosca) y avanza hacia +X.
- Mira trasera: origen en el centro de la base, sobre su cara de apoyo (Y = 0); avanza hacia +X.
- Riel lateral: origen en el borde trasero de la placa, sobre su cara de apoyo (Z = 0); la placa sube hacia +Y.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Axis, Box, Plane, Polygon, Pos, Rot, extrude, revolve

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.ak_formas import (
    caja_redonda,
    cilindro_x,
    cilindro_y,
    cilindro_z,
    estimada,
    loft_x,
)
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm, prisma
from taller6mm_pipeline.familias.detalle import nominales_de
from taller6mm_pipeline.familias.formas import filetear

INT_CANON = "montaje-canon-ak"
INT_GUARDAMANOS = "montaje-guardamanos-ak"
INT_MIRA_TRASERA = "montaje-mira-trasera-ak"
INT_RIEL_LATERAL = "montaje-riel-lateral-ak"
INT_COLA_MILANO = "rail-11mm-cola-milano"
Y_TUBO_GAS = 14.5


def _rev_x(puntos: list[tuple[float, float]]) -> Any:
    """Sólido de revolución alrededor de X a partir de un perfil (x, radio)."""
    return revolve(Plane.XY * Polygon(*puntos, align=None), axis=Axis.X)


class CanonAK(Familia):
    id = "ak.canon"
    nombre = "Cañón AK con bloque de gas y mira"
    material = "mat.acero_negro"
    requiere = (INT_CANON,)
    ofrece = (INT_GUARDAMANOS, e.ROSCAS_BOCA["14mm_ccw"])
    estandares = e.ROSCA_14
    parametros = (
        Parametro(
            "longitud", "Longitud visible, de la cara del receptor a la boca", float, "mm", 150, 480, de_sku=True
        ),
        Parametro("diametro", "Diámetro del cañón en el tramo del gas", float, "mm", 12, 20, de_sku=True),
        Parametro("longitud_rosca", "Tramo roscado de la boca", float, "mm", 8, 30, de_sku=True, critico=False),
        Parametro("mira", "Protección del punto de mira", str, opciones=("capucha", "orejas"), por_defecto="capucha"),
        Parametro(
            "fraccion_gas",
            "Posición del bloque de gas (fracción de la longitud)",
            float,
            "",
            0.4,
            0.8,
            por_defecto=0.62,
        ),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cañón AK de {mm(p, 'longitud')} con mira de {p['mira']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r = float(p["longitud"]), float(p["diametro"]) / 2
        lr = 14.0 if p["longitud_rosca"] is None else float(p["longitud_rosca"])
        rr = e.ROSCA_14_DIAMETRO.valor_mm / 2
        x_gas = largo * float(p["fraccion_gas"])
        x_mira = largo - lr - 24.0
        perfil = [
            (0, 0),
            (0, r + 1.2),  # el collar trasero (Ø18,4) cabe en el canal del guardamanos (Ø18,6)
            (2.0, r + 1.2),
            (2.0, r),
            (x_mira, r),
            (x_mira, r - 0.8),
            (largo - lr, r - 0.8),
            (largo - lr, rr + 0.8),
            (largo - 0.5, rr + 0.8),
            (largo, rr + 0.3),
            (largo, 0),
        ]
        cuerpo = _rev_x(perfil)
        vaciados = 0
        # Bloque de gas con su alojamiento superior y el tubo de gas hasta el receptor.
        cuerpo = cuerpo + cilindro_x(r + 3.4, x_gas, x_gas + 26)
        cuerpo = cuerpo + caja_redonda(x_gas, x_gas + 26, r, Y_TUBO_GAS + 6.5, -7.5, 7.5, 4.0, ejes="x")
        cuerpo = cuerpo + cilindro_x(6.8, 22, x_gas + 12, Y_TUBO_GAS)
        cuerpo = cuerpo + cilindro_z(1.9, 4.0, x_gas + 13, -r - 1.0, 0)
        # Varilla de limpieza bajo el cañón, entre el bloque de gas y la base de la mira.
        cuerpo = cuerpo + cilindro_x(2.9, x_gas + 20, x_mira + 6, -r - 3.0)
        # Base del punto de mira: collar, torre, protección y poste.
        cuerpo = cuerpo + cilindro_x(r + 3.0, x_mira, x_mira + 22)
        cuerpo = cuerpo + caja_redonda(x_mira + 2, x_mira + 20, r, 25.0, -5.5, 5.5, 2.5, ejes="x")
        if p["mira"] == "capucha":
            anillo = cilindro_x(8.6, x_mira + 3, x_mira + 17, 27.0) - cilindro_x(6.7, x_mira + 2, x_mira + 18, 27.0)
            cuerpo = cuerpo + anillo - caja_redonda(x_mira + 6, x_mira + 14, 31, 40, -1.1, 1.1, 0.0)
            vaciados += 2
        else:
            for lado in (1, -1):
                cuerpo = cuerpo + caja_redonda(x_mira + 4, x_mira + 18, 20.0, 33.0, lado * 7 - 1.1, lado * 7 + 1.1, 1.0)
            vaciados += 2
        cuerpo = cuerpo + cilindro_y(1.5, 12.0, x_mira + 11, 29.0)
        # Tetón de la bayoneta con su orificio, bajo la base de la mira.
        cuerpo = cuerpo + caja_redonda(x_mira + 4, x_mira + 15, -r - 12.0, -r, -4.2, 4.2, 2.2, ejes="z")
        cuerpo = cuerpo - cilindro_z(2.2, 12.0, x_mira + 9.5, -r - 8.0)
        vaciados += 3
        # Garganta de la rosca de la boca (queda entre el cañón y el tramo roscado).
        cuerpo = cuerpo - (
            cilindro_x(r + 1, largo - lr - 1.5, largo - lr) - cilindro_x(rr + 0.8, largo - lr - 1.5, largo - lr)
        )
        vaciados += 1
        sockets = (
            Socket(
                "muzzle",
                (largo, 0.0, 0.0),
                e.ROSCAS_BOCA["14mm_ccw"],
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {"diametro_rosca_mm": rr * 2},
            ),
            Socket("receiver", (0.0, 0.0, 0.0), INT_CANON, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
            Socket("handguard", (0.0, 0.0, 0.0), INT_GUARDAMANOS, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
            Socket(
                "gas_block", (x_gas + 13, r + 3.4, 0.0), "montaje-bloque-gas-ak", (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}
            ),
            # Mira trasera: se apoya sobre el tubo de gas, justo delante del receptor (antes no tenía padre).
            Socket(
                "rear_sight",
                (28.0 + 0.12 * largo, Y_TUBO_GAS + 6.8, 0.0),
                INT_MIRA_TRASERA,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {},
            ),
            Socket(
                "front_sight",
                (x_mira + 11, 40.0, 0.0),
                "montaje-punto-de-mira-ak",
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {},
            ),
        )
        cotas = (estimada("canon.x_bloque_gas", x_gas), estimada("canon.x_base_mira", x_mira))
        notas = (
            "Solo forma exterior: el cañón interior de precisión y el conducto de gas no se modelan.",
            "La rosca de boca es un cilindro liso de 14 mm nominales (la hélice no se modela).",
            "Posición del bloque de gas, perfil y proporciones de la mira estimados (confianza baja).",
        )
        return Geometria(cuerpo, sockets, cotas, notas, nominales_de(cuerpo), vaciados=vaciados)


TIPOS_BOCA = ("oblicuo", "dos_camaras", "embudo", "ranurado")


class FrenoBocaAK(Familia):
    id = "ak.boca"
    tolerancia_mm = 0.02  # pieza pequeña: teselado más fino
    tolerancia_angular = 0.2
    nombre = "Freno de boca / apagallamas AK"
    material = "mat.acero_negro"
    requiere = (e.ROSCAS_BOCA["14mm_ccw"],)
    ofrece = ()
    estandares = e.ROSCA_14
    parametros = (
        Parametro("tipo", "Forma del freno o apagallamas", str, opciones=TIPOS_BOCA, por_defecto="oblicuo"),
        Parametro("longitud", "Longitud total", float, "mm", 24, 80, de_sku=True),
        Parametro("diametro", "Diámetro exterior máximo", float, "mm", 17, 28, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Boca AK {p['tipo']} de {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r, tipo = float(p["longitud"]), float(p["diametro"]) / 2, str(p["tipo"])
        rr = e.ROSCA_14_DIAMETRO.valor_mm / 2
        vaciados = 0
        if tipo == "embudo":
            cuerpo = _rev_x(
                [(0, 0), (0, rr + 1.2), (largo * 0.25, rr + 1.2), (largo * 0.9, r), (largo, r - 0.6), (largo, 0)]
            )
            for giro in (0, 90):
                cuerpo = cuerpo - Rot(giro, 0, 0) * caja_redonda(
                    largo * 0.55, largo + 1, -1.7, 1.7, -r - 2, r + 2, 0.8, ejes="x"
                )
                vaciados += 1
            salida = 3.6
        elif tipo == "ranurado":
            cuerpo = _rev_x([(0, 0), (0, r - 0.6), (1.0, r), (largo - 1.0, r), (largo, r - 0.8), (largo, 0)])
            for giro in (0, 60, 120):
                cuerpo = cuerpo - Rot(giro, 0, 0) * caja_redonda(
                    largo * 0.42, largo + 1, -1.6, 1.6, -r - 2, r + 2, 0.8, ejes="x"
                )
                vaciados += 1
            salida = 4.5
        elif tipo == "dos_camaras":
            cuerpo = _rev_x([(0, 0), (0, r - 1.0), (1.0, r), (largo - 1.0, r), (largo, r - 1.0), (largo, 0)])
            cuerpo = cuerpo - (
                cilindro_x(r + 1, largo * 0.30, largo * 0.36) - cilindro_x(r - 2.0, largo * 0.30, largo * 0.36)
            )
            for x in (largo * 0.5, largo * 0.72):
                cuerpo = cuerpo - caja_redonda(x, x + largo * 0.14, -r - 1, r + 1, -3.0, 3.0, 1.2, ejes="y")
                vaciados += 1
            for x in (largo * 0.12, largo * 0.20):
                cuerpo = cuerpo - cilindro_y(2.2, 2 * r + 2, x, 0)
                vaciados += 1
            salida = 4.2
        else:  # oblicuo
            cuerpo = _rev_x([(0, 0), (0, r - 0.8), (1.0, r), (largo - 1.0, r), (largo, r - 0.8), (largo, 0)])
            corte = Pos(largo, r + 1.0, 0) * Rot(0, 0, -38) * Box(largo * 0.5, 3 * r, 3 * r)
            cuerpo = cuerpo - corte
            cuerpo = cuerpo - caja_redonda(largo * 0.45, largo * 0.85, r - 4.5, r + 1, -3.4, 3.4, 1.4, ejes="y")
            vaciados += 2
            salida = 3.8
        cuerpo = cuerpo - cilindro_x(rr, -1, largo * 0.4)  # alojamiento de la rosca
        cuerpo = cuerpo - cilindro_x(salida, largo * 0.3, largo + 1)  # paso del proyectil
        vaciados += 2
        sockets = (
            Socket(
                "muzzle_mount",
                (0.0, 0.0, 0.0),
                e.ROSCAS_BOCA["14mm_ccw"],
                (-1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {"diametro_rosca_mm": rr * 2},
            ),
        )
        notas = (
            "Solo forma exterior: la rosca es un alojamiento liso de 14 mm nominales y no se modela el interior real.",
            "Lumbreras, cámaras y corte oblicuo estimados (confianza baja).",
        )
        return Geometria(
            cuerpo, sockets, (estimada("boca.largo", largo),), notas, nominales_de(cuerpo), vaciados=vaciados
        )


class MiraTraseraAK(Familia):
    id = "ak.mira_trasera"
    tolerancia_mm = 0.02  # pieza pequeña: teselado más fino
    tolerancia_angular = 0.2
    nombre = "Mira trasera de tangente AK"
    material = "mat.acero_negro"
    requiere = (INT_MIRA_TRASERA,)
    ofrece = ()
    parametros = (
        Parametro("longitud", "Longitud de la base", float, "mm", 40, 100, de_sku=True),
        Parametro("ancho", "Ancho de la base", float, "mm", 16, 34, de_sku=True),
        Parametro("alto", "Alto de la hoja sobre la base", float, "mm", 14, 40, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Mira trasera AK de {mm(p, 'longitud')} de base"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, ancho, alto = float(p["longitud"]), float(p["ancho"]), float(p["alto"])
        hw = ancho / 2
        base = loft_x(
            0, largo, [(0, 7.0, 0.0, hw), (largo * 0.5, 7.0, 0.0, hw), (largo, 7.0, 0.0, hw * 0.92)], radio=3.0
        )
        # Hoja inclinada de la tangente, con sus marcas de graduación.
        x0, x1 = largo * 0.12, largo * 0.88
        y_alto = 7.0 + alto
        hoja = prisma([(x0, 6.0), (x1, 6.0), (x1, 7.0 + alto * 0.3), (x0, y_alto)], ancho * 0.62)
        cuerpo = base + hoja
        pendiente = math.degrees(math.atan2(y_alto - (7.0 + alto * 0.3), x0 - x1))
        vaciados = 1
        for i in range(8):
            x = x0 + (i + 0.7) * (x1 - x0) / 9
            y = y_alto + (7.0 + alto * 0.3 - y_alto) * (x - x0) / (x1 - x0)
            marca = Pos(x, y, 0) * Rot(0, 0, pendiente) * Box(0.7, 1.4, ancho * 0.62 * (0.5 if i % 2 else 0.8))
            cuerpo = cuerpo - marca
            vaciados += 1
        # Cursor: anillo que abraza la hoja, con la muesca en U.
        xc = (x0 + x1) / 2
        yc = y_alto + (7.0 + alto * 0.3 - y_alto) * (xc - x0) / (x1 - x0)
        cursor = caja_redonda(xc - 5, xc + 5, yc - 3.5, yc + 4.5, -hw * 0.62 - 2.2, hw * 0.62 + 2.2, 1.5, ejes="y")
        cuerpo = cuerpo + cursor - caja_redonda(xc - 6, xc + 6, yc + 1.6, yc + 6, -2.0, 2.0, 1.0, ejes="x")
        # Dos tornillos de la base.
        for lado in (1, -1):
            cuerpo = cuerpo + cilindro_y(2.2, 1.6, largo * 0.15, 7.0, lado * hw * 0.62)
        vaciados += 3
        cuerpo = filetear(cuerpo, 0.6)
        socket = Socket("base", (largo / 2, 0.0, 0.0), INT_MIRA_TRASERA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {})
        notas = (
            "Solo forma exterior: el muelle, el tornillo de deriva y los números de la escala no se modelan.",
            "Pendiente de la hoja, cursor y marcas estimados (confianza baja).",
        )
        return Geometria(
            cuerpo, (socket,), (estimada("mira.alto_hoja", alto),), notas, nominales_de(cuerpo), vaciados=vaciados
        )


class RielLateralAK(Familia):
    id = "ak.riel_lateral"
    nombre = "Riel lateral AK para ópticas"
    material = "mat.acero_negro"
    requiere = (INT_RIEL_LATERAL,)
    ofrece = (INT_COLA_MILANO,)
    parametros = (
        Parametro("longitud", "Longitud de la placa", float, "mm", 100, 280, de_sku=True),
        Parametro("alto", "Alto de la placa", float, "mm", 30, 70, de_sku=True),
        Parametro("ranuras", "Ranuras transversales del riel", int, "ud", 0, 12, por_defecto=6),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Riel lateral AK de {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, n = float(p["longitud"]), float(p["alto"]), int(p["ranuras"])
        placa = caja_redonda(0, largo, 0, alto, 0, 4.0, 5.0, ejes="z")
        # Cola de milano: más ancha arriba que abajo, a lo largo de la placa.
        a, b = alto * 0.22, alto * 0.78
        perfil = Plane.YZ * Polygon((a, 4.0), (b, 4.0), (b + 2.4, 11.5), (a - 2.4, 11.5), align=None)
        riel = extrude(perfil, largo - 20.0)
        cuerpo = placa + Pos(10.0, 0, 0) * riel
        vaciados = 1
        paso = (largo - 40.0) / max(n, 1)
        for i in range(n):
            x = 20.0 + (i + 0.5) * paso
            cuerpo = cuerpo - caja_redonda(x - 1.6, x + 1.6, a - 4, b + 4, 8.6, 13, 0.0)
            vaciados += 1
        for x, y in ((6.0, alto * 0.5), (largo - 6.0, alto * 0.5), (largo / 2, alto - 5.0)):
            cuerpo = cuerpo + cilindro_z(2.6, 1.8, x, y, 4.8)
            vaciados += 1
        cuerpo = filetear(cuerpo, 0.5)
        sockets = (
            Socket(
                "receiver_side", (largo / 2, alto / 2, 0.0), INT_RIEL_LATERAL, (0.0, 0.0, -1.0), (1.0, 0.0, 0.0), {}
            ),
            Socket(
                "rail.side",
                (largo / 2, alto / 2, 11.5),
                INT_COLA_MILANO,
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                {"ranuras": n},
            ),
        )
        notas = (
            "Solo forma exterior: la placa es plana y no copia la curvatura del receptor.",
            "Perfil de cola de milano, ranuras y tornillos estimados (confianza baja).",
        )
        return Geometria(
            cuerpo,
            sockets,
            (estimada("riel_lateral.altura_riel", 11.5),),
            notas,
            nominales_de(cuerpo),
            vaciados=vaciados,
        )
