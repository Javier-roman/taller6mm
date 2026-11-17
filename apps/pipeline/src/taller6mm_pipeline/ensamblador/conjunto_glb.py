"""GLB único del conjunto: una malla por pieza (ya en su sitio, escena en metros) y un nodo vacío por montaje.

Determinista (sin fechas ni rutas). Las piezas reales llevan el material de su familia y los marcadores visuales de
piezas sin malla llevan un material naranja translúcido, para que nadie los confunda con geometría de verdad.
"""

from __future__ import annotations

import json
import struct
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from taller6mm_pipeline.familias.glb import GENERADOR, MM_A_M

_MAGIA, _JSON, _BIN = 0x46546C67, 0x4E4F534A, 0x004E4942
_FLOAT, _UINT32, _ARRAY, _ELEMENTOS = 5126, 5125, 34962, 34963

MATERIALES: dict[str, dict[str, Any]] = {
    "mat.anodizado_negro": {"baseColorFactor": [0.08, 0.08, 0.09, 1.0], "metallicFactor": 0.8, "roughnessFactor": 0.4},
    "mat.polimero_negro": {"baseColorFactor": [0.05, 0.05, 0.055, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.65},
    "mat.marcador": {"baseColorFactor": [0.95, 0.45, 0.1, 0.55], "metallicFactor": 0.0, "roughnessFactor": 0.8},
}


@dataclass(frozen=True, slots=True)
class NodoPieza:
    nombre: str
    vertices_mm: NDArray[np.float64]
    triangulos: NDArray[np.uint32]
    material: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NodoVacio:
    nombre: str
    posicion_mm: tuple[float, float, float]
    rotacion: tuple[float, float, float, float]
    extras: dict[str, Any] = field(default_factory=dict)


def _relleno(datos: bytes, byte: bytes) -> bytes:
    return datos + byte * (-len(datos) % 4)


def _normales(v: NDArray[np.float64], t: NDArray[np.uint32]) -> NDArray[np.float32]:
    a, b, c = (v[t[:, i]] for i in range(3))
    caras = np.cross(b - a, c - a)
    suma = np.zeros_like(v)
    for i in range(3):
        np.add.at(suma, t[:, i], caras)
    norma = np.linalg.norm(suma, axis=1, keepdims=True)
    n = np.where(norma > 1e-12, suma / np.maximum(norma, 1e-12), (0.0, 1.0, 0.0))
    return (np.round(n, 5) + 0.0).astype(np.float32)


def escribir_conjunto(piezas: Sequence[NodoPieza], vacios: Sequence[NodoVacio], extras_raiz: dict[str, Any]) -> bytes:
    trozos: list[bytes] = []
    vistas: list[dict[str, Any]] = []
    accesores: list[dict[str, Any]] = []
    mallas: list[dict[str, Any]] = []
    nodos: list[dict[str, Any]] = []
    nombres_mat = sorted({p.material for p in piezas})
    indice_mat = {n: i for i, n in enumerate(nombres_mat)}
    desplazamiento = 0

    def añadir(datos: bytes, destino: int) -> int:
        nonlocal desplazamiento
        trozos.append(datos)
        vistas.append({"buffer": 0, "byteOffset": desplazamiento, "byteLength": len(datos), "target": destino})
        desplazamiento += len(datos)
        return len(vistas) - 1

    for i, p in enumerate(piezas):
        pos = (p.vertices_mm * MM_A_M).astype(np.float32)
        idx = p.triangulos.astype(np.uint32)
        vp = añadir(pos.tobytes(), _ARRAY)
        vn = añadir(_normales(p.vertices_mm, p.triangulos).tobytes(), _ARRAY)
        vi = añadir(idx.tobytes(), _ELEMENTOS)
        base = len(accesores)
        accesores += [
            {
                "bufferView": vp,
                "componentType": _FLOAT,
                "count": len(pos),
                "type": "VEC3",
                "min": [float(x) for x in pos.min(axis=0)],
                "max": [float(x) for x in pos.max(axis=0)],
            },
            {"bufferView": vn, "componentType": _FLOAT, "count": len(pos), "type": "VEC3"},
            {"bufferView": vi, "componentType": _UINT32, "count": int(idx.size), "type": "SCALAR"},
        ]
        mallas.append(
            {
                "name": p.nombre,
                "primitives": [
                    {
                        "attributes": {"POSITION": base, "NORMAL": base + 1},
                        "indices": base + 2,
                        "material": indice_mat[p.material],
                    }
                ],
            }
        )
        nodos.append({"name": p.nombre, "mesh": i, "extras": dict(p.extras)})
    for v in vacios:
        nodos.append(
            {
                "name": v.nombre,
                "translation": [round(c * MM_A_M, 7) + 0.0 for c in v.posicion_mm],
                "rotation": list(v.rotacion),
                "extras": dict(v.extras),
            }
        )
    materiales = []
    for n in nombres_mat:
        m: dict[str, Any] = {"name": n, "pbrMetallicRoughness": MATERIALES.get(n, MATERIALES["mat.anodizado_negro"])}
        if n == "mat.marcador":
            m["alphaMode"] = "BLEND"
        materiales.append(m)
    raiz = {"name": "build", "children": list(range(len(nodos))), "extras": extras_raiz}
    nodos.append(raiz)
    doc = {
        "asset": {"version": "2.0", "generator": GENERADOR + " ensamblador"},
        "scene": 0,
        "scenes": [{"name": str(extras_raiz.get("id", "build")), "nodes": [len(nodos) - 1]}],
        "nodes": nodos,
        "meshes": mallas,
        "materials": materiales,
        "accessors": accesores,
        "bufferViews": vistas,
        "buffers": [{"byteLength": desplazamiento}],
    }
    texto = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    json_b = _relleno(texto.encode("utf-8"), b" ")
    bin_b = _relleno(b"".join(trozos), b"\x00")
    total = 12 + 8 + len(json_b) + 8 + len(bin_b)
    return b"".join(
        [
            struct.pack("<III", _MAGIA, 2, total),
            struct.pack("<II", len(json_b), _JSON),
            json_b,
            struct.pack("<II", len(bin_b), _BIN),
            bin_b,
        ]
    )
