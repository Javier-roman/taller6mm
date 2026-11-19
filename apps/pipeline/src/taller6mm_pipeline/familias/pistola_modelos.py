"""Hi-Capa y Glock de airsoft: armazones con forma real, cachas de la Hi-Capa y cargadores de gas.

Sustituye al armazón del primer borrador (`pistola_armazon.py`, un bloque con un agarre lofteado a facetas). Aquí cada
armazón sale de un perfil lateral con esquinas redondeadas (`Face.fillet_2d`) extruido a lo ancho, y el agarre, la
guarda, los mandos y el texturizado se añaden encima. Todo en el origen común de pistola (`pistola_comun`): +X boca,
+Y arriba, +Z izquierda, cara trasera de la corredera en X = 0, eje del cañón en Y = 0, apoyo de la corredera en
`PLANO_CORREDERA_Y`.

- **Glock (polímero)**: cubrecañón con riel de accesorios, agarre inclinado 22 grados con la espalda abombada, punteado
  en los dos costados, ranuras de dedos, guarda cuadrada con gatillo de dos piezas, palanca de retenida, botón del
  cargador, palanca de desmontaje y tres pasadores.
- **Hi-Capa (metal, doble columna estilo 1911)**: marco estrecho con el agarre ancho de doble columna, guarda
  cuadrada, martillo de anilla, seguro de empuñadura con cola de castor, seguro manual, palanca de retenida, botón del
  cargador, gatillo aligerado y cuatro casquillos para las cachas (`cacha.hicapa`, que van aparte).
- **Cargador de gas** (`cargador.gas_pistola`): cuerpo recto de perfil extruido, labios de alimentación, depósito más
  grueso, muesca de retenida, ventanas y base con válvula de carga.

Solo formas exteriores. Las proporciones son de barrido (`es_demo`): ninguna es la medida de un SKU, salvo el largo
total de la Hi-Capa 5.1 de Tokyo Marui (222 mm, ficha oficial en `docs/catalogo/cotas-publicas.md`), que se anota como
referencia de la cota global y no se aplica a ninguna pieza suelta.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from build123d import Box, Compound, Cylinder, Face, Pos, Rot, Sphere, Vector, Wire, extrude

from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear
from taller6mm_pipeline.familias.pistola_comun import (
    INTERFAZ_CAJA_EMPUNADURA,
    INTERFAZ_RIEL_CORREDERA,
    PLANO_CORREDERA_Y,
    estimada,
)
from taller6mm_pipeline.ficha import Confianza, Cota

Y0 = PLANO_CORREDERA_Y
POZO_GLOCK = "pozo-glock-gbb"  # catalogo/interfaces.json
POZO_HICAPA = "pozo-hi-capa"  # catalogo/interfaces.json
RIEL_UNIVERSAL = "rail-pistola-glock-universal"
ESTILOS = ("glock", "hicapa")
RIEL_Z = 7.6  # posición lateral de los raíles de la corredera: caben en el canal de la corredera (19,2 mm)
POZO_H = 70.0  # profundidad del pozo del cargador (mm) y altura útil del cargador dentro del agarre
FUENTE_TM_HICAPA = "https://www.tokyo-marui.co.jp/products/gas/blowback/55 (ficha oficial Hi-Capa 5.1 Government)"
DESCARTADAS: list[str] = []


# --- Utilidades de perfil y booleanas ------------------------------------------------------------------------------


def cara(puntos: Sequence[tuple[float, float, float]]) -> Face:
    """Cara plana (plano XY) por los puntos `(x, y, radio)`; el radio redondea esa esquina (0 = viva)."""
    f = Face(Wire.make_polygon([Vector(x, y, 0.0) for x, y, _ in puntos], close=True))
    for x, y, r in puntos:
        if r > 0:
            v = min(f.vertices(), key=lambda q: (q.X - x) ** 2 + (q.Y - y) ** 2)
            for rr in (r, r * 0.6, r * 0.35):
                try:
                    f = f.fillet_2d(rr, [v])
                    break
                except ValueError:
                    continue
    return f


def prisma(puntos: Sequence[tuple[float, float, float]], ancho: float, z: float = 0.0) -> Any:
    """Perfil lateral extruido `ancho` mm en Z, centrado en `z`."""
    return Pos(0, 0, z) * extrude(cara(puntos), amount=ancho / 2, both=True)


def _valido(s: Any) -> bool:
    try:
        return bool(s.is_valid) and s.volume > 0 and len(s.solids()) == 1
    except Exception:
        return False


def aplicar(base: Any, piezas: Sequence[Any], op: str, etiqueta: str) -> Any:
    """Une o resta las piezas de una en una; si una deja un sólido inválido o partido se omite y se anota."""
    for i, p in enumerate(piezas):
        try:
            nuevo = base.fuse(p) if op == "fuse" else base.cut(p)
        except Exception:
            nuevo = None
        if nuevo is not None and _valido(nuevo):
            base = nuevo
        else:
            DESCARTADAS.append(f"{etiqueta}:{op}#{i}")
    return base


def punteado(sitio: Any, puntos: Sequence[tuple[float, float, float]], radio: float) -> Any:
    return sitio * Compound([Pos(*q) * Sphere(radio) for q in puntos])


def rejilla(x0: float, x1: float, y0: float, y1: float, paso: float) -> list[tuple[float, float]]:
    """Rejilla hexagonal de puntos dentro del rectángulo."""
    pts: list[tuple[float, float]] = []
    fila, y = 0, y0
    alto = paso * math.sqrt(3) / 2
    while y <= y1:
        x = x0 + (paso / 2 if fila % 2 else 0.0)
        while x <= x1:
            pts.append((x, y))
            x += paso
        y += alto
        fila += 1
    return pts


class _Agarre:
    """Geometría del agarre inclinado: puntos de las esquinas y el marco local (u a lo largo, v hacia atrás)."""

    def __init__(self, inc: float, alto: float, prof: float, y_top_front: float, y_trasera: float, x_trasera: float):
        th = math.radians(inc)
        self.inc, self.th = inc, th
        self.sx, self.cs = math.sin(th), math.cos(th)
        u = (-self.sx, -self.cs)  # baja y se inclina hacia atrás
        atras = (-self.cs, self.sx)  # perpendicular, hacia atrás
        f1 = (u[0] * alto, y_top_front + u[1] * alto)  # base delantera relativa a x_f = 0
        r1 = (f1[0] + atras[0] * prof, f1[1] + atras[1] * prof)
        alto2 = (y_trasera - r1[1]) / self.cs
        r0 = (r1[0] + self.sx * alto2, y_trasera)
        self.x_f = x_trasera - r0[0]  # desplaza todo para que el dorso arranque en x_trasera
        self.y_f = y_top_front
        self.f1 = (self.x_f + f1[0], f1[1])
        self.r1 = (self.x_f + r1[0], r1[1])
        self.r0 = (x_trasera, y_trasera)
        self.alto, self.prof = alto, prof
        self.u, self.atras = u, atras

    def punto(self, t: float, s: float) -> tuple[float, float]:
        """Punto del agarre a la fracción `t` de la altura (0 arriba) y distancia `s` hacia atrás desde el frente."""
        return (
            self.x_f + self.u[0] * t * self.alto + self.atras[0] * s,
            self.y_f + self.u[1] * t * self.alto + self.atras[1] * s,
        )

    def sitio(self) -> Any:
        """Marco con el origen en el frente arriba, +X hacia atrás (s), +Y a lo largo del agarre hacia arriba."""
        return Pos(self.x_f, self.y_f, 0) * Rot(0, 0, -self.inc)


def perfil_agarre(a: _Agarre, y_sup: float, rad_base: float = 4.0) -> list[tuple[float, float, float]]:
    """Polígono del agarre (con las esquinas redondeadas) desde `y_sup` hasta la base."""
    f0 = (a.x_f + a.sx * (a.y_f - y_sup) / a.cs, y_sup)
    return [
        (a.r0[0], y_sup, 7.0),
        (f0[0], y_sup, 0.0),
        (a.f1[0], a.f1[1], rad_base),
        (a.r1[0], a.r1[1], rad_base * 0.8),
    ]


# --- Armazón ------------------------------------------------------------------------------------------------------


class ArmazonPistola(Familia):
    id = "armazon.pistola"
    version = 1
    nombre = "Armazón de pistola (Glock de polímero o Hi-Capa metálica)"
    requiere = ()
    ofrece = (INTERFAZ_RIEL_CORREDERA, INTERFAZ_CAJA_EMPUNADURA, POZO_GLOCK, POZO_HICAPA, RIEL_UNIVERSAL)
    material = "mat.polimero_negro"
    parametros = (
        Parametro("estilo", "Glock de polímero o Hi-Capa de doble columna", str, opciones=ESTILOS, por_defecto="glock"),
        Parametro("largo", "Largo del armazón (frente del cubrecañón)", float, "mm", 100, 220, de_sku=True),
        Parametro("alto_empunadura", "Alto del agarre bajo el cubrecañón", float, "mm", 60, 130, de_sku=True),
        Parametro("profundidad", "Profundidad delante-detrás del agarre", float, "mm", 30, 60, de_sku=True),
        Parametro("ancho", "Ancho del agarre (con las cachas en la Hi-Capa)", float, "mm", 22, 38, de_sku=True),
        Parametro("inclinacion", "Inclinación del agarre hacia atrás", float, "grados", 8, 30, de_sku=True),
        Parametro("textura", "Textura del agarre (Glock)", str, opciones=("punteado", "liso"), por_defecto="punteado"),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return ()

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        if p["estilo"] == "glock":
            return (INTERFAZ_RIEL_CORREDERA, POZO_GLOCK, RIEL_UNIVERSAL)
        return (INTERFAZ_RIEL_CORREDERA, POZO_HICAPA, INTERFAZ_CAJA_EMPUNADURA)

    def describir(self, p: Mapping[str, Valor]) -> str:
        quien = "Glock de polímero" if p["estilo"] == "glock" else "Hi-Capa metálica de doble columna"
        return f"Armazón {quien} de {mm(p, 'largo')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        return (_glock if p["estilo"] == "glock" else _hicapa)(p)


def _anillo_guarda(
    exterior: Sequence[tuple[float, float, float]], interior: Sequence[tuple[float, float, float]], ancho: float
) -> Any:
    return prisma(exterior, ancho) - prisma(interior, ancho + 2.0)


def _mandos_comunes(cuerpo: Any, cw: float, x_boton: float, y_boton: float, radio_boton: float) -> list[Any]:
    boton = filetear(cilindro_en("z", radio_boton, 3.4, (x_boton, y_boton, cw / 2 + 0.9)), 0.8)
    return [boton]


def _glock(p: Mapping[str, Valor]) -> Geometria:
    largo, alto, prof = float(p["largo"]), float(p["alto_empunadura"]), float(p["profundidad"])
    ancho, inc = float(p["ancho"]), float(p["inclinacion"])
    cw = min(ancho - 6.0, 24.0)  # ancho del cubrecañón y el chasis
    y_dc = Y0 - 17.5  # cara inferior del cubrecañón
    a = _Agarre(inc, alto, prof, y_dc, Y0 - 12.0, 3.0)
    vaciados = 0
    # 1. Chasis superior: del culatín (cola de castor) al frente del cubrecañón.
    chasis = prisma(
        [
            (-1.5, Y0 + 2.0, 2.0),
            (largo, Y0, 1.6),
            (largo, Y0 - 12.5, 1.6),
            (largo - 5.0, y_dc, 3.2),
            (a.x_f + 2.0, y_dc, 0.0),
            (a.x_f - 1.5, y_dc - 6.0, 0.0),
            (a.r0[0], a.r0[1], 8.0),
            (-4.0, Y0 - 5.5, 6.0),
        ],
        cw,
    )
    chasis = filetear(
        chasis, 1.4, [e for e in chasis.edges() if abs(abs(e.center().Z) - cw / 2) < 0.02 and y_dc - 1 < e.center().Y]
    )
    # 2. Agarre: perfil redondeado, más ancho que el chasis, con los cantos laterales redondeados.
    agarre = prisma(perfil_agarre(a, y_dc + 3.0, 5.0), ancho)
    agarre = filetear(agarre, 3.4, [e for e in agarre.edges() if abs(abs(e.center().Z) - ancho / 2) < 0.02])
    # 3. Guarda cuadrada y gatillo.
    xg = a.x_f + 37.0
    ext = [
        (a.x_f - 4.0, y_dc + 2.0, 0.0),
        (xg, y_dc + 2.0, 0.0),
        (xg + 3.0, y_dc - 9.0, 4.5),
        (xg - 3.0, y_dc - 18.0, 7.0),
        (a.x_f - 7.0, y_dc - 18.0, 4.0),
    ]
    inte = [
        (a.x_f + 4.0, y_dc, 0.0),
        (xg - 4.0, y_dc, 0.0),
        (xg - 1.5, y_dc - 8.5, 3.0),
        (xg - 6.0, y_dc - 14.6, 5.0),
        (a.x_f - 1.5, y_dc - 14.6, 3.0),
    ]
    guarda = _anillo_guarda(ext, inte, 13.0)
    guarda = filetear(guarda, 1.2, [e for e in guarda.edges() if abs(abs(e.center().Z) - 6.5) < 0.02])
    gat = prisma(
        [
            (a.x_f + 10.0, y_dc + 1.0, 0.0),
            (a.x_f + 17.0, y_dc - 8.0, 3.0),
            (a.x_f + 21.0, y_dc - 15.0, 2.0),
            (a.x_f + 23.5, y_dc - 18.0, 1.2),
            (a.x_f + 19.0, y_dc - 19.0, 1.2),
            (a.x_f + 14.0, y_dc - 12.5, 3.0),
            (a.x_f + 8.0, y_dc - 3.0, 1.5),
        ],
        7.0,
    )
    gat = filetear(gat, 0.6, [e for e in gat.edges() if abs(abs(e.center().Z) - 3.5) < 0.02])
    seguro_gat = prisma(
        [
            (a.x_f + 15.5, y_dc - 6.0, 1.0),
            (a.x_f + 21.0, y_dc - 14.0, 1.2),
            (a.x_f + 19.0, y_dc - 14.5, 1.0),
            (a.x_f + 14.0, y_dc - 6.0, 1.0),
        ],
        2.6,
        z=0.0,
    )
    cuerpo = aplicar(chasis, [agarre, guarda, gat, seguro_gat], "fuse", "glock")
    # 4. Raíles de la corredera, bloque de cierre y mandos.
    piezas: list[Any] = []
    for z in (-RIEL_Z, RIEL_Z):
        for x0, x1 in ((20.0, 92.0), (118.0, largo - 12.0)):
            piezas.append(Pos((x0 + x1) / 2, Y0 + 1.5, z) * Box(x1 - x0, 3.6, 2.2))
    piezas.append(Pos(104.0, Y0 + 1.0, 0) * Box(20.0, 2.0, 2 * RIEL_Z))
    # palanca de retenida de corredera (izquierda), botón del cargador, palanca de desmontaje y pasadores
    palanca = prisma(
        [
            (a.x_f + 14.0, Y0 - 4.0, 1.0),
            (a.x_f + 55.0, Y0 - 4.0, 1.5),
            (a.x_f + 59.0, Y0 - 7.5, 2.0),
            (a.x_f + 52.0, Y0 - 9.2, 1.0),
            (a.x_f + 16.0, Y0 - 9.0, 1.0),
        ],
        2.4,
        z=cw / 2 + 0.6,
    )
    piezas += [palanca]
    piezas += _mandos_comunes(cuerpo, ancho, a.x_f + 10.0, y_dc - 9.0, 3.6)
    piezas.append(filetear(cilindro_en("z", 3.6, cw + 2.4, (largo * 0.52, Y0 - 12.0, 0.0)), 0.5))  # eje de desmontaje
    for xp in (largo * 0.50, largo * 0.38, a.x_f - 2.0):  # pasadores
        piezas.append(cilindro_en("z", 1.7, cw + 0.8, (xp, y_dc + 5.2 if xp == a.x_f - 2.0 else Y0 - 15.2, 0.0)))
    cuerpo = aplicar(cuerpo, piezas, "fuse", "glock-mandos")
    # 5. Cortes: riel de accesorios, ranuras de dedos, pozo del cargador, base abierta, texturizado.
    cortes: list[Any] = []
    for i in range(2):
        cortes.append(Pos(largo - 40.0 + i * 12.0, y_dc, 0) * Box(3.6, 3.8, 14.0))
    sitio = a.sitio()
    for k in range(3):  # ranuras de los dedos en la cara delantera del agarre
        t = 0.34 + 0.16 * k
        cx, cy = a.punto(t, 0.0)
        cortes.append(
            Pos(cx + 3.7, cy, 0) * Rot(0, 0, -inc) * Pos(0, 0, 0) * cilindro_en("z", 5.2, ancho * 0.84, (0, 0, 0))
        )
    pozo = a.sitio() * Pos(-prof / 2, -alto + POZO_H / 2 - 1.0, 0) * Box(prof - 8.0, POZO_H + 2.0, 24.0)
    cortes.append(filetear(pozo, 2.2, [e for e in pozo.edges() if abs(e.length - POZO_H - 2.0) < 0.01]))
    if p["textura"] == "punteado":
        pts = []
        for xs_, ys_ in rejilla(7.0, prof - 7.0, 12.0, alto * 0.86, 4.3):
            for lado in (1, -1):
                pts.append((-xs_, -ys_, lado * (ancho / 2 + 0.55)))
        cortes.append(punteado(sitio, pts, 1.1))
    # Marcas horizontales de la espalda (en el dorso, de arriba abajo).
    for k in range(6):
        t = 0.28 + 0.11 * k
        cx, cy = a.punto(t, prof)
        cortes.append(Pos(cx, cy, 0) * Rot(0, 0, -inc) * Box(2.4, 1.0, ancho * 0.7))
    cuerpo = aplicar(cuerpo, cortes, "cut", "glock-cortes")
    vaciados = len(cortes) + len(piezas)
    sockets = (
        Socket("corredera", (0.0, Y0, 0.0), INTERFAZ_RIEL_CORREDERA, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}),
        Socket(
            "cargador",
            _centro_pozo(a, alto),
            POZO_GLOCK,
            (a.u[0], a.u[1], 0.0),
            (-a.u[1], a.u[0], 0.0),
            {"inclinacion_grados": inc},
        ),
        Socket("riel_accesorios", (largo - 34.0, y_dc, 0.0), RIEL_UNIVERSAL, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
    )
    cotas = (estimada("armazon.ancho_cubrecanon", cw), estimada("armazon.inclinacion_agarre", inc))
    notas = (
        "Solo forma exterior: el chasis metálico interior, el seguro del gatillo y la mecánica no se modelan.",
        "Silueta, ranuras de los dedos, punteado y mandos estimados; el riel de accesorios no es un Picatinny.",
        "El pozo del cargador es un hueco liso de medida estimada, sin los rebajes de la retenida.",
    )
    caja = cuerpo.bounding_box()
    return Geometria(cuerpo, sockets, cotas, notas, (caja.size.X, caja.size.Y, caja.size.Z), vaciados=vaciados)


def _centro_pozo(a: _Agarre, alto: float) -> tuple[float, float, float]:
    """Centro de la boca superior del pozo (donde queda la cara superior del cargador)."""
    x, y = a.punto((alto - POZO_H) / alto, a.prof / 2)
    return (x, y, 0.0)


def _hicapa(p: Mapping[str, Valor]) -> Geometria:
    largo, alto, prof = float(p["largo"]), float(p["alto_empunadura"]), float(p["profundidad"])
    ancho, inc = float(p["ancho"]), float(p["inclinacion"])
    nucleo = ancho - 10.0  # grosor del marco entre cachas
    y_dc = Y0 - 15.0
    a = _Agarre(inc, alto, prof, y_dc - 4.0, Y0 - 13.0, 2.5)
    # 1. Marco: cubrecañón corto con rampa, culatín con la cola del seguro y agarre estrecho de metal.
    marco = prisma(
        [
            (-3.0, Y0 - 2.0, 3.0),
            (4.0, Y0, 0.0),
            (largo, Y0, 1.4),
            (largo, y_dc + 3.0, 1.4),
            (largo - 6.0, y_dc, 2.5),
            (a.x_f + 4.0, y_dc, 0.0),
            (a.x_f - 1.0, y_dc - 8.0, 0.0),
            (a.r0[0], a.r0[1], 7.0),
            (-5.0, Y0 - 9.0, 6.0),
        ],
        nucleo,
    )
    agarre = prisma(perfil_agarre(a, y_dc, 4.0), nucleo)
    marco = aplicar(marco, [agarre], "fuse", "hicapa")
    # 2. Guarda cuadrada con gancho, gatillo aligerado (tres taladros) y arco del muelle en la espalda.
    xg = a.x_f + 36.0
    ext = [
        (a.x_f - 2.0, y_dc + 2.0, 0.0),
        (xg, y_dc + 2.0, 0.0),
        (xg + 2.0, y_dc - 10.0, 5.0),
        (xg - 2.0, y_dc - 20.0, 6.0),
        (a.x_f - 8.0, y_dc - 20.0, 3.0),
    ]
    inte = [
        (a.x_f + 4.0, y_dc, 0.0),
        (xg - 4.0, y_dc, 0.0),
        (xg - 2.0, y_dc - 9.0, 3.0),
        (xg - 6.0, y_dc - 16.0, 4.0),
        (a.x_f - 2.0, y_dc - 16.0, 2.0),
    ]
    guarda = _anillo_guarda(ext, inte, nucleo)
    guarda = filetear(guarda, 1.0, [e for e in guarda.edges() if abs(abs(e.center().Z) - nucleo / 2) < 0.02])
    gat = prisma(
        [
            (a.x_f + 8.0, y_dc + 1.0, 0.0),
            (a.x_f + 17.0, y_dc - 9.0, 3.0),
            (a.x_f + 21.0, y_dc - 17.0, 2.0),
            (a.x_f + 18.0, y_dc - 19.5, 1.2),
            (a.x_f + 12.0, y_dc - 12.0, 3.0),
            (a.x_f + 6.0, y_dc - 3.0, 1.0),
        ],
        8.0,
    )
    for k in range(3):
        gat = gat - cilindro_en("z", 1.5, 10.0, (a.x_f + 11.0 + k * 3.0, y_dc - 6.0 - k * 4.2, 0.0))
    # 3. Mandos: martillo de anilla, seguro de empuñadura con cola de castor, seguro manual, retenida y botón.
    martillo = cilindro_en("z", 6.2, 7.0, (-4.2, Y0 - 5.0, 0.0)) - cilindro_en("z", 3.6, 9.0, (-4.2, Y0 - 5.0, 0.0))
    martillo = martillo + Pos(-1.6, Y0 - 8.0, 0) * Box(3.6, 6.0, 5.0)
    cola = prisma(
        [
            (-8.0, Y0 - 2.0, 2.0),
            (a.r0[0] - 2.5, Y0 - 12.0, 6.0),
            (a.r0[0] - 1.0, a.r0[1] - 18.0, 4.0),
            (a.r0[0] + 7.0, a.r0[1] - 14.0, 3.0),
            (6.0, Y0 - 6.0, 0.0),
        ],
        nucleo * 0.92,
    )
    cola = filetear(cola, 1.4, [e for e in cola.edges() if abs(abs(e.center().Z) - nucleo * 0.46) < 0.02])
    seguro = prisma(
        [
            (6.0, Y0 - 5.0, 1.2),
            (30.0, Y0 - 5.0, 1.5),
            (34.5, Y0 - 8.0, 3.0),
            (29.0, Y0 - 11.0, 1.5),
            (6.0, Y0 - 10.5, 1.2),
        ],
        2.6,
        z=nucleo / 2 + 1.3,
    )
    seguro_der = prisma(
        [(8.0, Y0 - 5.5, 1.0), (20.0, Y0 - 5.5, 1.2), (22.0, Y0 - 9.5, 1.5), (8.0, Y0 - 9.5, 1.0)],
        2.2,
        z=-nucleo / 2 - 1.1,
    )
    retenida = prisma(
        [
            (a.x_f - 22.0, Y0 - 9.0, 1.0),
            (a.x_f + 18.0, Y0 - 9.0, 1.5),
            (a.x_f + 22.0, Y0 - 12.0, 2.0),
            (a.x_f + 14.0, Y0 - 14.5, 1.0),
            (a.x_f - 22.0, Y0 - 14.0, 1.0),
        ],
        2.4,
        z=nucleo / 2 + 1.2,
    )
    boton = filetear(cilindro_en("z", 3.4, 3.4, (a.x_f + 9.0, y_dc - 10.0, nucleo / 2 + 1.6)), 0.8)
    # Casquillos para las cachas: cuatro por lado, en la zona del agarre.
    casquillos = []
    for t, s in ((0.12, 8.0), (0.12, prof - 9.0), (0.62, 8.0), (0.62, prof - 9.0)):
        cx, cy = a.punto(t, s)
        for lado in (1, -1):
            casquillos.append(cilindro_en("z", 2.5, 2.2, (cx, cy, lado * (nucleo / 2 + 0.9))))
    # Marco: raíles de la corredera sobre el cubrecañón, bloque de cierre y ranura de tornillo de mira.
    rieles = []
    for z in (-RIEL_Z, RIEL_Z):
        for x0, x1 in ((22.0, 90.0), (100.0, largo - 8.0)):
            rieles.append(Pos((x0 + x1) / 2, Y0 + 1.4, z) * Box(x1 - x0, 3.2, 2.0))
    cuerpo = aplicar(
        marco,
        [guarda, gat, martillo, cola, seguro, seguro_der, retenida, boton, *casquillos, *rieles],
        "fuse",
        "hicapa-piezas",
    )
    pozo = a.sitio() * Pos(-prof / 2, -alto + POZO_H / 2 - 1.0, 0) * Box(prof - 6.0, POZO_H + 2.0, nucleo - 3.0)
    pozo = filetear(pozo, 2.0, [e for e in pozo.edges() if abs(e.length - POZO_H - 2.0) < 0.01])
    cortes = [pozo]
    # Muesca de la cara delantera (rebaje del dedo) y marcas del cubrecañón.
    for i in range(2):
        cortes.append(Pos(largo - 36.0 + i * 11.0, y_dc, 0) * Box(2.6, 3.0, nucleo * 0.8))
    cuerpo = aplicar(cuerpo, cortes, "cut", "hicapa-cortes")
    sockets = (
        Socket("corredera", (0.0, Y0, 0.0), INTERFAZ_RIEL_CORREDERA, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}),
        Socket(
            "cargador",
            _centro_pozo(a, alto),
            POZO_HICAPA,
            (a.u[0], a.u[1], 0.0),
            (-a.u[1], a.u[0], 0.0),
            {"inclinacion_grados": inc},
        ),
        Socket(
            "cacha_izq",
            (a.r0[0], a.r0[1], nucleo / 2),
            INTERFAZ_CAJA_EMPUNADURA,
            (0.0, 0.0, 1.0),
            (1.0, 0.0, 0.0),
            {"lado": "izq"},
        ),
        Socket(
            "cacha_der",
            (a.r0[0], a.r0[1], -nucleo / 2),
            INTERFAZ_CAJA_EMPUNADURA,
            (0.0, 0.0, -1.0),
            (1.0, 0.0, 0.0),
            {"lado": "der"},
        ),
    )
    cotas = (
        estimada("armazon.grosor_marco", nucleo),
        Cota(
            "armazon.largo_total_referencia",
            222.0,
            FUENTE_TM_HICAPA + "; largo total del arma, no del armazón",
            "2026-11-17",
            Confianza.ALTA,
        ),
    )
    notas = (
        "Solo forma exterior: la mecánica (disparador, muelle, seguro interno) no se modela.",
        "Silueta, guarda, mandos y casquillos estimados; las cachas van aparte (`cacha.hicapa`).",
        "El largo total de 222 mm es el de la ficha del fabricante para el arma completa y no se aplica al armazón.",
    )
    caja = cuerpo.bounding_box()
    return Geometria(cuerpo, sockets, cotas, notas, (caja.size.X, caja.size.Y, caja.size.Z), vaciados=len(cortes) + 8)


# --- Cachas de la Hi-Capa -----------------------------------------------------------------------------------------


class CachaHiCapa(Familia):
    id = "cacha.hicapa"
    version = 1
    nombre = "Cacha lateral de Hi-Capa (par izquierdo o derecho)"
    requiere = (INTERFAZ_CAJA_EMPUNADURA,)
    ofrece = ()
    material = "mat.polimero_negro"
    parametros = (
        Parametro("lado", "Izquierda o derecha", str, opciones=("izq", "der"), por_defecto="izq"),
        Parametro("alto_empunadura", "Alto del agarre bajo el cubrecañón", float, "mm", 60, 130, de_sku=True),
        Parametro("profundidad", "Profundidad delante-detrás del agarre", float, "mm", 30, 60, de_sku=True),
        Parametro("ancho", "Ancho del agarre con las cachas", float, "mm", 22, 38, de_sku=True),
        Parametro("inclinacion", "Inclinación del agarre hacia atrás", float, "grados", 8, 30, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cacha {p['lado']} de Hi-Capa con rejilla de agarre"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        alto, prof, ancho, inc = (float(p[k]) for k in ("alto_empunadura", "profundidad", "ancho", "inclinacion"))
        lado = 1 if p["lado"] == "izq" else -1
        nucleo, grueso = ancho - 10.0, 5.0
        y_dc = Y0 - 15.0
        a = _Agarre(inc, alto, prof, y_dc - 4.0, Y0 - 13.0, 2.5)
        z = lado * (nucleo / 2 + grueso / 2)
        # Perfil: contorno del agarre con el rebaje del pulgar arriba delante y la base redondeada.
        placa = prisma(
            [
                (a.r0[0] + 1.0, Y0 - 17.0, 6.0),
                (a.x_f + 2.0, a.y_f - 4.0, 5.0),
                (a.f1[0], a.f1[1], 4.0),
                (a.r1[0], a.r1[1], 4.0),
            ],
            grueso,
            z=z,
        )
        placa = filetear(
            placa, 1.2, [e for e in placa.edges() if abs(abs(e.center().Z) - (nucleo / 2 + grueso)) < 0.02]
        )
        # Rejilla de agarre: ranuras en V cruzadas a ±45 grados en la cara exterior.
        sitio = a.sitio()
        ranuras = []
        for k in range(-12, 13):
            for giro in (45.0, -45.0):
                ranuras.append(
                    sitio
                    * Pos(-prof / 2 + k * 3.6, -alto * 0.5, lado * (nucleo / 2 + grueso - 0.35))
                    * Rot(0, 0, giro)
                    * Box(0.7, alto * 1.4, 0.9)
                )
        zona = sitio * Pos(-prof / 2, -alto * 0.52, z) * Box(prof - 12.0, alto * 0.70, grueso + 4.0)
        corte = Compound(ranuras) & zona
        agujeros = [
            cilindro_en("z", 2.2, 2.0, (*a.punto(t, s), lado * (nucleo / 2 + grueso - 0.5)))
            for t, s in ((0.12, 8.0), (0.12, prof - 9.0), (0.62, 8.0), (0.62, prof - 9.0))
        ]
        cuerpo = aplicar(placa, [corte, *agujeros], "cut", "cacha")
        sockets = (
            Socket(
                "armazon",
                (a.r0[0], a.r0[1], lado * nucleo / 2),
                INTERFAZ_CAJA_EMPUNADURA,
                (0.0, 0.0, -float(lado)),
                (1.0, 0.0, 0.0),
                {"lado": str(p["lado"])},
            ),
        )
        notas = ("Rejilla en V y casquillos estimados; sin marcajes ni logotipos.",)
        caja = cuerpo.bounding_box()
        return Geometria(
            cuerpo,
            sockets,
            (estimada("cacha.grosor", grueso),),
            notas,
            (caja.size.X, caja.size.Y, caja.size.Z),
            vaciados=len(agujeros) + 1,
        )


# --- Cargadores de gas --------------------------------------------------------------------------------------------


class CargadorGasPistola(Familia):
    id = "cargador.gas_pistola"
    version = 1
    nombre = "Cargador de gas de pistola (Hi-Capa o Glock)"
    requiere = (POZO_GLOCK,)
    ofrece = ()
    material = "mat.acero_negro"
    parametros = (
        Parametro("estilo", "Hi-Capa o Glock", str, opciones=ESTILOS, por_defecto="glock"),
        Parametro("capacidad", "Capacidad en bolas", int, "ud", minimo=10, maximo=60),
        Parametro("altura", "Altura total del cargador", float, "mm", 70, 150, de_sku=True),
        Parametro("profundidad", "Profundidad delante-detrás", float, "mm", 24, 50, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", 16, 32, de_sku=True),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (POZO_GLOCK if p["estilo"] == "glock" else POZO_HICAPA,)

    def describir(self, p: Mapping[str, Valor]) -> str:
        quien = "Glock" if p["estilo"] == "glock" else "Hi-Capa"
        return f"Cargador de gas {quien} de {p['capacidad']} bolas"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        estilo = str(p["estilo"])
        H, hx, hz = float(p["altura"]), float(p["profundidad"]) / 2, float(p["ancho"]) / 2  # noqa: N806
        # Origen: centro de la cara superior; el cargador cuelga hacia -Y; +X es delante.
        cuerpo = prisma(
            [(hx, 0.0, 1.5), (hx, -H, 2.5), (-hx, -H, 2.5), (-hx, 0.0, 1.5)]
            if estilo == "hicapa"
            else [
                (hx, 0.0, 1.2),
                (hx, -H + 6.0, 2.0),
                (hx - 1.2, -H, 2.0),
                (-hx + 1.2, -H, 2.0),
                (-hx, -H + 6.0, 2.0),
                (-hx, 0.0, 1.2),
            ],
            2 * hz,
        )
        cuerpo = filetear(
            cuerpo,
            1.6 if estilo == "hicapa" else 1.2,
            [
                e
                for e in cuerpo.edges()
                if abs(abs(e.center().Z) - hz) < 0.02 and abs(e.center().Y) > 1.5 and abs(e.center().Y + H) > 1.5
            ][:24],
        )
        piezas: list[Any] = []
        cortes: list[Any] = []
        # Labios de alimentación: dos orejas que suben sobre la boca y se cierran en la mitad.
        for lado in (1, -1):
            piezas.append(filetear(Pos(-0.05 * hx, 1.6, lado * (hz - 1.0)) * Box(1.7 * hx, 4.0, 2.0), 0.6))
        piezas.append(filetear(Pos(0.45 * hx, 2.2, 0) * Box(0.7 * hx, 3.0, 2 * hz - 4.0), 0.8))  # tubo de alimentación
        # Base: placa ancha con reborde, pestaña delantera y válvula de carga de gas.
        base_k = 1.07 if estilo == "hicapa" else 1.04
        base = prisma(
            [
                (hx * base_k, -H + 8.0, 1.5),
                (hx * base_k, -H - 5.0, 3.0),
                (-hx * base_k, -H - 5.0, 3.0),
                (-hx * base_k, -H + 8.0, 1.5),
            ],
            2 * hz * base_k,
        )
        piezas.append(filetear(base, 1.2, [e for e in base.edges() if abs(abs(e.center().Z) - hz * base_k) < 0.02]))
        if estilo == "glock":  # tope de polímero que sobresale hacia delante
            piezas.append(filetear(Pos(hx * base_k + 2.4, -H - 1.5, 0) * Box(5.0, 6.0, 2 * hz * 0.8), 1.0))
        piezas.append(filetear(cilindro_en("y", 3.6, 5.0, (hx * 0.35, -H - 7.0, 0.0)), 0.5))  # válvula
        piezas.append(filetear(cilindro_en("y", 5.2, 2.0, (hx * 0.35, -H - 4.8, 0.0)), 0.4))  # tuerca
        # Muesca de la retenida (izquierda) y marcas.
        if estilo == "glock":
            cortes.append(Pos(hx * 0.2, -0.28 * H, hz) * Box(0.8 * hx, 7.0, 1.6))
            for k in range(6):  # taladros de recuento en la cara delantera
                cortes.append(cilindro_en("x", 1.3, 3.0, (hx - 1.0, -0.14 * H - k * 0.1 * H * 0.62, 0.0)))
            for k in range(3):  # nervaduras de agarre en la cola
                cortes.append(Pos(-hx + 0.3, -0.65 * H - k * 6.0, 0) * Box(1.0, 1.6, 2 * hz * 0.6))
        else:
            cortes.append(Pos(0.0, -0.25 * H, hz) * Box(hx * 0.9, 6.0, 1.6))
            cortes.append(
                Pos(0.0, -0.5 * H, 0.0) * Box(2.2, 0.55 * H, 2 * hz + 2.0)
            )  # ranura de visión del depósito (pasante)
        piezas_unidas = aplicar(cuerpo, piezas, "fuse", estilo)
        cuerpo = aplicar(piezas_unidas, cortes, "cut", estilo + "-cortes")
        sockets = (
            Socket(
                "pozo",
                (0.0, 0.0, 0.0),
                POZO_GLOCK if estilo == "glock" else POZO_HICAPA,
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
            ),
        )
        notas = (
            "Cuerpo macizo: el depósito de gas, el muelle y la válvula interna no se modelan.",
            "Labios, muesca de la retenida, ventanas y base estimados, sin cota de ningún SKU.",
            "La capacidad en bolas no se convierte en medidas.",
        )
        caja = cuerpo.bounding_box()
        return Geometria(
            cuerpo,
            sockets,
            (estimada("cargador.profundidad", 2 * hx), estimada("cargador.ancho", 2 * hz)),
            notas,
            (caja.size.X, caja.size.Y, caja.size.Z),
            vaciados=len(cortes) + 2,
        )


FAMILIAS_MODELOS = {f.id: f for f in (ArmazonPistola(), CachaHiCapa(), CargadorGasPistola())}
__all__ = ["DESCARTADAS", "FAMILIAS_MODELOS", "ArmazonPistola", "CachaHiCapa", "CargadorGasPistola"]
_ = (Cylinder,)
