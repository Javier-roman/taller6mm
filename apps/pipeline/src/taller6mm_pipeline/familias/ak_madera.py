"""Familia AK de airsoft: guardamanos inferior, cubre-mano superior y culatas (fija y plegable lateral).

Ejes canónicos: +X boca, +Y arriba, +Z izquierda del tirador; el eje del cañón es Y = 0, Z = 0. Solo formas
exteriores; todas las proporciones son estimadas (confianza baja): son piezas `es_demo`, T0 y no publicables.
Sin marcajes ni logos.

- Guardamanos inferior y cubre-mano superior: origen en el centro de su extremo trasero, sobre el eje del cañón.
- Culata fija y plegable: origen en el centro de su cara delantera (la que se une al receptor); avanzan hacia -X.
"""

from __future__ import annotations

from collections.abc import Mapping

from build123d import Axis, Box, Pos

from taller6mm_pipeline.familias.ak_formas import (
    aristas_paralelas,
    caja_redonda,
    cilindro_x,
    cilindro_y,
    cilindro_z,
    estimada,
    loft_x,
)
from taller6mm_pipeline.familias.base import (
    Familia,
    Geometria,
    Parametro,
    ParametroInvalidoError,
    Socket,
    Valor,
)
from taller6mm_pipeline.familias.comun_oleada1 import mm, prisma
from taller6mm_pipeline.familias.detalle import nominales_de
from taller6mm_pipeline.familias.formas import filetear, suavizar

INT_GUARDAMANOS = "montaje-guardamanos-ak"
INT_CUBREMANO = "montaje-cubremano-ak"
INT_CULATA = "montaje-culata-ak"
INT_CULATA_PLEGABLE = "montaje-culata-ak-plegable-lateral"
Y_TUBO_GAS = 14.5  # eje del tubo de gas sobre el eje del cañón (estimado)


