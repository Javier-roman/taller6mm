"""Teselado determinista de un sólido de build123d a una malla de triángulos (numpy).

OCCT tesela cara a cara: los vértices no se comparten entre caras del B-rep, así que las normales por vértice
salen suaves dentro de cada cara (un cilindro) y con arista viva entre caras (un chaflán). Las coordenadas se
redondean a la décima de micra para que el mismo sólido dé siempre los mismos bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

DECIMALES_MM = 4


@dataclass(frozen=True, slots=True)
class Malla:
    """Malla en mm: `vertices` (Nx3 float64), `normales` (Nx3 float32, unitarias) y `triangulos` (Mx3 uint32)."""

    vertices: NDArray[np.float64]
    normales: NDArray[np.float32]
    triangulos: NDArray[np.uint32]

    @property
    def caja_mm(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Caja envolvente: (mínimos, máximos) en mm."""
        mn, mx = self.vertices.min(axis=0), self.vertices.max(axis=0)
        return (float(mn[0]), float(mn[1]), float(mn[2])), (float(mx[0]), float(mx[1]), float(mx[2]))

    @property
    def dimensiones_mm(self) -> tuple[float, float, float]:
        (x0, y0, z0), (x1, y1, z1) = self.caja_mm
        return (round(x1 - x0, DECIMALES_MM), round(y1 - y0, DECIMALES_MM), round(z1 - z0, DECIMALES_MM))

    @property
    def volumen_mm3(self) -> float:
        """Volumen con signo (teorema de la divergencia): positivo si las caras miran hacia fuera."""
        a, b, c = (self.vertices[self.triangulos[:, i]] for i in range(3))
        return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)

    def aristas_abiertas(self) -> int:
        """Aristas que no están compartidas por exactamente dos triángulos de sentido opuesto (0 = malla cerrada).

        Los vértices se sueldan por posición, porque OCCT no los comparte entre caras del B-rep.
        """
        _, soldado = np.unique(np.round(self.vertices, 3), axis=0, return_inverse=True)
        t = soldado.reshape(-1)[self.triangulos.astype(np.int64)]
        t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 2] != t[:, 0])]
        origen = np.concatenate([t[:, 0], t[:, 1], t[:, 2]])
        destino = np.concatenate([t[:, 1], t[:, 2], t[:, 0]])
        n = int(soldado.max()) + 1
        dirigidas, veces = np.unique(origen * n + destino, return_counts=True)
        opuestas = (dirigidas % n) * n + dirigidas // n
        return int((veces != 1).sum() + (~np.isin(opuestas, dirigidas)).sum())

    def normales_hacia_fuera(self) -> float:
        """Fracción de triángulos cuya normal de cara coincide con las normales de sus vértices (1.0 = todas)."""
        a, b, c = (self.vertices[self.triangulos[:, i]] for i in range(3))
        cara = np.cross(b - a, c - a)
        media = self.normales[self.triangulos].astype(np.float64).sum(axis=1)
        return float((np.einsum("ij,ij->i", cara, media) > 0).mean())


def teselar(solido: Any, tolerancia_mm: float, tolerancia_angular: float) -> Malla:
    """Tesela un `Shape` de build123d. Descarta triángulos degenerados y calcula normales por vértice."""
    vs, ts = solido.tessellate(tolerancia_mm, tolerancia_angular)
    vertices = np.round(np.array([(v.X, v.Y, v.Z) for v in vs], dtype=np.float64), DECIMALES_MM) + 0.0
    triangulos = np.array(ts, dtype=np.uint32).reshape(-1, 3)
    a, b, c = (vertices[triangulos[:, i]] for i in range(3))
    caras = np.cross(b - a, c - a)  # normal ponderada por área
    validos = np.linalg.norm(caras, axis=1) > 1e-9
    triangulos, caras = triangulos[validos], caras[validos]
    suma = np.zeros_like(vertices)
    for i in range(3):
        np.add.at(suma, triangulos[:, i], caras)
    norma = np.linalg.norm(suma, axis=1, keepdims=True)
    normales = np.where(norma > 1e-12, suma / np.maximum(norma, 1e-12), (0.0, 1.0, 0.0))
    return Malla(vertices, np.round(normales, 5).astype(np.float32) + np.float32(0.0), triangulos)
