"""Armazones de pistola de airsoft: de polímero (estilo Glock) y metálico (estilo 1911). Origen común de pistola.

Los dos arrancan en la cara trasera de la corredera (X = 0) con el eje del cañón en Y = 0; la cara de apoyo de la
corredera es `PLANO_CORREDERA_Y`. El agarre se inclina hacia atrás (la base queda a -X) el ángulo `inclinacion`.

Polímero: cuerpo lateral extruido con el cubrecañón y el riel de accesorios ranurado, empuñadura lofteada con
punteado y ranuras de los dedos, guardamonte, gatillo, palanca de retenida, pestillo y botón del cargador. Metálico:
perfil de cubrecañón corto y empuñadura recta con el arco del muelle real, guardamonte cuadrado, martillo con
espolón, seguro manual, gatillo largo y cuatro casquillos de tornillo para las cachas (`empunadura.lateral_1911`) y
el seguro de empuñadura (`seguro.empunadura_1911`) como piezas aparte. Solo forma exterior: la mecánica no se modela.
Las proporciones son de barrido (sin cota de ningún SKU).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Box, Compound, Cylinder, Face, Plane, Polygon, Pos, Rot, Sphere, Wire, extrude

from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import filetear, interpolar, loftear, superelipse
from taller6mm_pipeline.familias.pistola_comun import (
    INTERFAZ_RIEL_CORREDERA,
    PLANO_CORREDERA_Y,
    estimada,
    hexagonal,
    spline_cerrada,
)

Y0 = PLANO_CORREDERA_Y
POZO_POLIMERO = "pozo-glock-gbb"  # catalogo/interfaces.json
POZO_CLASICO = "pozo-1911-gbb"
RIEL_UNIVERSAL = "rail-pistola-glock-universal"
ANCHO_POZO = 23.0  # ancho (Z) del hueco del cargador; es el del cargador + holgura (estimado)
PROFUNDIDAD_POZO = 34.0


def _marco(x_sup: float, y_sup: float, inclinacion: float) -> Any:
    """Ubicación del eje del agarre: origen arriba, +Y a lo largo del agarre (inclinado hacia atrás)."""
    return Pos(x_sup, y_sup, 0) * Rot(0, 0, -inclinacion)


def _extruir(aristas: Any, ancho: float) -> Any:
    return extrude(Face(Wire(list(aristas))), amount=ancho / 2, both=True)


def _capsula(x: float, y: float, radio: float, largo: float) -> Any:
    cuerpo = Pos(x, y, 0) * Cylinder(radio, largo)
    for lado in (1, -1):
        cuerpo = cuerpo + Pos(x, y, lado * largo / 2) * Sphere(radio)
    return cuerpo


def _anillo(contorno: list[tuple[float, float]], ancho: float, centro: tuple[float, float], escala: float) -> Any:
    """Guardamonte: contorno liso extruido menos el mismo contorno reducido hacia `centro`."""
    interior = [(centro[0] + (x - centro[0]) * escala, centro[1] + (y - centro[1]) * escala) for x, y in contorno]
    return _extruir(spline_cerrada(contorno), ancho) - _extruir(spline_cerrada(interior), ancho + 2)


def _gatillo(pts: list[tuple[float, float]], ancho: float) -> Any:
    g = _extruir(spline_cerrada(pts), ancho)
    return filetear(g, 0.7, [a for a in g.edges() if a.length > 6 and abs(a.center().Z) > ancho / 2 - 0.1])


# Secciones del agarre de polímero a lo largo de la altura: (u, fracción de semi-profundidad delantera, trasera, ancho).
_SECCIONES_POLIMERO = (
    (0.00, 1.00, 1.00, 0.80),
    (0.12, 1.00, 1.02, 0.90),
    (0.35, 0.96, 0.94, 0.98),
    (0.62, 0.93, 0.92, 1.00),
    (0.85, 0.95, 0.98, 0.99),
    (0.96, 0.98, 1.03, 0.96),
    (1.00, 0.96, 1.00, 0.88),
)
_NIVELES = (0.0, 0.04, 0.09, 0.16, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.84, 0.91, 0.96, 0.99, 1.0)


class ArmazonPolimero(Familia):
    id = "armazon.polimero"
    version = 1
    nombre = "Armazón de polímero (estilo Glock)"
    requiere = ()
    ofrece = (INTERFAZ_RIEL_CORREDERA, POZO_POLIMERO, RIEL_UNIVERSAL)
    material = "mat.polimero_negro"
    parametros = (
        Parametro("largo", "Largo del armazón (cubrecañón incluido)", float, "mm", 120, 220, de_sku=True),
        Parametro("alto_empunadura", "Alto del agarre bajo la corredera", float, "mm", 60, 130, de_sku=True),
        Parametro("profundidad", "Profundidad delante-detrás del agarre", float, "mm", 30, 55, de_sku=True),
        Parametro("ancho", "Ancho del agarre", float, "mm", 22, 38, de_sku=True),
        Parametro("inclinacion", "Inclinación del agarre hacia atrás", float, "grados", 8, 30, de_sku=True),
        Parametro("textura", "Textura del agarre", str, opciones=("punteado", "liso"), por_defecto="punteado"),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Armazón de polímero de {mm(p, 'largo')} con agarre {p['textura']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, prof = float(p["largo"]), float(p["alto_empunadura"]), float(p["profundidad"])
        ancho, inc = float(p["ancho"]), float(p["inclinacion"])
        tan = math.tan(math.radians(inc))
        y_sup = Y0 - 6.0
        x_c = 36.0 + prof / 2 - 22.0  # centro del agarre arriba
        cuerpo_w = min(ancho - 4.0, 24.0)

        # Agarre lofteado: dorso curvo, cintura y panza de la palma.
        us = [r[0] for r in _SECCIONES_POLIMERO]
        secciones = []
        for u in _NIVELES:
            f, t, w = (interpolar(us, [r[i] for r in _SECCIONES_POLIMERO], u) for i in (1, 2, 3))
            y = y_sup - u * alto
            cx = x_c - tan * (y_sup - y) - 2.5 * math.sin(math.pi * u)  # el dorso se arquea un poco
            secciones.append(superelipse(y, cx, w * ancho / 2, f * prof / 2, t * prof / 2, n=3.4))
        grip = loftear(secciones)

        # Cuerpo superior: cubrecañón con el borde delantero achaflanado y el cuello trasero (cola de castor).
        perfil = [
            (6.0, Y0),
            (largo - 2.0, Y0),
            (largo, Y0 - 4.0),
            (largo, Y0 - 17.0),
            (largo - 6.0, Y0 - 21.0),
            (30.0, Y0 - 21.0),
            (14.0, Y0 - 24.0),
            (6.0, Y0 - 16.0),
        ]
        cuerpo_sup = extrude(Plane.XY * Polygon(*perfil, align=None), amount=cuerpo_w / 2, both=True)
        cuerpo_sup = filetear(cuerpo_sup, 3.0, [a for a in cuerpo_sup.edges() if abs(a.length - cuerpo_w) < 0.01])
        cuerpo_sup = filetear(
            cuerpo_sup, 1.4, [a for a in cuerpo_sup.edges() if a.length > 60 and a.center().Y > Y0 - 1]
        )
        cuerpo = grip + cuerpo_sup

        # Guardamonte (anillo liso) y gatillo.
        arco = [
            (58.0, -22.0),
            (60.0, -32.0),
            (68.0, -45.0),
            (84.0, -52.0),
            (102.0, -50.0),
            (114.0, -42.0),
            (118.0, -30.0),
            (118.0, -22.0),
        ]
        guarda = _anillo(arco, 13.0, (88.0, -37.0), 0.70)
        guarda = filetear(guarda, 1.2, [a for a in guarda.edges() if abs(abs(a.center().Z) - 6.5) < 0.05])
        cuerpo = cuerpo + guarda
        cuerpo = cuerpo + _gatillo(
            [
                (63.0, -21.0),
                (72.0, -34.0),
                (78.0, -45.0),
                (80.5, -49.0),
                (76.0, -50.5),
                (69.0, -47.0),
                (64.0, -36.0),
                (58.0, -24.0),
            ],
            7.0,
        )

        # Ranuras de los dedos en el frente del agarre, hueco del cargador y chaflán de la boca del pozo.
        sitio = _marco(x_c, y_sup, inc)
        for k in range(3):
            u = 0.34 + 0.15 * k
            y = y_sup - u * alto
            frente = x_c - tan * (y_sup - y) + prof / 2 * 0.98 - 0.6
            cuerpo = cuerpo - _capsula(frente + 4.3, y, 5.4, 0.9 * ancho)
        pozo = sitio * Pos(0.0, -alto + 31.0, 0) * Box(PROFUNDIDAD_POZO, 64.0, ANCHO_POZO)
        pozo = filetear(pozo, 3.0, [a for a in pozo.edges() if abs(a.length - 64.0) < 0.01])
        cuerpo = cuerpo - pozo
        vaciados = 5

        # Punteado de las dos caras del agarre.
        if p["textura"] == "punteado":
            puntos = []
            for a, b in hexagonal(-9.0, 9.0, 20.0, alto * 0.82, 3.4):
                u = b / alto
                w = interpolar(us, [r[3] for r in _SECCIONES_POLIMERO], u) * ancho / 2
                for lado in (1, -1):
                    puntos.append(sitio * Pos(a, -b, lado * (w + 0.62)))
            esferas = Compound([Pos(*q.position) * Sphere(1.05) for q in puntos])
            cuerpo = cuerpo - esferas
            vaciados += len(puntos)

        # Riel de accesorios: tres ranuras transversales bajo el cubrecañón.
        for i in range(3):
            cuerpo = cuerpo - Pos(largo - 52.0 + i * 12.0, Y0 - 21.0, 0) * Box(3.4, 3.4, 40.0)
        vaciados += 3
        # Raíles de la corredera sobre el armazón y bloque de cierre.
        for z in (-7.3, 7.3):
            for x0, x1 in ((22.0, 96.0), (120.0, largo - 14.0)):
                riel = Pos((x0 + x1) / 2, Y0 + 2.2, z) * Box(x1 - x0, 4.4, 2.2)
                cuerpo = cuerpo + filetear(riel, 0.6, [a for a in riel.edges() if a.length == x1 - x0])
        cuerpo = cuerpo + Pos(108.0, Y0 + 1.2, 0) * Box(22.0, 2.4, 16.6)
        # Mandos: palanca de retenida y botón del cargador a la izquierda, eje de desmontaje a ambos lados.
        palanca = extrude(
            Plane.XY.offset(cuerpo_w / 2 - 1.0)
            * Polygon(
                (50.0, Y0 - 5.5),
                (94.0, Y0 - 5.5),
                (98.0, Y0 - 8.4),
                (94.0, Y0 - 10.0),
                (52.0, Y0 - 10.0),
                (46.0, Y0 - 7.8),
                align=None,
            ),
            amount=3.0,
        )
        cuerpo = cuerpo + filetear(
            palanca, 0.8, [a for a in palanca.edges() if a.length > 3 and cuerpo_w / 2 + 1.5 < a.center().Z]
        )
        cuerpo = cuerpo + Pos(64.0, Y0 - 17.0, cuerpo_w / 2 + 0.6) * Rot(0, 0, 0) * Cylinder(3.3, 2.8)
        cuerpo = cuerpo + Pos(84.0, Y0 - 11.0, 0) * Cylinder(3.2, cuerpo_w + 2.4)
        cuerpo = cuerpo - Pos(84.0, Y0 - 11.0, cuerpo_w / 2 + 1.0) * Box(1.0, 5.0, 0.8)
        vaciados += 2

        sockets = (
            Socket("corredera", (0.0, Y0, 0.0), INTERFAZ_RIEL_CORREDERA, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket(
                "cargador",
                (x_c - tan * alto, y_sup - alto, 0.0),
                POZO_POLIMERO,
                (-math.sin(math.radians(inc)), -math.cos(math.radians(inc)), 0.0),
                (math.cos(math.radians(inc)), -math.sin(math.radians(inc)), 0.0),
                {"inclinacion_grados": inc},
            ),
            Socket(
                "riel_accesorios", (largo - 34.0, Y0 - 21.0, 0.0), RIEL_UNIVERSAL, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}
            ),
        )
        cotas = (
            estimada("armazon.ancho_cubrecanon", cuerpo_w),
            estimada("armazon.ancho_pozo_cargador", ANCHO_POZO),
            estimada("armazon.profundidad_pozo_cargador", PROFUNDIDAD_POZO),
        )
        notas = (
            "Solo forma exterior: el chasis metálico interior, el seguro del gatillo y la mecánica no se modelan.",
            "Silueta, ranuras de los dedos, punteado y raíles estimados; el riel de accesorios no es un Picatinny.",
            "El pozo del cargador es un hueco liso de medida estimada, sin los rebajes de la retenida.",
        )
        caja = cuerpo.bounding_box()
        return Geometria(cuerpo, sockets, cotas, notas, (caja.size.X, caja.size.Y, caja.size.Z), vaciados=vaciados)
