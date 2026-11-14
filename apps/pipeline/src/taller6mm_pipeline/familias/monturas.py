"""Monturas de óptica sobre Picatinny para réplicas de airsoft: elevador de red dot y anillos de visor.

Origen: extremo trasero de la montura, centrada, con el plano superior del raíl en y = 0. La montura avanza
hacia +X; las mordazas bajan por los flancos del raíl (y < 0) y el taco de retroceso entra en una ranura.
El ancho y la altura del raíl salen de `estandares.py` (confianza baja en el ancho); lo demás son cotas del SKU o
proporciones estimadas. El bulón de apriete se representa por sus cabezas, sin rosca.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Axis, Box, Cylinder, Plane, Pos, RegularPolygon, extrude, fillet

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.detalle import estimada, nominales_de

HUELLAS = {"t1": "huella-t1-micro", "rmr": "huella-rmr", "holosun_k": "huella-holosun-k"}
ANILLOS = {"25.4": "anillo-optica-25-4mm", "30": "anillo-optica-30mm", "34": "anillo-optica-34mm"}
GRUESO_MORDAZA_MM = 3.5
PROF_MORDAZA_MM = 8.0
NOTA_CLAMP = (
    "Mordazas, taco de retroceso y bulón simplificados: se ven las cabezas, no la rosca ni el muelle del apriete. "
    "El ancho del raíl es de confianza baja."
)


def _base_sobre_rail(x0: float, x1: float) -> tuple[Any, float]:
    """Mordazas y taco de retroceso entre x0 y x1. Devuelve el sólido y el semiancho exterior."""
    semi = e.PICATINNY_ANCHO.valor_mm / 2
    largo = x1 - x0
    mordazas = [
        Pos((x0 + x1) / 2, -PROF_MORDAZA_MM / 2, z * (semi + GRUESO_MORDAZA_MM / 2))
        * Box(largo, PROF_MORDAZA_MM, GRUESO_MORDAZA_MM)
        for z in (-1, 1)
    ]
    taco = Pos((x0 + x1) / 2, -e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm / 2, 0) * Box(
        e.PICATINNY_ANCHO_RANURA.valor_mm - 0.4,
        e.PICATINNY_PROFUNDIDAD_RANURA.valor_mm,
        e.PICATINNY_ANCHO_PLANO.valor_mm,
    )
    conjunto = mordazas[0] + mordazas[1] + taco
    # Cabeza del bulón (derecha) y tuerca hexagonal (izquierda).
    xb, yb = x0 + 0.7 * largo, -4.0
    zc = semi + GRUESO_MORDAZA_MM
    cabeza = Pos(xb, yb, -zc - 1.6) * Cylinder(4.4, 3.2) - Pos(xb, yb, -zc - 2.8) * Box(5.0, 1.0, 1.6)
    tuerca = Pos(xb, yb, zc + 1.6) * extrude(Plane.XY * RegularPolygon(4.6, 6), 1.6, both=True)
    return conjunto + cabeza + tuerca, semi + GRUESO_MORDAZA_MM


class MonturaRiser(Familia):
    id = "montura.riser"
    nombre = "Montura elevadora de red dot"
    requiere = (e.INTERFAZ_PICATINNY,)
    parametros = (
        Parametro("huella", "Huella de la óptica que recibe", str, opciones=tuple(HUELLAS), por_defecto="t1"),
        Parametro("longitud", "Longitud sobre el raíl", float, "mm", minimo=25, maximo=90, de_sku=True),
        Parametro("altura", "Altura sobre el plano del raíl", float, "mm", minimo=10, maximo=45, de_sku=True),
        Parametro("ancho", "Ancho de la plataforma", float, "mm", minimo=29, maximo=46, de_sku=True),
        Parametro(
            "separacion_tornillos",
            "Separación de los tornillos de la huella",
            float,
            "mm",
            minimo=8,
            maximo=40,
            de_sku=True,
            critico=False,
        ),
        Parametro("qd", "Palanca de desmontaje rápido", bool, por_defecto=False),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["longitud"] is not None
            and p["separacion_tornillos"] is not None
            and float(p["separacion_tornillos"]) > float(p["longitud"]) - 8
        ):
            raise ParametroInvalidoError("separacion_tornillos: no cabe en la longitud")

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (HUELLAS[str(p["huella"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Montura elevadora de {p['altura'] or 'sin dato'} mm para huella {p['huella']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, alto, w = float(p["longitud"]), float(p["altura"]), float(p["ancho"])
        base, _semi = _base_sobre_rail(0.0, largo)
        cuerpo = fillet((Pos(largo / 2, alto / 2, 0) * Box(largo, alto, w)).edges().filter_by(Axis.Z), radius=3.0)
        # Aligeramientos laterales (ranuras ovaladas) y plataforma de apoyo de la óptica.
        for z in (-1, 1):
            cuerpo = cuerpo - Pos(largo / 2, alto * 0.45, z * (w / 2)) * Box(largo * 0.5, alto * 0.4, 4.0)
        cuerpo = cuerpo - Pos(largo / 2, alto, 0) * Box(largo * 0.7, 1.6, w * 0.55)
        notas = [NOTA_CLAMP, "Huella genérica: la forma real de la óptica no se modela, solo el apoyo y los tornillos."]
        vaciados = 3
        if p["separacion_tornillos"] is None:
            notas.append("Separación de tornillos sin dato: no se modelan los taladros de la huella.")
        else:
            for dx in (-0.5, 0.5):
                cuerpo = cuerpo - Pos(largo / 2 + dx * float(p["separacion_tornillos"]), alto - 2.0, 0) * Cylinder(
                    1.5, 5.0
                ).rotate(Axis.X, 90)
            vaciados += 2
        if p["qd"]:
            cuerpo = (
                cuerpo
                + Pos(largo * 0.3, alto * 0.45, w / 2 + 3.0) * Cylinder(3.0, 6.0)
                + Pos(largo * 0.3 + 6.0, alto * 0.45, w / 2 + 5.0) * Box(14.0, 4.0, 3.0)
            )
            notas.append("Palanca QD reducida a una leva fija.")
        cuerpo = cuerpo + base
        sockets = (
            Socket("rail", (largo / 2, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket("optic", (largo / 2, alto, 0.0), HUELLAS[str(p["huella"])], (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), {}),
        )
        return Geometria(
            cuerpo,
            sockets,
            (estimada("montura.mordaza_profundidad", PROF_MORDAZA_MM),),
            tuple(notas),
            nominales_de(cuerpo),
            vaciados,
        )


class MonturaAnillos(Familia):
    id = "montura.anillos"
    nombre = "Anillos de visor"
    requiere = (e.INTERFAZ_PICATINNY,)
    parametros = (
        Parametro(
            "diametro_tubo", "Diámetro del tubo de la óptica (mm)", str, opciones=tuple(ANILLOS), por_defecto="30"
        ),
        Parametro("anillos", "Número de anillos", int, "ud", minimo=1, maximo=2, por_defecto=2),
        Parametro("altura_eje", "Altura del eje óptico sobre el raíl", float, "mm", minimo=20, maximo=45, de_sku=True),
        Parametro(
            "ancho_anillo", "Ancho de cada anillo (a lo largo del eje)", float, "mm", minimo=10, maximo=28, de_sku=True
        ),
        Parametro(
            "separacion",
            "Distancia entre centros de anillos",
            float,
            "mm",
            minimo=45,
            maximo=120,
            de_sku=True,
            critico=False,
        ),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        r_ext = float(p["diametro_tubo"]) / 2 + 5.0
        if p["altura_eje"] is not None and float(p["altura_eje"]) < r_ext + 1.0:
            raise ParametroInvalidoError("altura_eje: el anillo se hundiría en el raíl")
        if (
            p["separacion"] is not None
            and p["ancho_anillo"] is not None
            and int(p["anillos"]) == 2
            and float(p["separacion"]) < float(p["ancho_anillo"]) + 4.0
        ):
            raise ParametroInvalidoError("separacion: los anillos se tocarían")

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (ANILLOS[str(p["diametro_tubo"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Anillos de visor para tubo de {p['diametro_tubo']} mm ({p['anillos']})"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        r = float(p["diametro_tubo"]) / 2
        r_ext = r + 5.0
        eje, ancho = float(p["altura_eje"]), float(p["ancho_anillo"])
        sep = 70.0 if p["separacion"] is None else float(p["separacion"])
        dos = int(p["anillos"]) == 2
        xs = [ancho / 2, ancho / 2 + sep] if dos else [ancho / 2]
        semi = e.PICATINNY_ANCHO.valor_mm / 2 + GRUESO_MORDAZA_MM
        cuerpo: Any = None
        vaciados = 0
        notas = [NOTA_CLAMP, "Tornillos de la tapa reducidos a sus cabezas con hueco hexagonal."]
        for x in xs:
            pie = Pos(x, (eje - 6) / 2, 0) * Box(ancho, eje - 6, 2 * semi)
            aro = Pos(x, eje, 0) * Cylinder(r_ext, ancho).rotate(Axis.Y, 90)
            pieza = fillet(pie.edges().filter_by(Axis.X), radius=2.0) + aro
            pieza = pieza - Pos(x, eje, 0) * Cylinder(r, ancho + 2).rotate(Axis.Y, 90)
            # Junta de la tapa: rendija a la altura del eje en ambos lados.
            pieza = pieza - [Pos(x, eje, s * (r + 2.5)) * Box(ancho + 2, 0.5, 5.0) for s in (-1, 1)]
            for s in (-1, 1):
                for dx in (-0.25, 0.25):
                    cab = Pos(x + dx * ancho, eje + 2.6, s * (r + 2.8)) * Cylinder(2.2, 1.6).rotate(Axis.X, 90)
                    pieza = (
                        pieza
                        + cab
                        - Pos(x + dx * ancho, eje + 3.2, s * (r + 2.8))
                        * extrude(Plane.XZ * RegularPolygon(1.0, 6), 1.0, both=True)
                    )
            base, _ = _base_sobre_rail(x - ancho / 2, x + ancho / 2)
            pieza = pieza + base
            cuerpo = pieza if cuerpo is None else cuerpo + pieza
            vaciados += 4
        if dos:
            # Barra de unión baja entre los dos anillos (da cuerpo de una sola pieza sobre el raíl).
            cuerpo = cuerpo + Pos(xs[0] + sep / 2, 3.0, 0) * Box(sep - ancho + 2, 6.0, 2 * semi - 4.0)
        sockets = (
            Socket("rail", (xs[0], 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), {}),
            Socket(
                "tube",
                (sum(xs) / len(xs), eje + r_ext, 0.0),
                ANILLOS[str(p["diametro_tubo"])],
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
                {"diametro_tubo_mm": float(p["diametro_tubo"])},
            ),
        )
        cotas = (estimada("anillos.pared_del_aro", 5.0),)
        return Geometria(cuerpo, sockets, cotas, tuple(notas), nominales_de(cuerpo), vaciados + 1)
