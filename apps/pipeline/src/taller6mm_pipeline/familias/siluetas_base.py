"""Pistolas construidas a partir del CONTORNO medido en fotos de referencia (plan T2 de docs/05).

Cada parte (corredera, armazón, cachas, guardamonte, alzas, base del cargador…) es el contorno real de la foto,
medido en `catalogo/siluetas-referencia.json` (números, sin píxeles) y extruido con su ancho y filetes; encima van los
detalles medidos: serrados cortados, ventana, cañón a ras, tornillos, hoyuelos de agarre. Los anchos en Z no se ven en
una foto lateral: son estimaciones de confianza baja (`es_demo`) hasta tener medida con calibre.

Ejes del proyecto: +X boca, +Y arriba, +Z izquierda del tirador; origen en la cara trasera de la corredera
(x = 0) y su borde inferior (y = 0), plano medio z = 0. Todo T0 y no publicable.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from build123d import Compound, Face, Line, Pos, Sphere, Wire, extrude

from taller6mm_pipeline.familias.formas import cilindro_en, filetear, revolucion
from taller6mm_pipeline.familias.glb import escribir_glb
from taller6mm_pipeline.familias.malla import Malla, teselar
from taller6mm_pipeline.familias.silueta_solidos import extruir_contorno

RAIZ = Path(__file__).resolve().parents[5]
RUTA_SILUETAS = RAIZ / "catalogo" / "siluetas-referencia.json"
FECHA = "2026-11-25"
FUENTE_ANCHO = (
    "estimado: el ancho en Z no se ve en una foto lateral; proporción típica de la familia, sin calibre ni ficha "
    "(25-11-2026)"
)
Punto = tuple[float, float]


def cargar_siluetas(ruta: Path = RUTA_SILUETAS) -> dict[str, dict[str, Any]]:
    doc = json.loads(ruta.read_text(encoding="utf-8"))
    return {r["id"]: r for r in doc["replicas"]}


@dataclass
class Parte:
    nombre: str
    solido: Any
    material: str  # clave de la paleta (`colores_srgb` de la réplica o acabado propio)
    ancho_mm: float | None
    notas: list[str] = field(default_factory=list)


# --- ayudantes de geometría ---------------------------------------------------------------------------------------


def prisma_xy(pts: Sequence[Punto], z0: float, z1: float) -> Any:
    """Polígono del plano XY extruido de z0 a z1 (cortes: ranuras, ventanas)."""
    cara = Face(Wire([Line(a, b) for a, b in zip(pts, [*pts[1:], pts[0]], strict=True)]))
    return Pos(0, 0, z0) * extrude(cara, amount=z1 - z0)


def ranura(p0: Punto, p1: Punto, ancho: float, z0: float, z1: float) -> Any:
    """Ranura recta de `ancho` mm entre dos puntos del plano XY (serrado)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * ancho / 2, dx / n * ancho / 2
    return prisma_xy(
        [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)], z0, z1
    )


def _dist_borde(p: Punto, contorno: Sequence[Punto]) -> float:
    a = np.asarray(contorno)
    b = np.roll(a, -1, axis=0)
    ab = b - a
    t = np.clip(
        ((p[0] - a[:, 0]) * ab[:, 0] + (p[1] - a[:, 1]) * ab[:, 1]) / np.maximum((ab**2).sum(axis=1), 1e-12), 0, 1
    )
    q = a + ab * t[:, None]
    return float(np.hypot(q[:, 0] - p[0], q[:, 1] - p[1]).min())


def _dentro(p: Punto, poly: Sequence[Punto]) -> bool:
    x, y = p
    dentro = False
    for (x0, y0), (x1, y1) in zip(poly, [*poly[1:], poly[0]], strict=True):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            dentro = not dentro
    return dentro


def rejilla_hex(poly: Sequence[Punto], contorno: Sequence[Punto], paso: float, margen: float) -> list[Punto]:
    """Centros de una rejilla hexagonal dentro de `poly` y a más de `margen` mm del borde de `contorno`."""
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    sal: list[Punto] = []
    fila, y = 0, min(ys)
    alto = paso * math.sqrt(3) / 2
    while y <= max(ys):
        x = min(xs) + (paso / 2 if fila % 2 else 0.0)
        while x <= max(xs):
            if _dentro((x, y), poly) and _dist_borde((x, y), contorno) >= margen:
                sal.append((round(x, 3), round(y, 3)))
            x += paso
        y += alto
        fila += 1
    return sal


def hoyuelos(solido: Any, centros: Sequence[Punto], z_cara: float, radio: float, hondo: float) -> Any:
    """Resta esferas centradas fuera de la cara plana `z_cara` (ambas caras): hoyuelos esféricos de `hondo` mm."""
    desfase = radio - hondo
    esferas = []
    for lado in (1, -1):
        for x, y in centros:
            esferas.append(Pos(x, y, lado * (abs(z_cara) + desfase)) * Sphere(radio))
    return solido - Compound(esferas)


def tornillo(x: float, y: float, r: float, z_cara: float, alto: float = 0.5) -> list[Any]:
    """Cabezas de tornillo (cilindros bajos) en las dos caras."""
    return [cilindro_en("z", r, alto + 1.0, (x, y, lado * (z_cara + alto / 2 - 0.5))) for lado in (1, -1)]


def cano_hueco(x_boca: float, y: float, r_ext: float, r_int: float, largo: float) -> Any:
    """Tubo del cañón (eje X) que acaba en x_boca."""
    tubo = revolucion([(r_int, 0.0), (r_ext, 0.0), (r_ext, largo), (r_int, largo)])
    tubo = tubo - revolucion([(0.0, -1.0), (r_int, -1.0), (r_int, largo + 1), (0.0, largo + 1)])
    return Pos(x_boca - largo, y, 0) * (
        cilindro_en("x", r_ext, largo, (largo / 2, 0, 0)) - cilindro_en("x", r_int, largo + 2, (largo / 2, 0, 0))
    )


# --- mallas e informe ---------------------------------------------------------------------------------------------


def teselar_parte(p: Parte) -> Malla:
    return teselar(p.solido, 0.05, 0.35)


def glb_parte(p: Parte, replica: dict[str, Any], malla: Malla, extras: dict[str, Any]) -> bytes:
    meta = {
        "familia": "pistola.silueta",
        "id_variante": f"{replica['id']}.{p.nombre}",
        "nombre": f"{replica['nombre']} - {p.nombre}",
        "nivel": "T0",
        "publicable_3d": False,
        "sospechosa_de_cubo": False,
        "tiene_malla": True,
        "es_demo": False,
        "material": p.material,
        "parametros": {"ancho_z_mm": p.ancho_mm},
        "pendientes": ["ancho en Z (no visible en foto lateral)"],
        "notas": p.notas,
        "cotas": extras.get("cotas", []),
    }
    return escribir_glb(malla, [], meta, material=p.material)


__all__ = [
    "Parte",
    "cano_hueco",
    "cargar_siluetas",
    "extruir_contorno",
    "filetear",
    "glb_parte",
    "hoyuelos",
    "prisma_xy",
    "ranura",
    "rejilla_hex",
    "teselar_parte",
    "tornillo",
]
