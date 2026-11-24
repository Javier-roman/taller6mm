"""Ópticas de la tanda 3 del M4: red dot tubular, holográfica abierta, mira telescópica con torretas y magnificador.

Ejes: +X boca, +Y arriba, +Z izquierda. Origen: extremo trasero de la base, centrado, con el plano superior del raíl en
y = 0 (la base baja por los flancos del raíl). Las ópticas llevan los tubos huecos con las lentes rehundidas, torretas
con tapa y estrías, y la base con mordazas y bulón. Son carcasas de réplica: no hay óptica funcional. Las proporciones
son estimadas (sin cota de SKU) y por eso no pasan de T1.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Box, Cylinder, Pos

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, loftear, superelipse
from taller6mm_pipeline.familias.tanda3_comun import (
    NOTA_PICATINNY,
    base_sobre_rail,
    cuerpo_tubular,
    estimada,
    estriado,
    lente,
    nominales,
    prisma_redondeado,
    seccion_x,
)

INTERFAZ_HUELLA_RED_DOT = "huella-aimpoint-micro"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
ANILLO = {"25.4": "anillo-optica-25-4mm", "30": "anillo-optica-30mm"}


def _socket_rail(x: float) -> Socket:
    return Socket("rail", (x, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))


def _torreta(x: float, y: float, z: float, radio: float, alto: float, eje: str, lado: int) -> Any:
    """Torreta con tapa estriada y base redondeada; `lado` = signo del eje en el que sobresale."""
    d = {"y": (0, lado * alto / 2, 0), "z": (0, 0, lado * alto / 2)}[eje]
    centro = (x + d[0], y + d[1], z + d[2])
    cuerpo = estriado(eje, centro, radio, alto, 18, 0.45)
    punta = {"y": (0, lado * (alto + 0.8), 0), "z": (0, 0, lado * (alto + 0.8))}[eje]
    tapa = cilindro_en(eje, radio * 0.78, 1.6, (x + punta[0], y + punta[1], z + punta[2]))
    return filetear(cuerpo, 0.3) + tapa


class RedDotTubular(Familia):
    id = "optica.red_dot_tubular"
    nombre = "Red dot tubular"
    material = "mat.anodizado_negro"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("longitud", "Longitud del tubo", float, "mm", 40, 120, de_sku=True),
        Parametro("diametro", "Diámetro del tubo (cuerpo central)", float, "mm", 16, 34, de_sku=True),
        Parametro("altura_eje", "Altura del eje óptico sobre el plano del raíl", float, "mm", 18, 50, de_sku=True),
        Parametro("campana", "Campana del objetivo (más ancha que el tubo)", float, "mm", 1.0, 10.0, de_sku=True),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["diametro"] is not None
            and p["altura_eje"] is not None
            and float(p["altura_eje"]) < float(p["diametro"]) / 2 + 6
        ):
            raise ParametroInvalidoError("altura_eje: debe superar el radio del tubo en 6 mm")

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Red dot tubular de {mm(p, 'longitud')} y tubo de {mm(p, 'diametro')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, D, h, campana = (float(p[k]) for k in ("longitud", "diametro", "altura_eje", "campana"))  # noqa: N806
        r = D / 2
        rc = r + campana / 2  # radio de la campana del objetivo
        # Perfil (x, radio): ocular con aro, cintura con las torretas, campana del objetivo y borde frontal.
        perfil = [
            (0.0, 0.0),
            (0.0, r * 0.90),
            (0.04 * L, r * 0.98),
            (0.14 * L, r * 0.92),
            (0.30 * L, r),
            (0.58 * L, r),
            (0.74 * L, 0.5 * (r + rc)),
            (0.88 * L, rc),
            (0.97 * L, rc),
            (L, rc * 0.93),
            (L, 0.0),
        ]
        tubo = cuerpo_tubular(perfil, h, hueco_trasero=(r * 0.78, 0.16 * L), hueco_delantero=(rc * 0.90, 0.20 * L))
        tubo = tubo + lente(r * 0.78, 0.14 * L, h, 0.0) + lente(rc * 0.90, 0.78 * L, h, 0.0)
        # Torreta de elevación (arriba), de deriva (derecha) y tapa de la pila (izquierda) con ranura.
        torreta_y = _torreta(0.40 * L, h + r * 0.92, 0.0, 0.17 * r + 3.0, 6.0, "y", 1)
        torreta_z = _torreta(0.40 * L, h, -(r * 0.92), 0.17 * r + 3.0, 6.0, "z", -1)
        tapa = cilindro_en("z", 0.27 * r + 2.5, 4.0, (0.62 * L, h, r * 0.92 + 1.6))
        tapa = filetear(tapa, 0.5) - Pos(0.62 * L, h, r * 0.92 + 3.2) * Box(0.5 * r, 1.0, 1.6)
        # Base: plataforma lofteada con mordazas y un soporte curvo que sube hasta el tubo.
        base = base_sobre_rail(0.14 * L, 0.84 * L, h - r * 0.55, min(0.9 * D, 28.0))
        pie = loftear(
            [
                superelipse(h - r * 0.7, 0.49 * L, 0.34 * D, 0.31 * L, n=3.0),
                superelipse(h - r * 0.3, 0.49 * L, 0.25 * D, 0.27 * L, n=2.4),
            ]
        )
        cuerpo = tubo + torreta_y + torreta_z + tapa + base + pie
        notas = (
            "Proporciones, torretas y tapa de la pila estimadas, sin cota de SKU; el interior no se modela.",
            "No hay óptica ni punto luminoso funcional: carcasa de réplica con lentes de cristal planas.",
            NOTA_PICATINNY,
        )
        cotas = (estimada("rd.cuerpo_radio", r), estimada("rd.campana_radio", rc))
        sockets = (
            _socket_rail(0.49 * L),
            Socket("optica", (L, h, 0.0), "optica.eje", (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        )
        return Geometria(cuerpo, sockets, cotas, notas, nominales(cuerpo), vaciados=5)


class HolograficaAbierta(Familia):
    id = "optica.holografica_abierta"
    nombre = "Holográfica abierta"
    material = "mat.polimero_negro"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", 50, 130, de_sku=True),
        Parametro("altura", "Altura sobre el plano del raíl", float, "mm", 35, 80, de_sku=True),
        Parametro("ancho", "Ancho lateral del marco", float, "mm", 28, 60, de_sku=True),
        Parametro("pared", "Grosor del marco alrededor de la ventana", float, "mm", 4, 12, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Holográfica abierta de {mm(p, 'longitud')} y {mm(p, 'altura')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, H, W, t = (float(p[k]) for k in ("longitud", "altura", "ancho", "pared"))  # noqa: N806
        zocalo = 0.24 * H  # bajo la ventana: electrónica y pila
        # Envolvente: loft de secciones redondeadas, más estrecha en los extremos.
        envolvente = loftear(
            [
                seccion_x(0.0, H / 2, 0.48 * H, 0.46 * W, n=3.6),
                seccion_x(0.50 * L, H / 2, 0.50 * H, 0.50 * W, n=4.2),
                seccion_x(L, H / 2, 0.47 * H, 0.45 * W, n=3.8),
            ]
        )
        vh = H - zocalo - t
        ventana = prisma_redondeado(-2.0, L + 2.0, zocalo + vh / 2, vh / 2, W / 2 - t, n=5.0)
        cuerpo = envolvente - ventana
        # Cristal: lámina fina dentro de la ventana, a un tercio del largo.
        cristal = prisma_redondeado(0.44 * L, 0.44 * L + 1.0, zocalo + vh / 2, vh / 2 + 0.6, W / 2 - t + 0.6, n=5.0)
        cuerpo = cuerpo + cristal
        # Capota trasera del emisor, botones laterales, tapa de la pila y palanca de desmontaje.
        capota = loftear(
            [
                seccion_x(0.50 * L, H - 0.4 * t, 0.62 * t, 0.40 * W, n=3.0),
                seccion_x(0.80 * L, H - 0.3 * t, 0.56 * t, 0.36 * W, n=3.0),
                seccion_x(0.96 * L, H - 0.6 * t, 0.40 * t, 0.30 * W, n=3.0),
            ]
        )
        cuerpo = cuerpo + capota
        zl = 0.50 * W + 0.6
        for lado in (1, -1):
            for dx in (0.28, 0.44):
                cuerpo = cuerpo + filetear(cilindro_en("z", 2.8, 2.6, (dx * L, 0.12 * H, lado * zl)), 0.5)
        tapa = filetear(cilindro_en("z", 6.0, 2.8, (0.76 * L, 0.14 * H, zl)), 0.5)
        cuerpo = cuerpo + (tapa - Pos(0.76 * L, 0.14 * H, zl + 1.2) * Box(9.0, 1.0, 1.2))
        # Leva de desmontaje: dos muñones a los lados de las mordazas (antes era una barra de lado a lado que
        # atravesaba el raíl) y la palanca en el lado izquierdo.
        muñones = [filetear(cilindro_en("z", 3.0, 4.0, (0.30 * L, -2.0, lado * 13.0)), 0.5) for lado in (1, -1)]
        palanca = Pos(0.30 * L, -2.0, 0.31 * W + 2.0) * Cylinder(5.0, 4.0)
        cuerpo = cuerpo + muñones[0] + muñones[1] + filetear(palanca, 0.6)
        cuerpo = cuerpo + base_sobre_rail(0.12 * L, 0.88 * L, 0.10 * H, 0.60 * W)
        notas = (
            "Marco, capota del emisor, botones y tapa de la pila estimados, sin cota de SKU; el interior no se modela.",
            "No hay holograma ni retícula: carcasa de réplica con un cristal plano.",
            NOTA_PICATINNY,
        )
        cotas = (estimada("holo.altura_ventana", vh),)
        return Geometria(cuerpo, (_socket_rail(0.50 * L),), cotas, notas, nominales(cuerpo), vaciados=6)
