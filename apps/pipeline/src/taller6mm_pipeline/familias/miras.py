"""Familias de miras mecánicas del M4: asa de transporte A2 con mira trasera y BUIS abatible sobre raíl.

Ejes: +X boca, +Y arriba, +Z izquierda. Origen: centro de la cara que apoya (receptor o raíl). Las medidas son cotas del
SKU: sin ellas, T0 sin malla. Las ruedas de deriva y elevación, el tambor de la mira y el resorte no se modelan.
"""

from __future__ import annotations

from collections.abc import Mapping

from build123d import Box, Pos, Rot

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import caja_de, mm, prisma

INTERFAZ_ASA = "montaje-asa-a2"  # propuestas en catalogo/ar-m4.json (interfaces_nuevas)
INTERFAZ_MIRA_TRASERA = "montaje-mira-trasera-a2"


class AsaTransporteA2(Familia):
    id = "mira.asa_a2"
    nombre = "Asa de transporte A2"
    requiere = (INTERFAZ_ASA,)
    ofrece = (INTERFAZ_MIRA_TRASERA,)
    parametros = (
        Parametro("longitud", "Longitud del asa", float, "mm", 80, 220, de_sku=True),
        Parametro("altura", "Altura sobre la cara de montaje", float, "mm", 30, 100, de_sku=True),
        Parametro("ancho", "Ancho lateral", float, "mm", 10, 40, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Asa de transporte A2 de {mm(p, 'longitud')} de largo y {mm(p, 'altura')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, ancho = float(p["longitud"]), float(p["altura"]), float(p["ancho"])
        exterior = [
            (-0.5 * largo, 0.0),
            (0.5 * largo, 0.0),
            (0.5 * largo, 0.55 * alto),
            (0.42 * largo, 0.85 * alto),
            (-0.18 * largo, 0.85 * alto),
            (-0.18 * largo, alto),
            (-0.5 * largo, alto),
        ]
        ventana = [
            (-0.08 * largo, 0.16 * alto),
            (0.36 * largo, 0.16 * alto),
            (0.33 * largo, 0.66 * alto),
            (-0.08 * largo, 0.66 * alto),
        ]
        cuerpo = prisma(exterior, ancho) - prisma(ventana, ancho + 2)
        socket_base = Socket("montaje-asa-a2", (0.0, 0.0, 0.0), INTERFAZ_ASA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
        socket_mira = Socket(
            "mira-trasera",
            (round(-0.34 * largo, 4), alto, 0.0),
            INTERFAZ_MIRA_TRASERA,
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
        )
        notas = (
            "Silueta de perfil con proporciones estimadas; las ruedas de deriva y elevación y el tambor no se modelan.",
            "El raíl de montaje superior del asa desmontable no se modela.",
        )
        x0, x1, y0, y1 = caja_de(exterior)
        return Geometria(cuerpo, (socket_base, socket_mira), (), notas, (x1 - x0, y1 - y0, ancho), vaciados=1)


class Buis(Familia):
    id = "mira.buis"
    nombre = "BUIS abatible"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    parametros = (
        Parametro(
            "lado",
            "Mira trasera con ventana o delantera con poste",
            str,
            opciones=("trasera", "delantera"),
            por_defecto="trasera",
        ),
        Parametro("posicion", "Estado de la mira", str, opciones=("erguida", "abatida"), por_defecto="erguida"),
        Parametro("longitud_base", "Longitud de la base sobre el raíl", float, "mm", 15, 80, de_sku=True),
        Parametro("altura_base", "Altura de la base", float, "mm", 5, 30, de_sku=True),
        Parametro("altura", "Altura total con la mira erguida", float, "mm", 15, 70, de_sku=True),
        Parametro("ancho", "Ancho lateral", float, "mm", 10, 40, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"BUIS {p['lado']} {p['posicion']} de {mm(p, 'altura')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        lb, hb, h, ancho = (float(p[k]) for k in ("longitud_base", "altura_base", "altura", "ancho"))
        base = Pos(0, hb / 2, 0) * Box(lb, hb, ancho)
        grueso = max(2.0, 0.25 * lb)
        alto_cuerpo = h - hb
        if p["lado"] == "trasera":
            cuerpo_mira = Pos(0, alto_cuerpo / 2, 0) * Box(grueso, alto_cuerpo, 0.8 * ancho)
            hueco = Pos(0, 0.65 * alto_cuerpo, 0) * Box(grueso + 2, 0.3 * alto_cuerpo, 0.3 * ancho)
            cuerpo_mira = cuerpo_mira - hueco
        else:
            cuerpo_mira = Pos(0, alto_cuerpo / 2, 0) * Box(grueso, alto_cuerpo, 0.25 * ancho)
        if p["posicion"] == "abatida":  # gira sobre la bisagra (arriba de la base) hacia +X
            cuerpo_mira = Rot(0, 0, -90) * cuerpo_mira
        cuerpo = base + Pos(0, hb, 0) * cuerpo_mira
        # Apoyo en el raíl: la base queda sobre el raíl (cara de montaje abajo, en Y=0).
        socket = Socket("rail.base", (0.0, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
        notas = (
            "Pinza al raíl, bisagra, resorte y muelle no se modelan; silueta de proporciones estimadas.",
            "La mira abatida gira 90° sobre la bisagra hacia delante (+X).",
        )
        if p["posicion"] == "abatida":
            # Girada sobre la bisagra (x = 0, y = hb): ocupa x de -lb/2 a max(lb/2, alto) e y alrededor de la bisagra.
            nominal = (
                max(lb / 2, alto_cuerpo) + lb / 2,
                max(hb, hb + grueso / 2) - min(0.0, hb - grueso / 2),
                ancho,
            )
        else:
            nominal = (lb, h, ancho)
        return Geometria(cuerpo, (socket,), (), notas, nominal, vaciados=int(p["lado"] == "trasera"))
