"""Solapes y huecos entre mallas (mm), con numpy y sin dependencias nuevas.

- Solape: se muestrean puntos de la superficie de A (reparto por área, semilla fija) y se sondea 0,5 mm hacia dentro
  de A siguiendo su normal: si esa sonda está dentro de B (paridad de rayos, Möller-Trumbore) hay solape. Las caras
  que se tocan no cuentan. La profundidad es la mayor sonda (0,5 a 16 mm) que sigue dentro de B.
- Hueco: distancia mínima entre las superficies de dos piezas que deberían tocarse, medida en una ventana alrededor
  del socket con muestreo denso. La precisión es de decenas de micras a ~1 mm: se informa en `precision_mm`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Puntos = NDArray[np.float64]
PENETRACION_MIN_MM = 0.5
MUESTRAS = 5000
DIRECCION_RAYO = np.array([1.0, 0.0137, 0.0071]) / np.linalg.norm([1.0, 0.0137, 0.0071])


@dataclass(frozen=True, slots=True)
class Malla3D:
    vertices: Puntos
    triangulos: NDArray[np.uint32]

    @property
    def caja(self) -> tuple[Puntos, Puntos]:
        return self.vertices.min(axis=0), self.vertices.max(axis=0)


@dataclass(frozen=True, slots=True)
class Solape:
    puntos_a_en_b: int
    puntos_b_en_a: int
    muestras: int
    profundidad_max_mm: float
    caja_mm: tuple[tuple[float, float, float], tuple[float, float, float]]

    @property
    def hay(self) -> bool:
        return self.puntos_a_en_b + self.puntos_b_en_a > 0


def muestrear(
    malla: Malla3D, n: int = MUESTRAS, semilla: int = 7, ventana: tuple[Puntos, float] | None = None
) -> tuple[Puntos, Puntos]:
    """Puntos de la superficie y la normal (hacia fuera) de su triángulo, deterministas.

    Con `ventana=(centro, radio)` solo salen puntos a menos de `radio` del centro (se eligen los triángulos cuya caja
    toca la ventana, porque un triángulo grande puede tener el centroide lejos).
    """
    tri = malla.vertices[malla.triangulos]
    if ventana is not None:
        centro, radio = ventana
        cerca = np.all(tri.max(axis=1) >= centro - radio, axis=1) & np.all(tri.min(axis=1) <= centro + radio, axis=1)
        tri = tri[cerca]
    if len(tri) == 0:
        return np.empty((0, 3)), np.empty((0, 3))
    cruz = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = np.linalg.norm(cruz, axis=1) / 2
    if area.sum() <= 0:
        return np.empty((0, 3)), np.empty((0, 3))
    rng = np.random.default_rng(semilla)
    elegidos = rng.choice(len(tri), size=n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n)
    voltear = u + v > 1
    u, v = np.where(voltear, 1 - u, u), np.where(voltear, 1 - v, v)
    t = tri[elegidos]
    puntos = t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + v[:, None] * (t[:, 2] - t[:, 0])
    normales = cruz[elegidos] / np.maximum(np.linalg.norm(cruz[elegidos], axis=1, keepdims=True), 1e-12)
    if ventana is not None:
        cerca_p = np.linalg.norm(puntos - ventana[0], axis=1) <= ventana[1]
        puntos, normales = puntos[cerca_p], normales[cerca_p]
    return puntos, normales


def dentro_de(puntos: Puntos, malla: Malla3D) -> NDArray[np.bool_]:
    """Paridad de rayos (+X ligeramente inclinado) de cada punto contra la malla."""
    res = np.zeros(len(puntos), dtype=bool)
    if len(puntos) == 0:
        return res
    tri = malla.vertices[malla.triangulos]
    margen = (
        0.02 * (float(puntos[:, 0].max() - puntos[:, 0].min()) + float(tri[:, :, 0].max() - puntos[:, 0].min())) + 1e-3
    )
    lo, hi = puntos.min(axis=0), puntos.max(axis=0)
    tmin, tmax = tri.min(axis=1), tri.max(axis=1)
    util = (
        (tmax[:, 0] >= lo[0] - 1e-6)
        & (tmax[:, 1] >= lo[1] - margen)
        & (tmin[:, 1] <= hi[1] + margen)
        & (tmax[:, 2] >= lo[2] - margen)
        & (tmin[:, 2] <= hi[2] + margen)
    )
    tri = tri[util]
    if len(tri) == 0:
        return res
    d = DIRECCION_RAYO
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    h = np.cross(d, e2)
    a = np.einsum("ij,ij->i", e1, h)
    valido = np.abs(a) > 1e-12
    f = np.where(valido, 1.0 / np.where(valido, a, 1.0), 0.0)
    trozo = max(1, int(1_500_000 // len(tri)))
    for i in range(0, len(puntos), trozo):
        p = puntos[i : i + trozo]
        s = p[:, None, :] - tri[None, :, 0, :]
        u = f * np.einsum("cmj,mj->cm", s, h)
        q = np.cross(s, e1[None])
        v = f * np.einsum("j,cmj->cm", d, q)
        t = f * np.einsum("mj,cmj->cm", e2, q)
        golpe = valido & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
        res[i : i + trozo] = golpe.sum(axis=1) % 2 == 1
    return res


def distancia_min(a: Puntos, b: Puntos) -> float:
    """Distancia mínima entre dos nubes de puntos (árbol k-d de scipy, que ya trae build123d; si no, por trozos)."""
    if len(a) == 0 or len(b) == 0:
        return float("inf")
    try:
        from scipy.spatial import cKDTree
    except ImportError:  # pragma: no cover - scipy llega con build123d
        cKDTree = None  # noqa: N806
    if cKDTree is not None:
        return float(cKDTree(b).query(a, k=1)[0].min())
    mejor = float("inf")
    trozo = max(1, int(2_000_000 // len(b)))
    for i in range(0, len(a), trozo):
        d = np.linalg.norm(a[i : i + trozo, None, :] - b[None, :, :], axis=2)
        mejor = min(mejor, float(d.min()))
    return mejor


def _cajas_se_tocan(a: Malla3D, b: Malla3D, margen: float = 0.0) -> bool:
    a0, a1 = a.caja
    b0, b1 = b.caja
    return bool(np.all(a0 <= b1 + margen) and np.all(b0 <= a1 + margen))


PROFUNDIDADES_MM = (PENETRACION_MIN_MM, 1.0, 2.0, 4.0, 8.0, 16.0)


def _dentro_real(puntos: Puntos, normales: Puntos, otra: Malla3D) -> tuple[Puntos, float]:
    """Puntos de A cuyo interior (a `PENETRACION_MIN_MM` bajo la superficie) está dentro de `otra`, y su profundidad.

    Se sondea hacia dentro de A siguiendo su normal: dos caras que se tocan (el interior de A queda fuera de B) no
    cuentan, y la profundidad es la mayor sonda que sigue dentro de B (resolución de la lista de profundidades).
    """
    if len(puntos) == 0:
        return puntos, 0.0
    o0, o1 = otra.caja
    sondas = puntos - normales * PENETRACION_MIN_MM
    en_caja = np.all((sondas >= o0 - 1e-6) & (sondas <= o1 + 1e-6), axis=1)
    idx = np.flatnonzero(en_caja)
    if len(idx) == 0:
        return puntos[:0], 0.0
    dentro = dentro_de(sondas[idx], otra)
    elegidos = idx[dentro]
    if len(elegidos) == 0:
        return puntos[:0], 0.0
    profundidad = PENETRACION_MIN_MM
    for d in PROFUNDIDADES_MM[1:]:
        ok = dentro_de(puntos[elegidos] - normales[elegidos] * d, otra)
        if not ok.any():
            break
        profundidad = d
    return puntos[elegidos], profundidad


def solape(a: Malla3D, b: Malla3D) -> Solape | None:
    """Solape entre dos mallas, o `None` si ni sus cajas se tocan."""
    if not _cajas_se_tocan(a, b):
        return None
    (pa_, na), (pb_, nb) = muestrear(a, semilla=11), muestrear(b, semilla=13)
    en_b, prof_a = _dentro_real(pa_, na, b)
    en_a, prof_b = _dentro_real(pb_, nb, a)
    todos = np.vstack([en_b, en_a]) if len(en_b) + len(en_a) else np.empty((0, 3))
    if len(todos):
        caja = (
            tuple(round(float(v), 2) for v in todos.min(axis=0)),
            tuple(round(float(v), 2) for v in todos.max(axis=0)),
        )
    else:
        caja = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    return Solape(len(en_b), len(en_a), len(pa_) + len(pb_), max(prof_a, prof_b), caja)  # type: ignore[arg-type]


def holgura(a: Malla3D, b: Malla3D, centro: Puntos, radio: float = 30.0) -> float:
    """Distancia mínima entre las superficies de A y B en una ventana de `radio` mm alrededor de `centro`."""
    c = np.asarray(centro, dtype=np.float64)
    pa, _ = muestrear(a, 40000, 21, (c, radio))  # denso: una cara plana grande da pocos puntos con 6000
    pb, _ = muestrear(b, 40000, 23, (c, radio))
    return distancia_min(pa, pb)
