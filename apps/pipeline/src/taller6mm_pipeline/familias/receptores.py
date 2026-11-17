"""Receptores superior e inferior del M4/AR de airsoft: solo formas exteriores (oleada 1, B1 y B2 de familia-ar-m4).

Ejes canónicos: +X boca, +Y arriba, +Z izquierda del tirador. Sin internos: ni gearbox, ni cerrojo, ni muelles.

- Superior: origen en el centro de la cara trasera, con el eje del cañón en y = 0. La unión con el inferior queda
  en y = -EJE_SOBRE_UNION. Avanza hacia +X (el asa de armado asoma por detrás, x < 0).
- Inferior: origen en el centro de su cara trasera, con la unión con el superior en y = 0. La torre del tubo
  de culata sale por detrás (x < 0). Para ensamblar, el inferior se desplaza a y = -EJE_SOBRE_UNION.

Todas las medidas de forma que no son parámetros del SKU son estimadas (confianza baja, ver `detalle.py`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Cylinder,
    Location,
    Ellipse,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rot,
    chamfer,
    extrude,
    fillet,
    loft,
)

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.detalle import ancho_texto_mm, estimada, grabar, nominales_de
from taller6mm_pipeline.familias.formas import filetear
from taller6mm_pipeline.familias.rail_picatinny import NOTA_PERFIL, longitud_rail_mm, solido_rail

EJE_SOBRE_UNION_MM = 24.0
INTERFAZ_UNION = "union-superior-inferior-ar"
INTERFAZ_TUERCA = "tuerca-guardamanos-ar"
INTERFAZ_ASA_ARMADO = "montaje-asa-carga-ar"
INTERFAZ_TAPA = "ranura-cubierta-eyeccion"
INTERFAZ_MIRA_TRASERA = "montaje-mira-trasera-a2"
INTERFAZ_PISTOLETE = "montaje-pistolete-ar"
INTERFAZ_POZO = "pozo-stanag-m4"
CENTRO = (Align.CENTER, Align.CENTER, Align.CENTER)
MIN_X = (Align.MIN, Align.CENTER, Align.CENTER)


def _cil(eje: str, radio: float, largo: float, pos: tuple[float, float, float]) -> Any:
    c = Cylinder(radio, largo)
    if eje == "x":
        c = c.rotate(Axis.Y, 90)
    elif eje == "y":
        c = c.rotate(Axis.X, 90)
    return Pos(*pos) * c


def _caja(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Any:
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def _redondear_z(solido: Any, radio: float) -> Any:
    return fillet(solido.edges().filter_by(Axis.Z), radius=radio)


def _palanca_selector(xs: float, ys: float, zl: float) -> Any:
    """Palanca del selector del lado izquierdo: cubo, brazo cónico con puntero y lengüeta de pulgar con estrías.

    Se hunde 0,4 mm en el cuerpo (cara en z = zl). Apunta a +X con el selector en «seguro».
    """
    brazo = extrude(
        Plane.XY * Polygon((0, -4.5), (11, -3.4), (20, -3.0), (24.5, 0.0), (20, 3.0), (11, 3.4), (0, 4.5), align=None),
        1.5,
        both=True,
    )
    cubo = _cil("z", 5.6, 3.0, (0, 0, 1.1))
    pieza = Pos(0, 0, 1.1) * brazo + cubo
    tab = fillet(_caja(11.0, 21.0, -3.2, 3.2, 2.2, 3.8).edges().filter_by(Axis.Z), radius=1.0)
    for k in range(3):  # estrías de la lengüeta: 0,6 mm de profundidad, rebasan la cara superior
        tab = tab - _caja(13.0 + k * 2.6, 13.8 + k * 2.6, -4.0, 4.0, 3.2, 4.4)
    return Pos(xs, ys, zl) * (pieza + tab)


class ReceptorSuperior(Familia):
    id = "receptor.superior"
    version = 1
    nombre = "Receptor superior"
    requiere = (INTERFAZ_UNION,)
    ofrece = (INTERFAZ_TUERCA,)
    parametros = (
        Parametro("variante", "Variante", str, opciones=("a3_plano", "a2_asa"), por_defecto="a3_plano"),
        Parametro("longitud", "Longitud del cuerpo", float, "mm", minimo=140, maximo=340, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", minimo=26, maximo=46, de_sku=True),
        Parametro("alto", "Altura del cuerpo sin raíl ni asa", float, "mm", minimo=32, maximo=54, de_sku=True),
        Parametro(
            "tapa", "Tapa de la ventana de eyección", str, opciones=("cerrada", "abierta", "sin"), por_defecto="cerrada"
        ),
        Parametro("refuerzo", "Refuerzo de forja", str, opciones=("ninguno", "forjado"), por_defecto="ninguno"),
        Parametro("asa_armado", "Empuñadura de armado visible por detrás", bool, por_defecto=True),
        Parametro("forward_assist", "Botón de forward assist", bool, por_defecto=True),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if p["longitud"] is not None and p["variante"] == "a2_asa" and float(p["longitud"]) < 200:
            raise ParametroInvalidoError("longitud: el asa A2 pide al menos 200 mm de cuerpo")

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        extra = (e.INTERFAZ_PICATINNY,) if p["variante"] == "a3_plano" else (INTERFAZ_MIRA_TRASERA,)
        return (INTERFAZ_TUERCA, *extra)

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Receptor superior {p['variante']} de {largo}, tapa {p['tapa']}, refuerzo {p['refuerzo']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, w, h = float(p["longitud"]), float(p["ancho"]), float(p["alto"])
        y0, y1 = -EJE_SOBRE_UNION_MM, h - EJE_SOBRE_UNION_MM
        a2 = p["variante"] == "a2_asa"
        caja_base = _caja(0, largo, y0, y1, -w / 2, w / 2)
        # Cantos largos: los de arriba, filete de 3 mm; los de abajo (junta con el inferior), bisel de 4,5 mm.
        caja_base = chamfer(caja_base.edges().filter_by(Axis.X).filter_by_position(Axis.Y, y0 - 1, y0 + 1), 4.5)
        cuerpo = fillet(caja_base.edges().filter_by(Axis.X).filter_by_position(Axis.Y, y1 - 1, y1 + 1), radius=3.0)
        # Cantos de las caras trasera y delantera (los que quedan vivos tras redondear los largos): filete de 1,2 mm.
        cuerpo = filetear(cuerpo, 1.2, cuerpo.edges().filter_by(Axis.X, reverse=True).filter_by(Axis.Y, reverse=True))
        sockets: list[Socket] = []
        notas = [
            "Solo forma exterior: el interior (cerrojo, cámara, hop-up) no se modela; el cuerpo es macizo.",
            "Perfiles de ventana, asa y refuerzo simplificados y estimados (confianza baja).",
        ]
        vaciados = 0

        # Parte superior: raíl plano (A3) o asa de transporte con mira trasera (A2).
        if not a2:
            n = max(
                2,
                int(
                    (largo - (e.PICATINNY_PASO.valor_mm - e.PICATINNY_ANCHO_RANURA.valor_mm))
                    // e.PICATINNY_PASO.valor_mm
                ),
            )
            cuerpo = cuerpo + Pos(0, y1 - 0.5, 0) * solido_rail(n, e.PICATINNY_ALTURA.valor_mm + 0.5, largo)
            y_tope = y1 + e.PICATINNY_ALTURA.valor_mm
            sockets.append(
                Socket(
                    "rail.top",
                    (largo / 2, y_tope, 0.0),
                    e.INTERFAZ_PICATINNY,
                    (0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0),
                    {"longitud_mm": longitud_rail_mm(n), "ranuras": n},
                )
            )
            notas.append(NOTA_PERFIL)
            vaciados += n
        else:
            hh = 36.0
            xa, xb = 0.10 * largo, 0.60 * largo
            perfil = Polygon(
                (xa, y1 - 1),
                (xa, y1 + hh * 0.78),
                (xa + 10, y1 + hh),
                (xb - 14, y1 + hh),
                (xb, y1 + hh * 0.45),
                (xb + 6, y1 - 1),
                align=None,
            )
            asa = extrude(Plane.XY * perfil, 12, both=True)
            hueco = fillet(_caja(xa + 34, xb - 14, y1 + 6, y1 + hh - 10, -20, 20).edges().filter_by(Axis.Z), radius=5.0)
            asa = asa - hueco
            cx, cy = xa + 9, y1 + hh - 9
            tambor = _cil("z", 6.0, 30.0, (cx, cy, 0))
            for i in range(12):
                tambor = tambor - Pos(cx, cy, 0) * Rot(0, 0, i * 30) * Pos(0, 6.0, 0) * Box(0.8, 2.0, 31)
            cuerpo = cuerpo + asa + tambor + _cil("y", 4.0, 4.0, (cx, y1 + hh + 1.0, 0))
            sockets.append(
                Socket(
                    "rear_sight", (cx, y1 + hh + 3.0, 0.0), INTERFAZ_MIRA_TRASERA, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}
                )
            )
            notas.append("Asa A2: sin canal de mira, ruedas simplificadas a un tambor estriado y un pomo.")
            vaciados += 2

        # Ventana de eyección en el lado derecho (-Z), con tapa.
        wl, wh = min(0.24 * largo, 62.0), 0.40 * h
        wx0, wy0 = 0.30 * largo, y0 + 0.34 * h
        wy1, wx1 = wy0 + wh, wx0 + wl
        bolsillo = fillet(_caja(wx0, wx1, wy0, wy1, -w / 2 - 1, -w / 2 + 6).edges().filter_by(Axis.Z), radius=3.0)
        cuerpo = cuerpo - bolsillo
        vaciados += 1
        if p["refuerzo"] == "forjado":
            aro = fillet(
                _caja(wx0 - 4, wx1 + 4, wy0 - 4, wy1 + 4, -w / 2 - 1.2, -w / 2 + 0.5).edges().filter_by(Axis.Z),
                radius=5.0,
            )
            cuerpo = cuerpo + (aro - bolsillo)
            cuna = extrude(
                Plane.XZ * Polygon((wx0 - 16, -w / 2), (wx0 - 2, -w / 2), (wx0 - 2, -w / 2 - 4.5), align=None),
                wh * 0.3,
                both=True,
            )
            cuerpo = cuerpo + Pos(0, wy0 + wh * 0.6, 0) * cuna
            notas.append("Refuerzo de forja: reborde de la ventana y cuña del deflector simplificados.")
        if p["forward_assist"]:
            xf = wx0 - 36
            yf = wy0 + wh * 0.62
            carcasa = filetear(_cil("x", 6.6, 32.0, (xf + 16, yf, -w / 2 + 1.0)), 1.3)
            for k in range(3):  # tres anillos de agarre en la carcasa
                carcasa = carcasa - (
                    _cil("x", 7.0, 1.0, (xf + 6.0 + 5.0 * k, yf, -w / 2 + 1.0))
                    - _cil("x", 6.0, 1.0, (xf + 6.0 + 5.0 * k, yf, -w / 2 + 1.0))
                )
            boton = filetear(_cil("x", 4.6, 6.0, (xf - 3, yf, -w / 2 + 1.0)), 1.6)
            cuerpo = cuerpo + carcasa + boton
        if p["tapa"] != "sin":
            placa = fillet(
                _caja(wx0 + 0.6, wx1 - 0.6, wy0 + 0.6, wy1 - 0.6, -w / 2 - 0.5, -w / 2 + 2.5).edges().filter_by(Axis.Z),
                radius=2.4,
            )
            for k in range(3):  # nervios de agarre de la tapa
                placa = placa + _caja(
                    wx0 + wl * 0.3 + k * 4,
                    wx0 + wl * 0.3 + k * 4 + 1.2,
                    wy0 + wh * 0.3,
                    wy1 - wh * 0.3,
                    -w / 2 - 1.1,
                    -w / 2 - 0.4,
                )
            if p["tapa"] == "abierta":
                # Abierta: cuelga hacia abajo y hacia fuera (150°), como una tapa real sobre su varilla de bisagra.
                placa = placa.rotate(Axis((wx0, wy0, -w / 2), (1, 0, 0)), -150)
            cuerpo = cuerpo + placa + _cil("x", 1.4, wl + 6, ((wx0 + wx1) / 2, wy0 + 0.2, -w / 2 + 1.0))
            # Nudillos de la bisagra: sobre el eje de giro, así la tapa (abierta o cerrada) siempre queda unida.
            cuerpo = cuerpo + _cil("x", 1.7, wl - 1.2, ((wx0 + wx1) / 2, wy0, -w / 2))
            sockets.append(
                Socket(
                    "ejection_cover",
                    ((wx0 + wx1) / 2, wy0, -w / 2),
                    INTERFAZ_TAPA,
                    (0.0, 0.0, -1.0),
                    (1.0, 0.0, 0.0),
                    {},
                )
            )

        # Empuñadura de armado visible por detrás.
        if p["asa_armado"]:
            ya = y1 - 9.0
            # Cuerpo del pestillo en T: los extremos de las alas se redondean, cada ala lleva un rebaje para el dedo y
            # una palanca de liberación sobre el centro, con un gancho de apoyo bajo el vástago.
            alas = fillet(_caja(-24, -6, ya - 7, ya + 3, -22, 22).edges().filter_by(Axis.Y), radius=5.0)
            for lado in (-1, 1):
                alas = alas - fillet(
                    _caja(-20, -10, ya - 8, ya + 4, lado * 14.0 - 2.5, lado * 14.0 + 2.5).edges().filter_by(Axis.Y),
                    radius=2.4,
                )
            vastago = fillet(_caja(-24, 8, ya - 5, ya + 5, -8, 8).edges().filter_by(Axis.Y), radius=2.0)
            palanca = fillet(_caja(-22, -7, ya + 2, ya + 12, -7, 7).edges(), radius=2.4)
            gancho = fillet(_caja(-24, -15, ya - 18, ya - 4, -7, 7).edges(), radius=2.4)
            # Estrías de agarre de la palanca (siete nervios de 1,1 x 1,6 mm sobre su cara superior).
            for k in range(7):
                palanca = palanca + _caja(-21.0 + 2.1 * k, -19.9 + 2.1 * k, ya + 11.0, ya + 13.6, -5.5, 5.5)
            for k in range(3):  # y tres surcos en la cara trasera del gancho, donde apoya el dedo
                gancho = gancho - _caja(-25.0, -23.0, ya - 16.5 + 3.8 * k, ya - 15.3 + 3.8 * k, -5.5, 5.5)
            cuerpo = cuerpo + alas + vastago + palanca + gancho
            sockets.append(
                Socket("charging_handle", (-24.0, ya, 0.0), INTERFAZ_ASA_ARMADO, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {})
            )

        # Nariz de la tuerca del cañón con el alojamiento del cañón, 18 estrías de agarre, garganta del anillo elástico
        # y biseles: se hace aparte (es pequeña, los cortes salen rápido) y luego se une al cuerpo.
        nariz = filetear(_cil("x", 14.0, 8.0, (largo + 3.0, 0, 0)), 0.9)
        for k in range(18):
            nariz = nariz - Rot(k * 20.0, 0, 0) * Pos(largo + 3.6, 14.0, 0) * Box(5.6, 1.4, 1.5)
        nariz = nariz - (_cil("x", 14.6, 0.9, (largo + 5.6, 0, 0)) - _cil("x", 13.2, 0.9, (largo + 5.6, 0, 0)))
        nariz = nariz - _cil("x", 8.5, 14.0, (largo + 1.0, 0, 0))
        nariz = nariz - extrude(
            Plane.YZ * (Circle(10.4) - Circle(8.5)), 1.9, dir=(1, 0, 0)
        ).moved(Location((largo + 5.1, 0, 0)))
        cuerpo = cuerpo + nariz
        vaciados += 1
        sockets += [
            Socket("handguard", (largo + 7.0, 0.0, 0.0), INTERFAZ_TUERCA, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}),
            # Cara frontal del cuerpo: el guardamanos se apoya aquí y abraza la nariz de la tuerca (el cañón sigue
            # en `handguard`, al final de la nariz).
            Socket(
                "handguard_front", (largo, 0.0, 0.0), INTERFAZ_TUERCA, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), {}
            ),
            Socket("lower", (largo / 2, y0, 0.0), INTERFAZ_UNION, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
        ]

        # Líneas de partición (cara inferior) y leyenda neutra.
        cuerpo = cuerpo - [Pos(largo / 2, y0 + 4.0, s * w / 2) * Box(largo - 6, 0.5, 1.2) for s in (-1, 1)]
        texto = "AIRSOFT 6MM"
        cuerpo = cuerpo - grabar(texto, 4.0, (largo * 0.52, y0 + 9.0, w / 2), (1, 0, 0), (0, 0, 1))
        _ = ancho_texto_mm
        cotas = (estimada("receptor.eje_sobre_union", EJE_SOBRE_UNION_MM),)
        return Geometria(cuerpo, tuple(sockets), cotas, tuple(notas), nominales_de(cuerpo), vaciados + 2)


class ReceptorInferior(Familia):
    id = "receptor.inferior"
    version = 1
    nombre = "Receptor inferior"
    requiere = (INTERFAZ_UNION,)
    ofrece = (INTERFAZ_POZO, INTERFAZ_PISTOLETE)
    parametros = (
        Parametro("longitud", "Longitud hasta el frente", float, "mm", minimo=150, maximo=260, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", minimo=26, maximo=46, de_sku=True),
        Parametro(
            "profundidad_pozo",
            "Profundidad del pozo de cargador bajo la unión",
            float,
            "mm",
            minimo=50,
            maximo=90,
            de_sku=True,
            critico=False,
        ),
        Parametro("tubo", "Tubo de culata", str, opciones=tuple(e.TUBOS_CULATA), por_defecto="milspec"),
        Parametro("selector", "Posición del selector", str, opciones=("seguro", "semi", "auto"), por_defecto="seguro"),
        Parametro("selector_ambidiestro", "Palanca del selector también a la derecha", bool, por_defecto=False),
    )

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (INTERFAZ_POZO, INTERFAZ_PISTOLETE, e.TUBOS_CULATA[str(p["tubo"])])

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Receptor inferior de {largo}, selector {p['selector']}, tubo {p['tubo']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        ll, w = float(p["longitud"]), float(p["ancho"])
        hmag = 66.0 if p["profundidad_pozo"] is None else float(p["profundidad_pozo"])
        lt, r_torre = 22.0, 15.0
        # Silueta del cuerpo: solo la parte que llena todo el ancho (torre del tubo aparte). El guardamonte y el
        # asiento del pistolete se unen después, más estrechos y solapados con el cuerpo.
        sil = Polygon(
            (0, 0),
            (ll, 0),
            (ll, -24),
            (ll - 8, -30),
            (ll - 8, -hmag),
            (ll - 62, -hmag),
            (ll - 62, -34),
            (0, -34),
            align=None,
        )
        cuerpo = _redondear_z(extrude(Plane.XY * sil, w / 2, both=True), 2.5)
        # Contorno de las dos caras laterales: filete de 1,2 mm (los receptores reales no tienen canto vivo).
        cuerpo = filetear(cuerpo, 1.2, cuerpo.edges().filter_by(Axis.Z, reverse=True))
        torre = _caja(-lt, 0, -34, EJE_SOBRE_UNION_MM, -r_torre, r_torre) + _cil(
            "x", r_torre, lt, (-lt / 2, EJE_SOBRE_UNION_MM, 0)
        )
        torre = torre - _cil("x", 12.5, 18.0, (-lt + 9.0 - 0.5, EJE_SOBRE_UNION_MM, 0))
        cuerpo = cuerpo + torre
        vaciados = 4
        sockets: list[Socket] = []
        notas = [
            "Solo forma exterior: sin gearbox, gatillo ni cableado; macizo salvo pozo, guardamonte y torre.",
            "Sin pistolete: el receptor lo recibe por el socket.pistolete. Ángulos del selector simplificados.",
            "Guardamonte en arco, asiento del pistolete con tornillo y ranura del talón, boca del pozo acampanada, "
            "palanca del selector con lengüeta y pasadores en alojamientos: formas estimadas (confianza baja).",
        ]

        # Pozo del cargador pasante, con la boca acampanada (embudo troncopiramidal de esquinas redondeadas).
        xm = ll - 35.0
        eje_pozo = Plane(origin=(xm, 1.0, 0.0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        tramo = extrude(eje_pozo * RectangleRounded(44.0, 24.0, 3.0), hmag + 1.0 - 6.0)  # hasta y = 6 - hmag
        y_embudo = -hmag + 7.0
        embudo = loft(
            [
                Plane(origin=(xm, y_embudo, 0.0), x_dir=(1, 0, 0), z_dir=(0, 1, 0)) * RectangleRounded(44.0, 24.0, 3.0),
                Plane(origin=(xm, -hmag - 0.5, 0.0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
                * RectangleRounded(49.4, 29.4, 4.5),
            ],
            ruled=True,
        )
        cuerpo = cuerpo - tramo - embudo
        vaciados += 1

        # Guardamonte: arco elíptico más estrecho que el cuerpo, solapado 1 mm con la cara inferior y con el
        # frente del pozo. La ventana es la parte interior del arco.
        centro_g = (ll - 82.0, -34.0)
        exterior = Pos(centro_g[0], centro_g[1], 0) * extrude(Plane.XY * Ellipse(24.0, 19.0), 5.5, both=True)
        interior = Pos(centro_g[0], centro_g[1], 0) * extrude(Plane.XY * Ellipse(19.0, 15.0), 7.0, both=True)
        solo_abajo = _caja(centro_g[0] - 30, centro_g[0] + 30, -60.0, -33.0, -8, 8)
        arco = (exterior - interior) & solo_abajo
        cuerpo = cuerpo + arco
        vaciados += 1

        # Asiento del pistolete: plataforma que sobresale 2 mm bajo la cara inferior (solape 0,5 mm), con tornillo
        # del pistolete y ranura del talón. El socket `grip` se apoya en su cara inferior.
        x_asiento = ll - 140.0
        base = fillet(_caja(x_asiento, x_asiento + 36.0, -36.0, -33.5, -12, 12).edges().filter_by(Axis.Y), radius=5.0)
        base = base - _cil("y", 2.7, 14.5, (x_asiento + 22.0, -29.25, 0))  # taladro del tornillo, 3,5 mm hacia arriba
        base = base - _caja(x_asiento + 5, x_asiento + 14, -36.5, -34.3, -8, 8)  # ranura del talón
        cuerpo = cuerpo + base
        vaciados += 2

        # Selector (izquierda): asiento, muescas, palanca con puntero y lengüeta, y leyenda neutra.
        xs, ys, zl, zr = ll - 100.0, -14.0, w / 2, -w / 2
        cuerpo = cuerpo - (_cil("z", 10.0, 1.6, (xs, ys, zl)) - _cil("z", 9.0, 1.6, (xs, ys, zl)))
        for ang in (0, 90, 180):
            cuerpo = cuerpo - Pos(xs, ys, zl) * Rot(0, 0, ang) * Pos(11.5, 0, 0) * Box(5, 1.4, 2.4)
        grados = {"seguro": 0, "semi": 90, "auto": 180}[str(p["selector"])]
        izquierda = _palanca_selector(xs, ys, zl)
        cuerpo = cuerpo + izquierda.rotate(Axis((xs, ys, 0), (0, 0, 1)), grados)
        if p["selector_ambidiestro"]:
            derecha = izquierda.mirror(Plane.XY)
            cuerpo = cuerpo + derecha.rotate(Axis((xs, ys, 0), (0, 0, 1)), grados)
        cuerpo = cuerpo - grabar("SAFE SEMI AUTO", 2.8, (xs - 17.0, -8.0, zl), (1, 0, 0), (0, 0, 1))
        sockets.append(
            Socket(
                "selector",
                (xs, ys, zl + 2.5),
                "selector-ar",
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                {"posicion": str(p["selector"])},
            )
        )

        # Botón del cargador (derecha), con anillo y estrías.
        xb, yb = ll - 72.0, -16.0
        boton = _cil("z", 5.5, 5.0, (xb, yb, zr - 1.5)) + _cil("z", 7.5, 1.2, (xb, yb, zr - 0.2))
        for k in range(8):
            boton = boton - Pos(xb, yb, zr - 4.0) * Rot(0, 0, k * 22.5) * Box(0.8, 12.0, 1.0)
        cuerpo = cuerpo + boton

        # Pasadores en sus alojamientos (a ambos lados): del pivote y del desmontaje, y del gatillo y del martillo
        # (estos dos, más pequeños). Cada uno es un alojamiento con la cabeza del pasador hundida y un hexágono.
        pasadores = ((ll - 14.0, -9.0, 3.2), (12.0, -9.0, 3.2), (ll - 124.0, -18.0, 2.3), (ll - 146.0, -14.0, 2.3))
        for xp, yp, r_hueco in pasadores:
            for lado in (-1, 1):
                cuerpo = cuerpo - _cil("z", r_hueco, 3.2, (xp, yp, lado * zl))
                cuerpo = cuerpo + _cil("z", r_hueco - 0.9, 1.1, (xp, yp, lado * (zl - 1.35)))
                cuerpo = cuerpo - _cil("z", 0.9, 1.0, (xp, yp, lado * (zl - 1.0)))
        cuerpo = cuerpo - [Pos(ll / 2, -1.5, s * w / 2) * Box(ll - 10, 0.5, 1.2) for s in (-1, 1)]
        cuerpo = cuerpo - grabar("AIRSOFT 6MM", 3.2, (ll - 20.0, -46.0, zr), (-1, 0, 0), (0, 0, -1))

        sockets += [
            Socket(
                "buffer_tube",
                (-lt, EJE_SOBRE_UNION_MM, 0.0),
                e.TUBOS_CULATA[str(p["tubo"])],
                (-1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {},
            ),
            Socket("upper", (ll / 2, 0.0, 0.0), INTERFAZ_UNION, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket("magwell", (xm, -hmag, 0.0), INTERFAZ_POZO, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket("grip", (ll - 131.0, -36.0, 0.0), INTERFAZ_PISTOLETE, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
        ]
        cotas = (estimada("receptor.eje_sobre_union", EJE_SOBRE_UNION_MM),)
        return Geometria(cuerpo, tuple(sockets), cotas, tuple(notas), nominales_de(cuerpo), vaciados + 10)
