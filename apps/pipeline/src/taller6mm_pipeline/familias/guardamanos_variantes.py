"""Familia: guardamanos del AR-15/M4 por tipo (carabina, mid, RIS cuadrado o M-LOK).

Origen: centro de la cara trasera, sobre el eje del cañón; avanza hacia +X. Reutiliza el raíl Picatinny
(`rail_picatinny`) y, para el tipo M-LOK, el generador `GuardamanosMlok` tal cual (sin modificarlo). Longitud,
diámetro (o lado, en el RIS cuadrado) y pared son cotas del SKU: sin ellas, la pieza sale T0 sin malla.
Los rangos de longitud por tipo solo validan la entrada; no son cotas de ningún producto.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from build123d import Align, Axis, Circle, Cylinder, Plane, Pos, Rectangle, RectangleRounded, Rot, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import filetear, rosca_helicoidal
from taller6mm_pipeline.familias.guardamanos_mlok import MARGEN_EXTREMO_MM, GuardamanosMlok, ranuras_rail_que_caben
from taller6mm_pipeline.familias.rail_picatinny import NOTA_PERFIL, longitud_rail_mm, solido_rail

TIPOS = ("carabina", "mid", "ris", "mlok")
INTERFAZ_UNION = "tuerca-guardamanos-ar"  # propuesta en catalogo/ar-m4.json (interfaces_nuevas)
_LONGITUD_TIPO = {"carabina": (100.0, 230.0), "mid": (180.0, 330.0), "ris": (80.0, 400.0), "mlok": (100.0, 450.0)}
_CARAS_RIS = {
    "top": (0.0, (0.0, 1.0, 0.0)),
    "l": (90.0, (0.0, 0.0, 1.0)),
    "bottom": (180.0, (0.0, -1.0, 0.0)),
    "r": (270.0, (0.0, 0.0, -1.0)),
}


PASO_ROSCA_TUERCA_MM = 1.5  # estimado: el paso de la tuerca de cañón depende del SKU (confianza baja)
LARGO_ROSCA_TUERCA_MM = 20.0
INICIO_ROSCA_TUERCA_MM = 8.0


def _con_rosca_interna(solido: Any, radio_taladro: float) -> Any:
    """Rosca interior del extremo trasero (donde el guardamanos se atornilla a la tuerca de cañón).

    Un manguito de 1 mm de espesor sobre la pared del taladro con un surco helicoidal en V de paso estimado. Se
    construye aparte (un corte helicoidal directo sobre el guardamanos completo no se puede teselar en OCCT) y se
    une después a la pared.
    """
    base = (Align.CENTER, Align.CENTER, Align.MIN)
    manguito = Cylinder(radio_taladro + 0.5, LARGO_ROSCA_TUERCA_MM, align=base) - Cylinder(
        radio_taladro - 1.0, LARGO_ROSCA_TUERCA_MM, align=base
    )
    surco = Pos(0, 0, 1.0) * rosca_helicoidal(
        radio_taladro - 0.05, 1.0, PASO_ROSCA_TUERCA_MM, LARGO_ROSCA_TUERCA_MM - 2.0
    )
    # Empieza a 8 mm del extremo trasero: los primeros 7 mm los ocupa la nariz de la tuerca del receptor.
    rosca = Pos(INICIO_ROSCA_TUERCA_MM, 0, 0) * Rot(0, 90, 0) * (manguito - surco)
    unido = solido + rosca
    return unido if unido.is_valid and unido.volume > solido.volume else solido


def _mlok_que_caben(longitud_mm: float) -> int:
    n = int((longitud_mm - 2 * MARGEN_EXTREMO_MM + e.MLOK_SEPARACION.valor_mm) // e.MLOK_PASO_MM)
    return max(1, min(10, n))


class GuardamanosVariantes(Familia):
    id = "guardamanos.variantes"
    version = 2
    nombre = "Guardamanos AR por tipo"
    requiere = (INTERFAZ_UNION,)
    ofrece = (e.INTERFAZ_PICATINNY, e.INTERFAZ_MLOK)
    estandares = (*e.PICATINNY, *e.MLOK)
    parametros = (
        Parametro("tipo", "Tipo de guardamanos", str, opciones=TIPOS, por_defecto="carabina"),
        Parametro("longitud", "Longitud total", float, "mm", minimo=80, maximo=450, de_sku=True),
        Parametro(
            "diametro_exterior", "Diámetro exterior (lado, en el RIS cuadrado)", float, "mm", 30, 60, de_sku=True
        ),
        Parametro("grosor_pared", "Grosor de la pared", float, "mm", minimo=1.5, maximo=5, de_sku=True),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if p["longitud"] is None:
            return
        minimo, maximo = _LONGITUD_TIPO[str(p["tipo"])]
        if not minimo <= float(p["longitud"]) <= maximo:
            raise ParametroInvalidoError(
                f"longitud: {p['longitud']} mm fuera del rango {minimo:g} a {maximo:g} mm de «{p['tipo']}»"
            )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return self.requiere

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        if p["tipo"] in ("carabina", "mid"):
            return ()
        return (e.INTERFAZ_PICATINNY, e.INTERFAZ_MLOK) if p["tipo"] == "mlok" else (e.INTERFAZ_PICATINNY,)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Guardamanos AR tipo {p['tipo']} de {mm(p, 'longitud')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        tipo, largo = str(p["tipo"]), float(p["longitud"])
        d, pared = float(p["diametro_exterior"]), float(p["grosor_pared"])
        if tipo == "mlok":
            base = {
                "longitud": largo,
                "diametro_exterior": d,
                "grosor_pared": pared,
                "ranuras_mlok": _mlok_que_caben(largo),
                "rail_superior": True,
                "seccion": "redonda",
            }
            g = GuardamanosMlok()
            geo = g.construir(g.validar(base))
            geo = replace(geo, solido=_con_rosca_interna(geo.solido, d / 2 - pared))
        elif tipo == "ris":
            geo = self._ris(largo, d, pared)
            geo = replace(geo, solido=_con_rosca_interna(geo.solido, d / 2 - pared))
        else:
            geo = self._dos_mitades(tipo, largo, d, pared)

        union = Socket("union-receptor", (0.0, 0.0, 0.0), INTERFAZ_UNION, (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        return replace(geo, sockets=(union, *geo.sockets))

    @staticmethod
    def _dos_mitades(tipo: str, largo: float, d: float, pared: float) -> Geometria:
        radio = d / 2
        cuerpo = extrude(Plane.YZ * (Circle(radio) - Circle(radio - pared)), largo)
        anillo = 4.0  # aro del delta ring y tapa delantera, estimados
        # Aros con los cantos redondeados (filete de 0,8 mm) en vez de cilindros vivos.
        aro = filetear(extrude(Plane.YZ * (Circle(radio + 3.0) - Circle(radio - pared)), anillo), 0.8)
        cuerpo += aro
        if tipo == "mid":
            cuerpo += Pos(largo - anillo, 0, 0) * filetear(
                extrude(Plane.YZ * (Circle(radio + 1.5) - Circle(radio - pared)), anillo), 0.8
            )
        # Estrías de agarre: 12 canales longitudinales redondeados (Ø 3 mm) en la cara exterior, entre los aros,
        # sin tocar las juntas laterales.
        x0, x1 = anillo + 6.0, largo - anillo - 6.0
        canal = Pos((x0 + x1) / 2, 0, 0) * Cylinder(1.5, x1 - x0).rotate(Axis.Y, 90)
        for k in range(12):
            ang = 15.0 + k * 30.0  # 15°, 45°… : ningún canal cae sobre las juntas (90° y 270°)
            cuerpo -= Rot(ang, 0, 0) * Pos(0, radio + 0.4, 0) * canal
        # Ranuras de ventilación pasantes (óvalos de 14 x 4 mm) en cuatro columnas a 45°, repartidas a lo largo.
        n_vent = max(1, int((largo - 2 * anillo - 16.0) // 22.0))
        ranura = extrude(RectangleRounded(14.0, 4.0, 1.9), radio + 1.0)
        x_ini = (largo - (n_vent - 1) * 22.0) / 2
        for col in (45.0, 135.0, 225.0, 315.0):
            for j in range(n_vent):
                cuerpo -= Rot(col, 0, 0) * Pos(x_ini + j * 22.0, 0, 0) * ranura
        # Juntas de las dos mitades: dos ranuras finas laterales a todo lo largo.
        junta = extrude(Plane.YZ * Rectangle(0.8, 1.0), largo - 2 * anillo)
        cuerpo -= [Pos(anillo, 0, s * radio) * junta for s in (1, -1)]
        notas = (
            "El escudo térmico interior y la unión al receptor no se modelan; el aro es una simplificación.",
            "Las juntas laterales (0,8 x 1 mm) y los aros de 4 mm son estimaciones de silueta, sin cota de SKU.",
            "Estrías de agarre (12 canales de Ø 3 mm) y ranuras de ventilación (14 x 4 mm): detalle estimado.",
        )
        alto = 2 * (radio + 3.0)
        return Geometria(cuerpo, (), (), notas, (largo, alto, alto), vaciados=3 + 4 * n_vent)

    @staticmethod
    def _ris(largo: float, lado: float, pared: float) -> Geometria:
        medio = lado / 2
        cuerpo = extrude(Plane.YZ * (RectangleRounded(lado, lado, 3.5) - Circle(medio - pared)), largo)
        n_rail = ranuras_rail_que_caben(largo)
        y_base = medio - pared / 2
        y_alto = medio + e.PICATINNY_ALTURA.valor_mm
        rail = solido_rail(n_rail, y_alto - y_base, largo, radio_perfil=0.5)
        sockets = []
        for cara, (giro, normal) in _CARAS_RIS.items():
            cuerpo += Rot(giro, 0, 0) * Pos(0, y_base, 0) * rail
            nx, ny, nz = normal
            sockets.append(
                Socket(
                    f"rail.{cara}",
                    (0.0, round(ny * y_alto, 4), round(nz * y_alto, 4)),
                    e.INTERFAZ_PICATINNY,
                    (nx, ny, nz),
                    (1.0, 0.0, 0.0),
                    {"longitud_mm": longitud_rail_mm(n_rail), "paso_mm": e.PICATINNY_PASO.valor_mm, "ranuras": n_rail},
                )
            )
        notas = (
            NOTA_PERFIL,
            "El tubo cuadrado con taladro redondo y la unión al receptor (tuerca de cañón) son simplificaciones.",
        )
        total = 2 * y_alto
        return Geometria(cuerpo, tuple(sockets), (), notas, (largo, total, total), vaciados=1 + 4 * n_rail)
