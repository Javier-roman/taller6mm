"""Modelos guiados por silueta: AKM, AK-105, Mk18 Mod.1, Hi-Capa y Glock 19X.

Los contornos salen de `catalogo/siluetas-referencia.json` (medidos en fotos de referencia interna, solo números).
Los anchos en Z (no se ven en una foto lateral) y los relieves finos son estimaciones de confianza baja, declaradas en
cada parte. Todo T0 y no publicable. Sin logos ni marcajes: los rótulos de las fotos no se reproducen.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from build123d import Compound

from taller6mm_pipeline.familias.formas import cilindro_en
from taller6mm_pipeline.familias.siluetas_base import (
    Parte,
    cano_hueco,
    hoyuelos,
    prisma_xy,
    ranura,
    rejilla_hex,
    tornillo,
)
from taller6mm_pipeline.familias.siluetas_motor import Spec, construir, contorno_de, paleta

Punto = tuple[float, float]
Modelo = Callable[[dict[str, Any]], tuple[dict[str, Parte], dict[str, dict[str, Any]]]]


def _px(rep: dict[str, Any], x: float, y_img: float) -> Punto:
    """Coordenadas de la foto ORIGINAL (y hacia abajo) a mm del modelo (la foto se volcó si `espejo`)."""
    w, h = rep["foto_px"]
    xr = w - 1 - x if rep.get("espejo") else x
    ox, oy = rep["origen_px"]
    mm = rep["calibre"]["mm_por_px"]
    return ((xr - ox) * mm, (h - y_img - oy) * mm)


def _cortar(solido: Any, cortes: Sequence[Any]) -> Any:
    return solido - Compound(list(cortes)) if cortes else solido


def _cortes_horizontales(ext: Sequence[Punto], y: float) -> list[float]:
    xs = []
    for (xa, ya), (xb, yb) in zip(ext, [*ext[1:], ext[0]], strict=True):
        if (ya <= y < yb) or (yb <= y < ya):
            xs.append(xa + (xb - xa) * (y - ya) / (yb - ya))
    return sorted(xs)


def nervaduras_cargador(
    ext: Sequence[Punto], fracs: Sequence[float], ancho: float, hondo: float, z_cara: float, paso: float = 8.0
) -> list[Any]:
    """Nervaduras estampadas que siguen la curva del cargador: cada una es la línea a la fracción `t` entre el borde
    delantero y el trasero de la silueta, a cada altura."""
    ys = [p[1] for p in ext]
    cortes: list[Any] = []
    for t in fracs:
        pts: list[Punto] = []
        y = min(ys) + 5.0
        while y < max(ys) - 5.0:
            xs = _cortes_horizontales(ext, y)
            if len(xs) >= 2:
                pts.append((xs[0] + t * (xs[-1] - xs[0]), y))
            y += paso
        for p0, p1 in itertools.pairwise(pts):
            cortes.append(ranura(p0, p1, ancho, z_cara - hondo, z_cara + 1.0))
            cortes.append(ranura(p0, p1, ancho, -z_cara - 1.0, -z_cara + hondo))
    return cortes


def ranuras_laterales(rects: Sequence[tuple[float, float, float, float]], z_cara: float, hondo: float) -> list[Any]:
    """Ranuras rectangulares ciegas (M-LOK, ventanas) en ambos costados."""
    cortes = []
    for x0, y0, x1, y1 in rects:
        pol = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        cortes.append(prisma_xy(pol, z_cara - hondo, z_cara + 1.0))
        cortes.append(prisma_xy(pol, -z_cara - 1.0, -z_cara + hondo))
    return cortes


def agujeros_z(centros: Sequence[Punto], r: float, z_cara: float, hondo: float) -> list[Any]:
    cortes = []
    for x, y in centros:
        for lado in (1, -1):
            cortes.append(cilindro_en("z", r, hondo + 1.0, (x, y, lado * (z_cara - hondo / 2 + 0.5))))
    return cortes


def _pal(rep: dict[str, Any], mapa: dict[str, tuple[str, float, float]]) -> dict[str, dict[str, Any]]:
    return paleta(rep, mapa)


def _caja(rep: dict[str, Any], n: str) -> dict[str, float]:
    return rep["proporciones"]["cajas_partes_mm"][n]


# --- AKM ----------------------------------------------------------------------------------------------------------

SPECS_AKM = (
    Spec("receptor", "metal", 37.0, 11.0, eje="x", nota="tapa y cuerpo con el contorno medido; ancho estimado"),
    Spec("mira_trasera", "metal", 26.0, 1.5),
    Spec("culata", "madera", 46.0, 7.0, nota="caída y cantonera del contorno medido"),
    Spec("empunadura", "polimero", 34.0, 10.0),
    Spec("cargador", "metal", 37.0, 3.0, nota="curva del contorno medido"),
    Spec("guardamonte", "metal", 3.5, 0.8),
    Spec("guardamanos_sup", "madera", 36.0, 6.0),
    Spec("guardamanos_inf", "madera", 44.0, 7.0),
    Spec("tubo_gases", "metal", None),
    Spec("canon", "metal", None),
    Spec("freno", "metal", None),
    Spec("base_alza", "metal", 9.0, 1.0),
)


def modelo_akm(rep: dict[str, Any]) -> tuple[dict[str, Parte], dict[str, dict[str, Any]]]:
    partes = construir(rep, SPECS_AKM)
    ext_c, _ = contorno_de(rep, "cargador")
    partes["cargador"].solido = _cortar(
        partes["cargador"].solido, nervaduras_cargador(ext_c, (0.2, 0.35, 0.5, 0.65, 0.8), 3.2, 1.6, 18.5)
    )
    for x, y, r in ((505, 265, 2.0), (550, 267, 2.0), (588, 288, 2.0), (733, 285, 2.0), (500, 290, 1.8)):
        cx, cy = _px(rep, x, y)
        for c in tornillo(cx, cy, r, 18.5, 0.7):
            partes["receptor"].solido = partes["receptor"].solido + c
    partes["receptor"].notas.append("remaches laterales medidos en la foto; sin marcajes")
    pal = _pal(
        rep,
        {"metal": ("metal_negro", 0.6, 0.45), "madera": ("madera", 0.0, 0.5), "polimero": ("empunadura", 0.0, 0.5)},
    )
    return partes, pal


# --- AK-105 -------------------------------------------------------------------------------------------------------

SPECS_AK105 = (
    Spec("receptor", "metal", 38.0, 12.0, eje="x"),
    Spec("guardamanos", "polimero", 42.0, 6.0, nota="guardamanos M-LOK: ranuras medidas en la foto"),
    Spec("boca", "metal", None),
    Spec("alza_delantera", "metal", 8.0, 0.8),
    Spec("tubo_culata", "metal", None),
    Spec("culata", "polimero", 52.0, 8.0),
    Spec("empunadura", "polimero", 34.0, 10.0),
    Spec("cargador", "polimero", 36.0, 3.0, nota="curva del contorno medido"),
    Spec("guardamonte", "metal", 3.5, 0.8),
)


def modelo_ak105(rep: dict[str, Any]) -> tuple[dict[str, Parte], dict[str, dict[str, Any]]]:
    partes = construir(rep, SPECS_AK105)
    c = _caja(rep, "guardamanos")
    filas = (c["y_ini_mm"] + (c["alto_mm"]) * 0.62, c["y_ini_mm"] + c["alto_mm"] * 0.30)
    rects = []
    for k, yc in enumerate(filas):
        x = c["x_ini_mm"] + 22.0 + (14.0 if k else 0.0)
        while x + 34 < c["x_fin_mm"] - 18:
            rects.append((x, yc - 3.2, x + 34.0, yc + 3.2))
            x += 52.0
    partes["guardamanos"].solido = _cortar(partes["guardamanos"].solido, ranuras_laterales(rects, 21.0, 6.0))
    ext_c, _ = contorno_de(rep, "cargador")
    partes["cargador"].solido = _cortar(
        partes["cargador"].solido, nervaduras_cargador(ext_c, (0.25, 0.5, 0.75), 3.0, 1.4, 18.0, 9.0)
    )
    pal = _pal(rep, {"metal": ("metal_negro", 0.6, 0.4), "polimero": ("polimero", 0.0, 0.55)})
    return partes, pal


# --- Mk18 Mod.1 ---------------------------------------------------------------------------------------------------

SPECS_MK18 = (
    Spec("receptor_sup", "receptor", 40.0, 12.0, eje="x"),
    Spec("receptor_inf", "receptor", 38.0, 6.0, eje="x"),
    Spec("guardamanos", "arena", 52.0, 14.0),
    Spec("alza_delantera", "receptor", 4.0, 0.6),
    Spec("alza_trasera", "receptor", 8.0, 0.8),
    Spec("boca", "receptor", None),
    Spec("culata", "arena", 48.0, 12.0),
    Spec("empunadura", "receptor", 32.0, 10.0),
    Spec("cargador", "receptor", 28.0, 3.0),
)


def modelo_mk18(rep: dict[str, Any]) -> tuple[dict[str, Parte], dict[str, dict[str, Any]]]:
    partes = construir(rep, SPECS_MK18)
    c = _caja(rep, "guardamanos")
    centros = []
    for k, yc in enumerate((c["y_ini_mm"] + c["alto_mm"] * 0.68, c["y_ini_mm"] + c["alto_mm"] * 0.36)):
        x = c["x_ini_mm"] + 12.0 + (4.5 if k else 0.0)
        while x < c["x_fin_mm"] - 22.0:
            centros.append((x, yc))
            x += 9.0
    partes["guardamanos"].solido = _cortar(partes["guardamanos"].solido, agujeros_z(centros, 2.6, 26.0, 9.0))
    ext_c, _ = contorno_de(rep, "cargador")
    partes["cargador"].solido = _cortar(
        partes["cargador"].solido, nervaduras_cargador(ext_c, (0.3, 0.5, 0.7), 3.0, 1.4, 14.0, 9.0)
    )
    pal = _pal(
        rep,
        {"receptor": ("receptor", 0.6, 0.42), "arena": ("culata", 0.0, 0.5)},
    )
    return partes, pal


# --- Hi-Capa ------------------------------------------------------------------------------------------------------

SPECS_HICAPA = (
    Spec("corredera", "corredera", 25.0, 2.4, eje="x"),
    Spec("alza_delantera", "corredera", 3.6, 0.5),
    Spec("alza_trasera", "corredera", 10.0, 0.6),
    Spec("cubierta_optica", "corredera", 17.0, 0.6),
    Spec("armazon", "armazon", 23.0, 2.2, eje="x"),
    Spec("cachas", "polimero", 34.0, 9.0, nota="cachas con hoyuelos de agarre: relieve estimado"),
    Spec("guardamonte", "armazon", 9.0, 2.2, eje="x", nota="arco del guardamonte: ancho estimado"),
    Spec("base_cargador", "polimero", 30.0, 2.5),
)


def modelo_hicapa(rep: dict[str, Any]) -> tuple[dict[str, Parte], dict[str, dict[str, Any]]]:
    partes = construir(rep, SPECS_HICAPA)
    d = rep["detalles_mm"]
    cor = partes["corredera"]
    cortes = [
        ranura((r[0], r[1]), (r[2], r[3]), 1.4, 12.5 - 1.0, 13.5)
        for r in d["ranuras_traseras"] + d["ranuras_frontales"]
    ]
    cortes += [
        ranura((r[0], r[1]), (r[2], r[3]), 1.4, -13.5, -12.5 + 1.0)
        for r in d["ranuras_traseras"] + d["ranuras_frontales"]
    ]
    x0, y0, x1, y1 = d["ventana"][0]
    cortes.append(prisma_xy([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 12.5 - 1.2, 13.5))
    cc = _caja(rep, "corredera")
    y_eje = cc["y_ini_mm"] + cc["alto_mm"] * 0.57
    cortes.append(cilindro_en("x", 5.6, 26.0, (cc["x_fin_mm"] - 12.0, y_eje, 0.0)))
    cor.solido = _cortar(cor.solido, cortes)
    cor.notas.append("serrados y ventana medidos en la foto; cañón a ras de la boca")
    partes["canon"] = Parte(
        "canon",
        cano_hueco(cc["x_fin_mm"] - 0.6, y_eje, 5.0, 3.0, 24.0),
        "metal_canon",
        None,
        ["cañón visible en la boca"],
    )
    ext_ca, _ = contorno_de(rep, "cachas")
    centros = rejilla_hex([tuple(p) for p in d["textura_hoyuelos"]], ext_ca, 4.7, 9.0)
    partes["cachas"].solido = hoyuelos(partes["cachas"].solido, centros, 17.0, 2.15, 0.5)
    for (x, y, r), zc, alto in zip(d["tornillos"], (17.0, 11.5, 4.5, 17.0), (0.6, 0.5, 0.5, 1.2), strict=True):
        for c in tornillo(x, y, r, zc, alto):
            nombre = "cachas" if zc == 17.0 else ("guardamonte" if zc == 4.5 else "armazon")
            partes[nombre].solido = partes[nombre].solido + c
    pal = _pal(
        rep,
        {
            "corredera": ("corredera", 0.7, 0.4),
            "armazon": ("armazon_guardamonte", 0.7, 0.42),
            "polimero": ("empunadura", 0.0, 0.5),
        },
    )
    pal["metal_canon"] = {
        **pal["corredera"],
        "rgb": [28, 28, 29],
        "rugosidad": 0.3,
        "nota": "acero del cañón: acabado propio",
    }
    return partes, pal


# --- Glock 19X ----------------------------------------------------------------------------------------------------

SPECS_GLOCK = (
    Spec("corredera", "corredera", 25.4, 2.2, eje="x"),
    Spec("alza_delantera", "negro", 3.2, 0.4),
    Spec("alza_trasera", "negro", 10.0, 0.5),
    Spec("armazon", "armazon", 27.0, 6.0, eje="x"),
    Spec("riel_frontal", "armazon", 21.0, 1.6, eje="x"),
    Spec("guardamonte", "armazon", 11.0, 2.5, eje="x"),
    Spec("gatillo", "negro", 7.0, 1.0),
    Spec("retenida_cargador", "negro", 5.0, 0.8, z=15.0),
    Spec("base_cargador", "armazon", 26.0, 2.5),
)


def modelo_glock(rep: dict[str, Any]) -> tuple[dict[str, Parte], dict[str, dict[str, Any]]]:
    partes = construir(rep, SPECS_GLOCK)
    d = rep["detalles_mm"]
    cor = partes["corredera"]
    cortes = []
    for r in d["ranuras_traseras"]:
        cortes.append(ranura((r[0], r[1]), (r[2], r[3]), 1.3, 12.7 - 0.9, 13.7))
        cortes.append(ranura((r[0], r[1]), (r[2], r[3]), 1.3, -13.7, -12.7 + 0.9))
    x0, y0, x1, y1 = d["ventana"][0]
    cortes.append(prisma_xy([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 12.7 - 1.4, 13.7))
    cc = _caja(rep, "corredera")
    y_eje = cc["y_ini_mm"] + cc["alto_mm"] * 0.55
    cortes.append(cilindro_en("x", 5.4, 24.0, (cc["x_fin_mm"] - 11.0, y_eje, 0.0)))
    cor.solido = _cortar(cor.solido, cortes)
    partes["canon"] = Parte(
        "canon",
        cano_hueco(cc["x_fin_mm"] + 1.5, y_eje, 5.0, 3.0, 24.0),
        "negro",
        None,
        ["cañón ligeramente adelantado"],
    )
    ext_a, _ = contorno_de(rep, "armazon")
    centros = rejilla_hex([tuple(p) for p in d["textura_hoyuelos"]], ext_a, 2.5, 5.0)
    partes["armazon"].solido = hoyuelos(partes["armazon"].solido, centros, 13.5, 0.8, 0.35)
    for x, y, r in d["tornillos"]:
        for c in tornillo(x, y, r, 13.5, 0.5):
            partes["armazon"].solido = partes["armazon"].solido + c
    pal = _pal(
        rep,
        {"corredera": ("corredera", 0.2, 0.42), "armazon": ("armazon", 0.0, 0.55), "negro": ("mando_negro", 0.0, 0.45)},
    )
    return partes, pal


MODELOS: dict[str, Modelo] = {
    "akm-lateral-izq": modelo_akm,
    "ak105-lateral-izq": modelo_ak105,
    "mk18-mod1-lateral-izq": modelo_mk18,
    "hicapa-nighthawk-lateral-izq": modelo_hicapa,
    "glock-19x-lateral-izq": modelo_glock,
}

__all__ = ["MODELOS", "math", "np"]
