"""Familia: cargador de M4 por capacidad.

Origen: centro de la cara superior (la que entra en el brocal); el cargador baja hacia -Y, con el largo en X
y el ancho en Z. No hay una fuente pública verificable de las cotas exteriores (el STANAG 4179 no publica el
plano y cada fabricante de airsoft varía): las tres son cotas del SKU y, sin ellas, la pieza sale T0. La
capacidad es un dato de la variante y **no** se convierte en medidas.
"""

from __future__ import annotations

from collections.abc import Mapping

from build123d import Align, Box

from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Valor


class CargadorM4(Familia):
    id = "cargador.m4"
    nombre = "Cargador de M4"
    material = "mat.polimero_negro"
    parametros = (
        Parametro("capacidad", "Capacidad en bolas", int, "ud", minimo=20, maximo=600),
        Parametro("sistema", "Sistema de la réplica", str, opciones=("aeg", "gbb"), por_defecto="aeg"),
        Parametro("largo", "Largo del cuerpo (de delante a atrás)", float, "mm", minimo=40, maximo=80, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo", float, "mm", minimo=15, maximo=35, de_sku=True),
        Parametro("altura", "Altura total", float, "mm", minimo=80, maximo=300, de_sku=True),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (f"cargador.m4.{p['sistema']}",)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cargador de M4 ({p['sistema']}) de {p['capacidad']} bolas"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, ancho, altura = float(p["largo"]), float(p["ancho"]), float(p["altura"])
        cuerpo = Box(largo, altura, ancho, align=(Align.CENTER, Align.MAX, Align.CENTER))
        notas = ("Prisma recto: curvatura, labios y retenida sin verificar, no se modelan.",)
        return Geometria(cuerpo, (), (), notas)
