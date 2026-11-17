"""Pieza lista para ensamblar: malla en mm, sockets y metadatos, leídos de un GLB propio o de una `Pieza` sin malla.

Todas las piezas con malla entran por el GLB (`leer_pieza_glb`): así el ensamblador funciona igual con una pieza
recién generada, con una de la caché o con un GLB del kit. Una pieza sin malla (T0 sin geometría) conserva sus
metadatos y entra como hueco: nunca se le inventan cotas.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from taller6mm_pipeline.familias import FAMILIAS
from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.oleada1 import FAMILIAS_OLEADA1
from taller6mm_pipeline.familias.oleada1_cuerpos import FAMILIAS_CUERPOS

M_A_MM = 1000.0


def registro_familias() -> dict[str, Familia]:
    """Todas las familias conocidas (sin tocar ninguna): base, oleada 1 y cuerpos del M4."""
    return {**FAMILIAS, **FAMILIAS_OLEADA1, **FAMILIAS_CUERPOS}


@dataclass(frozen=True, slots=True)
class SocketPieza:
    """Socket leído del GLB (posición en mm, normal y tangente en ejes de la pieza)."""

    slot_key: str
    posicion_mm: tuple[float, float, float]
    normal: tuple[float, float, float]
    tangente: tuple[float, float, float]
    interfaz: str
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PiezaEnsamblable:
    id: str
    rol: str
    familia_id: str
    id_variante: str
    nivel: str
    es_demo: bool
    material: str
    requiere: tuple[str, ...]
    ofrece: tuple[str, ...]
    parametros: Mapping[str, Valor]
    pendientes: tuple[str, ...]
    notas: tuple[str, ...]
    sockets: tuple[SocketPieza, ...]
    vertices_mm: NDArray[np.float64] | None
    triangulos: NDArray[np.uint32] | None
    # Si no hay malla: motivo (el ensamblador lo registra como hueco de datos).
    motivo_sin_malla: str | None = None
    # Metadatos de la fuente (ruta o familia), para el informe.
    fuente: str = ""

    @property
    def tiene_malla(self) -> bool:
        return self.vertices_mm is not None

    def socket(self, slot_key: str) -> SocketPieza | None:
        return next((s for s in self.sockets if s.slot_key == slot_key), None)


def leer_pieza_glb(datos: bytes, id_: str, rol: str, fuente: str = "") -> PiezaEnsamblable:
    """Lee un GLB escrito por `familias.glb.escribir_glb` (nodo `pieza` + nodos `socket.*`)."""
    doc, binario = leer_glb(datos)
    prim = doc["meshes"][0]["primitives"][0]
    acc_pos = doc["accessors"][prim["attributes"]["POSITION"]]
    acc_idx = doc["accessors"][prim["indices"]]
    vp, vi = doc["bufferViews"][acc_pos["bufferView"]], doc["bufferViews"][acc_idx["bufferView"]]
    pos = np.frombuffer(binario, dtype="<f4", count=acc_pos["count"] * 3, offset=vp["byteOffset"]).reshape(-1, 3)
    idx = np.frombuffer(binario, dtype="<u4", count=acc_idx["count"], offset=vi["byteOffset"]).reshape(-1, 3)
    nodos = doc["nodes"]
    meta = next(n for n in nodos if n["name"] == "pieza").get("extras", {})
    sockets = []
    for n in nodos:
        if not n["name"].startswith("socket."):
            continue
        ex = dict(n.get("extras", {}))
        interfaz, normal, tangente = ex.pop("interfaz"), ex.pop("normal"), ex.pop("tangente")
        sockets.append(
            SocketPieza(
                n["name"].removeprefix("socket."),
                tuple(round(v * M_A_MM, 4) for v in n["translation"]),  # type: ignore[arg-type]
                tuple(normal),  # type: ignore[arg-type]
                tuple(tangente),  # type: ignore[arg-type]
                interfaz,
                ex,
            )
        )
    return PiezaEnsamblable(
        id=id_,
        rol=rol,
        familia_id=str(meta.get("familia", "externa")),
        id_variante=str(meta.get("id_variante", hashlib.sha256(datos).hexdigest()[:12])),
        nivel=str(meta.get("nivel", "T0")),
        es_demo=bool(meta.get("es_demo", True)),
        material=str(meta.get("material", "mat.anodizado_negro")),
        requiere=tuple(meta.get("requiere", ())),
        ofrece=tuple(meta.get("ofrece", ())),
        parametros=dict(meta.get("parametros", {})),
        pendientes=tuple(meta.get("pendientes", ())),
        notas=tuple(meta.get("notas", ())),
        sockets=tuple(sockets),
        vertices_mm=(pos.astype(np.float64) * M_A_MM).round(4),
        triangulos=idx.astype(np.uint32),
        fuente=fuente,
    )


def desde_pieza_sin_malla(p: Pieza, id_: str, rol: str, fuente: str) -> PiezaEnsamblable:
    return PiezaEnsamblable(
        id=id_,
        rol=rol,
        familia_id=p.familia_id,
        id_variante=p.id_variante,
        nivel=p.nivel,
        es_demo=p.es_demo,
        material=p.material,
        requiere=p.requiere,
        ofrece=p.ofrece,
        parametros=dict(p.parametros),
        pendientes=p.pendientes,
        notas=p.notas,
        sockets=(),
        vertices_mm=None,
        triangulos=None,
        motivo_sin_malla="; ".join(p.notas) or "sin malla",
        fuente=fuente,
    )


def generar_pieza(
    id_: str, rol: str, familia: str, params: Mapping[str, Valor], cache: Path | None = None
) -> PiezaEnsamblable:
    """Genera (o lee de la caché por `id_variante`) una pieza de una familia. Las cotas son de barrido (`es_demo`)."""
    fam = registro_familias().get(familia)
    if fam is None:
        raise KeyError(f"familia desconocida: {familia}")
    fuente = f"familia {familia}"
    idv = fam.id_variante(params)
    ruta = cache / f"{idv.replace('@', '_')}.glb" if cache is not None else None
    if ruta is not None and ruta.exists():
        return leer_pieza_glb(ruta.read_bytes(), id_, rol, fuente)
    pieza = fam.generar(params)
    if pieza.malla is None:
        return desde_pieza_sin_malla(pieza, id_, rol, fuente)
    glb = pieza.glb()
    if ruta is not None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(glb)
    return leer_pieza_glb(glb, id_, rol, fuente)


def cargar_glb(id_: str, rol: str, ruta: Path) -> PiezaEnsamblable | None:
    """Pieza de un GLB del kit; si el archivo no está (los binarios no viven en el repo) devuelve `None`."""
    if not ruta.exists():
        return None
    return leer_pieza_glb(ruta.read_bytes(), id_, rol, f"glb {ruta.name}")


def pieza_vacia(id_: str, rol: str, requiere: tuple[str, ...], motivo: str) -> PiezaEnsamblable:
    """Pieza de la que no existe ningún modelo ni familia (p. ej. un red dot): solo declara lo que requiere."""
    return PiezaEnsamblable(
        id=id_,
        rol=rol,
        familia_id="sin_modelo",
        id_variante="sin_modelo",
        nivel="T0",
        es_demo=True,
        material="mat.polimero_negro",
        requiere=requiere,
        ofrece=(),
        parametros={},
        pendientes=(),
        notas=(),
        sockets=(),
        vertices_mm=None,
        triangulos=None,
        motivo_sin_malla=motivo,
        fuente="sin modelo",
    )
