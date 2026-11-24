"""Utilidades compartidas por las familias de la tanda 3 del M4 (ópticas, linternas, bípodes, miras, guardamanos).

Todo es puro y determinista. Ejes de la pieza: +X boca, +Y arriba, +Z izquierda. En los accesorios de raíl el origen
está en el extremo trasero de la zona de apoyo, centrado, con el plano superior del raíl en y = 0 (las mordazas bajan
por los flancos, y < 0). Las proporciones de detalle son estimadas: `estimada` las marca siempre con confianza baja.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from build123d import Axis, Cylinder, Plane, Polygon, Pos, Rot, Solid, Spline, Wire, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, loftear, revolucion, superelipse
from taller6mm_pipeline.ficha import Confianza, Cota

FECHA = "2026-11-14"
FUENTE_ESTIMADO = (
    "estimado a ojo de las proporciones generales del accesorio de airsoft; sin fuente ni calibre (14-11-2026). "
    "Se sustituye por la ficha de un SKU o por medición con calibre."
)
SEMI_RAIL = e.PICATINNY_ANCHO.valor_mm / 2  # semiancho del raíl (estimado, confianza baja)
NOTA_PICATINNY = (
    "Mordazas y bulón de apriete simplificados: se ven las cabezas, no la rosca ni el muelle. El ancho del raíl "
    "es de confianza baja."
)


def estimada(clave: str, valor_mm: float) -> Cota:
    """Cota de proporción general sin fuente verificable (nunca se disfraza de dato de un SKU)."""
    return Cota(clave, round(valor_mm, 4), FUENTE_ESTIMADO, FECHA, Confianza.BAJA)


def nominales(solido: Any) -> tuple[float, float, float]:
    """Largo (X), alto (Y) y ancho (Z) de la caja exacta del B-rep, en mm."""
    caja = solido.bounding_box()
    return (round(caja.size.X, 4), round(caja.size.Y, 4), round(caja.size.Z, 4))


def revolucion_x(perfil: Sequence[tuple[float, float]], *, suave: bool = False) -> Any:
    """Sólido de revolución con el eje en X. `perfil`: puntos (x, radio) de atrás hacia delante (radio >= 0)."""
    cuerpo = revolucion([(r, x) for x, r in perfil], suave=suave)  # `revolucion` gira en torno a Y: (radio, y)
    return Rot(0, 0, -90) * cuerpo  # Y -> +X


def estriado(eje: str, centro: tuple[float, float, float], radio: float, largo: float, n: int, hondo: float) -> Any:
    """Cilindro de `n` estrías longitudinales (moleteado grueso), eje X, Y o Z, centrado en `centro`."""
    pts = []
    for i in range(2 * n):
        r = radio if i % 2 == 0 else radio - hondo
        # Tramos planos en la cresta y el valle: cuatro puntos por diente evitan dientes puntiagudos.
        a = math.tau * i / (2 * n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    cuerpo = extrude(Plane.XY * Polygon(*pts, align=None), largo / 2, both=True)
    giro = {"x": Rot(0, 90, 0), "y": Rot(90, 0, 0), "z": Rot(0, 0, 0)}[eje]
    return Pos(*centro) * giro * cuerpo


def ranura_perfil(largo: float, ancho: float, alto: float) -> Any:
    """Cápsula alargada en X (ranura de aligeramiento o de muelles), eje de la ranura en Z."""
    r = min(alto, ancho) / 2
    recta = max(largo - 2 * r, 0.01)
    cuerpo = Pos(0, 0, 0) * Rot(0, 90, 0) * Cylinder(r, recta)  # eje X
    for lado in (1, -1):
        cuerpo = cuerpo + Pos(lado * recta / 2, 0, 0) * Rot(0, 90, 0) * Cylinder(r, 0.01)
    return cuerpo


def mordazas(x0: float, x1: float, profundidad: float = 8.0, grueso: float = 3.5) -> Any:
    """Dos mordazas que bajan por los flancos del raíl (inclinadas como el bisel), con los cantos redondeados.

    Perfil en el plano YZ (X local = Y de la pieza, Y local = Z) extruido a lo largo de X.
    """
    largo = x1 - x0
    piezas = []
    # El raíl es una cola de milano: ancho máximo (SEMI_RAIL) a `bisel` bajo el plano superior y vuelve al ancho del
    # plano a `2 * bisel`. La cara interior de la mordaza lo sigue con 0,4 mm de holgura (el sondeo del ensamblador es de 0,5 mm; antes se hundía 0,9 mm en
    # el raíl y el ensamblador lo marcaba como colisión).
    semi_plano = e.PICATINNY_ANCHO_PLANO.valor_mm / 2
    bisel = SEMI_RAIL - semi_plano
    for lado in (1, -1):
        pts = [
            (0.0, lado * (SEMI_RAIL + 0.4)),
            (-bisel, lado * (SEMI_RAIL + 0.4)),
            (-2 * bisel, lado * (semi_plano + 0.4)),
            (-profundidad, lado * (semi_plano + 0.4)),
            (-profundidad, lado * (SEMI_RAIL + grueso)),
            (0.0, lado * (SEMI_RAIL + grueso)),
        ]
        # `both=True`: el sentido de la extrusión depende del giro del polígono; así sale centrada y siempre igual.
        jaw = Pos(x0 + largo / 2, 0, 0) * extrude(Plane.YZ * Polygon(*pts, align=None), largo / 2, both=True)
        piezas.append(filetear(jaw, min(1.0, 0.1 * largo)))
    return piezas[0] + piezas[1]


def bulon_apriete(x: float, y: float, z_der: float, z_izq: float) -> Any:
    """Cabeza estriada a la izquierda y tuerca con ranura a la derecha de un bulón transversal (eje Z)."""
    perilla = estriado("z", (x, y, z_izq + 2.2), 4.8, 4.4, 10, 0.5)
    perilla = perilla + Pos(x, y, z_izq + 4.6) * Cylinder(2.6, 1.4)
    tuerca = cilindro_en("z", 3.6, 2.4, (x, y, z_der - 1.2))
    tuerca = tuerca - Pos(x, y, z_der - 2.0) * Cylinder(0.5, 2.0).rotate(Axis.Z, 0)
    return filetear(perilla, 0.4) + tuerca


def base_sobre_rail(x0: float, x1: float, altura: float, ancho: float, *, bulon: bool = True) -> Any:
    """Plataforma lofteada sobre el raíl (de y = 0 a `altura`) con mordazas, taco de retroceso y bulón de apriete."""
    largo = x1 - x0
    cx = (x0 + x1) / 2
    placa = loftear(
        [
            superelipse(0.0, cx, ancho / 2, largo / 2, n=3.4),
            superelipse(0.5 * altura, cx, 0.46 * ancho, 0.47 * largo, n=3.0),
            superelipse(altura, cx, 0.40 * ancho, 0.42 * largo, n=2.8),
        ]
    )
    # Ajusta: la placa nace en y = 0 y sube; el raíl queda debajo.
    cuerpo = placa + mordazas(x0, x1)
    taco = Pos(cx, -e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm / 2, 0) * Cylinder(1.0, 1.0)
    # Taco de retroceso: entra en una ranura Picatinny (5,23 mm de ancho): 0,2 mm de holgura por lado, no más ancho
    # que la ranura (antes medía 6,4 mm y se hundía 0,6 mm en cada diente del raíl).
    semi_taco = e.PICATINNY_ANCHO_RANURA.valor_mm / 2 - 0.2
    cuerpo = cuerpo + Pos(cx, -1.7, 0) * extrude(
        Plane.XY * Polygon((-semi_taco, -1.3), (semi_taco, -1.3), (semi_taco, 1.3), (-semi_taco, 1.3), align=None),
        8.0 / 2,
        both=True,
    )
    _ = taco
    if bulon:
        z_ext = SEMI_RAIL + 3.5
        cuerpo = cuerpo + bulon_apriete(x0 + 0.72 * largo, -4.2, -z_ext, z_ext)
    return cuerpo


def lente(radio: float, x: float, y: float, z: float, grosor: float = 0.9) -> Any:
    """Cristal: disco fino con el eje en X (se suelda a la pared del tubo con un solape de 0,3 mm)."""
    return cilindro_en("x", radio + 0.3, grosor, (x, y, z))


def cuerpo_tubular(
    perfil: Sequence[tuple[float, float]],
    y_eje: float,
    *,
    hueco_trasero: tuple[float, float] | None = None,
    hueco_delantero: tuple[float, float] | None = None,
    z_eje: float = 0.0,
) -> Any:
    """Tubo de revolución a lo largo de X colocado en altura `y_eje`, con los huecos de las lentes si se piden.

    `hueco_*` = (radio, profundidad): taladro ciego en cada extremo; las lentes se añaden aparte con `lente`.
    """
    tubo = revolucion_x(perfil)
    x_min, x_max = perfil[0][0], perfil[-1][0]
    if hueco_trasero is not None:
        r, prof = hueco_trasero
        tubo = tubo - cilindro_en("x", r, prof, (x_min + prof / 2 - 0.01, 0.0, 0.0))
    if hueco_delantero is not None:
        r, prof = hueco_delantero
        tubo = tubo - cilindro_en("x", r, prof, (x_max - prof / 2 + 0.01, 0.0, 0.0))
    return Pos(0, y_eje, z_eje) * tubo


def solido_valido(s: Solid | Any) -> bool:
    return bool(getattr(s, "is_valid", True)) and s.volume > 0


def seccion_x(x: float, cy: float, hy: float, hz: float, *, cz: float = 0.0, n: float = 3.4, k: int = 32) -> Any:
    """Sección cerrada y lisa en el plano X = `x`: alto `±hy` en Y y ancho `±hz` en Z (superelipse de exponente `n`).

    Misma topología para todas las secciones: dos de ellas se unen con `loftear` para crear cuerpos a lo largo de X.
    """
    pts = []
    for i in range(k):
        t = math.tau * i / k
        c, s = math.cos(t), math.sin(t)
        pts.append(
            (
                x,
                cy + hy * math.copysign(abs(s) ** (2 / n), s),
                cz + hz * math.copysign(abs(c) ** (2 / n), c),
            )
        )
    return Wire([Spline(*pts, periodic=True)])


def prisma_redondeado(x0: float, x1: float, cy: float, hy: float, hz: float, *, cz: float = 0.0, n: float = 4.0) -> Any:
    """Prisma de esquinas redondeadas a lo largo de X (loft de dos secciones iguales)."""
    return loftear([seccion_x(x0, cy, hy, hz, cz=cz, n=n), seccion_x(x1, cy, hy, hz, cz=cz, n=n)])
