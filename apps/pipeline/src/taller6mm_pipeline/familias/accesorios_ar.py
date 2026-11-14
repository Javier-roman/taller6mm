"""Familias de accesorios del M4: empuñadura vertical (de poste o angular) y palanca de armado (charging handle).

Ejes: +X boca, +Y arriba, +Z izquierda. Medidas = cotas del SKU (sin ellas, T0 sin malla). Textura, mecanismo del
pestillo y sujeción interna no se modelan; las proporciones de silueta son estimadas.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from build123d import Align, Box, Cylinder, Pos, Rot

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm

INTERFAZ_ASA_CARGA = "montaje-asa-carga-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)


class EmpunaduraVertical(Familia):
    id = "accesorio.empunadura_vertical"
    nombre = "Empuñadura vertical"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    material = "mat.polimero_negro"
    parametros = (
        Parametro("longitud_total", "Longitud de la base al extremo del poste", float, "mm", 50, 160, de_sku=True),
        Parametro("diametro", "Diámetro del poste", float, "mm", 20, 45, de_sku=True),
        Parametro("largo_base", "Longitud de la base sobre el raíl", float, "mm", 20, 80, de_sku=True),
        Parametro("alto_base", "Altura de la base", float, "mm", 10, 40, de_sku=True),
        Parametro(
            "angulo", "Inclinación del poste hacia delante (0 = vertical)", float, "grados", 0, 45, por_defecto=0.0
        ),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["longitud_total"] is not None
            and p["alto_base"] is not None
            and float(p["longitud_total"]) < float(p["alto_base"]) + 20
        ):
            raise ParametroInvalidoError("longitud_total: debe superar la altura de la base en 20 mm")

    def describir(self, p: Mapping[str, Valor]) -> str:
        tipo = "angular" if float(p["angulo"]) > 0 else "de poste"
        return f"Empuñadura vertical {tipo} de {mm(p, 'longitud_total')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        total, diam = float(p["longitud_total"]), float(p["diametro"])
        lb, hb, ang = float(p["largo_base"]), float(p["alto_base"]), float(p["angulo"])
        ancho_base = e.PICATINNY_ANCHO.valor_mm + 8.0  # abraza el raíl (ancho estimado + 4 mm por lado)
        largo_poste = total - hb
        radio = diam / 2
        base = Pos(0, -hb / 2, 0) * Box(lb, hb, ancho_base)
        poste = (
            Pos(0, -hb, 0)
            * Rot(0, 0, ang)
            * Rot(90, 0, 0)
            * Cylinder(radio, largo_poste, align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        cuerpo = base + poste
        a = math.radians(ang)
        # Cajas de las dos tapas del poste (discos perpendiculares al eje) más la base.
        ext_x = [-lb / 2, lb / 2, -radio * math.cos(a), largo_poste * math.sin(a) + radio * math.cos(a)]
        fondo = -hb - largo_poste * math.cos(a) - radio * math.sin(a)
        nominal = (max(ext_x) - min(ext_x), -fondo, max(ancho_base, diam))
        socket = Socket("rail.agarre", (0.0, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        notas = (
            "Poste liso: sin textura ni tapa. La base es una caja, sin la pinza ni el tornillo de apriete.",
            "El ancho de la base (21,2 + 8 mm) hereda la cota estimada del raíl Picatinny (confianza baja).",
        )
        return Geometria(cuerpo, (socket,), (), notas, nominal, vaciados=0)


class PalancaArmado(Familia):
    id = "sup.palanca_armado"
    nombre = "Palanca de armado (charging handle)"
    requiere = (INTERFAZ_ASA_CARGA,)
    ofrece = ()
    parametros = (
        Parametro("largo_cuerpo", "Longitud del cuerpo (varilla guía)", float, "mm", 80, 200, de_sku=True),
        Parametro("ancho_cuerpo", "Ancho del cuerpo", float, "mm", 10, 30, de_sku=True),
        Parametro("alto", "Altura del cuerpo", float, "mm", 5, 20, de_sku=True),
        Parametro("ancho_total", "Ancho total con la palanca", float, "mm", 30, 90, de_sku=True),
        Parametro("largo_palanca", "Longitud de la palanca (trasera)", float, "mm", 10, 60, de_sku=True),
        Parametro(
            "tipo",
            "Palanca estándar o ambidiestra ampliada",
            str,
            opciones=("estandar", "ambidiestra"),
            por_defecto="estandar",
        ),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["ancho_total"] is not None
            and p["ancho_cuerpo"] is not None
            and float(p["ancho_total"]) <= float(p["ancho_cuerpo"])
        ):
            raise ParametroInvalidoError("ancho_total: debe superar el ancho del cuerpo")

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Palanca de armado {p['tipo']} de {mm(p, 'largo_cuerpo')}, ancho total {mm(p, 'ancho_total')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        lc, ac, alto = float(p["largo_cuerpo"]), float(p["ancho_cuerpo"]), float(p["alto"])
        at, lp = float(p["ancho_total"]), float(p["largo_palanca"])
        ambi = p["tipo"] == "ambidiestra"
        alto_palanca = alto * (1.5 if ambi else 1.0)
        cuerpo = Pos(lc / 2, alto / 2, 0) * Box(lc, alto, ac)
        mitad = (at - ac) / 2
        for lado in (1, -1):
            cuerpo += Pos(-lp / 2, alto_palanca / 2, lado * (ac / 2 + mitad / 2)) * Box(lp, alto_palanca, mitad)
        cuerpo += Pos(-lp / 2, alto / 2, 0) * Box(lp, alto, ac)  # puente entre las dos alas
        socket = Socket("montaje-asa-carga", (0.0, 0.0, 0.0), INTERFAZ_ASA_CARGA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
        notas = (
            "Pestillo, resorte y muescas del cuerpo no se modelan; las alas son cajas de proporciones estimadas.",
            "La palanca ambidiestra amplía el ala 1,5 veces en vertical (estimación de silueta, sin cota de SKU).",
        )
        return Geometria(cuerpo, (socket,), (), notas, (lc + lp, max(alto, alto_palanca), at), vaciados=0)
