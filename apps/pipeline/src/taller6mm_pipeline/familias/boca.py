"""Familias de boca de cañón: bocacha/apagallamas y silenciador, con rosca de 14 mm (CW o CCW).

Origen: centro de la cara trasera (la que apoya contra el cañón), sobre el eje. La pieza avanza hacia +X.
La rosca es un estándar (M14x1 a derechas o a izquierdas); longitud, diámetros y ranuras son cotas del SKU.
La hélice de la rosca no se modela: el alojamiento es un taladro liso del diámetro nominal.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Align, Box, Circle, Plane, Pos, Rot, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Valor

NOTA_ROSCA = "La hélice de la rosca no se modela: el alojamiento es un taladro liso de 14 mm nominales."
_ROSCA = Parametro("rosca", "Rosca de boca", str, opciones=tuple(e.ROSCAS_BOCA), por_defecto="14mm_ccw")
_COMUNES = (
    Parametro("longitud", "Longitud total", float, "mm", minimo=10, maximo=350, de_sku=True),
    Parametro("diametro", "Diámetro exterior", float, "mm", minimo=16, maximo=60, de_sku=True),
    Parametro("diametro_paso", "Diámetro del paso interior", float, "mm", 6, 40, de_sku=True, critico=False),
    Parametro(
        "profundidad_rosca", "Profundidad del alojamiento roscado", float, "mm", 3, 40, de_sku=True, critico=False
    ),
)


def _cilindro(radio: float, largo: float) -> Any:
    return extrude(Plane.YZ * Circle(radio), largo)


class _PiezaDeBoca(Familia):
    estandares = e.ROSCA_14

    def comprobar(self, p: dict[str, Valor]) -> None:
        diametro, paso, rosca, largo = p["diametro"], p["diametro_paso"], p["profundidad_rosca"], p["longitud"]
        if diametro is not None and paso is not None and float(paso) >= float(diametro):
            raise ParametroInvalidoError("diametro_paso: debe ser menor que el diámetro exterior")
        if largo is not None and rosca is not None and float(rosca) >= float(largo):
            raise ParametroInvalidoError("profundidad_rosca: debe ser menor que la longitud")

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.ROSCAS_BOCA[str(p["rosca"])],)

    def _cuerpo(self, p: Mapping[str, Valor]) -> tuple[Any, list[str]]:
        largo, radio = float(p["longitud"]), float(p["diametro"]) / 2
        cuerpo, notas = _cilindro(radio, largo), [NOTA_ROSCA]
        if p["diametro_paso"] is None:
            notas.append("Paso interior sin dato: se modela macizo.")
        else:
            cuerpo = cuerpo - _cilindro(float(p["diametro_paso"]) / 2, largo)
        if p["profundidad_rosca"] is None:
            notas.append("Profundidad de la rosca sin dato: el alojamiento no se modela.")
        else:
            cuerpo = cuerpo - _cilindro(e.ROSCA_14_DIAMETRO.valor_mm / 2, float(p["profundidad_rosca"]))
        return cuerpo, notas


class Silenciador(_PiezaDeBoca):
    id = "boca.silenciador"
    nombre = "Silenciador"
    parametros = (*_COMUNES, _ROSCA)

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        diam = "diámetro sin dato" if p["diametro"] is None else f"Ø{float(p['diametro']):g} mm"
        return f"Silenciador de {largo}, {diam}, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        cuerpo, notas = self._cuerpo(p)
        return Geometria(cuerpo, (), (), tuple(notas))


class Bocacha(_PiezaDeBoca):
    id = "boca.bocacha"
    nombre = "Bocacha"
    parametros = (
        *_COMUNES,
        _ROSCA,
        Parametro(
            "ranuras", "Ranuras longitudinales abiertas por delante", int, "ud", minimo=0, maximo=8, por_defecto=0
        ),
        Parametro("ancho_ranura", "Ancho de cada ranura", float, "mm", 1, 12, de_sku=True, critico=False),
        Parametro("longitud_ranura", "Longitud de cada ranura", float, "mm", 3, 80, de_sku=True, critico=False),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        super().comprobar(p)
        largo, ranura = p["longitud"], p["longitud_ranura"]
        if largo is not None and ranura is not None and float(ranura) >= float(largo):
            raise ParametroInvalidoError("longitud_ranura: debe ser menor que la longitud")

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Bocacha de {largo}, {p['ranuras']} ranuras, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        cuerpo, notas = self._cuerpo(p)
        n = int(p["ranuras"])
        if n and (p["ancho_ranura"] is None or p["longitud_ranura"] is None):
            notas.append("Ranuras sin cotas: no se modelan.")
        elif n:
            largo, radio = float(p["longitud"]), float(p["diametro"]) / 2
            lr, ar = float(p["longitud_ranura"]), float(p["ancho_ranura"])
            # Cada ranura corta la pared desde el eje hacia fuera y queda abierta por la cara delantera.
            corte = Pos(largo - lr, 0, 0) * Box(lr + 1, radio + 1, ar, align=(Align.MIN, Align.MIN, Align.CENTER))
            cuerpo = cuerpo - [Rot(i * 360.0 / n, 0, 0) * corte for i in range(n)]
        return Geometria(cuerpo, (), (), tuple(notas))
