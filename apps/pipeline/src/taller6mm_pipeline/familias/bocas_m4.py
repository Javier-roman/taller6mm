"""Bocachas y accesorios de rosca de boca del M4 (tanda 3): jaula A1, compensadores, cuña, adaptador, tapón.

Origen: centro de la cara trasera (la que apoya contra el cañón), sobre el eje; la pieza avanza hacia +X. El socket
`socket.muzzle` está en esa cara, con la normal hacia atrás. Registro propio `FAMILIAS_BOCAS`.

Cada pieza lleva su perfil real de revolución (hombros, biseles, gargantas) y sus cortes (ranuras con el fondo
redondo, ventanas de cámara, ranuras inclinadas). La hélice de la rosca no se modela: el alojamiento es un taladro liso
de 14 mm nominales y la «rosca falsa» son anillos en V (un perfil de dientes, no una hélice). Medidas de barrido
(`es_demo`, confianza baja): ninguna es la cota de un SKU. Solo airsoft: rosca de 14 mm, CW o CCW.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Box, Plane, Pos, RegularPolygon, Rot, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.detalle import nominales_de
from taller6mm_pipeline.familias.formas import cilindro_en
from taller6mm_pipeline.familias.formas_tanda3 import ranura_radial, revolucion_x, ventana_radial

NOTA_ROSCA = "La hélice de la rosca no se modela: el alojamiento es un taladro liso de 14 mm nominales."
R_ROSCA = e.ROSCA_14_DIAMETRO.valor_mm / 2
_ROSCA = Parametro("rosca", "Rosca de boca", str, opciones=tuple(e.ROSCAS_BOCA), por_defecto="14mm_ccw")
_LONGITUD = Parametro("longitud", "Longitud total", float, "mm", minimo=10, maximo=200, de_sku=True)
_DIAMETRO = Parametro("diametro", "Diámetro exterior", float, "mm", minimo=16, maximo=50, de_sku=True)
_PASO = Parametro("diametro_paso", "Diámetro del paso interior", float, "mm", 5, 30, de_sku=True, critico=False)
_PROF = Parametro(
    "profundidad_rosca", "Profundidad del alojamiento roscado", float, "mm", 3, 40, de_sku=True, critico=False
)


def _socket_muzzle(rosca: str) -> Socket:
    return Socket(
        "muzzle",
        (0.0, 0.0, 0.0),
        e.ROSCAS_BOCA[rosca],
        (-1.0, 0.0, 0.0),  # la rosca entra por detrás, hacia el cañón
        (0.0, 0.0, 1.0),
        {"referencia": "centro de la cara trasera", "diametro_rosca_mm": e.ROSCA_14_DIAMETRO.valor_mm},
    )


class _BocaBase(Familia):
    estandares = e.ROSCA_14
    material = "mat.anodizado_negro"

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.ROSCAS_BOCA[str(p["rosca"])],)

    def comprobar(self, p: dict[str, Valor]) -> None:
        d, paso, rosca, largo = p.get("diametro"), p.get("diametro_paso"), p.get("profundidad_rosca"), p["longitud"]
        if d is not None and paso is not None and float(paso) >= float(d):
            raise ParametroInvalidoError("diametro_paso: debe ser menor que el diámetro exterior")
        if largo is not None and rosca is not None and float(rosca) >= float(largo):
            raise ParametroInvalidoError("profundidad_rosca: debe ser menor que la longitud")
        if d is not None and float(d) < e.ROSCA_14_DIAMETRO.valor_mm + 3:
            raise ParametroInvalidoError("diametro: debe superar la rosca de 14 mm en 3 mm como mínimo")

    def _alojamiento(self, cuerpo: Any, p: Mapping[str, Valor], notas: list[str]) -> Any:
        """Rosca de entrada (taladro liso de 14 mm) y paso interior, con su aviso si falta el dato."""
        largo = float(p["longitud"])
        if p["profundidad_rosca"] is None:
            notas.append("Profundidad de la rosca sin dato: el alojamiento no se modela.")
        else:
            prof = float(p["profundidad_rosca"])
            cuerpo = cuerpo - cilindro_en("x", R_ROSCA, prof + 1.0, ((prof - 1.0) / 2, 0, 0))
        if p["diametro_paso"] is None:
            notas.append("Paso interior sin dato: se modela macizo.")
        else:
            cuerpo = cuerpo - cilindro_en("x", float(p["diametro_paso"]) / 2, largo + 2.0, (largo / 2, 0, 0))
        return cuerpo

    def _final(self, cuerpo: Any, p: Mapping[str, Valor], notas: list[str], vaciados: int) -> Geometria:
        sockets = (_socket_muzzle(str(p["rosca"])),)
        return Geometria(cuerpo, sockets, (), tuple(notas), nominales_de(cuerpo), vaciados)


# --- Pájaro jaula A1 ---------------------------------------------------------------------------------------------
class JaulaA1(_BocaBase):
    id = "boca.jaula_a1"
    nombre = "Apagallamas de jaula A1 (birdcage)"
    parametros = (
        _LONGITUD,
        _DIAMETRO,
        _PASO,
        _PROF,
        _ROSCA,
        Parametro("ancho_ranura", "Ancho de cada ranura", float, "mm", 1.5, 8, de_sku=True, critico=False),
        Parametro("longitud_ranura", "Longitud de cada ranura", float, "mm", 8, 80, de_sku=True, critico=False),
    )
    RANURAS = 6

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Jaula A1 de {mm(p, 'longitud')}, {self.RANURAS} ranuras, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r = float(p["longitud"]), float(p["diametro"]) / 2
        # Perfil: reborde trasero biselado, garganta de rosca, cuerpo cilíndrico, anillo de collar y nariz roma.
        perfil = [
            (0.0, 0.0),
            (0.80 * r, 0.0),
            (r, 1.6),
            (r, 7.0),
            (0.90 * r, 8.2),  # garganta
            (0.90 * r, 12.0),
            (r, 13.2),
            (r, largo - 5.0),
            (0.92 * r, largo - 1.8),
            (0.78 * r, largo),
            (0.0, largo),
        ]
        cuerpo = revolucion_x(perfil)
        notas = [NOTA_ROSCA]
        cuerpo = self._alojamiento(cuerpo, p, notas)
        vaciados = 2
        if p["ancho_ranura"] is None or p["longitud_ranura"] is None:
            notas.append("Ranuras sin cotas: no se modelan.")
        else:
            lr, ar = float(p["longitud_ranura"]), float(p["ancho_ranura"])
            corte = ranura_radial(largo - lr, largo + 1.0, ar, r + 1.0)
            n = self.RANURAS
            cuerpo = cuerpo - [Rot(30.0 + i * 360.0 / n, 0, 0) * corte for i in range(n)]
            vaciados += n
        return self._final(cuerpo, p, notas, vaciados)


# --- Compensador de 2 y 3 cámaras -------------------------------------------------------------------------------------
class CompensadorCamaras(_BocaBase):
    id = "boca.compensador_camaras"
    nombre = "Compensador de cámaras"
    parametros = (
        _LONGITUD,
        _DIAMETRO,
        _PASO,
        _PROF,
        _ROSCA,
        Parametro("camaras", "Número de cámaras", int, "ud", 2, 3, por_defecto=2),
        Parametro("ancho_ventana", "Ancho de cada ventana (en Z)", float, "mm", 3, 16, de_sku=True, critico=False),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Compensador de {p['camaras']} cámaras de {mm(p, 'longitud')}, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r, camaras = float(p["longitud"]), float(p["diametro"]) / 2, int(p["camaras"])
        perfil = [
            (0.0, 0.0),
            (0.84 * r, 0.0),
            (r, 1.4),
            (r, 8.0),
            (0.94 * r, 9.4),  # hombro trasero
            (0.94 * r, largo - 5.0),
            (0.80 * r, largo - 0.8),
            (0.0, largo - 0.8),
        ]
        cuerpo = revolucion_x(perfil)
        notas = [NOTA_ROSCA]
        cuerpo = self._alojamiento(cuerpo, p, notas)
        vaciados = 2
        if p["ancho_ventana"] is None:
            notas.append("Ancho de ventana sin dato: las cámaras no se abren.")
        else:
            av = float(p["ancho_ventana"])
            x_ini, x_fin = 14.0, largo - 7.0
            paso = (x_fin - x_ini) / camaras
            tabique = 0.30 * paso
            angulos = (0.0, 68.0, -68.0)  # arriba y a los lados; la cara inferior queda cerrada
            for k in range(camaras):
                x0 = x_ini + k * paso
                for ang in angulos:
                    cuerpo = cuerpo - Rot(ang, 0, 0) * ventana_radial(x0, x0 + paso - tabique, av, r + 1.0)
                    vaciados += 1
            notas.append(
                "Cámaras abiertas arriba y a los lados; los tabiques se modelan como anillos macizos con paso."
            )
        return self._final(cuerpo, p, notas, vaciados)


# --- Cuña de freno -----------------------------------------------------------------------------------------------
class CunaFreno(_BocaBase):
    id = "boca.cuna_freno"
    nombre = "Freno de boca de cuña"
    parametros = (
        _LONGITUD,
        _DIAMETRO,
        _PASO,
        _PROF,
        _ROSCA,
        Parametro("ranuras_laterales", "Ranuras inclinadas de cada lado", int, "ud", 2, 4, por_defecto=3),
        Parametro("ancho_ranura", "Ancho de cada ranura", float, "mm", 1.5, 6, de_sku=True, critico=False),
        Parametro("angulo_cuna", "Ángulo de la cara delantera", float, "grados", 20, 60, por_defecto=38.0),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Freno de cuña de {mm(p, 'longitud')}, {p['ranuras_laterales']} ranuras por lado, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r, n = float(p["longitud"]), float(p["diametro"]) / 2, int(p["ranuras_laterales"])
        ang = float(p["angulo_cuna"])
        perfil = [
            (0.0, 0.0),
            (0.82 * r, 0.0),
            (r, 1.6),
            (r, 6.0),
            (0.93 * r, 7.2),
            (0.93 * r, 11.0),
            (r, 12.2),
            (r, largo - 1.5),
            (0.9 * r, largo),
            (0.0, largo),
        ]
        cuerpo = revolucion_x(perfil)
        notas = [NOTA_ROSCA]
        cuerpo = self._alojamiento(cuerpo, p, notas)
        vaciados = 2
        # Cuña: plano inclinado que rebaja la parte superior delantera (arriba más corto, abajo más largo).
        a = math.radians(ang)
        arranque = largo - 0.45 * r / math.tan(a) - 4.0
        semiespacio = Pos(arranque, r * 0.95, 0) * Rot(0, 0, -ang) * Pos(0, 25.0, 0) * Box(80.0, 50.0, 3 * r)
        cuerpo = cuerpo - semiespacio
        vaciados += 1
        if p["ancho_ranura"] is None:
            notas.append("Ancho de ranura sin dato: las ranuras inclinadas no se modelan.")
        else:
            ar = float(p["ancho_ranura"])
            zona0, zona1 = 15.0, largo - 9.0
            paso = (zona1 - zona0) / n
            for k in range(n):
                xc = zona0 + (k + 0.5) * paso
                # Ranura pasante (de lado a lado) inclinada hacia atrás; deja intactas las crestas superior e inferior.
                corte = Pos(xc, 0, 0) * Rot(0, 28.0, 0) * Box(ar, 1.05 * r, 3 * r)
                cuerpo = cuerpo - corte
                vaciados += 1
        return self._final(cuerpo, p, notas, vaciados)


# --- Adaptador de silenciador (rosca 14 mm, CW o CCW) ---------------------------------------------------------
def _hexagono_x(radio_circ: float, x0: float, x1: float) -> Any:
    """Prisma hexagonal con el eje en X (para llave), de `x0` a `x1`; `radio_circ`: circunferencia envolvente."""
    prisma = extrude(Plane.YZ * RegularPolygon(radio_circ, 6), x1 - x0)
    return Pos(x0, 0, 0) * prisma


class AdaptadorSilenciador(_BocaBase):
    id = "boca.adaptador_silenciador"
    nombre = "Adaptador de rosca para silenciador"
    parametros = (
        _LONGITUD,
        Parametro("diametro", "Diámetro exterior del collar", float, "mm", 17, 40, de_sku=True),
        _PASO,
        _PROF,
        _ROSCA,
        Parametro(
            "rosca_salida",
            "Rosca de salida (macho, para el silenciador)",
            str,
            opciones=tuple(e.ROSCAS_BOCA),
            por_defecto="14mm_cw",
        ),
        Parametro("largo_hexagono", "Longitud del tramo hexagonal", float, "mm", 4, 20, de_sku=True, critico=False),
    )

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.ROSCAS_BOCA[str(p["rosca_salida"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Adaptador de silenciador de {mm(p, 'longitud')}, entrada {p['rosca']} y salida {p['rosca_salida']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r = float(p["longitud"]), float(p["diametro"]) / 2
        macho = 12.0  # tramo macho de salida
        # Perfil: collar trasero biselado, cuerpo, hombro de apoyo y macho de 14 mm con garganta de descarga.
        x_hex1 = largo - macho - 2.0
        perfil = [
            (0.0, 0.0),
            (0.86 * r, 0.0),
            (r, 1.2),
            (r, 5.0),
            (0.88 * r, 6.0),
            (0.88 * r, x_hex1),
            (R_ROSCA + 1.2, x_hex1 + 1.0),
            (R_ROSCA + 1.2, largo - macho),
            (R_ROSCA - 0.7, largo - macho),  # garganta de descarga de la rosca
            (R_ROSCA - 0.7, largo - macho + 1.4),
            (R_ROSCA, largo - macho + 1.4),
            (R_ROSCA, largo - 0.6),
            (R_ROSCA - 0.7, largo),
            (0.0, largo),
        ]
        cuerpo = revolucion_x(perfil)
        notas = [NOTA_ROSCA, "El macho de salida es liso (sin hélice) y con la garganta de descarga a su base."]
        vaciados = 3
        if p["largo_hexagono"] is None:
            notas.append("Tramo hexagonal sin dato: no se modela.")
        else:
            lh = float(p["largo_hexagono"])
            hexa = _hexagono_x(0.97 * r / math.cos(math.radians(30)), 6.0, 6.0 + lh)
            cuerpo = cuerpo + (hexa & cilindro_en("x", 0.97 * r + 0.5, lh, (6.0 + lh / 2, 0, 0)))
        cuerpo = self._alojamiento(cuerpo, p, notas)
        salida = Socket(
            "salida",
            (largo, 0.0, 0.0),
            e.ROSCAS_BOCA[str(p["rosca_salida"])],
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            {
                "referencia": "centro de la cara delantera (rosca macho)",
                "diametro_rosca_mm": e.ROSCA_14_DIAMETRO.valor_mm,
            },
        )
        return Geometria(
            cuerpo, (_socket_muzzle(str(p["rosca"])), salida), (), tuple(notas), nominales_de(cuerpo), vaciados
        )


# --- Rosca falsa (anillos en V) ----------------------------------------------------------------------------------
class RoscaFalsa(_BocaBase):
    id = "boca.rosca_falsa"
    nombre = "Tramo de rosca falsa (anillos en V)"
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", minimo=10, maximo=60, de_sku=True),
        Parametro("diametro", "Diámetro del reborde", float, "mm", minimo=17, maximo=40, de_sku=True),
        Parametro("longitud_rosca", "Longitud del tramo con dientes", float, "mm", 5, 40, de_sku=True, critico=False),
        _PASO,
        _ROSCA,
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        super().comprobar(p)
        if p["longitud_rosca"] is not None and float(p["longitud_rosca"]) > float(p["longitud"]) - 3.0:
            raise ParametroInvalidoError("longitud_rosca: no cabe en la longitud total (3 mm de reborde)")

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Rosca falsa de {mm(p, 'longitud')} (paso {e.ROSCA_14_PASO.valor_mm:g} mm), rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r = float(p["longitud"]), float(p["diametro"]) / 2
        paso = e.ROSCA_14_PASO.valor_mm
        notas = [
            "Rosca falsa: anillos en V con el paso real de 1 mm, no una hélice; solo aspecto.",
            "No es una rosca funcional: no se modela el acoplamiento.",
        ]
        perfil: list[tuple[float, float]] = [(0.0, 0.0), (0.88 * r, 0.0), (r, 1.2), (r, 3.0), (R_ROSCA - 0.2, 3.4)]
        if p["longitud_rosca"] is None:
            notas.append("Longitud del tramo con dientes sin dato: se modela liso.")
            perfil += [(R_ROSCA - 0.2, largo)]
        else:
            lr = float(p["longitud_rosca"])
            x = 3.4
            n = max(int(lr / paso), 1)
            profundidad = 0.65 * paso
            for _ in range(n):
                perfil += [(R_ROSCA - 0.2 - profundidad, x + 0.5 * paso), (R_ROSCA - 0.2, x + paso)]
                x += paso
            perfil += [(R_ROSCA - 0.2, max(largo - 0.8, x)), (R_ROSCA - 0.9, largo)]
        perfil += [(0.0, largo)]
        cuerpo = revolucion_x(perfil)
        if p["diametro_paso"] is None:
            notas.append("Paso interior sin dato: se modela macizo.")
        else:
            cuerpo = cuerpo - cilindro_en("x", float(p["diametro_paso"]) / 2, largo + 2.0, (largo / 2, 0, 0))
        return self._final(cuerpo, p, notas, 1 if p["diametro_paso"] is not None else 0)


# --- Tapón de rosca ------------------------------------------------------------------------------------------------
class TaponRosca(_BocaBase):
    id = "boca.tapon_rosca"
    nombre = "Tapón protector de rosca de boca"
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", minimo=10, maximo=40, de_sku=True),
        Parametro("diametro", "Diámetro exterior", float, "mm", minimo=17, maximo=32, de_sku=True),
        _PROF,
        _ROSCA,
        Parametro("estrias", "Estrías del agarre", int, "ud", 0, 36, por_defecto=24),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        super().comprobar(p)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Tapón de rosca de {mm(p, 'longitud')}, {p['estrias']} estrías, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r = float(p["longitud"]), float(p["diametro"]) / 2
        perfil = [
            (0.0, 0.0),
            (r, 0.0),
            (r, largo - 4.0),
            (0.92 * r, largo - 1.6),
            (0.70 * r, largo),  # cúpula plana con el borde redondeado
            (0.0, largo),
        ]
        cuerpo = revolucion_x(perfil)
        notas = [NOTA_ROSCA, "Tapón ciego: sin la junta de goma ni la hélice interior."]
        if p["profundidad_rosca"] is None:
            notas.append("Profundidad de la rosca sin dato: el alojamiento no se modela.")
        else:
            prof = float(p["profundidad_rosca"])
            cuerpo = cuerpo - cilindro_en("x", R_ROSCA, prof + 1.0, ((prof - 1.0) / 2, 0, 0))
        n = int(p["estrias"])
        vaciados = 1 + n
        if n:
            surco = cilindro_en("x", 0.55, largo - 7.0, ((largo - 7.0) / 2 + 3.0, r, 0))
            cuerpo = cuerpo - [Rot(i * 360.0 / n, 0, 0) * surco for i in range(n)]
        return self._final(cuerpo, p, notas, vaciados)


FAMILIAS_BOCAS: dict[str, Familia] = {
    f.id: f for f in (JaulaA1(), CompensadorCamaras(), CunaFreno(), AdaptadorSilenciador(), RoscaFalsa(), TaponRosca())
}

__all__ = ["FAMILIAS_BOCAS"]
