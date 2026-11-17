"""Accesorios de la tanda 3: linterna, láser y módulo combinado, bípode y mira delantera tipo A2 (poste o torre).

Ejes: +X boca, +Y arriba, +Z izquierda. Linterna, láser y bípode cuelgan del raíl inferior: el origen está en el extremo
trasero de la base, centrado, con la cara inferior del raíl en y = 0 (las mordazas suben por los flancos del raíl y el
accesorio cuelga hacia -Y). La mira delantera tiene el origen en el eje del cañón, en el centro del collarín (torre) o
en la base del poste. Medidas = cotas del SKU; sin ellas, la pieza sale T0 sin malla. Los detalles son estimados
(confianza baja) y no hay marcas ni leyendas: los accesorios son neutros.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Box, Plane, Pos, Rot

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, loftear, revolucion
from taller6mm_pipeline.familias.tanda3_comun import (
    NOTA_PICATINNY,
    base_sobre_rail,
    cuerpo_tubular,
    estimada,
    estriado,
    lente,
    nominales,
    revolucion_x,
    seccion_x,
)

INTERFAZ_LINTERNA = "anclaje-linterna-picatinny"
INTERFAZ_BLOQUE_GAS = "montaje-bloque-gas-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
TIPOS_LUZ = ("linterna", "laser", "combinado")
ALTO_BASE = 9.0  # grosor de la placa de la base bajo el raíl


def base_bajo_rail(x0: float, x1: float, ancho: float, *, bulon: bool = True) -> Any:
    """Base que abraza el raíl desde abajo: la de `base_sobre_rail` volteada (placa hacia -Y y mordazas hacia +Y)."""
    return base_sobre_rail(x0, x1, ALTO_BASE, ancho, bulon=bulon).mirror(Plane.XZ)


def _socket_rail(x: float, interfaz: str = e.INTERFAZ_PICATINNY) -> Socket:
    return Socket("rail", (x, 0.0, 0.0), interfaz, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))


def _linterna(L: float, r: float, y: float, z: float, *, cable: bool) -> Any:  # noqa: N803
    """Cuerpo de linterna con el eje en X a altura `y`: tapa trasera con pulsador, empuñadura estriada y cabeza."""
    rh = 1.28 * r  # radio de la cabeza
    perfil = [
        (0.0, 0.0),
        (0.0, 0.70 * r),
        (0.02 * L, 0.92 * r),
        (0.08 * L, 0.98 * r),
        (0.12 * L, 0.90 * r),
        (0.16 * L, r),
        (0.62 * L, r),
        (0.74 * L, 1.10 * r),
        (0.86 * L, rh),
        (0.985 * L, rh * 1.02),
        (L, rh * 0.96),
        (L, 0.0),
    ]
    cuerpo = cuerpo_tubular(perfil, y, hueco_delantero=(0.84 * rh, 0.26 * L), z_eje=z)
    cuerpo = cuerpo + lente(0.84 * rh, 0.80 * L, y, z)
    # Reflector: cono hueco delante del cristal (anillo cónico de pared fina).
    reflector = revolucion_x(
        [(0.80 * L - 0.01, 0.30 * r), (0.97 * L, 0.80 * rh), (0.97 * L, 0.70 * rh), (0.80 * L - 0.01, 0.20 * r)]
    )
    cuerpo = cuerpo + Pos(0, y, z) * reflector
    # Empuñadura: estrías a lo largo de la zona central.
    cuerpo = cuerpo + filetear(estriado("x", (0.39 * L, y, z), 1.02 * r, 0.40 * L, 48, 0.5), 0.2)
    # Pulsador trasero con anillo y, si lo hay, el puerto del cable del interruptor remoto.
    cuerpo = cuerpo + filetear(cilindro_en("x", 0.38 * r, 3.0, (-1.2, y, z)), 0.8)
    if cable:
        puerto = filetear(cilindro_en("z", 3.4, 4.0, (0.07 * L, y, z + r)), 0.6)
        cuerpo = cuerpo + puerto - cilindro_en("z", 1.5, 3.0, (0.07 * L, y, z + r + 1.5))
    # Bisel almenado: seis muescas en el borde delantero de la cabeza.
    for k in range(6):
        muesca = Pos(0, y, z) * Rot(k * 60.0, 0, 0) * Pos(L - 1.6, rh, 0) * Box(3.4, 2.6, 2.4)
        cuerpo = cuerpo - muesca
    return cuerpo


def _laser(L: float, r: float, y: float, z: float) -> Any:  # noqa: N803
    """Módulo láser: cuerpo lofteado con las ventanas, los tornillos de ajuste y la tapa trasera."""
    cuerpo = loftear(
        [
            seccion_x(0.0, y, 0.90 * r, 0.88 * r, cz=z, n=3.4),
            seccion_x(0.5 * L, y, r, 0.98 * r, cz=z, n=3.4),
            seccion_x(L, y, 0.94 * r, 0.92 * r, cz=z, n=3.4),
        ]
    )
    # Ventanas del haz (dos aperturas redondas, una sobre otra) y rehundido frontal.
    for dy in (0.34 * r, -0.36 * r):
        cuerpo = cuerpo - cilindro_en("x", 0.26 * r, 6.0, (L - 2.9, y + dy, z))
        cuerpo = cuerpo + lente(0.26 * r, L - 4.0, y + dy, z, 0.8)
    # Tornillos de ajuste de elevación (arriba) y deriva (lado), con la ranura en la cabeza.
    cab_y = cilindro_en("y", 0.30 * r, 3.0, (0.62 * L, y + r, z))
    cuerpo = cuerpo + filetear(cab_y, 0.4) - Pos(0.62 * L, y + r + 1.4, z) * Box(0.5 * r, 0.6, 1.0)
    cab_z = cilindro_en("z", 0.30 * r, 3.0, (0.50 * L, y, z - r))
    cuerpo = cuerpo + filetear(cab_z, 0.4) - Pos(0.50 * L, y, z - r - 1.4) * Box(0.5 * r, 1.0, 0.6)
    # Tapa trasera de la pila con ranura y pulsador remoto.
    tapa = filetear(cilindro_en("x", 0.62 * r, 3.0, (-1.2, y, z)), 0.8)
    cuerpo = cuerpo + tapa - Pos(-2.4, y, z) * Box(1.0, 0.5 * r, 1.0)
    return cuerpo


class LuzLaserTactico(Familia):
    id = "accesorio.luz_laser_tactico"
    nombre = "Linterna, láser o módulo combinado"
    material = "mat.anodizado_negro"
    requiere = (INTERFAZ_LINTERNA, e.INTERFAZ_PICATINNY)
    ofrece = ()
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("tipo", "Linterna, láser o módulo combinado", str, opciones=TIPOS_LUZ, por_defecto="linterna"),
        Parametro("longitud", "Longitud total del cuerpo", float, "mm", 40, 190, de_sku=True),
        Parametro("diametro", "Diámetro del cuerpo", float, "mm", 16, 40, de_sku=True),
        Parametro("cable", "Puerto para el interruptor remoto", bool, por_defecto=False),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if p["longitud"] is not None and p["diametro"] is not None and float(p["longitud"]) < 2 * float(p["diametro"]):
            raise ParametroInvalidoError("longitud: debe ser al menos el doble del diámetro")

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"{str(p['tipo']).capitalize()} táctico de {mm(p, 'longitud')} y {mm(p, 'diametro')} de diámetro"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, D, tipo = float(p["longitud"]), float(p["diametro"]), str(p["tipo"])  # noqa: N806
        r = D / 2
        y = -(ALTO_BASE + r + 0.6)  # eje de la luz bajo el raíl
        ancho_base = min(0.95 * D, 30.0)
        if tipo == "linterna":
            cuerpo = _linterna(L, r, y, 0.0, cable=bool(p["cable"]))
        elif tipo == "laser":
            cuerpo = _laser(L, 0.9 * r, y, 0.0)
        else:  # combinado: la linterna cuelga del raíl y el láser va a su izquierda, más corto
            cuerpo = _linterna(L, r, y, 0.0, cable=False)
            cuerpo = cuerpo + _laser(0.55 * L, 0.55 * r, y + 0.2 * r, r + 0.55 * r + 0.5)
        pie = filetear(Pos(0.5 * L, y + r - 0.5, 0.0) * Box(0.55 * L, 3.0, 0.5 * D), 1.0)
        cuerpo = cuerpo + pie + base_bajo_rail(0.08 * L, 0.62 * L, ancho_base)
        notas = (
            "Cuerpo, estrías, cabeza y tornillos de ajuste estimados, sin cota de SKU; el interior no se modela.",
            "No hay emisor ni lámpara funcional: carcasa de réplica con el cristal plano.",
            NOTA_PICATINNY,
        )
        interfaz = INTERFAZ_LINTERNA if tipo != "laser" else e.INTERFAZ_PICATINNY
        sockets = (_socket_rail(0.35 * L, interfaz),)
        cotas = (estimada("luz.altura_eje_bajo_rail", -y),)
        return Geometria(
            cuerpo,
            sockets,
            cotas,
            notas,
            nominales(cuerpo),
            vaciados=6,
        )


def _pata(largo: float, r: float) -> Any:
    """Pata telescópica de tres tramos colgando de y = 0 hacia -Y, con anillos de bloqueo y pie de goma."""
    l1, l2 = 0.42 * largo, 0.34 * largo
    perfil = [  # (radio, y) de abajo (pie) arriba
        (0.0, -largo - 6.0),
        (0.62 * r, -largo - 6.0),
        (0.95 * r, -largo - 4.4),
        (1.15 * r, -largo),
        (1.15 * r, -largo + 4.0),
        (0.66 * r, -largo + 4.8),
        (0.66 * r, -largo + l2 - 1.5),
        (0.86 * r, -largo + l2 - 0.5),
        (0.86 * r, -largo + l2 + 3.0),
        (0.80 * r, -largo + l2 + 3.8),
        (0.80 * r, -l1 - 1.0),
        (1.00 * r, -l1),
        (1.00 * r, -l1 + 3.4),
        (0.94 * r, -l1 + 4.2),
        (0.94 * r, -4.0),
        (r, -2.0),
        (r, 0.0),
        (0.0, 0.0),
    ]
    return revolucion(perfil)


class Bipode(Familia):
    id = "accesorio.bipode"
    nombre = "Bípode de patas abatibles"
    material = "mat.anodizado_negro"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("longitud_pata", "Longitud de cada pata desplegada", float, "mm", 80, 260, de_sku=True),
        Parametro("ancho_base", "Ancho de la base entre bisagras", float, "mm", 30, 70, de_sku=True),
        Parametro(
            "estado",
            "Patas desplegadas o plegadas hacia delante",
            str,
            opciones=("desplegado", "plegado"),
            por_defecto="desplegado",
        ),
        Parametro(
            "montaje",
            "Base con bulón o con palanca de montaje rápido",
            str,
            opciones=("estandar", "rapido"),
            por_defecto="estandar",
        ),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Bípode {p['estado']} de {mm(p, 'longitud_pata')} de pata y montaje {p['montaje']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        Lp, W = float(p["longitud_pata"]), float(p["ancho_base"])  # noqa: N806
        largo_base = 44.0
        xh, yh = 0.50 * largo_base, -(ALTO_BASE + 7.0)  # eje de las bisagras
        # Bloque central lofteado que une la base con las bisagras y el resorte del muelle de las patas.
        puente = loftear(
            [
                seccion_x(0.14 * largo_base, -ALTO_BASE / 2 - 4.0, 7.0, 0.26 * W, n=3.2),
                seccion_x(xh, yh + 1.0, 8.5, 0.52 * W, n=3.6),
                seccion_x(0.86 * largo_base, -ALTO_BASE / 2 - 4.0, 7.0, 0.26 * W, n=3.2),
            ]
        )
        cuerpo = puente + base_bajo_rail(0.0, largo_base, 0.55 * W, bulon=(p["montaje"] == "estandar"))
        # Cilindros de bisagra (eje Z) y un tornillo central estriado.
        cuerpo = cuerpo + filetear(cilindro_en("z", 6.2, W, (xh, yh, 0.0)), 0.6)
        for lado in (1, -1):
            cuerpo = cuerpo + filetear(cilindro_en("z", 4.0, 3.0, (xh, yh, lado * (W / 2 + 1.0))), 0.6)
        if p["montaje"] == "rapido":  # palanca de leva a un lado
            cuerpo = cuerpo + filetear(cilindro_en("z", 4.6, 5.0, (0.2 * largo_base, -3.0, 0.3 * W + 4.0)), 0.6)
            cuerpo = cuerpo + filetear(Pos(0.2 * largo_base + 7.0, -3.0, 0.3 * W + 4.0) * Box(16.0, 4.0, 3.0), 1.0)
        ang = 90.0 if p["estado"] == "plegado" else 0.0
        for lado in (1, -1):
            # Desplegada: abre las patas hacia los lados. Plegada: las gira hacia delante, paralelas al cañón.
            giro = Rot(lado * -12.0, 0, 0) if ang == 0.0 else Rot(0, 0, ang)
            pata = giro * _pata(Lp, 5.0)
            cuerpo = cuerpo + Pos(xh, yh, lado * (W / 2 - 3.0)) * pata
        notas = (
            "Patas, bisagras, anillos de bloqueo y pies estimados, sin cota de SKU; el muelle no se modela.",
            "El ángulo de apertura (12 grados) es un supuesto: no hay medida de ningún SKU.",
            NOTA_PICATINNY,
        )
        sockets = (_socket_rail(0.5 * largo_base),)
        return Geometria(cuerpo, sockets, (estimada("bipode.alto_bisagra", -yh),), notas, nominales(cuerpo), vaciados=5)


class MiraDelanteraA2(Familia):
    id = "mira.delantera_a2"
    nombre = "Mira delantera tipo A2"
    material = "mat.anodizado_negro"
    requiere = (INTERFAZ_BLOQUE_GAS,)
    ofrece = ()
    parametros = (
        Parametro("tipo", "Poste suelto o torre con collarín", str, opciones=("poste", "torre"), por_defecto="torre"),
        Parametro(
            "altura", "Altura total desde el eje del cañón (torre) o la base (poste)", float, "mm", 15, 60, de_sku=True
        ),
        Parametro(
            "diametro_canon", "Diámetro del cañón exterior donde asienta el collarín", float, "mm", 12, 30, de_sku=True
        ),
        Parametro("largo", "Longitud del collarín", float, "mm", 20, 70, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Mira delantera A2 ({p['tipo']}) de {mm(p, 'altura')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        H, Dc, Lc, tipo = float(p["altura"]), float(p["diametro_canon"]), float(p["largo"]), str(p["tipo"])  # noqa: N806
        if tipo == "poste":
            return self._poste(H)
        r = Dc / 2
        # Collarín: tubo con el interior del cañón, borde delantero biselado y resalte de bayoneta debajo.
        collarin = revolucion_x(
            [(0.0, 0.0), (0.0, r + 3.5), (0.12 * Lc, r + 4.2), (0.88 * Lc, r + 4.2), (Lc, r + 3.0), (Lc, 0.0)]
        )
        collarin = collarin - cilindro_en("x", r, Lc + 2.0, (Lc / 2, 0.0, 0.0))
        collarin = filetear(collarin, 0.5)
        # Torre: bloque lofteado que sube del collarín con las dos orejas de protección y el poste central.
        y_top = H - 12.0
        torre = loftear(
            [
                seccion_x(0.25 * Lc, r + 2.0 + 0.5 * (y_top - r), 0.5 * (y_top - r) + 2.0, 0.34 * Lc, n=3.0),
                seccion_x(0.50 * Lc, r + 2.0 + 0.5 * (y_top - r), 0.5 * (y_top - r) + 2.0, 0.36 * Lc, n=3.4),
                seccion_x(0.78 * Lc, r + 2.0 + 0.5 * (y_top - r), 0.5 * (y_top - r) + 2.0, 0.32 * Lc, n=3.0),
            ]
        )
        torre = filetear(torre - Pos(0.5 * Lc, y_top + 0.5, 0.0) * Box(0.5 * Lc, 4.0, 0.2 * Lc), 0.5)
        for lado in (1, -1):  # orejas
            oreja = loftear(
                [
                    seccion_x(0.28 * Lc, y_top + 3.0, 6.0, 1.2, cz=lado * 0.19 * Lc, n=3.0),
                    seccion_x(0.50 * Lc, y_top + 5.5, 8.0, 1.2, cz=lado * 0.19 * Lc, n=3.0),
                    seccion_x(0.72 * Lc, y_top + 3.0, 6.0, 1.2, cz=lado * 0.19 * Lc, n=3.0),
                ]
            )
            torre = torre + oreja
        cuerpo = collarin + torre + self._poste_en(0.5 * Lc, y_top, H - y_top)
        # Tetón de bayoneta bajo el collarín y pasador de sujeción transversal con cabezas.
        cuerpo = cuerpo + filetear(Pos(0.5 * Lc, -(r + 4.2) - 1.5, 0.0) * Box(0.3 * Lc, 5.0, 0.28 * Lc), 0.8)
        cuerpo = cuerpo + filetear(
            cilindro_en("z", 2.0, 2 * (0.25 * Lc + 2.0), (0.40 * Lc, 0.5 * (r + y_top), 0.0)), 0.3
        )
        for lado in (1, -1):
            cuerpo = cuerpo + filetear(
                cilindro_en("z", 3.0, 2.0, (0.40 * Lc, 0.5 * (r + y_top), lado * (0.18 * Lc + 4.0))), 0.4
            )
        notas = (
            "Collarín, torre, orejas y pasador estimados, sin cota de SKU; no se modela la rosca ni el muelle.",
            "El poste va rehundido en la torre: su regulación en altura no se modela.",
        )
        sockets = (Socket("bloque-gas", (0.0, 0.0, 0.0), INTERFAZ_BLOQUE_GAS, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),)
        return Geometria(
            cuerpo, sockets, (estimada("mira.radio_collarin", r + 4.2),), notas, nominales(cuerpo), vaciados=3
        )

    @staticmethod
    def _poste_en(x: float, y: float, sobresale: float) -> Any:
        """Poste de la mira (revolución con eje en Y) con su base en `y`, que sobresale `sobresale` mm."""
        h = max(sobresale, 6.0)
        perfil = [
            (0.0, -4.0),
            (3.4, -4.0),
            (3.4, -1.0),
            (2.6, 0.0),
            (2.2, 0.15 * h),
            (2.2, 0.40 * h),
            (1.9, 0.62 * h),
            (1.5, 0.86 * h),
            (1.1, h - 0.6),
            (0.6, h),
        ]
        return Pos(x, y, 0.0) * filetear(revolucion(perfil), 0.2)

    def _poste(self, H: float) -> Geometria:  # noqa: N803
        # Poste suelto: base con aletas, vástago roscado con garganta y punta cónica; origen en la base.
        base = cilindro_en("y", 5.6, 4.0, (0.0, 2.0, 0.0))
        base = filetear(base, 0.6)
        vastago = Pos(0.0, 4.0, 0.0) * filetear(revolucion(self._perfil_roscado(H - 4.0)), 0.15)
        orejas = []
        for lado in (1, -1):
            oreja = loftear(
                [
                    seccion_x(-5.0, 9.0, 6.0, 1.2, cz=lado * 5.2, n=3.0),
                    seccion_x(0.0, 11.0, 8.0, 1.2, cz=lado * 5.2, n=3.0),
                    seccion_x(5.0, 9.0, 6.0, 1.2, cz=lado * 5.2, n=3.0),
                ]
            )
            orejas.append(oreja)
        cuerpo = base + vastago + orejas[0] + orejas[1]
        notas = (
            "Vástago roscado, base y orejas estimados, sin cota de SKU; la rosca es un perfil de dientes de sierra.",
            "Sin marcas ni leyendas.",
        )
        sockets = (Socket("bloque-gas", (0.0, 0.0, 0.0), INTERFAZ_BLOQUE_GAS, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),)
        return Geometria(cuerpo, sockets, (estimada("poste.altura", H),), notas, nominales(cuerpo), vaciados=2)

    @staticmethod
    def _perfil_roscado(largo: float) -> list[tuple[float, float]]:
        pts = [(0.0, 0.0), (2.6, 0.0)]
        n = int(0.55 * largo / 1.0)
        for i in range(n):  # dientes de sierra de 1 mm de paso en el 55 % inferior del vástago
            y = 0.5 + i * 1.0
            pts += [(2.6, y), (2.1, y + 0.5)]
        y0 = 0.5 + n * 1.0
        pts += [(2.6, y0), (1.9, y0 + 0.12 * largo), (1.4, largo - 3.0), (0.9, largo - 0.6), (0.0, largo)]
        return pts


_ = (math, loftear, ParametroInvalidoError)
