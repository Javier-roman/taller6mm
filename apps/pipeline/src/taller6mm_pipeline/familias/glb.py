"""Escritor y lector mínimos de GLB (glTF 2.0 binario), deterministas y sin dependencias externas.

Convenciones (docs/05 §4): datos en mm, **escena en metros**; +X boca de cañón, +Y arriba, +Z izquierda del
tirador. El nodo `pieza` lleva la malla y cada anclaje es un nodo vacío `socket.<slotKey>` con su posición.
Sin fechas ni rutas en el archivo: los mismos datos dan los mismos bytes.
"""

from __future__ import annotations

import json
import struct
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from taller6mm_pipeline.familias.base import Socket
    from taller6mm_pipeline.familias.malla import Malla

MM_A_M = 0.001
_MAGIA = 0x46546C67  # "glTF"
_JSON = 0x4E4F534A
_BIN = 0x004E4942
_FLOAT, _UINT32, _ARRAY_BUFFER, _ELEMENT_ARRAY_BUFFER = 5126, 5125, 34962, 34963
GENERADOR = "taller6mm-pipeline familias"


def _relleno(datos: bytes, byte: bytes) -> bytes:
    return datos + byte * (-len(datos) % 4)


def _m(valor_mm: float) -> float:
    """mm → m, redondeado a la décima de micra y sin `-0.0`."""
    return round(valor_mm * MM_A_M, 7) + 0.0


def escribir_glb(malla: Malla, sockets: Sequence[Socket], metadatos: Mapping[str, Any], material: str) -> bytes:
    posiciones = (malla.vertices * MM_A_M).astype(np.float32)
    indices = malla.triangulos.astype(np.uint32)
    trozos = [posiciones.tobytes(), malla.normales.astype(np.float32).tobytes(), indices.tobytes()]
    vistas, desplazamiento = [], 0
    for trozo, destino in zip(trozos, (_ARRAY_BUFFER, _ARRAY_BUFFER, _ELEMENT_ARRAY_BUFFER), strict=True):
        vistas.append({"buffer": 0, "byteOffset": desplazamiento, "byteLength": len(trozo), "target": destino})
        desplazamiento += len(trozo)  # float32 y uint32: siempre múltiplo de 4
    n = len(posiciones)
    nodos: list[dict[str, Any]] = [{"name": "pieza", "mesh": 0, "extras": dict(metadatos)}]
    for s in sockets:
        nodos.append(
            {
                "name": s.nombre_nodo,
                "translation": [_m(v) for v in s.posicion_mm],
                "extras": {"interfaz": s.interfaz, **dict(s.extras)},
            }
        )
    doc = {
        "asset": {"version": "2.0", "generator": GENERADOR},
        "scene": 0,
        "scenes": [{"name": str(metadatos.get("id_variante", "pieza")), "nodes": list(range(len(nodos)))}],
        "nodes": nodos,
        "meshes": [{"name": "pieza", "primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2}]}],
        "materials": [
            {
                "name": material,
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.08, 0.08, 0.08, 1.0],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.6,
                },
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": _FLOAT,
                "count": n,
                "type": "VEC3",
                "min": [float(v) for v in posiciones.min(axis=0)],
                "max": [float(v) for v in posiciones.max(axis=0)],
            },
            {"bufferView": 1, "componentType": _FLOAT, "count": n, "type": "VEC3"},
            {"bufferView": 2, "componentType": _UINT32, "count": int(indices.size), "type": "SCALAR"},
        ],
        "bufferViews": vistas,
        "buffers": [{"byteLength": desplazamiento}],
    }
    doc["meshes"][0]["primitives"][0]["material"] = 0
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


def leer_glb(datos: bytes) -> tuple[dict[str, Any], bytes]:
    """Devuelve (documento glTF, bloque binario). Valida cabecera y longitudes."""
    magia, version, total = struct.unpack_from("<III", datos, 0)
    if magia != _MAGIA or version != 2 or total != len(datos):
        raise ValueError("no es un GLB 2.0 válido")
    largo_json, tipo = struct.unpack_from("<II", datos, 12)
    if tipo != _JSON:
        raise ValueError("falta el bloque JSON")
    doc = json.loads(datos[20 : 20 + largo_json].decode("utf-8"))
    pos = 20 + largo_json
    largo_bin, tipo = struct.unpack_from("<II", datos, pos)
    if tipo != _BIN:
        raise ValueError("falta el bloque BIN")
    return doc, datos[pos + 8 : pos + 8 + largo_bin]


def leer_posiciones_m(datos: bytes) -> np.ndarray:
    """Posiciones de la malla (Nx3, metros) de un GLB escrito por `escribir_glb`."""
    doc, binario = leer_glb(datos)
    acc = doc["accessors"][doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    vista = doc["bufferViews"][acc["bufferView"]]
    return np.frombuffer(binario, dtype="<f4", count=acc["count"] * 3, offset=vista["byteOffset"]).reshape(-1, 3)
