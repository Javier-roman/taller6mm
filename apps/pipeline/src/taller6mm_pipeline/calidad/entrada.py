"""Piezas que entran en la puerta: malla en mm, sockets, metadatos y cotas, leídos siempre de un GLB propio.

Una pieza recién generada pasa por `Pieza.glb()` y una del disco por sus bytes, así que la puerta mide exactamente
lo que verá el ensamblador y el visor. Los conjuntos (builds) entran con su informe JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from taller6mm_pipeline.familias.glb import leer_glb

RAIZ = Path(__file__).resolve().parents[5]
APP = Path(__file__).resolve().parents[3]
SALIDA = APP / "salida"
# Carpetas de GLB sueltos que se revisan por defecto (origen -> carpeta). El kit se genera con Blender desde modelos CC
# que no viven en git: si falta la carpeta, el bucle lo registra como hueco y no inventa nada.
CARPETAS = {
    "kit": SALIDA / "kit-m4",
}
M_A_MM = 1000.0


@dataclass(frozen=True, slots=True)
class PiezaCalidad:
    id: str
    origen: str
    familia: str
    vertices: NDArray[np.float64]
    triangulos: NDArray[np.int64]
    sockets: tuple[dict[str, Any], ...]
    cotas: tuple[dict[str, Any], ...]
    parametros: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)
    ruta_glb: str = ""
    glb: bytes = b""


@dataclass(frozen=True, slots=True)
class Ensamblaje:
    id: str
    informe: dict[str, Any]
    ruta_glb: str = ""


def desde_glb(datos: bytes, id_: str, origen: str, ruta: str = "") -> PiezaCalidad:
    doc, binario = leer_glb(datos)
    prim = doc["meshes"][0]["primitives"][0]
    ap, ai = doc["accessors"][prim["attributes"]["POSITION"]], doc["accessors"][prim["indices"]]
    vp, vi = doc["bufferViews"][ap["bufferView"]], doc["bufferViews"][ai["bufferView"]]
    pos = np.frombuffer(binario, dtype="<f4", count=ap["count"] * 3, offset=vp.get("byteOffset", 0)).reshape(-1, 3)
    idx = np.frombuffer(binario, dtype="<u4", count=ai["count"], offset=vi.get("byteOffset", 0)).reshape(-1, 3)
    nodos = doc["nodes"]
    meta = next((n for n in nodos if n.get("name") == "pieza"), {}).get("extras", {})
    sockets = tuple(
        {"nombre": n["name"], "posicion_mm": [v * M_A_MM for v in n.get("translation", (0, 0, 0))]}
        for n in nodos
        if str(n.get("name", "")).startswith("socket.")
    )
    return PiezaCalidad(
        id=id_,
        origen=origen,
        familia=str(meta.get("familia", "externa")),
        vertices=(pos.astype(np.float64) * M_A_MM).round(4),
        triangulos=idx.astype(np.int64),
        sockets=sockets,
        cotas=tuple(meta.get("cotas", ())),
        parametros=dict(meta.get("parametros", {})),
        meta=dict(meta),
        ruta_glb=ruta,
        glb=datos,
    )


def leer_carpeta(carpeta: Path, origen: str) -> list[PiezaCalidad]:
    if not carpeta.is_dir():
        return []
    return [desde_glb(f.read_bytes(), f.stem, origen, str(f)) for f in sorted(carpeta.glob("*.glb"))]


def generar_piezas() -> list[PiezaCalidad]:
    """Genera en proceso las variantes de la oleada 1 y de los cuerpos: la puerta ve siempre el código actual."""
    from taller6mm_pipeline.familias import oleada1, oleada1_cuerpos

    salida = [desde_glb(oleada1.generar(v).glb(), v.id, "oleada1") for v in oleada1.VARIANTES]
    salida += [desde_glb(oleada1_cuerpos.generar_variante(v).glb(), v.id, "cuerpos") for v in oleada1_cuerpos.TANDA]
    return salida


def leer_ensamblajes(carpeta: Path) -> list[Ensamblaje]:
    if not carpeta.is_dir():
        return []
    return [
        Ensamblaje(f.name.removesuffix(".informe.json"), json.loads(f.read_text(encoding="utf-8")), str(f))
        for f in sorted(carpeta.glob("*.informe.json"))
    ]


def generar_ensamblajes() -> list[Ensamblaje]:
    """Reensambla los builds de `catalogo/m4-builds.json` con el ensamblador actual y devuelve sus informes."""
    from taller6mm_pipeline.ensamblador.ensamblar import ensamblar

    doc = json.loads((RAIZ / "catalogo" / "m4-builds.json").read_text(encoding="utf-8"))
    carpeta = SALIDA / "ensamblador"
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = []
    for build in doc["builds"]:
        res = ensamblar(build, cache=carpeta / "cache", kit=SALIDA)
        ruta = carpeta / f"{res.id}.glb"
        ruta.write_bytes(res.glb)
        salida.append(Ensamblaje(res.id, res.informe, str(ruta)))
    return salida
