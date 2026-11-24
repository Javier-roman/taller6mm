"""Familias de accesorios del M4: empuñadura vertical (de poste o angular) y palanca de armado (charging handle).

Ejes: +X boca, +Y arriba, +Z izquierda. Medidas = cotas del SKU (sin ellas, T0 sin malla).

La empuñadura lleva una base lofteada con la ranura del raíl y el tornillo de apriete, y un poste de revolución con
anillos y los extremos redondeados. La palanca tiene el cuerpo guía con la nariz redondeada, la pala con las alas
curvas y estriadas, y el pestillo (con su eje) alojado en un rebaje. Las proporciones de silueta son estimadas, sin
cota de SKU; el mecanismo interno del pestillo y la sujeción no se modelan.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Box, Line, Pos, Rot, Spline

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, extruir_perfil, filetear, loftear, revolucion, superelipse

INTERFAZ_ASA_CARGA = "montaje-asa-carga-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)


def _perfil_poste(radio: float, largo: float) -> list[tuple[float, float]]:
    """Perfil (radio, y) del poste de abajo arriba, con la cima en y = 0: collar, tres anillos, panza y base redonda."""
    pts: list[tuple[float, float]] = [(0.0, -largo), (0.60 * radio, -largo), (0.86 * radio, -largo + 0.045 * largo)]
    pts.append((0.97 * radio, -0.88 * largo))
    # Anillos: tres surcos poco profundos en la zona de agarre (fracción de la longitud medida desde la cima).
    for centro in (0.66, 0.50, 0.34):
        a, b = centro - 0.035, centro + 0.035
        pts += [
            (radio, -(b + 0.02) * largo),
            (0.90 * radio, -b * largo),
            (0.90 * radio, -a * largo),
            (radio, -(a - 0.02) * largo),
        ]
    pts += [(0.96 * radio, -0.16 * largo), (0.88 * radio, -0.07 * largo), (0.88 * radio, 0.0)]
    return pts


class EmpunaduraVertical(Familia):
    id = "accesorio.empunadura_vertical"
    version = 2  # v2: base lofteada con ranura y tornillo, poste de revolución con anillos (antes, caja y cilindro)
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
        largo_poste = total - hb + 2.0  # entra 2 mm en la base
        radio = diam / 2
        # Base: loft de tres secciones (arriba ancha, abajo más estrecha) con la ranura del raíl en la cara superior.
        base = loftear(
            [
                superelipse(0.0, 0.0, ancho_base / 2, lb / 2, n=3.6),
                superelipse(-0.45 * hb, 0.0, 0.46 * ancho_base, 0.47 * lb, n=3.2),
                superelipse(-hb, 0.0, 0.40 * ancho_base, 0.34 * lb, n=2.6),
            ]
        )
        ranura = extruir_perfil(
            [
                Line((-lb, 0.8), (lb, 0.8)),
                Line((lb, 0.8), (lb, -2.6)),
                Line((lb, -2.6), (-lb, -2.6)),
                Line((-lb, -2.6), (-lb, 0.8)),
            ],
            e.PICATINNY_ANCHO.valor_mm + 0.8,  # 0,4 mm de holgura por lado: la cola de milano no roza la ranura
        )
        base = base - ranura
        # Tornillo de apriete: cabeza estriada rehundida en el lateral izquierdo.
        x_t, y_t = 0.18 * lb, -0.40 * hb
        base = base - cilindro_en("z", 5.2, 3.0, (x_t, y_t, 0.40 * ancho_base))
        cabeza = cilindro_en("z", 4.4, 3.4, (x_t, y_t, 0.40 * ancho_base))
        cabeza = cabeza - Pos(x_t, y_t, 0.40 * ancho_base + 1.4) * Box(8.0, 1.0, 1.4)
        poste = filetear(revolucion(_perfil_poste(radio, largo_poste)), 0.7)
        poste = Pos(0, -hb + 2.0, 0) * Rot(0, 0, ang) * poste
        cuerpo = base + cabeza + poste
        caja = cuerpo.bounding_box()
        nominal = (caja.size.X, caja.size.Y, caja.size.Z)
        socket = Socket("rail.agarre", (0.0, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        notas = (
            "Anillos, collar y base de proporciones estimadas; la pinza del raíl es solo la ranura superior.",
            "El ancho de la base (21,2 + 8 mm) hereda la cota estimada del raíl Picatinny (confianza baja).",
        )
        return Geometria(cuerpo, (socket,), (), notas, nominal, vaciados=4)


def _plano_a_mundo(solido: Any, grosor: float, y0: float = 0.0) -> Any:
    """Pasa un sólido extruido en Z (planta en X, Y) a planta en X, Z con su grosor en Y, apoyado en `y0`."""
    return Pos(0, y0 + grosor / 2, 0) * Rot(90, 0, 0) * solido


class PalancaArmado(Familia):
    id = "sup.palanca_armado"
    version = 2  # v2: cuerpo guía, pala con alas curvas y pestillo con eje (antes, cajas)
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
        alto_p = alto * (1.5 if ambi else 1.0)
        # Cuerpo guía: placa delgada con la nariz redondeada y un canal central rehundido.
        grueso = 0.55 * alto
        nariz = [
            Line((0.0, -ac / 2), (0.86 * lc, -ac / 2)),
            Spline(
                (0.86 * lc, -ac / 2),
                (0.96 * lc, -0.40 * ac),
                (lc, -0.20 * ac),
                (lc, 0.0),
                (lc, 0.20 * ac),
                (0.96 * lc, 0.40 * ac),
                (0.86 * lc, ac / 2),
            ),
            Line((0.86 * lc, ac / 2), (0.0, ac / 2)),
            Line((0.0, ac / 2), (0.0, -ac / 2)),
        ]
        cuerpo = _plano_a_mundo(extruir_perfil(nariz, grueso), grueso)
        cuerpo = filetear(cuerpo, min(1.2, 0.2 * grueso))
        canal = Pos(0.5 * lc, grueso, 0) * Box(0.78 * lc, 0.30 * grueso * 2, 0.34 * ac)
        cuerpo = cuerpo - filetear(canal, 0.6)
        # Pala: planta en T con alas curvas hacia atrás; las alas miden `alto_p` de alto (más en la ambidiestra).
        mitad_c, mitad_t = ac / 2, at / 2
        planta = [
            Spline((0.0, -mitad_c), (-0.10 * lp, -0.5 * (mitad_c + mitad_t)), (-0.34 * lp, -mitad_t)),
            Line((-0.34 * lp, -mitad_t), (-0.92 * lp, -mitad_t)),
            Spline((-0.92 * lp, -mitad_t), (-lp, -0.9 * mitad_t), (-lp, -0.5 * mitad_t)),
            Line((-lp, -0.5 * mitad_t), (-lp, 0.5 * mitad_t)),
            Spline((-lp, 0.5 * mitad_t), (-lp, 0.9 * mitad_t), (-0.92 * lp, mitad_t)),
            Line((-0.92 * lp, mitad_t), (-0.34 * lp, mitad_t)),
            Spline((-0.34 * lp, mitad_t), (-0.10 * lp, 0.5 * (mitad_c + mitad_t)), (0.0, mitad_c)),
            Line((0.0, mitad_c), (0.0, -mitad_c)),
        ]
        pala = _plano_a_mundo(extruir_perfil(planta, alto_p), alto_p)
        pala = filetear(pala, min(2.0, 0.25 * alto_p))
        # Estrías de agarre en las alas: ranuras verticales poco profundas en el borde trasero de cada ala.
        for lado in (1, -1):
            for k in range(4):
                z = lado * (mitad_t - 0.8 - k * 0.12 * (mitad_t - mitad_c) * 2)
                pala = pala - Pos(-0.62 * lp, alto_p, z) * Box(0.45 * lp, 2 * 0.28 * alto_p, 1.0)
        # Rebaje del pestillo y el pestillo con su eje (una palanca con el gancho hacia delante).
        x0, x1 = -0.88 * lp, -0.08 * lp
        pala = pala - Pos(0.5 * (x0 + x1), alto_p, 0) * Box(x1 - x0, 2 * 0.55 * alto_p, 0.50 * ac)
        perfil_pestillo = [
            Line((x0 + 0.04 * lp, 0.50 * alto_p), (x0 + 0.04 * lp, 0.94 * alto_p)),
            Line((x0 + 0.04 * lp, 0.94 * alto_p), (x1 - 0.30 * lp, 0.94 * alto_p)),
            Spline((x1 - 0.30 * lp, 0.94 * alto_p), (x1 - 0.12 * lp, 0.80 * alto_p), (x1 - 0.04 * lp, 0.56 * alto_p)),
            Line((x1 - 0.04 * lp, 0.56 * alto_p), (x1 - 0.20 * lp, 0.50 * alto_p)),
            Line((x1 - 0.20 * lp, 0.50 * alto_p), (x0 + 0.04 * lp, 0.50 * alto_p)),
        ]
        pestillo = filetear(extruir_perfil(perfil_pestillo, 0.42 * ac), 0.5)
        eje = cilindro_en("z", 0.07 * alto_p + 0.4, 0.50 * ac, (x0 + 0.18 * lp, 0.72 * alto_p, 0.0))
        cuerpo = cuerpo + pala + pestillo + eje
        socket = Socket("montaje-asa-carga", (0.0, 0.0, 0.0), INTERFAZ_ASA_CARGA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0))
        notas = (
            "Resorte del pestillo y muescas del cuerpo no se modelan; alas y pestillo de proporciones estimadas.",
            "La palanca ambidiestra amplía el ala 1,5 veces en vertical (estimación de silueta, sin cota de SKU).",
        )
        caja = cuerpo.bounding_box()
        return Geometria(cuerpo, (socket,), (), notas, (caja.size.X, caja.size.Y, caja.size.Z), vaciados=3)
