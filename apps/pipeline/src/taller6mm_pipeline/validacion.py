"""Validación de fidelidad T2 (docs/05): IoU de silueta por vista y error de cotas.

Criterio T2: IoU >= 0,95 en al menos 2 vistas y cotas clave con error <= 1 % o <= 2 mm (basta una de las
dos). Los límites son inclusivos. Una cota sin dato (de referencia o medida) no se da por buena.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

IOU_MINIMO = 0.95
VISTAS_MINIMAS = 2
TOLERANCIA_MM = 2.0
TOLERANCIA_PCT = 1.0
_EPS = 1e-9  # el 1 % de 777 mm en coma flotante no es exacto; el límite debe contar como aprobado

Mascara = NDArray[np.bool_]


class Estado(StrEnum):
    APROBADO = "aprobado"
    SUSPENDIDO = "suspendido"
    SIN_DATO = "sin_dato"


def binarizar(imagen: NDArray[np.generic], umbral: float = 128, *, invertir: bool = False) -> Mascara:
    """Binariza una imagen (gris HxW o color HxWxC) por umbral.

    Primer plano = píxeles con valor > `umbral` (media de los 3 primeros canales si es color). Con
    `invertir=True`, primer plano = valor <= `umbral` (objeto oscuro sobre fondo claro).
    """
    datos = np.asarray(imagen, dtype=np.float64)
    if datos.ndim == 3:
        datos = datos[..., :3].mean(axis=2)
    elif datos.ndim != 2:
        raise ValueError("la imagen debe ser HxW o HxWxC")
    return datos <= umbral if invertir else datos > umbral


def iou_silueta(a: Mascara, b: Mascara) -> float:
    """Intersección sobre unión de dos máscaras binarias del mismo tamaño."""
    ma, mb = np.asarray(a, dtype=bool), np.asarray(b, dtype=bool)
    if ma.shape != mb.shape:
        raise ValueError(f"las máscaras deben tener el mismo tamaño ({ma.shape} frente a {mb.shape})")
    union = int(np.logical_or(ma, mb).sum())
    if union == 0:
        raise ValueError("ambas máscaras están vacías: no hay silueta que comparar")
    return int(np.logical_and(ma, mb).sum()) / union


@dataclass(frozen=True, slots=True)
class ResultadoVista:
    nombre: str
    iou: float
    estado: Estado


@dataclass(frozen=True, slots=True)
class ResultadoCota:
    clave: str
    referencia_mm: float | None
    medido_mm: float | None
    error_mm: float | None
    error_pct: float | None
    estado: Estado


@dataclass(frozen=True, slots=True)
class ResultadoValidacion:
    vistas: tuple[ResultadoVista, ...]
    cotas: tuple[ResultadoCota, ...]
    aprobado_t2: bool


def comparar_cota(clave: str, referencia_mm: float | None, medido_mm: float | None) -> ResultadoCota:
    """Compara una cota medida en el modelo con la de referencia (error absoluto y relativo a la referencia)."""
    if referencia_mm is None or medido_mm is None:
        return ResultadoCota(clave, referencia_mm, medido_mm, None, None, Estado.SIN_DATO)
    if referencia_mm <= 0:
        raise ValueError(f"cota {clave!r}: la referencia debe ser positiva")
    error_mm = abs(medido_mm - referencia_mm)
    error_pct = error_mm / referencia_mm * 100
    ok = error_mm <= TOLERANCIA_MM + _EPS or error_pct <= TOLERANCIA_PCT + _EPS
    estado = Estado.APROBADO if ok else Estado.SUSPENDIDO
    return ResultadoCota(clave, referencia_mm, medido_mm, error_mm, error_pct, estado)


def validar(
    siluetas: Mapping[str, tuple[Mascara, Mascara]],
    cotas: Mapping[str, tuple[float | None, float | None]],
) -> ResultadoValidacion:
    """Valida un modelo: `siluetas` = {vista: (referencia, modelo)}, `cotas` = {clave: (referencia, medido)}.

    T2 exige al menos `VISTAS_MINIMAS` vistas con IoU >= `IOU_MINIMO`, y todas las cotas aprobadas
    (ninguna suspendida ni sin dato).
    """
    vistas = []
    for nombre, (ref, mod) in siluetas.items():
        iou = iou_silueta(ref, mod)
        vistas.append(ResultadoVista(nombre, iou, Estado.APROBADO if iou >= IOU_MINIMO else Estado.SUSPENDIDO))
    resultados = tuple(comparar_cota(k, r, m) for k, (r, m) in cotas.items())
    vistas_ok = sum(v.estado is Estado.APROBADO for v in vistas)
    cotas_ok = all(c.estado is Estado.APROBADO for c in resultados)
    return ResultadoValidacion(tuple(vistas), resultados, vistas_ok >= VISTAS_MINIMAS and cotas_ok)