class GuardamanosInferiorAK(Familia):
    id = "ak.guardamanos_inferior"
    nombre = "Guardamanos inferior AK"
    material = "mat.madera"
    requiere = (INT_GUARDAMANOS,)
    ofrece = (INT_CUBREMANO,)
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", 100, 280, de_sku=True),
        Parametro("ancho", "Ancho máximo", float, "mm", 30, 48, de_sku=True),
        Parametro("alto", "Alto máximo (bajo el eje)", float, "mm", 22, 42, de_sku=True),
        Parametro(
            "estilo",
            "Estilo de agarre",
            str,
            opciones=("madera_surcos", "polimero_estriado"),
            por_defecto="madera_surcos",
        ),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Guardamanos inferior AK {p['estilo']} de {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, ancho, alto = float(p["longitud"]), float(p["ancho"]), float(p["alto"])
        hw = ancho / 2
        nudos = [
            (0.0, 5.0, -alto, hw),
            (largo * 0.18, 4.5, -alto + 0.5, hw - 0.4),
            (largo * 0.7, 3.5, -alto + 2.5, hw - 1.8),
            (largo, 2.5, -alto + 4.5, hw - 2.6),
        ]
        cuerpo = loft_x(0, largo, nudos, radio=10.0)
        cuerpo = cuerpo - cilindro_x(9.3, -1, largo + 1)  # canal del cañón
        vaciados = 1
        if p["estilo"] == "madera_surcos":
            # Tres surcos transversales de agarre bajo el cuerpo, redondeados.
            for i in range(3):
                x = largo * 0.42 + i * 22.0
                cuerpo = cuerpo - caja_redonda(x - 4, x + 4, -alto - 1, -alto + 3.4, -hw - 1, hw + 1, 3.0, ejes="y")
                vaciados += 1
            # Escotaduras laterales de los dedos: tres cuencos poco profundos a cada lado.
            for lado in (1, -1):
                for i in range(3):
                    x = largo * 0.42 + i * 22.0
                    cuerpo = cuerpo - cilindro_y(7.0, 2 * alto, x, -alto / 2, lado * (hw + 3.2))
                    vaciados += 1
        else:
            # Estrías longitudinales a los dos lados y escalón trasero.
            for lado in (1, -1):
                for k in range(5):
                    y = -alto + 5 + k * 4.6
                    z0, z1 = (hw - 2.3, hw + 2) if lado > 0 else (-hw - 2, -hw + 2.3)
                    cuerpo = cuerpo - caja_redonda(22.0, largo - 12.0, y - 1.1, y + 1.1, z0, z1, 1.0)
                    vaciados += 1
        # Escotadura trasera para la cuna delantera del receptor y rebaje delantero.
        cuerpo = cuerpo - caja_redonda(-1, 12, -6, 6, -hw + 4, hw - 4, 2.5, ejes="y")
        vaciados += 1
        cuerpo = suavizar(cuerpo, (0.5, 0.35, 0.25, 0.15))  # cantos de surcos, estrías y escotaduras redondeados
        sockets = (
            Socket(
                "receiver",
                (0.0, 0.0, 0.0),
                INT_GUARDAMANOS,
                (-1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {},
            ),
            Socket(
                "upper",
                (largo / 2, 5.0, 0.0),
                INT_CUBREMANO,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {},
            ),
        )
        notas = (
            "Solo forma exterior: muescas de encaje, pasadores y herrajes no se modelan.",
            "Sección, surcos y estrías estimados (confianza baja).",
        )
        return Geometria(
            cuerpo,
            sockets,
            (estimada("guardamanos_inf.alto", alto),),
            notas,
            nominales_de(cuerpo),
            vaciados,
        )


class CubremanoAK(Familia):
    id = "ak.cubremano"
    nombre = "Cubre-mano superior AK"
    material = "mat.madera"
    requiere = (INT_CUBREMANO,)
    ofrece = ()
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", 90, 260, de_sku=True),
        Parametro("ancho", "Ancho máximo", float, "mm", 28, 44, de_sku=True),
        Parametro("alto", "Alto sobre el eje del cañón", float, "mm", 22, 36, de_sku=True),
        Parametro(
            "ventilacion",
            "Cortes superiores",
            str,
            opciones=("ninguna", "ranuras", "nervios"),
            por_defecto="ranuras",
        ),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cubre-mano AK de {mm(p, 'longitud')} con ventilación {p['ventilacion']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, ancho, alto = float(p["longitud"]), float(p["ancho"]), float(p["alto"])
        hw = ancho / 2
        y_sup = 1.0 + alto
        nudos = [
            (0.0, y_sup - 1.0, 1.0, hw),
            (largo * 0.2, y_sup, 1.0, hw),
            (largo * 0.8, y_sup - 0.8, 1.0, hw - 0.8),
            (largo, y_sup - 2.2, 1.0, hw - 2.0),
        ]
        cuerpo = loft_x(0, largo, nudos, radio=11.0)
        r_canal = 10.2
        cuerpo = cuerpo - cilindro_x(r_canal, -1, largo + 1, y=Y_TUBO_GAS)
        cuerpo = cuerpo - caja_redonda(-1, largo + 1, 0, Y_TUBO_GAS, -r_canal, r_canal, 0.0)  # abierto por abajo
        vaciados = 2
        # Dos surcos longitudinales a cada lado, para que ninguna variante sea un tubo liso.
        for lado in (1, -1):
            z0, z1 = (hw - 1.0, hw + 2) if lado > 0 else (-hw - 2, -hw + 1.0)
            for y in (y_sup * 0.32, y_sup * 0.62):
                cuerpo = cuerpo - caja_redonda(largo * 0.1, largo * 0.9, y - 1.0, y + 1.0, z0, z1, 0.9)
                vaciados += 1
        if p["ventilacion"] == "ranuras":
            paso = 17.0
            n = max(2, int((largo * 0.78) // paso))
            x0 = largo * 0.14
            for fila in (-1, 1):
                for i in range(n):
                    x = x0 + i * paso
                    cuerpo = cuerpo - caja_redonda(
                        x,
                        x + 12,
                        y_sup - 8,
                        y_sup + 1,
                        fila * 5.5 - 1.7,
                        fila * 5.5 + 1.7,
                        1.5,
                        ejes="y",
                    )
                    vaciados += 1
        elif p["ventilacion"] == "nervios":
            n = max(3, int((largo * 0.7) // 8.0))
            for i in range(n):
                x = largo * 0.15 + i * 8.0
                cuerpo = cuerpo - caja_redonda(x, x + 2.2, y_sup - 1.3, y_sup + 1, -hw - 1, hw + 1, 0.8, ejes="y")
                vaciados += 1
        cuerpo = suavizar(cuerpo, (0.5, 0.35, 0.25, 0.15))  # cantos de surcos, ranuras y nervios redondeados
        sockets = (
            Socket(
                "lower",
                (largo / 2, 1.0, 0.0),
                INT_CUBREMANO,
                (0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0),
                {},
            ),
        )
        notas = (
            "Solo forma exterior: grapa de retención y pantalla térmica interior no se modelan.",
            "Sección, canal del tubo de gas y cortes estimados (confianza baja).",
        )
        return Geometria(
            cuerpo,
            sockets,
            (estimada("cubremano.eje_tubo_gas", Y_TUBO_GAS),),
            notas,
            nominales_de(cuerpo),
            vaciados,
        )


def _perfil_culata(f: float, alto_culata: float) -> tuple[float, float]:
    """(y arriba, y abajo) de la culata a la fracción `f` de su longitud (0 = cara delantera)."""
    arriba = 6.0 - 20.0 * f**1.1
    abajo = -46.0 + (-14.0 - alto_culata + 46.0) * f**1.6
    return arriba, abajo


class CulataFijaAK(Familia):
    id = "ak.culata_fija"
    nombre = "Culata fija AK"
    material = "mat.madera"
    requiere = (INT_CULATA,)
    ofrece = ()
    parametros = (
        Parametro("longitud", "Longitud de la culata", float, "mm", 200, 440, de_sku=True),
        Parametro(
            "alto_culata",
            "Alto en la plancha de culata",
            float,
            "mm",
            80,
            140,
            de_sku=True,
        ),
        Parametro("ancho", "Ancho máximo", float, "mm", 26, 46, de_sku=True),
        Parametro(
            "material",
            "Madera o polímero",
            str,
            opciones=("madera", "polimero"),
            por_defecto="madera",
        ),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Culata fija AK de {p['material']} y {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto_c, ancho = (
            float(p["longitud"]),
            float(p["alto_culata"]),
            float(p["ancho"]),
        )
        hw = ancho / 2
        cuerpo_largo = largo - 5.0  # la plancha de culata ocupa los últimos 5 mm
        nudos = []
        for k in range(13):
            f = k / 12
            arriba, abajo = _perfil_culata(f, alto_c)
            cintura = 1.0 - 0.10 * (1 - abs(2 * f - 0.9)) if f < 0.9 else 1.0
            nudos.append((-cuerpo_largo * f, arriba, abajo, hw * cintura * (1.0 + 0.05 * f)))
        nudos.sort(key=lambda q: q[0])
        cuerpo = loft_x(-cuerpo_largo, 0, nudos, radio=8.0)
        a_t, a_b = _perfil_culata(1.0, alto_c)
        placa = loft_x(
            -largo,
            -cuerpo_largo,
            [
                (-largo, a_t + 1.2, a_b - 1.2, hw * 1.05 + 1.2),
                (-cuerpo_largo, a_t + 1.2, a_b - 1.2, hw * 1.05 + 1.2),
            ],
            radio=6.0,
        )
        cuerpo = cuerpo + placa
        vaciados = 0
        # Dos tornillos de la plancha con su ranura.
        for dy in (-12.0, -alto_c + 8.0):
            y = a_t + dy if dy > -20 else a_b + 12
            cuerpo = cuerpo + cilindro_x(3.0, -largo - 1.2, -largo + 0.5, y)
            cuerpo = cuerpo - Pos(-largo - 1.0, y, 0) * Box(1.0, 5.2, 1.0)
            vaciados += 2
        # Alojamiento de la espiga del receptor y taladro del tornillo, en la cara delantera.
        cuerpo = cuerpo - caja_redonda(-32, 1, -6.5, 6.5, -7, 7, 2.5, ejes="x")
        cuerpo = cuerpo - cilindro_x(3.0, -58, 1, -9.0)
        vaciados += 2
        notas = [
            "Solo forma exterior: la caja del estuche de limpieza y los herrajes interiores no se modelan.",
            "Perfil de alzado, cintura y proporciones estimados (confianza baja).",
        ]
        if p["material"] == "madera":
            # Tapa del estuche de limpieza: anillo grabado en la plancha.
            cuerpo = cuerpo - (
                cilindro_x(12.0, -largo - 2, -largo + 0.8, (a_t + a_b) / 2)
                - cilindro_x(10.6, -largo - 2, -largo + 0.8, (a_t + a_b) / 2)
            )
            vaciados += 1
        else:
            for lado in (1, -1):  # bolsillos de aligeramiento a los lados
                z0, z1 = (hw - 3.2, hw + 3) if lado > 0 else (-hw - 3, -hw + 3.2)
                for f0, f1 in ((0.12, 0.40), (0.48, 0.80)):
                    ym = sum(_perfil_culata((f0 + f1) / 2, alto_c)) / 2
                    cuerpo = cuerpo - caja_redonda(
                        -cuerpo_largo * f1,
                        -cuerpo_largo * f0,
                        ym - 11,
                        ym + 11,
                        z0,
                        z1,
                        7.0,
                    )
                    vaciados += 1
        socket = Socket(
            "receiver",
            (0.0, -8.0, 0.0),
            INT_CULATA,
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            {},
        )
        return Geometria(
            cuerpo,
            (socket,),
            (estimada("culata.alto_plancha", alto_c),),
            tuple(notas),
            nominales_de(cuerpo),
            vaciados,
        )


Z_BISAGRA = 22.0  # eje del pasador de la bisagra, a la izquierda del receptor (estimado)
X_BISAGRA = -14.0


class CulataPlegableAK(Familia):
    id = "ak.culata_plegable"
    nombre = "Culata plegable lateral AK"
    material = "mat.acero_negro"
    requiere = (INT_CULATA_PLEGABLE,)
    ofrece = ()
    parametros = (
        Parametro(
            "longitud",
            "Longitud con la culata extendida",
            float,
            "mm",
            220,
            400,
            de_sku=True,
        ),
        Parametro("alto_culata", "Alto de la culata", float, "mm", 90, 150, de_sku=True),
        Parametro("grosor", "Grosor lateral del bastidor", float, "mm", 8, 20, de_sku=True),
        Parametro(
            "posicion",
            "Extendida o plegada a la izquierda",
            str,
            opciones=("extendida", "plegada"),
            por_defecto="extendida",
        ),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["longitud"] is not None
            and p["alto_culata"] is not None
            and float(p["alto_culata"]) > float(p["longitud"]) * 0.6
        ):
            raise ParametroInvalidoError("alto_culata: demasiado alta para la longitud (bastidor deformado)")

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Culata plegable lateral AK de {mm(p, 'longitud')} ({p['posicion']})"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto_c, grosor = (
            float(p["longitud"]),
            float(p["alto_culata"]),
            float(p["grosor"]),
        )
        exterior = [
            (-4.0, 8.0),
            (-largo + 14, -8.0),
            (-largo + 4, -alto_c),
            (-12.0, -52.0),
        ]
        cx = sum(q[0] for q in exterior) / 4
        cy = sum(q[1] for q in exterior) / 4
        interior = [(cx + (x - cx) * 0.6, cy + (y - cy) * 0.6) for x, y in exterior]
        marco = prisma(exterior, grosor) - prisma(interior, grosor + 4)
        marco = filetear(marco, 2.5, aristas_paralelas(marco, "z"))
        # Alojamiento y pasador de la bisagra: pieza fija junto al receptor.
        brazo = caja_redonda(-26, -2, -14, 10, -grosor / 2, Z_BISAGRA + 5, 4.0, ejes="y")
        cuerpo = marco + brazo
        # Zapata trasera, abombada y redondeada.
        zapata = loft_x(
            -largo - 10,
            -largo + 8,
            [
                (-largo - 10, -9.0, -alto_c - 3, 16.0),
                (-largo + 8, -8.0, -alto_c - 3, 15.0),
            ],
            radio=7.0,
        )
        cuerpo = cuerpo + zapata
        vaciados = 1
        if p["posicion"] == "plegada":
            cuerpo = cuerpo.rotate(Axis((X_BISAGRA, 0, Z_BISAGRA), (0, 1, 0)), 180)
        carcasa = caja_redonda(-30, 0, -20, 12, -14, Z_BISAGRA + 5, 5.0, ejes="y")
        pasador = cilindro_y(5.0, 34.0, X_BISAGRA, -4.0, Z_BISAGRA) + cilindro_y(7.0, 3.0, X_BISAGRA, 13.5, Z_BISAGRA)
        cuerpo = cuerpo + carcasa + pasador
        # Resalte del cierre en el costado de la carcasa.
        cuerpo = cuerpo + cilindro_z(3.2, 3.0, -22.0, -8.0, -14.5)
        vaciados += 3
        notas = (
            "Solo forma exterior: el resorte, el cierre y el pasador son siluetas; no se modela su mecanismo.",
            "Bastidor triangular, zapata y posición de la bisagra estimados (confianza baja).",
        )
        socket = Socket(
            "receiver",
            (0.0, 0.0, 0.0),
            INT_CULATA_PLEGABLE,
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            {},
        )
        return Geometria(
            cuerpo,
            (socket,),
            (estimada("culata_plegable.z_bisagra", Z_BISAGRA),),
            notas,
            nominales_de(cuerpo),
            vaciados,
        )
