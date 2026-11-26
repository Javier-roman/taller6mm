"""De un contorno medido (mm) a un sólido de build123d: aristas rectas en las esquinas y splines en las curvas.

El contorno sale de `fotos/silueta.py` (números, nunca píxeles). Un polígono de cientos de segmentos cortos no se
puede filetear con OCCT; por eso los vértices del Douglas-Peucker se agrupan: entre dos esquinas duras (giro mayor que
`esquina_deg`) pasa un único `Spline`, y los tramos casi rectos son `Line`. Así la pieza tiene pocas caras y admite
filetes de verdad.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from build123d import Face, Line, Plane, Pos, RectangleRounded, Spline, Wire, extrude

from taller6mm_pipeline.familias.formas import interpolar
from taller6mm_pipeline.fotos import silueta as sil

Punto = tuple[float, float]
PASO_SPLINE_MM = 4.0


def _giro(a: Punto, b: Punto, c: Punto) -> float:
    """Ángulo de giro en `b` (grados, 0 = recto)."""
    v1, v2 = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    c_ = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(c_))


def aristas_desde_poligono(pts: Sequence[Punto], esquina_deg: float = 32.0) -> list[Any]:
    """Aristas encadenadas (cerradas) de un polígono: `Line` entre esquinas duras, `Spline` por las curvas."""
    n = len(pts)
    duras = [i for i in range(n) if _giro(pts[i - 1], pts[i], pts[(i + 1) % n]) > esquina_deg]
    if not duras:  # todo es curva: spline periódico
        return [Spline(*pts, periodic=True)]
    aristas: list[Any] = []
    for k, i in enumerate(duras):
        j = duras[(k + 1) % len(duras)]
        tramo = [pts[(i + t) % n] for t in range(((j - i) % n or n) + 1)]
        if len(tramo) == 2:
            aristas.append(Line(*tramo))
        else:
            # Un spline por pocos puntos lejanos se desborda y se come esquinas: se añaden puntos intermedios.
            denso: list[Punto] = [tramo[0]]
            for a, b in itertools.pairwise(tramo):
                paso = max(1, math.ceil(math.dist(a, b) / PASO_SPLINE_MM))
                denso += [
                    (a[0] + (b[0] - a[0]) * k / paso, a[1] + (b[1] - a[1]) * k / paso) for k in range(1, paso + 1)
                ]
            aristas.append(Spline(*denso))
    return aristas


def cara_con_huecos(ext: Sequence[Punto], huecos: Sequence[Sequence[Punto]] = (), esquina_deg: float = 32.0) -> Face:
    cara = Face(Wire(aristas_desde_poligono(ext, esquina_deg)))
    for h in huecos:
        cara = cara - Face(Wire(aristas_desde_poligono(h, esquina_deg)))
    return cara


def _eje_principal(ext: Sequence[Punto], eje: str = "pca") -> tuple[tuple[float, float], tuple[float, float]]:
    """Eje mayor (PCA) del contorno y su perpendicular, ambos unitarios (o X / Y si `eje` lo fija)."""
    if eje == "x":
        return (1.0, 0.0), (0.0, 1.0)
    if eje == "y":
        return (0.0, 1.0), (-1.0, 0.0)
    a = np.asarray(ext)
    c = a - a.mean(axis=0)
    _, vec = np.linalg.eigh(c.T @ c)
    u = vec[:, 1]
    if u[0] < 0:
        u = -u
    return (float(u[0]), float(u[1])), (float(-u[1]), float(u[0]))


def prisma_redondeado(
    ext: Sequence[Punto], ancho_mm: float, radio: float, z_centro: float = 0.0, eje: str = "pca"
) -> Any:
    """Prisma a lo largo del eje mayor del contorno con sección (perpendicular x Z) de rectángulo redondeado: al
    intersecarlo con el contorno extruido redondea las aristas largas (arriba y abajo del receptor, culata, cargador)
    sin filetes de OCCT, que se cuelgan con contornos medidos."""
    (ux, uy), (vx, vy) = _eje_principal(ext, eje)
    a = np.asarray(ext)
    pu, pv = a @ np.array([ux, uy]), a @ np.array([vx, vy])
    largo = float(pu.max() - pu.min()) + 4.0
    alto_v = float(pv.max() - pv.min())
    cu, cv = float((pu.max() + pu.min()) / 2), float((pv.max() + pv.min()) / 2)
    r = max(0.1, min(radio, alto_v / 2 - 0.05, ancho_mm / 2 - 0.05))
    origen = (ux * (cu - largo / 2) + vx * cv, uy * (cu - largo / 2) + vy * cv, z_centro)
    plano = Plane(origin=origen, x_dir=(vx, vy, 0), z_dir=(ux, uy, 0))
    seccion = RectangleRounded(alto_v, ancho_mm, r)
    return extrude(plano * seccion, amount=largo)


def prisma_planta(
    ext: Sequence[Punto], nodos: Sequence[tuple[float, float]], eje: str = "x", z_centro: float = 0.0
) -> Any:
    """Prisma que da el ESTRECHAMIENTO de la pieza (sección transversal que varía): ancho en Z según una posición
    relativa 0-1 a lo largo de X (0 = parte trasera) o de Y (0 = arriba). Al intersecarlo con el contorno extruido, la
    culata se estrecha hacia el cuello, la empuñadura se afina hacia abajo, etc. Los anchos son estimaciones."""
    a = np.asarray(ext)
    x0, x1, y0, y1 = float(a[:, 0].min()), float(a[:, 0].max()), float(a[:, 1].min()), float(a[:, 1].max())
    ts = [n[0] for n in nodos]
    ws = [n[1] for n in nodos]
    paso = 28
    fr = [i / paso for i in range(paso + 1)]
    anchos = [interpolar(ts, ws, t) for t in fr]
    if eje == "x":
        arriba = [(x0 - 1 + (x1 - x0 + 2) * t, z_centro + w / 2) for t, w in zip(fr, anchos, strict=True)]
        abajo = [(x, 2 * z_centro - z) for x, z in reversed(arriba)]
        pts = [(x, y0 - 1.0, z) for x, z in arriba + abajo]
        direccion, largo = (0, 1, 0), (y1 - y0) + 2.0
    else:
        arriba = [(y1 + 1 - (y1 - y0 + 2) * t, z_centro + w / 2) for t, w in zip(fr, anchos, strict=True)]
        abajo = [(y, 2 * z_centro - z) for y, z in reversed(arriba)]
        pts = [(x0 - 1.0, y, z) for y, z in arriba + abajo]
        direccion, largo = (1, 0, 0), (x1 - x0) + 2.0
    aristas = [Line(a_, b_) for a_, b_ in zip(pts, [*pts[1:], pts[0]], strict=True) if a_ != b_]
    return extrude(Face(Wire(aristas)), amount=largo, dir=direccion)


def _interseca_seguro(cuerpo: Any, herramienta: Any) -> Any:
    """`cuerpo & herramienta` con comprobación (OCCT a veces devuelve la herramienta o un sólido roto)."""
    try:
        r = cuerpo & herramienta
    except Exception:
        return cuerpo
    bb, br = cuerpo.bounding_box(), r.bounding_box()
    cabe = all(
        getattr(br.min, k) >= getattr(bb.min, k) - 0.05 and getattr(br.max, k) <= getattr(bb.max, k) + 0.05
        for k in "XYZ"
    )
    if cabe and r.is_valid and 0.2 * cuerpo.volume < r.volume <= cuerpo.volume * 1.001:
        return r
    return cuerpo


def extruir_contorno(
    ext: Sequence[Punto],
    huecos: Sequence[Sequence[Punto]],
    ancho_mm: float,
    *,
    radio: float = 0.0,
    esquina_deg: float = 32.0,
    z_centro: float = 0.0,
    eje: str = "pca",
    planta: Sequence[tuple[float, float]] | None = None,
    planta_eje: str = "x",
) -> Any:
    """Sólido del contorno (plano XY) extruido `ancho_mm` en Z, centrado en `z_centro`. Con `radio` > 0 se
    intersecta con un prisma de sección redondeada alineado con el eje mayor de la pieza."""
    cara = cara_con_huecos(ext, huecos, esquina_deg)
    cuerpo = Pos(0, 0, z_centro) * extrude(cara, amount=ancho_mm / 2, both=True)
    if planta:
        cuerpo = _interseca_seguro(cuerpo, prisma_planta(ext, planta, planta_eje, z_centro))
    if radio > 0:
        try:
            redondo = cuerpo & prisma_redondeado(ext, ancho_mm, radio, z_centro, eje)
        except Exception:
            return cuerpo
        # Comprobación: el resultado debe caber en el cuerpo (OCCT a veces devuelve la herramienta).
        bb, br = cuerpo.bounding_box(), redondo.bounding_box()
        cabe = (
            br.min.X >= bb.min.X - 0.05
            and br.max.X <= bb.max.X + 0.05
            and br.min.Y >= bb.min.Y - 0.05
            and br.max.Y <= bb.max.Y + 0.05
            and br.min.Z >= bb.min.Z - 0.05
            and br.max.Z <= bb.max.Z + 0.05
        )
        if cabe and redondo.is_valid and 0.5 * cuerpo.volume < redondo.volume <= cuerpo.volume * 1.001:
            return redondo
    return cuerpo


def mm_desde_foto(pts_px: Sequence[Punto], mm_por_px: float, origen_px: Punto) -> list[Punto]:
    return sil.a_mm(pts_px, mm_por_px, origen_px)


__all__ = ["Plane", "aristas_desde_poligono", "cara_con_huecos", "extruir_contorno", "mm_desde_foto"]
