"""Cuerpos de la tanda 3: guardamanos HK416, free-float octogonal y MWS; pistolete GBBR; cargadores de M4 con forma.

Ejes: +X boca, +Y arriba, +Z izquierda. Guardamanos: origen en el centro de la cara trasera, sobre el eje del cañón
(avanzan hacia +X). Pistolete: como `EmpunaduraPistolete` (cuelga de la cara de montaje). Cargador: origen en el centro
de la boca superior (donde entra al pozo), cuelga hacia -Y y se curva hacia +X.

No edita `guardamanos_*.py`, `empunaduras.py` ni `cargador_m4.py`: reutiliza sus piezas (`solido_rail`, la familia
`EmpunaduraPistolete`, la familia `CargadorM4`). El cargador hereda de `CargadorM4` solo los parámetros y el motivo de
la interfaz: aquí sí lleva malla, pero es una silueta estimada y de barrido (el plano del STANAG 4179 no es público),
así que nunca pasa de T1 ni se publica.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Box, Plane, Pos, Rot, SlotOverall, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.cargador_m4 import CargadorM4
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.empunaduras import EmpunaduraPistolete
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, loftear, superelipse
from taller6mm_pipeline.familias.rail_picatinny import NOTA_PERFIL, longitud_rail_mm, solido_rail
from taller6mm_pipeline.familias.tanda3_comun import estimada, estriado, nominales, revolucion_x, seccion_x

INTERFAZ_UNION = "tuerca-guardamanos-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
TIPOS_GM = ("hk416", "octogonal", "mws")


def _ranuras_laterales(n: int, x0: float, paso: float, largo: float, alto: float, y: float, ancho: float) -> Any:
    """`n` ranuras de ventilación alargadas que atraviesan las dos paredes laterales (eje Z)."""
    corte = None
    for i in range(n):
        ranura = Pos(x0 + i * paso, y, 0.0) * extrude(Plane.XY * SlotOverall(largo, alto), ancho / 2, both=True)
        corte = ranura if corte is None else corte + ranura
    return corte


def _rail_en(cara: tuple[float, float], x0: float, n: int, y_base: float) -> Any:
    """Raíl de `n` ranuras en una cara del guardamanos (ángulo en grados) que empieza en `x0`."""
    giro, _ = cara
    rail = solido_rail(n, e.PICATINNY_ALTURA.valor_mm + 1.0, longitud_rail_mm(n))
    return Rot(giro, 0, 0) * Pos(x0, y_base, 0) * rail


class GuardamanosTanda3(Familia):
    id = "guardamanos.tanda3"
    nombre = "Guardamanos HK416, free-float octogonal o MWS"
    material = "mat.anodizado_negro"
    requiere = (INTERFAZ_UNION,)
    ofrece = (e.INTERFAZ_PICATINNY,)
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("tipo", "Tipo de guardamanos", str, opciones=TIPOS_GM, por_defecto="hk416"),
        Parametro("longitud", "Longitud total", float, "mm", 150, 420, de_sku=True),
        Parametro(
            "diametro_exterior", "Diámetro exterior (entre caras en el octogonal)", float, "mm", 30, 60, de_sku=True
        ),
        Parametro("grosor_pared", "Grosor de la pared", float, "mm", 2, 6, de_sku=True),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        d, t = p["diametro_exterior"], p["grosor_pared"]
        if d is not None and t is not None and float(t) > float(d) / 4:
            raise ParametroInvalidoError("grosor_pared: demasiado grueso para el diámetro")

    def describir(self, p: Mapping[str, Valor]) -> str:
        nombres = {"hk416": "estilo HK416", "octogonal": "free-float octogonal", "mws": "estilo MWS"}
        return f"Guardamanos {nombres[str(p['tipo'])]} de {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        tipo, L, D, t = str(p["tipo"]), float(p["longitud"]), float(p["diametro_exterior"]), float(p["grosor_pared"])  # noqa: N806
        r = D / 2
        ri = r - t
        cuerpo = self._octogonal(L, r, ri) if tipo == "octogonal" else self._redondo(tipo, L, r, ri)
        n_top = max(3, int((L - 20.0) // e.PICATINNY_PASO.valor_mm))
        y_top = r - 1.2
        cuerpo = cuerpo + _rail_en((0.0, 0.0), 8.0, n_top, y_top)
        sockets = [
            Socket("union-receptor", (0.0, 0.0, 0.0), INTERFAZ_UNION, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            Socket(
                "rail.top",
                (8.0, y_top + e.PICATINNY_ALTURA.valor_mm + 1.0, 0.0),
                e.INTERFAZ_PICATINNY,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {"longitud_mm": longitud_rail_mm(n_top), "ranuras": n_top},
            ),
        ]
        # Raíles cortos delanteros a las 3, 6 y 9 horas (el HK416 y el MWS; el octogonal los lleva en las caras).
        n_corto = max(2, int(0.35 * L // e.PICATINNY_PASO.valor_mm))
        x_corto = L - 12.0 - longitud_rail_mm(n_corto)
        for cara, giro, normal in (
            ("l", 90.0, (0.0, 0.0, 1.0)),
            ("bottom", 180.0, (0.0, -1.0, 0.0)),
            ("r", 270.0, (0.0, 0.0, -1.0)),
        ):
            cuerpo = cuerpo + _rail_en((giro, 0.0), x_corto, n_corto, y_top)
            nx, ny, nz = normal
            alto = y_top + e.PICATINNY_ALTURA.valor_mm + 1.0
            sockets.append(
                Socket(
                    f"rail.{cara}",
                    (x_corto, round(ny * alto, 4), round(nz * alto, 4)),
                    e.INTERFAZ_PICATINNY,
                    (nx, ny, nz),
                    (1.0, 0.0, 0.0),
                    {"longitud_mm": longitud_rail_mm(n_corto), "ranuras": n_corto},
                )
            )
        notas = (
            NOTA_PERFIL,
            "Estrechamiento, ranuras de ventilación, collarín y tornillos de sujeción estimados, sin cota de SKU.",
            "La unión al receptor (tuerca de cañón) y el cañón interior no se modelan.",
        )
        cotas = (estimada("guardamanos.radio_interior", ri),)
        return Geometria(cuerpo, tuple(sockets), cotas, notas, nominales(cuerpo), vaciados=8)

    @staticmethod
    def _redondo(tipo: str, L: float, r: float, ri: float) -> Any:  # noqa: N803
        """Tubo estrechado (loft de secciones casi redondas) con el collarín trasero, ranuras y tornillos."""
        n = 2.6 if tipo == "hk416" else 2.15
        fr = 0.90 if tipo == "hk416" else 0.97  # el HK se afina más hacia delante
        tubo = loftear(
            [
                seccion_x(0.0, 0.0, r * 1.02, r * 1.02, n=n),
                seccion_x(0.35 * L, 0.0, r, r, n=n),
                seccion_x(0.78 * L, 0.0, r * 0.5 * (1 + fr), r * 0.5 * (1 + fr), n=n),
                seccion_x(L, 0.0, r * fr, r * fr, n=n),
            ]
        )
        cuerpo = tubo - cilindro_en("x", ri, L + 2.0, (L / 2, 0.0, 0.0))
        # Collarín trasero (anillo estriado) y tapa frontal con un resalte.
        collar = revolucion_x([(0.0, 0.0), (0.0, r + 2.5), (0.07 * L, r + 2.5), (0.09 * L, r + 0.4), (0.09 * L, 0.0)])
        collar = collar - cilindro_en("x", ri, 0.09 * L + 1.0, (0.045 * L, 0.0, 0.0))
        cuerpo = cuerpo + filetear(collar, 0.6)
        cuerpo = (
            cuerpo
            + estriado("x", (0.03 * L, 0.0, 0.0), r + 2.9, 0.05 * L, 40, 0.5)
            - cilindro_en("x", ri, 0.05 * L + 1.0, (0.03 * L, 0.0, 0.0))
        )
        for k in range(3):  # tornillos radiales de sujeción del collarín, a 120 grados
            tornillo = filetear(cilindro_en("y", 2.4, 3.0, (0.0, r + 3.6, 0.0)), 0.3)
            cuerpo = cuerpo + Pos(0.06 * L, 0.0, 0.0) * Rot(120.0 * k + 30.0, 0, 0) * tornillo
        # Ranuras de ventilación en la zona central de las paredes laterales.
        if tipo == "hk416":
            n_r = 7
            ranuras = _ranuras_laterales(n_r, 0.22 * L, 0.075 * L, 0.052 * L, 0.34 * r, 0.0, 2 * r + 6)
        else:
            n_r = 6
            ranuras = _ranuras_laterales(n_r, 0.25 * L, 0.07 * L, 0.04 * L, 0.38 * r, 0.0, 2 * r + 6)
        cuerpo = cuerpo - ranuras
        # Tapa frontal: aro con resalte.
        aro = revolucion_x([(L - 0.025 * L, 0.0), (L - 0.025 * L, r * fr + 1.2), (L, r * fr + 1.2), (L, 0.0)])
        aro = aro - cilindro_en("x", ri, 0.025 * L + 2.0, (L - 0.012 * L, 0.0, 0.0))
        return cuerpo + filetear(aro, 0.5)

    @staticmethod
    def _octogonal(L: float, r: float, ri: float) -> Any:  # noqa: N803
        """Octógono extruido con las aristas redondeadas, tuerca de cañón trasera y ranuras en las caras laterales."""
        R = r / math.cos(math.radians(22.5))  # noqa: N806 - radio de circunscrita para que `D` sea entre caras
        pts = [(R * math.cos(math.radians(22.5 + 45 * k)), R * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
        from build123d import Polygon

        prisma = extrude(Plane.YZ * Polygon(*pts, align=None), (L - 12.0) / 2, both=True)
        prisma = Pos((L - 12.0) / 2 + 12.0, 0, 0) * prisma
        aristas = [ed for ed in prisma.edges() if abs(ed.length - (L - 12.0)) < 0.5]
        prisma = filetear(prisma, min(2.0, 0.12 * r), aristas)
        cuerpo = prisma - cilindro_en("x", ri, L + 2.0, (L / 2, 0.0, 0.0))
        # Tuerca de cañón: anillo con dos planos para la llave y tres tornillos radiales.
        tuerca = revolucion_x([(0.0, 0.0), (0.0, r + 1.5), (12.0, r + 1.5), (12.0, 0.0)])
        tuerca = tuerca - cilindro_en("x", ri, 14.0, (6.0, 0.0, 0.0))
        for lado in (1, -1):
            tuerca = tuerca - Pos(6.0, 0.0, lado * (r + 1.5 + 0.1)) * Box(4.0, 2 * r + 4, 3.0)
        cuerpo = cuerpo + filetear(tuerca, 0.5)
        # Ranuras de ventilación en las cuatro caras no ocupadas por raíles (lados): estadio largo y poco profundo.
        cuerpo = cuerpo - _ranuras_laterales(5, 0.28 * L, 0.12 * L, 0.08 * L, 0.34 * r, 0.0, 2 * r + 6)
        # Tapa delantera achaflanada.
        return cuerpo


class PistoleteGbbr(EmpunaduraPistolete):
    id = "empunadura.pistolete_gbbr"
    version = 1
    nombre = "Pistolete AR de GBBR"

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Pistolete AR de GBBR ({str(p['perfil']).upper()}) de {mm(p, 'altura')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        base = super().construir(p)
        alto, prof, ancho = float(p["altura"]), float(p["profundidad"]), float(p["ancho"])
        cuerpo = base.solido
        # Dorso con cinco rebajes horizontales poco profundos (agarre trasero) y llanta del tornillo del cuello.
        desplaza = alto * math.tan(math.radians(float(p["inclinacion"])))
        for k in range(5):
            u = 0.30 + 0.10 * k
            x = -desplaza * u - 0.04 * prof * u - 0.5 * prof * 0.82
            cuerpo = cuerpo - Pos(x, -u * alto, 0.0) * Box(2.4, 2.2, 0.62 * ancho)
        # Mejilla del pulgar: resalte lofteado en el lado izquierdo, para distinguirlo del pistolete de AEG.
        cuerpo = cuerpo + loftear(
            [
                seccion_x(-0.18 * prof, -0.22 * alto, 8.0, 2.4, cz=ancho / 2 - 1.6, n=2.6),
                seccion_x(-0.05 * prof, -0.20 * alto, 10.0, 3.0, cz=ancho / 2 - 1.0, n=2.6),
                seccion_x(0.10 * prof, -0.22 * alto, 8.0, 2.4, cz=ancho / 2 - 1.6, n=2.6),
            ]
        )
        notas = (
            *base.notas,
            "Variante de GBBR: la diferencia real de interfaz con el pistolete de AEG (tornillo y cuello) no tiene "
            "fuente y no se modela; los rebajes y la mejilla son distintivos estimados.",
        )
        return Geometria(cuerpo, base.sockets, base.cotas, notas, nominales(cuerpo), base.vaciados + 3)


class CargadorM4Forma(CargadorM4):
    """Cargador de M4 con silueta curva estimada. Hereda de `CargadorM4` los parámetros y la interfaz del pozo."""

    id = "cargador.m4_forma"
    nombre = "Cargador de M4 (silueta curva estimada)"
    motivo_sin_malla = None

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cargador de M4 ({p['sistema']}) de {p['capacidad']} bolas, silueta estimada"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        H, hx, hz = float(p["altura"]), float(p["largo"]) / 2, float(p["ancho"]) / 2  # noqa: N806
        capacidad = int(p["capacidad"])
        curva = 0.20 * H if capacidad < 200 else 0.14 * H  # el de alta capacidad es más ancho y se curva menos
        puntos = (0.0, 0.025, 0.09, 0.25, 0.5, 0.75, 0.93, 0.985, 1.0)
        secciones = []
        for u in puntos:
            cx = curva * u * u
            # El cuerpo se ensancha un poco hacia abajo; la boca (u = 0) es más estrecha: labios de alimentación.
            f = 0.90 if u < 0.01 else 1.0 + 0.05 * u
            y = -u * H
            if u >= 0.985:
                f *= 1.04  # placa de base ligeramente más grande
            secciones.append(superelipse(y, cx, hz * f, hx * f, n=4.2))
        cuerpo = loftear(secciones)
        # Boca de alimentación: bolsillo hondo (el interior real no se modela, pero la abertura se ve).
        cuerpo = cuerpo - Pos(0.0, -4.0, 0.0) * Box(2 * hx * 0.72, 9.0, 2 * hz * 0.70)
        # Rebajes laterales: seis ranuras alargadas poco profundas en cada lado, siguiendo la curva.
        n_r = 6 if capacidad < 200 else 8
        for i in range(n_r):
            u = 0.20 + 0.70 * i / (n_r - 1)
            cx = curva * u * u
            ranura = (
                Pos(cx, -u * H, 0.0)
                * Rot(0, 0, math.degrees(math.atan(2 * curva * u / H)) * -1)
                * extrude(Plane.XY * SlotOverall(0.78 * 2 * hx, 0.045 * H), (hz * 2 + 2.0) / 2, both=True)
            )
            # Resta solo 0,8 mm de cada pared: se limita con la caja de la sección (más estrecha que el hueco).
            envuelta = Pos(cx, -u * H, 0.0) * Box(2 * hx + 4, 0.2 * H, 2 * hz - 1.6)
            cuerpo = cuerpo - (ranura - envuelta)
        # Placa de base con la pestaña de tirar en el frente.
        u1 = 1.0
        cx1 = curva * u1 * u1
        cuerpo = cuerpo + filetear(Pos(cx1 + hx * 1.1, -H + 3.0, 0.0) * Box(7.0, 5.0, 0.7 * 2 * hz), 1.2)
        if p["sistema"] == "gbb":  # válvula de carga de gas delante de la placa de base
            cuerpo = cuerpo + filetear(cilindro_en("y", 3.2, 6.0, (cx1 + hx * 0.7, -H - 2.0, 0.0)), 0.5)
            cuerpo = cuerpo + filetear(cilindro_en("y", 1.6, 2.0, (cx1 + hx * 0.7, -H - 5.0, 0.0)), 0.3)
        notas = (
            "Silueta curva, ensanche, labios, ranuras y placa de base estimados, sin plano (STANAG 4179 no público).",
            "Los cargadores de AEG y de GBBR no son intercambiables; aquí solo cambia la válvula de gas.",
            "La capacidad en bolas no se convierte en medidas: largo, ancho y altura son parámetros de barrido.",
        )
        sockets = (Socket("pozo", (0.0, 0.0, 0.0), "pozo-stanag-m4", (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),)
        cotas = (estimada("cargador.curvatura_total", curva),)
        return Geometria(cuerpo, sockets, cotas, notas, nominales(cuerpo), vaciados=n_r + 1)
