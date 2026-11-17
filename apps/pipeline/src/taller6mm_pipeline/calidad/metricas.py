"""Métricas de malla de la puerta de calidad: numpy puro, deterministas (semilla fija) y sin E/S.

Todas trabajan sobre `vertices` (Nx3, mm) y `triangulos` (Mx3). Los vértices se sueldan por posición porque OCCT no
comparte los de caras distintas del B-rep.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

SEMILLA = 20261117
UMBRAL_TRANSICION_MIN_GRADOS = 4.0  # por debajo, dos caras vecinas son la misma superficie lisa
UMBRAL_VIVA_GRADOS = 60.0  # por encima, la arista es viva (sin filete)
PUNTOS_SILUETA = 400_000
RESOLUCION_SILUETA = 200


def soldar(
    vertices: NDArray[np.float64], triangulos: NDArray[np.int64]
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    únicos, inverso = np.unique(np.round(vertices, 3), axis=0, return_inverse=True)
    t = inverso.reshape(-1)[triangulos]
    ok = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 2] != t[:, 0])
    return únicos, t[ok]


def _caras(v: NDArray[np.float64], t: NDArray[np.int64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    cruz = np.cross(b - a, c - a)
    area = np.linalg.norm(cruz, axis=1) / 2.0
    return cruz / np.maximum(2.0 * area, 1e-12)[:, None], area


def volumen(vertices: NDArray[np.float64], triangulos: NDArray[np.int64]) -> float:
    a, b, c = (vertices[triangulos[:, i]] for i in range(3))
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def aristas_abiertas(v: NDArray[np.float64], t: NDArray[np.int64]) -> int:
    """Aristas no compartidas por exactamente dos triángulos de sentido opuesto (0 = cerrada). `v`,`t` ya soldados."""
    origen = np.concatenate([t[:, 0], t[:, 1], t[:, 2]])
    destino = np.concatenate([t[:, 1], t[:, 2], t[:, 0]])
    n = len(v)
    dirigidas, veces = np.unique(origen * n + destino, return_counts=True)
    opuestas = (dirigidas % n) * n + dirigidas // n
    return int((veces != 1).sum() + (~np.isin(opuestas, dirigidas)).sum())


def componentes(v: NDArray[np.float64], t: NDArray[np.int64]) -> int:
    padre = list(range(len(v)))

    def raiz(x: int) -> int:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for a, b, c in t.tolist():
        ra, rb, rc = raiz(a), raiz(b), raiz(c)
        padre[rb] = ra
        padre[rc] = ra
    return len({raiz(i) for i in np.unique(t)})


def _diedros(
    v: NDArray[np.float64], t: NDArray[np.int64], normales: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """(ángulo en grados, longitud en mm) de cada arista interior compartida por dos triángulos."""
    n = len(v)
    e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    fila = np.concatenate([np.arange(len(t))] * 3)
    clave = np.minimum(e[:, 0], e[:, 1]) * n + np.maximum(e[:, 0], e[:, 1])
    orden = np.argsort(clave, kind="stable")
    clave, fila, e = clave[orden], fila[orden], e[orden]
    iguales = clave[1:] == clave[:-1]
    i = np.nonzero(iguales)[0]
    cos = np.clip(np.einsum("ij,ij->i", normales[fila[i]], normales[fila[i + 1]]), -1.0, 1.0)
    largo = np.linalg.norm(v[e[i, 0]] - v[e[i, 1]], axis=1)
    return np.degrees(np.arccos(cos)), largo


def detalle(v: NDArray[np.float64], t: NDArray[np.int64]) -> dict[str, float]:
    normales, area = _caras(v, t)
    area_cm2 = float(area.sum()) / 100.0
    angulos, largos = _diedros(v, t, normales)
    transicion = (angulos >= UMBRAL_TRANSICION_MIN_GRADOS) & (angulos < UMBRAL_VIVA_GRADOS)
    viva = angulos >= UMBRAL_VIVA_GRADOS
    plano = angulos < UMBRAL_TRANSICION_MIN_GRADOS
    largo_total = float(largos[~plano].sum()) or 1.0
    return {
        "area_cm2": area_cm2,
        "orientaciones": float(len({tuple(x) for x in np.round(normales, 1).tolist()})),
        "transiciones_por_cm2": float(transicion.sum()) / max(area_cm2, 1e-9),
        "viva_frac": float(largos[viva].sum()) / largo_total,
        "aristas_vivas": float(viva.sum()),
    }


def _muestras(v: NDArray[np.float64], t: NDArray[np.int64], n: int) -> NDArray[np.float64]:
    _, area = _caras(v, t)
    rng = np.random.default_rng(SEMILLA)
    tri = rng.choice(len(t), size=n, p=area / area.sum())
    u, w = rng.random(n), rng.random(n)
    r = u + w > 1.0
    u, w = np.where(r, 1 - u, u), np.where(r, 1 - w, w)
    a, b, c = v[t[tri, 0]], v[t[tri, 1]], v[t[tri, 2]]
    return a + (b - a) * u[:, None] + (c - a) * w[:, None]


def silueta(v: NDArray[np.float64], t: NDArray[np.int64], puntos: NDArray[np.float64] | None = None) -> dict[str, Any]:
    """Relleno y complejidad de la silueta en las 3 vistas ortográficas (XY, XZ, ZY).

    `complejidad` = píxeles de borde / perímetro del rectángulo envolvente: 1,0 es un rectángulo; los huecos y muescas
    lo suben. `relleno` = píxeles ocupados / píxeles de la caja de la vista. `no_rectangular` (0 = un rectángulo
    puro, el perfil de un cubito) = max(1 - relleno, complejidad - 1): lo que la vista se aparta de una caja.
    """
    p = _muestras(v, t, PUNTOS_SILUETA) if puntos is None else puntos
    vistas: dict[str, dict[str, float]] = {}
    px = float((p.max(axis=0) - p.min(axis=0)).max()) / RESOLUCION_SILUETA  # mismo píxel en las 3 vistas
    for nombre, (i, j) in {"lateral_xy": (0, 1), "planta_xz": (0, 2), "frontal_zy": (2, 1)}.items():
        a, b = p[:, i], p[:, j]
        wa, wb = float(a.max() - a.min()), float(b.max() - b.min())
        px = max(px, 1e-6)
        na, nb = int(wa / px) + 1, int(wb / px) + 1
        ia = np.minimum(((a - a.min()) / px).astype(int), na - 1)
        ib = np.minimum(((b - b.min()) / px).astype(int), nb - 1)
        m = np.zeros((na, nb), dtype=bool)
        m[ia, ib] = True
        pad = np.pad(m, 1)
        vecinos = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
        borde = int((m & ~vecinos).sum())
        vistas[nombre] = {
            "relleno": float(m.sum()) / (na * nb),
            "complejidad": borde / max(2.0 * (na + nb), 1.0),
        }
        vistas[nombre]["no_rectangular"] = max(1.0 - vistas[nombre]["relleno"], vistas[nombre]["complejidad"] - 1.0)
    return {
        "vistas": vistas,
        "complejidad_media": float(np.mean([x["complejidad"] for x in vistas.values()])),
        "relleno_medio": float(np.mean([x["relleno"] for x in vistas.values()])),
        "no_rectangular_medio": float(np.mean([x["no_rectangular"] for x in vistas.values()])),
    }


def forma(vertices: NDArray[np.float64], triangulos: NDArray[np.int64]) -> dict[str, Any]:
    """Todas las métricas de malla de una pieza."""
    v, t = soldar(vertices, triangulos)
    lo, hi = v.min(axis=0), v.max(axis=0)
    dim = hi - lo
    caja = float(np.prod(np.maximum(dim, 1e-9)))
    _normales, area = _caras(v, t)
    centroide = (((v[t[:, 0]] + v[t[:, 1]] + v[t[:, 2]]) / 3.0) * area[:, None]).sum(axis=0) / max(area.sum(), 1e-12)
    d = detalle(v, t)
    return {
        "dimensiones_mm": [round(float(x), 3) for x in dim],
        "triangulos": len(t),
        "volumen_mm3": volumen(v, t),
        "relleno_caja": volumen(v, t) / caja,
        "aristas_abiertas": aristas_abiertas(v, t),
        "componentes": componentes(v, t),
        "asimetria": [round(float(x), 4) for x in np.abs(centroide - (lo + hi) / 2.0) / np.maximum(dim, 1e-9)],
        "eje_largo": "xyz"[int(np.argmax(dim))],
        **d,
        "silueta": silueta(v, t),
    }
