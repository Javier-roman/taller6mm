"""Miras (fija y regulable, trasera y delantera) y cañón exterior de pistola o revólver de airsoft.

Miras: origen en el centro de la cola de milano, a ras de la cara superior de la corredera; el cuerpo sube por +Y y la
cola baja por -Y. Cañón: coordenadas absolutas de pistola (ver `pistola_comun`), con el eje en Y = 0; el cañón de
pistola arranca en la cámara (`X_RECAMARA`) y el de revólver en la cara delantera del armazón (`X_FRENTE_REVOLVER`).
El tramo roscado de boca (14 mm CCW, estándar de `estandares.py`) se dibuja con anillos: la hélice no se modela.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Box, Plane, Polygon, Pos, Rot, extrude

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, revolucion
from taller6mm_pipeline.familias.pistola_comun import (
    INTERFAZ_CANON_PISTOLA,
    INTERFAZ_CANON_REVOLVER,
    INTERFAZ_MIRA_PISTOLA,
    estimada,
)

X_RECAMARA = 34.0  # cara de la recámara respecto a la cara trasera de la corredera
X_FRENTE_REVOLVER = 62.0  # cara delantera del armazón del revólver (ver `revolver.py`)
PROFUNDIDAD_COLA = 2.4


def _cola(largo: float, semi_arriba: float) -> Any:
    """Cola de milano: trapecio en (Z, Y) más ancho abajo, extruido a lo largo de X (centrado)."""
    pts = [
        (-semi_arriba, 0.2),
        (semi_arriba, 0.2),
        (semi_arriba + 1.1, -PROFUNDIDAD_COLA),
        (-semi_arriba - 1.1, -PROFUNDIDAD_COLA),
    ]
    cuerpo = extrude(Plane.YZ * Polygon(*[(y, z) for z, y in pts], align=None), amount=largo)
    return Pos(-largo / 2, 0, 0) * cuerpo


def _perfil_lateral(pts: list[tuple[float, float]], ancho: float) -> Any:
    return extrude(Plane.XY * Polygon(*pts, align=None), amount=ancho / 2, both=True)


class MiraPistola(Familia):
    id = "mira.pistola"
    version = 1
    nombre = "Mira de pistola"
    requiere = (INTERFAZ_MIRA_PISTOLA,)
    ofrece = ()
    material = "mat.acero_negro"
    parametros = (
        Parametro("lado", "Trasera o delantera", str, opciones=("trasera", "delantera"), por_defecto="trasera"),
        Parametro(
            "tipo",
            "Fija o regulable (tornillo de deriva o de altura)",
            str,
            opciones=("fija", "regulable"),
            por_defecto="fija",
        ),
        Parametro("alto", "Alto sobre la corredera", float, "mm", 3, 14, de_sku=True),
        Parametro("ancho", "Ancho del cuerpo de la mira", float, "mm", 2, 22, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Mira {p['lado']} {p['tipo']} de {mm(p, 'alto')} de alto"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        alto, ancho = float(p["alto"]), float(p["ancho"])
        lado, tipo = str(p["lado"]), str(p["tipo"])
        vaciados = 2
        notas = ["Solo forma exterior: los muelles y el tornillo no se modelan por dentro."]
        if lado == "trasera":
            largo = 7.0 if tipo == "fija" else 11.0
            ala = 0.0 if tipo == "fija" else 2.0
            # Perfil lateral: cara trasera vertical con serrado, frente en rampa hacia delante.
            pts = [
                (-largo / 2, 0.0),
                (-largo / 2, alto),
                (largo / 2 - 2.6, alto),
                (largo / 2, alto - 2.4),
                (largo / 2, 0.0),
            ]
            cuerpo = _perfil_lateral(pts, ancho)
            cuerpo = filetear(
                cuerpo, 0.5, [a for a in cuerpo.edges() if a.length > 3 and abs(a.center().Y - alto) < 0.1]
            )
            cuerpo = cuerpo + _cola(largo - 1.0, 5.6)
            # Ventana en U (nítida y con fondo redondeado).
            ventana = 3.4 if tipo == "fija" else 3.0
            prof = min(4.2, alto - 1.8)
            hueco = Pos(0, alto - prof / 2 + 0.2, 0) * Box(largo + 2, prof + 0.4, ventana)
            hueco = hueco + cilindro_en("x", ventana / 2, largo + 2, (0.0, alto - prof, 0.0))
            cuerpo = cuerpo - hueco
            for i in range(4):  # serrado antirreflejo de la cara trasera
                cuerpo = cuerpo - Pos(-largo / 2 + 0.2, 1.2 + i * 1.15, 0) * Box(0.5, 0.45, ancho - 1.6)
            vaciados += 5
            if tipo == "regulable":
                # Tornillo de deriva: cabeza moleteada a un lado y muelle al otro (cabeza con ranura).
                z = ancho / 2 + ala
                cuerpo = cuerpo + Pos(0, alto * 0.45, ancho / 2 + 0.5) * Rot(0, 0, 0) * cilindro_en(
                    "z", 2.4, 2.4, (0, 0, 0)
                )
                cuerpo = cuerpo - Pos(0, alto * 0.45, z + 0.2) * Box(0.7, 3.2, 0.8)
                cuerpo = cuerpo + Pos(0, alto * 0.45, -(ancho / 2 + 0.2)) * cilindro_en("z", 1.5, 1.4, (0, 0, 0))
                notas.append("Tornillo de deriva y su muelle: solo cabezas exteriores.")
                vaciados += 2
        else:
            largo = 7.0 if tipo == "fija" else 9.0
            base = 2.0 + (1.2 if tipo == "regulable" else 0.0)
            ancho_poste = max(2.4, min(ancho, 4.2))
            zocalo = Pos(0, base / 2, 0) * Box(largo, base, 9.0)
            zocalo = filetear(zocalo, 0.7, [a for a in zocalo.edges() if a.length == base])
            pts = [(-1.6, base - 0.2), (-1.6, alto), (0.4, alto), (2.8, base + 0.6), (2.8, base - 0.2)]
            poste = _perfil_lateral(pts, ancho_poste)
            poste = filetear(poste, 0.4, [a for a in poste.edges() if abs(a.center().Y - alto) < 0.1 and a.length > 2])
            cuerpo = zocalo + poste + _cola(largo - 1.0, 4.0)
            # Alojamiento del punto de contraste en la cara trasera del poste (sin pintura: solo el hueco).
            cuerpo = cuerpo - cilindro_en("x", 0.8, 0.8, (-1.6 + 0.2, alto - 2.0, 0.0))
            vaciados += 1
            if tipo == "regulable":
                cuerpo = cuerpo + Pos(1.4, base + 0.35, 0) * cilindro_en("y", 1.6, 0.8, (0, 0, 0))
                cuerpo = cuerpo - Pos(1.4, base + 0.7, 0) * Box(2.6, 0.5, 0.6)
                notas.append("Tornillo de altura de la mira delantera: solo la cabeza exterior.")
                vaciados += 1
        sockets = (
            Socket(
                "corredera",
                (0.0, -PROFUNDIDAD_COLA, 0.0),
                INTERFAZ_MIRA_PISTOLA,
                (0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0),
                {"lado": lado},
            ),
        )
        cotas = (estimada("mira.largo_base", largo), estimada("mira.profundidad_cola_milano", PROFUNDIDAD_COLA))
        notas.append("Proporciones y cola de milano estimadas, sin cota de ningún SKU ni norma.")
        caja = cuerpo.bounding_box()
        return Geometria(
            cuerpo, sockets, cotas, tuple(notas), (caja.size.X, caja.size.Y, caja.size.Z), vaciados=vaciados
        )


class CanonPistola(Familia):
    id = "canon.pistola"
    version = 1
    nombre = "Cañón exterior de pistola o revólver"
    requiere = ()
    ofrece = (e.ROSCAS_BOCA["14mm_ccw"],)
    material = "mat.acero_negro"
    estandares = e.ROSCA_14
    parametros = (
        Parametro(
            "tipo",
            "De pistola (con capó de recámara) o de revólver",
            str,
            opciones=("semi", "revolver"),
            por_defecto="semi",
        ),
        Parametro("rosca", "Rosca de boca", str, opciones=tuple(e.ROSCAS_BOCA), por_defecto="14mm_ccw"),
        Parametro("longitud", "Longitud total", float, "mm", 60, 260, de_sku=True),
        Parametro("diametro", "Diámetro del cuerpo", float, "mm", 9, 20, de_sku=True),
        Parametro("longitud_rosca", "Longitud del tramo roscado", float, "mm", 8, 24, de_sku=True, critico=False),
    )

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.ROSCAS_BOCA[str(p["rosca"])],)

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (INTERFAZ_CANON_REVOLVER if p["tipo"] == "revolver" else INTERFAZ_CANON_PISTOLA,)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Cañón de {p['tipo']} de {mm(p, 'longitud')} con rosca {p['rosca'].replace('_', ' ')}"

    def comprobar(self, p: dict[str, Valor]) -> None:
        d = p["diametro"]
        if d is not None and float(d) <= e.ROSCA_14_DIAMETRO.valor_mm - 4.0:
            from taller6mm_pipeline.familias.base import ParametroInvalidoError

            raise ParametroInvalidoError("diametro: el cuerpo debe quedar cerca de la rosca de 14 mm")

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, d = float(p["longitud"]), float(p["diametro"])
        lr = 12.0 if p["longitud_rosca"] is None else float(p["longitud_rosca"])
        r, rr = d / 2, e.ROSCA_14_DIAMETRO.valor_mm / 2
        revolver = p["tipo"] == "revolver"
        x0 = X_FRENTE_REVOLVER if revolver else X_RECAMARA
        paso = e.ROSCA_14_PASO.valor_mm
        # Perfil (radio, distancia desde x0). Cuerpo, hombro de la rosca y anillos con paso de 1 mm.
        hombro = largo - lr
        perfil: list[tuple[float, float]] = [(0.0, 0.0), (r + 0.6, 0.0), (r + 0.6, 6.0), (r, 7.0)]
        if revolver:
            perfil = [(0.0, 0.0), (r - 0.8, 0.0), (r - 0.8, 6.0), (r, 7.0)]
        perfil += [(r, hombro - 1.2), (rr + 0.2, hombro - 0.2), (rr + 0.2, hombro)]
        for i in range(int(lr // paso) - 1):  # anillos: V de 0,5 mm de fondo
            y = hombro + i * paso
            perfil += [(rr - 0.5, y + paso * 0.5), (rr, y + paso)]
        perfil += [(rr - 0.2, largo - 0.4), (rr - 0.8, largo), (0.0, largo)]
        cuerpo = revolucion([(max(a, 0.0), b) for a, b in perfil])
        cuerpo = Rot(0, 0, -90) * cuerpo  # eje Y -> eje X
        cuerpo = Pos(x0, 0, 0) * cuerpo
        vaciados = 2
        notas = [
            "Solo forma exterior: el cañón interior de precisión (hop-up, Ø6,03) no se modela.",
            "La rosca de boca son anillos de 1 mm de paso (la hélice no se modela).",
        ]
        if not revolver:
            # Capó de la recámara con la cara superior plana, la rampa de alimentación y el tetón de cierre.
            capo = Pos(x0 + 15.0, 0.4, 0) * Box(30.0, 2 * r + 0.8, 2 * r - 0.6)
            capo = filetear(capo, 2.2, [a for a in capo.edges() if a.length == 30.0])
            tapon = Pos(x0 + 23.0, r + 2.4, 0) * Box(12.0, 2.6, 8.0)
            tapon = filetear(tapon, 0.8, [a for a in tapon.edges() if a.length == 12.0])
            rampa = extrude(
                Plane.XY * Polygon((x0, -r), (x0 + 16.0, -r), (x0 + 3.0, -r - 5.4), (x0, -r - 5.4), align=None),
                amount=4.2,
                both=True,
            )
            cuerpo = cuerpo + capo + tapon + rampa
            cuerpo = cuerpo - Pos(x0 + 14.0, r + 1.4, 0) * Box(2.0, 2.4, 9.0)  # ranura del cierre
            vaciados += 1
            notas.append("Capó, tetón de cierre y rampa de alimentación simplificados.")
        else:
            # Rampa de la mira delantera del revólver y nervio superior.
            rampa = extrude(
                Plane.XY
                * Polygon(
                    (x0 + largo - 18.0, r - 0.4),
                    (x0 + largo - 4.0, r - 0.4),
                    (x0 + largo - 4.0, r + 4.4),
                    (x0 + largo - 12.0, r + 3.2),
                    align=None,
                ),
                amount=2.2,
                both=True,
            )
            nervio = Pos(x0 + (largo - lr) / 2 + 4.0, r + 0.4, 0) * Box(largo - lr - 12.0, 1.8, 5.0)
            nervio = filetear(nervio, 0.7, [a for a in nervio.edges() if a.length > 5])
            cuerpo = cuerpo + rampa + nervio
            notas.append("Mira delantera integral (rampa) y nervio superior simplificados.")
        sockets = (
            Socket(
                "muzzle",
                (x0 + largo, 0.0, 0.0),
                e.ROSCAS_BOCA[str(p["rosca"])],
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {"diametro_rosca_mm": rr * 2},
            ),
            Socket(
                "recamara",
                (x0, 0.0, 0.0),
                INTERFAZ_CANON_REVOLVER if revolver else INTERFAZ_CANON_PISTOLA,
                (-1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {},
            ),
        )
        cotas = (estimada("canon.largo_hombro_rosca", hombro),)
        caja = cuerpo.bounding_box()
        return Geometria(
            cuerpo, sockets, cotas, tuple(notas), (caja.size.X, caja.size.Y, caja.size.Z), vaciados=vaciados
        )
