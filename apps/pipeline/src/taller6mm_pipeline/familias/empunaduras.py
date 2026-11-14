"""Familia: empuñadura de pistola (pistolete) del AR-15/M4 de airsoft, estilo A2, MOE o ergonómico.

Origen: centro de la cara de montaje (donde el pistolete toca el receptor inferior). El pistolete cuelga hacia -Y y se
inclina hacia atrás (-X). Alto, profundidad, ancho e inclinación son cotas del SKU: sin ellas, la pieza sale T0 y sin
malla.

El cuerpo es un loft de secciones redondeadas (superelipses) que dan el dorso curvo, el estrechamiento del cuello y el
ensanche de la base (la «panza» de la palma); sobre él se tallan las ranuras de los dedos (cápsulas), el hueco de la
base con la cabeza del tornillo y el taladro del tornillo en la cara de montaje. Las curvas son de proporción estimada,
no cotas medidas: por eso la pieza no pasa de T1. El interior (compartimento y cuello de unión) no se modela: es macizo.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping
from typing import Any

from build123d import Box, Cylinder, Edge, Plane, Pos, Rot, Solid, Sphere, Wire

from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, interpolar, loftear, superelipse

INTERFAZ_MONTAJE = "montaje-pistolete-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
PERFILES = ("a2", "moe", "ergo")

# Rasgos por perfil: ranuras de dedos, hondo de ranura (mm), modulación del contorno (1 = A2; menos = más liso),
# repecho (mm, saliente delantero del meñique), repisa del pulgar, huecos laterales del pulgar (MOE).
_RASGOS = {
    "a2": (3, 2.4, 1.0, 0.0, False, False),
    "moe": (0, 0.0, 0.7, 3.0, False, True),
    "ergo": (3, 3.0, 1.2, 4.0, True, False),
}
# Secciones a lo largo de la altura: (u, semi-profundidad delantera, semi-profundidad trasera, semi-ancho) en
# fracción de profundidad/2 y de ancho/2. u = 0 en la cara de montaje y 1 en la base. Dan el resalte del dorso bajo
# la cara de montaje, la cintura, la panza de la palma y el ensanche del meñique; el último bisela la base.
_SECCIONES = (
    (0.000, 1.00, 1.00, 0.94),
    (0.070, 1.00, 1.10, 0.98),
    (0.220, 0.97, 0.86, 1.00),
    (0.450, 0.90, 0.78, 0.97),
    (0.680, 0.93, 0.92, 0.95),
    (0.860, 1.05, 1.18, 0.98),
    (0.955, 1.12, 1.24, 0.96),
    (0.990, 1.08, 1.18, 0.90),
    (1.000, 0.96, 1.04, 0.80),
)
_N_SUPERELIPSE = 3.2
_NIVELES = (
    0.0,
    0.035,
    0.07,
    0.12,
    0.18,
    0.25,
    0.33,
    0.42,
    0.51,
    0.60,
    0.69,
    0.77,
    0.84,
    0.90,
    0.945,
    0.975,
    0.992,
    1.0,
)


def _centro_x(u: float, desplaza: float, prof: float) -> float:
    """Centro de la sección: baja inclinado hacia atrás y se afina un poco hacia abajo."""
    return -desplaza * u - 0.04 * prof * u


def _cuerpo(p: Mapping[str, Valor]) -> tuple[Any, list[tuple[float, float, float, float]]]:
    alto, prof, ancho = float(p["altura"]), float(p["profundidad"]), float(p["ancho"])
    desplaza = alto * math.tan(math.radians(float(p["inclinacion"])))
    _, _, mod, repecho, _, _ = _RASGOS[str(p["perfil"])]
    secciones: list[Wire] = []
    cajas: list[tuple[float, float, float, float]] = []  # (u, x delantero, x trasero, y)
    us = [r[0] for r in _SECCIONES]
    # Secciones intermedias interpoladas con una curva lisa: sin ellas el loft deja facetas entre las tabulares.
    for u in _NIVELES:
        f, t, b = (interpolar(us, [r[i] for r in _SECCIONES], u) for i in (1, 2, 3))
        cx = _centro_x(u, desplaza, prof)
        f, t = 1 + (f - 1) * mod, 1 + (t - 1) * mod
        delante = f * prof / 2 + (repecho * max(0.0, (u - 0.80) / 0.20) if repecho else 0.0)
        atras = t * prof / 2
        y = -u * alto
        secciones.append(superelipse(y, cx, b * ancho / 2, delante, atras, n=_N_SUPERELIPSE))
        cajas.append((u, cx + delante, cx - atras, y))
    return loftear(secciones), cajas


def _capsula(x: float, y: float, radio: float, largo: float) -> Any:
    """Cápsula con el eje en Z (cilindro con tapas esféricas): hueco redondeado de un dedo."""
    cuerpo = Pos(x, y, 0) * Cylinder(radio, largo)
    for lado in (1, -1):
        cuerpo = cuerpo + Pos(x, y, lado * largo / 2) * Sphere(radio)
    return cuerpo


def _repisa_pulgar(x: float, y: float, z: float, lado: int) -> Any:
    """Repisa elíptica del pulgar: loft de tres elipses en planos paralelos al lateral (sobresale 2,5 mm)."""
    pasos = ((0.0, 8.0, 5.2), (1.2, 7.0, 4.4), (2.5, 4.4, 2.6))
    secciones = []
    for dz, rx, ry in pasos:
        plano = Plane(origin=(x, y, z + lado * (dz - 1.0)), x_dir=(1, 0, 0), z_dir=(0, 0, lado))
        secciones.append(Wire([Edge.make_ellipse(rx, ry, plano)]))
    return Solid.make_loft(secciones)


class EmpunaduraPistolete(Familia):
    id = "empunadura.pistolete"
    version = 2  # v2: formas reales (loft de secciones, ranuras, base con tornillo) en vez de un prisma extruido
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
        ancho, perfil, alto, prof = float(p["ancho"]), str(p["perfil"]), float(p["altura"]), float(p["profundidad"])
        ranuras, hondo, _, _, repisa, huecos_pulgar = _RASGOS[perfil]
        desplaza = alto * math.tan(math.radians(float(p["inclinacion"])))
        cuerpo, cajas = _cuerpo(p)
        vaciados = 0

        def delante_en(u: float) -> float:
            """x del frente de la sección más cercana a `u` (interpolado)."""
            for (u0, f0, _, _), (u1, f1, _, _) in itertools.pairwise(cajas):
                if u0 <= u <= u1:
                    return f0 + (f1 - f0) * (u - u0) / (u1 - u0)
            return cajas[-1][1]

        # Ranuras de los dedos: cápsulas horizontales que muerden el frente (el índice queda arriba, el meñique abajo).
        radio_dedo = 0.085 * alto
        if ranuras:
            for k in range(ranuras):
                u = 0.30 + 0.17 * k
                x = delante_en(u) + radio_dedo - hondo
                cuerpo = cuerpo - _capsula(x, -u * alto, radio_dedo, 0.78 * ancho)
                vaciados += 1
        if huecos_pulgar:  # huecos suaves del pulgar a ambos lados (MOE)
            for lado in (1, -1):
                x = _centro_x(0.2, desplaza, prof) + 0.05 * prof
                hueco = Pos(x, -0.2 * alto, lado * (ancho / 2 + 5.5)) * Sphere(9.0)
                cuerpo = cuerpo - hueco
                vaciados += 1
        # Base: hueco rebajado con la cabeza del tornillo (cilindro con ranura) en el fondo.
        x_base = _centro_x(1.0, desplaza, prof)
        fondo = Pos(x_base, -alto + 1.2, 0) * Rot(90, 0, 0) * Cylinder(0.30 * ancho, 3.6)
        cuerpo = cuerpo - fondo
        tornillo = Pos(x_base, -alto + 2.6, 0) * Rot(90, 0, 0) * Cylinder(0.11 * ancho, 2.2)
        tornillo = tornillo - Pos(x_base, -alto + 3.4, 0) * Box(0.20 * ancho, 1.6, 1.4)
        cuerpo = cuerpo + tornillo
        # Taladro del tornillo de unión en la cara de montaje (se ve al quitar el pistolete del receptor).
        cuerpo = cuerpo - cilindro_en("y", 3.4, 16.0, (-0.14 * prof, -8.0, 0.0))
        vaciados += 2
        ancho_total = ancho
        notas = [
            "Silueta del dorso, las ranuras de los dedos y la panza de la base estimada, no medida en ningún SKU.",
            "El interior (compartimento, cuello de unión al receptor) no se modela: es macizo.",
        ]
        if repisa:  # repisa del pulgar a cada lado (estilo ergonómico)
            for lado in (1, -1):
                x = _centro_x(0.2, desplaza, prof) + 0.08 * prof
                cuerpo = cuerpo + _repisa_pulgar(x, -0.2 * alto, lado * ancho / 2, lado)
            ancho_total = ancho + 3.0
            notas.append("Repisa del pulgar de 3 mm de saliente estimada, sin cota de ningún SKU.")
        cuerpo = filetear(cuerpo, 0.8, [e for e in cuerpo.edges() if abs(e.center().Y) < 0.5])
        caja = cuerpo.bounding_box()
        socket = Socket(
            "montaje-pistolete", (0.0, 0.0, 0.0), INTERFAZ_MONTAJE, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {"perfil": perfil}
        )
        return Geometria(
            cuerpo,
            (socket,),
            (),
            tuple(notas),
            (caja.size.X, caja.size.Y, ancho_total),
            vaciados=vaciados,
        )
