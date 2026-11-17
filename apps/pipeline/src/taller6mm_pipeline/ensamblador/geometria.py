"""Transformaciones rígidas en mm para el ensamblador (numpy, sin E/S).

Una transformación es una matriz 4x4 homogénea (columna = vector). Los ejes son los canónicos del proyecto:
+X boca de cañón, +Y arriba, +Z izquierda del tirador (docs/05 §4).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

Matriz = NDArray[np.float64]
Vec = tuple[float, float, float]

IDENTIDAD: Matriz = np.eye(4)
# Giro de 180° alrededor de X local: lleva +Z (normal) a -Z y +Y a -Y. Es lo que enfrenta dos sockets.
VOLTEO_X: Matriz = np.diag([1.0, -1.0, -1.0, 1.0])


def trasladar(x: float, y: float, z: float) -> Matriz:
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def marco_socket(posicion: Vec, normal: Vec, tangente: Vec) -> Matriz:
    """Marco local de un socket: X = tangente, Y = Z x X, Z = normal (la misma convención que `Socket.ejes`)."""
    z = np.asarray(normal, dtype=np.float64)
    x = np.asarray(tangente, dtype=np.float64)
    y = np.cross(z, x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, posicion
    return m


def aplicar(m: Matriz, puntos: NDArray[np.float64]) -> NDArray[np.float64]:
    """Transforma puntos (Nx3 o un único vector)."""
    p = np.asarray(puntos, dtype=np.float64)
    return p @ m[:3, :3].T + m[:3, 3]


def rotar(m: Matriz, vector: Vec) -> NDArray[np.float64]:
    return m[:3, :3] @ np.asarray(vector, dtype=np.float64)


def cuaternion(m: Matriz) -> tuple[float, float, float, float]:
    """Rotación de `m` como cuaternión glTF (x, y, z, w) con w >= 0 y sin `-0.0`."""
    r = m[:3, :3]
    traza = float(np.trace(r))
    if traza > 0:
        s = math.sqrt(traza + 1.0) * 2
        q = ((r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, s / 4)
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = math.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        q = (s / 4, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s, (r[2, 1] - r[1, 2]) / s)
    elif r[1, 1] > r[2, 2]:
        s = math.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        q = ((r[0, 1] + r[1, 0]) / s, s / 4, (r[1, 2] + r[2, 1]) / s, (r[0, 2] - r[2, 0]) / s)
    else:
        s = math.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        q = ((r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, s / 4, (r[1, 0] - r[0, 1]) / s)
    signo = -1.0 if q[3] < -1e-12 else 1.0
    return tuple(round(signo * v, 7) + 0.0 for v in q)  # type: ignore[return-value]


def redondear(m: Matriz, decimales: int = 4) -> list[list[float]]:
    """Matriz como listas de float (sin `-0.0`) para el informe JSON."""
    return [[round(float(v), decimales) + 0.0 for v in fila] for fila in m]


def es_rigida(m: Matriz, tol: float = 1e-6) -> bool:
    r = m[:3, :3]
    return bool(np.allclose(r @ r.T, np.eye(3), atol=tol) and math.isclose(float(np.linalg.det(r)), 1.0, abs_tol=tol))
