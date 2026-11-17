"""Familias de boca de cañón: bocacha/apagallamas y silenciador, con rosca de 14 mm (CW o CCW).

Origen: centro de la cara trasera (la que apoya contra el cañón), sobre el eje. La pieza avanza hacia +X.
La rosca es un estándar (M14x1 a derechas o a izquierdas); longitud, diámetros y ranuras son cotas del SKU.

Cada pieza es un sólido de revolución con su detalle torneado (chaflanes, gargantas de partición, corona rehundida y
alojamiento roscado con filetes en V al paso de la rosca) más el fresado: moleteado y acanalado en las tapas del
silenciador, planos de llave y ranuras en las bocachas. La hélice no se modela (los filetes son anillos), así que el
sentido de la rosca no se ve en la malla. Las proporciones del detalle son estimadas: no son cotas de ningún SKU.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from build123d import Align, Box, Cylinder, Pos, Rot

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import (
    Familia,
    Geometria,
    Parametro,
    ParametroInvalidoError,
    Socket,
    Valor,
)
from taller6mm_pipeline.familias.formas import (
    ALTURA_FILETE_ISO,
    cilindro_en,
    dientes_rosca,
    estrias_x,
    planos_llave_x,
    ranura_oblonga,
    revolucion_x,
)

NOTA_ROSCA = "La rosca son filetes en V al paso de M14x1 hechos de anillos: la hélice y su sentido no se modelan."
NOTA_DETALLE = "Chaflanes, gargantas, corona y fresados de proporción estimada: no son cotas de ningún SKU."
R_ROSCA = e.ROSCA_14_DIAMETRO.valor_mm / 2
PASO = e.ROSCA_14_PASO.valor_mm
Perfil = list[tuple[float, float]]

_ROSCA = Parametro("rosca", "Rosca de boca", str, opciones=tuple(e.ROSCAS_BOCA), por_defecto="14mm_ccw")
_COMUNES = (
    Parametro("longitud", "Longitud total", float, "mm", minimo=10, maximo=350, de_sku=True),
    Parametro("diametro", "Diámetro exterior", float, "mm", minimo=16, maximo=60, de_sku=True),
    Parametro("diametro_paso", "Diámetro del paso interior", float, "mm", 6, 40, de_sku=True, critico=False),
    Parametro(
        "profundidad_rosca", "Profundidad del alojamiento roscado", float, "mm", 3, 40, de_sku=True, critico=False
    ),
)


def _chaflan(p: Mapping[str, Valor]) -> float:
    """Chaflán de las caras: como mucho 1 mm y nunca más de lo que deja la pared alrededor de la rosca."""
    radio = float(p["diametro"]) / 2
    c = min(1.0, 0.1 * radio)
    if p["profundidad_rosca"] is not None:
        c = min(c, 0.5 * (radio - R_ROSCA - 0.6))
    return max(c, 0.15)


def _interior(p: Mapping[str, Valor]) -> Perfil:
    """Pared interior, de delante atrás, desde el fondo del paso hasta la cara trasera (x = 0).

    Con profundidad de rosca: fondo del alojamiento, alivio al diámetro nominal, filetes en V y chaflán de entrada.
    Sin paso interior la pieza es maciza (radio 0); sin profundidad de rosca, el paso llega liso hasta atrás.
    """
    r_paso = 0.0 if p["diametro_paso"] is None else float(p["diametro_paso"]) / 2
    radio = float(p["diametro"]) / 2
    if p["profundidad_rosca"] is None or r_paso >= R_ROSCA or radio <= R_ROSCA + 0.9:
        return [(0.0, r_paso)]
    hondo = float(p["profundidad_rosca"])
    alivio, entrada = min(1.5, 0.25 * hondo), min(0.6, 0.15 * hondo)
    cresta = R_ROSCA - ALTURA_FILETE_ISO * PASO
    return [
        (hondo, r_paso),
        (hondo, R_ROSCA),
        *dientes_rosca(hondo - alivio, entrada, R_ROSCA, cresta, PASO),
        (0.0, R_ROSCA + entrada),
    ]


def _fondo_rosca(p: Mapping[str, Valor]) -> float:
    """Hasta dónde llega por dentro el alojamiento de la rosca (0 si no se modela)."""
    interior = _interior(p)
    return interior[0][0] if len(interior) > 1 else 0.0


def _corona(p: Mapping[str, Valor], r_borde: float, hondo: float) -> Perfil:
    """Cara delantera, de fuera adentro: corona rehundida en cono hasta el paso (o hasta el eje si es maciza)."""
    largo = float(p["longitud"])
    r_paso = 0.0 if p["diametro_paso"] is None else float(p["diametro_paso"]) / 2
    libre = largo - _fondo_rosca(p)
    hondo = min(hondo, 0.35 * libre)
    if r_borde - r_paso < 1.6 or hondo < 0.3:
        bisel = min(0.5, 0.3 * libre, max(0.0, r_borde - r_paso - 0.2))
        return [(largo, r_paso + bisel), (largo - bisel, r_paso)] if r_paso and bisel > 0.05 else [(largo, r_paso)]
    r_piso = r_paso + 0.45 * (r_borde - r_paso)
    if not r_paso:
        return [(largo, r_borde), (largo - hondo, r_piso), (largo - hondo, 0.0)]
    bisel = min(0.5, 0.2 * libre)
    return [(largo, r_borde), (largo - hondo, r_piso), (largo - hondo, r_paso + bisel), (largo - hondo - bisel, r_paso)]


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

    @staticmethod
    def _nominales(p: Mapping[str, Valor]) -> tuple[float, float, float]:
        return (float(p["longitud"]), float(p["diametro"]), float(p["diametro"]))

    @staticmethod
    def _vaciados(p: Mapping[str, Valor]) -> int:
        """Huecos modelados: el paso interior y el alojamiento de la rosca, si tienen dato."""
        return int(p["diametro_paso"] is not None) + int(p["profundidad_rosca"] is not None)

    @staticmethod
    def _notas(p: Mapping[str, Valor]) -> list[str]:
        notas = [NOTA_ROSCA, NOTA_DETALLE]
        if p["diametro_paso"] is None:
            notas.append("Paso interior sin dato: se modela macizo.")
        if p["profundidad_rosca"] is None:
            notas.append("Profundidad de la rosca sin dato: el alojamiento no se modela.")
        return notas

    @staticmethod
    def _trasera_con_planos(p: Mapping[str, Valor]) -> tuple[Perfil, list[Any], float]:
        """Zona trasera de una bocacha: chaflán, tramo de los planos de llave y garganta.

        Devuelve su perfil exterior, las herramientas de los dos planos y la x donde empieza el cuerpo.
        """
        largo, radio = float(p["longitud"]), float(p["diametro"]) / 2
        c = _chaflan(p)
        tramo = min(7.0, 0.16 * largo)
        garganta = min(0.9, 0.02 * largo)
        hondo = min(0.6, 0.08 * radio)
        x1 = c + tramo
        perfil = [(0.0, radio - c), (c, radio), (x1, radio), (x1, radio - hondo), (x1 + garganta, radio - hondo)]
        perfil.append((x1 + garganta, radio))
        entre_caras = 2 * max(0.86 * radio, R_ROSCA + 1.2)
        planos = planos_llave_x(radio, c + 0.4, x1 - 0.4, entre_caras) if entre_caras < 2 * radio - 0.5 else []
        return perfil, planos, x1 + garganta


class Silenciador(_PiezaDeBoca):
    id = "boca.silenciador"
    version = 2  # v2: tapas con moleteado y acanalado, gargantas de partición, corona y rosca con filetes
    nombre = "Silenciador"
    parametros = (*_COMUNES, _ROSCA)

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        diam = "diámetro sin dato" if p["diametro"] is None else f"Ø{float(p['diametro']):g} mm"
        return f"Silenciador de {largo}, {diam}, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, radio = float(p["longitud"]), float(p["diametro"]) / 2
        c = _chaflan(p)
        # Tapa trasera (moleteada) y delantera (acanalada), separadas del tubo por una garganta de partición; el
        # tubo queda unas décimas por debajo de las tapas, como en un cuerpo de tres piezas roscadas.
        tapa_t = min(16.0, max(0.11 * largo, min(7.0, 0.20 * largo)))
        tapa_f = min(14.0, max(0.09 * largo, min(6.0, 0.17 * largo)))
        g, gh, rebaje = min(0.6, 0.03 * largo), min(0.5, 0.06 * radio), min(0.35, 0.03 * radio)
        exterior = [
            (0.0, radio - c),
            (c, radio),
            (tapa_t, radio),
            (tapa_t, radio - gh),
            (tapa_t + g, radio - gh),
            (tapa_t + g, radio - rebaje),
            (largo - tapa_f - g, radio - rebaje),
            (largo - tapa_f - g, radio - gh),
            (largo - tapa_f, radio - gh),
            (largo - tapa_f, radio),
            (largo - c, radio),
            (largo, radio - c),
        ]
        corona = _corona(p, radio - c - min(2.0, 0.12 * radio), min(2.5, 0.25 * tapa_f))
        cuerpo = revolucion_x([*exterior, *corona, *_interior(p)])
        vaciados = self._vaciados(p) + 2
        if tapa_t - c >= 4.0:  # moleteado recto de la tapa trasera
            n = max(12, round(math.tau * radio / 2.2))
            cuerpo = cuerpo - estrias_x(radio, c + 0.6, tapa_t - 0.8, n, min(0.35, 0.04 * radio))
            vaciados += 1
        if tapa_f >= 5.0:  # acanalado de la tapa delantera: ocho medias cañas abiertas hacia el frente
            r_cana = 0.22 * radio
            y_cana = radio + r_cana - min(0.7, 0.08 * radio)
            cana = cilindro_en("x", r_cana, tapa_f, (largo - tapa_f / 2 + 1.4, y_cana, 0.0))
            cuerpo = cuerpo - [Rot(22.5 + 45.0 * k, 0, 0) * cana for k in range(8)]
            vaciados += 1
        return Geometria(cuerpo, (), (), tuple(self._notas(p)), self._nominales(p), vaciados)


class Bocacha(_PiezaDeBoca):
    id = "boca.bocacha"
    version = 2  # v2: planos de llave, garganta, corona en cono, ranuras de fondo redondo y rosca con filetes
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
        largo, radio = float(p["longitud"]), float(p["diametro"]) / 2
        notas = self._notas(p)
        trasera, planos, _ = self._trasera_con_planos(p)
        c = min(1.2, 0.12 * radio)
        exterior = [*trasera, (largo - c, radio), (largo, radio - c)]
        cuerpo = revolucion_x([*exterior, *_corona(p, radio - c - 0.4, min(2.2, 0.25 * radio)), *_interior(p)])
        vaciados = self._vaciados(p) + 1
        if planos:
            cuerpo = cuerpo - planos
        n = int(p["ranuras"])
        if n and (p["ancho_ranura"] is None or p["longitud_ranura"] is None):
            notas.append("Ranuras sin cotas: no se modelan.")
        elif n:
            lr, ar = float(p["longitud_ranura"]), float(p["ancho_ranura"])
            # Cada ranura corta la pared desde el eje hacia fuera, queda abierta por la cara delantera y termina
            # atrás en media caña (el fondo que deja la fresa).
            x0 = largo - lr + ar / 2
            corte = Pos(x0, 0, 0) * Box(lr + 1, radio + 1, ar, align=(Align.MIN, Align.MIN, Align.CENTER))
            corte = corte + Pos(x0, (radio + 1) / 2, 0) * Rot(90, 0, 0) * Cylinder(ar / 2, radio + 1)
            cuerpo = cuerpo - [Rot(i * 360.0 / n, 0, 0) * corte for i in range(n)]
            vaciados += n
        return Geometria(cuerpo, (), (), tuple(notas), self._nominales(p), vaciados)


class ApagallamasA2(_PiezaDeBoca):
    """Apagallamas tipo A2 («jaula») de M4/AR: cinco ranuras oblongas cerradas, a 60 grados, y la base ciega.

    El socket `socket.muzzle` está en la cara trasera (donde entra la rosca), con la normal hacia atrás. Las cotas
    son del SKU: sin ficha son de barrido y la pieza sale `es_demo` (T1 como máximo, `publicable_3d = False`).
    """

    id = "boca.apagallamas_a2"
    version = 2  # v2: cinco ranuras cerradas con la base ciega (antes, cuatro abiertas), cámara, planos y corona
    nombre = "Apagallamas A2"
    RANURAS = 5
    ANGULOS = (-120.0, -60.0, 0.0, 60.0, 120.0)  # 0 = arriba; abajo (180) no lleva ranura
    parametros = (
        *_COMUNES,
        _ROSCA,
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
        return f"Apagallamas A2 de {largo}, {self.RANURAS} ranuras, rosca {p['rosca']}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, radio = float(p["longitud"]), float(p["diametro"]) / 2
        notas = self._notas(p)
        vaciados = self._vaciados(p) + 1
        trasera, planos, x_cuerpo = self._trasera_con_planos(p)
        c = min(2.0, 0.18 * radio)
        exterior = [*trasera, (largo - c, radio), (largo, radio - c)]
        interior = _interior(p)
        r_paso = 0.0 if p["diametro_paso"] is None else float(p["diametro_paso"]) / 2
        # Zona de las ranuras: entre la garganta trasera (o el fondo de la rosca) y la pared delantera.
        x1 = largo - max(3.0, 0.09 * largo)
        x_min = max(x_cuerpo, _fondo_rosca(p)) + 1.5
        con_cotas = p["ancho_ranura"] is not None and p["longitud_ranura"] is not None
        lr = min(float(p["longitud_ranura"]), x1 - x_min) if con_cotas else 0.0
        ar = float(p["ancho_ranura"]) if con_cotas else 0.0
        ranurable = con_cotas and lr >= ar + 0.5
        if ranurable and r_paso and radio - r_paso > 4.0:
            # Cámara de expansión bajo las ranuras: la pared queda fina y el paso solo se estrecha en la salida.
            r_camara = max(r_paso + 1.0, radio - max(2.4, 0.26 * radio))
            interior = [
                (x1 + 1.0, r_paso),
                (x1 + 0.2, r_camara),
                (x1 - lr - 0.2, r_camara),
                (x1 - lr - 1.0, r_paso),
                *interior,
            ]
        cuerpo = revolucion_x([*exterior, *_corona(p, radio - c - 0.4, 0.8), *interior])
        if planos:
            cuerpo = cuerpo - planos
        if not con_cotas:
            notas.append("Ranuras sin cotas: no se modelan.")
        elif not ranurable:
            notas.append("Ranuras sin sitio entre la rosca y la pared delantera: no se modelan.")
        else:
            if lr < float(p["longitud_ranura"]):
                notas.append("Ranuras recortadas para no invadir la rosca ni la pared delantera.")
            fondo = r_paso if r_paso else 0.6 * radio  # maciza: ranuras ciegas
            ventana = Pos(x1 - lr / 2, fondo - 0.5, 0) * ranura_oblonga(lr, ar, radio - fondo + 1.5)
            cuerpo = cuerpo - [Rot(a, 0, 0) * ventana for a in self.ANGULOS]
            vaciados += self.RANURAS
            notas.append("Cinco ranuras a 60 grados con la base ciega: reparto estimado, sin cota de SKU.")
        socket = Socket(
            "muzzle",
            (0.0, 0.0, 0.0),
            e.ROSCAS_BOCA[str(p["rosca"])],
            (-1.0, 0.0, 0.0),  # la rosca entra por detrás, hacia el cañón
            (0.0, 0.0, 1.0),
            {"referencia": "centro de la cara trasera", "diametro_rosca_mm": e.ROSCA_14_DIAMETRO.valor_mm},
        )
        return Geometria(cuerpo, (socket,), (), tuple(notas), self._nominales(p), vaciados)
