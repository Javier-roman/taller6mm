"""Corredera de las pistolas de airsoft (GBB y AEP): origen común de pistola (ver `pistola_comun`).

La corredera es un loft de secciones redondeadas a lo largo de X (con el chaflán delantero y el rebaje trasero), con
el canal inferior hueco por donde entra el armazón, la ventana de eyección con el frente inclinado, el serrado en V
delante y detrás, las colas de milano de las miras y la boca con el alojamiento del muelle guía. Las miras tienen
base en cola de milano, y las regulables, tornillo de deriva. El cañón es de revolución, con el tramo roscado de boca
(14 mm CCW) hecho con anillos (la hélice no se modela) y el capó de la recámara con su rampa.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Box, Plane, Polygon, Pos, Rot, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear
from taller6mm_pipeline.familias.pistola_comun import (
    INTERFAZ_CANON_PISTOLA,
    INTERFAZ_MIRA_PISTOLA,
    INTERFAZ_RIEL_CORREDERA,
    PLANO_CORREDERA_Y,
    estimada,
)
from taller6mm_pipeline.familias.pistola_modelos import cara

ESTILOS = ("polimero", "clasico")
Y_SUP_ESTILO = {"polimero": 18.5, "clasico": 17.0}  # cara superior de la corredera sobre el eje del cañón
MURO = 3.4  # espesor de las paredes laterales de la corredera


def _hueco_x(x0: float, x1: float, y0: float, y1: float, semi: float, radio: float = 2.0) -> Any:
    """Prisma de esquinas redondeadas (perfil XY extruido en Z) para vaciar o cortar."""
    caja = Pos((x0 + x1) / 2, (y0 + y1) / 2, 0) * Box(x1 - x0, y1 - y0, 2 * semi)
    return filetear(
        caja, radio, [a for a in caja.edges() if abs(a.center().X - (x0 + x1) / 2) > 0 and a.length == 2 * semi]
    )


def _v_vertical(x: float, ancho: float, fondo: float, y0: float, y1: float, z_cara: float, lado: int) -> Any:
    """Surco vertical de fondo redondo en una cara lateral (z_cara) de la corredera: sirve de serrado.

    Cilindro vertical de radio `ancho / 2` con el eje `ancho / 2 - fondo` mm hacia fuera de la cara: entra `fondo` mm.
    Los bordes salen suaves (no a 90 grados) y la malla no los cuenta como aristas vivas.
    """
    r = ancho / 2 + 0.2
    return cilindro_en("y", r, y1 - y0, (x, (y0 + y1) / 2, z_cara + lado * (r - fondo)))


class Corredera(Familia):
    id = "corredera.pistola"
    version = 1
    nombre = "Corredera de pistola"
    tolerancia_mm = 0.03  # malla más fina: las ranuras y los filetes de una corredera son pequeños
    tolerancia_angular = 0.25
    requiere = (INTERFAZ_RIEL_CORREDERA,)
    ofrece = (INTERFAZ_MIRA_PISTOLA, e.ROSCAS_BOCA["14mm_ccw"])
    material = "mat.acero_negro"
    parametros = (
        Parametro("largo", "Largo de la corredera", float, "mm", 120, 240, de_sku=True),
        Parametro("ancho", "Ancho de la corredera", float, "mm", 20, 32, de_sku=True),
        Parametro("alto", "Alto total (del canal inferior a la cara superior)", float, "mm", 24, 38, de_sku=True),
        Parametro("largo_ventana", "Largo de la ventana de eyección", float, "mm", 20, 60, de_sku=True, critico=False),
        Parametro(
            "estilo", "Silueta: polímero moderno o clásica de acero", str, opciones=ESTILOS, por_defecto="polimero"
        ),
        Parametro("serrado_trasero", "Surcos del serrado trasero (0 = sin)", int, "ud", 0, 12, por_defecto=6),
        Parametro("serrado_frontal", "Surcos del serrado frontal (0 = sin)", int, "ud", 0, 8, por_defecto=3),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Corredera {p['estilo']} de {mm(p, 'largo')} con serrado {p['serrado_trasero']}/{p['serrado_frontal']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, ancho, alto = float(p["largo"]), float(p["ancho"]), float(p["alto"])
        ventana = 40.0 if p["largo_ventana"] is None else float(p["largo_ventana"])
        estilo = str(p["estilo"])
        semi = ancho / 2
        y_sup = alto + PLANO_CORREDERA_Y  # la cara inferior apoya en PLANO_CORREDERA_Y
        y_inf = PLANO_CORREDERA_Y
        # La corredera es la intersección del perfil lateral (XY, extruido en Z) con la vista en planta (XZ, extruida
        # en Y), con los filetes de las aristas largas: caras planas limpias y esquinas redondeadas.
        if estilo == "polimero":
            lado = [
                (0, y_inf),
                (0, y_sup - 3.0),
                (3.0, y_sup),
                (largo - 24.0, y_sup),
                (largo - 2.0, y_sup - 8.5),
                (largo, y_sup - 10.0),
                (largo, y_inf),
            ]
            planta = [
                (0, semi - 2.2),
                (2.5, semi),
                (largo - 30.0, semi),
                (largo - 6.0, semi - 2.6),
                (largo, semi - 4.4),
            ]
            # Frontal: el costado se estrecha hacia la cara superior (bisel de la corredera moderna).
            frontal = [
                (-semi, y_inf, 0.0),
                (semi, y_inf, 0.0),
                (semi, y_sup - 9.0, 3.5),
                (semi - 3.0, y_sup, 2.0),
                (-semi + 3.0, y_sup, 2.0),
                (-semi, y_sup - 9.0, 3.5),
            ]
            r_sup, x_delantera, x_trasera = 3.2, largo - 22.0, 12.5
        else:
            lado = [
                (0, y_inf),
                (0, y_sup - 5.0),
                (9.0, y_sup),
                (largo - 8.0, y_sup),
                (largo - 1.0, y_sup - 3.5),
                (largo, y_sup - 5.5),
                (largo, y_inf),
            ]
            planta = [(0, semi - 3.2), (3.0, semi - 0.4), (7.0, semi), (largo - 14.0, semi), (largo, semi - 3.6)]
            # Frontal: lomo redondeado en la cara superior, como una corredera clásica de acero.
            frontal = [
                (-semi, y_inf, 0.0),
                (semi, y_inf, 0.0),
                (semi, y_sup, 5.8),
                (-semi, y_sup, 5.8),
            ]
            r_sup, x_delantera, x_trasera = 1.8, largo - 14.0, 12.5
        pl = [(x, z) for x, z in planta] + [(x, -z) for x, z in reversed(planta)]
        cuerpo = extrude(Plane.XY * Polygon(*lado, align=None), amount=semi + 2, both=True) & (
            Rot(90, 0, 0) * extrude(Plane.XY * Polygon(*pl, align=None), amount=40, both=True)
        )
        cuerpo = cuerpo & (
            Pos(-2.0, 0, 0) * extrude(Plane.YZ * cara([(y, z, r) for z, y, r in frontal]), amount=-(largo + 4))
        )
        largas = [a for a in cuerpo.edges() if a.length > largo * 0.4]
        for r in (r_sup, 1.4, 0.8):  # el filete grande falla contra el bisel de la cara superior: se prueba más pequeño
            redondeado = filetear(cuerpo, r, [a for a in largas if y_sup - 2.0 < a.center().Y])
            if redondeado is not cuerpo:
                cuerpo = redondeado
                break
        largas = [a for a in cuerpo.edges() if a.length > largo * 0.4 and abs(a.center().Z) > semi - 0.1]
        cuerpo = filetear(cuerpo, 1.6, [a for a in largas if y_sup - 12.0 < a.center().Y < y_sup - 4.0])
        cuerpo = filetear(
            cuerpo, 1.2, [a for a in cuerpo.edges() if a.length > largo * 0.4 and y_inf + 1 > a.center().Y]
        )
        cuerpo = filetear(
            cuerpo,
            1.8,
            [a for a in cuerpo.edges() if (a.length < 40 and abs(a.center().X) < 4) or largo - 1.5 < a.center().X],
        )
        # Canal inferior: por ahí entra el armazón y bajan los raíles. Termina en el cierre de la boca.
        y_canal = y_sup - 8.0
        canal = Pos(largo / 2 - 4, (y_inf + y_canal) / 2 - 0.5, 0) * Box(
            largo - 6, y_canal - y_inf + 1, ancho - 2 * MURO
        )
        canal = filetear(canal, 1.2, [a for a in canal.edges() if a.length == largo - 6])
        cuerpo = cuerpo - canal
        # Ventana de eyección en la cara derecha (-Z): corte con el frente inclinado, por encima de la cámara.
        x0 = largo * 0.28
        v = Polygon(
            (x0, 2.0), (x0 + ventana, 2.0), (x0 + ventana - 2.0, y_sup - 2.2), (x0 + 5.0, y_sup - 2.2), align=None
        )
        corte = extrude(Plane.XY.offset(-semi - 1.0) * v, amount=semi + 1.0 + semi - MURO)
        corte = filetear(
            corte,
            1.6,
            [a for a in corte.edges() if abs(a.center().Z - (-semi - 1.0 + (2 * semi + 1.0 - MURO) / 2)) > 1],
        )
        cuerpo = cuerpo - corte
        # Serrado en V, a ambos lados, en trasero y frontal.
        x_serr = 6.5 if estilo == "polimero" else 13.0
        x_serr_f = largo - (44.0 if estilo == "polimero" else 36.0)
        surcos = 0
        for z_cara, lado in ((semi, 1), (-semi, -1)):
            for i in range(int(p["serrado_trasero"])):
                cuerpo = cuerpo - _v_vertical(x_serr + i * 3.4, 2.0, 1.3, y_inf + 4.0, y_sup - 2.5, z_cara, lado)
                surcos += 1
            for i in range(int(p["serrado_frontal"])):
                cuerpo = cuerpo - _v_vertical(x_serr_f + i * 3.4, 2.0, 1.3, y_inf + 4.0, y_sup - 4.0, z_cara, lado)
                surcos += 1
        # Colas de milano: ranura trasera (para la mira trasera) y delantera (zócalo para la mira delantera).
        for x_c in (x_delantera, x_trasera):
            ranura = Pos(x_c, y_sup - 1.2, 0) * Box(7.2, 2.6, 12.5)
            cuerpo = cuerpo - ranura
            surcos += 1
        # Boca: alojamiento del cañón y, debajo, el del muelle guía.
        cuerpo = cuerpo - cilindro_en("x", 7.4, 16.0, (largo - 7.5, 0.0, 0.0))
        cuerpo = cuerpo - cilindro_en("x", 2.1, 6.0, (2.5, 3.0, 0.0))  # alojamiento del percutor en la cara trasera
        cuerpo = cuerpo - cilindro_en("x", 3.2, 12.0, (largo - 5.5, -9.0, 0.0))
        surcos += 2
        y_trasera = y_sup - 0.5
        sockets = (
            Socket("armazon", (0.0, y_inf, 0.0), INTERFAZ_RIEL_CORREDERA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket(
                "mira_trasera",
                (x_trasera, y_trasera, 0.0),
                INTERFAZ_MIRA_PISTOLA,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {"lado": "trasera"},
            ),
            Socket(
                "mira_delantera",
                (x_delantera, y_trasera, 0.0),
                INTERFAZ_MIRA_PISTOLA,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {"lado": "delantera"},
            ),
            Socket("canon", (largo, 0.0, 0.0), INTERFAZ_CANON_PISTOLA, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
        )
        cotas = (estimada("corredera.pared_lateral", MURO), estimada("corredera.altura_cara_superior_sobre_eje", y_sup))
        notas = (
            "Solo forma exterior: el interior (extractor, percutor, muelle) no se modela.",
            "Proporciones de silueta, ventana, serrado y colas de milano estimadas, sin cota de ningún SKU.",
        )
        return Geometria(cuerpo, sockets, cotas, notas, (largo, alto, ancho), vaciados=surcos)
