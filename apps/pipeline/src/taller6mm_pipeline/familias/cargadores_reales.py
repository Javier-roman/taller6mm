"""Cargadores con forma real: STANAG de baja capacidad, estilo PMAG, mid-cap, hi-cap con rueda, GBBR y AK.

Sustituyen a la «silueta curva estimada» común de `tanda3_cuerpos.CargadorM4Forma` y `ak_cuerpos.CargadorAK`, que
sacaban casi la misma pieza para todos los tipos. Aquí cada tipo tiene su perfil de sección (el mid-cap abulta por
delante, el hi-cap es más ancho y lleva rueda de cuerda, el de GBBR es de chapa con depósito de gas y válvula) y sus
detalles propios (labios de alimentación, tubo de alimentación, nervaduras laterales, base con tope).

Ejes: +X boca, +Y arriba, +Z izquierda. Origen en el centro de la boca; el cargador cuelga hacia -Y y se curva hacia +X
(un arco de radio `R`). El cuerpo es un loft de secciones perpendiculares a la espina. Las nervaduras, el lomo y las
ranuras largas se modelan **dentro del propio perfil** (la sección crece o se hunde en su sitio): así no hay decenas de
booleanas sobre una superficie spline, que eran lentas y dejaban sólidos inválidos. Los detalles sueltos (labios,
tubo, base, rueda, válvula) se unen en el marco local de cada altura de la espina (x delante, y arriba, z lateral).

Datos honestos: el plano del STANAG 4179 no es público, así que largo, ancho y altura son parámetros de barrido
(`es_demo`), con tope T1 y sin publicar. Las pocas cifras con fuente (boca de 22,75 mm y tubo de alimentación de
Ø9,2 mm de una reseña, alto del mid-cap de 225 bolas de una ficha de tienda) van como cota de confianza baja; los
labios, nervaduras, rueda, válvula y la curvatura son proporciones estimadas y se declaran en las notas. Los modelos CC
BY del kit (`catalogo/kit-esencial-m4.json`) no están en este equipo: sin su malla, solo se tomó de referencia lo que
cuentan las fichas (capacidad, boca, alto) y las fotos CC de `referencias-cc.json` para el acabado.

No edita `cargador_m4.py`, `tanda3_cuerpos.py` ni `ak_cuerpos.py`: hereda de `CargadorM4` y `CargadorAK` solo sus
parámetros y su interfaz.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from build123d import Box, Pos, Rot, Solid, Wire
from build123d import Spline as _Spline

from taller6mm_pipeline.familias.ak_cuerpos import INT_POZO as INT_POZO_AK
from taller6mm_pipeline.familias.ak_cuerpos import CargadorAK
from taller6mm_pipeline.familias.base import Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.cargador_m4 import CargadorM4
from taller6mm_pipeline.familias.detalle import nominales_de
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, interpolar, loftear
from taller6mm_pipeline.familias.tanda3_comun import estimada, estriado
from taller6mm_pipeline.ficha import Confianza, Cota

INT_POZO_STANAG = "pozo-stanag-m4"
INT_POZO_GBBR = "pozo-gbbr-m4-mws"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
TIPOS = ("lowcap", "pmag", "midcap", "hicap", "gbbr")
FUENTE_EVIKE = "https://www.evike.com/products/20017/reviews (reseña de comprador, G&G 105 bolas; consulta 12-11-2026)"
FUENTE_NOVRITSCH = "https://us.novritsch.com/product/m4-mid-cap-magazine-gen2-225bbs/ (ficha de tienda; 12-11-2026)"

def _muestras_laterales(n: int = 24) -> tuple[float, ...]:
    """Coordenada lateral normalizada de -1 a 1: más densa en las esquinas, sin dejar la cara plana sin puntos."""
    return tuple(0.6 * (2 * j / (n - 1) - 1) + 0.4 * math.sin(math.pi / 2 * (2 * j / (n - 1) - 1)) for j in range(n))


WS = _muestras_laterales()
ALTO_PLACA = 12.0  # mm de la placa de base que se solapa con el cuerpo


# --- Espina curva y secciones -------------------------------------------------------------------------------------


def marco(s: float, radio: float, th0: float) -> tuple[float, float, float]:
    """Centro (x, y) y ángulo del marco local a la distancia `s` a lo largo de la espina (arco de radio `radio`)."""
    th = th0 + s / radio
    return radio * (math.cos(th0) - math.cos(th)), -radio * (math.sin(th) - math.sin(th0)), th


def en_marco(s: float, solido: Any, radio: float, th0: float) -> Any:
    """Coloca un sólido dibujado en el marco local (x delante, y arriba, z lateral) a la altura `s` de la espina."""
    cx, cy, th = marco(s, radio, th0)
    return Pos(cx, cy, 0.0) * Rot(0, 0, math.degrees(th)) * solido


def _pot(v: float, n: float) -> float:
    return math.copysign(abs(v) ** (2 / n), v)


def seccion(
    s: float,
    radio: float,
    th0: float,
    a_del: float,
    a_tras: float,
    b: float,
    *,
    n: float = 4.0,
    ox: float = 0.0,
    cresta_del: float = 0.0,
    cresta_tras: float = 0.0,
    ancho_cresta: float = 3.0,
) -> Wire:
    """Sección cerrada perpendicular a la espina: `a_del` hacia delante, `a_tras` hacia atrás y `±b` lateral.

    `cresta_*` suma (o resta, si es negativa) un nervio vertical en el centro de la cara delantera o trasera.
    """
    cx, cy, th = marco(s, radio, th0)
    fx, fy = math.cos(th), math.sin(th)
    pts: list[tuple[float, float, float]] = []
    # Se muestrea por la coordenada lateral (no por el ángulo): así un nervio estrecho de la cara delantera o trasera
    # siempre queda cubierto por varios puntos. Primero la cara delantera de -b a +b y luego la trasera de +b a -b.
    caras = ((a_del, cresta_del, 1.0, False), (a_tras, cresta_tras, -1.0, True))
    for a, cresta, signo, vuelta in caras:
        ws = [WS[j] for j in range(len(WS))]
        if vuelta:
            ws = list(reversed(ws))
        for idx, w in enumerate(ws):
            if idx in (0, len(ws) - 1) and vuelta:
                continue  # las esquinas de la cara trasera ya están en la delantera
            z = b * w
            x = a * (1.0 - min(abs(w), 1.0) ** n) ** (1.0 / n)
            if cresta:
                x += cresta * math.exp(-((z / ancho_cresta) ** 2))
            pts.append((cx + (signo * x + ox) * fx, cy + (signo * x + ox) * fy, z))
    return Wire([_Spline(*pts, periodic=True)])


def _bump(s: float, centros: Sequence[float], ancho: float) -> float:
    """Suma de relieves suaves (coseno elevado, aplanado en la cima) de `ancho` mm centrados en `centros`."""
    total = 0.0
    for c in centros:
        d = abs(s - c)
        if d < ancho / 2:
            total = max(total, min(1.0, 1.7 * (0.5 + 0.5 * math.cos(math.tau * d / ancho))))
    return total


@dataclass(frozen=True, slots=True)
class Perfil:
    """Cómo cambia la sección con la altura `u = s / altura` (0 boca, 1 base) y los relieves que lleva en el perfil."""

    nudos: tuple[float, ...]
    delante: tuple[float, ...]  # multiplicadores del semiancho delantero
    detras: tuple[float, ...]
    lado: tuple[float, ...]
    n: float = 4.0
    costillas: tuple[float, ...] = ()  # centros (u) de las nervaduras laterales
    costilla_h: float = 0.8  # mm que sobresale cada nervadura de la cara lateral
    costilla_w: float = 6.0  # mm de ancho de cada nervadura medidos a lo largo de la espina
    bandas: tuple[float, ...] = ()  # centros (u) de bandas rebajadas en la cara delantera
    banda_h: float = 1.0
    banda_w: float = 8.0
    cresta_del: tuple[float, float, float, float] | None = (
        None  # (alto mm, ancho mm, u inicial, u final); alto < 0: surco
    )
    cresta_tras: tuple[float, float, float, float] | None = None

    def en(self, u: float) -> tuple[float, float, float]:
        u = min(max(u, 0.0), 1.0)
        d, t, lat = (interpolar(self.nudos, v, u) for v in (self.delante, self.detras, self.lado))
        return d, t, lat


def _envolvente(u: float, u0: float, u1: float, borde: float = 0.04) -> float:
    if u <= u0 or u >= u1:
        return 0.0
    return min(1.0, (u - u0) / borde, (u1 - u) / borde)


def _posiciones(perfil: Perfil, altura: float, s_fin: float, base: int) -> list[float]:
    """Alturas de las secciones del loft: malla regular más los puntos clave de cada relieve."""
    pos = {round(s_fin * i / base, 3) for i in range(base + 1)}
    for lista, w in ((perfil.costillas, perfil.costilla_w), (perfil.bandas, perfil.banda_w)):
        for u in lista:
            for f in (-0.5, -0.25, 0.0, 0.25, 0.5):
                pos.add(round(u * altura + f * w, 3))
    for cr in (perfil.cresta_del, perfil.cresta_tras):
        if cr:
            for u in (cr[2], cr[2] + 0.04, cr[3] - 0.04, cr[3]):
                pos.add(round(u * altura, 3))
    orden = sorted(p for p in pos if 0.0 <= p <= s_fin)
    # Quita secciones casi superpuestas (el loft se vuelve inestable con separaciones de décimas de mm).
    util = [orden[0]]
    for p in orden[1:]:
        if p - util[-1] >= 0.9:
            util.append(p)
    if util[-1] != orden[-1]:
        util[-1] = orden[-1]
    return util


def cuerpo_espina(altura: float, radio: float, th0: float, perfil: Perfil, hx: float, hz: float, base: int = 24) -> Any:
    """Loft del cuerpo hasta `altura - ALTO_PLACA / 2` (la placa de base cierra el resto)."""
    s_fin = altura - ALTO_PLACA / 2
    secciones = []
    for s in _posiciones(perfil, altura, s_fin, base):
        u = s / altura
        d, t, lat = perfil.en(u)
        ad, at, b = hx * d, hx * t, hz * lat
        b += perfil.costilla_h * _bump(s, [c * altura for c in perfil.costillas], perfil.costilla_w)
        ad -= perfil.banda_h * _bump(s, [c * altura for c in perfil.bandas], perfil.banda_w)
        cd = ct = 0.0
        ancho = 3.0
        if perfil.cresta_del:
            cd = perfil.cresta_del[0] * _envolvente(u, perfil.cresta_del[2], perfil.cresta_del[3])
            ancho = perfil.cresta_del[1]
        if perfil.cresta_tras:
            ct = perfil.cresta_tras[0] * _envolvente(u, perfil.cresta_tras[2], perfil.cresta_tras[3])
            ancho = perfil.cresta_tras[1] if not perfil.cresta_del else ancho
        secciones.append(
            seccion(s, radio, th0, ad, at, b, n=perfil.n, cresta_del=cd, cresta_tras=ct, ancho_cresta=ancho)
        )
    return Solid.make_loft(secciones, ruled=True)


# --- Booleanas robustas -------------------------------------------------------------------------------------------

DESCARTADAS: list[str] = []  # diagnóstico: detalles cuya booleana dejó un sólido inválido (se omiten, no se inventan)


def _valido(s: Any) -> bool:
    try:
        return bool(s.is_valid) and s.volume > 0 and len(s.solids()) == 1
    except Exception:
        return False


def _booleana(base: Any, piezas: Sequence[Any], op: str, etiqueta: str) -> Any:
    """Aplica las piezas de una en una y se queda solo con las operaciones que dejan un único sólido válido."""
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


# --- Detalles sueltos ---------------------------------------------------------------------------------------------


def _bolsillo_boca(
    altura: float, radio: float, th0: float, perfil: Perfil, hx: float, hz: float, prof: float, pared: float
) -> Any:
    """Hueco de la boca: se ve el interior (seguidor, tubo), no la mecánica completa."""
    secs = []
    for s in (-2.0, prof * 0.5, prof):
        d, t, lat = perfil.en(max(s, 0.0) / altura)
        secs.append(seccion(s, radio, th0, hx * d - pared, hx * t - pared, hz * lat - pared * 0.9, n=perfil.n))
    return loftear(secs)


def _labios(radio: float, th0: float, hx: float, hz: float, *, subida: float = 3.6) -> list[Any]:
    """Labios de alimentación: dos orejas laterales que suben sobre la boca y un resalte trasero más bajo."""
    piezas = []
    for lado in (1, -1):
        oreja = filetear(Box(1.6 * hx, subida + 2.0, 2.0), 0.7)
        piezas.append(en_marco(0.0, Pos(-0.06 * hx, subida / 2 - 1.0, lado * (hz - 1.0)) * oreja, radio, th0))
    trasero = filetear(Box(2.6, subida * 0.7 + 2.0, 1.3 * hz), 0.6)
    piezas.append(en_marco(0.0, Pos(-hx + 1.8, subida * 0.35 - 1.0, 0.0) * trasero, radio, th0))
    return piezas


def _tubo_alimentacion(radio: float, th0: float, hx: float, prof: float) -> tuple[Any, Any]:
    """Tubo de alimentación en el fondo de la boca delante (sobresale 4,9 mm, cifra de una reseña) y su taladro."""
    largo = prof + 4.9
    tubo = filetear(cilindro_en("y", 4.6, largo, (0.42 * hx, (4.9 - prof) / 2, 0.0)), 0.5)
    taladro = cilindro_en("y", 3.2, largo - 2.0, (0.42 * hx, (4.9 - prof) / 2 + 1.1, 0.0))
    return en_marco(0.0, tubo, radio, th0), en_marco(0.0, taladro, radio, th0)


def _seguidor(radio: float, th0: float, hx: float, hz: float, prof: float) -> Any:
    """Seguidor: plataforma baja y redondeada detrás del tubo, apoyada en el fondo del bolsillo."""
    plato = filetear(Box(0.62 * hx, 3.2, 2 * hz - 4.0), 0.9)
    return en_marco(0.0, Pos(-0.36 * hx, -prof + 1.0, 0.0) * plato, radio, th0)


def _base_con_tope(
    altura: float,
    radio: float,
    th0: float,
    perfil: Perfil,
    hx: float,
    hz: float,
    *,
    crece: float = 1.08,
    tope_atras: float = 5.0,
    pestana_delante: float = 3.5,
) -> list[Any]:
    """Placa de base algo más ancha que el cuerpo, con un tope trasero (escalón) y una pestaña de tirar delante."""
    d, t, lat = perfil.en(1.0)
    k = crece
    s0 = altura - ALTO_PLACA
    placa = loftear(
        [
            seccion(s0, radio, th0, hx * d * 1.012, hx * t * 1.012, hz * lat * 1.012, n=perfil.n),
            seccion(s0 + 2.0, radio, th0, hx * d * k, hx * t * k, hz * lat * k, n=perfil.n - 0.4),
            seccion(altura - 2.5, radio, th0, hx * d * k, hx * t * k, hz * lat * k, n=perfil.n - 0.4),
            seccion(altura, radio, th0, hx * d * 0.96, hx * t * 0.96, hz * lat * 0.94, n=perfil.n - 0.8),
        ]
    )
    tope = filetear(Box(tope_atras + 2.0, 4.2, 0.64 * 2 * hz * lat), 1.0)
    tope = en_marco(altura - 6.0, Pos(-(hx * t * k) - tope_atras / 2 + 1.0, 0.0, 0.0) * tope, radio, th0)
    pestana = filetear(Box(pestana_delante + 1.5, 3.0, 0.5 * 2 * hz * lat), 0.8)
    pestana = en_marco(altura - 5.5, Pos(hx * d * k + pestana_delante / 2 - 0.6, 0.0, 0.0) * pestana, radio, th0)
    return [placa, tope, pestana]


def _ensamblar(cuerpo: Any, pieza_a_pieza: Sequence[Any], cortes: Sequence[Any], etiqueta: str) -> Any:
    cuerpo = _booleana(cuerpo, pieza_a_pieza, "fuse", etiqueta)
    return _booleana(cuerpo, cortes, "cut", etiqueta)


# --- Cargadores de AR/M4 ------------------------------------------------------------------------------------------

_I5 = (0, 0.07, 0.5, 0.93, 1.0)
PERFILES: dict[str, Perfil] = {
    # Stick de 30: paredes casi paralelas, boca estrechada por los labios, cinco nervaduras por cara.
    "lowcap": Perfil(
        _I5,
        (0.90, 1.0, 1.0, 1.0, 1.0),
        (0.90, 1.0, 1.0, 1.0, 1.0),
        (0.95, 1, 1, 1, 1),
        4.4,
        costillas=tuple(0.22 + 0.12 * i for i in range(5)),
        costilla_h=0.8,
        costilla_w=5.0,
    ),
    # Estilo PMAG: se ensancha hacia la base; nervio de agarre delantero, ventana de recuento y cuatro nervaduras.
    "pmag": Perfil(
        _I5,
        (0.92, 1.0, 1.03, 1.06, 1.06),
        (0.92, 1.0, 1.02, 1.04, 1.04),
        (0.95, 1, 1, 1, 1),
        4.0,
        costillas=tuple(0.52 + 0.09 * i for i in range(4)),
        costilla_h=0.7,
        costilla_w=5.0,
        cresta_del=(1.3, 2.6, 0.10, 0.92),
    ),
    # Mid-cap: el cuerpo abulta por delante en la mitad baja (alberga la cuerda y las bolas), con bandas y ventana.
    "midcap": Perfil(
        (0, 0.08, 0.32, 0.58, 0.85, 1.0),
        (0.90, 1.0, 1.16, 1.26, 1.20, 1.10),
        (0.90, 1.0, 1.0, 1.02, 1.02, 1.0),
        (0.95, 1.0, 1.0, 1.0, 1.0, 1.0),
        3.6,
        bandas=(0.30, 0.52, 0.74),
        banda_h=1.1,
        banda_w=9.0,
        cresta_del=(1.5, 3.2, 0.10, 0.90),
        cresta_tras=(-1.6, 2.6, 0.25, 0.80),  # surco trasero: ventana de comprobación de bolas
    ),
    # Hi-cap: tambor ancho que crece hacia abajo, esquinas muy redondeadas, bandas de agarre.
    "hicap": Perfil(
        (0, 0.07, 0.3, 0.6, 0.9, 1.0),
        (0.88, 1.0, 1.10, 1.22, 1.26, 1.22),
        (0.88, 1.0, 1.06, 1.14, 1.16, 1.12),
        (0.92, 1.0, 1.04, 1.08, 1.10, 1.06),
        3.3,
        bandas=(0.30, 0.45, 0.80),
        banda_h=1.2,
        banda_w=9.0,
    ),
    # GBBR: chapa de caras planas; la mitad baja es el depósito de gas (algo más gruesa); costura vertical trasera.
    "gbbr": Perfil(
        (0, 0.07, 0.45, 0.68, 0.9, 1.0),
        (0.88, 1.0, 1.0, 1.08, 1.14, 1.14),
        (0.88, 1.0, 1.0, 1.04, 1.06, 1.06),
        (0.92, 1.0, 1.0, 1.0, 1.0, 1.0),
        5.2,
        costillas=(0.30, 0.42),
        costilla_h=0.5,
        costilla_w=5.0,
        cresta_tras=(-1.0, 1.1, 0.12, 0.90),
    ),
}
RADIO_POR_ALTURA = {"lowcap": 4.0, "pmag": 2.6, "midcap": 2.0, "hicap": 5.0, "gbbr": 3.6}


class CargadorM4Real(CargadorM4):
    """Cargador de M4 con forma propia por tipo. Hereda de `CargadorM4` parámetros e interfaz del pozo."""

    id = "cargador.m4_real"
    nombre = "Cargador de M4 (lowcap, PMAG, mid-cap, hi-cap, GBBR)"
    motivo_sin_malla = None
    parametros = (
        *CargadorM4.parametros,
        Parametro("tipo", "Tipo de cargador", str, opciones=TIPOS, por_defecto="lowcap"),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (INT_POZO_GBBR,) if p["tipo"] == "gbbr" else (INT_POZO_STANAG,)

    def describir(self, p: Mapping[str, Valor]) -> str:
        nombre = {
            "lowcap": "baja capacidad",
            "pmag": "estilo PMAG",
            "midcap": "mid-cap",
            "hicap": "hi-cap con rueda",
            "gbbr": "de GBBR con depósito de gas",
        }[str(p["tipo"])]
        return f"Cargador de M4 ({p['sistema']}), {nombre}, de {p['capacidad']} bolas"

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (p["tipo"] == "gbbr") != (p["sistema"] == "gbb"):
            raise ParametroInvalidoError(
                "tipo gbbr y sistema gbb van juntos: los cargadores de AEG y GBBR no se cruzan"
            )

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        tipo = str(p["tipo"])
        H, hx, hz = float(p["altura"]), float(p["largo"]) / 2, float(p["ancho"]) / 2  # noqa: N806
        perfil = PERFILES[tipo]
        R = RADIO_POR_ALTURA[tipo] * H  # noqa: N806
        th0 = math.radians(2.0)
        cuerpo = cuerpo_espina(H, R, th0, perfil, hx, hz)
        notas = [
            "Silueta, labios, nervaduras y base estimados: el plano del STANAG 4179 no es público.",
            "El interior (muelle, cuerda, depósito) no se modela; el cuerpo es macizo salvo la boca.",
            "La capacidad en bolas no se convierte en medidas: largo, ancho y altura son parámetros de barrido.",
        ]
        cotas: list[Cota] = [estimada("cargador.curvatura_total", marco(H, R, th0)[0])]
        aeg = p["sistema"] == "aeg"

        # Boca: bolsillo con pared fina, tubo de alimentación y seguidor (AEG) o labios rodados de chapa (GBBR).
        prof = 12.0 if tipo != "gbbr" else 9.0
        pared = 1.5 if tipo != "gbbr" else 1.2
        cuerpo = cuerpo.cut(_bolsillo_boca(H, R, th0, perfil, hx, hz, prof, pared))
        piezas: list[Any] = [*_labios(R, th0, hx, hz, subida=3.6 if tipo != "gbbr" else 2.6)]
        cortes: list[Any] = []
        if aeg:
            tubo, taladro = _tubo_alimentacion(R, th0, hx, prof)
            piezas += [tubo, _seguidor(R, th0, hx, hz, prof)]
            cortes.append(taladro)
            cotas.append(Cota("cargador.tubo_alimentacion_diametro", 9.2, FUENTE_EVIKE, "2026-11-12", Confianza.BAJA))
        piezas += _base_con_tope(H, R, th0, perfil, hx, hz, crece=1.08 if tipo != "gbbr" else 1.05)

        if tipo == "lowcap":
            notas.append(
                "Lowcap: cinco nervaduras laterales por cara, labios, base con tope trasero y pestaña delantera."
            )
        elif tipo == "pmag":
            _, _, lat = perfil.en(0.29)
            cortes.append(en_marco(0.29 * H, Pos(0.0, 0.0, hz * lat) * Box(0.62 * hx, 0.24 * H, 1.4), R, th0))
            notas.append("Estilo PMAG: ventana de recuento, nervio de agarre delantero y cuatro nervaduras laterales.")
        elif tipo == "midcap":
            notas.append("Mid-cap: abultamiento delantero, nervio vertical, tres bandas rebajadas y surco trasero.")
            cotas.append(
                Cota("cargador.alto_referencia_midcap_225", 190.0, FUENTE_NOVRITSCH, "2026-11-12", Confianza.BAJA)
            )
        elif tipo == "hicap":
            _, _, lat = perfil.en(0.60)
            rueda = estriado("z", (0.0, 0.0, hz * lat + 1.6), 0.5 * hx + 4.0, 6.4, 20, 1.0)
            buje = cilindro_en("z", 5.0, 8.4, (0.0, 0.0, hz * lat + 2.6))
            piezas += [en_marco(0.60 * H, rueda, R, th0), en_marco(0.60 * H, buje, R, th0)]
            cortes.append(en_marco(0.60 * H, Pos(0.0, 0.0, hz * lat + 6.8) * Box(2.4, 8.0, 2.0), R, th0))
            notas.append("Hi-cap: cuerpo más ancho y bajo, rueda de cuerda estriada a la izquierda y bandas de agarre.")
        else:  # gbbr
            d16 = perfil.en(0.16)[0]
            cortes.append(en_marco(0.16 * H, Pos(hx * d16 + 0.4, 0.0, 0.0) * Box(3.4, 7.0, 0.52 * 2 * hz), R, th0))
            d1 = perfil.en(1.0)[0]
            piezas += [
                en_marco(H, filetear(cilindro_en("y", 3.4, 6.0, (hx * d1 * 0.35, -3.0, 0.0)), 0.4), R, th0),
                en_marco(H, filetear(cilindro_en("y", 4.6, 2.0, (hx * d1 * 0.35, -1.0, 0.0)), 0.3), R, th0),
            ]
            notas.append("GBBR: chapa de caras planas, labios rodados, depósito de gas más grueso, muesca y válvula.")
            notas.append(
                "La cifra publicada es solo la capacidad (35 bolas, tiendas): alto, ancho y grosor no tienen dato."
            )
        cuerpo = _ensamblar(cuerpo, piezas, cortes, tipo)
        sistema_pozo = INT_POZO_GBBR if tipo == "gbbr" else INT_POZO_STANAG
        sockets = (Socket("pozo", (0.0, 0.0, 0.0), sistema_pozo, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),)
        return Geometria(cuerpo, sockets, tuple(cotas), tuple(notas), nominales_de(cuerpo), vaciados=len(cortes) + 2)


# --- Cargadores de AK ---------------------------------------------------------------------------------------------

_AK5 = (0, 0.05, 0.5, 0.95, 1.0)
PERFIL_AK_ACERO = Perfil(
    _AK5,
    (0.92, 1.0, 1.0, 1.0, 1.0),
    (0.92, 1.0, 1.0, 1.0, 1.0),
    (0.88, 1, 1, 1, 1),
    5.0,
    costillas=(0.22, 0.40, 0.58, 0.76),
    costilla_h=1.0,
    costilla_w=0.09 * 250,
    cresta_tras=(1.4, 4.0, 0.12, 0.92),
)
PERFIL_AK_POLIMERO = Perfil(
    _AK5,
    (0.94, 1.0, 1.03, 1.05, 1.05),
    (0.94, 1.0, 1.03, 1.05, 1.05),
    (0.90, 1.0, 1.04, 1.06, 1.06),
    3.4,
    costillas=tuple(0.14 + 0.065 * i for i in range(12)),
    costilla_h=0.6,
    costilla_w=7.5,
    cresta_del=(1.0, 3.0, 0.10, 0.92),
    cresta_tras=(1.0, 3.0, 0.10, 0.92),
)


class CargadorAKReal(CargadorAK):
    """Cargador de AK: chapa de acero con nervaduras prensadas o polímero con nervios finos. Hereda parámetros."""

    id = "ak.cargador_real"
    nombre = "Cargador curvo AK (acero prensado o polímero)"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        H, prof, ancho, R = (float(p[k]) for k in ("altura", "profundidad", "ancho", "radio_curva"))  # noqa: N806
        acero = p["material"] == "acero"
        th0 = math.radians(3.0)
        hx, hz = prof / 2, ancho / 2
        perfil = PERFIL_AK_ACERO if acero else PERFIL_AK_POLIMERO
        ancho_costilla = 0.09 * H if acero else 7.5
        perfil = replace(perfil, costilla_w=ancho_costilla)
        cuerpo = cuerpo_espina(H, R, th0, perfil, hx, hz, base=24)
        cuerpo = cuerpo.cut(_bolsillo_boca(H, R, th0, perfil, hx, hz, 10.0, 1.4))
        piezas: list[Any] = [*_labios(R, th0, hx, hz, subida=3.0)]
        piezas += _base_con_tope(
            H, R, th0, perfil, hx, hz, crece=1.08 if acero else 1.10, tope_atras=3.5, pestana_delante=3.0
        )
        # Gancho delantero y tetón trasero de enganche (silueta exterior).
        gancho = filetear(Box(5.0, 12.0, 0.55 * 2 * hz), 1.2)
        piezas.append(en_marco(0.04 * H, Pos(hx + 1.6, 0.0, 0.0) * gancho, R, th0))
        teton = filetear(Box(5.0, 14.0, 0.50 * 2 * hz), 1.0)
        piezas.append(en_marco(0.12 * H, Pos(-hx - 1.4, 0.0, 0.0) * teton, R, th0))
        cuerpo = _ensamblar(cuerpo, piezas, [], "ak-acero" if acero else "ak-polimero")
        if acero:
            tipo_nota = "Acero: cuatro nervaduras prensadas largas por cara, lomo trasero, gancho delantero y tetón."
        else:
            tipo_nota = "Polímero: doce nervios finos por cara, nervios verticales delante y detrás y base redondeada."
        socket = Socket("mag_well", (0.0, 0.0, 0.0), INT_POZO_AK, (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {})
        notas = (
            tipo_nota,
            "Solo forma exterior: muelle y seguidor no se modelan; la curvatura y los relieves son estimados.",
        )
        cotas = (estimada("cargador.profundidad_boca", prof),)
        return Geometria(cuerpo, (socket,), cotas, notas, nominales_de(cuerpo), vaciados=3)


FAMILIAS_CARGADORES = {f.id: f for f in (CargadorM4Real(), CargadorAKReal())}

__all__ = ["DESCARTADAS", "FAMILIAS_CARGADORES", "CargadorAKReal", "CargadorM4Real"]
