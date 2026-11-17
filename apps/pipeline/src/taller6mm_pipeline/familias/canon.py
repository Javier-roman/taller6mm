"""Familias de cañón exterior y bloque de gas del M4/AR de airsoft (solo formas exteriores, oleada 1).

Cañón exterior: origen en la cara trasera (la que apoya en el receptor), sobre el eje; avanza hacia +X.
Bloque de gas: origen en el centro de su cara trasera, sobre el eje del cañón que abraza.
Las cotas propias (longitud, diámetros) son del SKU; las proporciones de detalle son estimadas (confianza baja).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Align, Axis, Box, Circle, Cylinder, Plane, Polygon, Pos, extrude, revolve

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.detalle import estimada, nominales_de
from taller6mm_pipeline.familias.rail_picatinny import NOTA_PERFIL, longitud_rail_mm, solido_rail

INTERFAZ_BLOQUE_GAS = "montaje-bloque-gas-ar"  # propuesta del catálogo (ar-m4.json), aún no está en interfaces.json
INTERFAZ_TUERCA = "tuerca-guardamanos-ar"

# Distancia estimada del receptor al bloque de gas por variante (mm). Sin fuente: confianza baja.
GAS_POR_VARIANTE = {"carabina": 190.0, "mid": 240.0, "a2": 300.0, "largo": 360.0}
VARIANTES = tuple(GAS_POR_VARIANTE)
LARGO_BRIDA_MM = 10.0
LARGO_BLOQUE_MM = 24.0


def _cil_x(radio: float, x0: float, x1: float) -> Any:
    return Pos(x0, 0, 0) * extrude(Plane.YZ * Circle(radio), x1 - x0)


def _revolucion(puntos: list[tuple[float, float]]) -> Any:
    """Sólido de revolución alrededor de X a partir de un perfil (x, radio)."""
    return revolve(Plane.XY * Polygon(*puntos, align=None), axis=Axis.X)


class CanonExterior(Familia):
    id = "canon.exterior"
    nombre = "Cañón exterior"
    requiere = ()
    ofrece = (INTERFAZ_BLOQUE_GAS,)
    estandares = e.ROSCA_14
    parametros = (
        Parametro(
            "variante", "Variante de longitud de sistema de gas", str, opciones=VARIANTES, por_defecto="carabina"
        ),
        Parametro("perfil", "Perfil del cañón", str, opciones=("ligero", "pesado"), por_defecto="ligero"),
        Parametro("rosca", "Rosca de boca", str, opciones=tuple(e.ROSCAS_BOCA), por_defecto="14mm_ccw"),
        Parametro("longitud", "Longitud total", float, "mm", minimo=100, maximo=700, de_sku=True),
        Parametro("diametro", "Diámetro del cuerpo (hasta el bloque de gas)", float, "mm", 16, 32, de_sku=True),
        Parametro("diametro_boca", "Diámetro por delante del bloque de gas", float, "mm", 16, 28, de_sku=True),
        Parametro(
            "longitud_rosca", "Longitud del tramo roscado de boca", float, "mm", 8, 30, de_sku=True, critico=False
        ),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        d, db, largo = p["diametro"], p["diametro_boca"], p["longitud"]
        if d is not None and db is not None and float(db) > float(d):
            raise ParametroInvalidoError("diametro_boca: no puede superar el diámetro del cuerpo")
        if db is not None and float(db) <= e.ROSCA_14_DIAMETRO.valor_mm + 1.0:
            raise ParametroInvalidoError("diametro_boca: debe superar la rosca de 14 mm con un resalte mínimo")
        lr = 14.0 if p["longitud_rosca"] is None else float(p["longitud_rosca"])
        if largo is not None and float(largo) < (
            GAS_POR_VARIANTE[str(p["variante"])]
            + LARGO_BLOQUE_MM
            + (27.0 if p["perfil"] == "pesado" else 2.0)
            + lr
            + 3.0
        ):
            raise ParametroInvalidoError(f"longitud: no llega al bloque de gas de la variante {p['variante']}")

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.ROSCAS_BOCA[str(p["rosca"])], INTERFAZ_BLOQUE_GAS)

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Cañón exterior {p['variante']} {p['perfil']} de {largo}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r, rb = float(p["longitud"]), float(p["diametro"]) / 2, float(p["diametro_boca"]) / 2
        lr = 14.0 if p["longitud_rosca"] is None else float(p["longitud_rosca"])
        rr = e.ROSCA_14_DIAMETRO.valor_mm / 2
        x_gas = GAS_POR_VARIANTE[str(p["variante"])]
        x_fin_cuerpo = x_gas + LARGO_BLOQUE_MM
        brida = r + 3.0
        c = 0.6
        r_cuello = r + 1.2  # escalón de la extensión del cañón, tras la brida
        # Perfil (x, radio) de atrás adelante: brida de apoyo, escalón de la extensión, cuerpo, escalón del bloque
        # de gas, hombro de boca, garganta de la rosca y rosca. Todo dentro del polígono: sin booleanas tangentes.
        perfil = [
            (0, 0),
            (0, brida - c),
            (c, brida),
            (LARGO_BRIDA_MM, brida),
            (LARGO_BRIDA_MM, r_cuello),
            (LARGO_BRIDA_MM + 5.0, r_cuello),
            (LARGO_BRIDA_MM + 5.0, r),
            (x_fin_cuerpo, r),
        ]
        if p["perfil"] == "pesado":
            # Hombro cónico por delante del bloque y un segundo escalón corto antes de afinar a la boca.
            r_medio = (r + rb) / 2
            perfil += [(x_fin_cuerpo + 18, r_medio), (x_fin_cuerpo + 18, r_medio - 0.5), (x_fin_cuerpo + 26, rb)]
        else:
            perfil += [(x_fin_cuerpo, rb + 0.6), (x_fin_cuerpo + 1.2, rb)]
        # Hombro de boca, garganta de la rosca y rosca de perfil en V al paso de `estandares` (anillos: sin hélice).
        paso = e.ROSCA_14_PASO.valor_mm
        r_raiz, x_rosca = rr - 0.6, largo - lr
        n_dientes = max(1, int((lr - 1.0) / paso))
        perfil += [(x_rosca - 2.2, rb), (x_rosca - 2.2, r_raiz - 0.3), (x_rosca, r_raiz - 0.3), (x_rosca, r_raiz)]
        for i in range(n_dientes):
            x0 = x_rosca + i * paso
            perfil += [(x0 + 0.5 * paso - 0.06, rr), (x0 + 0.5 * paso + 0.06, rr), (x0 + paso, r_raiz)]
        perfil += [(largo - 0.5, r_raiz), (largo, r_raiz - 0.5), (largo, 0)]
        cuerpo = _revolucion(perfil)
        # Ranuras anulares de retención (a ras del bloque, para que el bloque las tape).
        for x in (x_gas - 3.0, x_gas + LARGO_BLOQUE_MM + 3.0):
            cuerpo = cuerpo - (_cil_x(r + 1, x, x + 1.2) - _cil_x(r - 0.5, x, x + 1.2))
        # Cuello del gas: el orificio del tubo de gas arriba y los dos hoyuelos de los tornillos del bloque.
        cuerpo = cuerpo - Pos(x_gas + LARGO_BLOQUE_MM / 2, 0, 0) * Cylinder(
            0.9, r + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ).rotate(Axis.X, -90)
        for dx in (6.0, LARGO_BLOQUE_MM - 6.0):
            for z in (-1, 1):
                cuerpo = cuerpo - Pos(x_gas + dx, 0, z * (r - 0.1)) * Cylinder(1.5, 1.6)
        sockets = (
            Socket(
                "muzzle",
                (largo, 0.0, 0.0),
                e.ROSCAS_BOCA[str(p["rosca"])],
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {"diametro_rosca_mm": rr * 2},
            ),
            Socket(
                "gas_block",
                (x_gas, r, 0.0),
                INTERFAZ_BLOQUE_GAS,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {"distancia_al_receptor_mm": x_gas},
            ),
            Socket("receiver", (0.0, 0.0, 0.0), INTERFAZ_TUERCA, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
        )
        cotas = (estimada("canon.distancia_bloque_gas", x_gas), estimada("canon.largo_brida", LARGO_BRIDA_MM))
        notas = (
            "Solo forma exterior: el cañón interior de precisión no se modela.",
            "La rosca de boca son anillos en V al paso de 14 x 1 mm (sin hélice), con garganta y hombro.",
            "Escalones de extensión y boca, orificio del gas y hoyuelos del bloque: forma estimada.",
            "Distancia al bloque de gas y proporciones del escalón estimadas (confianza baja).",
        )
        nominales = (largo, 2 * brida, 2 * brida)
        return Geometria(cuerpo, sockets, cotas, notas, nominales, vaciados=3)


class BloqueGas(Familia):
    id = "canon.bloque_gas"
    nombre = "Bloque de gas"
    requiere = (INTERFAZ_BLOQUE_GAS,)
    estandares = ()
    parametros = (
        Parametro("tipo", "Tipo de bloque", str, opciones=("bajo_perfil", "a2_mira", "rail"), por_defecto="a2_mira"),
        Parametro("diametro_canon", "Diámetro del cañón que abraza", float, "mm", 14, 32, de_sku=True),
        Parametro("pared", "Espesor del collar", float, "mm", 2.5, 8, de_sku=True, critico=False),
        Parametro(
            "altura_mira",
            "Altura del poste sobre el collar (tipo a2_mira)",
            float,
            "mm",
            10,
            40,
            de_sku=True,
            critico=False,
        ),
    )

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.INTERFAZ_PICATINNY,) if p["tipo"] == "rail" else ()

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Bloque de gas {p['tipo']} para cañón de Ø{p['diametro_canon'] or 'sin dato'} mm"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        rc = float(p["diametro_canon"]) / 2
        pared = 4.0 if p["pared"] is None else float(p["pared"])
        ro = rc + pared
        largo = LARGO_BLOQUE_MM
        cuerpo = _cil_x(ro, 0, largo)
        # Chaflán de las dos caras del collar.
        cuerpo = cuerpo.chamfer(0.8, None, cuerpo.edges().filter_by(Axis.X, reverse=True))
        sockets: list[Socket] = [
            Socket("bore", (0.0, 0.0, 0.0), INTERFAZ_BLOQUE_GAS, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {})
        ]
        notas = ["Solo forma exterior; el conducto de gas no se modela."]
        if p["tipo"] == "a2_mira":
            alto = 18.0 if p["altura_mira"] is None else float(p["altura_mira"])
            torre = Pos(0, ro - 1.0, 0) * extrude(
                Plane.YZ
                * Polygon((0, -5.5), (alto * 0.55 + 1.0, -3.0), (alto * 0.55 + 1.0, 3.0), (0, 5.5), align=None),
                largo * 0.7,
            )
            poste = Pos(largo * 0.35, ro + alto * 0.55, 0) * Cylinder(
                1.6, alto * 0.45 + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
            ).rotate(Axis.X, -90)
            guarda = [
                Pos(largo * 0.35, ro + alto * 0.55 + 1.0, z)
                * Box(5, alto * 0.45, 1.6, align=(Align.CENTER, Align.MIN, Align.CENTER))
                for z in (-5.0, 5.0)
            ]
            cuerpo = cuerpo + torre + poste + guarda
            # Tetón inferior para la bayoneta (solo su silueta exterior) y dos pasadores laterales.
            cuerpo = cuerpo + Pos(largo * 0.4, -ro - 3.0, 0) * Box(10, 7, 9)
            notas.append("Tetón de bayoneta y poste de la mira simplificados: sin la geometría de sujeción real.")
        elif p["tipo"] == "rail":
            n = max(
                2,
                int(
                    (largo + 8 - (e.PICATINNY_PASO.valor_mm - e.PICATINNY_ANCHO_RANURA.valor_mm))
                    // e.PICATINNY_PASO.valor_mm
                ),
            )
            y0 = math.sqrt(max(ro**2 - (e.PICATINNY_ANCHO_PLANO.valor_mm / 2) ** 2, 1.0)) - 0.5
            cuerpo = cuerpo + Pos(0, y0, 0) * solido_rail(n, e.PICATINNY_ALTURA.valor_mm + 1.5, largo)
            sockets.append(
                Socket(
                    "rail.top",
                    (largo / 2, y0 + e.PICATINNY_ALTURA.valor_mm + 1.5, 0.0),
                    e.INTERFAZ_PICATINNY,
                    (0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0),
                    {"longitud_mm": longitud_rail_mm(n), "ranuras": n},
                )
            )
            notas.append(NOTA_PERFIL)
        else:
            cuerpo = cuerpo + Pos(largo / 2, ro - 0.8, 0) * Box(
                largo * 0.8, 2.0, 2 * ro * 0.5, align=(Align.CENTER, Align.MIN, Align.CENTER)
            )
        # Dos pasadores transversales (cabezas visibles en ambos lados) y tornillo inferior.
        for z in (-1, 1):
            cuerpo = cuerpo + Pos(largo * 0.3, 0, z * (ro - 0.3)) * Cylinder(
                2.2, 1.6, align=(Align.CENTER, Align.CENTER, Align.CENTER)
            )
            cuerpo = cuerpo + Pos(largo * 0.75, 0, z * (ro - 0.3)) * Cylinder(
                2.2, 1.6, align=(Align.CENTER, Align.CENTER, Align.CENTER)
            )
        cuerpo = cuerpo - _cil_x(rc, -1, largo + 1)
        return Geometria(cuerpo, tuple(sockets), (), tuple(notas), nominales_de(cuerpo), vaciados=1)
