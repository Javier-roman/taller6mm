"""Asignador de materiales por familia y pieza (catálogo `catalogo/materiales-piezas.json`).

Es determinista: la semilla de variación entre piezas del mismo conjunto sale del id (CRC32), no del azar.
"""

from __future__ import annotations

import fnmatch
import json
import zlib
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from taller6mm_pipeline.materiales import biblioteca

RAIZ = Path(__file__).resolve().parents[5]
RUTA_CATALOGO = RAIZ / "catalogo" / "materiales-piezas.json"


@dataclass(frozen=True, slots=True)
class Asignacion:
    pieza_id: str
    familia: str
    material_id: str
    cubierta: bool  # False = cayó en el material por defecto (no hay regla explícita)
    motivo: str
    semilla: int
    variacion: dict[str, float]  # factores deterministas entre piezas del mismo conjunto

    def spec(self) -> dict[str, Any]:
        return biblioteca.material(self.material_id)


@cache
def cargar(ruta: Path = RUTA_CATALOGO) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def semilla_de(pieza_id: str) -> int:
    return zlib.crc32(pieza_id.encode("utf-8"))


def variacion_de(pieza_id: str, material_id: str) -> dict[str, float]:
    """Pequeño desplazamiento reproducible de color, rugosidad y desgaste (mismo material, piezas distintas)."""
    s = semilla_de(pieza_id)
    u = [((s >> (8 * i)) & 0xFF) / 255.0 * 2.0 - 1.0 for i in range(3)]  # tres números en [-1, 1]
    v = biblioteca.material(material_id)["variacion_pieza"]
    return {
        "color": round(1.0 + u[0] * v["color"], 4),
        "rugosidad": round(u[1] * v["rugosidad"], 4),
        "desgaste": round(1.0 + u[2] * 0.35, 4),
    }


def asignar(familia: str, pieza_id: str, cat: dict[str, Any] | None = None) -> Asignacion:
    """Material de una pieza: id por patrón, familia exacta, familia con `*`, prefijo y, si no, el defecto."""
    cat = cat or cargar()
    regla = next((r for r in cat["por_id"] if fnmatch.fnmatch(pieza_id, r["patron"])), None)
    if regla is None:
        fams = cat["familias"]
        clave = familia if familia in fams else None
        clave = clave or next((k for k in fams if "*" in k and fnmatch.fnmatch(familia, k)), None)
        clave = clave or familia.split(".")[0]
        regla = fams.get(clave)
    if regla is None:
        mat, motivo, cubierta = cat["defecto"], "sin regla: material por defecto", False
    else:
        mat, motivo, cubierta = regla["material"], regla["motivo"], True
    return Asignacion(pieza_id, familia, mat, cubierta, motivo, semilla_de(pieza_id), variacion_de(pieza_id, mat))


def validar_catalogo(cat: dict[str, Any] | None = None) -> list[str]:
    """Errores del catálogo: materiales inexistentes o inválidos."""
    cat = cat or cargar()
    ids = {cat["defecto"]} | {r["material"] for r in cat["por_id"]} | {r["material"] for r in cat["familias"].values()}
    ids |= {m for r in cat.get("ranuras_secundarias", {}).values() for m in r.values()}
    errores = [f"material desconocido: {i}" for i in sorted(ids) if i not in biblioteca.MATERIALES]
    for i, m in biblioteca.MATERIALES.items():
        errores += biblioteca.validar(i, m)
    return errores
