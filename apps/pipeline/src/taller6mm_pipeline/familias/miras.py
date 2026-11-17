"""Familias de miras mecánicas del M4: asa de transporte A2 con alza trasera y BUIS abatible sobre raíl.

Ejes: +X boca, +Y arriba, +Z izquierda. Origen: centro de la cara que apoya (receptor o raíl). Las medidas son cotas del
SKU: sin ellas, T0 sin malla.

El asa es un perfil con arco extruido (hueco de la mano incluido) con el alza trasera encima: guardas laterales, placa
con el agujero de la mira, tambor de elevación a la izquierda y mando de deriva a la derecha, ambos con estrías. El BUIS
lleva base con tornillo de apriete, bisagra con eje, y un cuerpo plegable de secciones lofteadas: trasera con tambor de
apertura y carrillos de protección; delantera con poste y guardas. Los muelles, el trinquete interno y las muescas del
raíl no se modelan, y las proporciones son estimadas (sin cota de SKU): de ahí que no pasen de T1.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Axis, Box, Line, Pos, Rot, Spline

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import (
    biselar,
    cilindro_en,
    extruir_perfil,
    filetear,
    loftear,
    superelipse,
)

INTERFAZ_ASA = "montaje-asa-a2"  # propuestas en catalogo/ar-m4.json (interfaces_nuevas)
INTERFAZ_MIRA_TRASERA = "montaje-mira-trasera-a2"


def _estrias(eje_centro: tuple[float, float, float], radio: float, largo: float, n: int, hondo: float) -> Any:
    """Conjunto de `n` ranuras longitudinales alrededor de un cilindro con eje en Z (moleteado del tambor)."""
    x0, y0, z0 = eje_centro
    corte = None
    for k in range(n):
        ang = 360.0 * k / n
        ranura = (
            Pos(x0, y0, z0)
            * Rot(0, 0, ang)
            * Pos(radio, 0, 0)
            * Box(2 * hondo, 0.9 * (math.tau * radio / n), largo + 2)
        )
        corte = ranura if corte is None else corte + ranura
    return corte


class AsaTransporteA2(Familia):
    id = "mira.asa_a2"
    version = 2  # v2: asa con arco, guardas, placa de mira y tambores (antes, una silueta extruida con una ventana)
    nombre = "Asa de transporte A2"
    requiere = (INTERFAZ_ASA,)
    ofrece = (INTERFAZ_MIRA_TRASERA,)
    parametros = (
        Parametro("longitud", "Longitud del asa", float, "mm", 80, 220, de_sku=True),
        Parametro("altura", "Altura sobre la cara de montaje", float, "mm", 30, 100, de_sku=True),
        Parametro("ancho", "Ancho lateral (con los mandos del alza)", float, "mm", 10, 40, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Asa de transporte A2 de {mm(p, 'longitud')} de largo y {mm(p, 'altura')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, A, W = float(p["longitud"]), float(p["altura"]), float(p["ancho"])  # noqa: N806
        bw = max(6.0, 0.72 * W)  # ancho del cuerpo; los mandos del alza llegan hasta W
        # Contorno exterior: base, frente curvo, dorso del asa que sube hacia el alza, torre trasera plana.
        contorno = [
            Line((-0.5 * L, 0.0), (0.5 * L, 0.0)),
            Spline(
                (0.5 * L, 0.0),
                (0.5 * L, 0.24 * A),
                (0.45 * L, 0.48 * A),
                (0.31 * L, 0.62 * A),
                (0.10 * L, 0.70 * A),
                (-0.10 * L, 0.76 * A),
                (-0.17 * L, 0.80 * A),
            ),
            Line((-0.17 * L, 0.80 * A), (-0.19 * L, A)),
            Line((-0.19 * L, A), (-0.46 * L, A)),
            Line((-0.46 * L, A), (-0.5 * L, 0.90 * A)),
            Line((-0.5 * L, 0.90 * A), (-0.5 * L, 0.0)),
        ]
        cuerpo = extruir_perfil(contorno, bw)
        # El arco: hueco de la mano bajo el asa (atraviesa de lado a lado).
        arco = [
            Spline(
                (-0.10 * L, -1.0),
                (-0.095 * L, 0.30 * A),
                (-0.03 * L, 0.47 * A),
                (0.08 * L, 0.52 * A),
                (0.20 * L, 0.46 * A),
                (0.285 * L, 0.30 * A),
                (0.30 * L, -1.0),
            ),
            Line((0.30 * L, -1.0), (-0.10 * L, -1.0)),
        ]
        cuerpo = cuerpo - extruir_perfil(arco, bw + 2)
        cuerpo = filetear(
            cuerpo, min(1.6, 0.04 * L), [ed for ed in cuerpo.edges() if abs(abs(ed.center().Z) - bw / 2) < 0.2]
        )
        cuerpo = filetear(
            cuerpo,
            2.2,
            [
                ed
                for ed in cuerpo.edges()
                if (ed.center().Y > 0.97 * A and abs(ed.center().Z) < bw / 2 - 0.2)
                or (ed.center().Y > 0.97 * A and abs(ed.center().X) > 0.4 * L)
            ],
        )
        # Alza trasera: ranura transversal entre dos guardas laterales y, dentro, la placa del agujero de la mira.
        x_mira = -0.33 * L
        ancho_ranura = 0.10 * L
        cuerpo = cuerpo - Pos(x_mira, A - 0.21 * A, 0) * Box(ancho_ranura, 0.42 * A, 0.54 * bw)
        placa = Pos(x_mira, A - 0.27 * A, 0) * Box(0.30 * ancho_ranura, 0.54 * A, 0.54 * bw - 0.8)
        placa = filetear(placa, 0.8)
        cuerpo = cuerpo + placa
        cuerpo = cuerpo - cilindro_en("x", 0.085 * A, 0.4 * ancho_ranura, (x_mira, A - 0.19 * A, 0.0))
        # Rebajes de las caras laterales de la torre: la pared deja de ser una placa plana.
        for lado in (1, -1):
            rebaje = Pos(-0.355 * L, 0.52 * A, lado * (bw / 2)) * Box(0.20 * L, 0.46 * A, 2.4)
            cuerpo = cuerpo - filetear(rebaje, 1.0)
        # Tambor de elevación (izquierda, estriado) y mando de deriva (derecha, más pequeño y estriado).
        r_elev, r_deriva = 0.19 * A, 0.11 * A
        z_c = (W / 2 + bw / 2 - 1.6) / 2  # centro del saliente, con su base hundida en el rebaje
        saliente = W / 2 - bw / 2 + 1.6
        tambor = cilindro_en("z", r_elev, saliente, (-0.33 * L, 0.36 * A, z_c))
        tambor = tambor - _estrias((-0.33 * L, 0.36 * A, z_c), r_elev, saliente, 14, 0.5)
        mando = cilindro_en("z", r_deriva, saliente, (-0.27 * L, 0.52 * A, -(z_c)))
        mando = mando - _estrias((-0.27 * L, 0.52 * A, -(z_c)), r_deriva, saliente, 10, 0.45)
        cuerpo = cuerpo + tambor + mando
        socket_base = Socket("montaje-asa-a2", (0.0, 0.0, 0.0), INTERFAZ_ASA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
        socket_mira = Socket(
            "mira-trasera",
            (round(-0.34 * L, 4), A, 0.0),
            INTERFAZ_MIRA_TRASERA,
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
        )
        notas = (
            "Silueta del arco, guardas, placa y mandos con proporciones estimadas, sin cota de SKU.",
            "El raíl de montaje superior del asa desmontable y la hélice de los mandos no se modelan.",
        )
        caja = cuerpo.bounding_box()
        return Geometria(
            cuerpo, (socket_base, socket_mira), (), notas, (caja.size.X, caja.size.Y, caja.size.Z), vaciados=3
        )


class Buis(Familia):
    id = "mira.buis"
    version = 3  # v2: base con tornillo, bisagra y cuerpo plegable con tambor o poste (antes, cajas)
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

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["altura"] is not None
            and p["altura_base"] is not None
            and float(p["altura"]) < float(p["altura_base"]) + 10
        ):
            raise ParametroInvalidoError("altura: debe superar la altura de la base en 10 mm")

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"BUIS {p['lado']} {p['posicion']} de {mm(p, 'altura')} de alto"

    def _base(self, lb: float, hb: float, ancho: float) -> Any:
        """Base con laterales biselados, tornillo de apriete a la izquierda y dos orejas de bisagra con eje."""
        # Perfil lateral: pared trasera y delantera inclinadas, con el borde superior achaflanado.
        lateral = [
            Line((-0.5 * lb, 0.0), (0.5 * lb, 0.0)),
            Line((0.5 * lb, 0.0), (0.5 * lb, 0.55 * hb)),
            Line((0.5 * lb, 0.55 * hb), (0.30 * lb, hb)),
            Line((0.30 * lb, hb), (-0.30 * lb, hb)),
            Line((-0.30 * lb, hb), (-0.5 * lb, 0.55 * hb)),
            Line((-0.5 * lb, 0.55 * hb), (-0.5 * lb, 0.0)),
        ]
        base = extruir_perfil(lateral, ancho)
        # Esquinas de la huella (aristas verticales, en planta) y cantos largos con bisel: la pinza real no es un taco.
        base = biselar(base, 0.22 * lb, base.edges().filter_by(Axis.Y))
        base = biselar(base, min(2.6, 0.30 * hb), base.edges().filter_by(Axis.X).filter_by_position(Axis.Y, -0.1, 0.1))
        base = biselar(
            base, min(2.0, 0.24 * hb), base.edges().filter_by(Axis.X).filter_by_position(Axis.Y, hb - 0.1, hb + 0.1)
        )
        base = filetear(base, min(1.2, 0.12 * hb))
        # Tornillo de apriete: cabeza cilíndrica con ranura, rehundida en un avellanado del lateral izquierdo.
        x_t, y_t = -0.22 * lb, 0.45 * hb
        base = base - cilindro_en("z", 0.20 * hb + 1.2, 3.0, (x_t, y_t, ancho / 2 - 1.5))
        cabeza = cilindro_en("z", 0.20 * hb + 0.6, 2.4, (x_t, y_t, ancho / 2 - 1.8))
        cabeza = cabeza - Pos(x_t, y_t, ancho / 2 - 0.9) * Box(2 * (0.20 * hb + 1), 0.8, 1.2)
        # Muesca bajo la base para el diente de retroceso del raíl.
        base = base - Pos(0.15 * lb, 0.0, 0) * Box(0.16 * lb, 2.0, 0.5 * ancho)
        return base + cabeza

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        lb, hb, h, ancho = (float(p[k]) for k in ("longitud_base", "altura_base", "altura", "ancho"))
        base = self._base(lb, hb, ancho)
        r_eje = min(0.12 * hb + 1.3, 0.35 * max(3.0, 0.30 * lb))
        alto_cuerpo = h - hb - 0.2 * r_eje  # de la bisagra al punto más alto
        grueso = max(3.0, 0.30 * lb)
        w = 0.52 * ancho  # ancho del cuerpo plegable
        trasera = p["lado"] == "trasera"
        # Orejas de bisagra y su eje (extremos del eje visibles a cada lado).
        z_oreja = w / 2 + 1.3
        orejas = None
        for lado in (1, -1):
            oreja = cilindro_en("z", 1.6 * r_eje, 2.2, (0.0, hb + 0.2 * r_eje, lado * z_oreja)) + Pos(
                0, hb - 0.4 * r_eje, lado * z_oreja
            ) * Box(3.2 * r_eje, 2.0 * r_eje, 2.2)
            orejas = oreja if orejas is None else orejas + oreja
        eje = cilindro_en("z", r_eje, 2 * z_oreja + 3.0, (0.0, hb + 0.2 * r_eje, 0.0))
        eje = filetear(eje, 0.4)
        # Cuerpo plegable (coordenadas relativas a la bisagra, que queda en el origen).
        yb = 0.2 * r_eje
        if trasera:
            radio = min(0.30 * alto_cuerpo, 0.40 * lb, 0.5 * w)
            y_tambor = alto_cuerpo - radio  # el tambor termina justo a la altura `h`
            cuello = loftear(
                [
                    superelipse(yb, 0.0, 0.5 * w, 0.46 * grueso, n=3.0),
                    superelipse(0.45 * y_tambor, 0.0, 0.40 * w, 0.38 * grueso, n=3.0),
                    superelipse(y_tambor, 0.0, 0.46 * w, 0.62 * radio, n=2.4),
                ]
            )
            tambor = cilindro_en("z", radio, w, (0.0, y_tambor, 0.0))
            tambor = tambor - cilindro_en("x", 0.30 * radio, 2 * radio + 2, (0.0, y_tambor, 0.0))  # agujero de la mira
            tambor = tambor - cilindro_en("x", 0.18 * radio, 2 * radio + 2, (0.0, y_tambor - 0.55 * radio, 0.0))
            tambor = tambor - _estrias((0.0, y_tambor, 0.0), radio, w, 16, 0.4 * radio * 0.28)
            carrillos = None
            for lado in (1, -1):
                c = Pos(0, y_tambor - 0.15 * radio, lado * (w / 2 + 0.9)) * Box(1.6 * radio, 1.6 * radio, 1.8)
                c = filetear(c, 0.6)
                carrillos = c if carrillos is None else carrillos + c
            cuerpo_mira = cuello + tambor + carrillos
        else:
            radio_poste = max(0.8, 0.045 * alto_cuerpo)
            y_poste = alto_cuerpo
            cuello = loftear(
                [
                    superelipse(yb, 0.0, 0.5 * w, 0.46 * grueso, n=3.0),
                    superelipse(0.42 * y_poste, 0.0, 0.42 * w, 0.36 * grueso, n=3.0),
                    superelipse(0.70 * y_poste, 0.0, 0.36 * w, 0.30 * grueso, n=2.6),
                ]
            )
            poste = cilindro_en("y", radio_poste, 0.34 * y_poste, (0.0, 0.83 * y_poste, 0.0))
            guardas = None
            for lado in (1, -1):
                g = Pos(0, 0.72 * y_poste, lado * (0.40 * w)) * Box(0.7 * grueso, 0.44 * y_poste, 1.4)
                g = filetear(g, 0.5)
                guardas = g if guardas is None else guardas + g
            cuerpo_mira = cuello + poste + guardas
        cuerpo_mira = cuerpo_mira + eje
        if p["posicion"] == "abatida":  # gira sobre la bisagra hacia +X
            cuerpo_mira = Rot(0, 0, -90) * cuerpo_mira
        cuerpo = base + orejas + Pos(0, hb + 0.2 * r_eje, 0) * cuerpo_mira
        socket = Socket("rail.base", (0.0, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
        notas = (
            "Pinza al raíl, muelles y trinquete de la bisagra no se modelan; proporciones estimadas.",
            "La mira abatida gira 90° sobre la bisagra hacia delante (+X).",
        )
        caja = cuerpo.bounding_box()
        nominal = (caja.size.X, caja.size.Y, ancho) if p["posicion"] == "abatida" else (lb, h, ancho)
        return Geometria(cuerpo, (socket,), (), notas, nominal, vaciados=3 if trasera else 2)
