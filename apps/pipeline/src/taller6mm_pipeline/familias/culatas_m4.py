"""Culatas del M4 (tanda 3): telescópicas de 6 posiciones, fija A2, plegable lateral, skeleton y brace de pistola.

Ejes: +X boca, +Y arriba, +Z izquierda. Origen: centro de la cara delantera del tubo (donde apoya contra el
receptor), sobre el eje; todo avanza hacia -X. Registro propio `FAMILIAS_CULATAS`.

Las formas son **genéricas**: proporciones de la familia, sin marcas, logos ni marcajes ni copia de ningún producto
concreto (el estilo «polímero» recoge solo rasgos comunes: mejilla alta, palanca ancha, anillas de correa). Todas las
medidas son estimaciones de barrido (confianza baja, `es_demo`); el tubo se incluye como referencia visual y puede
quitarse con `incluir_tubo = False` para componerla con `amortiguador.tubo`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Box, Pos, Rot, Spline

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.detalle import nominales_de
from taller6mm_pipeline.familias.formas import cilindro_en, extruir_perfil, filetear, interpolar
from taller6mm_pipeline.familias.formas_tanda3 import (
    cuerpo_por_secciones,
    estadio_en_z,
    ranura_radial,
    torus_xy,
)

INTERFAZ_CORREA = "anclaje-correa-qd-socket"
INTERFAZ_PLEGABLE = "montaje-culata-plegable-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
NOTA_TUBO = "El tubo y su quilla son referencia visual: el tubo real lo aporta `amortiguador.tubo`."
NOTA_INTERIOR = "Solo forma exterior: sin hueco de batería, muelles ni mecanismo de bloqueo."

_ESPEC = Parametro("especificacion", "Tipo de tubo", str, opciones=tuple(e.TUBOS_CULATA), por_defecto="milspec")
_TUBO = Parametro("diametro_tubo", "Diámetro del tubo que aloja", float, "mm", 22, 36, de_sku=True, critico=False)
_INCLUIR = Parametro("incluir_tubo", "Incluir el tubo como referencia visual", bool, por_defecto=True)


def _ranura_inferior(x0: float, x1: float, ancho: float, alto: float) -> Any:
    """Ranura que muerde hacia abajo (-Y) desde el eje."""
    return Rot(180, 0, 0) * ranura_radial(x0, x1, ancho, alto)


def tubo_con_quilla(diametro: float, largo: float, posiciones: int, paso: float) -> Any:
    """Tubo cilíndrico con la quilla inferior y sus taladros de posición (referencia visual)."""
    r = diametro / 2
    tubo = cilindro_en("x", r, largo, (-largo / 2, 0, 0))
    alto, ancho = 8.0, 10.0
    xq0, xq1 = -9.0, -(largo - 6.0)
    centro_y = -(r + alto / 2 - 2.5)
    quilla = Pos((xq0 + xq1) / 2, centro_y, 0) * Box(abs(xq1 - xq0) - alto, alto, ancho)
    for xe in (xq0 - alto / 2, xq1 + alto / 2):
        quilla = quilla + cilindro_en("z", alto / 2, ancho, (xe, centro_y, 0))
    quilla = filetear(quilla, 0.8)
    for i in range(posiciones):
        quilla = quilla - cilindro_en("z", 2.2, ancho + 2, (-(34.0 + i * paso), centro_y, 0))
    return tubo + quilla


def _plantilla_tubo(p: Mapping[str, Valor], largo: float, posiciones: int, paso: float) -> Any | None:
    if not p["incluir_tubo"] or p["diametro_tubo"] is None:
        return None
    return tubo_con_quilla(float(p["diametro_tubo"]), largo, posiciones, paso)


def _estrias_cantonera(x_tras: float, y0: float, y1: float, ancho: float, paso: float = 5.0) -> Any | None:
    """Surcos horizontales poco profundos en la cara trasera de la cantonera (agarre contra el hombro)."""
    surcos: list[Any] = []
    y = y0
    while y <= y1:
        surcos.append(Pos(x_tras, y, 0) * Box(1.6, 1.0, ancho))
        y += paso
    if not surcos:
        return None
    total = surcos[0]
    for s in surcos[1:]:
        total = total + s
    return total


def _sockets(
    x_correa: float, y_correa: float, extra: tuple[Socket, ...] = (), interfaz_tubo: str = ""
) -> tuple[Socket, ...]:
    tubo = Socket(
        "tubo",
        (0.0, 0.0, 0.0),
        interfaz_tubo,
        (1.0, 0.0, 0.0),  # hacia el receptor
        (0.0, 1.0, 0.0),
        {"referencia": "centro de la cara delantera del tubo"},
    )
    correa = Socket(
        "correa",
        (x_correa, y_correa, 0.0),
        INTERFAZ_CORREA,
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
        {"referencia": "centro de la anilla de correa"},
    )
    return (tubo, correa, *extra)


# --- Telescópica de 6 posiciones (carabina y estilo polímero) ---------------------------------------------------
# Fila: (fracción del largo, hy_pos, hy_neg, hz_pos, hz_neg, n, cy, cz). El eje del tubo es Y = 0.
_PERFILES: dict[str, dict[str, Any]] = {
    "carabina": {
        "tabla": (
            (0.00, 22.0, 24.0, 21.0, 21.0, 2.6, 0.0, 0.0),
            (0.12, 25.0, 27.0, 22.5, 22.5, 2.8, 0.0, 0.0),
            (0.45, 27.5, 30.0, 23.0, 23.0, 3.0, 0.0, 0.0),
            (0.80, 30.0, 40.0, 23.5, 23.5, 3.0, 0.0, 0.0),
            (0.95, 31.0, 58.0, 23.0, 23.0, 3.2, 0.0, 0.0),
            (1.00, 29.0, 55.0, 20.5, 20.5, 3.0, 0.0, 0.0),
        ),
        "palanca": (14.0, 56.0, 9.0),  # x desde el frente, largo, alto
        "estrias": True,
        "rueda_correa": 0.88,
    },
    "str": {
        "tabla": (
            (0.00, 23.0, 25.0, 22.0, 22.0, 2.6, 0.0, 0.0),
            (0.10, 27.0, 28.0, 24.0, 24.0, 2.8, 0.0, 0.0),
            (0.40, 33.0, 32.0, 25.0, 25.0, 3.1, 0.0, 0.0),  # mejilla alta
            (0.78, 35.0, 42.0, 26.0, 26.0, 3.1, 0.0, 0.0),
            (0.95, 33.0, 62.0, 25.0, 25.0, 3.3, 0.0, 0.0),
            (1.00, 30.0, 58.0, 22.0, 22.0, 3.0, 0.0, 0.0),
        ),
        "palanca": (10.0, 64.0, 11.0),
        "estrias": False,
        "rueda_correa": 0.90,
    },
    "ctr": {
        "tabla": (
            (0.00, 21.0, 23.0, 20.0, 20.0, 2.5, 0.0, 0.0),
            (0.12, 23.0, 25.0, 21.0, 21.0, 2.6, 0.0, 0.0),
            (0.45, 26.0, 27.0, 21.5, 21.5, 2.8, 0.0, 0.0),
            (0.82, 28.0, 36.0, 22.0, 22.0, 3.0, 0.0, 0.0),
            (0.95, 28.0, 52.0, 22.0, 22.0, 3.2, 0.0, 0.0),
            (1.00, 26.0, 49.0, 19.5, 19.5, 3.0, 0.0, 0.0),
        ),
        "palanca": (8.0, 40.0, 8.0),
        "estrias": False,
        "rueda_correa": 0.0,
        "bocas_correa": True,
    },
    "moe": {
        "tabla": (
            (0.00, 23.0, 25.0, 22.0, 22.0, 2.7, 0.0, 0.0),
            (0.15, 26.0, 28.0, 24.0, 24.0, 2.8, 0.0, 0.0),
            (0.50, 28.0, 31.0, 25.0, 25.0, 2.6, 0.0, 0.0),
            (0.85, 30.0, 41.0, 25.5, 25.5, 2.8, 0.0, 0.0),
            (0.96, 30.0, 55.0, 24.5, 24.5, 3.0, 0.0, 0.0),
            (1.00, 27.0, 50.0, 20.5, 20.5, 2.9, 0.0, 0.0),
        ),
        "palanca": (11.0, 52.0, 10.0),
        "estrias": False,
        "rueda_correa": 0.86,
    },
}


def _palanca(x_frente: float, y_base: float, largo: float, alto: float, ancho: float) -> Any:
    """Palanca de ajuste: lengüeta curva bajo el frente del cuerpo (forma orgánica de spline, con dedo de agarre)."""
    x0 = x_frente - 2.0
    pts = [
        (x0, y_base),
        (x0 - 0.30 * largo, y_base - 0.45 * alto),
        (x0 - 0.60 * largo, y_base - 0.55 * alto),
        (x0 - 0.92 * largo, y_base - alto),  # dedo
        (x0 - largo, y_base - 0.55 * alto),
        (x0 - 0.80 * largo, y_base + 0.5),
        (x0 - 0.40 * largo, y_base + 1.0),
    ]
    lengueta = extruir_perfil([Spline(*pts, periodic=True)], ancho)
    return filetear(lengueta, 0.8)


class _TelescopicaBase(Familia):
    material = "mat.polimero_negro"
    paso_defecto = 12.0
    clave_perfil = "carabina"

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["diametro_tubo"] is not None
            and p["ancho"] is not None
            and float(p["ancho"]) < float(p["diametro_tubo"]) + 6
        ):
            raise ParametroInvalidoError("ancho: debe superar el diámetro del tubo en 6 mm como mínimo")

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (INTERFAZ_CORREA,)

    def _perfil(self, p: Mapping[str, Valor]) -> dict[str, Any]:
        return _PERFILES[self.clave_perfil]

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        perfil = self._perfil(p)
        largo, alto_cant, ancho = float(p["longitud_cuerpo"]), float(p["alto_cantonera"]), float(p["ancho"])
        pos, paso = int(p["posicion"]), float(p["paso_posicion"])
        x_frente = -(18.0 + (pos - 1) * paso)
        # Escalas respecto a la tabla base (alto de cantonera 93 mm, ancho 46 mm).
        esc_alto = alto_cant / 93.0
        esc_ancho = ancho / 46.0
        tabla = []
        for f, hp, hn, zp, zn, n, cy, cz in perfil["tabla"]:
            tabla.append(
                (f, hp, hn * (1 + (esc_alto - 1) * min(1.0, f * 1.3)), zp * esc_ancho, zn * esc_ancho, n, cy, cz)
            )
        cuerpo = cuerpo_por_secciones(x_frente, largo, tabla)
        x_tras = x_frente - largo
        notas = [NOTA_INTERIOR]
        # Boca delantera: se rehunde para que se vea el tubo entrando.
        d_tubo = float(p["diametro_tubo"]) if p["diametro_tubo"] is not None else 29.0
        cuerpo = cuerpo - cilindro_en("x", d_tubo / 2 + 1.6, 9.0, (x_frente - 3.5, 0, 0))
        # Hueco de la palanca y palanca.
        px, plargo, palto = perfil["palanca"]
        y_fondo = -tabla[1][2]
        # Alojamiento somero bajo el frente (6 mm de profundidad) y la palanca que sale de él.
        bahia = Pos(0, y_fondo + 6.0, 0) * _ranura_inferior(x_frente - px - 2, x_frente - px - plargo - 2, 20.0, 14.0)
        cuerpo = cuerpo - bahia
        cuerpo = cuerpo + _palanca(x_frente - px, y_fondo + 7.0, plargo, palto * 1.4, 14.0)
        # Bolsillos laterales poco profundos (agarre y aligeramiento de molde), dos por flanco.
        fs, zs = [f[0] for f in tabla], [f[3] for f in tabla]
        for lado in (-1, 1):
            for fx, largo_b in ((0.30, 34.0), (0.56, 30.0)):
                tramo = [fx + k * (largo_b / 2 / largo) for k in (-1, 0, 1)]
                suelo = min(interpolar(fs, zs, f) for f in tramo) - 1.3  # el fondo queda siempre dentro de la piel
                cuerpo = cuerpo - estadio_en_z(x_frente - fx * largo, 2.0, largo_b, 15.0, 6.0, lado * (suelo + 3.0))
        # Cantonera: estrías y anilla de correa.
        y_cant_alto = tabla[-2][1]
        y_cant_bajo = -tabla[-2][2]
        if perfil["estrias"]:
            estrias = _estrias_cantonera(x_tras, y_cant_bajo + 8, y_cant_alto - 4, ancho * 0.8)
            if estrias is not None:
                cuerpo = cuerpo - estrias
        # Surco entre la cantonera y el cuerpo.
        cuerpo = cuerpo - (
            Pos(x_tras + 18.0, (y_cant_alto + y_cant_bajo) / 2, 0) * Box(0.9, y_cant_alto - y_cant_bajo + 4, ancho + 4)
        )
        x_correa = x_tras + 14.0
        y_correa = y_cant_bajo + 11.0
        cuerpo = cuerpo - estadio_en_z(x_correa, y_correa, 22.0, 7.0, ancho + 4)
        sockets = _sockets(x_correa, y_correa, interfaz_tubo=self.requiere_de(p)[0])
        if perfil.get("bocas_correa"):
            # Dos casquillos de correa a los lados de la cantonera (QD genérico), de cabeza redonda.
            for lado in (-1, 1):
                z = lado * (ancho / 2 * 0.95 + 1.0)
                cuerpo = cuerpo + cilindro_en("z", 5.5, 4.0, (x_tras + 26.0, y_cant_bajo + 24.0, z))
                cuerpo = cuerpo - cilindro_en("z", 2.2, 3.0, (x_tras + 26.0, y_cant_bajo + 24.0, z + lado * 1.5))
        tubo = _plantilla_tubo(p, 18.0 + 5 * paso + largo + 10.0, 6, paso)
        if tubo is not None:
            cuerpo = cuerpo + tubo
            notas.append(NOTA_TUBO)
        else:
            notas.append("Sin tubo: se compone con `amortiguador.tubo`.")
            if p["diametro_tubo"] is not None:
                # La culata es una funda: con el tubo suelto, el cuerpo lleva el alojamiento (cilindro + quilla) para
                # que el tubo del ensamblaje entre sin atravesar el material (antes se montaba con 15 mm de solape).
                r_a = d_tubo / 2 + 1.2  # el anillo trasero del tubo llega a +1 mm sobre el cuerpo
                prof = largo - 12.0
                x_a = x_frente - prof / 2 + 0.5
                aloj = cilindro_en("x", r_a, prof + 1.0, (x_a, 0, 0))
                aloj = aloj + Pos(x_a, -(r_a + 4.0) / 2, 0) * Box(prof + 1.0, r_a + 4.0, 8.4)
                cuerpo = cuerpo - aloj
                notas.append("Alojamiento interior del tubo (cilindro y quilla) con holgura para el anillo del tubo.")
        notas.append(f"Posición {pos} de 6 ({paso:g} mm por posición, estimado).")
        return Geometria(cuerpo, sockets, (), tuple(notas), nominales_de(cuerpo), vaciados=9)


def _comunes_telescopica(clave_perfil: str, por_defecto: dict[str, Any]) -> tuple[Parametro, ...]:
    return (
        _ESPEC,
        _TUBO,
        _INCLUIR,
        Parametro("longitud_cuerpo", "Longitud del cuerpo deslizante", float, "mm", 120, 220, de_sku=True),
        Parametro("alto_cantonera", "Altura de la cantonera", float, "mm", 60, 140, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", 34, 60, de_sku=True),
        Parametro("paso_posicion", "Paso entre posiciones", float, "mm", 8, 16, de_sku=True, critico=False),
        Parametro("posicion", "Posición de extensión (1 = cerrada)", int, "ud", 1, 6, por_defecto=1),
    )


class CulataTelescopica6(_TelescopicaBase):
    id = "culata.telescopica_6pos"
    nombre = "Culata telescópica de 6 posiciones (tipo carabina)"
    clave_perfil = "carabina"
    parametros = _comunes_telescopica("carabina", {})

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = mm(p, "longitud_cuerpo")
        return f"Culata telescópica de 6 posiciones tipo carabina, posición {p['posicion']}, cuerpo de {largo}"


class CulataTelescopicaPolimero(_TelescopicaBase):
    """Estilo polímero genérico (rasgos comunes de las culatas de mejilla alta, sin marcas ni copia de un modelo)."""

    id = "culata.telescopica_polimero"
    nombre = "Culata telescópica de polímero (estilo genérico)"
    parametros = (
        *_comunes_telescopica("str", {}),
        Parametro("estilo", "Estilo de la silueta", str, opciones=("str", "ctr", "moe"), por_defecto="str"),
    )

    def _perfil(self, p: Mapping[str, Valor]) -> dict[str, Any]:
        return _PERFILES[str(p["estilo"])]

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Culata telescópica de polímero estilo {p['estilo']}, posición {p['posicion']}"


# --- Fija A2 ---------------------------------------------------------------------------------------------------
class CulataFijaA2(Familia):
    id = "culata.fija_a2"
    nombre = "Culata fija tipo A2 (con compartimento)"
    material = "mat.polimero_negro"
    parametros = (
        _ESPEC,
        _INCLUIR,
        Parametro("longitud", "Longitud del cuerpo desde el receptor", float, "mm", 200, 320, de_sku=True),
        Parametro("alto_cantonera", "Altura de la cantonera", float, "mm", 80, 150, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", 34, 60, de_sku=True),
        Parametro("diametro_tubo", "Diámetro del tubo", float, "mm", 22, 36, de_sku=True, critico=False),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Culata fija A2 de {mm(p, 'longitud')}, cantonera de {mm(p, 'alto_cantonera')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, ancho = float(p["longitud"]), float(p["alto_cantonera"]), float(p["ancho"])
        ea, ez = alto / 112.0, ancho / 46.0
        tabla = (
            (0.00, 22.0, 24.0, 21.0 * ez, 21.0 * ez, 2.6, 0.0, 0.0),
            (0.10, 25.0, 27.0, 23.0 * ez, 23.0 * ez, 2.7, 0.0, 0.0),
            (0.35, 29.0, 33.0 * ea, 24.5 * ez, 24.5 * ez, 2.9, 0.0, 0.0),
            (0.65, 33.0, 46.0 * ea, 25.5 * ez, 25.5 * ez, 3.0, 0.0, 0.0),
            (0.90, 36.0, 66.0 * ea, 25.0 * ez, 25.0 * ez, 3.2, 0.0, 0.0),
            (0.97, 35.5, 70.0 * ea, 24.0 * ez, 24.0 * ez, 3.3, 0.0, 0.0),
            (1.00, 33.0, 66.0 * ea, 21.5 * ez, 21.5 * ez, 3.0, 0.0, 0.0),
        )
        x_tras = -largo
        cuerpo = cuerpo_por_secciones(0.0, largo, tabla)
        cuerpo = cuerpo - cilindro_en("x", 17.5, 3.0, (-1.4, 0, 0))  # asiento contra el receptor
        y_alto, y_bajo = 36.0, -70.0 * ea
        estrias = _estrias_cantonera(x_tras, y_bajo + 10, y_alto - 6, ancho * 0.75)
        if estrias is not None:
            cuerpo = cuerpo - estrias
        # Tapa del compartimento: marco de surcos finos en la cara trasera (sin mecanismo).
        ay, by = y_bajo + 14, y_bajo + 46
        marco = (
            Pos(x_tras + 0.2, (ay + by) / 2, 0) * Box(1.2, 0.7, 26.0 * ez)
            + Pos(x_tras + 0.2, ay, 0) * Box(1.2, 0.7, 26.0 * ez)
            + Pos(x_tras + 0.2, by, 0) * Box(1.2, 0.7, 26.0 * ez)
        )
        marco = Pos(0, 0, 0) * marco
        cuerpo = (
            cuerpo
            - (Pos(x_tras + 0.2, (ay + by) / 2, 13.0 * ez) * Box(1.2, by - ay, 0.7))
            - (Pos(x_tras + 0.2, (ay + by) / 2, -13.0 * ez) * Box(1.2, by - ay, 0.7))
            - marco
        )
        # Tornillo superior (cabeza rehundida) y anilla de correa bajo la culata.
        cuerpo = cuerpo - cilindro_en("y", 4.2, 3.0, (x_tras + 16.0, y_alto - 1.0, 0))
        # Surco de separación de la cantonera y tetón con anilla de correa bajo la culata.
        cuerpo = cuerpo - Pos(x_tras + 20.0, (y_alto + y_bajo) / 2, 0) * Box(0.9, y_alto - y_bajo + 4, ancho + 4)
        x_t = x_tras + 46.0
        y_fondo = -interpolar([f[0] for f in tabla], [f[2] for f in tabla], -x_t / largo)
        cuerpo = cuerpo + cilindro_en("y", 4.0, 10.0, (x_t, y_fondo - 1.0, 0))
        cuerpo = cuerpo + torus_xy((x_t, y_fondo - 9.5, 0.0), 8.0, 1.8)
        x_correa, y_correa = x_tras + 22.0, y_bajo + 12.0
        cuerpo = cuerpo - estadio_en_z(x_correa, y_correa, 20.0, 7.0, ancho + 4)
        notas = [NOTA_INTERIOR, "Sin tubo propio: la culata fija envuelve el tubo de amortiguador."]
        sockets = _sockets(x_correa, y_correa, interfaz_tubo=self.requiere_de(p)[0])
        return Geometria(cuerpo, sockets, (), tuple(notas), nominales_de(cuerpo), vaciados=8)


# --- Plegable lateral --------------------------------------------------------------------------------------------
class CulataPlegableLateral(Familia):
    id = "culata.plegable_lateral"
    nombre = "Culata plegable lateral (adaptador de AR genérico)"
    material = "mat.polimero_negro"
    requiere = (INTERFAZ_PLEGABLE,)
    ofrece = (INTERFAZ_CORREA,)
    parametros = (
        Parametro(
            "longitud_brazo", "Longitud del brazo desplegado desde la bisagra", float, "mm", 150, 260, de_sku=True
        ),
        Parametro("alto_cantonera", "Altura de la cantonera", float, "mm", 50, 120, de_sku=True),
        Parametro("desplazamiento_bisagra", "Distancia de la bisagra al eje", float, "mm", 26, 44, de_sku=True),
        Parametro("plegada", "Culata plegada hacia delante", bool, por_defecto=False),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Culata plegable lateral de {mm(p, 'longitud_brazo')} ({'plegada' if p['plegada'] else 'desplegada'})"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo_brazo, alto = float(p["longitud_brazo"]), float(p["alto_cantonera"])
        zh = float(p["desplazamiento_bisagra"])
        xh = -34.0
        # Adaptador: anillo alrededor del tubo con un hombro lateral hacia la bisagra.
        adaptador = cuerpo_por_secciones(
            0.0,
            46.0,
            (
                (0.0, 21.0, 21.0, zh + 9.0, 21.0, 3.0, 0.0, 0.0),
                (0.5, 22.0, 22.0, zh + 10.0, 22.0, 3.2, 0.0, 0.0),
                (1.0, 20.0, 20.0, zh + 8.0, 20.0, 3.0, 0.0, 0.0),
            ),
        )
        adaptador = adaptador - cilindro_en("x", 15.2, 48.0, (-23.0, 0, 0))
        adaptador = adaptador + cilindro_en("x", 17.0, 4.0, (-48.0, 0, 0)) - cilindro_en("x", 15.2, 6.0, (-48.0, 0, 0))
        # Bisagra: pasador vertical con cabeza.
        pasador = cilindro_en("y", 6.5, 40.0, (xh, 0, zh)) + cilindro_en("y", 8.5, 3.0, (xh, 21.5, zh))
        pasador = pasador + cilindro_en("y", 8.5, 3.0, (xh, -21.5, zh))
        botón = cilindro_en("z", 5.5, 4.0, (-12.0, 0, -(21.0 + 1.5)))
        # Brazo: dos largueros curvos con una ventana de aligeramiento, unidos al frente y a la cantonera.
        x_r = xh - largo_brazo
        pts_ext = [
            (xh + 8, 14.0),
            (xh - 0.30 * largo_brazo, 20.0),
            (xh - 0.70 * largo_brazo, 25.0),
            (x_r + 10, 32.0),
            (x_r, 30.0),
            (x_r + 2, -alto + 18.0),
            (x_r + 12, -alto + 2.0),
            (xh - 0.60 * largo_brazo, -26.0),
            (xh - 0.25 * largo_brazo, -20.0),
            (xh + 8, -14.0),
        ]
        brazo = extruir_perfil([Spline(*pts_ext, periodic=True)], 13.0)
        ventana = [
            (xh - 0.22 * largo_brazo, 7.0),
            (xh - 0.45 * largo_brazo, 10.0),
            (xh - 0.68 * largo_brazo, 14.0),
            (xh - 0.67 * largo_brazo, -12.0),
            (xh - 0.45 * largo_brazo, -12.0),
            (xh - 0.22 * largo_brazo, -7.0),
        ]
        brazo = brazo - extruir_perfil([Spline(*ventana, periodic=True)], 16.0)
        brazo = filetear(brazo, 1.0)
        brazo = Pos(0, 0, zh) * brazo
        # Cantonera: placa lofteada que vuelve hacia el eje, con estrías.
        placa = cuerpo_por_secciones(
            x_r + 14.0,
            16.0,
            (
                (0.0, 31.0, alto - 18.0, 8.0, 8.0, 3.0, 0.0, zh),
                (0.6, 32.0, alto - 12.0, 16.0, 22.0, 3.1, 0.0, zh - 8.0),
                (1.0, 30.0, alto - 14.0, 13.0, 19.0, 3.0, 0.0, zh - 8.0),
            ),
        )
        x_tras = x_r + 14.0 - 16.0
        estrias = _estrias_cantonera(x_tras, -alto + 22.0, 24.0, 40.0)
        if estrias is not None:
            placa = placa - Pos(0, 0, zh - 8.0) * estrias
        mov = brazo + placa
        mov = mov - estadio_en_z(x_r + 12.0, -alto + 14.0, 18.0, 6.0, 60.0, zh - 4.0)
        if bool(p["plegada"]):
            mov = Pos(xh, 0, zh) * Rot(0, 180, 0) * Pos(-xh, 0, -zh) * mov
        cuerpo = adaptador + pasador + botón + mov
        sockets = (
            Socket(
                "tubo",
                (0.0, 0.0, 0.0),
                INTERFAZ_PLEGABLE,
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {"referencia": "centro de la cara delantera del adaptador"},
            ),
            Socket(
                "correa",
                (x_r + 12.0, -alto + 14.0, zh - 4.0)
                if not p["plegada"]
                else (xh + (xh - (x_r + 12.0)), -alto + 14.0, zh + 4.0),
                INTERFAZ_CORREA,
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 0.0),
                {"referencia": "centro de la anilla de correa"},
            ),
        )
        notas = [
            NOTA_INTERIOR,
            "Brazo y cantonera descentrados hacia la bisagra (forma genérica); sin mecanismo de bloqueo.",
        ]
        return Geometria(cuerpo, sockets, (), tuple(notas), nominales_de(cuerpo), vaciados=6)


# --- Skeleton ----------------------------------------------------------------------------------------------------
class CulataSkeleton(Familia):
    id = "culata.skeleton"
    nombre = "Culata esqueleto (skeleton)"
    material = "mat.polimero_negro"
    parametros = (
        _ESPEC,
        _INCLUIR,
        _TUBO,
        Parametro("longitud", "Longitud total desde el receptor", float, "mm", 170, 280, de_sku=True),
        Parametro("alto_cantonera", "Altura de la cantonera", float, "mm", 70, 140, de_sku=True),
        Parametro("ancho", "Separación exterior entre largueros", float, "mm", 34, 60, de_sku=True),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (INTERFAZ_CORREA,)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Culata skeleton de {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, ancho = float(p["longitud"]), float(p["alto_cantonera"]), float(p["ancho"])
        z_l = ancho / 2 - 3.5
        x_r = -largo
        d_tubo = float(p["diametro_tubo"]) if p["diametro_tubo"] is not None else 29.0
        collar = cuerpo_por_secciones(
            -2.0,
            32.0,
            (
                (0.0, 21.0, 21.0, ancho / 2, ancho / 2, 3.0, 0.0, 0.0),
                (0.5, 22.0, 22.0, ancho / 2 + 0.5, ancho / 2 + 0.5, 3.2, 0.0, 0.0),
                (1.0, 20.0, 20.0, ancho / 2, ancho / 2, 3.0, 0.0, 0.0),
            ),
        ) - cilindro_en("x", d_tubo / 2 + 0.2, 34.0, (-19.0, 0, 0))
        marco_ext = [
            (-10.0, 22.0),
            (-0.40 * largo, 26.0),
            (x_r + 22.0, 30.0),
            (x_r + 5.0, 29.0),
            (x_r, 20.0),
            (x_r + 1.0, -alto + 20.0),
            (x_r + 8.0, -alto + 3.0),
            (x_r + 30.0, -alto + 10.0),
            (-0.62 * largo, -alto * 0.40),
            (-0.30 * largo, -27.0),
            (-10.0, -22.0),
        ]
        marco = extruir_perfil([Spline(*marco_ext, periodic=True)], 7.0)
        ventana = [
            (-0.12 * largo, 8.0),
            (-0.18 * largo, 14.5),
            (-0.40 * largo, 17.0),
            (-0.66 * largo, 15.0),
            (-0.72 * largo, 0.0),
            (-0.69 * largo, -alto * 0.24),
            (-0.52 * largo, -alto * 0.26),
            (-0.35 * largo, -20.0),
            (-0.20 * largo, -14.0),
            (-0.12 * largo, -4.0),
        ]
        marco = marco - extruir_perfil([Spline(*ventana, periodic=True)], 9.0)
        marco = filetear(marco, 1.2)
        largueros = Pos(0, 0, z_l) * marco + Pos(0, 0, -z_l) * marco
        # Cantonera curva que une los dos largueros, y travesaños.
        placa = cuerpo_por_secciones(
            x_r + 16.0,
            18.0,
            (
                (0.0, 30.0, alto - 6.0, ancho / 2 - 1.0, ancho / 2 - 1.0, 3.2, 0.0, 0.0),
                (0.5, 31.0, alto - 4.0, ancho / 2, ancho / 2, 3.3, 0.0, 0.0),
                (1.0, 28.0, alto - 7.0, ancho / 2 - 3.0, ancho / 2 - 3.0, 3.0, 0.0, 0.0),
            ),
        )
        estrias = _estrias_cantonera(x_r + 16.0 - 18.0, -alto + 10, 24.0, ancho * 0.7)
        if estrias is not None:
            placa = placa - estrias
        travesano = cilindro_en("z", 4.2, ancho - 4.0, (-0.42 * largo, -alto * 0.05, 0))
        cuerpo = collar + largueros + placa + travesano
        x_correa, y_correa = x_r + 24.0, -alto + 12.0
        cuerpo = cuerpo - estadio_en_z(x_correa, y_correa, 18.0, 6.5, ancho + 4)
        notas = [NOTA_INTERIOR, "Largueros planos de proporción estimada; sin posiciones de ajuste."]
        tubo = _plantilla_tubo(p, largo - 14.0, 0, 12.0)
        if tubo is not None:
            cuerpo = cuerpo + tubo
            notas.append(NOTA_TUBO)
        sockets = _sockets(x_correa, y_correa, interfaz_tubo=self.requiere_de(p)[0])
        return Geometria(cuerpo, sockets, (), tuple(notas), nominales_de(cuerpo), vaciados=6)


# --- Brace de pistola (solo la forma) -----------------------------------------------------------------------------
class BraceDePistola(Familia):
    id = "culata.brace_pistola"
    nombre = "Brace estabilizador de antebrazo (forma genérica)"
    material = "mat.polimero_negro"
    parametros = (
        _ESPEC,
        _INCLUIR,
        _TUBO,
        Parametro("longitud", "Longitud total desde el receptor", float, "mm", 140, 260, de_sku=True),
        Parametro("ancho_mayor", "Ancho de la boca del brace", float, "mm", 40, 90, de_sku=True),
        Parametro("alto_mayor", "Alto de la boca del brace", float, "mm", 40, 90, de_sku=True),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Brace estabilizador de antebrazo de {mm(p, 'longitud')} (solo la forma)"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, zm, ym = float(p["longitud"]), float(p["ancho_mayor"]) / 2, float(p["alto_mayor"]) / 2
        d_tubo = float(p["diametro_tubo"]) if p["diametro_tubo"] is not None else 29.0
        cono = cuerpo_por_secciones(
            -26.0,
            largo - 26.0,
            (
                (0.00, 19.0, 19.0, 19.0, 19.0, 2.4, 0.0, 0.0),
                (0.18, 22.0, 22.0, 24.0, 24.0, 2.4, 0.0, 0.0),
                (0.55, 0.62 * ym + 8, 0.62 * ym + 8, 0.6 * zm + 8, 0.6 * zm + 8, 2.3, 0.0, 0.0),
                (0.92, ym, ym, zm, zm, 2.2, 0.0, 0.0),
                (1.00, ym * 0.93, ym * 0.93, zm * 0.93, zm * 0.93, 2.2, 0.0, 0.0),
            ),
        )
        # Manguito de unión al tubo, rehundido por delante.
        manguito = cuerpo_por_secciones(
            0.0,
            34.0,
            (
                (0.0, 19.5, 19.5, 19.5, 19.5, 2.3, 0.0, 0.0),
                (1.0, 20.0, 20.0, 20.0, 20.0, 2.3, 0.0, 0.0),
            ),
        )
        cuerpo = cono + manguito
        # Canal del antebrazo: cortado en la cara izquierda (+Z), con el fondo redondo.
        x_c0, x_c1 = -0.34 * largo, -largo - 2.0
        canal = cilindro_en("x", 0.5 * ym + 1.0, abs(x_c1 - x_c0), ((x_c0 + x_c1) / 2, 0, zm * 0.62 + 0.45 * ym))
        cuerpo = cuerpo - canal
        # Dos ojales para la correa y un taladro de fijación del cierre trasero.
        cuerpo = cuerpo - estadio_en_z(-0.55 * largo, -0.3 * ym, 22.0, 7.0, 2 * zm + 4)
        cuerpo = cuerpo - estadio_en_z(-0.8 * largo, -0.3 * ym, 22.0, 7.0, 2 * zm + 4)
        cuerpo = cuerpo - cilindro_en("x", d_tubo / 2 + 0.2, 26.0, (-13.0, 0, 0))
        notas = [
            NOTA_INTERIOR,
            "Solo la forma de un brace de antebrazo genérico: sin correa, sin ligar a ningún arma real.",
        ]
        tubo = _plantilla_tubo(p, largo - 20.0, 0, 12.0)
        if tubo is not None:
            cuerpo = cuerpo + tubo
            notas.append(NOTA_TUBO)
        socket = Socket(
            "tubo",
            (0.0, 0.0, 0.0),
            self.requiere_de(p)[0],
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            {"referencia": "centro de la cara delantera del tubo"},
        )
        return Geometria(cuerpo, (socket,), (), tuple(notas), nominales_de(cuerpo), vaciados=4)


FAMILIAS_CULATAS: dict[str, Familia] = {
    f.id: f
    for f in (
        CulataTelescopica6(),
        CulataTelescopicaPolimero(),
        CulataFijaA2(),
        CulataPlegableLateral(),
        CulataSkeleton(),
        BraceDePistola(),
    )
}

__all__ = ["FAMILIAS_CULATAS"]
