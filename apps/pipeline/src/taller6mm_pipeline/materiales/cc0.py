"""Resuelve las bases CC0 de `catalogo/materiales-cc0.json` a rutas de mapas en disco (solo uso interno del render).

Los mapas viven en `assets-src/materiales-cc0/` (ignorada por git). Pueden estar en el repo principal aunque se trabaje
desde un worktree: se busca también allí, o en la carpeta de `TALLER6MM_CC0`. Si no están, devuelve `None` y el render
usa la receta procedural (nada se inventa). Los hashes del catálogo entran en la clave de caché de los renders.
"""

from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[5]
RUTA_CATALOGO = RAIZ / "catalogo" / "materiales-cc0.json"
# Nombre del mapa según la fuente: (clave del render, sufijos posibles por orden de preferencia).
MAPAS = {
    "color": ("_1K-JPG_Color.jpg", "_diff_1k.jpg"),
    "rugosidad": ("_1K-JPG_Roughness.jpg", "_rough_1k.jpg"),
    "altura": ("_1K-JPG_Displacement.jpg",),
}


@cache
def catalogo() -> dict[str, dict[str, Any]]:
    doc = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))
    return {m["id"]: m for m in doc["materiales"]}


def raices() -> list[Path]:
    cand = [Path(p) for p in [os.environ.get("TALLER6MM_CC0", "")] if p]
    cand.append(RAIZ)
    partes = RAIZ.parts
    if ".claude" in partes:  # worktree: el repo principal está por encima de `.claude/worktrees/<x>`
        cand.append(Path(*partes[: partes.index(".claude")]))
    return cand


def resolver(spec_cc0: dict[str, Any] | None) -> dict[str, Any] | None:
    """Rutas absolutas de los mapas de la base CC0 de un material y su medida, o None si no están en disco."""
    if not spec_cc0 or spec_cc0["id"] not in catalogo():
        return None
    m = catalogo()[spec_cc0["id"]]
    for raiz in raices():
        carpeta = raiz / m["carpeta"]
        if not carpeta.is_dir():
            continue
        rutas: dict[str, str] = {}
        for clave, sufijos in MAPAS.items():
            for s in sufijos:
                f = next(iter(carpeta.glob(f"*{s}")), None)
                if f is not None:
                    rutas[clave] = str(f)
                    break
        if "rugosidad" in rutas:
            med = m.get("medidas", {})
            return {
                "id": m["id"],
                "mapas": rutas,
                "escala_m": spec_cc0.get("escala_m", 0.2),
                "solo": spec_cc0.get("solo"),
                "rug_media_tex": med.get("rugosidad_media"),
                "albedo_media_srgb": med.get("albedo_medio_srgb"),
                "huellas": {a["nombre"]: a["sha256"] for a in m["archivos"]},
            }
    return None
