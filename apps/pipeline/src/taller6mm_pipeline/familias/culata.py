"""Familias de culata AR-15/M4: tubo de culata (mil-spec o comercial) y culata telescópica.

Origen del tubo: centro de su cara delantera (la del receptor), sobre el eje; el tubo va hacia -X.
El diámetro del tubo es un estándar. La culata telescópica es **solo T0**: registra parámetros, interfaz y
cotas del SKU (plano T0 y ficha), pero no genera malla porque su forma no tiene cotas verificables.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Circle, Plane, Pos, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor

_ESPECIFICACION = Parametro(
    "especificacion", "Tipo de tubo", str, opciones=tuple(e.TUBO_DIAMETROS), por_defecto="milspec"
)


def _cilindro_atras(radio: float, largo: float) -> Any:
    """Cilindro sobre el eje X, desde x = 0 hasta x = -largo."""
    return Pos(-largo, 0, 0) * extrude(Plane.YZ * Circle(radio), largo)


class TuboCulata(Familia):
    id = "culata.tubo"
    version = 2  # v2: el socket lleva orientación
    nombre = "Tubo de culata"
    requiere = ("rosca.1_3/16-16",)
    estandares = e.TUBO
    parametros = (
        _ESPECIFICACION,
        Parametro("longitud", "Longitud total", float, "mm", minimo=100, maximo=300, de_sku=True),
        Parametro("longitud_rosca", "Longitud del tramo roscado", float, "mm", 5, 40, de_sku=True, critico=False),
    )

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (f"tubo_culata.{p['especificacion']}",)

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Tubo de culata {p['especificacion']} de {largo}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo = float(p["longitud"])
        diametro = e.TUBO_DIAMETROS[str(p["especificacion"])].valor_mm
        notas = [
            "Tubo macizo: el diámetro interior no está verificado.",
            "Sin quilla ni posiciones de la culata: sus cotas no están verificadas.",
        ]
        cuerpo = _cilindro_atras(diametro / 2, largo)
        if p["longitud_rosca"] is None:
            notas.append("Tramo roscado sin dato: no se modela.")
        else:
            cuerpo = cuerpo + _cilindro_atras(e.TUBO_ROSCA_DIAMETRO.valor_mm / 2, float(p["longitud_rosca"]))
            notas.append("La hélice de la rosca no se modela: cilindro del diámetro nominal.")
        socket = Socket(
            "stock",
            (-largo, 0.0, 0.0),
            f"tubo_culata.{p['especificacion']}",
            (-1.0, 0.0, 0.0),  # la culata entra por detrás
            (0.0, 1.0, 0.0),  # sin eje de deslizamiento transversal: +X local apunta arriba
            {"diametro_mm": diametro, "longitud_mm": largo, "referencia": "extremo trasero del tubo"},
        )
        return Geometria(cuerpo, (socket,), (), tuple(notas))


class CulataTelescopica(Familia):
    id = "culata.telescopica"
    nombre = "Culata telescópica"
    material = "mat.polimero_negro"
    motivo_sin_malla = (
        "Sin malla: el cuerpo de una culata (vaciados, almohadilla, quilla, palanca) no tiene cotas públicas "
        "verificables; solo lo está el diámetro del tubo. Hace falta un plano o un escaneo con licencia del SKU."
    )
    parametros = (
        _ESPECIFICACION,
        Parametro("longitud", "Longitud total", float, "mm", minimo=100, maximo=300, de_sku=True),
        Parametro("altura", "Altura de la cantonera", float, "mm", minimo=60, maximo=180, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", minimo=32, maximo=70, de_sku=True),
        Parametro("pared", "Pared alrededor del tubo", float, "mm", minimo=1.5, maximo=8, de_sku=True),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (f"tubo_culata.{p['especificacion']}",)

    def comprobar(self, p: dict[str, Valor]) -> None:
        if p["pared"] is None:
            return
        funda = e.TUBO_DIAMETROS[str(p["especificacion"])].valor_mm + 2 * float(p["pared"])
        if p["ancho"] is not None and float(p["ancho"]) < funda:
            raise ParametroInvalidoError(f"ancho: debe ser al menos {funda:.2f} mm (tubo + 2 paredes)")
        if p["altura"] is not None and float(p["altura"]) < funda:
            raise ParametroInvalidoError(f"altura: debe ser al menos {funda:.2f} mm (tubo + 2 paredes)")

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Culata telescópica para tubo {p['especificacion']}, {largo}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        raise NotImplementedError(self.motivo_sin_malla)
