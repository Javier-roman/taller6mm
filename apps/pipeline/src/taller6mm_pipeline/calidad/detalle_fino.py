"""N2 de la escalera: métricas de detalle geométrico fino de una malla (numpy puro, deterministas, sin E/S).

Miden lo que un cubito con filetes todavía no tiene: roscas y estrías (periodicidad axial), tornillos y rebajes
(rasgos pequeños), líneas de partición y escalones (discontinuidades del perfil), chaflanes con radio real (aristas
vivas ≤ 25 %, transiciones finas) y relieve de agarre (área en triángulos finos). Reutiliza el soldado y el cálculo de
diedros de `metricas`.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from taller6mm_pipeline.calidad import metricas

FINO_MM = 1.5  # un triángulo con todas las aristas ≤ 1,5 mm es detalle fino (radios de filete, rebajes, estrías)
PASO_PERFIL_MM = 0.5
RASGO_MIN_MM, RASGO_MAX_MM = 1.5, 15.0  # tamaño de un tornillo, un rebaje o un agujero pequeño
LAG_MIN_MM, LAG_MAX_MM = 1.0, 14.0  # paso de rosca o de estría


def _perfil_axial(v: NDArray[np.float64], t: NDArray[np.int64], eje: int) -> NDArray[np.float64]:
    """Área de superficie por rodaja de 0,5 mm a lo largo del eje largo (proxy del perímetro de cada sección).

    Un triángulo largo reparte su área por igual a lo largo de su extensión axial: así un tubo teselado en pocos
    triángulos largos no concentra toda su área en un solo bin.
    """
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2.0
    xs = np.stack([a[:, eje], b[:, eje], c[:, eje]]) - v[:, eje].min()
    lo, hi = xs.min(axis=0), xs.max(axis=0)
    k = np.clip(np.ceil((hi - lo) / PASO_PERFIL_MM).astype(int) + 1, 1, 400)
    tri = np.repeat(np.arange(len(t)), k)
    inicio = np.repeat(np.cumsum(k) - k, k)
    f = (np.arange(len(tri)) - inicio + 0.5) / k[tri]
    x = lo[tri] + f * (hi[tri] - lo[tri])
    n = int(xs.max() / PASO_PERFIL_MM) + 1
    return np.bincount(np.minimum((x / PASO_PERFIL_MM).astype(int), n - 1), weights=area[tri] / k[tri], minlength=n)


def periodicidad(perfil: NDArray[np.float64]) -> tuple[float, float]:
    """(fuerza 0-1, paso en mm) de la repetición axial: pico de autocorrelación del perfil sin su tendencia."""
    if len(perfil) < 40:
        return 0.0, 0.0
    ventana = 17
    tendencia = np.convolve(perfil, np.ones(ventana) / ventana, mode="same")
    r = (perfil - tendencia)[ventana:-ventana]
    if r.std() < 1e-9 or len(r) < 30:
        return 0.0, 0.0
    r = r - r.mean()
    ac = np.correlate(r, r, mode="full")[len(r) - 1 :]
    ac = ac / max(ac[0], 1e-12)
    lo, hi = int(LAG_MIN_MM / PASO_PERFIL_MM), min(int(LAG_MAX_MM / PASO_PERFIL_MM), len(ac) - 1)
    if hi <= lo:
        return 0.0, 0.0
    k = int(np.argmax(ac[lo : hi + 1])) + lo
    return float(max(ac[k], 0.0)), k * PASO_PERFIL_MM


def escalones(perfil: NDArray[np.float64]) -> float:
    """Saltos bruscos del perfil axial por cada 100 mm (partiduras, ranuras, resaltes)."""
    if len(perfil) < 10:
        return 0.0
    d = np.abs(np.diff(perfil))
    corte = max(float(perfil.mean()) * 0.3, 1e-9)
    return float((d > corte).sum()) / (len(perfil) * PASO_PERFIL_MM / 100.0)


def rasgos_pequenos(v: NDArray[np.float64], t: NDArray[np.int64], fino: NDArray[np.bool_]) -> int:
    """Grupos de triángulos finos conectados cuyo tamaño es el de un tornillo, un rebaje o un agujero pequeño."""
    idx = np.nonzero(fino)[0]
    if len(idx) == 0:
        return 0
    padre = {int(i): int(i) for i in np.unique(t[idx])}

    def raiz(x: int) -> int:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for a, b, c in t[idx].tolist():
        ra = raiz(a)
        padre[raiz(b)] = ra
        padre[raiz(c)] = ra
    grupos: dict[int, list[int]] = {}
    for p in padre:
        grupos.setdefault(raiz(p), []).append(p)
    n = 0
    for vs in grupos.values():
        diag = float(np.linalg.norm(v[vs].max(axis=0) - v[vs].min(axis=0)))
        n += RASGO_MIN_MM <= diag <= RASGO_MAX_MM
    return n


def medir(vertices: NDArray[np.float64], triangulos: NDArray[np.int64]) -> dict[str, Any]:
    """Métricas de N2 de una pieza (vértices en mm)."""
    v, t = metricas.soldar(vertices, triangulos)
    _, area = metricas._caras(v, t)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    lado_max = np.maximum.reduce(
        [np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)]
    )
    fino = lado_max <= FINO_MM
    area_cm2 = float(area.sum()) / 100.0
    normales, _ = metricas._caras(v, t)
    angulos, largos = metricas._diedros(v, t, normales)
    transicion = (angulos >= metricas.UMBRAL_TRANSICION_MIN_GRADOS) & (angulos < metricas.UMBRAL_VIVA_GRADOS)
    finas = transicion & (largos <= FINO_MM)
    d = metricas.detalle(v, t)
    eje = int(np.argmax(v.max(axis=0) - v.min(axis=0)))
    perfil = _perfil_axial(v, t, eje)
    fuerza, paso = periodicidad(perfil)
    return {
        "area_fina_frac": round(float(area[fino].sum() / max(area.sum(), 1e-9)), 4),
        "transiciones_finas_cm2": round(float(finas.sum()) / max(area_cm2, 1e-9), 3),
        "viva_frac": round(d["viva_frac"], 4),
        "periodicidad": round(fuerza, 4),
        "paso_mm": round(paso, 2),
        "escalones_100mm": round(escalones(perfil), 3),
        "rasgos_pequenos": rasgos_pequenos(v, t, fino),
    }
