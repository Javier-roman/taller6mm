"""Familia: cargador de M4 por capacidad. **Solo T0**: no hay cotas verificables para una geometría creíble.

No existe una fuente pública verificable de las cotas exteriores (el STANAG 4179 no publica el plano y cada
fabricante de airsoft varía), ni de la curvatura, los labios o la retenida. Una caja recta con tres medidas
no es un cargador: hasta tener un plano o un escaneo con licencia, la familia registra los parámetros y las
cotas del SKU (para el plano T0 y la ficha) y **no genera malla**. La capacidad nunca se convierte en medidas.
"""

from __future__ import annotations

from collections.abc import Mapping

from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Valor


class CargadorM4(Familia):
    id = "cargador.m4"
    nombre = "Cargador de M4"
    material = "mat.polimero_negro"
    motivo_sin_malla = (
        "Sin malla: curvatura, labios, retenida y sección del cargador no tienen fuente pública verificable "
        "(el STANAG 4179 no publica el plano). Hace falta un plano o un escaneo con licencia."
    )
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
        raise NotImplementedError(self.motivo_sin_malla)
