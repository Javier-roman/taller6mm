"""Familia AK de airsoft: receptor estampado, tapa de receptor, pistolete y cargador curvo.

Ejes canónicos: +X boca, +Y arriba, +Z izquierda del tirador. Solo formas exteriores (sin internos). Todas las cotas
de forma son proporciones estimadas (confianza baja): ninguna es la medida de un SKU, así que las piezas salen
`es_demo`, T0 y no publicables. Sin marcajes, logos ni leyendas.

- Receptor: origen en el eje del cañón, sobre la cara delantera; el cuerpo avanza hacia -X.
- Tapa: origen en el centro de su borde delantero, sobre el plano de apoyo (Y = 0); avanza hacia -X.
- Pistolete: origen en el centro de la cara de montaje (arriba); cuelga hacia -Y y se inclina hacia atrás.
- Cargador: origen en el centro de la boca (labios de alimentación); baja curvándose hacia +X.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Box, Pos, Rot

from taller6mm_pipeline.familias.ak_formas import (
    caja_redonda,
    cilindro_x,
    cilindro_y,
    estimada,
    loft_x,
    remache,
    seccion_curva,
)
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm, prisma
from taller6mm_pipeline.familias.detalle import nominales_de
from taller6mm_pipeline.familias.formas import filetear, interpolar, loftear, superelipse
from taller6mm_pipeline.familias.rail_picatinny import NOTA_PERFIL, longitud_rail_mm, solido_rail

INT_CANON = "montaje-canon-ak"  # propuesta (aún no está en interfaces.json)
INT_TAPA = "montaje-tapa-ak"
INT_GUARDAMANOS = "montaje-guardamanos-ak"
INT_PISTOLETE = "montaje-pistolete-ak"
INT_POZO = "pozo-ak"
INT_CULATA = "montaje-culata-ak"
INT_PICATINNY = "picatinny-mil-std-1913"


class ReceptorAK(Familia):
    id = "ak.receptor"
    nombre = "Receptor AK estampado"
    material = "mat.acero_negro"
    requiere = ()
    ofrece = (INT_CANON, INT_TAPA, INT_GUARDAMANOS, INT_PISTOLETE, INT_POZO, INT_CULATA)
    parametros = (
        Parametro(
            "longitud", "Longitud del receptor (de la cara delantera a la trasera)", float, "mm", 250, 450, de_sku=True
        ),
        Parametro("alto", "Alto del cuerpo estampado (sin tapa)", float, "mm", 38, 58, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", 28, 46, de_sku=True),
        Parametro("nervaduras", "Nervaduras prensadas y ventana de eyección", bool, por_defecto=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Receptor AK estampado de {mm(p, 'longitud')} y {mm(p, 'ancho')} de ancho"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, ancho = float(p["longitud"]), float(p["alto"]), float(p["ancho"])
        hw = ancho / 2
        yt, yb = 0.38 * alto, -0.62 * alto
        cuerpo = loft_x(
            -largo,
            -52,
            [(-largo, yt - 1.5, yb + 1.5, hw * 0.96), (-largo * 0.5, yt, yb, hw), (-52, yt, yb, hw)],
            radio=5.0,
        )
        # Cuna delantera (trunnion): más ancha y redondeada alrededor del cañón.
        cuerpo = cuerpo + loft_x(
            -58,
            0,
            [(-58, yt + 1.5, yb + 3, hw + 0.6), (-20, yt + 2, yb + 3.5, hw + 1.0), (0, yt + 1.0, yb + 4.5, hw + 0.2)],
            radio=9.0,
        )
        # Espiga trasera para la culata.
        cuerpo = cuerpo + caja_redonda(-largo - 18, -largo + 14, yt - 15, yt - 3, -7.5, 7.5, 3.0, ejes="y")
        x_mag = -0.36 * largo  # borde delantero del pozo
        x_mag_t = x_mag - 45.0
        vaciados = 0
        cuerpo = cuerpo - cilindro_x(8.6, -16, 0.5)  # alojamiento del cañón
        cuerpo = cuerpo - caja_redonda(x_mag_t, x_mag, yb - 1, yb + 42, -13.5, 13.5, 3.0, ejes="y")  # pozo
        vaciados += 2
        if p["nervaduras"]:
            # Ventana de eyección en el lateral derecho (-Z), rebajada.
            cuerpo = cuerpo - caja_redonda(-0.68 * largo, -0.30 * largo, yt - 27, yt - 3, -hw - 1, -hw + 5, 3.5)
            # Nervaduras prensadas: surco largo a media altura y tres cortos tras el pozo, a ambos lados.
            for lado in (1, -1):
                z0, z1 = (hw - 1.4, hw + 2) if lado > 0 else (-hw - 2, -hw + 1.4)
                cuerpo = cuerpo - caja_redonda(-0.33 * largo, -14, yb + 12, yb + 17, z0, z1, 1.4)
                for i in range(3):
                    x = -0.52 * largo - i * 11.0
                    cuerpo = cuerpo - caja_redonda(x - 2, x + 2, yb + 3, yb + 17, z0, z1, 1.8)
                vaciados += 4
            vaciados += 1
        # Guardamonte: tira rebordeada con dos remaches.
        x1 = x_mag_t - 2.0
        x2 = x1 - 52.0
        exterior = prisma([(x1, yb + 3), (x1 - 2, yb - 22), (x2 + 4, yb - 24), (x2, yb + 3)], 7.0)
        interior = prisma([(x1 - 4, yb + 4), (x1 - 5.5, yb - 17), (x2 + 6, yb - 19.5), (x2 + 4, yb + 4)], 12.0)
        guarda = filetear(exterior - interior, 2.0, [e for e in (exterior - interior).edges() if _paralela_z(e)])
        cuerpo = cuerpo + guarda
        # Remaches: cuna delantera (3 por lado), espiga trasera (2 por lado) y guardamonte.
        puntos = [
            (-18, yt - 4, hw + 0.9),
            (-18, yb + 8, hw + 0.9),
            (-38, yb + 10, hw + 0.9),
            (-largo + 12, yt - 6, hw * 0.96),
            (-largo + 12, yb + 8, hw * 0.96),
            (x1 - 2, yb + 1.5, hw),
            (x2 + 5, yb + 1.5, hw),
        ]
        for x, y, z in puntos:
            cuerpo = cuerpo + remache(x, y, z - 0.3, 1) + remache(x, y, -(z - 0.3), -1)
        vaciados += len(puntos)
        x_grip = x2 - 18.0
        sockets = (
            Socket("barrel", (0.0, 0.0, 0.0), INT_CANON, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
            Socket("handguard", (-30.0, yb + 14, 0.0), INT_GUARDAMANOS, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
            Socket("dust_cover", (0.0, yt, 0.0), INT_TAPA, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket("mag_well", ((x_mag + x_mag_t) / 2, yb, 0.0), INT_POZO, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket("grip", (x_grip, yb, 0.0), INT_PISTOLETE, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket("stock", (-largo - 18, yt - 9, 0.0), INT_CULATA, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
        )
        cotas = (estimada("receptor.y_eje_sobre_base", -yb), estimada("receptor.x_pozo_desde_cara", -x_mag))
        notas = (
            "Solo forma exterior: el interior estampado (carriles, gearbox) no se modela; el cuerpo es macizo.",
            "Perfil, nervaduras, ventana, guardamonte y posición del pozo estimados (confianza baja).",
        )
        return Geometria(cuerpo, sockets, cotas, notas, nominales_de(cuerpo), vaciados=vaciados)


def _paralela_z(e: Any) -> bool:
    d = e.end_point() - e.start_point()
    return abs(d.X) < 1e-6 and abs(d.Y) < 1e-6 and abs(d.Z) > 1e-6


class TapaAK(Familia):
    id = "ak.tapa"
    tolerancia_mm = 0.02  # cúpula casi plana: teselado fino para que no se vea facetada
    tolerancia_angular = 0.2
    nombre = "Tapa de receptor AK"
    material = "mat.acero_negro"
    requiere = (INT_TAPA,)
    ofrece = ()
    parametros = (
        Parametro("longitud", "Longitud de la tapa", float, "mm", 180, 380, de_sku=True),
        Parametro("alto", "Alto de la cúpula sobre el apoyo", float, "mm", 12, 30, de_sku=True),
        Parametro("ancho", "Ancho en el apoyo", float, "mm", 28, 46, de_sku=True),
        Parametro("nervaduras", "Nervaduras transversales prensadas", int, "ud", 0, 6, por_defecto=2),
        Parametro("rail", "Raíl Picatinny superior", bool, por_defecto=False),
    )

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (INT_PICATINNY,) if p["rail"] else ()

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Tapa de receptor AK de {mm(p, 'longitud')}" + (" con raíl" if p["rail"] else "")

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, ancho = float(p["longitud"]), float(p["alto"]), float(p["ancho"])
        w = ancho / 2
        # Alzado de la cúpula: baja hacia los dos extremos (fracciones de la longitud, de atrás adelante). La chapa
        # estampada real se estrecha y baja hacia delante (hacia el tubo de gases) y trae un escalón trasero.
        perfil = (
            (0.0, 0.5, 0.8),
            (0.07, 0.8, 0.95),
            (0.3, 1.0, 1.0),
            (0.6, 0.95, 0.96),
            (0.84, 0.66, 0.78),
            (1.0, 0.5, 0.62),
        )
        nudos = [(-largo * (1 - f), alto * k, -alto * k, w * kw) for f, k, kw in perfil]
        radio = alto * 0.95
        cupula = loft_x(-largo, 0, nudos, radio=radio)
        # Chapa de 1,4 mm: el interior se vacía por debajo (abierto delante y por la base, cerrado atrás).
        grosor = 1.4
        interior = loft_x(
            -largo + grosor,
            1.0,
            [(x, yt - grosor, yb, sw - grosor) for x, yt, yb, sw in nudos],
            radio=radio - grosor,
        )
        cuerpo = (cupula - interior) - Pos(-largo / 2, -alto - 5, 0) * Box(largo + 40, 2 * alto + 10, ancho + 20)
        # Reborde inferior a cada lado, con la muesca trasera para la palanca de retención.
        for lado in (1, -1):
            za, zb = sorted((lado * (w - 0.4), lado * (w + 2.6)))
            cuerpo = cuerpo + caja_redonda(-largo * 0.93, -largo * 0.05, 0.0, 1.3, za, zb, 0.5, ejes="y")
            za, zb = sorted((lado * (w - 3.0), lado * (w + 4.0)))
            cuerpo = cuerpo - caja_redonda(-largo * 0.8, -largo * 0.7, -1.0, 2.0, za, zb, 1.0, ejes="y")
        # Casquillo trasero de la varilla del muelle, con su orificio.
        cuerpo = cuerpo + cilindro_x(5.8, -largo - 5, -largo + 12, alto * 0.5)
        cuerpo = cuerpo - cilindro_x(2.0, -largo - 6, -largo + 1, alto * 0.5)
        vaciados = 1
        n_nerv = int(p["nervaduras"])
        for lado in (1, -1):
            z0, z1 = (w - 1.2, w + 2) if lado > 0 else (-w - 2, -w + 1.2)
            cuerpo = cuerpo - caja_redonda(-largo * 0.9, -largo * 0.12, alto * 0.4, alto * 0.4 + 3.2, z0, z1, 1.3)
            vaciados += 1
            for i in range(n_nerv):
                x = -largo * 0.62 - i * 13.0
                cuerpo = cuerpo - caja_redonda(x - 1.2, x + 1.2, 2.0, alto * 0.75, z0, z1, 0.9)
                vaciados += 1
        sockets = [Socket("base", (-largo / 2, 0.0, 0.0), INT_TAPA, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {})]
        notas = [
            "Solo forma exterior; el interior y la bisagra delantera no se modelan.",
            "Curvatura, nervaduras y casquillo trasero estimados (confianza baja).",
        ]
        if p["rail"]:
            n = max(2, int((largo - 70) // 10.01))
            cuerpo = cuerpo + Pos(-largo + 28, alto - 1.2, 0) * solido_rail(n)
            sockets.append(
                Socket(
                    "rail.top",
                    (-largo + 28, alto + 8, 0.0),
                    INT_PICATINNY,
                    (0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0),
                    {"longitud_mm": longitud_rail_mm(n), "ranuras": n},
                )
            )
            notas.append(NOTA_PERFIL)
        return Geometria(
            cuerpo,
            tuple(sockets),
            (estimada("tapa.alto_cupula", alto),),
            tuple(notas),
            nominales_de(cuerpo),
            vaciados=vaciados,
        )


# Secciones del pistolete a lo largo de la altura: (u, semi-profundidad delante, detrás, semi-ancho), en fracción.
_SEC_PISTOLETE = (
    (0.00, 1.00, 1.00, 0.92),
    (0.06, 0.98, 1.10, 0.97),
    (0.20, 0.92, 0.96, 1.00),
    (0.45, 0.88, 0.86, 0.98),
    (0.70, 0.97, 0.92, 0.96),
    (0.88, 1.07, 0.98, 0.98),
    (0.97, 1.03, 0.97, 0.94),
    (1.00, 0.88, 0.88, 0.80),
)
_NIVELES = (0.0, 0.03, 0.07, 0.12, 0.18, 0.26, 0.35, 0.45, 0.55, 0.65, 0.74, 0.82, 0.89, 0.94, 0.975, 0.992, 1.0)


class PistoleteAK(Familia):
    id = "ak.pistolete"
    nombre = "Pistolete AK"
    material = "mat.polimero_marron"
    requiere = (INT_PISTOLETE,)
    ofrece = ()
    parametros = (
        Parametro("altura", "Altura de la cara de montaje a la base", float, "mm", 70, 130, de_sku=True),
        Parametro("profundidad", "Profundidad delante-detrás arriba", float, "mm", 24, 50, de_sku=True),
        Parametro("ancho", "Ancho lateral máximo", float, "mm", 24, 46, de_sku=True),
        Parametro("inclinacion", "Inclinación hacia atrás respecto a la vertical", float, "grados", 5, 35, de_sku=True),
        Parametro("estilo", "Estilo de superficie", str, opciones=("bakelita", "polimero"), por_defecto="polimero"),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Pistolete AK {p['estilo']} de {mm(p, 'altura')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        alto, prof, ancho, incl = (
            float(p["altura"]),
            float(p["profundidad"]),
            float(p["ancho"]),
            float(p["inclinacion"]),
        )
        tan = math.tan(math.radians(incl))
        us = [r[0] for r in _SEC_PISTOLETE]
        secciones = []
        for u in _NIVELES:
            f, t, b = (interpolar(us, [r[i] for r in _SEC_PISTOLETE], u) for i in (1, 2, 3))
            secciones.append(superelipse(-u * alto, -alto * tan * u, b * ancho / 2, f * prof / 2, t * prof / 2, n=3.2))
        cuerpo = loftear(secciones)
        vaciados = 0
        # Hueco de la espiga y taladro del tornillo, arriba.
        cuerpo = cuerpo - caja_redonda(-8, 8, -16, 1, -5.5, 5.5, 2.0, ejes="y")
        cuerpo = cuerpo - cilindro_y(3.0, 40, 0, -20)
        # Base: rebaje con la cabeza del tornillo.
        x_b = -alto * tan
        cuerpo = cuerpo - cilindro_y(0.30 * ancho, 3.6, x_b, -alto + 1.2)
        cuerpo = cuerpo + cilindro_y(0.11 * ancho, 2.2, x_b, -alto + 2.6)
        vaciados += 3
        # Estriado lateral: más fino en el polímero, dos surcos en la baquelita.
        n_ranuras = 6 if p["estilo"] == "polimero" else 2
        paso = 3.2 if p["estilo"] == "polimero" else 9.0
        for lado in (1, -1):
            zc = lado * (0.97 * ancho / 2)
            for i in range(n_ranuras):
                x = (i - (n_ranuras - 1) / 2) * paso
                ranura = caja_redonda(x - 0.8, x + 0.8, -0.80 * alto, -0.26 * alto, zc - 1.1, zc + 3, 0.7)
                cuerpo = cuerpo - Rot(0, 0, -incl) * ranura
                vaciados += 1
        cuerpo = filetear(cuerpo, 0.7, [e for e in cuerpo.edges() if abs(e.center().Y + alto) < 0.5])
        socket = Socket(
            "grip", (0.0, 0.0, 0.0), INT_PISTOLETE, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {"estilo": str(p["estilo"])}
        )
        notas = (
            "Dorso, panza de la base y estriado estimados, no medidos en ningún SKU.",
            "El interior (espiga, tornillo) no se modela: la pieza es maciza con rebajes superficiales.",
        )
        return Geometria(cuerpo, (socket,), (), notas, nominales_de(cuerpo), vaciados=vaciados)


def _espina(s: float, radio: float, theta0: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Punto y tangente de la espina del cargador: baja y se curva hacia +X con el radio dado."""
    th = theta0 + s / radio
    return (radio * (math.cos(theta0) - math.cos(th)), -radio * (math.sin(th) - math.sin(theta0))), (
        math.sin(th),
        -math.cos(th),
    )


