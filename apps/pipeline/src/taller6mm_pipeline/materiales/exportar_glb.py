"""Exporta GLB con materiales PBR horneados (baseColor, metalicidad/rugosidad y normal en WebP) para el visor web.

El visor y los renders de Blender comparten fuente: el material de cada pieza sale de `catalogo/materiales-piezas.json`
y de la biblioteca (`biblioteca.py`), con el desgaste y la suciedad de N4 ya horneados en las texturas por
`blender/escalera_render.py` (modo `exportar`). La luz no va dentro: la pone el visor con
`catalogo/iluminacion-presets.json`. Las texturas salen de las recetas procedurales y de la base CC0 interna; ninguna
foto de terceros, sin logos ni marcajes. Todo es T0 y `publicable_3d=false`. Salida en
`assets-src/vistas/glb-materiales/` (ignorada por git) con un `indice.json` que el visor lee para saber qué hay.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from taller6mm_pipeline.materiales import cc0

RAIZ = cc0.RAIZ
DIR_GLB = RAIZ / "assets-src" / "vistas" / "glb-materiales"
ESQUEMA_INDICE = "glb-materiales/v1"
SCRIPT_BLENDER = RAIZ / "apps" / "pipeline" / "blender" / "escalera_render.py"
RES_PIEZA = 512
RES_ENSAMBLAJE = 256


def spec_render(material_id: str) -> dict[str, Any]:
    """Receta del material más las rutas de la base CC0 si están en disco (uso interno del horneado)."""
    from taller6mm_pipeline.materiales import biblioteca

    spec = dict(biblioteca.material(material_id))
    base = cc0.resolver(spec.get("cc0"))
    if base is not None:
        spec["_cc0"] = base
    return spec


def trabajo_pieza(
    pieza_id: str, glb: Path, material_id: str, semilla: int, variacion: dict[str, float], salida: Path, res: int
) -> dict[str, Any]:
    return {
        "exportar": True,
        "id": pieza_id,
        "glb": str(glb),
        "salida_glb": str(salida),
        "material": spec_render(material_id),
        "semilla": semilla,
        "variacion": variacion,
        "res": res,
    }


def trabajo_ensamblaje(
    build_id: str, glb: Path, piezas: dict[str, dict[str, Any]], salida: Path, res: int
) -> dict[str, Any]:
    """`piezas`: {nodo `pieza.<id>`: {material_id, semilla, variacion}} (los marcadores no entran)."""
    return {
        "exportar": True,
        "id": build_id,
        "glb": str(glb),
        "salida_glb": str(salida),
        "piezas": {
            nodo: {"material": spec_render(p["material_id"]), "semilla": p["semilla"], "variacion": p["variacion"]}
            for nodo, p in piezas.items()
        },
        "res": res,
    }


def ejecutar(blender: Path, trabajos: list[dict[str, Any]], carpeta: Path = DIR_GLB) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "lista-exportar.json"
    ruta.write_text(json.dumps(trabajos), encoding="utf-8")
    cmd = [
        str(blender),
        "--background",
        "--factory-startup",
        "--python",
        str(SCRIPT_BLENDER),
        "--",
        "--lista",
        str(ruta),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=4 * 3600)  # noqa: S603


def actualizar_indice(entradas: dict[str, dict[str, Any]], carpeta: Path = DIR_GLB) -> Path:
    """`indice.json`: por id, ruta relativa del GLB, tamaño y hash; el visor lo lee para listar lo exportado."""
    ruta = carpeta / "indice.json"
    doc = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {"esquema": ESQUEMA_INDICE, "glb": {}}
    for id_, e in entradas.items():
        glb = carpeta / e["archivo"]
        if not glb.exists():
            continue
        datos = glb.read_bytes()
        doc["glb"][id_] = {
            **e,
            "bytes": len(datos),
            "sha256": hashlib.sha256(datos).hexdigest(),
            "nivel_fidelidad": "T0",
            "publicable_3d": False,
            "texturas": "webp",
        }
    ruta.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return ruta