class CargadorAK(Familia):
    id = "ak.cargador"
    nombre = "Cargador curvo AK"
    material = "mat.acero_negro"
    requiere = (INT_POZO,)
    ofrece = ()
    parametros = (
        Parametro("altura", "Longitud de la espina del cargador", float, "mm", 150, 330, de_sku=True),
        Parametro("profundidad", "Profundidad delante-detrás de la boca", float, "mm", 28, 52, de_sku=True),
        Parametro("ancho", "Ancho lateral", float, "mm", 20, 42, de_sku=True),
        Parametro("radio_curva", "Radio de curvatura de la espina", float, "mm", 250, 900, de_sku=True),
        Parametro("material", "Chapa de acero o polímero", str, opciones=("acero", "polimero"), por_defecto="acero"),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cargador curvo AK de {p['material']}, espina de {mm(p, 'altura')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, prof, ancho, radio = (
            float(p["altura"]),
            float(p["profundidad"]),
            float(p["ancho"]),
            float(p["radio_curva"]),
        )
        theta0 = math.radians(3.0)
        a, b = prof / 2, ancho / 2
        nudos = [0.0, 0.05, 0.95, 1.0]
        k_a, k_b = [0.96, 1.0, 1.0, 1.0], [0.85, 1.0, 1.0, 1.0]
        pasos = 22
        s_fin = largo - 4.0
        secc = []
        for i in range(pasos + 1):
            s = s_fin * i / pasos
            c, t = _espina(s, radio, theta0)
            f = s / largo
            secc.append(seccion_curva(c, t, a * interpolar(nudos, k_a, f), b * interpolar(nudos, k_b, f), n=3.6))
        cuerpo = loftear(secc)
        # Placa de base: ligeramente más grande que el cuerpo.
        placa = []
        for s, k in ((largo - 12.0, 1.08), (largo - 6.0, 1.09), (largo, 1.07)):
            c, t = _espina(s, radio, theta0)
            placa.append(seccion_curva(c, t, a * k, b * k, n=3.2))
        cuerpo = cuerpo + loftear(placa)
        vaciados = 0
        acero = p["material"] == "acero"
        cantidad = 5 if acero else 8
        for lado in (1, -1):
            zc = lado * (b - 0.4)
            for i in range(cantidad):
                if acero:  # surcos horizontales prensados, de lado a lado del cuerpo
                    c, t = _espina((0.20 + i * 0.13) * largo, radio, theta0)
                    ang = math.degrees(math.atan2(-t[0], t[1]))  # alinea el eje largo con la normal de la espina
                    cuerpo = cuerpo - Pos(c[0], c[1], zc) * Rot(
                        0, 0, math.degrees(math.atan2(t[0], -t[1])) + 0 * ang
                    ) * Box(0.8 * prof, 2.2, 2.8)
                else:  # estriado fino en el sentido de la espina
                    c, t = _espina(0.5 * largo, radio, theta0)
                    off = (i - (cantidad - 1) / 2) * 3.8
                    nx, ny = t[1], -t[0]
                    giro = math.degrees(math.atan2(t[0], -t[1]))
                    cuerpo = cuerpo - Pos(c[0] + off * nx, c[1] + off * ny, zc) * Rot(0, 0, giro) * Box(
                        1.4, 0.45 * largo, 2.8
                    )
                vaciados += 1
        # Gancho delantero y tetón trasero de enganche (silueta exterior).
        c, t = _espina(0.03 * largo, radio, theta0)
        nx, ny = t[1], -t[0]
        giro = math.degrees(math.atan2(t[0], -t[1]))
        cuerpo = cuerpo + Pos(c[0] - nx * (a + 0.5), c[1] - ny * (a + 0.5), 0) * Rot(0, 0, giro) * caja_redonda(
            -3.5, 3.5, -5, 5, -b * 0.55, b * 0.55, 1.2, ejes="x"
        )
        c, t = _espina(0.12 * largo, radio, theta0)
        nx, ny = t[1], -t[0]
        giro = math.degrees(math.atan2(t[0], -t[1]))
        cuerpo = cuerpo + Pos(c[0] + nx * a, c[1] + ny * a, 0) * Rot(0, 0, giro) * caja_redonda(
            -2.5, 2.5, -7, 7, -b * 0.5, b * 0.5, 1.0, ejes="x"
        )
        vaciados += 2
        socket = Socket("mag_well", (0.0, 0.0, 0.0), INT_POZO, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {})
        notas = (
            "Solo forma exterior: labios, muelle y seguidor no se modelan; el cuerpo es macizo.",
            "Curvatura, estriado, gancho y tetón estimados (confianza baja).",
        )
        return Geometria(
            cuerpo,
            (socket,),
            (estimada("cargador.profundidad_boca", prof),),
            notas,
            nominales_de(cuerpo),
            vaciados=vaciados,
        )


__all__ = ["CargadorAK", "PistoleteAK", "ReceptorAK", "TapaAK"]
